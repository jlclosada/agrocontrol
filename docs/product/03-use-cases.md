# Casos de Uso

Casos de uso por módulo, con actor, precondiciones, flujo principal, flujos alternativos y
postcondiciones. Notación `UC-<módulo>.<n>`.

---

## UC-1 · Usuarios

### UC-1.1 Iniciar sesión con MFA

- **Actor:** cualquier usuario.
- **Precondición:** cuenta activa; MFA configurado si el tenant lo exige.
- **Flujo principal:** introduce email+contraseña → sistema valida → solicita código TOTP →
  emite JWT (access+refresh) → resuelve cooperativa y rol activos.
- **Alternativos:** credenciales inválidas (bloqueo progresivo); código TOTP erróneo;
  recuperación de contraseña.
- **Postcondición:** sesión activa con tenant y rol resueltos; evento `login.succeeded`.

### UC-1.2 Invitar a un usuario a la cooperativa

- **Actor:** COOP_ADMIN.
- **Flujo:** introduce email + rol → si el usuario existe se vincula; si no, recibe invitación →
  al aceptar, se crea la membresía.
- **Postcondición:** `CooperativeMembership` creado; evento `user.invited`.

### UC-1.3 Crear un equipo y asignar operarios

- **Actor:** FARMER / COOP_ADMIN.
- **Flujo:** crea equipo → añade operarios → asigna parcelas/labores.
- **Postcondición:** operarios pueden registrar en campo dentro de su ámbito.

---

## UC-2 · Cooperativas

### UC-2.1 Alta de cooperativa (onboarding)

- **Actor:** SUPERADMIN.
- **Flujo:** crea tenant con datos fiscales → designa COOP_ADMIN → configura branding y MFA.
- **Postcondición:** cooperativa operativa; agentes IA por defecto sembrados.

### UC-2.2 Comunicación masiva a socios

- **Actor:** COOP_ADMIN.
- **Flujo:** redacta aviso → elige segmento (todos / por cultivo / por zona) → envía por
  canales configurados → registra entregas y lecturas.
- **Postcondición:** `Broadcast` + `BroadcastRecipient`; evento `broadcast.sent`.

### UC-2.3 Ver dashboard global de cooperativa

- **Actor:** COOP_ADMIN, AUDITOR.
- **Flujo:** abre dashboard → producción total/por cultivo, socios activos, riesgos y alertas.

---

## UC-3 · Explotaciones

### UC-3.1 Dar de alta finca, parcela, sector y cultivo

- **Actor:** FARMER.
- **Flujo:** crea finca → añade parcela (SIGPAC + superficie + polígono) → divide en sectores →
  planta cultivo (especie, variedad, fecha).
- **Validación:** Σ superficies de sectores ≤ superficie de la parcela.
- **Postcondición:** jerarquía creada; evento `crop.planted`.

### UC-3.2 Cerrar campaña y registrar cosecha

- **Actor:** FARMER / COOP_ADMIN.
- **Flujo:** registra producción (kg) → cierra campaña → recalcula costes y rentabilidad.
- **Postcondición:** campaña archivada; eventos `crop.harvested`, `campaign.closed`.

---

## UC-4 · Cuaderno de campo

### UC-4.1 Registrar un tratamiento fitosanitario

- **Actor:** OPERATOR / FARMER / AGRONOMIST.
- **Precondición:** producto en inventario; cultivo activo.
- **Flujo principal:** selecciona parcela+cultivo → producto → dosis → plaga objetivo →
  condiciones → guarda.
- **Validaciones:** producto autorizado; **plazo de seguridad** OK; dosis en rango; stock
  suficiente.
- **Efectos:** salida de stock automática; entrada en trazabilidad; evaluación IA de riesgo.
- **Alternativos:** plazo de seguridad violado → aviso + requiere confirmación de rol elevado;
  stock insuficiente → bloqueo.
- **Postcondición:** `Treatment` + `TraceEvent`; eventos `treatment.registered` (y
  `safety_interval.violated` si aplica).

### UC-4.2 Exportar cuaderno oficial

