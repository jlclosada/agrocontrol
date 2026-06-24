"""MFA (TOTP) helpers for enrollment, confirmation and verification."""
import pyotp

from apps.accounts.models import MfaDevice
from apps.tenants.models import CooperativeMembership

ISSUER = "AgroControl OS"


def enroll(user, name="Authenticator"):
    """Create an unconfirmed TOTP device and return (device, provisioning_uri)."""
    secret = pyotp.random_base32()
    device = MfaDevice.objects.create(user=user, name=name, secret=secret)
    uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user.email, issuer_name=ISSUER
    )
    return device, uri


def confirm(device, code):
    """Confirm a pending device if the code is valid."""
    if verify_code(device.secret, code):
        device.confirmed = True
        device.save(update_fields=["confirmed"])
        return True
    return False


def verify_code(secret, code):
    return pyotp.TOTP(secret).verify(str(code), valid_window=1)


def has_confirmed_device(user):
    return user.mfa_devices.filter(confirmed=True).exists()


def verify_user_code(user, code):
    """True if ``code`` matches any confirmed device of the user."""
    for device in user.mfa_devices.filter(confirmed=True):
        if verify_code(device.secret, code):
            return True
    return False


def mfa_required_for(user):
    """MFA is required if the user enrolled a device or any of their
    cooperatives mandates it."""
    if has_confirmed_device(user):
        return True
    return CooperativeMembership.objects.filter(
        user=user, is_active=True, cooperative__mfa_required=True
    ).exists()
