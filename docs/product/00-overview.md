# AgroControl OS — Visión de Producto y Arquitectura Funcional

> **Documento maestro de diseño de producto.** Nivel empresarial. Define _qué_ es la
> plataforma, _para quién_, _qué problemas resuelve_ y _cómo se estructura funcionalmente_
> antes de cualquier implementación.

---

## 1. Visión

**AgroControl OS no es un ERP agrícola: es el sistema operativo de la explotación y de la
cooperativa.**

Un único lugar donde conviven la gestión diaria del campo, el cumplimiento normativo, la
trazabilidad, los costes, la inteligencia artificial y la comunicación entre agricultor,
técnico y cooperativa. Todo centralizado, todo conectado, todo auditable.

> _"Del satélite a la factura, de la semilla a la venta — una sola plataforma."_

### Declaración de valor

| Para…                | que necesita…                                 | AgroControl OS…                                                 |
| -------------------- | --------------------------------------------- | --------------------------------------------------------------- |
| Pequeño agricultor   | cumplir la normativa sin papeleo              | digitaliza el cuaderno de campo y lo valida solo                |
| Mediano agricultor   | saber si gana o pierde dinero en cada parcela | calcula costes y rentabilidad por parcela/cultivo/campaña       |
| Técnico agrónomo     | atender a muchos agricultores con criterio    | le da histórico, diagnóstico IA y recomendaciones centralizadas |
| Admin de cooperativa | visión global y reducir riesgos colectivos    | agrega producción, detecta riesgos y comunica de forma masiva   |
| Empresa agrícola     | integrar IoT/satélite/ERP y escalar           | ofrece API, multi-tenant y módulos enterprise                   |

---

## 2. Problemas reales del sector que resolvemos

1. **Burocracia asfixiante** — el cuaderno de campo y los registros oficiales consumen
   horas y se hacen en papel o en hojas de cálculo dispersas.
2. **Falta de trazabilidad** — ante una inspección o una alerta alimentaria no hay
   historial fiable de quién aplicó qué, cuándo y dónde.
3. **Decisiones a ciegas** — el agricultor no sabe el coste real ni la rentabilidad de
   cada parcela.
4. **Conocimiento agronómico no escalable** — un técnico no llega a todos sus agricultores
   con el mismo nivel de detalle.
5. **Pérdidas evitables** — plagas detectadas tarde, productos caducados, tratamientos
   fuera de plazo de seguridad.
6. **Cooperativa desconectada** — la dirección no tiene una foto agregada en tiempo real de
   la producción ni de los riesgos colectivos.
7. **Datos en silos** — clima, sensores, satélite, contabilidad y campo no se hablan.

---

## 3. Personas (usuarios objetivo)

| Persona              | Rol técnico  | Objetivo principal                           | Dolor que eliminamos                         |
| -------------------- | ------------ | -------------------------------------------- | -------------------------------------------- |
| **Superadmin**       | `SUPERADMIN` | Operar la plataforma SaaS                    | Gestión multi-tenant y soporte               |
| **Gerente coop.**    | `COOP_ADMIN` | Visión global, socios, economía              | Falta de datos agregados y comunicación      |
| **Técnico agrónomo** | `AGRONOMIST` | Asesorar con criterio y a escala             | Sin histórico ni herramientas de diagnóstico |
| **Agricultor**       | `FARMER`     | Gestionar su explotación y cumplir normativa | Papeleo, no saber su rentabilidad            |
| **Operario**         | `OPERATOR`   | Ejecutar y registrar labores en campo        | Registro manual, sin app móvil sencilla      |
| **Auditor**          | `AUDITOR`    | Verificar cumplimiento (solo lectura)        | Datos no fiables ni inmutables               |

---

