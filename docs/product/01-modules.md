# Módulos Funcionales — Detalle

Catálogo completo de los 14 módulos: propósito, funcionalidades, reglas de negocio,
entidades implicadas y eventos que emiten.

---

## Módulo 1 — Gestión de Usuarios

**Propósito:** identidad segura y control de acceso por rol y por equipo.

**Funcionalidades**

- Registro (auto-registro o por invitación de una cooperativa).
- Inicio de sesión con email + contraseña (JWT access/refresh).
- Recuperación de contraseña (token por email, caducidad corta).
- **MFA** (TOTP por app autenticadora; SMS opcional como add-on).
- Gestión de perfil (idioma, teléfono, preferencias de notificación).
- Roles y permisos (ver [02-roles-permissions.md](02-roles-permissions.md)).
- **Gestión de equipos**: un agricultor puede tener operarios; un técnico cubre una
  cartera de agricultores.
- Sesiones activas y revocación; registro de dispositivos.

**Reglas de negocio**

- Un usuario puede pertenecer a varias cooperativas con un rol distinto en cada una.
- El rol efectivo se resuelve por el tenant activo (cabecera `X-Cooperative`).
- MFA obligatorio configurable a nivel de cooperativa para roles administrativos.

**Entidades:** `User`, `CooperativeMembership`, `Team`, `TeamMembership`, `MfaDevice`,
`PasswordResetToken`, `AuditEvent`.

**Eventos:** `user.registered`, `user.invited`, `user.mfa_enabled`, `login.succeeded`,
`login.failed`.

---

## Módulo 2 — Gestión de Cooperativas

**Propósito:** operar la cooperativa como tenant: socios, documentos, comunicación y economía.

**Funcionalidades**

- Crear/configurar cooperativa (datos fiscales, región, branding).
- **Gestión de socios** (altas, bajas, estados, cuota).
- Parcelas asociadas a la cooperativa (vista agregada).
- **Gestión documental** de la cooperativa (estatutos, actas, certificados).
- **Comunicaciones masivas** (avisos a todos los socios o a segmentos).
- Estadísticas globales y **gestión económica** (liquidaciones, aportaciones).

**Dashboard cooperativa**

- Producción total y por cultivo (campaña actual vs anterior).
- Agricultores activos / inactivos.
- Riesgos detectados (stock, plazos de seguridad, plagas) y alertas abiertas.
- Mapa de parcelas de la cooperativa.

**Reglas de negocio**

- Solo `COOP_ADMIN` gestiona socios y comunicaciones.
- Las comunicaciones masivas quedan registradas (quién, cuándo, a quién).

**Entidades:** `Cooperative`, `Member` (socio), `CooperativeDocument`, `Broadcast`,
`BroadcastRecipient`, `EconomicEntry`.

**Eventos:** `coop.created`, `member.joined`, `member.left`, `broadcast.sent`.

---

## Módulo 3 — Gestión de Explotaciones

**Propósito:** estructurar el campo en una jerarquía clara y con histórico.

**Jerarquía:** `Finca → Parcela → Sector → Cultivo (por campaña)`.

**Funcionalidades**

- CRUD de fincas, parcelas (referencia SIGPAC/catastral), sectores y cultivos.
- Geolocalización y superficie (ha) por parcela/sector; polígonos en mapa.
- Ficha de cultivo: especie, variedad, fecha de plantación/siembra, estado, marco.
- **Historial agrícola** y **producción histórica** por parcela y campaña.

**Reglas de negocio**

- La suma de superficies de sectores no debe superar la de su parcela.
- Un cultivo pertenece a una campaña; al cerrar campaña se archiva con su producción.

**Entidades:** `Farm`, `Parcel`, `Sector`, `Crop`, `Campaign`, `HarvestRecord`.

**Eventos:** `parcel.created`, `crop.planted`, `crop.harvested`, `campaign.closed`.

---

## Módulo 4 — Cuaderno de Campo Digital

**Propósito:** registro normativo (Reglamento UE de uso sostenible de fitosanitarios y
PAC) sin papeleo, con validaciones automáticas.

**Funcionalidades**

- Registrar **tratamientos** fitosanitarios (producto, dosis, plaga objetivo, condiciones).
- Registrar **fertilizaciones** (tipo, unidades fertilizantes N-P-K, dosis).
- Registrar **riegos** (volumen, método, fuente de agua).
- Registrar **incidencias** (plaga, enfermedad, meteorología adversa).
- Registrar **labores** (poda, siembra, cosecha, laboreo).
- **Exportaciones**: PDF oficial, Excel y formatos oficiales por comunidad/país.

