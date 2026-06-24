import csv

from django.http import HttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.services import build_dashboard, profitability_rows
from apps.tenants.permissions import HasCooperativeRole
from apps.tenants.utils import TenantContextMixin


class DashboardView(TenantContextMixin, APIView):
    """Role-aware KPI dashboard for the active cooperative."""

    permission_classes = [IsAuthenticated, HasCooperativeRole]

    def get(self, request):
        data = build_dashboard(
            self.get_cooperative(), request.user, self.get_role()
        )
        return Response(data)


class ProfitabilityExportView(TenantContextMixin, APIView):
    """CSV export of per-crop profitability."""

    permission_classes = [IsAuthenticated, HasCooperativeRole]

    def get(self, request):
        rows = profitability_rows(
            self.get_cooperative(), request.user, self.get_role()
        )
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            'attachment; filename="rentabilidad.csv"'
        )
        fieldnames = [
            "cultivo", "variedad", "campaña", "parcela", "coste_total",
            "ingreso", "beneficio", "coste_ha", "margen_pct",
        ]
        writer = csv.DictWriter(response, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        return response
