from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.accounts.models import MfaDevice
from apps.tenants.models import (
    Cooperative,
    CooperativeMembership,
    Role,
    get_settings,
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "phone", "locale",
            "avatar", "avatar_url",
        ]
        read_only_fields = ["id", "email", "avatar_url"]
        extra_kwargs = {"avatar": {"write_only": True, "required": False}}

    def get_avatar_url(self, obj):
        if not obj.avatar:
            return None
        url = obj.avatar.url
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("La contraseña actual no es correcta.")
        return value

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


def _unique_coop_slug(name: str) -> str:
    base = slugify(name)[:110] or "coop"
    slug, i = base, 1
    while Cooperative.objects.filter(slug=slug).exists():
        i += 1
        slug = f"{base}-{i}"
    return slug


class RegisterSerializer(serializers.ModelSerializer):
    """Self-service signup: creates the user and their own cooperative, making
    them its administrator so they can use the app right away."""

    password = serializers.CharField(write_only=True, min_length=8)
    cooperative_name = serializers.CharField(write_only=True, max_length=200)

    class Meta:
        model = User
        fields = [
            "id", "email", "password", "first_name", "last_name", "phone",
            "cooperative_name",
        ]
        read_only_fields = ["id"]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Ya existe una cuenta con este email.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password")
        coop_name = validated_data.pop("cooperative_name").strip()
        user = User.objects.create_user(password=password, **validated_data)
        coop = Cooperative.objects.create(
            name=coop_name, slug=_unique_coop_slug(coop_name)
        )
        CooperativeMembership.objects.create(
            user=user, cooperative=coop, role=Role.COOP_ADMIN
        )
        get_settings(coop)  # lazily create the settings row
        self._cooperative = coop
        return user



class AuditTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT serializer that enforces MFA and exposes ``otp`` as optional input."""

    otp = serializers.CharField(required=False, allow_blank=True, write_only=True)

    def validate(self, attrs):
        from apps.accounts import mfa

        otp = (attrs.pop("otp", "") or "").strip()
        data = super().validate(attrs)  # raises if credentials are invalid

        if mfa.mfa_required_for(self.user):
            if not otp:
                raise serializers.ValidationError({"mfa_required": True})
            if not mfa.verify_user_code(self.user, otp):
                raise serializers.ValidationError({"otp": "Código MFA inválido."})

        return data


class MfaDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = MfaDevice
        fields = ["id", "name", "confirmed", "created_at"]
        read_only_fields = fields

