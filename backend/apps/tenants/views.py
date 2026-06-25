from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.crypto import get_random_string
from django.utils.text import slugify
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.tenants.models import (
    Cooperative,
    CooperativeMembership,
    CooperativeSettings,
    Role,
    get_settings,
)
from apps.tenants.permissions import IsCoopAdmin, IsCooperativeMember
from apps.tenants.serializers import (
    CooperativeSerializer,
    CooperativeSettingsSerializer,
    CreateMemberSerializer,
    InviteMemberSerializer,
    MembershipSerializer,
)
from apps.tenants.utils import TenantContextMixin, resolve_membership
from apps.audit.models import AuditEvent
from apps.audit.services import record_audit

User = get_user_model()


class CooperativeViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Cooperatives the current user belongs to. Creating one makes you admin."""

    serializer_class = CooperativeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        memberships = {
            m.cooperative_id: m
            for m in CooperativeMembership.objects.filter(
                user=self.request.user, is_active=True
            )
        }
        qs = Cooperative.objects.filter(id__in=memberships.keys())
        for coop in qs:
            coop._current_membership = memberships.get(coop.id)
        return qs

    def _unique_slug(self, name):
        base = slugify(name)[:110] or "coop"
        slug, i = base, 1
        while Cooperative.objects.filter(slug=slug).exists():
            i += 1
            slug = f"{base}-{i}"
        return slug

    @transaction.atomic
    def perform_create(self, serializer):
        coop = serializer.save(slug=self._unique_slug(serializer.validated_data["name"]))
        CooperativeMembership.objects.create(
            user=self.request.user, cooperative=coop, role=Role.COOP_ADMIN
        )
        coop._current_membership = CooperativeMembership.objects.get(
            user=self.request.user, cooperative=coop
        )

    @action(detail=False, methods=["get", "patch"], url_path="settings")
    def cooperative_settings(self, request):
        """Read (any member) or update (admins) the active cooperative settings."""
        requested = request.headers.get("X-Cooperative")
        membership = resolve_membership(request.user, requested)
        if membership is None:
            raise ValidationError({"detail": "No active cooperative."})
        config = get_settings(membership.cooperative)

        if request.method == "PATCH":
            if membership.role not in (Role.SUPERADMIN, Role.COOP_ADMIN):
                raise ValidationError(
                    {"detail": "Solo los administradores pueden cambiar la configuración."}
                )
            serializer = CooperativeSettingsSerializer(
                config, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        return Response(CooperativeSettingsSerializer(config).data)


class MembershipViewSet(TenantContextMixin, viewsets.ModelViewSet):
    """The cooperative's team. Any member can view the roster (e.g. to assign
    tasks); only admins can add, update roles, deactivate or create users."""

    serializer_class = MembershipSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated(), IsCooperativeMember()]
        return [IsAuthenticated(), IsCoopAdmin()]

    def get_queryset(self):
        return (
            CooperativeMembership.objects.select_related("user")
            .filter(cooperative=self.get_cooperative())
            .order_by("-is_active", "user__first_name", "user__email")
        )

    def perform_update(self, serializer):
        instance = serializer.instance
        prev_role = instance.role
        prev_active = instance.is_active
        membership = serializer.save()
        coop = self.get_cooperative()
        if membership.role != prev_role:
            record_audit(
                AuditEvent.MEMBER_ROLE_CHANGED,
                request=self.request,
                user=membership.user,
                cooperative=coop,
                detail=f"{prev_role} → {membership.role}",
            )
        if membership.is_active != prev_active:
            record_audit(
                AuditEvent.MEMBER_REACTIVATED
                if membership.is_active
                else AuditEvent.MEMBER_DEACTIVATED,
                request=self.request,
                user=membership.user,
                cooperative=coop,
            )

    @action(detail=False, methods=["post"], url_path="add")
    def add_member(self, request):
        """Add an existing user to the team, or create (alta) a new one."""
        serializer = CreateMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        coop = self.get_cooperative()

        user = User.objects.filter(email__iexact=data["email"]).first()
        created_user = False
        if not user:
            create_account = data.get("create_account", True)
            password = None
            if create_account:
                password = data.get("password") or get_random_string(16)
            user = User.objects.create_user(
                email=data["email"],
                password=password,
                first_name=data.get("first_name", ""),
                last_name=data.get("last_name", ""),
                phone=data.get("phone", ""),
            )
            created_user = True
            record_audit(
                AuditEvent.USER_REGISTERED,
                request=request,
                user=user,
                cooperative=coop,
                detail="Alta de usuario desde el equipo"
                + (" (con cuenta de acceso)" if create_account else " (sin cuenta)"),
            )
        elif data.get("first_name") or data.get("last_name") or data.get("phone"):
            # Keep basic profile info up to date for existing users.
            user.first_name = data.get("first_name") or user.first_name
            user.last_name = data.get("last_name") or user.last_name
            user.phone = data.get("phone") or user.phone
            user.save(update_fields=["first_name", "last_name", "phone"])

        membership, created = CooperativeMembership.objects.get_or_create(
            user=user, cooperative=coop, defaults={"role": data["role"]}
        )
        if not created:
            membership.role = data["role"]
            membership.is_active = True
            membership.save()
        if created or created_user:
            record_audit(
                AuditEvent.MEMBER_ADDED,
                request=request,
                user=user,
                cooperative=coop,
                detail=f"Rol: {data['role']}",
            )
        return Response(
            MembershipSerializer(membership).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="create-account")
    def create_account(self, request, pk=None):
        """Create login credentials for an existing member without an account."""
        membership = self.get_object()
        user = membership.user
        if user.has_usable_password():
            raise ValidationError(
                {"detail": "Este usuario ya tiene una cuenta de acceso."}
            )
        raw = (request.data.get("password") or "").strip()
        generated = None
        if not raw:
            raw = get_random_string(12)
            generated = raw
        user.set_password(raw)
        user.save(update_fields=["password"])
        record_audit(
            AuditEvent.MEMBER_ACCOUNT_CREATED,
            request=request,
            user=user,
            cooperative=self.get_cooperative(),
        )
        payload = MembershipSerializer(membership).data
        if generated:
            payload["generated_password"] = generated
        return Response(payload)

    @action(detail=False, methods=["post"])
    def invite(self, request):
        serializer = InviteMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        role = serializer.validated_data["role"]

        user = User.objects.filter(email=email).first()
        if not user:
            raise ValidationError({"email": "No user with this email yet."})

        membership, created = CooperativeMembership.objects.get_or_create(
            user=user,
            cooperative=self.get_cooperative(),
            defaults={"role": role},
        )
        if not created:
            membership.role = role
            membership.is_active = True
            membership.save()
        if created:
            record_audit(
                AuditEvent.MEMBER_ADDED,
                request=request,
                user=user,
                cooperative=self.get_cooperative(),
                detail=f"Rol: {role}",
            )
        return Response(
            MembershipSerializer(membership).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
