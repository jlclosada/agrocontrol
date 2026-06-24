# Requisitos Funcionales y No Funcionales

---

## 1. Requisitos Funcionales (RF)

Codificación: `RF-<módulo>-<n>`. Prioridad MoSCoW. Fase objetivo (ver
[07-roadmap.md](07-roadmap.md)).

### Usuarios y Seguridad (USR)

| ID       | Requisito                                                   | Prioridad | Fase |
| -------- | ----------------------------------------------------------- | --------- | ---- |
| RF-USR-1 | Registro/invitación de usuarios con verificación de email   | Must      | MVP  |
| RF-USR-2 | Autenticación JWT con refresh y expiración configurable     | Must      | MVP  |
| RF-USR-3 | Un usuario pertenece a varias cooperativas con rol distinto | Must      | MVP  |
| RF-USR-4 | Gestión de roles (6 roles) y permisos por recurso           | Must      | MVP  |
| RF-USR-5 | MFA (TOTP/SMS) obligatorio configurable por cooperativa     | Should    | V1   |
| RF-USR-6 | Recuperación de contraseña por email                        | Must      | MVP  |
| RF-USR-7 | Auditoría de accesos e inicios de sesión                    | Should    | V1   |

### Cooperativas y Multi-tenant (COOP)

| ID        | Requisito                                           | Prioridad | Fase |
| --------- | --------------------------------------------------- | --------- | ---- |
| RF-COOP-1 | Aislamiento total de datos por cooperativa (tenant) | Must      | MVP  |
| RF-COOP-2 | Resolución de tenant por cabecera `X-Cooperative`   | Must      | MVP  |
| RF-COOP-3 | Alta/baja de cooperativas por SUPERADMIN            | Must      | MVP  |
| RF-COOP-4 | Comunicados (broadcast) a miembros                  | Could     | V2   |

### Explotaciones (FARM)

| ID        | Requisito                                       | Prioridad | Fase |
| --------- | ----------------------------------------------- | --------- | ---- |
| RF-FARM-1 | CRUD de fincas, parcelas, sectores y cultivos   | Must      | MVP  |
| RF-FARM-2 | Geolocalización de parcela (lat/lon + polígono) | Should    | V1   |
| RF-FARM-3 | Referencia SIGPAC en parcela                    | Should    | V1   |
| RF-FARM-4 | Campañas agrícolas que agrupan cultivos         | Should    | V1   |
| RF-FARM-5 | Registro de cosechas con calidad y rendimiento  | Should    | V1   |

### Cuaderno de Campo (FIELD)

| ID         | Requisito                                                            | Prioridad | Fase |
| ---------- | -------------------------------------------------------------------- | --------- | ---- |
| RF-FIELD-1 | Registrar operaciones de campo por cultivo                           | Must      | MVP  |
| RF-FIELD-2 | Tipos especializados: tratamiento, abonado, riego, incidencia, labor | Must      | MVP  |
| RF-FIELD-3 | Validar plazo de seguridad en tratamientos                           | Must      | V1   |
| RF-FIELD-4 | Exportar cuaderno oficial (PDF) conforme a normativa                 | Should    | V1   |
| RF-FIELD-5 | Registro offline y sincronización posterior                          | Could     | V2   |

### Trazabilidad (TRACE)

| ID         | Requisito                                                | Prioridad | Fase |
| ---------- | -------------------------------------------------------- | --------- | ---- |
| RF-TRACE-1 | Generar evento append-only por cada escritura de dominio | Must      | V1   |
| RF-TRACE-2 | Encadenamiento por hash (integridad verificable)         | Should    | V1   |
| RF-TRACE-3 | Consulta de historia completa de un lote/cultivo         | Should    | V1   |
| RF-TRACE-4 | Exportar dossier de trazabilidad para auditoría          | Should    | V2   |

### Inventario (INV)

