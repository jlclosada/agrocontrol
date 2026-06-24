from django.contrib import admin

from apps.tenants.models import (
    Cooperative,
    CooperativeMembership,
    CooperativeSettings,
)


class CooperativeSettingsInline(admin.StackedInline):
    model = CooperativeSettings
    can_delete = False
    extra = 0
    fieldsets = (
        ("Economía", {"fields": ("currency", "default_operation_cost")}),
        (
            "Alertas",
            {
                "fields": (
                    "stock_alerts_enabled",
                    "expiry_alerts_enabled",
                    "safety_alerts_enabled",
                    "expiry_alert_days",
                )
            },
        ),
        (
            "Marca",
            {
                "fields": (
                    "display_name",
                    "tagline",
                    "primary_color",
                    "logo_emoji",
                )
            },
        ),
        ("Módulos", {"fields": ("agents_enabled", "traceability_enabled")}),
    )


@admin.register(Cooperative)
class CooperativeAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "country", "mfa_required", "is_active", "created_at"]
    list_filter = ["mfa_required", "is_active"]
    search_fields = ["name", "slug", "tax_id"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [CooperativeSettingsInline]


@admin.register(CooperativeSettings)
class CooperativeSettingsAdmin(admin.ModelAdmin):
    list_display = [
        "cooperative",
        "currency",
        "default_operation_cost",
        "expiry_alert_days",
        "primary_color",
    ]
    search_fields = ["cooperative__name", "display_name"]


@admin.register(CooperativeMembership)
class CooperativeMembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "cooperative", "role", "is_active"]
    list_filter = ["role", "is_active"]
    search_fields = ["user__email", "cooperative__name"]
