<script setup lang="ts">
import { useAuthStore } from '~/stores/auth';
import type {
  Crop,
  FieldOperation,
  Paginated,
  Parcel,
  ParcelWeather,
  Sector,
} from '~/types/api';

const route = useRoute();
const api = useApi();
const toast = useToast();
const auth = useAuthStore();
const { number, date, dateTime } = useFormat();

const parcelId = route.params.id as string;

const ZONE_COLORS = [
  '#16a34a',
  '#0ea5e9',
  '#f59e0b',
  '#8b5cf6',
  '#ec4899',
  '#14b8a6',
  '#ef4444',
  '#84cc16',
];

const STATUS_META: Record<
  string,
  { label: string; tone: string; color: string }
> = {
  PLANNED: { label: 'Planificado', tone: 'sky', color: '#0ea5e9' },
  GROWING: { label: 'En crecimiento', tone: 'green', color: '#16a34a' },
  HARVESTED: { label: 'Cosechado', tone: 'violet', color: '#8b5cf6' },
  FAILED: { label: 'Fallido', tone: 'red', color: '#ef4444' },
};

// ---- Parcel ----
const {
  data: parcel,
  pending: parcelPending,
  error: parcelError,
  refresh: refreshParcel,
} = await useAsyncData(`parcel-${parcelId}`, () =>
  api.get<Parcel>(`/parcels/${parcelId}/`),
);

// ---- Related collections ----
const loading = ref(false);
const sectors = ref<Sector[]>([]);
const crops = ref<Crop[]>([]);

async function loadRelated() {
  loading.value = true;
  try {
    const [sec, cr] = await Promise.all([
      api.get<Paginated<Sector>>('/sectors/', { parcel: parcelId }),
      api.get<Paginated<Crop>>('/crops/', { parcel: parcelId }),
    ]);
    sectors.value = sec.results ?? [];
    crops.value = cr.results ?? [];
  } catch {
    toast.error('No se pudo cargar el detalle de la parcela.');
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadRelated();
  if (parcel.value?.latitude && parcel.value?.longitude) loadWeather();
});

// ---- Tabs ----
const tab = ref<'overview' | 'zones' | 'crops' | 'weather' | 'data'>(
  'overview',
);
watch(tab, (t) => {
  if (t === 'weather' && !weather.value && !weatherLoading.value) loadWeather();
});

// ---- Map ----
const mapRef = ref<any>(null);
const parcelPolygon = computed<number[][] | null>(
  () => (parcel.value?.polygon as number[][] | null) ?? null,
);
const parcelCenter = computed<[number, number] | null>(() => {
  const p = parcel.value;
  if (p?.latitude && p?.longitude)
    return [Number(p.latitude), Number(p.longitude)];
  return null;
});

const subPolygons = computed(() => {
  const zones = sectors.value
    .filter((s) => s.polygon?.length)
    .map((s) => ({
      id: s.id,
      name: s.name,
      color: s.color || ZONE_COLORS[0],
      points: s.polygon as number[][],
    }));
  if (pending.value)
    zones.push({
      id: '_pending',
      name: zoneForm.value.name || 'Nueva zona',
      color: zoneForm.value.color,
      points: pending.value.points,
    });
  return zones;
});

// ---- Digitizing ----
const digitizing = ref(false);
const drawArea = ref(0);
const pending = ref<{ points: number[][]; areaHa: number } | null>(null);
const zoneForm = ref({ name: '', color: ZONE_COLORS[0] });
const savingZone = ref(false);

function resetDigitizing() {
  digitizing.value = false;
  pending.value = null;
  drawArea.value = 0;
}

function startDigitizing() {
  pending.value = null;
  drawArea.value = 0;
  digitizing.value = true;
  tab.value = 'zones';
  nextTick(() => mapRef.value?.startDraw?.());
}

function onDrawProgress(e: { points: number[][]; areaHa: number }) {
  drawArea.value = e.areaHa;
}

function onDrawComplete(e: { points: number[][]; areaHa: number }) {
  pending.value = e;
  drawArea.value = e.areaHa;
  digitizing.value = false;
  const idx = sectors.value.length % ZONE_COLORS.length;
  zoneForm.value = {
    name: `Zona ${sectors.value.length + 1}`,
    color: ZONE_COLORS[idx],
  };
}

function cancelPending() {
  pending.value = null;
  drawArea.value = 0;
  resetDigitizing();
}

async function saveZone() {
  if (!pending.value) return;
  if (!zoneForm.value.name.trim()) {
    toast.error('Ponle un nombre a la zona.');
    return;
  }
  savingZone.value = true;
  try {
    await api.post<Sector>('/sectors/', {
      parcel: parcelId,
      name: zoneForm.value.name.trim(),
      area_ha: pending.value.areaHa.toFixed(4),
      color: zoneForm.value.color,
      polygon: pending.value.points,
    });
    toast.success('Zona digitalizada.');
    pending.value = null;
    drawArea.value = 0;
    await loadRelated();
  } catch {
    toast.error('No se pudo guardar la zona.');
  } finally {
    savingZone.value = false;
  }
}

async function deleteZone(s: Sector) {
  if (!confirm(`¿Eliminar la zona "${s.name}"?`)) return;
  try {
    await api.del(`/sectors/${s.id}/`);
    toast.success('Zona eliminada.');
    await loadRelated();
  } catch {
    toast.error('No se pudo eliminar la zona.');
  }
}

// ---- Crops ----
const showCropForm = ref(false);
const savingCrop = ref(false);
const cropBlank = () => ({
  sector: '' as string,
  species: '',
  variety: '',
  campaign: '',
  status: 'PLANNED',
  sowing_date: '',
  expected_harvest_date: '',
  expected_yield_kg: '',
});
const cropForm = ref(cropBlank());

function openCropForm(sectorId?: string) {
  cropForm.value = cropBlank();
  if (sectorId) cropForm.value.sector = sectorId;
  showCropForm.value = true;
}

const sectorOptions = computed(() =>
  sectors.value.map((s) => ({ value: s.id, label: s.name })),
);
const statusOptions = Object.entries(STATUS_META).map(([value, m]) => ({
  value,
  label: m.label,
}));

async function saveCrop() {
  if (!cropForm.value.species.trim() || !cropForm.value.campaign.trim()) {
    toast.error('Indica al menos especie y campaña.');
    return;
  }
  savingCrop.value = true;
  try {
    const payload: Record<string, unknown> = {
      parcel: parcelId,
      sector: cropForm.value.sector || null,
      species: cropForm.value.species.trim(),
      variety: cropForm.value.variety.trim(),
      campaign: cropForm.value.campaign.trim(),
      status: cropForm.value.status,
    };
    if (cropForm.value.sowing_date)
      payload.sowing_date = cropForm.value.sowing_date;
    if (cropForm.value.expected_harvest_date)
      payload.expected_harvest_date = cropForm.value.expected_harvest_date;
    if (cropForm.value.expected_yield_kg)
      payload.expected_yield_kg = cropForm.value.expected_yield_kg;
    await api.post<Crop>('/crops/', payload);
    toast.success('Cultivo añadido.');
    showCropForm.value = false;
    await loadRelated();
  } catch {
    toast.error('No se pudo añadir el cultivo.');
  } finally {
    savingCrop.value = false;
  }
}

async function deleteCrop(c: Crop) {
  if (!confirm(`¿Eliminar el cultivo "${c.species}"?`)) return;
  try {
    await api.del(`/crops/${c.id}/`);
    toast.success('Cultivo eliminado.');
    await loadRelated();
  } catch {
    toast.error('No se pudo eliminar el cultivo.');
  }
}

// ---- Field notebook (operations per crop) ----
const OPERATION_TYPES = [
  { value: 'SOWING', label: 'Siembra', emoji: '🌱' },
  { value: 'FERTILIZATION', label: 'Abonado', emoji: '🧪' },
  { value: 'IRRIGATION', label: 'Riego', emoji: '💧' },
  { value: 'TREATMENT', label: 'Tratamiento fitosanitario', emoji: '🛡️' },
  { value: 'PRUNING', label: 'Poda', emoji: '✂️' },
  { value: 'HARVEST', label: 'Cosecha', emoji: '🌾' },
  { value: 'OTHER', label: 'Otra labor', emoji: '📋' },
];
const opTypeOptions = OPERATION_TYPES.map((o) => ({
  value: o.value,
  label: o.label,
}));
function opMeta(t: string) {
  return OPERATION_TYPES.find((o) => o.value === t);
}

const cropOps = ref<Record<string, FieldOperation[]>>({});
const loadingOps = ref<Record<string, boolean>>({});

async function loadOps(cropId: string) {
  loadingOps.value[cropId] = true;
  try {
    const res = await api.get<Paginated<FieldOperation>>('/operations/', {
      crop: cropId,
    });
    cropOps.value[cropId] = res.results ?? [];
  } catch {
    cropOps.value[cropId] = [];
  } finally {
    loadingOps.value[cropId] = false;
  }
}

const showOpForm = ref(false);
const savingOp = ref(false);
const opCropId = ref('');
const opBlank = () => ({
  operation_type: 'OTHER',
  date: new Date().toISOString().slice(0, 10),
  description: '',
  area_ha: '',
});
const opForm = ref(opBlank());

function openOpForm(cropId: string) {
  opCropId.value = cropId;
  opForm.value = opBlank();
  showOpForm.value = true;
}

async function saveOp() {
  if (!opForm.value.date) {
    toast.error('Indica la fecha de la labor.');
    return;
  }
  savingOp.value = true;
  try {
    const payload: Record<string, unknown> = {
      crop: opCropId.value,
      operation_type: opForm.value.operation_type,
      date: opForm.value.date,
      description: opForm.value.description.trim(),
    };
    if (opForm.value.area_ha) payload.area_ha = opForm.value.area_ha;
    await api.post('/operations/', payload);
    toast.success('Labor registrada en el cuaderno.');
    showOpForm.value = false;
    await loadOps(opCropId.value);
  } catch {
    toast.error('No se pudo registrar la labor.');
  } finally {
    savingOp.value = false;
  }
}

