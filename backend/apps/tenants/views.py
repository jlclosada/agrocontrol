from django.contrib.auth import get_user_model
from django.db import transaction
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
from apps.tenants.permissions import IsCoopAdmin
from apps.tenants.serializers import (
    CooperativeSerializer,
    CooperativeSettingsSerializer,
    InviteMemberSerializer,
    MembershipSerializer,
)
from apps.tenants.utils import TenantContextMixin, resolve_membership

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
    """Manage members of the active cooperative (admin only)."""

    serializer_class = MembershipSerializer
    permission_classes = [IsAuthenticated, IsCoopAdmin]

    def get_queryset(self):
        return CooperativeMembership.objects.select_related("user").filter(
            cooperative=self.get_cooperative()
        )

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
        return Response(
            MembershipSerializer(membership).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
