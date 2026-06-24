"""Seed a full demo environment for local testing.

Creates:
- A superuser admin (admin@agrocontrol.os / Agro1234!)
- A technician (tecnico@agrocontrol.os) and a farmer (agricultor@agrocontrol.os)
- A cooperative with memberships (admin, agronomist, farmer)
- Farms, parcels and crops
- Phytosanitary products with stock
- Field operations and a treatment (auto-deducts stock + triggers agents)
- The four built-in AI agents
- Sample memory entries (USER / PARCEL / GLOBAL)

Usage:
    python manage.py seed_demo
"""
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.farms.models import (
    Campaign,
    Crop,
    CropStatus,
    Farm,
    HarvestRecord,
    Parcel,
    Sector,
)
from apps.fieldbook.models import FieldOperation, OperationType, Treatment
from apps.costs.services import (
    compute_profitability,
    impute_operation_cost,
    impute_treatment_cost,
)
from apps.costs.models import CostCategory, CostEntry, CostSource
from apps.alerts.services import ensure_default_rules, evaluate_cooperative
from apps.inventory.models import (
    MovementType,
    Product,
    ProductCategory,
    StockBatch,
    StockMovement,
)
from apps.memory.models import MemoryScope
from apps.memory.services import MemoryService
from apps.tenants.models import (
    Cooperative,
    CooperativeMembership,
    Role,
    get_settings,
)

User = get_user_model()

ADMIN_EMAIL = "admin@agrocontrol.os"
ADMIN_PASSWORD = "Agro1234!"
TECH_EMAIL = "tecnico@agrocontrol.os"
FARMER_EMAIL = "agricultor@agrocontrol.os"
OPERATOR_EMAIL = "operario@agrocontrol.os"
AUDITOR_EMAIL = "auditor@agrocontrol.os"
FARMER2_EMAIL = "agricultor2@agrocontrol.os"
DEMO_PASSWORD = "Agro1234!"


