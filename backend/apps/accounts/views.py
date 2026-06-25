from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts import mfa
from apps.audit.models import AuditEvent
from apps.audit.services import record_audit
from apps.tenants.utils import resolve_membership

from .serializers import (
    AuditTokenObtainPairSerializer,
    ChangePasswordSerializer,
    MfaDeviceSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


def _login_cooperative(request, user):
    """Best-effort cooperative for stamping a login audit event."""
    if user is None:
        return None
    requested = request.headers.get("X-Cooperative")
    membership = resolve_membership(user, requested)
    return membership.cooperative if membership else None


class AuditTokenObtainPairView(TokenObtainPairView):
    """Login endpoint that enforces MFA and records audit events."""

    serializer_class = AuditTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        email = request.data.get("email", "")
        user = User.objects.filter(email=email).first()
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as exc:
            detail = exc.detail if isinstance(exc.detail, dict) else {}
            if "mfa_required" in detail:
                record_audit(
                    AuditEvent.LOGIN_MFA_REQUIRED, request=request, user=user,
                    email=email, cooperative=_login_cooperative(request, user),
                    detail="Segundo factor requerido",
                )
                return Response(
                    {"mfa_required": True}, status=status.HTTP_401_UNAUTHORIZED
                )
            record_audit(
                AuditEvent.LOGIN_FAILED, request=request, user=user, email=email,
                cooperative=_login_cooperative(request, user),
                detail="Credenciales o MFA inválidos",
            )
            raise

        record_audit(
            AuditEvent.LOGIN_SUCCESS, request=request, user=serializer.user,
            email=email, cooperative=_login_cooperative(request, serializer.user),
        )
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        coop = getattr(serializer, "_cooperative", None)
        record_audit(
            AuditEvent.USER_REGISTERED, request=request, user=user,
            email=user.email, cooperative=coop,
            detail="Alta de usuario y cooperativa",
        )
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
                "cooperative_slug": coop.slug if coop else None,
            },
            status=status.HTTP_201_CREATED,
        )


class MeView(APIView):
    def get(self, request):
        return Response(
            UserSerializer(request.user, context={"request": request}).data
        )

    def patch(self, request):
        serializer = UserSerializer(
            request.user, data=request.data, partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ChangePasswordView(APIView):
    """Let an authenticated user change their own password."""

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        record_audit(
            AuditEvent.PASSWORD_CHANGED, request=request, user=request.user,
            email=request.user.email,
        )
        return Response({"detail": "Contraseña actualizada."})


class MfaEnrollView(APIView):
    """Start TOTP enrollment: returns the secret provisioning URI."""

    def post(self, request):
        device, uri = mfa.enroll(request.user)
        return Response(
            {"device_id": str(device.id), "provisioning_uri": uri},
            status=status.HTTP_201_CREATED,
        )


class MfaConfirmView(APIView):
    """Confirm a pending TOTP device with a code."""

    def post(self, request):
        device_id = request.data.get("device_id")
        code = request.data.get("code", "")
        device = request.user.mfa_devices.filter(id=device_id, confirmed=False).first()
        if device is None:
            return Response(
                {"detail": "Dispositivo no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if not mfa.confirm(device, code):
            return Response(
                {"detail": "Código inválido."}, status=status.HTTP_400_BAD_REQUEST
            )
        record_audit(
            AuditEvent.MFA_ENROLLED, request=request, user=request.user,
            email=request.user.email,
        )
        return Response(MfaDeviceSerializer(device).data)


class MfaDeviceListView(generics.ListAPIView):
    serializer_class = MfaDeviceSerializer

    def get_queryset(self):
        return self.request.user.mfa_devices.all()