**Validaciones automáticas**

- Producto autorizado para el cultivo (nº de registro fitosanitario).
- **Plazo de seguridad** respetado respecto a la fecha prevista de cosecha.
- Dosis dentro del rango permitido; aplicador con carnet vigente (si aplica).
- Stock suficiente del producto (enlaza con inventario).

**Reglas de negocio**

- Toda entrada del cuaderno alimenta automáticamente la trazabilidad (Módulo 5).
- Las entradas validadas no se borran: se corrigen con una entrada de rectificación.

**Entidades:** `FieldOperation`, `Treatment`, `Fertilization`, `Irrigation`,
`Incident`, `LaborTask`, `Applicator`, `ExportJob`.

**Eventos:** `operation.registered`, `treatment.registered`, `safety_interval.violated`.

---

## Módulo 5 — Trazabilidad Completa

**Propósito:** historial completo, inmutable y auditable de todo lo que ocurre.

**Funcionalidades**

- Registro append-only de toda actividad: quién, qué, cuándo, dónde (parcela), con qué
  productos.
- Línea de tiempo por parcela, por cultivo y por campaña.
- **Auditoría total** consultable por el rol `AUDITOR` (solo lectura).
- Encadenamiento por hash (cada registro referencia el hash del anterior) para detectar
  manipulaciones.

**Reglas de negocio**

- Los registros de trazabilidad son **inmutables**; cualquier cambio es un nuevo evento.
- Acceso de auditoría no altera datos y queda a su vez registrado.

**Entidades:** `TraceEvent` (append-only, hash-chained), `AuditAccessLog`.

**Eventos:** `trace.appended`.

---

## Módulo 6 — Gestión de Inventario

**Propósito:** controlar todos los insumos y consumibles con stock fiable.

**Categorías:** fertilizantes, fitosanitarios, semillas, herramientas, maquinaria menor.

**Funcionalidades**

- Stock por producto y por almacén (cooperativa / finca).
- **Entradas** (compras) y **salidas** (consumo por tratamiento/fertilización).
- **Caducidades** y números de lote; FEFO (first-expired-first-out).
- **Alertas** de stock bajo y de producto caducado/por caducar.

**Reglas de negocio**

- Cada tratamiento genera una salida automática de stock (ledger inmutable).
- No se permite consumir producto caducado (bloqueo + aviso).

**Entidades:** `Product`, `Warehouse`, `StockBatch` (lote+caducidad), `StockMovement`,
`Supplier`, `PurchaseOrder`.

**Eventos:** `stock.low`, `stock.expired`, `stock.moved`.

---

## Módulo 7 — Gestión de Maquinaria

**Propósito:** controlar el parque móvil y su coste real.

**Funcionalidades**

- Registro de tractores, aperos, vehículos y equipos.
- **Horas de uso** y asignación a labores/parcelas.
- **Consumo** de combustible y eficiencia.
- **Mantenimiento** (preventivo programado y correctivo) e historial.
- **Costes** de uso imputables a parcela/cultivo (alimenta Módulo 8).

**Entidades:** `Machine`, `MachineUsage`, `MaintenanceTask`, `FuelLog`.

**Eventos:** `machine.maintenance_due`, `machine.used`.

---

## Módulo 8 — Gestión de Costes y Rentabilidad

**Propósito:** saber cuánto cuesta y cuánto renta cada parcela, cultivo y campaña.

**Componentes de coste:** mano de obra, productos (inventario), maquinaria, agua,
electricidad, otros directos e indirectos.

**Funcionalidades**

- Imputación automática de costes desde cuaderno, inventario y maquinaria.
- Coste por parcela / cultivo / campaña / hectárea.
- **Rentabilidad** = ingresos (producción × precio) − costes.
- Comparativas entre campañas y entre parcelas.

**Reglas de negocio**

- Cada movimiento de inventario, hora de máquina y parte de labor lleva un coste asociado.
- La rentabilidad se recalcula al cerrar la campaña y bajo demanda.

**Entidades:** `CostEntry`, `LaborCost`, `PriceList`, `ProfitabilityReport`.

**Eventos:** `cost.imputed`, `profitability.calculated`.

---

## Módulo 9 — Inteligencia Agrícola (Agentes IA)

**Propósito:** escalar el conocimiento agronómico con agentes especializados que usan
herramientas y memoria.

### Agente Agrónomo

Resuelve consultas, recomienda tratamientos/fertilización/riego, analiza históricos.

### Agente Plagas (visión por imagen)

Analiza fotografías para detectar **enfermedades, plagas y carencias nutricionales**.
Devuelve: **diagnóstico, probabilidad, gravedad y tratamiento recomendado**.

