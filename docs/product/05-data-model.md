# Modelo de Datos Completo

Modelo conceptual/lógico de todas las entidades, sus atributos clave y relaciones.
Toda entidad de dominio incluye `id (UUID)`, `created_at`, `updated_at` y, salvo las
globales, `cooperative_id` (aislamiento multi-tenant).

> Leyenda relaciones: `||--o{` = uno a muchos · `}o--o{` = muchos a muchos ·
> `||--||` = uno a uno.

---

## 1. Núcleo: Identidad y Tenant

```mermaid
erDiagram
    USER ||--o{ COOPERATIVE_MEMBERSHIP : "tiene"
    COOPERATIVE ||--o{ COOPERATIVE_MEMBERSHIP : "agrupa"
    USER ||--o{ MFA_DEVICE : "registra"
    USER ||--o{ TEAM_MEMBERSHIP : "participa"
    TEAM ||--o{ TEAM_MEMBERSHIP : "incluye"
    COOPERATIVE ||--o{ TEAM : "define"

    USER {
        uuid id PK
        string email UK
        string first_name
        string last_name
        string phone
        string locale
        bool is_active
    }
    COOPERATIVE {
        uuid id PK
        string name
        string slug UK
        string tax_id
        string country
        string region
        bool mfa_required
        bool is_active
    }
    COOPERATIVE_MEMBERSHIP {
        uuid id PK
        uuid user_id FK
        uuid cooperative_id FK
        enum role "SUPERADMIN|COOP_ADMIN|AGRONOMIST|FARMER|OPERATOR|AUDITOR"
        bool is_active
    }
    TEAM {
        uuid id PK
        uuid cooperative_id FK
        string name
    }
    TEAM_MEMBERSHIP {
        uuid id PK
        uuid team_id FK
        uuid user_id FK
        enum role
    }
    MFA_DEVICE {
        uuid id PK
        uuid user_id FK
        enum type "TOTP|SMS"
        string secret
        bool confirmed
    }
```

---

## 2. Explotación: Fincas → Parcelas → Sectores → Cultivos

```mermaid
erDiagram
    COOPERATIVE ||--o{ FARM : "asocia"
    USER ||--o{ FARM : "posee"
    FARM ||--o{ PARCEL : "contiene"
    PARCEL ||--o{ SECTOR : "se divide en"
    PARCEL ||--o{ CROP : "cultiva"
    SECTOR ||--o{ CROP : "cultiva"
    CAMPAIGN ||--o{ CROP : "enmarca"
    CROP ||--o{ HARVEST_RECORD : "produce"

    FARM {
        uuid id PK
        uuid cooperative_id FK
        uuid owner_id FK
        string name
        text description
    }
    PARCEL {
        uuid id PK
        uuid farm_id FK
        string name
        string sigpac_ref
        decimal area_ha
        string soil_type
        decimal latitude
        decimal longitude
        json polygon
        bool is_active
    }
    SECTOR {
        uuid id PK
        uuid parcel_id FK
        string name
        decimal area_ha
    }
    CAMPAIGN {
        uuid id PK
        uuid cooperative_id FK
        string label "2025/2026"
        date start_date
        date end_date
        bool is_closed
    }
    CROP {
        uuid id PK
        uuid parcel_id FK
        uuid sector_id FK
        uuid campaign_id FK
        string species
        string variety
        date sowing_date
        date expected_harvest_date
        enum status "PLANNED|GROWING|HARVESTED|FAILED"
        decimal expected_yield_kg
    }
    HARVEST_RECORD {
        uuid id PK
        uuid crop_id FK
        date date
        decimal quantity_kg
        decimal quality_grade
    }
```

---

## 3. Cuaderno de campo y Trazabilidad

```mermaid
erDiagram
    CROP ||--o{ FIELD_OPERATION : "registra"
    FIELD_OPERATION ||--o| TREATMENT : "puede ser"
    FIELD_OPERATION ||--o| FERTILIZATION : "puede ser"
    FIELD_OPERATION ||--o| IRRIGATION : "puede ser"
    FIELD_OPERATION ||--o| INCIDENT : "puede ser"
    FIELD_OPERATION ||--o| LABOR_TASK : "puede ser"
    PRODUCT ||--o{ TREATMENT : "usa"
    USER ||--o{ FIELD_OPERATION : "realiza"
    FIELD_OPERATION ||--o{ TRACE_EVENT : "genera"

    FIELD_OPERATION {
        uuid id PK
        uuid cooperative_id FK
        uuid crop_id FK
        enum operation_type "SOWING|FERTILIZATION|IRRIGATION|TREATMENT|PRUNING|HARVEST|OTHER"
        date date
        text description
        decimal area_ha
        uuid performed_by FK
    }
    TREATMENT {
        uuid id PK
        uuid operation_id FK
        uuid crop_id FK
        uuid product_id FK
        date date
        decimal dose
        string dose_unit
        decimal total_quantity
        string target_pest
        string weather
        uuid applicator_id FK
        bool safety_interval_ok
    }
    FERTILIZATION {
        uuid id PK
        uuid operation_id FK
        string fertilizer
        decimal n_units
        decimal p_units
        decimal k_units
        decimal dose
    }
    IRRIGATION {
        uuid id PK
        uuid operation_id FK
        decimal volume_m3
        string method
        string water_source
    }
    INCIDENT {
        uuid id PK
        uuid operation_id FK
        enum kind "PEST|DISEASE|WEATHER|DEFICIENCY"
        enum severity "LOW|MEDIUM|HIGH"
        text notes
    }
    LABOR_TASK {
        uuid id PK
        uuid operation_id FK
        string task
        decimal hours
    }
    TRACE_EVENT {
        uuid id PK
        uuid cooperative_id FK
        uuid actor_id FK
        string entity_type
        uuid entity_id
        json payload
        string prev_hash
        string hash
        datetime occurred_at
    }
```