| ID       | Requisito                                              | Prioridad | Fase |
| -------- | ------------------------------------------------------ | --------- | ---- |
| RF-INV-1 | Catálogo de productos fitosanitarios y fertilizantes   | Must      | MVP  |
| RF-INV-2 | Movimientos de stock (entrada/salida/ajuste)           | Must      | MVP  |
| RF-INV-3 | Descuento automático de stock al registrar tratamiento | Must      | V1   |
| RF-INV-4 | Gestión de lotes y caducidad (FEFO)                    | Should    | V1   |
| RF-INV-5 | Alertas de stock mínimo y caducidad                    | Should    | V1   |

### Maquinaria (MACH)

| ID        | Requisito                                | Prioridad | Fase |
| --------- | ---------------------------------------- | --------- | ---- |
| RF-MACH-1 | Inventario de maquinaria con coste/hora  | Should    | V1   |
| RF-MACH-2 | Registro de uso e imputación a cultivo   | Should    | V1   |
| RF-MACH-3 | Mantenimientos preventivos y correctivos | Could     | V2   |

### Costes y Rentabilidad (COST)

| ID        | Requisito                                                | Prioridad | Fase |
| --------- | -------------------------------------------------------- | --------- | ---- |
| RF-COST-1 | Imputación automática de costes (producto/labor/máquina) | Should    | V1   |
| RF-COST-2 | Cálculo de coste/ha y rentabilidad por cultivo           | Should    | V1   |
| RF-COST-3 | Comparativa entre campañas                               | Could     | V2   |

### Inteligencia Agrícola (AI)

| ID      | Requisito                                                  | Prioridad | Fase |
| ------- | ---------------------------------------------------------- | --------- | ---- |
| RF-AI-1 | Agente agrónomo conversacional con contexto de explotación | Must      | V1   |
| RF-AI-2 | Registro de runs, mensajes e invocaciones de herramientas  | Must      | V1   |
| RF-AI-3 | Detección de plagas por imagen                             | Should    | V2   |
| RF-AI-4 | Modo offline / fallback determinista sin API externa       | Must      | MVP  |
| RF-AI-5 | Agentes reactivos a eventos (`listens_to`)                 | Should    | V2   |

### Memoria (MEM)

| ID       | Requisito                                     | Prioridad | Fase |
| -------- | --------------------------------------------- | --------- | ---- |
| RF-MEM-1 | Memoria en 3 niveles (usuario/parcela/global) | Must      | V1   |
| RF-MEM-2 | Recuperación por relevancia y etiquetas       | Must      | V1   |
| RF-MEM-3 | Resumen/consolidación periódica de memoria    | Could     | V2   |

### Alertas (ALERT)

| ID         | Requisito                                    | Prioridad | Fase |
| ---------- | -------------------------------------------- | --------- | ---- |
| RF-ALERT-1 | Reglas configurables por disparador          | Should    | V1   |
| RF-ALERT-2 | Entrega multicanal (email/SMS/WhatsApp/push) | Should    | V2   |
| RF-ALERT-3 | Acuse de recibo y escalado                   | Could     | V2   |

### Analítica (ANALYTICS)

| ID      | Requisito                                 | Prioridad | Fase |
| ------- | ----------------------------------------- | --------- | ---- |
| RF-AN-1 | Dashboards por rol con KPIs clave         | Should    | V1   |
| RF-AN-2 | Exportación CSV/Excel                     | Should    | V1   |
| RF-AN-3 | Cuadro de mando de cooperativa (agregado) | Could     | V2   |

### Documentación (DOC)

| ID       | Requisito                                           | Prioridad | Fase |
| -------- | --------------------------------------------------- | --------- | ---- |
| RF-DOC-1 | Almacenamiento de documentos vinculados a entidades | Could     | V2   |
| RF-DOC-2 | OCR de facturas/certificados                        | Could     | V3   |

### Integraciones (INT)

