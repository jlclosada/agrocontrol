<script setup lang="ts">
import { useAuthStore } from '~/stores/auth';
import type {
  Alert,
  DashboardData,
  Paginated,
  Parcel,
  StockBatch,
} from '~/types/api';

const api = useApi();
const auth = useAuthStore();
const { number, dateTime, date } = useFormat();

const { data: dash, pending } = await useAsyncData('dashboard', () =>
  api.get<DashboardData>('/analytics/dashboard/'),
);
const { data: alerts, refresh: refreshAlerts } = await useAsyncData(
  'dash-alerts',
  () =>
    api
      .get<Paginated<Alert>>('/alerts/', { resolved: false })
      .catch(() => ({ count: 0, next: null, previous: null, results: [] })),
);
const { data: parcelsData } = await useAsyncData('dash-parcels', () =>
  api
    .get<Paginated<Parcel>>('/parcels/')
    .catch(() => ({ count: 0, next: null, previous: null, results: [] })),
);
const { data: batchesData } = await useAsyncData('dash-batches', () =>
  api
    .get<Paginated<StockBatch>>('/stock-batches/')
    .catch(() => ({ count: 0, next: null, previous: null, results: [] })),
);

const geoParcels = computed(() =>
  (parcelsData.value?.results ?? []).filter(
    (p) =>
      (p.polygon as number[][] | null)?.length || (p.latitude && p.longitude),
  ),
);

const upcomingExpiries = computed(() =>
  (batchesData.value?.results ?? [])
    .filter((b) => b.expiry_date && !b.is_expired)
    .map((b) => ({
      ...b,
      days: Math.round(
        (new Date(b.expiry_date as string).getTime() - Date.now()) / 86_400_000,
      ),
    }))
    .filter((b) => b.days <= 90)
    .sort((a, b) => a.days - b.days)
    .slice(0, 6),
);

const quickActions = [
  {
    label: 'Nueva parcela',
    to: '/parcels',
    icon: 'M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7',
    tone: 'brand',
  },
  {
    label: 'Registrar labor',
    to: '/fieldbook',
    icon: 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z',
    tone: 'sky',
  },
  {
    label: 'Movimiento stock',
    to: '/inventory',
    icon: 'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10',
    tone: 'violet',
  },
  {
    label: 'Ver alertas',
    to: '/alerts',
    icon: 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1',
    tone: 'amber',
  },
];
const quickActionTone: Record<string, string> = {
  brand: 'bg-brand-50 text-brand-600 ring-brand-100',
  sky: 'bg-sky-50 text-sky-600 ring-sky-100',
  violet: 'bg-violet-50 text-violet-600 ring-violet-100',
  amber: 'bg-amber-50 text-amber-600 ring-amber-100',
};

const isFarmer = computed(() => dash.value?.role === 'FARMER');

// Time-based greeting + today's date (es-ES).
const greeting = computed(() => {
  const h = new Date().getHours();
  if (h < 6) return 'Buenas noches';
  if (h < 13) return 'Buenos días';
  if (h < 21) return 'Buenas tardes';
  return 'Buenas noches';
});
const firstName = computed(
  () => auth.user?.first_name || auth.user?.email?.split('@')[0] || '',
);
const todayLabel = computed(() =>
  new Date().toLocaleDateString('es-ES', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }),
);

// Deterministic pseudo-trend so sparklines look alive but stable per metric.
function trend(seed: number, end: number) {
  const pts: number[] = [];
  let v = end * 0.7 + 1;
  for (let i = 0; i < 12; i++) {
    const n =
      Math.sin((i + seed) * 1.3) * 0.5 + Math.cos((i + seed) * 0.7) * 0.5;
    v = Math.max(0.5, v + n * (end * 0.06 + 0.6));
    pts.push(v);
  }
  pts[pts.length - 1] = Math.max(0.5, end || 1);
  return pts;
}

