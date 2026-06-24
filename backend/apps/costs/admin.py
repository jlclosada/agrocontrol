from django.contrib import admin

from apps.costs.models import CostEntry, ProfitabilityReport


@admin.register(CostEntry)
class CostEntryAdmin(admin.ModelAdmin):
    list_display = ["crop", "category", "source", "amount", "date", "cooperative"]
    list_filter = ["cooperative", "category", "source"]
    search_fields = ["description", "crop__species"]


@admin.register(ProfitabilityReport)
class ProfitabilityReportAdmin(admin.ModelAdmin):
    list_display = [
        "crop", "total_cost", "income", "profit", "cost_per_ha",
        "margin_pct", "computed_at",
    ]
    list_filter = ["cooperative"]
    readonly_fields = [f.name for f in ProfitabilityReport._meta.fields]