class Command(BaseCommand):
    help = "Seed a full demo environment (users, cooperative, data, agents)."

    @transaction.atomic
    def handle(self, *args, **options):
        admin = self._user(ADMIN_EMAIL, ADMIN_PASSWORD, "Ada", "Admin", superuser=True)
        tech = self._user(TECH_EMAIL, DEMO_PASSWORD, "Tomás", "Técnico")
        farmer = self._user(FARMER_EMAIL, DEMO_PASSWORD, "Paco", "Agricultor")
        operator = self._user(OPERATOR_EMAIL, DEMO_PASSWORD, "Olga", "Operaria")
        auditor = self._user(AUDITOR_EMAIL, DEMO_PASSWORD, "Aurora", "Auditora")
        farmer2 = self._user(FARMER2_EMAIL, DEMO_PASSWORD, "Lucía", "Campos")

        coop, _ = Cooperative.objects.get_or_create(
            slug="cooperativa-demo",
            defaults={"name": "Cooperativa Demo", "country": "ES", "region": "Andalucía"},
        )
        for user, role in [
            (admin, Role.COOP_ADMIN),
            (tech, Role.AGRONOMIST),
            (farmer, Role.FARMER),
            (operator, Role.OPERATOR),
            (auditor, Role.AUDITOR),
            (farmer2, Role.FARMER),
        ]:
            CooperativeMembership.objects.get_or_create(
                user=user, cooperative=coop, defaults={"role": role}
            )

        settings = get_settings(coop)
        settings.display_name = "AgroControl OS"
        settings.tagline = "Cooperativa Demo · Olivar y cereal"
        settings.primary_color = "#16a34a"
        settings.logo_emoji = "\U0001F331"
        settings.currency = "EUR"
        settings.save()

        farm, _ = Farm.objects.get_or_create(
            cooperative=coop, owner=farmer, name="Finca El Olivar",
            defaults={"description": "Explotación de olivar y cereal de secano."},
        )
        parcel1, _ = Parcel.objects.get_or_create(
            cooperative=coop, farm=farm, name="Recinto Olivar Norte",
            defaults={
                "sigpac_ref": "29:067:0:0:12:34:A", "area_ha": Decimal("4.5"),
                "soil_type": "Franco-arcilloso", "latitude": Decimal("37.388300"),
                "longitude": Decimal("-4.765400"),
            },
        )
        parcel2, _ = Parcel.objects.get_or_create(
            cooperative=coop, farm=farm, name="Recinto Cereal Sur",
            defaults={
                "sigpac_ref": "29:067:0:0:12:35:B", "area_ha": Decimal("8.2"),
                "soil_type": "Franco-arenoso",
            },
        )

        campaign, _ = Campaign.objects.get_or_create(
            cooperative=coop, label="2025/2026",
            defaults={
                "start_date": date(2025, 9, 1), "end_date": date(2026, 8, 31),
            },
        )
        sector_norte, _ = Sector.objects.get_or_create(
            cooperative=coop, parcel=parcel1, name="Olivar Norte - Zona alta",
            defaults={"area_ha": Decimal("2.0")},
        )

        crop_olivo, _ = Crop.objects.get_or_create(
            cooperative=coop, parcel=parcel1, species="Olivo", variety="Picual",
            campaign="2025/2026",
            defaults={"status": CropStatus.GROWING, "sowing_date": date(2015, 3, 1),
                      "expected_yield_kg": Decimal("18000"),
                      "season": campaign, "sector": sector_norte},
        )
        crop_trigo, _ = Crop.objects.get_or_create(
            cooperative=coop, parcel=parcel2, species="Trigo", variety="Duro",
            campaign="2025/2026",
            defaults={"status": CropStatus.GROWING,
                      "sowing_date": date.today() - timedelta(days=60),
                      "expected_yield_kg": Decimal("32000"), "season": campaign},
        )

        # Backfill campaign/sector links on crops that pre-date these fields.
        Crop.objects.filter(pk=crop_olivo.pk, season__isnull=True).update(
            season=campaign, sector=sector_norte
        )
        Crop.objects.filter(pk=crop_trigo.pk, season__isnull=True).update(
            season=campaign
        )

        HarvestRecord.objects.get_or_create(
            cooperative=coop, crop=crop_olivo, date=date.today() - timedelta(days=5),
            defaults={"quantity_kg": Decimal("16500"), "quality_grade": Decimal("21.50"),
                      "notes": "Rendimiento graso 21,5%. Cosecha temprana."},
        )

        cobre = self._product(coop, "Cobre Nordox 75 WG", ProductCategory.FUNGICIDE,
                              "Óxido cuproso", "kg", 15, reorder=10)
        herbicida = self._product(coop, "Glifosato 36%", ProductCategory.HERBICIDE,
                                   "Glifosato", "L", 7, reorder=20)
        abono = self._product(coop, "NPK 15-15-15", ProductCategory.FERTILIZER,
                              "Nitrógeno-Fósforo-Potasio", "kg", 0, reorder=200)

        self._stock_in(coop, cobre, 25)
        self._stock_in(coop, herbicida, 12)   # below reorder after use → low stock
        self._stock_in(coop, abono, 500)

        FieldOperation.objects.get_or_create(
            cooperative=coop, crop=crop_trigo, operation_type=OperationType.SOWING,
            date=date.today() - timedelta(days=60),
            defaults={"description": "Siembra de trigo duro a 180 kg/ha.",
                      "area_ha": Decimal("8.2"), "performed_by": farmer},
        )
        FieldOperation.objects.get_or_create(
            cooperative=coop, crop=crop_trigo, operation_type=OperationType.FERTILIZATION,
            date=date.today() - timedelta(days=30),
            defaults={"description": "Abonado de cobertera con NPK.",
                      "area_ha": Decimal("8.2"), "performed_by": farmer},
        )

        if not Treatment.objects.filter(crop=crop_olivo, product=cobre).exists():
            Treatment.objects.create(
                cooperative=coop, crop=crop_olivo, product=cobre,
                date=date.today() - timedelta(days=10), dose=Decimal("3"),
                dose_unit="kg/ha", total_quantity=Decimal("13.5"),
                target_pest="Repilo (Spilocaea oleagina)", weather="Seco, 18°C",
                applicator=tech,
            )

        # ------------------------------------------------------------------
        # Second farm + diversified crops (viñedo, almendro, cítricos) to make
        # the demo richer and exercise alerts, costs and traceability.
        # ------------------------------------------------------------------
        farm2, _ = Farm.objects.get_or_create(
            cooperative=coop, owner=farmer2, name="Finca Las Viñas",
            defaults={"description": "Viñedo, almendro y cítricos en regadío."},
        )
        parcel_vina, _ = Parcel.objects.get_or_create(
            cooperative=coop, farm=farm2, name="Recinto Viñedo Este",
            defaults={
                "sigpac_ref": "29:067:0:0:13:01:C", "area_ha": Decimal("6.0"),
                "soil_type": "Franco-calcáreo", "latitude": Decimal("37.402100"),
                "longitude": Decimal("-4.741200"),
            },
        )
        parcel_almendro, _ = Parcel.objects.get_or_create(
            cooperative=coop, farm=farm2, name="Recinto Almendro Oeste",
            defaults={
                "sigpac_ref": "29:067:0:0:13:02:D", "area_ha": Decimal("5.5"),
                "soil_type": "Franco",
            },
        )
        parcel_citricos, _ = Parcel.objects.get_or_create(
            cooperative=coop, farm=farm2, name="Recinto Cítricos Bajo",
            defaults={
                "sigpac_ref": "29:067:0:0:13:03:E", "area_ha": Decimal("2.8"),
                "soil_type": "Franco-arenoso",
            },
        )
        sector_vina, _ = Sector.objects.get_or_create(
            cooperative=coop, parcel=parcel_vina, name="Viñedo Este - Pago alto",
            defaults={"area_ha": Decimal("3.0")},
        )
        sector_almendro, _ = Sector.objects.get_or_create(
            cooperative=coop, parcel=parcel_almendro, name="Almendro Oeste - Ladera",
            defaults={"area_ha": Decimal("2.5")},
        )

        # Previous (closed) campaign for historical reporting.
        campaign_prev, _ = Campaign.objects.get_or_create(
            cooperative=coop, label="2024/2025",
            defaults={
                "start_date": date(2024, 9, 1), "end_date": date(2025, 8, 31),
                "is_closed": True,
            },
        )

        crop_vid, _ = Crop.objects.get_or_create(
            cooperative=coop, parcel=parcel_vina, species="Vid", variety="Tempranillo",
            campaign="2025/2026",
            defaults={"status": CropStatus.GROWING, "sowing_date": date(2018, 3, 15),
                      "expected_yield_kg": Decimal("21000"),
                      "expected_harvest_date": date(2026, 9, 20),
                      "season": campaign, "sector": sector_vina},
        )
        crop_almendro, _ = Crop.objects.get_or_create(
            cooperative=coop, parcel=parcel_almendro, species="Almendro", variety="Guara",
            campaign="2025/2026",
            defaults={"status": CropStatus.GROWING, "sowing_date": date(2016, 2, 20),
                      "expected_yield_kg": Decimal("8000"),
                      "expected_harvest_date": date.today() + timedelta(days=25),
                      "season": campaign, "sector": sector_almendro},
        )
        crop_naranja, _ = Crop.objects.get_or_create(
            cooperative=coop, parcel=parcel_citricos, species="Naranjo", variety="Navelina",
            campaign="2025/2026",
            defaults={"status": CropStatus.GROWING, "sowing_date": date(2014, 4, 1),
                      "expected_yield_kg": Decimal("26000"),
                      "expected_harvest_date": date.today() + timedelta(days=5),
                      "season": campaign},
        )
        crop_girasol, _ = Crop.objects.get_or_create(
            cooperative=coop, parcel=parcel2, species="Girasol", variety="Alto oleico",
            campaign="2025/2026",
            defaults={"status": CropStatus.PLANNED,
                      "sowing_date": date.today() + timedelta(days=30),
                      "expected_yield_kg": Decimal("12000"), "season": campaign},
        )
        crop_olivo_prev, _ = Crop.objects.get_or_create(
            cooperative=coop, parcel=parcel1, species="Olivo", variety="Picual",
            campaign="2024/2025",
            defaults={"status": CropStatus.HARVESTED, "sowing_date": date(2015, 3, 1),
                      "expected_yield_kg": Decimal("15000"),
                      "season": campaign_prev, "sector": sector_norte},
        )

        # More phytosanitary products / inputs.
        insecticida = self._product(coop, "Spintor 480 SC", ProductCategory.INSECTICIDE,
                                    "Spinosad", "L", 7, reorder=10)
        acaricida = self._product(coop, "Vertimec 1.8 EC", ProductCategory.INSECTICIDE,
                                   "Abamectina", "L", 14, reorder=6)
        foliar = self._product(coop, "Bioestimulante Algas", ProductCategory.FERTILIZER,
                               "Extracto de algas marinas", "L", 0, reorder=15)
        azufre = self._product(coop, "Azufre Mojable 80%", ProductCategory.FUNGICIDE,
                               "Azufre", "kg", 5, reorder=30)
        semilla = self._product(coop, "Semilla Girasol AO", ProductCategory.OTHER,
                                "Semilla certificada", "ud", 0, reorder=5)

        # Batches with varied expiry → exercises expiry alerts.
        self._batch_in(coop, insecticida, 18, "L-SPIN-2025", expiry_days=20)   # caduca pronto
        self._batch_in(coop, acaricida, 8, "L-VERT-2025", expiry_days=400)
        self._batch_in(coop, foliar, 5, "L-ALGA-2024", expiry_days=-10)        # caducado
        self._batch_in(coop, azufre, 60, "L-AZUF-2025", expiry_days=90)
        self._batch_in(coop, semilla, 12, "L-GIRA-2025", expiry_days=None)

        # Field operations across the new crops (some performed by the operator).
        FieldOperation.objects.get_or_create(
            cooperative=coop, crop=crop_olivo, operation_type=OperationType.PRUNING,
            date=date.today() - timedelta(days=45),
            defaults={"description": "Poda de mantenimiento del olivar.",
                      "area_ha": Decimal("4.5"), "performed_by": operator},
        )
        FieldOperation.objects.get_or_create(
            cooperative=coop, crop=crop_vid, operation_type=OperationType.IRRIGATION,
            date=date.today() - timedelta(days=15),
            defaults={"description": "Riego por goteo, 25 mm.",
                      "area_ha": Decimal("6.0"), "performed_by": operator},
        )
        FieldOperation.objects.get_or_create(
            cooperative=coop, crop=crop_almendro, operation_type=OperationType.PRUNING,
            date=date.today() - timedelta(days=50),
            defaults={"description": "Poda de formación del almendro.",
                      "area_ha": Decimal("5.5"), "performed_by": operator},
        )
        FieldOperation.objects.get_or_create(
            cooperative=coop, crop=crop_naranja, operation_type=OperationType.FERTILIZATION,
            date=date.today() - timedelta(days=20),
            defaults={"description": "Fertirrigación con NPK + microelementos.",
                      "area_ha": Decimal("2.8"), "performed_by": farmer2},
        )
        FieldOperation.objects.get_or_create(
            cooperative=coop, crop=crop_olivo_prev, operation_type=OperationType.HARVEST,
            date=date(2025, 1, 15),
            defaults={"description": "Recolección mecanizada de aceituna.",
                      "area_ha": Decimal("4.5"), "performed_by": farmer},
        )

        # Treatments (auto-deduct stock + safety-interval checks).
        if not Treatment.objects.filter(crop=crop_vid, product=azufre).exists():
            Treatment.objects.create(
                cooperative=coop, crop=crop_vid, product=azufre,
                date=date.today() - timedelta(days=8), dose=Decimal("4"),
                dose_unit="kg/ha", total_quantity=Decimal("8"),
                target_pest="Oídio (Erysiphe necator)", weather="Soleado, 24°C",
                applicator=tech,
            )
        if not Treatment.objects.filter(crop=crop_almendro, product=insecticida).exists():
            Treatment.objects.create(
                cooperative=coop, crop=crop_almendro, product=insecticida,
                date=date.today() - timedelta(days=6), dose=Decimal("0.4"),
                dose_unit="L/ha", total_quantity=Decimal("4"),
                target_pest="Avispilla del almendro", weather="Nublado, 20°C",
                applicator=tech,
            )
        # Applied close to harvest → safety interval NOT met → raises SAFETY alert.
        if not Treatment.objects.filter(crop=crop_naranja, product=acaricida).exists():
            Treatment.objects.create(
                cooperative=coop, crop=crop_naranja, product=acaricida,
                date=date.today() - timedelta(days=4), dose=Decimal("0.5"),
                dose_unit="L/ha", total_quantity=Decimal("3"),
                target_pest="Araña roja (Tetranychus urticae)", weather="Seco, 26°C",
                applicator=tech,
            )

        # Harvests (current + historical), with sale prices for income.
        HarvestRecord.objects.get_or_create(
            cooperative=coop, crop=crop_almendro, date=date.today() - timedelta(days=2),
            defaults={"quantity_kg": Decimal("7600"), "quality_grade": Decimal("23.00"),
                      "price_per_kg": Decimal("3.40"),
                      "notes": "Rendimiento en grano 23%. Calibre 14/16."},
        )
        HarvestRecord.objects.get_or_create(
            cooperative=coop, crop=crop_olivo_prev, date=date(2025, 1, 15),
            defaults={"quantity_kg": Decimal("14200"), "quality_grade": Decimal("20.80"),
                      "price_per_kg": Decimal("0.92"),
                      "notes": "Campaña 2024/2025 cerrada. Acidez 0,3º."},
        )

        # Manual cost entries (machinery, water, labor) on several crops.
        self._manual_cost(coop, crop_trigo, CostCategory.MACHINE, Decimal("850.00"),
                          "Cosechadora alquilada (8,2 ha)", days_ago=3)
        self._manual_cost(coop, crop_vid, CostCategory.WATER, Decimal("320.00"),
                          "Consumo de agua de riego (campaña)", days_ago=12)
        self._manual_cost(coop, crop_almendro, CostCategory.LABOR, Decimal("600.00"),
                          "Cuadrilla de recolección (jornales)", days_ago=2)
        self._manual_cost(coop, crop_naranja, CostCategory.ELECTRICITY, Decimal("180.00"),
                          "Bombeo de riego (electricidad)", days_ago=18)

        mem = MemoryService(coop)
        mem.remember(MemoryScope.USER, "Prefiere recibir avisos por SMS y en español.",
                     user=farmer, key="pref-comunicacion", importance=2)
        mem.remember(MemoryScope.PARCEL,
                     "Recinto Olivar Norte: histórico de repilo en otoños húmedos.",
                     parcel=parcel1, crop=crop_olivo, tags=["repilo", "olivar"],
                     importance=3)
        mem.remember(MemoryScope.GLOBAL,
                     "Campaña 2025/2026: alta presión de repilo en la comarca.",
                     tags=["tendencia", "repilo"], importance=3)
        mem.remember(MemoryScope.PARCEL,
                     "Viñedo Este: sensible a oídio; vigilar tras lluvias de primavera.",
                     parcel=parcel_vina, crop=crop_vid, tags=["oidio", "vid"],
                     importance=3)
        mem.remember(MemoryScope.PARCEL,
                     "Cítricos Bajo: respetar plazo de seguridad antes de recolección.",
                     parcel=parcel_citricos, crop=crop_naranja,
                     tags=["seguridad", "citricos"], importance=2)
        mem.remember(MemoryScope.USER, "Coordina la recolección con cuadrillas externas.",
                     user=farmer2, key="pref-recoleccion", importance=2)

        call_command("seed_agents", cooperative=coop.slug)

        # Set product prices and harvest price, then compute profitability.
        Product.objects.filter(pk=cobre.pk).update(unit_cost=Decimal("8.50"))
        Product.objects.filter(pk=herbicida.pk).update(unit_cost=Decimal("4.20"))
        Product.objects.filter(pk=abono.pk).update(unit_cost=Decimal("0.65"))
        Product.objects.filter(pk=insecticida.pk).update(unit_cost=Decimal("22.00"))
        Product.objects.filter(pk=acaricida.pk).update(unit_cost=Decimal("30.00"))
        Product.objects.filter(pk=foliar.pk).update(unit_cost=Decimal("6.80"))
        Product.objects.filter(pk=azufre.pk).update(unit_cost=Decimal("1.10"))
        Product.objects.filter(pk=semilla.pk).update(unit_cost=Decimal("3.20"))
        HarvestRecord.objects.filter(crop=crop_olivo, price_per_kg__isnull=True).update(
            price_per_kg=Decimal("0.95")
        )

        # (Re)impute costs for existing demo records and compute reports.
        for treatment in Treatment.objects.filter(cooperative=coop):
            impute_treatment_cost(treatment)
        for op in FieldOperation.objects.filter(cooperative=coop):
            if not Treatment.objects.filter(operation=op).exists():
                impute_operation_cost(op)
        for crop in Crop.objects.filter(cooperative=coop):
            compute_profitability(crop)

        # Default alert rules + an initial evaluation pass.
        ensure_default_rules(coop)
        evaluate_cooperative(coop)

        self.stdout.write(self.style.SUCCESS("\n=== Demo environment ready ==="))
        self.stdout.write(f"Admin login:    {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        self.stdout.write(f"Técnico login:  {TECH_EMAIL} / {DEMO_PASSWORD}")
        self.stdout.write(f"Agricultor:     {FARMER_EMAIL} / {DEMO_PASSWORD}")
        self.stdout.write(f"Operaria:       {OPERATOR_EMAIL} / {DEMO_PASSWORD}")
        self.stdout.write(f"Auditora:       {AUDITOR_EMAIL} / {DEMO_PASSWORD}")
        self.stdout.write(f"Agricultor 2:   {FARMER2_EMAIL} / {DEMO_PASSWORD}")
        self.stdout.write(f"Cooperative slug: {coop.slug}")

    # -- helpers ----------------------------------------------------------
    def _user(self, email, password, first, last, superuser=False):
        user = User.objects.filter(email=email).first()
        if user:
            return user
        if superuser:
            return User.objects.create_superuser(
                email=email, password=password, first_name=first, last_name=last
            )
        return User.objects.create_user(
            email=email, password=password, first_name=first, last_name=last
        )

    def _product(self, coop, name, category, ai, unit, safety, reorder):
        product, _ = Product.objects.get_or_create(
            cooperative=coop, name=name,
            defaults={
                "category": category, "active_ingredient": ai, "unit": unit,
                "safety_interval_days": safety, "reorder_level": Decimal(reorder),
            },
        )
        return product

    def _stock_in(self, coop, product, qty):
        if not product.movements.filter(movement_type=MovementType.IN).exists():
            batch = StockBatch.objects.create(
                cooperative=coop, product=product,
                lot=f"L-{product.name[:4].upper()}-2025",
                received_date=date.today() - timedelta(days=20),
                expiry_date=date.today() + timedelta(days=540),
            )
            StockMovement.objects.create(
                cooperative=coop, product=product, batch=batch,
                movement_type=MovementType.IN,
                quantity=Decimal(qty), reason="Stock inicial (demo)",
            )

    def _batch_in(self, coop, product, qty, lot, expiry_days=540, received_days=20):
        """Idempotent (by lot) batch + IN movement with a configurable expiry."""
        if StockBatch.objects.filter(cooperative=coop, product=product, lot=lot).exists():
            return
        expiry = (
            date.today() + timedelta(days=expiry_days)
            if expiry_days is not None
            else None
        )
        batch = StockBatch.objects.create(
            cooperative=coop, product=product, lot=lot,
            received_date=date.today() - timedelta(days=received_days),
            expiry_date=expiry,
        )
        StockMovement.objects.create(
            cooperative=coop, product=product, batch=batch,
            movement_type=MovementType.IN,
            quantity=Decimal(qty), reason="Entrada de stock (demo)",
        )

    def _manual_cost(self, coop, crop, category, amount, description, days_ago=0):
        CostEntry.objects.get_or_create(
            cooperative=coop, crop=crop, category=category,
            source=CostSource.MANUAL, description=description,
            defaults={"amount": amount,
                      "date": date.today() - timedelta(days=days_ago)},
        )
