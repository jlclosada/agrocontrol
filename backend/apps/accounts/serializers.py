from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.accounts.models import MfaDevice

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "phone", "locale"]
        read_only_fields = ["id", "email"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "email", "password", "first_name", "last_name", "phone"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)


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

