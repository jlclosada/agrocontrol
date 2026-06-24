# Arquitectura — AgroControl OS

## 1. Visión general

AgroControl OS es una plataforma SaaS **multi-tenant** donde cada **Cooperativa** es un
tenant lógico. Los datos están aislados por cooperativa mediante un campo
`cooperative_id` presente en todos los modelos de dominio y forzado a nivel de queryset
(row-level scoping) más permisos por rol.

```
                       ┌─────────────────────────────────────────┐
                       │                Frontend                  │
                       │        Nuxt 3 + Vue 3 + Tailwind         │
                       └───────────────────┬─────────────────────┘
                                           │ HTTPS / JWT
                       ┌───────────────────▼─────────────────────┐
                       │              API REST (DRF)              │
                       │  accounts · tenants · farms · fieldbook  │
                       │      inventory · memory · agents         │
                       └───────┬───────────────────────┬─────────┘
                               │                       │
                   ┌───────────▼──────┐      ┌─────────▼─────────┐
                   │   PostgreSQL     │      │   Celery workers  │
                   │  (datos + memo)  │      │ (tareas async IA) │
                   └──────────────────┘      └─────────┬─────────┘
                               ▲                       │
                               │                ┌──────▼──────┐
                          ┌────┴─────┐          │    Redis    │
                          │  Memory  │◄─────────┤ broker+cache│
                          │  Service │          └─────────────┘
                          └────┬─────┘
                               │
                       ┌───────▼────────┐
                       │  Agent Runtime │──► OpenAI (tool calling)
                       └────────────────┘
```

## 2. Multi-tenancy

- **Estrategia:** tenant compartido (shared DB, shared schema) con columna
  discriminadora `cooperative`.
- Cada request autenticado resuelve la **membresía activa** del usuario
  (`CooperativeMembership`) y expone `request.cooperative` y `request.role`.
- Los `ModelViewSet` heredan de `TenantScopedViewSet`, que filtra automáticamente
  `get_queryset()` por `cooperative` y asigna el tenant en `perform_create()`.

## 3. Roles y permisos

| Rol               | Código       | Capacidades                                         |
| ----------------- | ------------ | --------------------------------------------------- |
| Admin cooperativa | `COOP_ADMIN` | Gestión total de la cooperativa, miembros, informes |
| Técnico agrónomo  | `AGRONOMIST` | Diagnósticos, tratamientos, validación de cuadernos |
| Agricultor        | `FARMER`     | Sus parcelas, su cuaderno de campo, su stock        |

Permisos implementados en `apps/tenants/permissions.py` (`HasCooperativeRole`).

## 4. Modelo de datos (resumen)

```
User ──< CooperativeMembership >── Cooperative
                                      │
                                      ├──< Farm (explotación)
                                      │      └──< Parcel (parcela/recinto SIGPAC)
                                      │             └──< Crop (cultivo por campaña)
                                      │                    ├──< FieldOperation (cuaderno)
                                      │                    └──< Treatment ──> Product
                                      │
                                      ├──< Product (fitosanitario) ──< StockMovement
                                      │
                                      ├──< Agent ──< AgentRun ──< AgentMessage
                                      │
                                      └──< MemoryEntry (scope: USER|PARCEL|GLOBAL)
```

Detalle completo de campos en `docs/API.md` y en los `models.py` de cada app.

## 5. Sistema de memoria (3 niveles)

Implementado en `apps/memory`.

| Nivel   | Scope    | Clave                      | Uso                                      |
| ------- | -------- | -------------------------- | ---------------------------------------- |
| Usuario | `USER`   | `user_id`                  | Preferencias, historial de interacciones |
| Parcela | `PARCEL` | `parcel_id` / `crop_id`    | Estado del cultivo, incidencias, suelo   |
| Global  | `GLOBAL` | `cooperative_id` o sistema | Tendencias, aprendizajes agregados       |

Cada `MemoryEntry` guarda `content` (texto), `data` (JSON), `tags`, `embedding`
(opcional para búsqueda semántica) y `importance`. El `MemoryService` ofrece
`remember()`, `recall()` y `summarize()` consumibles por los agentes vía herramientas.

## 6. Framework de agentes

Implementado en `apps/agents`.

- **Agent**: configuración persistente (nombre, propósito, modelo, skills, system prompt).
- **Tool registry**: herramientas Python registradas (`@register_tool`) expuestas a la IA
  vía _function calling_.
- **AgentRuntime**: orquesta el bucle ReAct (mensaje → llamada de modelo → ejecución de
  herramientas → respuesta), persiste `AgentRun` y `AgentMessage`, integra memoria.
- **Eventos**: los agentes pueden suscribirse a eventos de dominio (`signals`) y ejecutarse
  de forma asíncrona con Celery.

Agentes iniciales: **Agrónomo**, **Administrativo**, **Cooperativa**, **Soporte**.

## 7. Seguridad

- JWT (access + refresh) con `djangorestframework-simplejwt`.
- Scoping por tenant en todas las queries (evita IDOR / fuga entre cooperativas).
- Permisos por rol en endpoints sensibles.
- Variables secretas en `.env` (nunca en el repo).
- CORS restringido al dominio del frontend.

## 8. Escalabilidad

- Stateless API → escalado horizontal detrás de balanceador.
- Celery workers independientes para carga de IA.
- Redis como caché de memoria temporal y broker.
- Índices en `cooperative`, claves foráneas y `tags` (GIN) para consultas frecuentes.
- Preparado para `pgvector` (embeddings) cuando se active búsqueda semántica.
