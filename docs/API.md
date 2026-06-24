# API REST — AgroControl OS

Base URL: `/api/v1/` · Auth: `Authorization: Bearer <access>` · Tenant: `X-Cooperative: <slug>`

Interactive docs (Swagger UI): `/api/schema/swagger-ui/`

## Autenticación

| Método | Endpoint               | Descripción                 | Auth |
| ------ | ---------------------- | --------------------------- | ---- |
| POST   | `/auth/register/`      | Alta de usuario             | No   |
| POST   | `/auth/token/`         | Login → `{access, refresh}` | No   |
| POST   | `/auth/token/refresh/` | Renueva el access token     | No   |
| GET    | `/auth/me/`            | Perfil del usuario actual   | Sí   |
| PATCH  | `/auth/me/`            | Actualiza perfil            | Sí   |

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@coop.com","password":"secret123"}'
```

## Cooperativas (multi-tenant) y miembros

| Método    | Endpoint              | Rol        | Descripción                           |
| --------- | --------------------- | ---------- | ------------------------------------- |
| GET/POST  | `/cooperatives/`      | cualquiera | Lista/crea cooperativas (crear→admin) |
| GET/PATCH | `/cooperatives/{id}/` | miembro    | Detalle/actualización                 |
| GET       | `/members/`           | COOP_ADMIN | Miembros de la cooperativa activa     |
| POST      | `/members/invite/`    | COOP_ADMIN | `{email, role}` invita a un usuario   |

## Explotaciones, parcelas y cultivos

| Método           | Endpoint       | Descripción                              |
| ---------------- | -------------- | ---------------------------------------- |
| GET/POST         | `/farms/`      | Explotaciones (farmer ve solo las suyas) |
| GET/PATCH/DELETE | `/farms/{id}/` |                                          |
| GET/POST         | `/parcels/`    | Parcelas/recintos SIGPAC                 |
| GET/POST         | `/crops/`      | Cultivos por campaña                     |

Filtros: `?farm=`, `?status=`, `?campaign=`, `?species=`, `?search=`.

## Cuaderno de campo y tratamientos

| Método   | Endpoint       | Descripción                                              |
| -------- | -------------- | -------------------------------------------------------- |
| GET/POST | `/operations/` | Entradas del cuaderno (siembra, riego, cosecha…)         |
| GET/POST | `/treatments/` | Tratamientos fitosanitarios (descuenta stock automático) |

Al crear un `treatment` con `total_quantity`, el sistema:

1. Crea un `StockMovement` de salida.
2. Emite `treatment_registered`, que dispara los agentes suscritos.

## Inventario / stock

| Método   | Endpoint               | Descripción                          |
| -------- | ---------------------- | ------------------------------------ |
| GET/POST | `/products/`           | Productos fitosanitarios             |
| GET      | `/products/low_stock/` | Productos bajo nivel de reposición   |
| GET/POST | `/stock-movements/`    | Movimientos de stock (IN/OUT/ADJUST) |

## Memoria (3 niveles)

| Método   | Endpoint     | Descripción                      |
| -------- | ------------ | -------------------------------- | ------ | -------- |
| GET/POST | `/memories/` | Entradas de memoria (`scope=USER | PARCEL | GLOBAL`) |

Filtros: `?scope=`, `?user=`, `?parcel=`, `?crop=`, `?source=`, `?search=`.

## Agentes IA

| Método   | Endpoint             | Descripción                                 |
| -------- | -------------------- | ------------------------------------------- |
| GET/POST | `/agents/`           | Agentes de la cooperativa                   |
| POST     | `/agents/{id}/chat/` | `{message, async_run?}` → ejecuta el agente |
| GET      | `/agent-runs/`       | Historial de ejecuciones (con transcript)   |
| GET      | `/agent-runs/{id}/`  | Detalle de una ejecución + mensajes/tools   |

```bash
# Hablar con un agente
curl -X POST http://localhost:8000/api/v1/agents/<agent_id>/chat/ \
  -H "Authorization: Bearer $ACCESS" \
  -H "X-Cooperative: mi-cooperativa" \
  -H "Content-Type: application/json" \
  -d '{"message":"¿Qué productos tengo bajo mínimos?"}'
```

Respuesta (resumen):

```json
{
  "id": "…",
  "agent_name": "Agente Cooperativa",
  "status": "COMPLETED",
  "output_text": "Tienes 2 productos bajo mínimos: …",
  "messages": [
    { "role": "system", "content": "…" },
    { "role": "user", "content": "¿Qué productos…" },
    { "role": "tool", "tool_name": "list_low_stock", "content": "[…]" },
    { "role": "assistant", "content": "Tienes 2 productos…" }
  ]
}
```

## Bootstrap rápido (datos de ejemplo)

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
# Crea una cooperativa vía API (POST /cooperatives/) y luego:
docker compose exec backend python manage.py seed_agents --cooperative <slug>
```