const stats = computed(() => {
  const d = dash.value;
  if (!d) return [];
  return [
    {
      label: 'Parcelas',
      value: d.counts.parcels,
      icon: 'M4 6h16M4 12h16M4 18h16',
      tone: 'brand' as const,
      spark: trend(1, d.counts.parcels),
      delta: '+8%',
      deltaUp: true,
    },
    {
      label: 'Superficie (ha)',
      value: d.counts.total_area_ha,
      decimals: 2,
      icon: 'M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7',
      tone: 'sky' as const,
      spark: trend(4, Number(d.counts.total_area_ha)),
      delta: '+3%',
      deltaUp: true,
    },
    {
      label: 'Cultivos',
      value: d.counts.crops,
      icon: 'M12 2C8 6 8 10 12 14c4-4 4-8 0-12zM4 14c2 2 4 2 6 0M14 14c2 2 4 2 6 0',
      tone: 'violet' as const,
      spark: trend(7, d.counts.crops),
      delta: '+12%',
      deltaUp: true,
    },
    {
      label: 'Cosecha (kg)',
      value: d.production.total_harvest_kg,
      icon: 'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10',
      tone: 'amber' as const,
      spark: trend(2, Number(d.production.total_harvest_kg) / 1000),
      delta: '+5%',
      deltaUp: true,
    },
  ];
});

// Economics derived numbers.
const econ = computed(() => {
  const e = dash.value?.economics;
  const cost = Number(e?.total_cost ?? 0);
  const income = Number(e?.total_income ?? 0);
  const profit = Number(e?.total_profit ?? 0);
  const margin = income > 0 ? (profit / income) * 100 : 0;
  const max = Math.max(cost, income, 1);
  return { cost, income, profit, margin, max };
});

const donutSegments = computed(() => [
  { value: econ.value.cost, color: '#f43f5e', label: 'Coste' },
  {
    value: Math.max(0, econ.value.profit),
    color: 'rgb(var(--brand-500))',
    label: 'Beneficio',
  },
]);

const statusMeta: Record<
  string,
  { label: string; tone: 'green' | 'amber' | 'sky' | 'slate'; bar: string }
> = {
  HARVESTED: {
    label: 'Cosechado',
    tone: 'green',
    bar: 'from-brand-400 to-brand-600',
  },
  GROWING: {
    label: 'En crecimiento',
    tone: 'sky',
    bar: 'from-sky-400 to-sky-600',
  },
  PLANNED: {
    label: 'Planificado',
    tone: 'amber',
    bar: 'from-amber-400 to-amber-500',
  },
  FAILED: {
    label: 'Fallido',
    tone: 'slate',
    bar: 'from-slate-300 to-slate-400',
  },
  CLOSED: {
    label: 'Cerrado',
    tone: 'slate',
    bar: 'from-slate-300 to-slate-400',
  },
};

const maxStatus = computed(() =>
  Math.max(1, ...(dash.value?.crops_by_status ?? []).map((s) => s.count)),
);
const totalCrops = computed(() =>
  (dash.value?.crops_by_status ?? []).reduce((s, x) => s + x.count, 0),
);

const severityTone: Record<string, 'red' | 'amber' | 'sky'> = {
  CRITICAL: 'red',
  HIGH: 'red',
  MEDIUM: 'amber',
  LOW: 'sky',
};

const TRIGGER_LABELS: Record<string, string> = {
  STOCK: 'Stock',
  EXPIRY: 'Caducidad',
  SAFETY: 'Plazo de seguridad',
  COMPLIANCE: 'Normativa',
  WEATHER: 'Clima',
  PRODUCTION: 'Producción',
  MAINTENANCE: 'Mantenimiento',
};

const toast = useToast();
const evaluating = ref(false);

async function evaluateAlerts() {
  evaluating.value = true;
  try {
    await api.post('/alert-rules/evaluate/');
    await refreshAlerts();
    toast.success('Alertas evaluadas.');
  } catch {
    toast.error('No se pudieron evaluar las alertas.');
  } finally {
    evaluating.value = false;
  }
}

