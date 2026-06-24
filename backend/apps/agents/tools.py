"""Tool registry for AI agents (OpenAI function-calling compatible).

Register a tool with ``@register_tool``. Each tool receives a ``ToolContext``
(cooperative, user, role, memory service) plus its own JSON arguments and returns
a JSON-serializable result. The registry exposes ``openai_schema()`` to advertise
tools to the model and ``execute()`` to run them.
"""
from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Callable

from apps.memory.services import MemoryService


@dataclass
class ToolContext:
    cooperative: Any
    user: Any
    role: str | None

    @property
    def memory(self) -> MemoryService:
        return MemoryService(self.cooperative)


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    func: Callable

    def to_openai(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


_REGISTRY: dict[str, Tool] = {}


def register_tool(name: str, description: str, parameters: dict | None = None):
    def decorator(func: Callable) -> Callable:
        _REGISTRY[name] = Tool(
            name=name,
            description=description,
            parameters=parameters or {"type": "object", "properties": {}},
            func=func,
        )
        return func

    return decorator


def get_tool(name: str) -> Tool | None:
    return _REGISTRY.get(name)


def openai_schema(names: list[str]) -> list[dict]:
    return [_REGISTRY[n].to_openai() for n in names if n in _REGISTRY]


def execute(name: str, ctx: ToolContext, **kwargs) -> Any:
    tool = _REGISTRY.get(name)
    if not tool:
        return {"error": f"Unknown tool '{name}'."}
    sig = inspect.signature(tool.func)
    accepted = {k: v for k, v in kwargs.items() if k in sig.parameters}
    return tool.func(ctx, **accepted)


def all_tool_names() -> list[str]:
    return list(_REGISTRY.keys())


# ---------------------------------------------------------------------------
# Built-in tools
# ---------------------------------------------------------------------------

@register_tool(
    "list_parcels",
    "Lista las parcelas de la cooperativa con su superficie y cultivo activo.",
    {"type": "object", "properties": {
        "limit": {"type": "integer", "description": "Máx. parcelas a devolver."}
    }},
)
def list_parcels(ctx: ToolContext, limit: int = 20):
    from apps.farms.models import Parcel

    parcels = Parcel.objects.filter(
        cooperative=ctx.cooperative, is_active=True
    ).prefetch_related("crops")[:limit]
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "area_ha": float(p.area_ha),
            "soil_type": p.soil_type,
            "active_crops": [
                f"{c.species} {c.variety}".strip()
                for c in p.crops.all()
                if c.status in ("PLANNED", "GROWING")
            ],
        }
        for p in parcels
    ]


@register_tool(
    "get_crop_status",
    "Devuelve el estado y los últimos tratamientos de un cultivo por su id.",
    {"type": "object", "properties": {
        "crop_id": {"type": "string", "description": "UUID del cultivo."}
    }, "required": ["crop_id"]},
)
def get_crop_status(ctx: ToolContext, crop_id: str):
    from apps.farms.models import Crop

    crop = Crop.objects.filter(cooperative=ctx.cooperative, id=crop_id).first()
    if not crop:
        return {"error": "Cultivo no encontrado."}
    treatments = crop.treatments.order_by("-date")[:5]
    return {
        "species": crop.species,
        "variety": crop.variety,
        "campaign": crop.campaign,
        "status": crop.status,
        "parcel": crop.parcel.name,
        "recent_treatments": [
            {"product": t.product.name, "date": str(t.date), "pest": t.target_pest}
            for t in treatments
        ],
    }


@register_tool(
    "check_product_stock",
    "Comprueba el stock disponible de un producto fitosanitario por nombre.",
    {"type": "object", "properties": {
        "name": {"type": "string", "description": "Nombre (parcial) del producto."}
    }, "required": ["name"]},
)
def check_product_stock(ctx: ToolContext, name: str):
    from apps.inventory.models import Product

    products = Product.objects.filter(
        cooperative=ctx.cooperative, name__icontains=name
    )[:10]
    if not products:
        return {"error": "No se encontraron productos."}
    return [
        {
            "name": p.name,
            "current_stock": float(p.current_stock),
            "unit": p.unit,
            "needs_reorder": p.needs_reorder,
            "safety_interval_days": p.safety_interval_days,
        }
        for p in products
    ]


@register_tool(
    "recall_memory",
    "Recupera memoria persistente relevante (usuario, parcela o global).",
    {"type": "object", "properties": {
        "scope": {"type": "string", "enum": ["USER", "PARCEL", "GLOBAL"]},
        "query": {"type": "string", "description": "Texto a buscar."},
    }},
)
def recall_memory(ctx: ToolContext, scope: str = None, query: str = ""):
    entries = ctx.memory.recall(scope=scope, query=query, limit=8)
    return [{"scope": e.scope, "content": e.content, "tags": e.tags} for e in entries]


@register_tool(
    "save_memory",
    "Guarda una conclusión o aprendizaje en la memoria persistente.",
    {"type": "object", "properties": {
        "scope": {"type": "string", "enum": ["USER", "PARCEL", "GLOBAL"]},
        "content": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
    }, "required": ["scope", "content"]},
)
def save_memory(ctx: ToolContext, scope: str, content: str, tags: list = None):
    entry = ctx.memory.remember(
        scope=scope,
        content=content,
        user=ctx.user if scope == "USER" else None,
        tags=tags or [],
        source="agent",
        importance=2,
    )
    return {"saved": True, "id": str(entry.id)}


@register_tool(
    "list_low_stock",
    "Lista los productos que están por debajo del nivel de reposición.",
)
def list_low_stock(ctx: ToolContext):
    from apps.inventory.models import Product

    products = Product.objects.filter(cooperative=ctx.cooperative)
    low = [p for p in products if p.needs_reorder]
    return [
        {"name": p.name, "current_stock": float(p.current_stock), "unit": p.unit}
        for p in low
    ]
