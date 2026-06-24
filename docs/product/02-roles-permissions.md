# Roles, Permisos y Matriz de Acceso

Modelo de autorización **multi-tenant + por rol**. El rol es efectivo dentro de la
cooperativa activa (un mismo usuario puede tener roles distintos en cooperativas distintas).

---

## 1. Roles

| Rol         | Código       | Ámbito                     | Descripción                                                                                        |
| ----------- | ------------ | -------------------------- | -------------------------------------------------------------------------------------------------- |
| SuperAdmin  | `SUPERADMIN` | Plataforma (global)        | Opera el SaaS, soporte, gestión de tenants. No accede a datos agronómicos salvo soporte explícito. |
| Admin Coop. | `COOP_ADMIN` | Cooperativa (tenant)       | Control total de su cooperativa: socios, documentos, economía, comunicaciones.                     |
| Técnico     | `AGRONOMIST` | Cartera de agricultores    | Diagnóstico, recomendaciones, validación de cuadernos de su cartera.                               |
| Agricultor  | `FARMER`     | Sus explotaciones          | Gestiona sus fincas, cuaderno, inventario y costes.                                                |
| Operario    | `OPERATOR`   | Tareas asignadas           | Registra labores/tratamientos en campo; sin acceso económico.                                      |
| Auditor     | `AUDITOR`    | Solo lectura (cooperativa) | Verifica trazabilidad y cumplimiento; no modifica nada.                                            |

---

## 2. Principios de autorización

1. **Aislamiento por tenant**: ninguna query devuelve datos de otra cooperativa.
2. **Mínimo privilegio**: cada rol ve y hace solo lo necesario.
3. **Propiedad del dato**: el `FARMER` solo ve sus explotaciones; el `OPERATOR` solo lo
   asignado; el `AGRONOMIST` solo su cartera.
4. **Inmutabilidad para auditoría**: el `AUDITOR` nunca escribe.
5. **Acciones críticas con doble control**: aplicar fuera de plazo de seguridad, borrar un
   socio o cerrar campaña requieren rol elevado y quedan auditadas.

---

## 3. Matriz de permisos (CRUD + acciones)

> `C`=crear · `R`=leer · `U`=actualizar · `D`=borrar · `—`=sin acceso · `R*`=lectura limitada a su ámbito

| Recurso / Acción         | SUPERADMIN | COOP_ADMIN | AGRONOMIST | FARMER | OPERATOR | AUDITOR |
| ------------------------ | :--------: | :--------: | :--------: | :----: | :------: | :-----: |
| Cooperativa (config)     |    CRUD    |    R U     |     R      |   R    |    —     |    R    |
| Socios / miembros        |    CRUD    |    CRUD    |     R      |  R\*   |    —     |    R    |
| Equipos                  |    CRUD    |    CRUD    |    R U     | CRU\*  |    —     |    R    |
| Fincas / Parcelas        |    R\*     |     R      |    R U     | CRUD\* |   R\*    |    R    |
| Cultivos / Campañas      |    R\*     |     R      |    R U     | CRUD\* |   R\*    |    R    |
| Cuaderno de campo        |    R\*     |     R      |    CRU     | CRUD\* |  C R\*   |    R    |
| Tratamientos             |    R\*     |     R      |    CRU     | CRUD\* |  C R\*   |    R    |
| Trazabilidad             |    R\*     |     R      |     R      |  R\*   |   R\*    |    R    |
| Inventario               |    R\*     |    CRUD    |    R U     | CRUD\* |   R\*    |    R    |
| Maquinaria               |    R\*     |    CRUD    |     R      | CRUD\* |  R U\*   |    R    |
| Costes / Rentabilidad    |    R\*     |    CRUD    |     R      |  R\*   |    —     |    R    |
| Agentes IA (chat)        |     R      |    C R     |    C R     |  C R   |   C R    |    —    |
| Memoria                  |    R\*     |     R      |    R U     |  R\*   |    —     |    R    |
| Alertas (reglas)         |    CRUD    |    CRUD    |    R U     | R U\*  |   R\*    |    R    |
| Analítica / Dashboards   |     R      |     R      |     R      |  R\*   |    —     |    R    |
| Documentación            |    R\*     |    CRUD    |    CRU     | CRUD\* |   R\*    |    R    |
| API Keys / Integraciones |    CRUD    |    CRUD    |     —      |  R\*   |    —     |    —    |
| Auditoría / logs         |     R      |     R      |     —      |   —    |    —     |    R    |

---

## 4. Acciones especiales (gated)

| Acción                                  | Quién                         | Control adicional                   |
| --------------------------------------- | ----------------------------- | ----------------------------------- |
| Aplicar tratamiento fuera de plazo      | AGRONOMIST / COOP_ADMIN       | Confirmación + motivo + auditoría   |
| Cerrar campaña                          | COOP_ADMIN / FARMER (suya)    | Recalcula costes; irreversible      |
| Eliminar socio                          | COOP_ADMIN                    | Baja lógica + auditoría             |
| Exportar cuaderno oficial               | FARMER / AGRONOMIST / AUDITOR | Marca de tiempo + hash              |
| Activar MFA obligatorio                 | COOP_ADMIN / SUPERADMIN       | Afecta a roles admin del tenant     |
| Ejecutar agente con acción de escritura | rol del recurso afectado      | Recomendación → confirmación humana |

---

## 5. Modelo técnico de permisos

- Resolución de tenant por cabecera `X-Cooperative` → `CooperativeMembership` activo.
- Permiso base: `IsCooperativeMember`; por rol: `HasCooperativeRole` con `required_roles`.
- Scoping de propiedad en `get_queryset()` (p. ej. `FARMER` filtra por `owner`).
- Toda acción gated emite un `AuditEvent` con actor, recurso, motivo y timestamp.
