from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.tenants.models import (
    Cooperative,
    CooperativeMembership,
    CooperativeSettings,
    Role,
)

User = get_user_model()


class CooperativeSettingsSerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(read_only=True)

    class Meta:
        model = CooperativeSettings
        fields = [
            "currency", "default_operation_cost",
            "stock_alerts_enabled", "expiry_alerts_enabled",
            "safety_alerts_enabled", "weather_alerts_enabled", "expiry_alert_days",
            "display_name", "tagline", "primary_color", "logo_emoji",
            "brand_name", "agents_enabled", "traceability_enabled",
        ]


class CooperativeSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    settings = serializers.SerializerMethodField()

    class Meta:
        model = Cooperative
        fields = [
            "id", "name", "slug", "tax_id", "country", "region",
            "is_active", "role", "settings", "created_at",
        ]
        read_only_fields = ["id", "is_active", "created_at", "role", "settings"]

    def get_role(self, obj):
        membership = getattr(obj, "_current_membership", None)
        return membership.role if membership else None

    def get_settings(self, obj):
        from apps.tenants.models import get_settings

        return CooperativeSettingsSerializer(get_settings(obj)).data


class MembershipSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.SerializerMethodField()
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)
    locale = serializers.CharField(source="user.locale", read_only=True)
    last_login = serializers.DateTimeField(source="user.last_login", read_only=True)
    date_joined = serializers.DateTimeField(source="user.date_joined", read_only=True)
    has_account = serializers.SerializerMethodField()
    initials = serializers.SerializerMethodField()
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = CooperativeMembership
        fields = [
            "id", "user", "user_email", "user_name", "first_name", "last_name",
            "phone", "locale", "last_login", "date_joined", "has_account",
            "initials", "role", "role_display", "is_active", "created_at",
        ]
        read_only_fields = ["id", "user", "created_at"]

    def get_user_name(self, obj):
        full = f"{obj.user.first_name} {obj.user.last_name}".strip()
        return full or obj.user.email

    def get_has_account(self, obj):
        return obj.user.has_usable_password()

    def get_initials(self, obj):
        u = obj.user
        a = (u.first_name[:1] or u.email[:1]).upper()
        b = (u.last_name[:1] or u.email[1:2]).upper()
        return (a + b) or "·"


class CreateMemberSerializer(serializers.Serializer):
    """Add an existing user to the team or create (alta) a brand-new one."""

    email = serializers.EmailField()
    first_name = serializers.CharField(required=False, allow_blank=True, default="")
    last_name = serializers.CharField(required=False, allow_blank=True, default="")
    phone = serializers.CharField(required=False, allow_blank=True, default="")
    role = serializers.ChoiceField(choices=Role.choices, default=Role.FARMER)
    create_account = serializers.BooleanField(default=True)
    password = serializers.CharField(
        required=False, allow_blank=True, write_only=True,
        help_text="Initial password when creating a login account.",
    )


class InviteMemberSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=Role.choices, default=Role.FARMER)
