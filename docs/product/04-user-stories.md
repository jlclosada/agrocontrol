# Historias de Usuario

Formato: _"Como **[rol]**, quiero **[acción]**, para **[beneficio]**."_ con criterios de
aceptación (CA). Agrupadas por épica/módulo. ID `HU-<módulo>.<n>`. Prioridad MoSCoW
(Must / Should / Could / Won't-now) y fase objetivo.

---

## Épica 1 — Identidad y acceso

**HU-1.1** · _Must · MVP_ — Como **agricultor**, quiero **registrarme e iniciar sesión**,
para acceder a mi explotación.

- CA: validación de email; contraseña ≥ 8; JWT emitido; error claro si credenciales inválidas.

**HU-1.2** · _Must · MVP_ — Como **admin de cooperativa**, quiero **invitar usuarios con un
rol**, para construir mi equipo.

- CA: invitación por email; vinculación si ya existe; rol asignado; auditado.

**HU-1.3** · _Should · V2_ — Como **admin**, quiero **exigir MFA a los roles administrativos**,
para proteger los datos sensibles.

- CA: TOTP; login pide código; recuperación con códigos de respaldo.

**HU-1.4** · _Could · V2_ — Como **agricultor**, quiero **crear un equipo de operarios**,
para delegar el registro en campo.

- CA: operario solo ve sus parcelas/labores asignadas; sin acceso económico.

---

## Épica 2 — Cooperativa

**HU-2.1** · _Must · MVP_ — Como **admin**, quiero **crear y configurar mi cooperativa**, para
operar como tenant aislado.

- CA: datos fiscales; slug único; branding; aislamiento de datos garantizado.

**HU-2.2** · _Should · V2_ — Como **admin**, quiero **enviar comunicaciones masivas a los
socios**, para informar de campañas o riesgos.

- CA: segmentación; multicanal; registro de entregas/lecturas.

**HU-2.3** · _Must · V2_ — Como **admin**, quiero un **dashboard global** (producción, socios
activos, riesgos, alertas), para dirigir con datos.

- CA: KPIs en tiempo real; comparativa con campaña anterior; mapa de parcelas.

---

## Épica 3 — Explotaciones

**HU-3.1** · _Must · MVP_ — Como **agricultor**, quiero **gestionar fincas, parcelas, sectores y
cultivos**, para estructurar mi explotación.

- CA: jerarquía completa; SIGPAC; superficie validada; estado del cultivo.

**HU-3.2** · _Should · V2_ — Como **agricultor**, quiero **ver el historial y producción de cada
parcela**, para comparar campañas.

- CA: histórico por campaña; rendimiento kg/ha; gráfico de evolución.

---

## Épica 4 — Cuaderno de campo

**HU-4.1** · _Must · MVP_ — Como **operario**, quiero **registrar un tratamiento desde el móvil**,
para cumplir la normativa sin papeleo.

- CA: selección parcela/producto/dosis/plaga; validación de plazo de seguridad; descuento de
  stock automático; entra en trazabilidad.

**HU-4.2** · _Must · MVP_ — Como **agricultor**, quiero **registrar fertilización, riego,
incidencias y labores**, para tener el cuaderno completo.

- CA: formularios por tipo; campos obligatorios normativos; fecha y responsable.

**HU-4.3** · _Must · V2_ — Como **agricultor**, quiero **exportar el cuaderno en PDF/Excel/formato
oficial**, para presentarlo en inspecciones.

- CA: rango y parcelas; formato oficial por región; sellado con hash y fecha.

**HU-4.4** · _Should · V2_ — Como **técnico**, quiero que el sistema **avise de
incumplimientos** al registrar, para evitar sanciones.

- CA: bloqueo o confirmación de rol elevado con motivo; aviso visible.

---

## Épica 5 — Trazabilidad

**HU-5.1** · _Must · MVP_ — Como **auditor**, quiero **ver la cronología inmutable de cada
parcela**, para verificar el cumplimiento.

- CA: solo lectura; quién/qué/cuándo/dónde/productos; sin posibilidad de edición.

**HU-5.2** · _Should · V2_ — Como **auditor**, quiero **verificar la integridad por hash**, para
detectar manipulaciones.

- CA: validación de cadena; informe de integridad exportable.

---

## Épica 6 — Inventario

**HU-6.1** · _Must · MVP_ — Como **agricultor**, quiero **controlar el stock de fitosanitarios y
fertilizantes**, para no quedarme sin producto ni usar caducados.

- CA: entradas/salidas; stock en tiempo real; bloqueo de producto caducado.

**HU-6.2** · _Should · V2_ — Como **agricultor**, quiero **alertas de stock bajo y caducidad
(FEFO)**, para anticipar compras y evitar pérdidas.

- CA: umbral configurable; aviso multicanal; orden de consumo por caducidad.

---

## Épica 7 — Maquinaria

**HU-7.1** · _Should · V2_ — Como **agricultor**, quiero **registrar horas y consumo de
maquinaria**, para imputar su coste real.

- CA: asignación a labor/parcela; coste calculado.

**HU-7.2** · _Could · V2_ — Como **agricultor**, quiero **alertas de mantenimiento preventivo**,
para alargar la vida de los equipos.

- CA: umbral por horas/fecha; historial de intervenciones.

---

## Épica 8 — Costes y rentabilidad

**HU-8.1** · _Must · V2_ — Como **agricultor**, quiero **ver el coste y la rentabilidad por
parcela y cultivo**, para saber dónde gano o pierdo.

- CA: agregación automática de labor/productos/máquina/agua/luz; rentabilidad neta; €/ha.

**HU-8.2** · _Should · V3_ — Como **admin**, quiero **comparar la rentabilidad entre socios y la
media**, para asesorar a los menos rentables.

- CA: ranking anonimizable; comparativa contra media de la cooperativa.

---

## Épica 9 — Inteligencia agrícola

**HU-9.1** · _Should · V2_ — Como **agricultor**, quiero **preguntar al Agente Agrónomo en
lenguaje natural**, para resolver dudas al instante.

- CA: usa histórico y stock; recomendación justificada; transcript auditable.

**HU-9.2** · _Should · V3_ — Como **agricultor**, quiero **subir una foto y obtener un
diagnóstico de plaga**, para actuar a tiempo.

- CA: diagnóstico + probabilidad + gravedad + tratamiento; opción de crear incidencia.

**HU-9.3** · _Could · V3_ — Como **admin**, quiero **un informe colectivo de riesgos** generado
por IA, para anticipar problemas de la cooperativa.

- CA: detecta riesgos agregados; informe descargable para directivos.

---

## Épica 10 — Memoria inteligente

**HU-10.1** · _Should · V2_ — Como **agente IA**, quiero **recordar el historial de la parcela y
las preferencias del agricultor**, para dar respuestas contextuales.

- CA: memoria USER/PARCEL/GLOBAL; recuperación por texto/tags; origen e importancia.

---

## Épica 11 — Alertas

**HU-11.1** · _Should · V2_ — Como **agricultor**, quiero **recibir alertas por email/WhatsApp**,
para no perderme nada crítico.

- CA: reglas configurables; severidades; confirmación de lectura; escalado.

---

## Épica 12 — Analítica

**HU-12.1** · _Should · V2_ — Como **técnico**, quiero **cuadros de mando con KPIs agrícolas**,
para tomar decisiones con datos.

- CA: producción, rendimiento, coste/ha, agua; comparativas; export.

---

## Épica 13 — Documentación

**HU-13.1** · _Could · V3_ — Como **agricultor**, quiero **subir facturas y certificados con OCR
y clasificación automática**, para tener todo ordenado y buscable.

- CA: OCR; clasificación por tipo; vinculación; búsqueda full-text.

---

## Épica 14 — Integraciones

**HU-14.1** · _Could · V3_ — Como **empresa agrícola**, quiero **conectar sensores IoT y datos
de satélite**, para enriquecer la analítica y las alertas.

- CA: API keys; ingesta de lecturas; índice NDVI por parcela; webhooks.

**HU-14.2** · _Won't-now · Enterprise_ — Como **cooperativa**, quiero **sincronizar con mi ERP
contable**, para unificar costes e ingresos.

- CA: conector con mapeo; reintentos; conciliación.
