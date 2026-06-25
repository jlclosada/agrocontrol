<script setup lang="ts">
import type { Paginated, TraceEvent } from '~/types/api';

const api = useApi();
const { dateTime } = useFormat();

const { data, pending } = await useAsyncData('trace-events', () =>
  api.get<Paginated<TraceEvent>>('/trace-events/'),
);

const events = computed(() =>
  [...(data.value?.results ?? [])].sort((a, b) => b.sequence - a.sequence),
);

// Verify the local chain integrity (prev_hash links).
const chainValid = computed(() => {
  const ordered = [...events.value].sort((a, b) => a.sequence - b.sequence);
  for (let i = 1; i < ordered.length; i++) {
    if (ordered[i].prev_hash !== ordered[i - 1].hash) return false;
  }
  return true;
});

const actionTone: Record<string, 'green' | 'sky' | 'red' | 'amber' | 'slate'> =
  {
    CREATE: 'green',
    CREATED: 'green',
    UPDATE: 'sky',
    UPDATED: 'sky',
    DELETE: 'red',
    DELETED: 'red',
  };

function short(hash: string) {
  return hash ? `${hash.slice(0, 8)}…${hash.slice(-6)}` : '—';
}
</script>

<template>
  <div class="p-6 lg:p-8 space-y-6 w-full">
    <PageHeader
      title="Trazabilidad"
      subtitle="Registro inmutable encadenado por hash (SHA-256)"
    >
      <template #actions>
        <UiBadge :tone="chainValid ? 'green' : 'red'" dot>
          {{ chainValid ? 'Cadena íntegra' : 'Integridad comprometida' }}
        </UiBadge>
      </template>
    </PageHeader>

    <UiCard v-if="pending"><UiSkeleton :rows="6" :cols="1" /></UiCard>

    <div v-else-if="events.length" class="relative">
      <!-- vertical line -->
      <div class="absolute left-[19px] top-2 bottom-2 w-px bg-slate-200" />
      <TransitionGroup name="list" tag="div" class="space-y-3 relative">
        <div
          v-for="(e, i) in events"
          :key="e.id"
          class="relative flex gap-4"
          :style="{ '--i': i }"
        >
          <div class="relative z-10 shrink-0">
            <div
              class="w-10 h-10 rounded-full grid place-items-center bg-white border-2 shadow-sm"
              :class="{
                'border-brand-500 text-brand-600':
                  (actionTone[e.action] ?? 'slate') === 'green',
                'border-sky-500 text-sky-600':
                  (actionTone[e.action] ?? 'slate') === 'sky',
                'border-red-500 text-red-600':
                  (actionTone[e.action] ?? 'slate') === 'red',
                'border-slate-300 text-slate-400':
                  (actionTone[e.action] ?? 'slate') === 'slate',
              }"
            >
              <span class="text-xs font-bold">#{{ e.sequence }}</span>
            </div>
          </div>
          <UiCard class="flex-1 !p-4">
            <div class="flex items-center gap-2 flex-wrap">
              <UiBadge :tone="actionTone[e.action] ?? 'slate'">{{
                e.action
              }}</UiBadge>
              <span class="font-medium text-slate-700">{{
                e.entity_type
              }}</span>
              <span class="text-xs text-slate-400">{{
                dateTime(e.occurred_at)
              }}</span>
            </div>
            <p v-if="e.actor_email" class="text-xs text-slate-500 mt-1">
              por {{ e.actor_email }}
            </p>
            <div
              class="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] font-mono text-slate-400"
            >
              <span title="hash anterior">prev: {{ short(e.prev_hash) }}</span>
              <span class="text-brand-600" title="hash"
                >hash: {{ short(e.hash) }}</span
              >
            </div>
          </UiCard>
        </div>
      </TransitionGroup>
    </div>

    <UiCard v-else>
      <EmptyState
        title="Sin eventos"
        message="No hay eventos de trazabilidad registrados todavía."
      />
    </UiCard>
  </div>
</template>