---

## 4. Inventario y Maquinaria

```mermaid
erDiagram
    COOPERATIVE ||--o{ PRODUCT : "cataloga"
    COOPERATIVE ||--o{ WAREHOUSE : "tiene"
    PRODUCT ||--o{ STOCK_BATCH : "tiene lotes"
    PRODUCT ||--o{ STOCK_MOVEMENT : "mueve"
    WAREHOUSE ||--o{ STOCK_MOVEMENT : "ubica"
    SUPPLIER ||--o{ PURCHASE_ORDER : "suministra"
    TREATMENT ||--o{ STOCK_MOVEMENT : "consume"
    MACHINE ||--o{ MACHINE_USAGE : "se usa"
    MACHINE ||--o{ MAINTENANCE_TASK : "mantiene"
    CROP ||--o{ MACHINE_USAGE : "imputa"

    PRODUCT {
        uuid id PK
        uuid cooperative_id FK
        string name
        string registration_number
        string active_ingredient
        enum category "HERBICIDE|FUNGICIDE|INSECTICIDE|FERTILIZER|SEED|TOOL|OTHER"
        string unit
        int safety_interval_days
        decimal reorder_level
    }
    STOCK_BATCH {
        uuid id PK
        uuid product_id FK
        string lot
        date expiry_date
        decimal quantity
    }
    STOCK_MOVEMENT {
        uuid id PK
        uuid cooperative_id FK
        uuid product_id FK
        uuid warehouse_id FK
        uuid batch_id FK
        enum movement_type "IN|OUT|ADJUST"
        decimal quantity
        decimal signed_quantity
        string reason
        uuid treatment_id FK
    }
    WAREHOUSE { uuid id PK
        uuid cooperative_id FK
        string name
    }
    SUPPLIER { uuid id PK
        uuid cooperative_id FK
        string name
        string tax_id
    }
    PURCHASE_ORDER { uuid id PK
        uuid supplier_id FK
        date date
        decimal total
    }
    MACHINE {
        uuid id PK
        uuid cooperative_id FK
        enum kind "TRACTOR|IMPLEMENT|VEHICLE|EQUIPMENT"
        string name
        decimal hour_cost
    }
    MACHINE_USAGE {
        uuid id PK
        uuid machine_id FK
        uuid crop_id FK
        date date
        decimal hours
        decimal fuel_liters
    }
    MAINTENANCE_TASK {
        uuid id PK
        uuid machine_id FK
        enum type "PREVENTIVE|CORRECTIVE"
        date date
        decimal cost
    }
```

---

## 5. Costes, IA, Memoria, Alertas, Documentos, Integraciones

