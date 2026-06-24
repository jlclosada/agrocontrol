<script setup lang="ts">
import type {
  CostEntry,
  Crop,
  Paginated,
  ProfitabilityReport,
} from '~/types/api';

const api = useApi();
const toast = useToast();
const { currency, number, date } = useFormat();

const tab = ref('profitability');
const recomputing = ref(false);
const exporting = ref(false);

const {
  data: reports,
  pending: pendingReports,
  refresh: refreshReports,
} = await useAsyncData('cost-reports', () =>
  api.get<Paginated<ProfitabilityReport>>('/profitability/'),
);
const {
  data: entries,
  pending: pendingEntries,
  refresh: refreshEntries,
} = await useAsyncData('cost-entries', () =>
  api.get<Paginated<CostEntry>>('/cost-entries/'),
);
const { data: crops } = await useAsyncData('cost-crops', () =>
  api.get<Paginated<Crop>>('/crops/'),
);

const tabs = computed(() => [
  {
    value: 'profitability',
    label: 'Rentabilidad',
    count: reports.value?.count,
  },
  { value: 'entries', label: 'Costes', count: entries.value?.count },
]);

const cropOptions = computed(() =>
  (crops.value?.results ?? []).map((c) => ({
    value: c.id,
    label: `${c.species} ${c.variety} — ${c.parcel_name}`,
  })),
);

const costCategories = [
  { value: 'LABOR', label: 'Mano de obra' },
  { value: 'PRODUCT', label: 'Producto / insumo' },
  { value: 'MACHINE', label: 'Maquinaria' },
  { value: 'WATER', label: 'Agua / riego' },
  { value: 'ELECTRICITY', label: 'Electricidad' },
  { value: 'OTHER', label: 'Otro' },
];

const today = new Date().toISOString().slice(0, 10);
const saving = ref(false);
const showEntry = ref(false);
const entryBlank = () => ({
  crop: '',
  category: 'OTHER',
  amount: '',
  date: today,
  description: '',
});
const entryForm = ref(entryBlank());
function openEntry() {
  entryForm.value = entryBlank();
  showEntry.value = true;
}
async function submitEntry() {
  if (!entryForm.value.crop || !entryForm.value.amount) {
    toast.error('Cultivo e importe son obligatorios.');
    return;
  }
  saving.value = true;
  try {
    await api.post('/cost-entries/', { ...entryForm.value });
    toast.success('Coste registrado.');
    showEntry.value = false;
    await refreshEntries();
  } catch {
    toast.error('No se pudo registrar el coste.');
  } finally {
    saving.value = false;
  }
}

const totals = computed(() => {
  const rows = reports.value?.results ?? [];
  const sum = (k: 'total_cost' | 'income' | 'profit') =>
    rows.reduce((s, r) => s + parseFloat(r[k] || '0'), 0);
  return {
    cost: sum('total_cost'),
    income: sum('income'),
    profit: sum('profit'),
  };
});

async function recompute() {
  recomputing.value = true;
  try {
    await api.post('/profitability/recompute/', {});
    await refreshReports();
    toast.success('Rentabilidad recalculada.');
  } catch {
    toast.error('No se pudo recalcular.');
  } finally {
    recomputing.value = false;
  }
}

async function exportCsv() {
  exporting.value = true;
  try {
    await api.download('/analytics/export/profitability/', 'rentabilidad.csv');
  } catch {
    toast.error('No se pudo exportar.');
  } finally {
    exporting.value = false;
  }
}

function marginTone(pct: string) {
  const n = parseFloat(pct || '0');
  if (n >= 30) return 'green';
  if (n >= 0) return 'amber';
  return 'red';
}

const catTone: Record<string, 'sky' | 'violet' | 'amber' | 'slate'> = {
  LABOR: 'sky',
  PRODUCT: 'violet',
  MACHINE: 'amber',
};
</script>

