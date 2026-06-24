"""Seed the four built-in agents for a cooperative.

Usage:
    python manage.py seed_agents --cooperative <slug>
"""
from django.core.management.base import BaseCommand, CommandError

from apps.agents.models import Agent, AgentType
from apps.tenants.models import Cooperative

AGENT_BLUEPRINTS = [
    {
        "agent_type": AgentType.AGRONOMIST,
        "name": "Agente Agrónomo",
        "purpose": "Diagnóstico de cultivos, recomendaciones agrícolas e interpretación de datos de campo.",
        "system_prompt": (
            "Eres un ingeniero agrónomo experto. Diagnosticas problemas de cultivos, "
            "recomiendas tratamientos respetando dosis y plazos de seguridad, y siempre "
            "justificas tus recomendaciones con datos. Si faltan datos, consúltalos con tus herramientas."
        ),
        "skills": [
            "Diagnóstico de cultivos",
            "Recomendaciones agrícolas",
            "Interpretación de datos de campo",
        ],
        "tools": ["list_parcels", "get_crop_status", "check_product_stock", "recall_memory", "save_memory"],
        "listens_to": ["treatment_registered"],
    },
    {
        "agent_type": AgentType.ADMIN,
        "name": "Agente Administrativo",
        "purpose": "Generación de informes, gestión del cuaderno de campo y cumplimiento normativo.",
        "system_prompt": (
            "Eres un asistente administrativo agrícola. Generas informes claros del cuaderno "
            "de campo, verificas el cumplimiento normativo (registros de tratamientos, plazos "
            "de seguridad) y resumes la actividad. Sé preciso y formal."
        ),
        "skills": ["Generación de informes", "Gestión de cuaderno de campo", "Cumplimiento normativo"],
        "tools": ["get_crop_status", "check_product_stock", "recall_memory", "save_memory"],
        "listens_to": [],
    },
    {
        "agent_type": AgentType.COOPERATIVE,
        "name": "Agente Cooperativa",
        "purpose": "Visión global de la producción, control de agricultores, alertas y planificación.",
        "system_prompt": (
            "Eres el agente de dirección de la cooperativa. Ofreces una visión global de la "
            "producción, detectas anomalías y riesgos (stock bajo, tratamientos fuera de plazo), "
            "y propones planificación. Piensa en agregados y tendencias."
        ),
        "skills": ["Vista global de producción", "Control de agricultores", "Alertas y planificación"],
        "tools": ["list_parcels", "list_low_stock", "recall_memory", "save_memory"],
        "listens_to": ["treatment_registered"],
    },
    {
        "agent_type": AgentType.SUPPORT,
        "name": "Agente de Soporte",
        "purpose": "Responde dudas de agricultores con acceso a su historial y memoria.",
        "system_prompt": (
            "Eres un agente de soporte cercano y claro para agricultores. Respondes dudas "
            "usando el historial y la memoria del usuario. Si no sabes algo, lo dices y derivas "
            "al agente adecuado."
        ),
        "skills": ["Atención al agricultor", "Acceso a historial y memoria"],
        "tools": ["get_crop_status", "check_product_stock", "recall_memory"],
        "listens_to": [],
    },
]


class Command(BaseCommand):
    help = "Create the four built-in AI agents for a cooperative."

    def add_arguments(self, parser):
        parser.add_argument("--cooperative", required=True, help="Cooperative slug.")
        parser.add_argument("--model", default="gpt-4o-mini")

    def handle(self, *args, **options):
        slug = options["cooperative"]
        try:
            coop = Cooperative.objects.get(slug=slug)
        except Cooperative.DoesNotExist as exc:
            raise CommandError(f"Cooperative '{slug}' not found.") from exc

        created = 0
        for bp in AGENT_BLUEPRINTS:
            _, was_created = Agent.objects.update_or_create(
                cooperative=coop,
                agent_type=bp["agent_type"],
                defaults={**bp, "model": options["model"]},
            )
            created += int(was_created)
            self.stdout.write(f"  {'created' if was_created else 'updated'}: {bp['name']}")

        self.stdout.write(
            self.style.SUCCESS(f"Done. {created} agents created for '{coop.name}'.")
        )
