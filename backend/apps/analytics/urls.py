from django.urls import path

from apps.analytics.views import DashboardView, ProfitabilityExportView

urlpatterns = [
    path("analytics/dashboard/", DashboardView.as_view(), name="analytics-dashboard"),
    path(
        "analytics/export/profitability/",
        ProfitabilityExportView.as_view(),
        name="analytics-export-profitability",
    ),
]