```mermaid
erDiagram
    CROP ||--o{ COST_ENTRY : "acumula"
    CROP ||--o| PROFITABILITY_REPORT : "resume"
    AGENT ||--o{ AGENT_RUN : "ejecuta"
    AGENT_RUN ||--o{ AGENT_MESSAGE : "contiene"
    AGENT_RUN ||--o{ TOOL_INVOCATION : "invoca"
    AGENT_RUN ||--o| IMAGE_ANALYSIS : "produce"
    COOPERATIVE ||--o{ MEMORY_ENTRY : "acumula"
    COOPERATIVE ||--o{ ALERT_RULE : "define"
    ALERT_RULE ||--o{ ALERT : "dispara"
    ALERT ||--o{ ALERT_DELIVERY : "entrega"
    COOPERATIVE ||--o{ DOCUMENT : "almacena"
    DOCUMENT ||--o| OCR_RESULT : "extrae"
    COOPERATIVE ||--o{ INTEGRATION : "configura"
    INTEGRATION ||--o{ DEVICE_READING : "ingresa"
    PARCEL ||--o{ DEVICE_READING : "mide"
    PARCEL ||--o{ SATELLITE_INDEX : "observa"

    COST_ENTRY {
        uuid id PK
        uuid cooperative_id FK
        uuid crop_id FK
        enum category "LABOR|PRODUCT|MACHINE|WATER|ELECTRICITY|OTHER"
        decimal amount
        date date
    }
    PROFITABILITY_REPORT {
        uuid id PK
        uuid crop_id FK
        decimal total_cost
        decimal income
        decimal profit
        decimal cost_per_ha
    }
    AGENT {
        uuid id PK
        uuid cooperative_id FK
        enum agent_type "AGRONOMIST|PEST|ADMIN|COOPERATIVE|SUPPORT"
        string name
        text purpose
        string model
        json skills
        json tools
        json listens_to
        bool is_active
    }
    AGENT_RUN {
        uuid id PK
        uuid agent_id FK
        uuid user_id FK
        enum status "PENDING|RUNNING|COMPLETED|FAILED"
        text input_text
        text output_text
        int tokens_used
    }
    AGENT_MESSAGE {
        uuid id PK
        uuid run_id FK
        enum role "system|user|assistant|tool"
        text content
        string tool_name
    }
    IMAGE_ANALYSIS {
        uuid id PK
        uuid run_id FK
        string image_url
        string diagnosis
        decimal probability
        enum severity "LOW|MEDIUM|HIGH"
        text recommended_treatment
    }
    MEMORY_ENTRY {
        uuid id PK
        uuid cooperative_id FK
        enum scope "USER|PARCEL|GLOBAL"
        uuid user_id FK
        uuid parcel_id FK
        uuid crop_id FK
        text content
        json data
        json tags
        int importance
        string source
    }
    ALERT_RULE {
        uuid id PK
        uuid cooperative_id FK
        enum trigger "WEATHER|PEST|EXPIRY|COMPLIANCE|STOCK|PRODUCTION|MAINTENANCE"
        json condition
        enum severity
    }
    ALERT {
        uuid id PK
        uuid rule_id FK
        text message
        enum severity
        bool acknowledged
    }
    ALERT_DELIVERY {
        uuid id PK
        uuid alert_id FK
        enum channel "EMAIL|SMS|WHATSAPP|PUSH"
        enum status "PENDING|SENT|FAILED"
    }
    DOCUMENT {
        uuid id PK
        uuid cooperative_id FK
        enum doc_class "INVOICE|CERTIFICATE|CONTRACT|INSPECTION|PHOTO|OTHER"
        string file_url
        uuid linked_entity_id
    }
    OCR_RESULT {
        uuid id PK
        uuid document_id FK
        text raw_text
        json fields
    }
    INTEGRATION {
        uuid id PK
        uuid cooperative_id FK
        enum kind "IOT|WEATHER|SATELLITE|DRONE|ERP|WHATSAPP"
        json config
        bool is_active
    }
    DEVICE_READING {
        uuid id PK
        uuid integration_id FK
        uuid parcel_id FK
        string metric
        decimal value
        datetime measured_at
    }
    SATELLITE_INDEX {
        uuid id PK
        uuid parcel_id FK
        enum index_type "NDVI|NDWI"
        decimal value
        date date
    }
```

---

## 6. Resumen de relaciones clave

- **USER ⟷ COOPERATIVE** (N:M vía `COOPERATIVE_MEMBERSHIP` con rol) → multi-tenant.
- **FARM → PARCEL → SECTOR → CROP** → jerarquía de explotación.
- **CROP → FIELD_OPERATION** (1:N) y cada operación se especializa (treatment, fertilization…).
- **TREATMENT → STOCK_MOVEMENT** (consumo automático) → inventario consistente.
- Toda escritura de dominio → **TRACE_EVENT** (append-only, hash-chained) → trazabilidad.
- **CROP → COST_ENTRY → PROFITABILITY_REPORT** → costes y rentabilidad.
- **AGENT → AGENT_RUN → {AGENT_MESSAGE, TOOL_INVOCATION, IMAGE_ANALYSIS}** → IA auditable.
- **MEMORY_ENTRY** con scope USER/PARCEL/GLOBAL → memoria de 3 niveles.
- **ALERT_RULE → ALERT → ALERT_DELIVERY** → alertas multicanal.
- **INTEGRATION → {DEVICE_READING, SATELLITE_INDEX}** asociadas a PARCEL → datos externos.

---

## 7. Estado actual de implementación (backend)

Ya implementado en el código: `User`, `Cooperative`, `CooperativeMembership`, `Farm`,
`Parcel`, `Crop`, `FieldOperation`, `Treatment`, `Product`, `StockMovement`, `MemoryEntry`,
`Agent`, `AgentRun`, `AgentMessage`.

Pendiente (diseñado aquí, a implementar por fases): `Sector`, `Campaign`, `HarvestRecord`,
`Fertilization`, `Irrigation`, `Incident`, `LaborTask`, `TraceEvent`, `StockBatch`,
`Warehouse`, `Supplier`, `PurchaseOrder`, `Machine`, `MachineUsage`, `MaintenanceTask`,
`CostEntry`, `ProfitabilityReport`, `ImageAnalysis`, `AlertRule`, `Alert`, `AlertDelivery`,
`Document`, `OcrResult`, `Integration`, `DeviceReading`, `SatelliteIndex`, `Team`, `MfaDevice`.