## 4. Arquitectura funcional (capas)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  EXPERIENCIA            Web (SaaS) · App móvil · Portal cooperativa · API   │
├──────────────────────────────────────────────────────────────────────────┤
│  INTELIGENCIA           Agentes IA · Memoria 3 niveles · Alertas · Analítica│
├──────────────────────────────────────────────────────────────────────────┤
│  PROCESOS DE NEGOCIO    Cuaderno · Trazabilidad · Costes · Inventario · …   │
├──────────────────────────────────────────────────────────────────────────┤
│  DOMINIO CENTRAL        Usuarios · Cooperativas · Explotaciones · Cultivos  │
├──────────────────────────────────────────────────────────────────────────┤
│  PLATAFORMA             Multi-tenant · Auth/MFA · Auditoría · Documentos    │
├──────────────────────────────────────────────────────────────────────────┤
│  INTEGRACIONES          IoT · Meteo · Satélite · Drones · ERP · WhatsApp    │
└──────────────────────────────────────────────────────────────────────────┘
```

### Principios de arquitectura

- **Multi-tenant por cooperativa** — aislamiento estricto de datos por tenant.
- **Event-driven** — cada acción del dominio emite eventos que alimentan IA, alertas y
  analítica sin acoplar módulos.
- **Inmutabilidad y auditoría** — la trazabilidad se construye sobre un log append-only.
- **IA aumentada, no autónoma** — los agentes recomiendan; las personas deciden y firman.
- **API-first** — toda función de UI existe también como endpoint para integraciones.
- **Mobile-first en campo** — el operario y el agricultor registran desde el móvil, incluso
  sin cobertura (offline-first en el roadmap).

---

## 5. Mapa de módulos (14)

| #   | Módulo                     | Núcleo de valor                                  | Fase   |
| --- | -------------------------- | ------------------------------------------------ | ------ |
| 1   | Gestión de usuarios        | Identidad, MFA, roles, equipos                   | MVP    |
| 2   | Gestión de cooperativas    | Socios, documental, comunicaciones, economía     | MVP/V2 |
| 3   | Gestión de explotaciones   | Fincas, parcelas, sectores, cultivos             | MVP    |
| 4   | Cuaderno de campo digital  | Registro normativo + exportaciones oficiales     | MVP    |
| 5   | Trazabilidad completa      | Historial inmutable y auditoría                  | MVP/V2 |
| 6   | Gestión de inventario      | Stock, caducidades, entradas/salidas             | MVP/V2 |
| 7   | Gestión de maquinaria      | Horas, consumo, mantenimiento, costes            | V2     |
| 8   | Gestión de costes          | Coste y rentabilidad por parcela/cultivo/campaña | V2     |
| 9   | Inteligencia agrícola (IA) | Agentes Agrónomo, Plagas, Admin, Cooperativa     | V2/V3  |
| 10  | Memoria inteligente        | Memoria agricultor / parcela / cooperativa       | V2/V3  |
| 11  | Alertas                    | Clima, plagas, caducidades, normativa            | V2     |
| 12  | Analítica                  | KPIs, producción, rentabilidad, comparativas     | V2/V3  |
| 13  | Documentación              | Repositorio + OCR + clasificación                | V3     |
| 14  | API e integraciones        | IoT, meteo, satélite, drones, ERP, WhatsApp      | V3/Ent |

> El detalle funcional de cada módulo está en
> [01-modules.md](01-modules.md). Roles y permisos en
> [02-roles-permissions.md](02-roles-permissions.md). Casos de uso e historias en
> [03-use-cases.md](03-use-cases.md) y [04-user-stories.md](04-user-stories.md).
> Modelo de datos en [05-data-model.md](05-data-model.md). Requisitos en
> [06-requirements.md](06-requirements.md). Roadmap en [07-roadmap.md](07-roadmap.md).

---

## 6. Flujos de usuario clave (visión)

1. **Onboarding cooperativa** → Superadmin crea tenant → Gerente invita socios y técnicos →
   socios dan de alta sus fincas.
2. **Día de campo** → Operario abre la app → registra un tratamiento → se descuenta stock →
   se valida plazo de seguridad → entra en el cuaderno y la trazabilidad → IA evalúa riesgo.
3. **Cierre de campaña** → se consolidan costes por parcela → se calcula rentabilidad →
   Agente Cooperativa genera informe para directivos.
4. **Inspección** → Auditor entra en modo solo lectura → exporta cuaderno oficial en PDF →
   verifica trazabilidad inmutable.

---

## 7. Modelo de negocio (contexto para priorizar)

- **SaaS por suscripción** escalonada: _Agricultor_ (parcelas limitadas), _Cooperativa_
  (socios + módulos colectivos), _Enterprise_ (integraciones + IA avanzada + SLA).
- **Add-ons**: IA de imagen (plagas), satélite/NDVI, canales de alerta (SMS/WhatsApp).
- **Métricas norte**: explotaciones activas, hectáreas gestionadas, % cuadernos completos,
  retención de cooperativas.
