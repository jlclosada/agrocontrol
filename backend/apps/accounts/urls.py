from django.urls import path

from .views import (
    ChangePasswordView,
    MeView,
    MfaConfirmView,
    MfaDeviceListView,
    MfaEnrollView,
    RegisterView,
)

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("auth/password/", ChangePasswordView.as_view(), name="change-password"),
    path("auth/mfa/enroll/", MfaEnrollView.as_view(), name="mfa-enroll"),
    path("auth/mfa/confirm/", MfaConfirmView.as_view(), name="mfa-confirm"),
    path("auth/mfa/devices/", MfaDeviceListView.as_view(), name="mfa-devices"),
]