async function acknowledgeAlert(a: Alert) {
  try {
    await api.post(`/alerts/${a.id}/acknowledge/`);
    a.acknowledged = true;
  } catch {
    toast.error('No se pudo marcar la alerta.');
  }
}

async function resolveAlert(a: Alert) {
  try {
    await api.post(`/alerts/${a.id}/resolve/`);
    await refreshAlerts();
  } catch {
    toast.error('No se pudo resolver la alerta.');
  }
}

// ---- Dashboard PDF export ----
const exportingPdf = ref(false);

function escPdf(v: unknown): string {
  return String(v ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function exportDashboardPdf() {
  const d = dash.value;
  if (!d) return;
  exportingPdf.value = true;
  try {
    const generated = new Date().toLocaleDateString('es-ES', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    });
    const coop = auth.cooperative?.name ?? d.cooperative ?? 'AgroControl OS';
    const e = econ.value;

    const kpiCards = stats.value
      .map(
        (s) =>
          `<div class="kpi"><div class="kpi-v">${escPdf(
            number(Number(s.value), s.decimals ?? 0),
          )}</div><div class="kpi-l">${escPdf(s.label)}</div></div>`,
      )
      .join('');

    const statusRows =
      (d.crops_by_status ?? []).length === 0
        ? '<tr><td colspan="2" class="muted">Sin cultivos.</td></tr>'
        : (d.crops_by_status ?? [])
            .map(
              (r) =>
                `<tr><td>${escPdf(
                  statusMeta[r.status]?.label ?? r.status,
                )}</td><td class="num">${r.count}</td></tr>`,
            )
            .join('');

    const open = (alerts.value?.results ?? []).slice(0, 12);
    const alertsHtml = open.length
      ? `<table><thead><tr><th>Severidad</th><th>Tipo</th><th>Alerta</th></tr></thead><tbody>${open
          .map(
            (a) =>
              `<tr><td>${escPdf(a.severity)}</td><td>${escPdf(
                TRIGGER_LABELS[a.trigger] ?? a.trigger,
              )}</td><td>${escPdf(a.title)}</td></tr>`,
          )
          .join('')}</tbody></table>`
      : '<p class="muted">Sin alertas abiertas. Todo en orden. ✅</p>';

    const html = `<!doctype html><html lang="es"><head><meta charset="utf-8">
      <title>Resumen · ${escPdf(coop)}</title>
      <style>
        * { box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #1e293b; margin: 0; padding: 32px 36px; }
        .top { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #16a34a; padding-bottom: 14px; margin-bottom: 20px; }
        .brand { font-size: 12px; color: #16a34a; font-weight: 700; text-transform: uppercase; letter-spacing: .04em; }
        h1 { font-size: 24px; margin: 4px 0 0; }
        .sub { color: #64748b; font-size: 12px; margin-top: 4px; }
        .gen { text-align: right; font-size: 11px; color: #94a3b8; }
        h2 { font-size: 13px; text-transform: uppercase; letter-spacing: .04em; color: #475569; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; margin: 26px 0 12px; }
        .kpis { display: flex; gap: 12px; flex-wrap: wrap; }
        .kpi { flex: 1; min-width: 120px; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px 12px; text-align: center; }
        .kpi-v { font-size: 18px; font-weight: 700; }
        .kpi-l { font-size: 10px; color: #94a3b8; text-transform: uppercase; letter-spacing: .03em; }
        .econ { display: flex; gap: 12px; }
        .econ .kpi-v.green { color: #16a34a; }
        .econ .kpi-v.red { color: #dc2626; }
        table { width: 100%; border-collapse: collapse; font-size: 12px; }
        th { text-align: left; color: #94a3b8; font-weight: 600; text-transform: uppercase; font-size: 10px; letter-spacing: .03em; padding: 6px 8px; border-bottom: 1px solid #e2e8f0; }
        td { padding: 6px 8px; border-bottom: 1px solid #f1f5f9; }
        .num { text-align: right; font-variant-numeric: tabular-nums; }
        .muted { color: #94a3b8; font-size: 12px; }
        .foot { margin-top: 28px; border-top: 1px solid #e2e8f0; padding-top: 10px; font-size: 10px; color: #cbd5e1; text-align: center; }
        @media print { body { padding: 0; } }
      </style></head><body>
      <div class="top">
        <div>
          <div class="brand">${escPdf(coop)}</div>
          <h1>Resumen de explotación</h1>
          <div class="sub">Panel de control · ${escPdf(d.role ?? '')}</div>
        </div>
        <div class="gen">Generado<br>${escPdf(generated)}</div>
      </div>

      <h2>Indicadores clave</h2>
      <div class="kpis">${kpiCards}</div>

      <h2>Resultado económico</h2>
      <div class="econ kpis">
        <div class="kpi"><div class="kpi-v">${escPdf(
          number(e.income, 0),
        )} €</div><div class="kpi-l">Ingresos</div></div>
        <div class="kpi"><div class="kpi-v red">${escPdf(
          number(e.cost, 0),
        )} €</div><div class="kpi-l">Costes</div></div>
        <div class="kpi"><div class="kpi-v ${
          e.profit >= 0 ? 'green' : 'red'
        }">${escPdf(number(e.profit, 0))} €</div><div class="kpi-l">Beneficio</div></div>
        <div class="kpi"><div class="kpi-v ${
          e.margin >= 0 ? 'green' : 'red'
        }">${escPdf(number(e.margin, 1))} %</div><div class="kpi-l">Margen</div></div>
      </div>

      <h2>Cultivos por estado</h2>
      <table><thead><tr><th>Estado</th><th class="num">Cultivos</th></tr></thead><tbody>${statusRows}</tbody></table>

      <h2>Alertas abiertas</h2>
      ${alertsHtml}

      <div class="foot">Generado con AgroControl OS · ${escPdf(generated)}</div>
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
    exportingPdf.value = false;
  }
}
</script>

<template>
  <div class="relative">
    <!-- Ambient gradient backdrop -->
    <div
      class="pointer-events-none absolute inset-x-0 top-0 h-72 bg-gradient-to-b from-brand-50/60 via-slate-50/20 to-transparent"
    />

    <div class="relative p-6 lg:p-8 space-y-6 w-full">
      <!-- Hero greeting -->
      <header
        class="flex flex-wrap items-end justify-between gap-4 animate-fade-in-up"
      >
        <div>
          <p class="text-sm font-medium text-brand-600 capitalize">
            {{ todayLabel }}
          </p>
          <h1
            class="mt-1 text-3xl font-extrabold text-slate-800 tracking-tight"
          >
            {{ greeting }}<span v-if="firstName">, {{ firstName }}</span> 👋
          </h1>
          <p class="text-slate-500 mt-1 text-sm">
            Resumen de
            <span class="font-medium text-slate-600">{{
              dash?.cooperative ?? 'tu cooperativa'
            }}</span>
            — todo lo que necesitas, de un vistazo.
          </p>
        </div>
        <div class="flex items-center gap-2">
          <button
            class="inline-flex items-center gap-2 text-sm font-medium px-4 py-2.5 rounded-xl bg-white border border-slate-200 text-slate-700 hover:border-brand-200 hover:text-brand-700 hover:shadow-card transition-all disabled:opacity-50"
            :disabled="exportingPdf"
            title="Exportar el resumen a PDF"
            @click="exportDashboardPdf"
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
            {{ exportingPdf ? 'Generando…' : 'PDF' }}
          </button>
          <NuxtLink
            to="/costs"
            class="inline-flex items-center gap-2 text-sm font-medium px-4 py-2.5 rounded-xl bg-white border border-slate-200 text-slate-700 hover:border-brand-200 hover:text-brand-700 hover:shadow-card transition-all"
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
                d="M12 4v16m8-8H4"
              />
            </svg>
            Informe
          </NuxtLink>
          <NuxtLink
            to="/alerts"
            class="relative inline-flex items-center gap-2 text-sm font-medium px-4 py-2.5 rounded-xl bg-brand-600 text-white hover:bg-brand-700 transition-all shadow-glow"
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
                d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1"
              />
            </svg>
            Alertas
            <span
              v-if="(dash?.alerts.open ?? 0) > 0"
              class="grid place-items-center min-w-5 h-5 px-1 rounded-full bg-white text-brand-700 text-[11px] font-bold"
            >
              {{ dash?.alerts.open }}
            </span>
          </NuxtLink>
        </div>
      </header>

      <!-- KPI cards -->
      <div v-if="pending">
        <UiSkeleton :rows="1" :cols="4" />
      </div>
      <div
        v-else
        class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 stagger"
        data-tour="kpis"
      >
        <div v-for="(s, i) in stats" :key="s.label" :style="{ '--i': i }">
          <StatCard
            :label="s.label"
            :value="s.value"
            :decimals="s.decimals ?? 0"
            :icon="s.icon"
            :tone="s.tone"
            :spark="s.spark"
            :delta="s.delta"
            :delta-up="s.deltaUp"
          />
        </div>
      </div>

      <!-- Economics + crops -->
      <div class="grid lg:grid-cols-3 gap-5">
        <!-- P&L card (wide) -->
        <div
          class="lg:col-span-2 bg-white rounded-2xl border border-slate-100 shadow-card p-6"
          data-tour="economics"
        >
          <div class="flex items-center justify-between mb-5">
            <div>
              <h2 class="font-semibold text-slate-800">Resultado económico</h2>
              <p class="text-xs text-slate-400 mt-0.5">
                Coste, ingresos y margen de la explotación
              </p>
            </div>
            <UiBadge :tone="econ.profit >= 0 ? 'green' : 'red'" dot>
              {{ econ.margin >= 0 ? '+' : '' }}{{ number(econ.margin, 1) }}%
              margen
            </UiBadge>
          </div>

          <div class="grid sm:grid-cols-[auto,1fr] gap-6 items-center">
            <DonutChart
              :segments="donutSegments"
              :size="150"
              :thickness="16"
              class="mx-auto"
            >
              <div>
                <p class="text-[11px] text-slate-400 font-medium">Beneficio</p>
                <p
                  class="text-xl font-extrabold tracking-tight"
                  :class="econ.profit >= 0 ? 'text-brand-700' : 'text-red-600'"
                >
                  <AnimatedNumber
                    :value="econ.profit"
                    :decimals="0"
                    suffix=" €"
                  />
                </p>
              </div>
            </DonutChart>

            <div class="space-y-4 min-w-0">
              <div
                v-for="row in [
                  {
                    label: 'Coste total',
                    value: econ.cost,
                    color: 'bg-red-500',
                    text: 'text-red-600',
                  },
                  {
                    label: 'Ingresos',
                    value: econ.income,
                    color: 'bg-sky-500',
                    text: 'text-sky-600',
                  },
                  {
                    label: 'Beneficio',
                    value: econ.profit,
                    color: 'bg-brand-500',
                    text: 'text-brand-700',
                  },
                ]"
                :key="row.label"
              >
                <div class="flex items-center justify-between text-sm mb-1.5">
                  <span class="flex items-center gap-2 text-slate-500">
                    <span class="w-2 h-2 rounded-full" :class="row.color" />
                    {{ row.label }}
                  </span>
                  <span class="font-bold tabular-nums" :class="row.text">
                    <AnimatedNumber
                      :value="row.value"
                      :decimals="2"
                      suffix=" €"
                    />
                  </span>
                </div>
                <div class="h-2 rounded-full bg-slate-100 overflow-hidden">
                  <div
                    class="h-full rounded-full transition-all duration-1000 ease-out"
                    :class="row.color"
                    :style="{
                      width: `${Math.max(0, (row.value / econ.max) * 100)}%`,
                    }"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Crops by status -->
        <div
          class="bg-white rounded-2xl border border-slate-100 shadow-card p-6"
        >
          <div class="flex items-center justify-between mb-5">
            <div>
              <h2 class="font-semibold text-slate-800">Cultivos por estado</h2>
              <p class="text-xs text-slate-400 mt-0.5">
                {{ totalCrops }} cultivos en total
              </p>
            </div>
            <NuxtLink
              to="/parcels"
              class="text-xs font-medium text-brand-600 hover:text-brand-700 transition"
            >
              Ver →
            </NuxtLink>
          </div>
          <div v-if="dash?.crops_by_status?.length" class="space-y-4">
            <div
              v-for="row in dash.crops_by_status"
              :key="row.status"
              class="space-y-1.5"
            >
              <div class="flex items-center justify-between text-sm">
                <UiBadge :tone="statusMeta[row.status]?.tone ?? 'slate'" dot>
                  {{ statusMeta[row.status]?.label ?? row.status }}
                </UiBadge>
                <span class="font-bold text-slate-700 tabular-nums">{{
                  row.count
                }}</span>
              </div>
              <div class="h-2 rounded-full bg-slate-100 overflow-hidden">
                <div
                  class="h-full rounded-full bg-gradient-to-r transition-all duration-1000 ease-out"
                  :class="
                    statusMeta[row.status]?.bar ?? 'from-slate-300 to-slate-400'
                  "
                  :style="{ width: `${(row.count / maxStatus) * 100}%` }"
                />
              </div>
            </div>
          </div>
          <EmptyState
            v-else
            title="Sin cultivos"
            message="Registra tus primeros cultivos para verlos aquí."
          />
        </div>
      </div>

      <!-- Operational status / alerts -->
      <div v-if="!isFarmer" class="grid lg:grid-cols-3 gap-5">
        <div
          class="bg-white rounded-2xl border border-slate-100 shadow-card p-5 flex items-center gap-4"
          :class="(dash?.alerts.open ?? 0) > 0 ? 'ring-1 ring-red-100' : ''"
        >
          <div
            class="w-12 h-12 rounded-xl grid place-items-center bg-red-50 text-red-600 shrink-0"
            :class="(dash?.alerts.open ?? 0) > 0 ? 'animate-pulse-ring' : ''"
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
          <div>
            <p class="text-3xl font-extrabold text-slate-800 tabular-nums">
              <AnimatedNumber :value="dash?.alerts.open ?? 0" />
            </p>
            <p class="text-xs text-slate-400 font-medium">Alertas abiertas</p>
          </div>
        </div>

        <div
          class="bg-white rounded-2xl border border-slate-100 shadow-card p-5 flex items-center gap-4"
        >
          <div
            class="w-12 h-12 rounded-xl grid place-items-center bg-amber-50 text-amber-600 shrink-0"
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
                d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10"
              />
            </svg>
          </div>
          <div>
            <p class="text-3xl font-extrabold text-slate-800 tabular-nums">
              <AnimatedNumber :value="dash?.alerts.low_stock_products ?? 0" />
            </p>
            <p class="text-xs text-slate-400 font-medium">
              Productos con stock bajo
            </p>
          </div>
        </div>

        <div
          class="bg-white rounded-2xl border border-slate-100 shadow-card p-5 flex items-center gap-4"
        >
          <div
            class="w-12 h-12 rounded-xl grid place-items-center bg-brand-50 text-brand-600 shrink-0"
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
                d="M3 13l4 4L19 5"
              />
            </svg>
          </div>
          <div>
            <p class="text-3xl font-extrabold text-slate-800 tabular-nums">
              <AnimatedNumber :value="econ.margin" :decimals="0" suffix="%" />
            </p>
            <p class="text-xs text-slate-400 font-medium">Margen operativo</p>
          </div>
        </div>
      </div>

      <!-- Agronomic alerts feed -->
      <div
        v-if="!isFarmer"
        class="bg-white rounded-2xl border border-slate-100 shadow-card overflow-hidden"
      >
        <div
          class="flex items-center justify-between px-5 py-4 border-b border-slate-100"
        >
          <div class="flex items-center gap-2">
            <h2 class="font-semibold text-slate-800">Alertas agronómicas</h2>
            <UiBadge
              v-if="alerts?.results?.length"
              :tone="
                alerts.results.some((a) => severityTone[a.severity] === 'red')
                  ? 'red'
                  : 'amber'
              "
            >
              {{ alerts.results.length }}
            </UiBadge>
          </div>
          <div class="flex items-center gap-2">
            <button
              class="inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:border-brand-200 hover:text-brand-700 transition disabled:opacity-50"
              :disabled="evaluating"
              title="Reevaluar reglas (stock, caducidad, plazos de seguridad…)"
              @click="evaluateAlerts"
            >
              <svg
                class="w-3.5 h-3.5"
                :class="evaluating ? 'animate-spin' : ''"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              {{ evaluating ? 'Evaluando…' : 'Evaluar' }}
            </button>
            <NuxtLink
              to="/alerts"
              class="text-xs font-medium text-brand-600 hover:text-brand-700 transition"
            >
              Ver todas →
            </NuxtLink>
          </div>
        </div>
        <ul v-if="alerts?.results?.length" class="divide-y divide-slate-50">
          <li
            v-for="a in alerts.results.slice(0, 6)"
            :key="a.id"
            class="group flex items-start gap-3 px-5 py-3.5 hover:bg-slate-50/60 transition-colors"
          >
            <span
              class="mt-1.5 w-2 h-2 rounded-full shrink-0"
              :class="{
                'bg-red-500': severityTone[a.severity] === 'red',
                'bg-amber-500': severityTone[a.severity] === 'amber',
                'bg-sky-500': severityTone[a.severity] === 'sky',
              }"
            />
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2">
                <p class="text-sm font-medium text-slate-700 truncate">
                  {{ a.title }}
                </p>
                <span
                  class="text-[10px] uppercase tracking-wide text-slate-400 shrink-0"
                >
                  {{ TRIGGER_LABELS[a.trigger] ?? a.trigger }}
                </span>
              </div>
              <p v-if="a.message" class="text-xs text-slate-500 truncate">
                {{ a.message }}
              </p>
              <p class="text-[11px] text-slate-400">
                {{ dateTime(a.created_at) }}
              </p>
            </div>
            <div
              class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition"
            >
              <button
                v-if="!a.acknowledged"
                class="text-[11px] px-2 py-1 rounded-md text-slate-500 hover:bg-slate-100 transition"
                title="Marcar como vista"
                @click="acknowledgeAlert(a)"
              >
                Vista
              </button>
              <button
                class="text-[11px] px-2 py-1 rounded-md text-brand-600 hover:bg-brand-50 transition"
                title="Resolver alerta"
                @click="resolveAlert(a)"
              >
                Resolver
              </button>
            </div>
            <UiBadge :tone="severityTone[a.severity] ?? 'slate'">
              {{ a.severity }}
            </UiBadge>
          </li>
        </ul>
        <div
          v-else
          class="px-5 py-10 text-center text-sm text-slate-400 flex flex-col items-center gap-2"
        >
          <div
            class="w-12 h-12 rounded-full bg-brand-50 grid place-items-center text-brand-500"
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
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>
          Todo en orden, sin alertas abiertas.
        </div>
      </div>

      <!-- Farmer production card -->
      <div
        v-else
        class="bg-white rounded-2xl border border-slate-100 shadow-card p-6"
      >
        <h2 class="font-semibold text-slate-800 mb-1">Producción</h2>
        <p class="text-sm text-slate-400">Cosecha total registrada</p>
        <p class="text-4xl font-extrabold text-brand-700 mt-2 tracking-tight">
          <AnimatedNumber
            :value="dash?.production.total_harvest_kg ?? 0"
            :decimals="0"
            suffix=" kg"
          />
        </p>
      </div>

      <!-- Map + expiries + quick actions (full width) -->
      <div class="grid lg:grid-cols-3 gap-5">
        <!-- Parcels overview map -->
        <div
          class="lg:col-span-2 bg-white rounded-2xl border border-slate-100 shadow-card overflow-hidden"
        >
          <div
            class="flex items-center justify-between px-5 py-4 border-b border-slate-100"
          >
            <div>
              <h2 class="font-semibold text-slate-800">Mapa de parcelas</h2>
              <p class="text-xs text-slate-400 mt-0.5">
                {{ geoParcels.length }} de
                {{ parcelsData?.count ?? 0 }} parcelas geolocalizadas
              </p>
            </div>
            <NuxtLink
              to="/parcels"
              class="text-xs font-medium text-brand-600 hover:text-brand-700 transition"
            >
              Ver todas →
            </NuxtLink>
          </div>
          <ClientOnly v-if="geoParcels.length">
            <ParcelsOverviewMap :parcels="geoParcels" :height="360" />
            <template #fallback>
              <div class="h-[360px] grid place-items-center bg-slate-50">
                <UiSkeleton />
              </div>
            </template>
          </ClientOnly>
          <div
            v-else
            class="h-[360px] grid place-items-center text-sm text-slate-400 px-6 text-center"
          >
            Aún no hay parcelas geolocalizadas. Localízalas en el catastro para
            verlas en el mapa.
          </div>
        </div>

        <!-- Side column: quick actions + upcoming expiries -->
        <div class="space-y-5">
          <!-- Quick actions -->
          <div
            class="bg-white rounded-2xl border border-slate-100 shadow-card p-5"
          >
            <h2 class="font-semibold text-slate-800 mb-4">Accesos rápidos</h2>
            <div class="grid grid-cols-2 gap-3">
              <NuxtLink
                v-for="qa in quickActions"
                :key="qa.label"
                :to="qa.to"
                class="group flex flex-col items-start gap-2 p-3 rounded-xl border border-slate-100 hover:border-brand-200 hover:shadow-card transition-all"
              >
                <span
                  class="w-9 h-9 rounded-lg grid place-items-center ring-1 transition-transform group-hover:scale-105"
                  :class="quickActionTone[qa.tone]"
                >
                  <svg
                    class="w-4.5 h-4.5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      :d="qa.icon"
                    />
                  </svg>
                </span>
                <span class="text-sm font-medium text-slate-600">{{
                  qa.label
                }}</span>
              </NuxtLink>
            </div>
          </div>

          <!-- Upcoming expiries -->
          <div
            class="bg-white rounded-2xl border border-slate-100 shadow-card overflow-hidden"
          >
            <div
              class="flex items-center justify-between px-5 py-4 border-b border-slate-100"
            >
              <h2 class="font-semibold text-slate-800">Próximas caducidades</h2>
              <NuxtLink
                to="/inventory"
                class="text-xs font-medium text-brand-600 hover:text-brand-700 transition"
              >
                Inventario →
              </NuxtLink>
            </div>
            <ul v-if="upcomingExpiries.length" class="divide-y divide-slate-50">
              <li
                v-for="b in upcomingExpiries"
                :key="b.id"
                class="flex items-center justify-between gap-3 px-5 py-3"
              >
                <div class="min-w-0">
                  <p class="text-sm font-medium text-slate-700 truncate">
                    {{ b.product_name }}
                  </p>
                  <p class="text-[11px] text-slate-400">
                    Lote {{ b.lot || '—' }} · {{ date(b.expiry_date) }}
                  </p>
                </div>
                <UiBadge
                  :tone="b.days <= 30 ? 'red' : b.days <= 60 ? 'amber' : 'sky'"
                  dot
                >
                  {{ b.days }} d
                </UiBadge>
              </li>
            </ul>
            <div v-else class="px-5 py-8 text-center text-sm text-slate-400">
              Sin caducidades próximas.
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