async function deleteOp(cropId: string, op: FieldOperation) {
  if (!confirm('¿Eliminar esta labor del cuaderno?')) return;
  try {
    await api.del(`/operations/${op.id}/`);
    toast.success('Labor eliminada.');
    await loadOps(cropId);
  } catch {
    toast.error('No se pudo eliminar la labor.');
  }
}

// ---- Phytosanitary treatments (consume stock) ----
const products = ref<Product[]>([]);
const productsLoaded = ref(false);
const productOptions = computed(() =>
  products.value.map((p) => ({
    value: p.id,
    label: `${p.name} · ${p.current_stock} ${p.unit}`,
  })),
);

async function loadProducts() {
  if (productsLoaded.value) return;
  try {
    const res = await api.get<Paginated<Product>>('/products/');
    products.value = res.results ?? [];
  } catch {
    products.value = [];
  } finally {
    productsLoaded.value = true;
  }
}

const cropTreatments = ref<Record<string, Treatment[]>>({});

async function loadTreatments(cropId: string) {
  try {
    const res = await api.get<Paginated<Treatment>>('/treatments/', {
      crop: cropId,
    });
    cropTreatments.value[cropId] = res.results ?? [];
  } catch {
    cropTreatments.value[cropId] = [];
  }
}

const showTrForm = ref(false);
const savingTr = ref(false);
const trCropId = ref('');
const trBlank = () => ({
  product: '',
  date: new Date().toISOString().slice(0, 10),
  dose: '',
  dose_unit: 'L/ha',
  total_quantity: '',
  target_pest: '',
  weather: '',
});
const trForm = ref(trBlank());

const trProduct = computed(() =>
  products.value.find((p) => p.id === trForm.value.product),
);

function openTrForm(cropId: string) {
  trCropId.value = cropId;
  trForm.value = trBlank();
  loadProducts();
  showTrForm.value = true;
}

async function saveTr() {
  if (
    !trForm.value.product ||
    !trForm.value.dose ||
    !trForm.value.total_quantity
  ) {
    toast.error('Producto, dosis y cantidad total son obligatorios.');
    return;
  }
  savingTr.value = true;
  try {
    await api.post('/treatments/', {
      crop: trCropId.value,
      product: trForm.value.product,
      date: trForm.value.date,
      dose: trForm.value.dose,
      dose_unit: trForm.value.dose_unit,
      total_quantity: trForm.value.total_quantity,
      target_pest: trForm.value.target_pest.trim(),
      weather: trForm.value.weather.trim(),
    });
    toast.success('Tratamiento registrado. Stock consumido (FEFO).');
    showTrForm.value = false;
    productsLoaded.value = false;
    await Promise.all([
      loadTreatments(trCropId.value),
      loadOps(trCropId.value),
    ]);
  } catch (err: any) {
    const data = err?.response?._data;
    const msg =
      data?.total_quantity?.[0] ||
      data?.product?.[0] ||
      data?.detail ||
      'No se pudo registrar el tratamiento.';
    toast.error(msg);
  } finally {
    savingTr.value = false;
  }
}

async function deleteTr(cropId: string, tr: Treatment) {
  if (!confirm('¿Eliminar este tratamiento del cuaderno?')) return;
  try {
    await api.del(`/treatments/${tr.id}/`);
    toast.success('Tratamiento eliminado.');
    await loadTreatments(cropId);
  } catch {
    toast.error('No se pudo eliminar el tratamiento.');
  }
}

// ---- PDF export (printable report) ----
const exporting = ref(false);

