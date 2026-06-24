from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel
from decimal import Decimal


class Role(models.TextChoices):
    SUPERADMIN = "SUPERADMIN", "Superadministrador"
    COOP_ADMIN = "COOP_ADMIN", "Admin cooperativa"
    AGRONOMIST = "AGRONOMIST", "Técnico agrónomo"
    FARMER = "FARMER", "Agricultor"
    OPERATOR = "OPERATOR", "Operario"
    AUDITOR = "AUDITOR", "Auditor"


# Roles allowed to manage the cooperative configuration and memberships.
ADMIN_ROLES = frozenset({Role.SUPERADMIN, Role.COOP_ADMIN})
# Roles allowed to write domain data (field notebook, inventory, etc.).
WRITE_ROLES = frozenset(
    {Role.SUPERADMIN, Role.COOP_ADMIN, Role.AGRONOMIST, Role.FARMER, Role.OPERATOR}
)
# Read-only roles never get write access regardless of the endpoint.
READONLY_ROLES = frozenset({Role.AUDITOR})
# Convenience set for auditor-only access grants.
AUDITOR_ROLE_SET = frozenset({Role.AUDITOR})


class Cooperative(TimeStampedModel):
    """A tenant. All domain data is isolated per cooperative."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=120, unique=True)
    tax_id = models.CharField(max_length=32, blank=True)
    country = models.CharField(max_length=2, default="ES")
    region = models.CharField(max_length=120, blank=True)
    mfa_required = models.BooleanField(
        default=False, help_text="Require MFA for all members of this cooperative."
    )
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class CooperativeSettings(TimeStampedModel):
    """Per-cooperative configuration. Drives business rules and branding so the
    whole application is configurable from the admin panel (no hardcoded values).

    A settings row is lazily created for every cooperative via
    :func:`get_settings`. Edit it inline from the Cooperative admin page.
    """

    cooperative = models.OneToOneField(
        Cooperative, on_delete=models.CASCADE, related_name="settings"
    )

    # --- Economics ---
    currency = models.CharField(
        max_length=3, default="EUR", help_text="ISO 4217 code shown across the UI."
    )
    default_operation_cost = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("25.00"),
        help_text="Default labour cost imputed per field operation.",
    )

    # --- Alerts ---
    stock_alerts_enabled = models.BooleanField(default=True)
    expiry_alerts_enabled = models.BooleanField(default=True)
    safety_alerts_enabled = models.BooleanField(default=True)
    expiry_alert_days = models.PositiveIntegerField(
        default=30,
        help_text="Default days-before-expiry threshold for expiry alerts.",
    )

    # --- Branding (consumed by the frontend) ---
    display_name = models.CharField(
        max_length=120, blank=True,
        help_text="Brand name shown in the UI. Defaults to the cooperative name.",
    )
    tagline = models.CharField(max_length=200, blank=True)
    primary_color = models.CharField(
        max_length=7, default="#16a34a",
        help_text="Primary brand colour (hex), e.g. #16a34a.",
    )
    logo_emoji = models.CharField(max_length=8, default="🌱")

    # --- Feature flags ---
    agents_enabled = models.BooleanField(
        default=True, help_text="Expose the AI agents module in the UI."
    )
    traceability_enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Cooperative settings"
        verbose_name_plural = "Cooperative settings"

    def __str__(self) -> str:
        return f"Configuración · {self.cooperative.name}"

    @property
    def brand_name(self) -> str:
        return self.display_name or self.cooperative.name


def get_settings(cooperative) -> "CooperativeSettings":
    """Return the cooperative settings, creating defaults on first access."""
    obj, _ = CooperativeSettings.objects.get_or_create(cooperative=cooperative)
    return obj


class CooperativeMembership(TimeStampedModel):
    """Links a user to a cooperative with a role (the tenant binding)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    cooperative = models.ForeignKey(
        Cooperative,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.FARMER)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("user", "cooperative")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user} @ {self.cooperative} ({self.role})"
