<script setup lang="ts">
import type { Alert, AlertRule, Paginated } from '~/types/api';

const api = useApi();
const { dateTime } = useFormat();

const tab = ref('open');
const evaluating = ref(false);
const busy = ref<string | null>(null);

const {
  data: alerts,
  pending,
  refresh,
} = await useAsyncData('alerts', () => api.get<Paginated<Alert>>('/alerts/'));
const { data: rules } = await useAsyncData('alert-rules', () =>
  api.get<Paginated<AlertRule>>('/alert-rules/'),
);

const open = computed(() =>
  (alerts.value?.results ?? []).filter((a) => !a.resolved),
);
const resolved = computed(() =>
  (alerts.value?.results ?? []).filter((a) => a.resolved),
);

const tabs = computed(() => [
  { value: 'open', label: 'Abiertas', count: open.value.length },
  { value: 'resolved', label: 'Resueltas', count: resolved.value.length },
  { value: 'rules', label: 'Reglas', count: rules.value?.count },
]);

const list = computed(() =>
  tab.value === 'open' ? open.value : resolved.value,
);

const severityTone: Record<string, 'red' | 'amber' | 'sky' | 'slate'> = {
  CRITICAL: 'red',
  HIGH: 'red',
  MEDIUM: 'amber',
  LOW: 'sky',
};

async function evaluate() {
  evaluating.value = true;
  try {
    await api.post('/alert-rules/evaluate/', {});
    await refresh();
  } finally {
    evaluating.value = false;
  }
}

async function acknowledge(a: Alert) {
  busy.value = a.id;
  try {
    await api.post(`/alerts/${a.id}/acknowledge/`, {});
    await refresh();
  } finally {
    busy.value = null;
  }
}

async function resolve(a: Alert) {
  busy.value = a.id;
  try {
    await api.post(`/alerts/${a.id}/resolve/`, {});
    await refresh();
  } finally {
    busy.value = null;
  }
}
</script>

<template>
  <div class="p-6 lg:p-8 space-y-6 w-full">
    <PageHeader
      title="Alertas"
      subtitle="Eventos de stock, caducidad y plazos de seguridad"
    >
      <template #actions>
        <button
          class="text-sm px-3 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition disabled:opacity-50 shadow-glow"
          :disabled="evaluating"
          @click="evaluate"
        >
          {{ evaluating ? 'Evaluando…' : 'Evaluar ahora' }}
        </button>
      </template>
    </PageHeader>

    <UiTabs v-model="tab" :tabs="tabs" />

    <Transition name="page" mode="out-in">
      <!-- Alert lists -->
      <div v-if="tab !== 'rules'" :key="tab" class="space-y-3">
        <UiSkeleton v-if="pending" />
        <TransitionGroup
          v-else
          name="list"
          tag="div"
          class="space-y-3 relative"
        >
          <UiCard v-for="a in list" :key="a.id" class="!p-0">
            <div class="flex items-start gap-4 p-5">
              <div
                class="w-10 h-10 rounded-xl grid place-items-center shrink-0"
                :class="{
                  'bg-red-50 text-red-600': severityTone[a.severity] === 'red',
                  'bg-amber-50 text-amber-600':
                    severityTone[a.severity] === 'amber',
                  'bg-sky-50 text-sky-600': severityTone[a.severity] === 'sky',
                  'bg-slate-100 text-slate-500':
                    severityTone[a.severity] === 'slate',
                }"
              >
                <svg
                  class="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 9v2m0 4h.01M5.07 19h13.86a2 2 0 001.73-3L13.73 4a2 2 0 00-3.46 0L3.34 16a2 2 0 001.73 3z"
                  />
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                  <p class="font-semibold text-slate-800">{{ a.title }}</p>
                  <UiBadge :tone="severityTone[a.severity] ?? 'slate'">{{
                    a.severity
                  }}</UiBadge>
                  <UiBadge tone="slate">{{ a.trigger_display }}</UiBadge>
                  <UiBadge v-if="a.acknowledged && !a.resolved" tone="sky"
                    >Reconocida</UiBadge
                  >
                </div>
                <p class="text-sm text-slate-500 mt-1">{{ a.message }}</p>
                <p class="text-xs text-slate-400 mt-1">
                  {{ dateTime(a.created_at) }}
                </p>
              </div>
              <div v-if="!a.resolved" class="flex flex-col gap-2 shrink-0">
                <button
                  v-if="!a.acknowledged"
                  class="text-xs px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 transition disabled:opacity-50"
                  :disabled="busy === a.id"
                  @click="acknowledge(a)"
                >
                  Reconocer
                </button>
                <button
                  class="text-xs px-3 py-1.5 rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition disabled:opacity-50"
                  :disabled="busy === a.id"
                  @click="resolve(a)"
                >
                  Resolver
                </button>
              </div>
              <UiBadge v-else tone="green" dot>Resuelta</UiBadge>
            </div>
          </UiCard>
        </TransitionGroup>
        <UiCard v-if="!pending && !list.length">
          <EmptyState
            :title="
              tab === 'open' ? 'Sin alertas abiertas' : 'Sin alertas resueltas'
            "
            :message="
              tab === 'open'
                ? 'Todo en orden. ✅'
                : 'Aún no se ha resuelto ninguna alerta.'
            "
          />
        </UiCard>
      </div>

      <!-- Rules -->
      <UiCard v-else key="rules" :padded="false">
        <table class="w-full text-sm">
          <thead class="bg-slate-50 text-slate-500 text-left">
            <tr>
              <th class="px-5 py-3 font-medium">Regla</th>
              <th class="px-5 py-3 font-medium">Disparador</th>
              <th class="px-5 py-3 font-medium">Severidad</th>
              <th class="px-5 py-3 font-medium">Estado</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr
              v-for="r in rules?.results"
              :key="r.id"
              class="hover:bg-slate-50/70 transition"
            >
              <td class="px-5 py-3 font-medium text-slate-700">{{ r.name }}</td>
              <td class="px-5 py-3">
                <UiBadge tone="slate">{{ r.trigger_display }}</UiBadge>
              </td>
              <td class="px-5 py-3">
                <UiBadge :tone="severityTone[r.severity] ?? 'slate'">{{
                  r.severity
                }}</UiBadge>
              </td>
              <td class="px-5 py-3">
                <UiBadge :tone="r.is_active ? 'green' : 'slate'" dot>
                  {{ r.is_active ? 'Activa' : 'Inactiva' }}
                </UiBadge>
              </td>
            </tr>
          </tbody>
        </table>
        <EmptyState
          v-if="!rules?.results?.length"
          title="Sin reglas"
          message="No hay reglas de alerta configuradas."
        />
      </UiCard>
    </Transition>
  </div>
</template>
