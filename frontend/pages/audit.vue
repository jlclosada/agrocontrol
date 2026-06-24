<script setup lang="ts">
import type { AuditLog, Paginated } from '~/types/api';

const api = useApi();
const { dateTime } = useFormat();

const { data, pending } = await useAsyncData('audit-logs', () =>
  api.get<Paginated<AuditLog>>('/audit-logs/'),
);

const eventTone: Record<string, 'green' | 'red' | 'amber' | 'sky' | 'slate'> = {
  LOGIN_SUCCESS: 'green',
  LOGIN_FAILED: 'red',
  LOGIN_MFA_REQUIRED: 'amber',
  MFA_ENROLLED: 'sky',
  LOGOUT: 'slate',
};
</script>

<template>
  <div class="p-6 lg:p-8 space-y-6 max-w-6xl mx-auto">
    <PageHeader
      title="Auditoría"
      subtitle="Registro de eventos de seguridad y accesos"
    />

    <UiCard v-if="pending"><UiSkeleton :rows="8" :cols="1" /></UiCard>

    <UiCard v-else :padded="false">
      <table class="w-full text-sm">
        <thead class="bg-slate-50 text-slate-500 text-left">
          <tr>
            <th class="px-5 py-3 font-medium">Fecha</th>
            <th class="px-5 py-3 font-medium">Evento</th>
            <th class="px-5 py-3 font-medium">Usuario</th>
            <th class="px-5 py-3 font-medium">IP</th>
            <th class="px-5 py-3 font-medium">Detalle</th>
          </tr>
        </thead>
        <TransitionGroup
          tag="tbody"
          name="list"
          class="divide-y divide-slate-100"
        >
          <tr
            v-for="log in data?.results"
            :key="log.id"
            class="hover:bg-slate-50/70 transition"
          >
            <td class="px-5 py-3 text-slate-500 whitespace-nowrap">
              {{ dateTime(log.created_at) }}
            </td>
            <td class="px-5 py-3">
              <UiBadge :tone="eventTone[log.event] ?? 'slate'" dot>{{
                log.event_display
              }}</UiBadge>
            </td>
            <td class="px-5 py-3 text-slate-700">{{ log.email || '—' }}</td>
            <td class="px-5 py-3 font-mono text-xs text-slate-400">
              {{ log.ip_address || '—' }}
            </td>
            <td class="px-5 py-3 text-slate-500">{{ log.detail || '—' }}</td>
          </tr>
        </TransitionGroup>
      </table>
      <EmptyState
        v-if="!data?.results?.length"
        title="Sin registros"
        message="No hay eventos de auditoría registrados."
      />
    </UiCard>
  </div>
</template>