| ID       | Requisito                              | Prioridad | Fase |
| -------- | -------------------------------------- | --------- | ---- |
| RF-INT-1 | API REST documentada (OpenAPI)         | Must      | MVP  |
| RF-INT-2 | API keys y webhooks por cooperativa    | Should    | V2   |
| RF-INT-3 | Ingesta IoT/meteo/satélite por parcela | Could     | V3   |
| RF-INT-4 | Conector WhatsApp Business             | Could     | V3   |

---

## 2. Requisitos No Funcionales (RNF)

### Rendimiento y Escalabilidad

- **RNF-PERF-1**: P95 de respuesta API < 300 ms en operaciones de lectura estándar.
- **RNF-PERF-2**: Tareas pesadas (IA, OCR, informes) ejecutadas asíncronamente vía Celery.
- **RNF-PERF-3**: Arquitectura stateless en backend → escalado horizontal.
- **RNF-PERF-4**: Paginación obligatoria en todos los listados (límite por defecto 25).

### Seguridad

- **RNF-SEC-1**: Autenticación JWT, contraseñas con hashing fuerte (PBKDF2/Argon2).
- **RNF-SEC-2**: Autorización por rol y aislamiento de tenant en todas las consultas.
- **RNF-SEC-3**: Cifrado TLS en tránsito; secretos fuera del código (variables de entorno).
- **RNF-SEC-4**: Protección OWASP Top 10 (inyección, XSS, CSRF, etc.).
- **RNF-SEC-5**: Rate limiting y bloqueo por fuerza bruta en login.
- **RNF-SEC-6**: Registros de auditoría inmutables para acciones sensibles.

### Disponibilidad y Fiabilidad

- **RNF-AVAIL-1**: Objetivo de disponibilidad 99,5% (V1) → 99,9% (Enterprise).
- **RNF-AVAIL-2**: Backups diarios de base de datos con retención ≥ 30 días.
- **RNF-AVAIL-3**: Idempotencia en seed/migraciones y reintentos en tareas Celery.

### Mantenibilidad y Calidad

- **RNF-MAINT-1**: Cobertura de tests ≥ 80% en lógica de dominio crítica.
- **RNF-MAINT-2**: Configuración por entornos vía settings split (base/dev/prod).
- **RNF-MAINT-3**: Migraciones versionadas y revisables.
- **RNF-MAINT-4**: Documentación OpenAPI autogenerada y al día.

### Portabilidad y Despliegue

- **RNF-DEPLOY-1**: Todos los entornos idénticos (PostgreSQL en local y producción).
- **RNF-DEPLOY-2**: Despliegue reproducible vía Docker Compose / contenedores.
- **RNF-DEPLOY-3**: Variables de entorno para toda configuración.

### Usabilidad y Accesibilidad

- **RNF-UX-1**: Interfaz responsive (móvil-first para agricultores en campo).
- **RNF-UX-2**: Cumplimiento WCAG 2.1 AA.
- **RNF-UX-3**: Internacionalización (i18n) y soporte multi-idioma.
- **RNF-UX-4**: Tiempos de carga percibidos < 2 s con estados de carga claros.

### Observabilidad

- **RNF-OBS-1**: Logs estructurados centralizados.
- **RNF-OBS-2**: Métricas de API, colas Celery y uso de agentes IA.
- **RNF-OBS-3**: Trazas de errores con alertado.

### Cumplimiento Normativo

- **RNF-COMP-1**: RGPD (consentimiento, derecho al olvido, portabilidad de datos).
- **RNF-COMP-2**: Cuaderno de campo conforme a normativa fitosanitaria vigente.
- **RNF-COMP-3**: Trazabilidad conforme a requisitos de certificación agroalimentaria.

### IA Responsable

- **RNF-AI-1**: Toda recomendación IA es auditable (run, mensajes, herramientas).
- **RNF-AI-2**: Funcionamiento degradado (fallback) sin dependencia de proveedor externo.
- **RNF-AI-3**: No exposición de datos de un tenant a otro en contexto de los agentes.