function esc(v: unknown): string {
  return String(v ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

async function exportPdf() {
  const p = parcel.value;
  if (!p) return;
  exporting.value = true;
  try {
    // Make sure every crop's notebook is loaded so it appears in the report.
    await Promise.all(
      crops.value.flatMap((c) => {
        const tasks = [];
        if (cropOps.value[c.id] === undefined) tasks.push(loadOps(c.id));
        if (cropTreatments.value[c.id] === undefined)
          tasks.push(loadTreatments(c.id));
        return tasks;
      }),
    );

    const generated = new Date().toLocaleDateString('es-ES', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    });
    const coop = auth.cooperative?.name ?? 'AgroControl OS';

    const zonesRows =
      sectors.value.length === 0
        ? '<tr><td colspan="2" class="muted">Sin zonas digitalizadas.</td></tr>'
        : sectors.value
            .map(
              (s) => `<tr>
                <td><span class="dot" style="background:${esc(
                  s.color || '#16a34a',
                )}"></span>${esc(s.name)}</td>
                <td class="num">${
                  s.area_ha ? number(Number(s.area_ha), 2) + ' ha' : '—'
                }</td>
              </tr>`,
            )
            .join('');

    const cropsHtml =
      crops.value.length === 0
        ? '<p class="muted">Sin cultivos registrados.</p>'
        : crops.value
            .map((c) => {
              const ops = cropOps.value[c.id] ?? [];
              const opsHtml = ops.length
                ? `<ul class="ops">${ops
                    .map(
                      (op) =>
                        `<li><b>${esc(
                          opMeta(op.operation_type)?.label ??
                            op.operation_type_display,
                        )}</b> · ${esc(date(op.date))}${
                          op.area_ha
                            ? ' · ' + number(Number(op.area_ha), 2) + ' ha'
                            : ''
                        }${op.description ? ' — ' + esc(op.description) : ''}</li>`,
                    )
                    .join('')}</ul>`
                : '<p class="muted small">Sin labores registradas.</p>';
              const trs = cropTreatments.value[c.id] ?? [];
              const trsHtml = trs.length
                ? `<div class="crop-label">Tratamientos fitosanitarios</div>
                  <ul class="ops">${trs
                    .map(
                      (tr) =>
                        `<li>🛡️ <b>${esc(tr.product_name)}</b> · ${esc(
                          date(tr.date),
                        )} · ${number(Number(tr.dose), 2)} ${esc(
                          tr.dose_unit,
                        )} · ${number(
                          Number(tr.total_quantity),
                          2,
                        )} total${tr.target_pest ? ' — ' + esc(tr.target_pest) : ''}${
                          tr.safety_interval_ok
                            ? ''
                            : ' <b style="color:#dc2626">[plazo de seguridad incumplido]</b>'
                        }</li>`,
                    )
                    .join('')}</ul>`
                : '';
              const meta = STATUS_META[c.status];
              return `<div class="crop">
                <div class="crop-head">
                  <span class="crop-title">${esc(c.species)}${
                    c.variety ? ' · ' + esc(c.variety) : ''
                  }</span>
                  <span class="badge">${esc(meta?.label ?? c.status)}</span>
                </div>
                <div class="crop-meta">${esc(c.campaign)}${
                  c.sowing_date ? ' · siembra ' + esc(date(c.sowing_date)) : ''
                }${
                  c.expected_harvest_date
                    ? ' · cosecha ' + esc(date(c.expected_harvest_date))
                    : ''
                }${
                  c.expected_yield_kg
                    ? ' · ' +
                      number(Number(c.expected_yield_kg), 0) +
                      ' kg prev.'
                    : ''
                }</div>
                <div class="crop-label">Cuaderno de campo</div>
                ${opsHtml}
                ${trsHtml}
              </div>`;
            })
            .join('');

    const w = weather.value;
    const wt = weekTotals.value;
    const weatherHtml = w
      ? `<div class="section">
          <h2>Clima · próximos 7 días</h2>
          <div class="kpis">
            <div class="kpi"><div class="kpi-v">${number(
              wt.rain,
              1,
            )} mm</div><div class="kpi-l">Lluvia</div></div>
            <div class="kpi"><div class="kpi-v">${number(
              wt.et0,
              1,
            )} mm</div><div class="kpi-l">ET₀</div></div>
            <div class="kpi"><div class="kpi-v">${
              wt.balance >= 0 ? '+' : ''
            }${number(
              wt.balance,
              1,
            )} mm</div><div class="kpi-l">Balance hídrico</div></div>
          </div>
        </div>`
      : '';

    const html = `<!doctype html><html lang="es"><head><meta charset="utf-8">
      <title>Ficha de parcela · ${esc(p.name)}</title>
      <style>
        * { box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #1e293b; margin: 0; padding: 32px 36px; }
        .top { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #16a34a; padding-bottom: 14px; margin-bottom: 20px; }
        .brand { font-size: 12px; color: #16a34a; font-weight: 700; text-transform: uppercase; letter-spacing: .04em; }
        h1 { font-size: 24px; margin: 4px 0 0; }
        .sub { color: #64748b; font-size: 12px; margin-top: 4px; }
        .gen { text-align: right; font-size: 11px; color: #94a3b8; }
        h2 { font-size: 13px; text-transform: uppercase; letter-spacing: .04em; color: #475569; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; margin: 26px 0 12px; }
        .section { margin-bottom: 8px; }
        .kpis { display: flex; gap: 12px; }
        .kpi { flex: 1; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px 12px; text-align: center; }
        .kpi-v { font-size: 18px; font-weight: 700; }
        .kpi-l { font-size: 10px; color: #94a3b8; text-transform: uppercase; letter-spacing: .03em; }
        table { width: 100%; border-collapse: collapse; font-size: 12px; }
        td { padding: 6px 8px; border-bottom: 1px solid #f1f5f9; }
        .num { text-align: right; font-variant-numeric: tabular-nums; }
        .dot { display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 7px; vertical-align: middle; }
        .info { display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px 24px; font-size: 12px; }
        .info div { display: flex; justify-content: space-between; border-bottom: 1px solid #f1f5f9; padding: 5px 0; }
        .info span:first-child { color: #94a3b8; }
        .crop { border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px 14px; margin-bottom: 10px; page-break-inside: avoid; }
        .crop-head { display: flex; justify-content: space-between; align-items: center; }
        .crop-title { font-weight: 700; font-size: 14px; }
        .badge { font-size: 10px; background: #f1f5f9; color: #475569; border-radius: 999px; padding: 2px 9px; }
        .crop-meta { font-size: 11px; color: #64748b; margin-top: 3px; }
        .crop-label { font-size: 10px; text-transform: uppercase; letter-spacing: .04em; color: #94a3b8; margin: 9px 0 4px; }
        .ops { margin: 0; padding-left: 18px; font-size: 12px; }
        .ops li { margin-bottom: 3px; }
        .muted { color: #94a3b8; font-size: 12px; }
        .small { font-size: 11px; }
        .foot { margin-top: 28px; border-top: 1px solid #e2e8f0; padding-top: 10px; font-size: 10px; color: #cbd5e1; text-align: center; }
        @media print { body { padding: 0; } }
      </style></head><body>
      <div class="top">
        <div>
          <div class="brand">${esc(coop)}</div>
          <h1>${esc(p.name)}</h1>
          <div class="sub">${esc(p.farm_name)} · ${
            p.is_active ? 'Activa' : 'Inactiva'
          }</div>
        </div>
        <div class="gen">Ficha generada<br>${esc(generated)}</div>
      </div>

      <div class="kpis">
        <div class="kpi"><div class="kpi-v">${number(
          Number(p.area_ha),
          2,
        )}</div><div class="kpi-l">Superficie (ha)</div></div>
        <div class="kpi"><div class="kpi-v">${
          sectors.value.length
        }</div><div class="kpi-l">Zonas</div></div>
        <div class="kpi"><div class="kpi-v">${
          crops.value.length
        }</div><div class="kpi-l">Cultivos</div></div>
        <div class="kpi"><div class="kpi-v">${number(
          digitizedArea.value,
          2,
        )}</div><div class="kpi-l">Digitalizado (ha)</div></div>
      </div>

      <h2>Datos de la parcela</h2>
      <div class="info">
        <div><span>Explotación</span><b>${esc(p.farm_name)}</b></div>
        <div><span>Superficie</span><b>${number(
          Number(p.area_ha),
          2,
        )} ha</b></div>
        <div><span>Referencia SIGPAC</span><b>${
          esc(p.sigpac_ref) || '—'
        }</b></div>
        <div><span>Tipo de suelo</span><b>${esc(p.soil_type) || '—'}</b></div>
        <div><span>Municipio</span><b>${esc(p.municipality) || '—'}</b></div>
        <div><span>Provincia</span><b>${esc(p.province) || '—'}</b></div>
        <div><span>Ubicación catastral</span><b>${
          esc(p.address) || '—'
        }</b></div>
        <div><span>Coordenadas</span><b>${
          p.latitude && p.longitude
            ? esc(Number(p.latitude).toFixed(5)) +
              ', ' +
              esc(Number(p.longitude).toFixed(5))
            : '—'
        }</b></div>
        <div><span>Estado</span><b>${
          p.is_active ? 'Activa' : 'Inactiva'
        }</b></div>
      </div>

      <h2>Zonas / sectores</h2>
      <table><tbody>${zonesRows}</tbody></table>

      <h2>Cultivos y cuaderno de campo</h2>
      ${cropsHtml}

      ${weatherHtml}

      <div class="foot">Generado con AgroControl OS · ${esc(generated)}</div>
    </body></html>`;

    const iframe = document.createElement('iframe');
    iframe.style.cssText =
      'position:fixed;right:0;bottom:0;width:0;height:0;border:0;';
    document.body.appendChild(iframe);
    const win = iframe.contentWindow;
    if (!win) {
      document.body.removeChild(iframe);
      toast.error('No se pudo generar el PDF.');
      return;
    }
    win.document.open();
    win.document.write(html);
    win.document.close();
    win.focus();
    setTimeout(() => {
      win.print();
      setTimeout(() => document.body.removeChild(iframe), 1500);
    }, 300);
  } catch {
    toast.error('No se pudo generar el PDF.');
  } finally {
    exporting.value = false;
  }
}

// ---- Edit parcel ----
const showEdit = ref(false);
const savingEdit = ref(false);
const editForm = ref({
  name: '',
  soil_type: '',
  sigpac_ref: '',
  is_active: true,
});

function openEdit() {
  if (!parcel.value) return;
  editForm.value = {
    name: parcel.value.name,
    soil_type: parcel.value.soil_type || '',
    sigpac_ref: parcel.value.sigpac_ref || '',
    is_active: parcel.value.is_active,
  };
  showEdit.value = true;
}

async function saveEdit() {
  if (!editForm.value.name.trim()) {
    toast.error('El nombre es obligatorio.');
    return;
  }
  savingEdit.value = true;
  try {
    await api.patch<Parcel>(`/parcels/${parcelId}/`, {
      name: editForm.value.name.trim(),
      soil_type: editForm.value.soil_type.trim(),
      sigpac_ref: editForm.value.sigpac_ref.trim(),
      is_active: editForm.value.is_active,
    });
    toast.success('Parcela actualizada.');
    showEdit.value = false;
    await refreshParcel();
  } catch {
    toast.error('No se pudo actualizar la parcela.');
  } finally {
    savingEdit.value = false;
  }
}

// ---- Cadastre zone enrichment ----
interface CadastreZoneResult {
  reference: string;
  province?: string | null;
  municipality?: string | null;
  address?: string | null;
}
const enrichingZone = ref(false);
const canEnrichZone = computed(
  () =>
    !!parcel.value?.sigpac_ref &&
    !parcel.value?.municipality &&
    !parcel.value?.province,
);

async function enrichZone() {
  const refValue = parcel.value?.sigpac_ref?.trim();
  if (!refValue) {
    toast.error('La parcela no tiene referencia catastral.');
    return;
  }
  enrichingZone.value = true;
  try {
    const res = await api.get<CadastreZoneResult>('/parcels/lookup/', {
      ref: refValue,
    });
    await api.patch<Parcel>(`/parcels/${parcelId}/`, {
      province: res.province ?? '',
      municipality: res.municipality ?? '',
      address: res.address ?? '',
    });
    if (res.municipality || res.province)
      toast.success(
        `Zona recuperada · ${[res.municipality, res.province]
          .filter(Boolean)
          .join(', ')}`,
      );
    else
      toast.info('El catastro no devolvió datos de zona para esta referencia.');
    await refreshParcel();
  } catch (err: any) {
    toast.error(
      err?.response?.status === 404
        ? 'No se encontró la parcela en el catastro.'
        : 'No se pudieron recuperar los datos de zona.',
    );
  } finally {
    enrichingZone.value = false;
  }
}

// ---- Delete parcel ----
const showDelete = ref(false);
const deleting = ref(false);

async function deleteParcel() {
  deleting.value = true;
  try {
    await api.del(`/parcels/${parcelId}/`);
    toast.success('Parcela eliminada.');
    await navigateTo('/parcels');
  } catch {
    toast.error('No se pudo eliminar la parcela.');
    deleting.value = false;
  }
}

// ---- Weather ----
const weather = ref<ParcelWeather | null>(null);
const weatherLoading = ref(false);
const weatherError = ref('');

const WEEKDAYS = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
function weekday(iso: string): string {
  const d = new Date(iso + 'T00:00:00');
  return WEEKDAYS[d.getDay()] ?? '';
}
const weekTotals = computed(() => {
  const days = weather.value?.daily ?? [];
  const rain = days.reduce((s, d) => s + (d.precip_mm ?? 0), 0);
  const et0 = days.reduce((s, d) => s + (d.et0_mm ?? 0), 0);
  return { rain, et0, balance: rain - et0 };
});

// Irrigation recommendation from the 7-day water balance.
// 1 mm of water = 10 m³ per hectare.
const irrigation = computed(() => {
  const deficit = Math.max(0, -weekTotals.value.balance);
  const area = Number(parcel.value?.area_ha || 0);
  const mmPerDay = deficit / 7;
  let level: 'none' | 'low' | 'moderate' | 'high' = 'none';
  if (deficit >= 25) level = 'high';
  else if (deficit >= 12) level = 'moderate';
  else if (deficit > 0) level = 'low';
  // Next forecast day with meaningful rain (≥ 2 mm).
  const nextRain = (weather.value?.daily ?? []).find(
    (d) => (d.precip_mm ?? 0) >= 2,
  );
  return {
    deficit,
    mmPerDay,
    m3PerHa: deficit * 10,
    m3Total: deficit * 10 * area,
    level,
    nextRain: nextRain?.date ?? null,
    nextRainMm: nextRain?.precip_mm ?? 0,
  };
});

const IRRIGATION_META: Record<
  string,
  { label: string; tone: string; bg: string; text: string; advice: string }
> = {
  none: {
    label: 'Sin riego necesario',
    tone: 'green',
    bg: 'from-brand-500 to-emerald-600',
    text: 'text-brand-700',
    advice:
      'La lluvia prevista cubre la demanda de los cultivos. No se requiere riego esta semana.',
  },
  low: {
    label: 'Riego ligero',
    tone: 'sky',
    bg: 'from-sky-500 to-cyan-600',
    text: 'text-sky-700',
    advice:
      'Déficit hídrico leve. Un riego de apoyo mantendrá la humedad óptima del suelo.',
  },
  moderate: {
    label: 'Riego moderado',
    tone: 'amber',
    bg: 'from-amber-500 to-orange-500',
    text: 'text-amber-700',
    advice:
      'Déficit hídrico notable. Programa riego para compensar la evapotranspiración.',
  },
  high: {
    label: 'Riego prioritario',
    tone: 'red',
    bg: 'from-red-500 to-rose-600',
    text: 'text-red-700',
    advice:
      'Déficit hídrico elevado. Riega cuanto antes para evitar estrés hídrico en los cultivos.',
  },
};

async function loadWeather() {
  if (!parcel.value) return;
  if (!parcel.value.latitude || !parcel.value.longitude) {
    weatherError.value =
      'La parcela no tiene coordenadas. Localízala en el mapa para ver el clima.';
    return;
  }
  weatherLoading.value = true;
  weatherError.value = '';
  try {
    weather.value = await api.get<ParcelWeather>(
      `/parcels/${parcelId}/weather/`,
    );
  } catch {
    weatherError.value = 'No se pudo obtener la previsión meteorológica.';
  } finally {
    weatherLoading.value = false;
  }
}

// ---- Derived metrics ----
const digitizedArea = computed(() =>
  sectors.value.reduce((s, z) => s + Number(z.area_ha || 0), 0),
);
const digitizedPct = computed(() => {
  const total = Number(parcel.value?.area_ha || 0);
  if (!total) return 0;
  return Math.min(100, (digitizedArea.value / total) * 100);
});
const activeCrops = computed(
  () =>
    crops.value.filter((c) => c.status === 'GROWING' || c.status === 'PLANNED')
      .length,
);

const cropsBySector = computed(() => {
  const map: Record<string, Crop[]> = { _none: [] };
  for (const s of sectors.value) map[s.id] = [];
  for (const c of crops.value) {
    const key = c.sector && map[c.sector] ? c.sector : '_none';
    map[key].push(c);
  }
  return map;
});

// ---- Crop phenology ----
// Generic phenological stages applicable to most annual/perennial crops,
// each occupying a fraction of the sowing→harvest cycle.
interface PhenoStage {
  key: string;
  label: string;
  emoji: string;
  start: number; // fraction of cycle [0–1]
}
const PHENO_STAGES: PhenoStage[] = [
  { key: 'germination', label: 'Germinación', emoji: '🌱', start: 0 },
  {
    key: 'vegetative',
    label: 'Crecimiento vegetativo',
    emoji: '🌿',
    start: 0.1,
  },
  { key: 'flowering', label: 'Floración', emoji: '🌼', start: 0.4 },
  { key: 'fruiting', label: 'Desarrollo del fruto', emoji: '🍃', start: 0.6 },
  { key: 'maturity', label: 'Maduración', emoji: '🌾', start: 0.85 },
];

const expandedCrop = ref<string | null>(null);
function toggleCrop(id: string) {
  expandedCrop.value = expandedCrop.value === id ? null : id;
  if (expandedCrop.value === id && cropOps.value[id] === undefined) {
    loadOps(id);
    loadTreatments(id);
  }
}

function dayDiff(a: string, b: string): number {
  const ms = new Date(b).getTime() - new Date(a).getTime();
  return Math.round(ms / 86_400_000);
}

function cropPhenology(c: Crop) {
  if (!c.sowing_date || !c.expected_harvest_date) return null;
  const today = new Date().toISOString().slice(0, 10);
  const total = dayDiff(c.sowing_date, c.expected_harvest_date);
  if (total <= 0) return null;
  const elapsed = dayDiff(c.sowing_date, today);
  // Harvested crops are shown as complete.
  const rawProgress = c.status === 'HARVESTED' ? 1 : elapsed / total;
  const progress = Math.max(0, Math.min(1, rawProgress));
  const remaining = Math.max(0, total - elapsed);

  let currentIndex = 0;
  for (let i = 0; i < PHENO_STAGES.length; i++) {
    if (progress >= PHENO_STAGES[i].start) currentIndex = i;
  }
  if (c.status === 'PLANNED' && elapsed < 0) currentIndex = -1;

  const stages = PHENO_STAGES.map((s, i) => {
    const end = PHENO_STAGES[i + 1]?.start ?? 1;
    return {
      ...s,
      end,
      done: progress >= end,
      active: i === currentIndex && c.status !== 'HARVESTED',
    };
  });

  return {
    total,
    elapsed: Math.max(0, elapsed),
    remaining,
    progressPct: Math.round(progress * 100),
    currentIndex,
    current: currentIndex >= 0 ? PHENO_STAGES[currentIndex] : null,
    stages,
    notStarted: elapsed < 0,
  };
}

const cropStatusSegments = computed(() => {
  const counts: Record<string, number> = {};
  for (const c of crops.value) counts[c.status] = (counts[c.status] || 0) + 1;
  return Object.entries(counts).map(([k, v]) => ({
    value: v,
    color: STATUS_META[k]?.color || '#94a3b8',
    label: STATUS_META[k]?.label || k,
  }));
});

const zoneSegments = computed(() =>
  sectors.value
    .filter((s) => Number(s.area_ha) > 0)
    .map((s) => ({
      value: Number(s.area_ha),
      color: s.color || ZONE_COLORS[0],
      label: s.name,
    })),
);

const expectedYield = computed(() =>
  crops.value.reduce((s, c) => s + Number(c.expected_yield_kg || 0), 0),
);

useHead(() => ({
  title: parcel.value ? `${parcel.value.name} · Parcela` : 'Parcela',
}));
</script>

<template>
  <div class="p-6 lg:p-8 space-y-6 w-full">
    <!-- Breadcrumb -->
    <NuxtLink
      to="/parcels"
      class="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-brand-700 transition"
    >
      <svg
        class="w-4 h-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M15 19l-7-7 7-7"
        />
      </svg>
      Volver a parcelas
    </NuxtLink>

    <div v-if="parcelPending" class="space-y-6">
      <UiSkeleton />
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <UiCard v-for="i in 4" :key="i"><UiSkeleton /></UiCard>
      </div>
    </div>

    <EmptyState
      v-else-if="parcelError || !parcel"
      title="Parcela no encontrada"
      message="No se pudo cargar esta parcela. Puede que haya sido eliminada."
    >
      <template #action>
        <NuxtLink
          to="/parcels"
          class="text-sm px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition"
        >
          Volver a parcelas
        </NuxtLink>
      </template>
    </EmptyState>

    <template v-else>
      <!-- Header -->
      <div
        class="flex flex-wrap items-start justify-between gap-4 animate-fade-in-up"
      >
        <div class="flex items-stretch gap-3 min-w-0">
          <span
            class="w-1 rounded-full bg-gradient-to-b from-brand-400 to-brand-600 shrink-0"
          />
          <div class="min-w-0">
            <p class="text-xs font-medium text-brand-600">
              {{ parcel.farm_name }}
            </p>
            <h1
              class="text-2xl font-bold text-slate-800 tracking-tight truncate"
            >
              {{ parcel.name }}
            </h1>
            <div class="mt-1.5 flex flex-wrap items-center gap-2 text-xs">
              <UiBadge :tone="parcel.is_active ? 'green' : 'slate'" dot>
                {{ parcel.is_active ? 'Activa' : 'Inactiva' }}
              </UiBadge>
              <span class="text-slate-400"
                >{{ number(Number(parcel.area_ha), 2) }} ha</span
              >
              <span v-if="parcel.sigpac_ref" class="text-slate-400 font-mono">
                · {{ parcel.sigpac_ref }}
              </span>
              <span v-if="parcel.soil_type" class="text-slate-400">
                · {{ parcel.soil_type }}
              </span>
            </div>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button
            class="text-sm px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 transition inline-flex items-center gap-1.5"
            title="Exportar ficha de la parcela a PDF"
            @click="exportPdf"
          >
            <svg
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            PDF
          </button>
          <button
            class="text-sm px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 transition"
            @click="openEdit"
          >
            Editar
          </button>
          <button
            class="text-sm px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 transition inline-flex items-center gap-1.5"
            @click="startDigitizing"
          >
            <svg
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
              />
            </svg>
            Digitalizar zona
          </button>
          <button
            class="text-sm px-3 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition shadow-glow"
            @click="openCropForm()"
          >
            + Añadir cultivo
          </button>
        </div>
      </div>

      <!-- KPI cards -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Superficie"
          :value="Number(parcel.area_ha)"
          :decimals="2"
          suffix=" ha"
          tone="brand"
          icon="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
        />
        <StatCard
          label="Zonas digitalizadas"
          :value="sectors.length"
          tone="sky"
          icon="M4 6h16M4 12h16M4 18h16"
        />
        <StatCard
          label="Cultivos activos"
          :value="activeCrops"
          tone="violet"
          icon="M12 6.5C9 4 4 4 4 4v14s5 0 8 2.5M12 6.5C15 4 20 4 20 4v14s-5 0-8 2.5M12 6.5v14"
        />
        <StatCard
          label="Superficie digitalizada"
          :value="digitizedPct"
          :decimals="0"
          suffix=" %"
          tone="amber"
          icon="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </div>

      <!-- Map + side panel -->
      <div class="grid lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2">
          <UiCard :padded="false">
            <div class="relative">
              <ClientOnly>
                <ParcelMap
                  ref="mapRef"
                  :polygon="parcelPolygon"
                  :sub-polygons="subPolygons"
                  :center="parcelCenter"
                  :mode="digitizing ? 'draw' : 'view'"
                  :height="420"
                  @draw-progress="onDrawProgress"
                  @draw-complete="onDrawComplete"
                />
                <template #fallback>
                  <div class="h-[420px] grid place-items-center bg-slate-50">
                    <UiSkeleton />
                  </div>
                </template>
              </ClientOnly>

              <!-- Digitizing toolbar -->
              <div
                v-if="digitizing"
                class="absolute top-2 right-2 z-[600] bg-white/95 rounded-xl shadow-lg ring-1 ring-slate-100 p-2 flex items-center gap-2"
              >
                <span class="text-xs text-slate-500 px-1"
                  >≈ {{ number(drawArea, 4) }} ha</span
                >
                <button
                  class="text-xs px-2 py-1 rounded-lg border border-slate-200 hover:bg-slate-50"
                  @click="mapRef?.undoPoint?.()"
                >
                  Deshacer
                </button>
                <button
                  class="text-xs px-2 py-1 rounded-lg border border-slate-200 hover:bg-slate-50"
                  @click="mapRef?.finishDraw?.()"
                >
                  Cerrar
                </button>
                <button
                  class="text-xs px-2 py-1 rounded-lg bg-slate-100 hover:bg-slate-200"
                  @click="cancelPending"
                >
                  Cancelar
                </button>
              </div>
            </div>

            <!-- Pending zone save -->
            <div
              v-if="pending"
              class="border-t border-amber-200 bg-amber-50 p-4 space-y-3"
            >
              <p class="text-sm font-medium text-amber-800">
                Nueva zona · ≈ {{ number(pending.areaHa, 4) }} ha
              </p>
              <div class="flex items-end gap-3 flex-wrap">
                <div class="flex-1 min-w-[180px]">
                  <UiField label="Nombre de la zona">
                    <UiInput
                      v-model="zoneForm.name"
                      placeholder="Ej. Olivar norte"
                    />
                  </UiField>
                </div>
                <div class="flex items-center gap-1.5">
                  <button
                    v-for="c in ZONE_COLORS"
                    :key="c"
                    class="w-6 h-6 rounded-full ring-2 transition"
                    :class="
                      zoneForm.color === c
                        ? 'ring-slate-700 scale-110'
                        : 'ring-transparent'
                    "
                    :style="{ backgroundColor: c }"
                    @click="zoneForm.color = c"
                  />
                </div>
              </div>
              <div class="flex justify-end gap-2">
                <button
                  class="text-sm px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-white transition"
                  @click="cancelPending"
                >
                  Descartar
                </button>
                <button
                  class="text-sm px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition disabled:opacity-50"
                  :disabled="savingZone"
                  @click="saveZone"
                >
                  {{ savingZone ? 'Guardando…' : 'Guardar zona' }}
                </button>
              </div>
            </div>
          </UiCard>
        </div>

        <!-- Side: weather snapshot + quick facts -->
        <div class="space-y-4">
          <div
            v-if="weather"
            class="rounded-2xl p-4 text-white bg-gradient-to-br from-sky-500 to-brand-600 shadow-glow"
          >
            <div class="flex items-center justify-between">
              <div>
                <p class="text-xs text-white/80">Tiempo ahora</p>
                <p class="text-3xl font-bold tabular-nums">
                  {{ number(weather.current.temperature ?? 0, 1) }}°C
                </p>
                <p class="text-sm text-white/90">
                  {{ weather.current.weather.label }}
                </p>
              </div>
              <div class="text-5xl">{{ weather.current.weather.emoji }}</div>
            </div>
            <div
              class="mt-3 grid grid-cols-3 gap-2 text-center text-xs text-white/90"
            >
              <div class="rounded-lg bg-white/15 py-1.5">
                <p class="font-semibold tabular-nums">
                  {{ weather.current.humidity ?? '—' }}%
                </p>
                <p class="text-white/70">Humedad</p>
              </div>
              <div class="rounded-lg bg-white/15 py-1.5">
                <p class="font-semibold tabular-nums">
                  {{ number(weather.current.wind_speed ?? 0, 0) }}
                </p>
                <p class="text-white/70">km/h</p>
              </div>
              <div class="rounded-lg bg-white/15 py-1.5">
                <p class="font-semibold tabular-nums">
                  {{ number(weather.current.precipitation ?? 0, 1) }}
                </p>
                <p class="text-white/70">mm</p>
              </div>
            </div>
          </div>
          <div
            v-else-if="weatherLoading"
            class="rounded-2xl bg-white ring-1 ring-slate-100 p-4"
          >
            <UiSkeleton />
          </div>

          <UiCard :padded="false">
            <div class="px-5 py-4 border-b border-slate-100">
              <h3
                class="text-sm font-semibold text-slate-700 flex items-center gap-2"
              >
                <svg
                  class="w-4 h-4 text-brand-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                Ficha rápida
              </h3>
            </div>
            <dl class="divide-y divide-slate-100 text-sm">
              <div class="flex items-center justify-between gap-3 px-5 py-3">
                <dt class="text-slate-400 shrink-0">Explotación</dt>
                <dd class="font-medium text-slate-700 text-right truncate">
                  {{ parcel.farm_name }}
                </dd>
              </div>
              <div class="flex items-center justify-between gap-3 px-5 py-3">
                <dt class="text-slate-400 shrink-0">Referencia</dt>
                <dd class="font-mono text-slate-700 text-right truncate">
                  {{ parcel.sigpac_ref || '—' }}
                </dd>
              </div>
              <div class="flex items-center justify-between gap-3 px-5 py-3">
                <dt class="text-slate-400 shrink-0">Tipo de suelo</dt>
                <dd class="text-slate-700 text-right truncate">
                  {{ parcel.soil_type || '—' }}
                </dd>
              </div>
              <div
                v-if="parcel.municipality"
                class="flex items-center justify-between gap-3 px-5 py-3"
              >
                <dt class="text-slate-400 shrink-0">Municipio</dt>
                <dd class="text-slate-700 text-right truncate">
                  {{ parcel.municipality }}
                </dd>
              </div>
              <div
                v-if="parcel.province"
                class="flex items-center justify-between gap-3 px-5 py-3"
              >
                <dt class="text-slate-400 shrink-0">Provincia</dt>
                <dd class="text-slate-700 text-right truncate">
                  {{ parcel.province }}
                </dd>
              </div>
              <div v-if="parcel.address" class="px-5 py-3">
                <dt class="text-slate-400 mb-1">Ubicación catastral</dt>
                <dd class="text-slate-700 text-sm leading-snug">
                  {{ parcel.address }}
                </dd>
              </div>
              <div v-if="canEnrichZone" class="px-5 py-3">
                <button
                  type="button"
                  class="w-full inline-flex items-center justify-center gap-1.5 text-sm font-medium px-3 py-2 rounded-lg bg-brand-50 text-brand-700 ring-1 ring-brand-200 hover:bg-brand-100 transition disabled:opacity-50"
                  :disabled="enrichingZone"
                  title="Recuperar provincia, municipio y ubicación desde el Catastro"
                  @click="enrichZone"
                >
                  <svg
                    v-if="!enrichingZone"
                    class="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                    />
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                  <svg
                    v-else
                    class="w-4 h-4 animate-spin"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      class="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      stroke-width="4"
                    />
                    <path
                      class="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    />
                  </svg>
                  {{
                    enrichingZone ? 'Consultando…' : 'Recuperar datos de zona'
                  }}
                </button>
              </div>
              <div class="px-5 py-3">
                <div class="flex items-center justify-between gap-3 mb-1.5">
                  <dt class="text-slate-400">Digitalizado</dt>
                  <dd class="text-slate-700 tabular-nums">
                    {{ number(digitizedArea, 2) }} /
                    {{ number(Number(parcel.area_ha), 2) }} ha
                  </dd>
                </div>
                <div class="h-1.5 rounded-full bg-slate-100 overflow-hidden">
                  <div
                    class="h-full rounded-full bg-gradient-to-r from-brand-400 to-brand-600 transition-all duration-700"
                    :style="{ width: `${digitizedPct}%` }"
                  />
                </div>
              </div>
              <div
                v-if="parcel.latitude && parcel.longitude"
                class="flex items-center justify-between gap-3 px-5 py-3"
              >
                <dt class="text-slate-400 shrink-0">Coordenadas</dt>
                <dd class="font-mono text-xs text-slate-700 text-right">
                  {{ Number(parcel.latitude).toFixed(5) }},
                  {{ Number(parcel.longitude).toFixed(5) }}
                </dd>
              </div>
            </dl>
          </UiCard>
        </div>
      </div>

      <!-- Tabbed content -->
      <UiCard>
        <div class="flex items-center justify-between flex-wrap gap-3 mb-5">
          <UiTabs
            v-model="tab"
            :tabs="[
              { value: 'overview', label: 'Resumen' },
              { value: 'zones', label: 'Zonas', count: sectors.length },
              { value: 'crops', label: 'Cultivos', count: crops.length },
              { value: 'weather', label: 'Clima' },
              { value: 'data', label: 'Datos' },
            ]"
          />
          <button
            v-if="tab === 'zones' && !digitizing && !pending"
            class="text-sm px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition shadow-glow"
            @click="startDigitizing"
          >
            Digitalizar zona
          </button>
          <button
            v-else-if="tab === 'crops'"
            class="text-sm px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition shadow-glow"
            @click="openCropForm()"
          >
            + Añadir cultivo
          </button>
        </div>

        <div v-if="loading" class="py-8"><UiSkeleton /></div>

        <!-- Overview -->
        <div v-else-if="tab === 'overview'" class="space-y-6">
          <div class="grid md:grid-cols-2 gap-6">
            <!-- Zone distribution -->
            <div class="rounded-xl ring-1 ring-slate-100 p-5">
              <h3 class="text-sm font-semibold text-slate-700 mb-4">
                Distribución de zonas
              </h3>
              <div v-if="zoneSegments.length" class="flex items-center gap-5">
                <DonutChart
                  :segments="zoneSegments"
                  :size="140"
                  :thickness="14"
                >
                  <div class="text-center">
                    <p class="text-lg font-bold text-slate-800 tabular-nums">
                      {{ number(digitizedArea, 1) }}
                    </p>
                    <p class="text-[11px] text-slate-400">ha digitaliz.</p>
                  </div>
                </DonutChart>
                <ul class="space-y-1.5 text-sm min-w-0 flex-1">
                  <li
                    v-for="z in zoneSegments"
                    :key="z.label"
                    class="flex items-center gap-2"
                  >
                    <span
                      class="w-2.5 h-2.5 rounded-full shrink-0"
                      :style="{ backgroundColor: z.color }"
                    />
                    <span class="text-slate-600 truncate flex-1">{{
                      z.label
                    }}</span>
                    <span class="text-slate-400 tabular-nums"
                      >{{ number(z.value, 2) }} ha</span
                    >
                  </li>
                </ul>
              </div>
              <EmptyState
                v-else
                title="Sin zonas"
                message="Digitaliza zonas sobre el mapa para repartir la parcela."
              />
            </div>

            <!-- Crop status -->
            <div class="rounded-xl ring-1 ring-slate-100 p-5">
              <h3 class="text-sm font-semibold text-slate-700 mb-4">
                Estado de cultivos
              </h3>
              <div
                v-if="cropStatusSegments.length"
                class="flex items-center gap-5"
              >
                <DonutChart
                  :segments="cropStatusSegments"
                  :size="140"
                  :thickness="14"
                >
                  <div class="text-center">
                    <p class="text-lg font-bold text-slate-800 tabular-nums">
                      {{ crops.length }}
                    </p>
                    <p class="text-[11px] text-slate-400">cultivos</p>
                  </div>
                </DonutChart>
                <ul class="space-y-1.5 text-sm min-w-0 flex-1">
                  <li
                    v-for="c in cropStatusSegments"
                    :key="c.label"
                    class="flex items-center gap-2"
                  >
                    <span
                      class="w-2.5 h-2.5 rounded-full shrink-0"
                      :style="{ backgroundColor: c.color }"
                    />
                    <span class="text-slate-600 truncate flex-1">{{
                      c.label
                    }}</span>
                    <span class="text-slate-400 tabular-nums">{{
                      c.value
                    }}</span>
                  </li>
                </ul>
              </div>
              <EmptyState
                v-else
                title="Sin cultivos"
                message="Añade cultivos para ver su reparto por estado."
              />
            </div>
          </div>

          <!-- Mini summary row -->
          <div
            class="grid grid-cols-2 sm:grid-cols-4 gap-4 rounded-xl bg-slate-50 ring-1 ring-slate-100 p-4 text-center"
          >
            <div>
              <p class="text-xs text-slate-400">Rendimiento previsto</p>
              <p class="text-lg font-bold text-slate-800 tabular-nums">
                {{ number(expectedYield, 0) }} kg
              </p>
            </div>
            <div>
              <p class="text-xs text-slate-400">Lluvia 7 días</p>
              <p class="text-lg font-bold text-sky-600 tabular-nums">
                {{ weather ? number(weekTotals.rain, 1) : '—' }} mm
              </p>
            </div>
            <div>
              <p class="text-xs text-slate-400">Balance hídrico</p>
              <p
                class="text-lg font-bold tabular-nums"
                :class="
                  !weather
                    ? 'text-slate-400'
                    : weekTotals.balance >= 0
                      ? 'text-brand-600'
                      : 'text-red-500'
                "
              >
                {{ weather ? number(weekTotals.balance, 1) : '—' }} mm
              </p>
            </div>
            <div>
              <p class="text-xs text-slate-400">Alta</p>
              <p class="text-lg font-bold text-slate-800">
                {{ date(parcel.created_at) }}
              </p>
            </div>
          </div>
        </div>

        <!-- Zones -->
        <div v-else-if="tab === 'zones'" class="space-y-2">
          <p v-if="sectors.length" class="text-xs text-slate-400">
            {{ sectors.length }} zonas · {{ number(digitizedArea, 2) }} ha
            digitalizadas de {{ number(Number(parcel.area_ha), 2) }} ha
          </p>
          <div
            v-for="s in sectors"
            :key="s.id"
            class="bg-white rounded-xl ring-1 ring-slate-100 p-3 flex items-center gap-3"
          >
            <span
              class="w-3.5 h-3.5 rounded-full shrink-0"
              :style="{ backgroundColor: s.color || '#16a34a' }"
            />
            <div class="min-w-0 flex-1">
              <p class="font-medium text-slate-700 truncate">{{ s.name }}</p>
              <p class="text-xs text-slate-400">
                {{ number(Number(s.area_ha), 4) }} ha ·
                {{ cropsBySector[s.id]?.length || 0 }} cultivos
              </p>
            </div>
            <button
              class="text-xs px-2 py-1 rounded-lg text-brand-700 hover:bg-brand-50 transition"
              @click="openCropForm(s.id)"
            >
              + Cultivo
            </button>
            <button
              class="text-slate-300 hover:text-red-500 transition p-1"
              title="Eliminar zona"
              @click="deleteZone(s)"
            >
              <svg
                class="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            </button>
          </div>
          <EmptyState
            v-if="!sectors.length"
            title="Parcela sin digitalizar"
            message="Dibuja zonas sobre el mapa para gestionar varios cultivos dentro de la parcela."
          >
            <template #action>
              <button
                class="text-sm px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition"
                @click="startDigitizing"
              >
                Digitalizar primera zona
              </button>
            </template>
          </EmptyState>
        </div>

        <!-- Crops -->
        <div v-else-if="tab === 'crops'" class="space-y-2">
          <div
            v-for="c in crops"
            :key="c.id"
            class="bg-white rounded-xl ring-1 ring-slate-100 overflow-hidden"
          >
            <div
              class="p-3 flex items-center gap-3 cursor-pointer hover:bg-slate-50/70 transition"
              @click="toggleCrop(c.id)"
            >
              <svg
                class="w-4 h-4 text-slate-300 transition-transform shrink-0"
                :class="expandedCrop === c.id ? 'rotate-90' : ''"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 5l7 7-7 7"
                />
              </svg>
              <div class="min-w-0 flex-1">
                <p class="font-medium text-slate-700 truncate">
                  {{ c.species }}
                  <span v-if="c.variety" class="text-slate-400"
                    >· {{ c.variety }}</span
                  >
                </p>
                <p class="text-xs text-slate-400">
                  {{ c.campaign }}
                  <span v-if="c.sector">
                    · {{ sectors.find((s) => s.id === c.sector)?.name }}
                  </span>
                  <span v-if="c.sowing_date">
                    · siembra {{ date(c.sowing_date) }}</span
                  >
                  <span v-if="c.expected_yield_kg">
                    · {{ number(Number(c.expected_yield_kg), 0) }} kg prev.
                  </span>
                </p>
              </div>
              <UiBadge :tone="(STATUS_META[c.status]?.tone as any) || 'slate'">
                {{ STATUS_META[c.status]?.label || c.status }}
              </UiBadge>
              <button
                class="text-slate-300 hover:text-red-500 transition p-1"
                title="Eliminar cultivo"
                @click.stop="deleteCrop(c)"
              >
                <svg
                  class="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
              </button>
            </div>

            <!-- Phenology timeline -->
            <Transition name="expand">
              <div
                v-if="expandedCrop === c.id"
                class="border-t border-slate-100 bg-slate-50/60 p-4"
              >
                <template v-if="cropPhenology(c)">
                  <div class="flex items-center justify-between mb-3">
                    <h4
                      class="text-xs font-semibold text-slate-600 uppercase tracking-wide"
                    >
                      Fenología del cultivo
                    </h4>
                    <span
                      v-if="!cropPhenology(c)!.notStarted"
                      class="text-xs text-slate-400"
                    >
                      {{ cropPhenology(c)!.progressPct }}% del ciclo
                    </span>
                  </div>

                  <p
                    v-if="cropPhenology(c)!.notStarted"
                    class="text-sm text-slate-500"
                  >
                    Siembra programada para el {{ date(c.sowing_date) }}.
                  </p>

                  <template v-else>
                    <!-- Stage chips -->
                    <div class="flex items-stretch gap-1.5">
                      <div
                        v-for="st in cropPhenology(c)!.stages"
                        :key="st.key"
                        class="flex-1 text-center"
                      >
                        <div
                          class="text-base leading-none mb-1"
                          :class="
                            st.active || st.done ? '' : 'opacity-30 grayscale'
                          "
                        >
                          {{ st.emoji }}
                        </div>
                        <div
                          class="h-1.5 rounded-full transition-all"
                          :class="
                            st.done
                              ? 'bg-brand-500'
                              : st.active
                                ? 'bg-brand-400'
                                : 'bg-slate-200'
                          "
                        />
                        <p
                          class="mt-1 text-[10px] leading-tight"
                          :class="
                            st.active
                              ? 'text-brand-700 font-semibold'
                              : 'text-slate-400'
                          "
                        >
                          {{ st.label }}
                        </p>
                      </div>
                    </div>

                    <!-- Current stage + dates -->
                    <div
                      class="mt-3 grid grid-cols-3 gap-2 text-center text-xs"
                    >
                      <div
                        class="rounded-lg bg-white ring-1 ring-slate-100 py-2"
                      >
                        <p class="font-semibold text-slate-700">
                          {{ cropPhenology(c)!.current?.emoji }}
                          {{ cropPhenology(c)!.current?.label }}
                        </p>
                        <p class="text-slate-400">Etapa actual</p>
                      </div>
                      <div
                        class="rounded-lg bg-white ring-1 ring-slate-100 py-2"
                      >
                        <p class="font-semibold text-slate-700 tabular-nums">
                          {{ cropPhenology(c)!.elapsed }} d
                        </p>
                        <p class="text-slate-400">Transcurridos</p>
                      </div>
                      <div
                        class="rounded-lg bg-white ring-1 ring-slate-100 py-2"
                      >
                        <p
                          class="font-semibold tabular-nums"
                          :class="
                            cropPhenology(c)!.remaining > 0
                              ? 'text-slate-700'
                              : 'text-brand-600'
                          "
                        >
                          {{ cropPhenology(c)!.remaining }} d
                        </p>
                        <p class="text-slate-400">Para cosecha</p>
                      </div>
                    </div>
                    <p class="mt-2 text-[11px] text-slate-400 text-right">
                      {{ date(c.sowing_date) }} →
                      {{ date(c.expected_harvest_date) }} ·
                      {{ cropPhenology(c)!.total }} días de ciclo
                    </p>
                  </template>
                </template>
                <p v-else class="text-sm text-slate-500">
                  Define la
                  <span class="font-medium">fecha de siembra</span> y la
                  <span class="font-medium">cosecha prevista</span> para ver la
                  línea fenológica del cultivo.
                </p>

                <!-- Cuaderno de campo -->
                <div class="mt-4 pt-4 border-t border-slate-200/70">
                  <div class="flex items-center justify-between mb-2.5">
                    <h4
                      class="text-xs font-semibold text-slate-600 uppercase tracking-wide"
                    >
                      Cuaderno de campo
                    </h4>
                    <div class="flex items-center gap-1.5">
                      <button
                        class="text-xs px-2.5 py-1 rounded-lg bg-white ring-1 ring-slate-200 text-brand-700 hover:ring-brand-300 hover:bg-brand-50 transition font-medium"
                        @click="openOpForm(c.id)"
                      >
                        + Labor
                      </button>
                      <button
                        class="text-xs px-2.5 py-1 rounded-lg bg-white ring-1 ring-slate-200 text-sky-700 hover:ring-sky-300 hover:bg-sky-50 transition font-medium inline-flex items-center gap-1"
                        @click="openTrForm(c.id)"
                      >
                        🛡️ Tratamiento
                      </button>
                    </div>
                  </div>

                  <div
                    v-if="loadingOps[c.id]"
                    class="text-xs text-slate-400 py-2"
                  >
                    Cargando labores…
                  </div>
                  <div
                    v-else-if="
                      (cropOps[c.id]?.length ?? 0) === 0 &&
                      (cropTreatments[c.id]?.length ?? 0) === 0
                    "
                    class="text-xs text-slate-400 py-2"
                  >
                    Aún no hay labores ni tratamientos para este cultivo.
                  </div>
                  <template v-else>
                    <ul v-if="cropOps[c.id]?.length" class="space-y-1.5">
                      <li
                        v-for="op in cropOps[c.id]"
                        :key="op.id"
                        class="group flex items-center gap-2.5 rounded-lg bg-white ring-1 ring-slate-100 px-3 py-2"
                      >
                        <span class="text-base leading-none shrink-0">
                          {{ opMeta(op.operation_type)?.emoji ?? '📋' }}
                        </span>
                        <div class="min-w-0 flex-1">
                          <p class="text-sm text-slate-700 truncate">
                            {{ op.operation_type_display }}
                            <span v-if="op.description" class="text-slate-400">
                              · {{ op.description }}
                            </span>
                          </p>
                          <p class="text-[11px] text-slate-400 tabular-nums">
                            {{ date(op.date) }}
                            <span v-if="op.area_ha">
                              · {{ number(Number(op.area_ha), 2) }} ha
                            </span>
                          </p>
                        </div>
                        <button
                          class="text-slate-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition p-1 shrink-0"
                          title="Eliminar labor"
                          @click="deleteOp(c.id, op)"
                        >
                          <svg
                            class="w-3.5 h-3.5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              stroke-linecap="round"
                              stroke-linejoin="round"
                              stroke-width="2"
                              d="M6 18L18 6M6 6l12 12"
                            />
                          </svg>
                        </button>
                      </li>
                    </ul>

                    <!-- Treatments -->
                    <div v-if="cropTreatments[c.id]?.length" class="mt-2.5">
                      <p
                        class="text-[10px] font-semibold uppercase tracking-wide text-sky-600/80 mb-1.5"
                      >
                        Tratamientos fitosanitarios
                      </p>
                      <ul class="space-y-1.5">
                        <li
                          v-for="tr in cropTreatments[c.id]"
                          :key="tr.id"
                          class="group flex items-center gap-2.5 rounded-lg bg-sky-50/50 ring-1 ring-sky-100 px-3 py-2"
                        >
                          <span class="text-base leading-none shrink-0"
                            >🛡️</span
                          >
                          <div class="min-w-0 flex-1">
                            <p class="text-sm text-slate-700 truncate">
                              {{ tr.product_name }}
                              <span
                                v-if="tr.target_pest"
                                class="text-slate-400"
                              >
                                · {{ tr.target_pest }}
                              </span>
                            </p>
                            <p class="text-[11px] text-slate-400 tabular-nums">
                              {{ date(tr.date) }} ·
                              {{ number(Number(tr.dose), 2) }}
                              {{ tr.dose_unit }} ·
                              {{ number(Number(tr.total_quantity), 2) }} total
                            </p>
                          </div>
                          <span
                            v-if="!tr.safety_interval_ok"
                            class="shrink-0"
                            title="No respeta el plazo de seguridad antes de la cosecha"
                          >
                            <UiBadge tone="red">PS</UiBadge>
                          </span>
                          <button
                            class="text-slate-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition p-1 shrink-0"
                            title="Eliminar tratamiento"
                            @click="deleteTr(c.id, tr)"
                          >
                            <svg
                              class="w-3.5 h-3.5"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                stroke-width="2"
                                d="M6 18L18 6M6 6l12 12"
                              />
                            </svg>
                          </button>
                        </li>
                      </ul>
                    </div>
                  </template>
                </div>
              </div>
            </Transition>
          </div>
          <EmptyState
            v-if="!crops.length"
            title="Sin cultivos"
            message="Añade los cultivos de esta parcela y asígnalos a una zona."
          >
            <template #action>
              <button
                class="text-sm px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition"
                @click="openCropForm()"
              >
                + Añadir cultivo
              </button>
            </template>
          </EmptyState>
        </div>

        <!-- Weather -->
        <div v-else-if="tab === 'weather'" class="space-y-4">
          <div v-if="weatherLoading" class="py-8"><UiSkeleton /></div>
          <EmptyState
            v-else-if="weatherError"
            title="Sin datos de clima"
            :message="weatherError"
          />
          <template v-else-if="weather">
            <div
              class="bg-white rounded-xl ring-1 ring-slate-100 divide-y divide-slate-100"
            >
              <div
                v-for="d in weather.daily"
                :key="d.date"
                class="flex items-center gap-3 px-4 py-2.5 text-sm"
              >
                <span class="w-9 font-medium text-slate-600">{{
                  weekday(d.date)
                }}</span>
                <span class="text-xl w-7 text-center">{{
                  d.weather.emoji
                }}</span>
                <span class="flex-1 text-slate-500 truncate">{{
                  d.weather.label
                }}</span>
                <span
                  v-if="(d.precip_mm ?? 0) > 0"
                  class="text-xs text-sky-600 tabular-nums w-12 text-right"
                >
                  {{ number(d.precip_mm ?? 0, 1) }}mm
                </span>
                <span
                  v-else
                  class="text-xs text-amber-500 tabular-nums w-12 text-right"
                  title="Evapotranspiración (ET₀)"
                >
                  {{ number(d.et0_mm ?? 0, 1) }}↓
                </span>
                <span class="tabular-nums text-slate-700 w-9 text-right">
                  {{ number(d.t_max ?? 0, 0) }}°
                </span>
                <span class="tabular-nums text-slate-400 w-9 text-right">
                  {{ number(d.t_min ?? 0, 0) }}°
                </span>
              </div>
            </div>

            <div
              class="rounded-xl bg-slate-50 ring-1 ring-slate-100 p-4 grid grid-cols-3 gap-3 text-center"
            >
              <div>
                <p class="text-xs text-slate-400">Lluvia 7 días</p>
                <p class="text-lg font-bold text-sky-600 tabular-nums">
                  {{ number(weekTotals.rain, 1) }} mm
                </p>
              </div>
              <div>
                <p class="text-xs text-slate-400" title="Evapotranspiración">
                  ET₀ 7 días
                </p>
                <p class="text-lg font-bold text-amber-500 tabular-nums">
                  {{ number(weekTotals.et0, 1) }} mm
                </p>
              </div>
              <div>
                <p class="text-xs text-slate-400">Balance hídrico</p>
                <p
                  class="text-lg font-bold tabular-nums"
                  :class="
                    weekTotals.balance >= 0 ? 'text-brand-600' : 'text-red-500'
                  "
                >
                  {{ weekTotals.balance >= 0 ? '+' : ''
                  }}{{ number(weekTotals.balance, 1) }} mm
                </p>
              </div>
            </div>
            <!-- Irrigation recommendation -->
            <div
              class="rounded-2xl p-4 text-white bg-gradient-to-br shadow-glow"
              :class="IRRIGATION_META[irrigation.level].bg"
            >
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <p class="text-xs text-white/80 flex items-center gap-1.5">
                    <svg
                      class="w-3.5 h-3.5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M12 3v1m0 0c-3 4-5 6.5-5 9a5 5 0 0010 0c0-2.5-2-5-5-9z"
                      />
                    </svg>
                    Recomendación de riego
                  </p>
                  <p class="text-xl font-bold mt-0.5">
                    {{ IRRIGATION_META[irrigation.level].label }}
                  </p>
                </div>
                <span v-if="irrigation.deficit > 0" class="shrink-0 text-right">
                  <span class="text-3xl font-bold tabular-nums">{{
                    number(irrigation.deficit, 0)
                  }}</span>
                  <span class="text-sm text-white/80"> mm</span>
                </span>
              </div>
              <p class="text-sm text-white/90 mt-2 leading-relaxed">
                {{ IRRIGATION_META[irrigation.level].advice }}
              </p>
              <div
                v-if="irrigation.deficit > 0"
                class="mt-3 grid grid-cols-3 gap-2 text-center text-xs text-white/90"
              >
                <div class="rounded-lg bg-white/15 py-1.5">
                  <p class="font-semibold tabular-nums">
                    {{ number(irrigation.mmPerDay, 1) }}
                  </p>
                  <p class="text-white/70">mm/día</p>
                </div>
                <div class="rounded-lg bg-white/15 py-1.5">
                  <p class="font-semibold tabular-nums">
                    {{ number(irrigation.m3PerHa, 0) }}
                  </p>
                  <p class="text-white/70">m³/ha</p>
                </div>
                <div class="rounded-lg bg-white/15 py-1.5">
                  <p class="font-semibold tabular-nums">
                    {{ number(irrigation.m3Total, 0) }}
                  </p>
                  <p class="text-white/70">m³ parcela</p>
                </div>
              </div>
              <p
                v-if="irrigation.nextRain"
                class="text-xs text-white/80 mt-2.5 flex items-center gap-1.5"
              >
                <span>🌧️</span>
                Próxima lluvia: {{ weekday(irrigation.nextRain) }} ·
                {{ number(irrigation.nextRainMm, 1) }} mm
              </p>
            </div>
            <p class="text-[11px] text-slate-300 text-right">
              Fuente: Open-Meteo · ET₀ FAO-56
            </p>
          </template>
        </div>

        <!-- Data -->
        <div
          v-else-if="tab === 'data'"
          class="bg-white rounded-xl ring-1 ring-slate-100 divide-y divide-slate-100 text-sm"
        >
          <div class="flex justify-between px-4 py-3">
            <span class="text-slate-400">Explotación</span>
            <span class="font-medium text-slate-700">{{
              parcel.farm_name
            }}</span>
          </div>
          <div class="flex justify-between px-4 py-3">
            <span class="text-slate-400">Superficie oficial</span>
            <span class="font-medium text-slate-700"
              >{{ number(Number(parcel.area_ha), 4) }} ha</span
            >
          </div>
          <div class="flex justify-between px-4 py-3">
            <span class="text-slate-400">Referencia catastral</span>
            <span class="font-mono text-slate-700">{{
              parcel.sigpac_ref || '—'
            }}</span>
          </div>
          <div class="flex justify-between px-4 py-3">
            <span class="text-slate-400">Tipo de suelo</span>
            <span class="text-slate-700">{{ parcel.soil_type || '—' }}</span>
          </div>
          <div
            v-if="parcel.municipality"
            class="flex justify-between px-4 py-3"
          >
            <span class="text-slate-400">Municipio</span>
            <span class="text-slate-700">{{ parcel.municipality }}</span>
          </div>
          <div v-if="parcel.province" class="flex justify-between px-4 py-3">
            <span class="text-slate-400">Provincia</span>
            <span class="text-slate-700">{{ parcel.province }}</span>
          </div>
          <div
            v-if="parcel.address"
            class="flex justify-between gap-4 px-4 py-3"
          >
            <span class="text-slate-400 shrink-0">Ubicación catastral</span>
            <span class="text-slate-700 text-right">{{ parcel.address }}</span>
          </div>
          <div
            v-if="parcel.latitude && parcel.longitude"
            class="flex justify-between px-4 py-3"
          >
            <span class="text-slate-400">Coordenadas</span>
            <span class="font-mono text-slate-700">
              {{ Number(parcel.latitude).toFixed(5) }},
              {{ Number(parcel.longitude).toFixed(5) }}
            </span>
          </div>
          <div class="flex justify-between px-4 py-3">
            <span class="text-slate-400">Estado</span>
            <span class="text-slate-700">{{
              parcel.is_active ? 'Activa' : 'Inactiva'
            }}</span>
          </div>
          <div class="flex justify-between px-4 py-3">
            <span class="text-slate-400">Alta</span>
            <span class="text-slate-700">{{
              dateTime(parcel.created_at)
            }}</span>
          </div>
        </div>
      </UiCard>
    </template>

    <!-- Crop form modal -->
    <UiModal v-model="showCropForm" title="Nuevo cultivo">
      <div class="space-y-4">
        <UiField label="Zona (opcional)">
          <UiSelect
            v-model="cropForm.sector"
            :options="sectorOptions"
            placeholder="Toda la parcela"
          />
        </UiField>
        <div class="grid grid-cols-2 gap-4">
          <UiField label="Especie" required>
            <UiInput v-model="cropForm.species" placeholder="Ej. Olivo" />
          </UiField>
          <UiField label="Variedad">
            <UiInput v-model="cropForm.variety" placeholder="Ej. Picual" />
          </UiField>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <UiField label="Campaña" required>
            <UiInput v-model="cropForm.campaign" placeholder="2025/2026" />
          </UiField>
          <UiField label="Estado">
            <UiSelect v-model="cropForm.status" :options="statusOptions" />
          </UiField>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <UiField label="Fecha de siembra">
            <UiInput v-model="cropForm.sowing_date" type="date" />
          </UiField>
          <UiField label="Cosecha prevista">
            <UiInput v-model="cropForm.expected_harvest_date" type="date" />
          </UiField>
        </div>
        <UiField label="Rendimiento esperado (kg)">
          <UiInput
            v-model="cropForm.expected_yield_kg"
            type="number"
            step="0.01"
            placeholder="Opcional"
          />
        </UiField>
      </div>
      <template #footer>
        <button
          class="text-sm px-4 py-2 rounded-lg border border-slate-200 hover:bg-slate-50 transition"
          @click="showCropForm = false"
        >
          Cancelar
        </button>
        <button
          class="text-sm px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition disabled:opacity-50"
          :disabled="savingCrop"
          @click="saveCrop"
        >
          {{ savingCrop ? 'Guardando…' : 'Añadir cultivo' }}
        </button>
      </template>
    </UiModal>

    <!-- Field operation modal -->
    <UiModal v-model="showOpForm" title="Registrar labor">
      <div class="space-y-4">
        <UiField label="Tipo de labor" required>
          <UiSelect v-model="opForm.operation_type" :options="opTypeOptions" />
        </UiField>
        <div class="grid grid-cols-2 gap-4">
          <UiField label="Fecha" required>
            <UiInput v-model="opForm.date" type="date" />
          </UiField>
          <UiField label="Superficie (ha)">
            <UiInput
              v-model="opForm.area_ha"
              type="number"
              step="0.01"
              placeholder="Opcional"
            />
          </UiField>
        </div>
        <UiField label="Descripción / notas">
          <UiTextarea
            v-model="opForm.description"
            placeholder="Detalle de la labor realizada (producto, dosis, observaciones…)"
          />
        </UiField>
      </div>
      <template #footer>
        <button
          class="text-sm px-4 py-2 rounded-lg border border-slate-200 hover:bg-slate-50 transition"
          @click="showOpForm = false"
        >
          Cancelar
        </button>
        <button
          class="text-sm px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition disabled:opacity-50"
          :disabled="savingOp"
          @click="saveOp"
        >
          {{ savingOp ? 'Guardando…' : 'Registrar labor' }}
        </button>
      </template>
    </UiModal>

    <!-- Treatment modal -->
    <UiModal v-model="showTrForm" title="Registrar tratamiento fitosanitario">
      <div class="space-y-4">
        <UiField label="Producto" required>
          <UiSelect
            v-model="trForm.product"
            :options="productOptions"
            placeholder="Selecciona un producto del inventario"
          />
          <p v-if="!productsLoaded" class="text-[11px] text-slate-400 mt-1">
            Cargando productos…
          </p>
          <p
            v-else-if="productOptions.length === 0"
            class="text-[11px] text-amber-600 mt-1"
          >
            No hay productos en el inventario. Añádelos en la sección de stock.
          </p>
          <p v-else-if="trProduct" class="text-[11px] text-slate-400 mt-1">
            Stock disponible: {{ trProduct.current_stock }}
            {{ trProduct.unit }} · plazo de seguridad
            {{ trProduct.safety_interval_days }} días
          </p>
        </UiField>
        <div class="grid grid-cols-2 gap-4">
          <UiField label="Fecha" required>
            <UiInput v-model="trForm.date" type="date" />
          </UiField>
          <UiField label="Plaga / objetivo">
            <UiInput
              v-model="trForm.target_pest"
              placeholder="Ej. Mildiu, pulgón…"
            />
          </UiField>
        </div>
        <div class="grid grid-cols-3 gap-4">
          <UiField label="Dosis" required>
            <UiInput
              v-model="trForm.dose"
              type="number"
              step="0.01"
              placeholder="0.00"
            />
          </UiField>
          <UiField label="Unidad">
            <UiInput v-model="trForm.dose_unit" placeholder="L/ha" />
          </UiField>
          <UiField label="Cantidad total" required>
            <UiInput
              v-model="trForm.total_quantity"
              type="number"
              step="0.01"
              placeholder="A consumir"
            />
          </UiField>
        </div>
        <UiField label="Condiciones meteorológicas">
          <UiInput
            v-model="trForm.weather"
            placeholder="Ej. Despejado, 18 °C, sin viento"
          />
        </UiField>
        <p class="text-[11px] text-slate-400">
          Al guardar se descontará la cantidad total del stock por lotes (FEFO)
          y se comprobará el plazo de seguridad frente a la cosecha prevista.
        </p>
      </div>
      <template #footer>
        <button
          class="text-sm px-4 py-2 rounded-lg border border-slate-200 hover:bg-slate-50 transition"
          @click="showTrForm = false"
        >
          Cancelar
        </button>
        <button
          class="text-sm px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-700 text-white transition disabled:opacity-50"
          :disabled="savingTr"
          @click="saveTr"
        >
          {{ savingTr ? 'Guardando…' : 'Registrar tratamiento' }}
        </button>
      </template>
    </UiModal>

    <!-- Edit parcel modal -->
    <UiModal v-model="showEdit" title="Editar parcela">
      <div class="space-y-4">
        <UiField label="Nombre" required>
          <UiInput v-model="editForm.name" placeholder="Ej. La Vega" />
        </UiField>
        <UiField label="Referencia catastral / SIGPAC">
          <UiInput v-model="editForm.sigpac_ref" placeholder="Opcional" />
        </UiField>
        <UiField label="Tipo de suelo">
          <UiInput v-model="editForm.soil_type" placeholder="Opcional" />
        </UiField>
        <label class="flex items-center gap-2 text-sm text-slate-600">
          <input
            v-model="editForm.is_active"
            type="checkbox"
            class="rounded border-slate-300 text-brand-600 focus:ring-brand-500"
          />
          Parcela activa
        </label>
      </div>
      <template #footer>
        <button
          class="text-sm px-4 py-2 rounded-lg text-red-600 hover:bg-red-50 transition mr-auto inline-flex items-center gap-1.5"
          @click="
            showEdit = false;
            showDelete = true;
          "
        >
          <svg
            class="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
            />
          </svg>
          Eliminar
        </button>
        <button
          class="text-sm px-4 py-2 rounded-lg border border-slate-200 hover:bg-slate-50 transition"
          @click="showEdit = false"
        >
          Cancelar
        </button>
        <button
          class="text-sm px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition disabled:opacity-50"
          :disabled="savingEdit"
          @click="saveEdit"
        >
          {{ savingEdit ? 'Guardando…' : 'Guardar cambios' }}
        </button>
      </template>
    </UiModal>

    <!-- Delete confirmation -->
    <UiModal v-model="showDelete" title="Eliminar parcela">
      <div class="space-y-3">
        <div
          class="w-12 h-12 rounded-2xl bg-red-50 grid place-items-center text-red-500"
        >
          <svg
            class="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
        <p class="text-sm text-slate-600">
          ¿Seguro que quieres eliminar la parcela
          <span class="font-semibold text-slate-800">{{ parcel?.name }}</span
          >? Se eliminarán también sus
          <span class="font-medium">{{ sectors.length }} zonas</span> y
          <span class="font-medium">{{ crops.length }} cultivos</span>. Esta
          acción no se puede deshacer.
        </p>
      </div>
      <template #footer>
        <button
          class="text-sm px-4 py-2 rounded-lg border border-slate-200 hover:bg-slate-50 transition"
          @click="showDelete = false"
        >
          Cancelar
        </button>
        <button
          class="text-sm px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white transition disabled:opacity-50"
          :disabled="deleting"
          @click="deleteParcel"
        >
          {{ deleting ? 'Eliminando…' : 'Eliminar parcela' }}
        </button>
      </template>
    </UiModal>
  </div>
</template>

<style scoped>
.expand-enter-active,
.expand-leave-active {
  transition:
    opacity 0.25s ease,
    transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  transform-origin: top;
}
.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  transform: scaleY(0.96) translateY(-4px);
}
@media (prefers-reduced-motion: reduce) {
  .expand-enter-active,
  .expand-leave-active {
    transition: none;
  }
  .expand-enter-from,
  .expand-leave-to {
    transform: none;
  }
}
</style>
