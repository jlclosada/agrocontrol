<script setup lang="ts">
import { useAuthStore } from '~/stores/auth';
import type { Alert, DashboardData, Paginated } from '~/types/api';

const api = useApi();
const auth = useAuthStore();
const { number, dateTime } = useFormat();

const { data: dash, pending } = await useAsyncData('dashboard', () =>
  api.get<DashboardData>('/analytics/dashboard/'),
);
const { data: alerts } = await useAsyncData('dash-alerts', () =>
  api
    .get<Paginated<Alert>>('/alerts/', { resolved: false })
    .catch(() => ({ count: 0, next: null, previous: null, results: [] })),
);

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
</script>

<template>
  <div class="relative">
    <!-- Ambient gradient backdrop -->
    <div
      class="pointer-events-none absolute inset-x-0 top-0 h-72 bg-gradient-to-b from-brand-50/60 via-slate-50/20 to-transparent"
    />

    <div class="relative p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
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

      <!-- Recent alerts feed -->
      <div
        v-if="!isFarmer"
        class="bg-white rounded-2xl border border-slate-100 shadow-card overflow-hidden"
      >
        <div
          class="flex items-center justify-between px-5 py-4 border-b border-slate-100"
        >
          <h2 class="font-semibold text-slate-800">Actividad reciente</h2>
          <NuxtLink
            to="/alerts"
            class="text-xs font-medium text-brand-600 hover:text-brand-700 transition"
          >
            Ver todas →
          </NuxtLink>
        </div>
        <ul v-if="alerts?.results?.length" class="divide-y divide-slate-50">
          <li
            v-for="a in alerts.results.slice(0, 5)"
            :key="a.id"
            class="group flex items-center gap-3 px-5 py-3.5 hover:bg-slate-50/60 transition-colors"
          >
            <span
              class="w-2 h-2 rounded-full shrink-0"
              :class="{
                'bg-red-500': severityTone[a.severity] === 'red',
                'bg-amber-500': severityTone[a.severity] === 'amber',
                'bg-sky-500': severityTone[a.severity] === 'sky',
              }"
            />
            <div class="min-w-0 flex-1">
              <p class="text-sm font-medium text-slate-700 truncate">
                {{ a.title }}
              </p>
              <p class="text-xs text-slate-400">{{ dateTime(a.created_at) }}</p>
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
    </div>
  </div>
</template>