### Agente Administrativo

Genera informes, revisa documentación, detecta errores y completa registros del cuaderno.

### Agente Cooperativa

Analiza la situación global, detecta **riesgos colectivos** y genera informes para directivos.

**Reglas de negocio**

- Los agentes **recomiendan**; las acciones críticas requieren confirmación humana.
- Toda ejecución se persiste (run + transcript + herramientas usadas) para auditoría.
- Los agentes consultan la **memoria** (Módulo 10) y emiten/escuchan eventos.

**Entidades:** `Agent`, `AgentRun`, `AgentMessage`, `ToolInvocation`, `ImageAnalysis`.

**Eventos:** escucha `treatment.registered`, `stock.low`, `incident.reported`;
emite `agent.recommendation`, `agent.alert`.

---

## Módulo 10 — Memoria Inteligente (3 niveles)

**Propósito:** dar contexto persistente y consultable a los agentes y a la analítica.

| Nivel       | Contenido                                             |
| ----------- | ----------------------------------------------------- |
| Agricultor  | Historial de consultas, tratamientos, preferencias    |
| Parcela     | Historial completo, producción, problemas recurrentes |
| Cooperativa | Datos agregados, tendencias, riesgos colectivos       |

**Funcionalidades**

- Escritura (`remember`), recuperación (`recall`) y resumen (`summarize`).
- Búsqueda por texto/tags hoy; **búsqueda semántica (embeddings/pgvector)** en roadmap.
- Importancia y origen (`system` / `agent:<nombre>` / `user`) por entrada.

**Entidades:** `MemoryEntry` (scope USER/PARCEL/GLOBAL).

**Eventos:** `memory.written`.

---

## Módulo 11 — Alertas

**Propósito:** anticipación. Convertir datos en avisos accionables.

**Disparadores:** clima adverso, plagas/enfermedades, caducidades, incumplimientos
normativos, riesgos de producción, stock bajo, mantenimiento de maquinaria.

**Canales:** Email, SMS, **WhatsApp**, Push (web/móvil).

**Funcionalidades**

- Reglas configurables por cooperativa y por usuario.
- Niveles de severidad (info / aviso / crítico) y agrupación anti-spam.
- Confirmación de lectura y escalado si no se atiende.

**Entidades:** `AlertRule`, `Alert`, `AlertDelivery`, `NotificationChannel`.

**Eventos:** `alert.raised`, `alert.delivered`, `alert.acknowledged`.

---

## Módulo 12 — Analítica

**Propósito:** cuadros de mando para decidir con datos.

**Funcionalidades**

- KPIs agrícolas: producción, rendimiento (kg/ha), rentabilidad, coste/ha, uso de agua.
- Comparativas: campaña vs campaña, parcela vs parcela, socio vs media de la cooperativa.
- Cuadros para agricultor, técnico y cooperativa (cada rol ve su nivel).
- Exportación de cuadros e informes.

**Entidades:** `KpiSnapshot`, `Dashboard`, `Report`.

**Eventos:** `kpi.snapshot_generated`.

---

## Módulo 13 — Documentación

**Propósito:** repositorio documental único e inteligente.

**Funcionalidades**

- Almacén de facturas, certificados, contratos, inspecciones y fotografías.
- **OCR automático** para extraer texto y datos clave.
- **Clasificación automática** por tipo y vinculación a parcela/proveedor/campaña.
- Búsqueda full-text sobre el contenido OCR.

**Entidades:** `Document`, `DocumentClass`, `OcrResult`, `DocumentLink`.

**Eventos:** `document.uploaded`, `document.classified`.

---

## Módulo 14 — API e Integraciones

**Propósito:** abrir la plataforma al ecosistema agrícola.

**Integraciones previstas**

- **Sensores IoT** (humedad de suelo, pluviómetros) → telemetría a parcela.
- **Estaciones meteorológicas** y servicios meteo → alertas de clima.
- **Satélite** (índices NDVI/NDWI) → estado vegetativo por parcela.
- **Drones** → ortofotos e inspección dirigida del Agente Plagas.
- **ERP/contabilidad externos** → costes e ingresos.
- **WhatsApp Business** → alertas y registro conversacional.

**Funcionalidades**

- API REST documentada (OpenAPI), claves de API y webhooks salientes.
- Conectores con mapeo de datos y reintentos.

**Entidades:** `ApiKey`, `Webhook`, `Integration`, `DeviceReading`, `SatelliteIndex`.

**Eventos:** `integration.synced`, `device.reading_received`, `webhook.delivered`.
