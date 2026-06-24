# AgroControl OS

Sistema operativo SaaS para cooperativas agrícolas y agricultores. Multi-tenant, con
cuaderno de campo digital, trazabilidad, control de stock fitosanitario y un sistema
de **agentes de IA** con memoria persistente en 3 niveles.

## Stack

| Capa          | Tecnología                                   |
| ------------- | -------------------------------------------- |
| Backend       | Python 3.12, Django 5, Django REST Framework |
| Async         | Celery + Redis                               |
| Base de datos | PostgreSQL 16                                |
| IA            | OpenAI (tool calling) + framework de agentes |
| Frontend      | Nuxt 3, Vue 3, TailwindCSS, Pinia            |
| Infra         | Docker + Docker Compose                      |

## Arranque rápido (Docker)

Todo se ejecuta en contenedores. **Mismo motor (PostgreSQL) en todos los entornos.**

```bash
docker compose up --build
```

Al arrancar, el backend aplica migraciones y crea automáticamente los datos demo
(usuarios, cooperativa, parcelas, productos y los 4 agentes IA).

| Servicio | URL                                          |
| -------- | -------------------------------------------- |
| Frontend | http://localhost:3001/                       |
| API      | http://localhost:8001/api/v1/                |
| Admin    | http://localhost:8001/admin/                 |
| Docs API | http://localhost:8001/api/schema/swagger-ui/ |

> Los puertos de host son 8001/3001/5433/6380 para no chocar con otros proyectos
> que usen 8000/3000/5432/6379.

### Credenciales demo

| Rol               | Email                       | Password    |
| ----------------- | --------------------------- | ----------- |
| Admin cooperativa | `admin@agrocontrol.os`      | `Agro1234!` |
| Técnico agrónomo  | `tecnico@agrocontrol.os`    | `Agro1234!` |
| Agricultor        | `agricultor@agrocontrol.os` | `Agro1234!` |

Cooperativa: `cooperativa-demo` (cabecera `X-Cooperative`).

Comandos útiles:

```bash
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py seed_demo        # re-seed (idempotente)
docker compose logs -f backend
```

## Estructura del monorepo

```
AgroControl/
├── backend/          # Django + DRF + Celery
├── frontend/         # Nuxt 3 + Tailwind
├── docs/             # ARCHITECTURE.md, API.md
└── docker-compose.yml
```

## Fases de construcción

1. **Fase 1** — Arquitectura, schema, auth, cooperativas (multi-tenant) ✅
2. **Fase 2** — Parcelas, cultivos, cuaderno de campo, stock ✅
3. **Fase 3** — Agentes IA + memoria persistente ✅
4. **Fase 4** — Frontend completo (scaffold incluido) 🚧
5. **Fase 5** — Automatizaciones y optimización 🚧

Ver [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) y [docs/API.md](docs/API.md).