- **Actor:** FARMER / AGRONOMIST / AUDITOR.
- **Flujo:** elige rango y parcelas → genera PDF/Excel/formato oficial → se sella con hash y
  fecha.

---

## UC-5 · Trazabilidad

### UC-5.1 Consultar la línea de tiempo de una parcela

- **Actor:** AUDITOR, AGRONOMIST, FARMER.
- **Flujo:** abre parcela → ve cronología inmutable de todas las actividades.

### UC-5.2 Verificar integridad ante inspección

- **Actor:** AUDITOR.
- **Flujo:** ejecuta verificación de cadena de hashes → confirma que no hubo manipulación →
  exporta informe.

---

## UC-6 · Inventario

### UC-6.1 Recepción de compra con lote y caducidad

- **Actor:** COOP_ADMIN / FARMER.
- **Flujo:** registra entrada (producto, lote, caducidad, cantidad) → actualiza stock.

### UC-6.2 Alerta de caducidad / stock bajo

- **Actor:** sistema → notifica a FARMER/COOP_ADMIN.
- **Flujo:** job evalúa lotes y umbrales → genera alertas FEFO y de reposición.

---

## UC-7 · Maquinaria

### UC-7.1 Registrar uso de máquina en una labor

- **Actor:** OPERATOR.
- **Flujo:** selecciona máquina + labor + horas + consumo → imputa coste a parcela.

### UC-7.2 Mantenimiento preventivo

- **Actor:** sistema/COOP_ADMIN.
- **Flujo:** al alcanzar horas/umbral → alerta de mantenimiento → registra intervención.

---

## UC-8 · Costes y rentabilidad

### UC-8.1 Calcular rentabilidad de una parcela

- **Actor:** FARMER / COOP_ADMIN.
- **Flujo:** sistema agrega costes (labor, productos, máquina, agua, luz) + ingresos →
  rentabilidad por parcela/cultivo/campaña → comparativa con campañas previas.

---

## UC-9 · Inteligencia agrícola

### UC-9.1 Consultar al Agente Agrónomo

- **Actor:** FARMER / AGRONOMIST.
- **Flujo:** pregunta en lenguaje natural → el agente usa herramientas (parcelas, histórico,
  stock) y memoria → responde con recomendación justificada.

### UC-9.2 Diagnóstico de plaga por foto (Agente Plagas)

- **Actor:** FARMER / OPERATOR.
- **Flujo:** sube foto de hoja/fruto → el agente devuelve **diagnóstico, probabilidad,
  gravedad y tratamiento recomendado** → opción de registrar incidencia.
- **Postcondición:** `ImageAnalysis`; posible `Incident` y alerta.

### UC-9.3 Informe colectivo (Agente Cooperativa)

- **Actor:** COOP_ADMIN.
- **Flujo:** solicita informe → el agente analiza datos agregados → detecta riesgos colectivos →
  genera informe para directivos.

---

## UC-11 · Alertas

### UC-11.1 Configurar una regla de alerta

- **Actor:** COOP_ADMIN / FARMER.
- **Flujo:** define condición (p. ej. "humedad < X" o "plazo de seguridad próximo") + canal +
  severidad → activa.

### UC-11.2 Recibir y confirmar una alerta crítica

- **Actor:** destinatario.
- **Flujo:** recibe por canal → confirma lectura → si no atiende, escalado a rol superior.

---

## UC-13 · Documentación

### UC-13.1 Subir factura con OCR y clasificación

- **Actor:** FARMER / COOP_ADMIN.
- **Flujo:** sube documento → OCR extrae datos → clasificación automática → se vincula a
  proveedor/parcela/campaña → indexado para búsqueda.

---

## UC-14 · Integraciones

### UC-14.1 Ingesta de telemetría IoT

- **Actor:** dispositivo (vía API key).
- **Flujo:** sensor envía lectura → se asocia a la parcela → alimenta alertas y analítica.

### UC-14.2 Índice satelital NDVI por parcela

- **Actor:** sistema/integración.
- **Flujo:** sincroniza índice vegetativo → muestra estado por parcela → alimenta al Agente
  Agrónomo.
