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
            "safety_alerts_enabled", "expiry_alert_days",
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

    class Meta:
        model = CooperativeMembership
        fields = [
            "id", "user", "user_email", "user_name",
            "role", "is_active", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip()


class InviteMemberSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=Role.choices, default=Role.FARMER)