<template>
  <div class="p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
    <PageHeader
      title="Costes y rentabilidad"
      subtitle="Imputación automática de costes y análisis de margen por cultivo"
    >
      <template #actions>
        <button
          class="text-sm px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 transition disabled:opacity-50"
          :disabled="recomputing"
          @click="recompute"
        >
          {{ recomputing ? 'Calculando…' : 'Recalcular' }}
        </button>
        <button
          class="text-sm px-3 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition disabled:opacity-50 shadow-glow"
          :disabled="exporting"
          @click="exportCsv"
        >
          {{ exporting ? 'Exportando…' : 'Exportar CSV' }}
        </button>
      </template>
    </PageHeader>

    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 stagger">
      <StatCard
        label="Coste total"
        :value="totals.cost"
        :decimals="2"
        suffix=" €"
        tone="red"
        icon="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8V7m0 9v1"
      />
      <StatCard
        label="Ingresos"
        :value="totals.income"
        :decimals="2"
        suffix=" €"
        tone="sky"
        icon="M3 13h2l2 5 4-12 3 7h4"
      />
      <StatCard
        label="Beneficio"
        :value="totals.profit"
        :decimals="2"
        suffix=" €"
        tone="brand"
        icon="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
      />
    </div>

    <div class="flex justify-end gap-2">
      <button
        v-if="tab === 'entries'"
        class="text-sm px-3 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition shadow-glow"
        @click="openEntry"
      >
        + Coste manual
      </button>
      <UiTabs v-model="tab" :tabs="tabs" />
    </div>

    <Transition name="page" mode="out-in">
      <!-- Profitability -->
      <UiCard v-if="tab === 'profitability'" key="prof" :padded="false">
        <div class="p-5" v-if="pendingReports"><UiSkeleton /></div>
        <table v-else class="w-full text-sm">
          <thead class="bg-slate-50 text-slate-500 text-left">
            <tr>
              <th class="px-5 py-3 font-medium">Cultivo</th>
              <th class="px-5 py-3 font-medium text-right">Coste</th>
              <th class="px-5 py-3 font-medium text-right">Ingreso</th>
              <th class="px-5 py-3 font-medium text-right">Beneficio</th>
              <th class="px-5 py-3 font-medium text-right">Coste/ha</th>
              <th class="px-5 py-3 font-medium text-right">Margen</th>
            </tr>
          </thead>
          <TransitionGroup
            tag="tbody"
            name="list"
            class="divide-y divide-slate-100"
          >
            <tr
              v-for="r in reports?.results"
              :key="r.id"
              class="hover:bg-slate-50/70 transition"
            >
              <td class="px-5 py-3 font-medium text-slate-700">
                {{ r.crop_label }}
              </td>
              <td class="px-5 py-3 text-right text-slate-500">
                {{ currency(r.total_cost) }}
              </td>
              <td class="px-5 py-3 text-right text-slate-500">
                {{ currency(r.income) }}
              </td>
              <td
                class="px-5 py-3 text-right font-semibold"
                :class="
                  Number(r.profit) < 0 ? 'text-red-600' : 'text-brand-700'
                "
              >
                {{ currency(r.profit) }}
              </td>
              <td class="px-5 py-3 text-right text-slate-500">
                {{ currency(r.cost_per_ha) }}
              </td>
              <td class="px-5 py-3 text-right">
                <UiBadge :tone="marginTone(r.margin_pct)"
                  >{{ number(r.margin_pct, 1) }}%</UiBadge
                >
              </td>
            </tr>
          </TransitionGroup>
        </table>
        <EmptyState
          v-if="!pendingReports && !reports?.results?.length"
          title="Sin informes"
          message="Pulsa «Recalcular» para generar los informes de rentabilidad."
        />
      </UiCard>

      <!-- Cost entries -->
      <UiCard v-else key="entries" :padded="false">
        <div class="p-5" v-if="pendingEntries"><UiSkeleton /></div>
        <table v-else class="w-full text-sm">
          <thead class="bg-slate-50 text-slate-500 text-left">
            <tr>
              <th class="px-5 py-3 font-medium">Fecha</th>
              <th class="px-5 py-3 font-medium">Cultivo</th>
              <th class="px-5 py-3 font-medium">Categoría</th>
              <th class="px-5 py-3 font-medium">Origen</th>
              <th class="px-5 py-3 font-medium">Descripción</th>
              <th class="px-5 py-3 font-medium text-right">Importe</th>
            </tr>
          </thead>
          <TransitionGroup
            tag="tbody"
            name="list"
            class="divide-y divide-slate-100"
          >
            <tr
              v-for="e in entries?.results"
              :key="e.id"
              class="hover:bg-slate-50/70 transition"
            >
              <td class="px-5 py-3 text-slate-500 whitespace-nowrap">
                {{ date(e.date) }}
              </td>
              <td class="px-5 py-3 text-slate-700">{{ e.crop_label }}</td>
              <td class="px-5 py-3">
                <UiBadge :tone="catTone[e.category] ?? 'slate'">{{
                  e.category_display
                }}</UiBadge>
              </td>
              <td class="px-5 py-3">
                <span class="text-xs text-slate-400">{{ e.source }}</span>
              </td>
              <td class="px-5 py-3 text-slate-500">
                {{ e.description || '—' }}
              </td>
              <td class="px-5 py-3 text-right font-medium">
                {{ currency(e.amount) }}
              </td>
            </tr>
          </TransitionGroup>
        </table>
        <EmptyState
          v-if="!pendingEntries && !entries?.results?.length"
          title="Sin costes"
          message="No hay costes registrados todavía."
        >
          <template #action>
            <button
              class="text-sm px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition"
              @click="openEntry"
            >
              + Coste manual
            </button>
          </template>
        </EmptyState>
      </UiCard>
    </Transition>

    <UiModal v-model="showEntry" title="Nuevo coste manual">
      <div class="space-y-4">
        <UiField label="Cultivo" required>
          <UiSelect
            v-model="entryForm.crop"
            :options="cropOptions"
            placeholder="Selecciona un cultivo"
          />
        </UiField>
        <div class="grid grid-cols-2 gap-4">
          <UiField label="Categoría" required>
            <UiSelect v-model="entryForm.category" :options="costCategories" />
          </UiField>
          <UiField label="Importe (€)" required>
            <UiInput
              v-model="entryForm.amount"
              type="number"
              step="0.01"
              placeholder="0,00"
            />
          </UiField>
        </div>
        <UiField label="Fecha" required>
          <UiInput v-model="entryForm.date" type="date" />
        </UiField>
        <UiField label="Descripción">
          <UiInput v-model="entryForm.description" placeholder="Opcional" />
        </UiField>
      </div>
      <template #footer>
        <button
          class="text-sm px-4 py-2 rounded-lg border border-slate-200 hover:bg-slate-50 transition"
          @click="showEntry = false"
        >
          Cancelar
        </button>
        <button
          class="text-sm px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition disabled:opacity-50"
          :disabled="saving"
          @click="submitEntry"
        >
          {{ saving ? 'Guardando…' : 'Registrar coste' }}
        </button>
      </template>
    </UiModal>
  </div>
</template>
