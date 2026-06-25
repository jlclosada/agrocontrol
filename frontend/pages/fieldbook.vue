<script setup lang="ts">
import type {
  Crop,
  FieldOperation,
  Paginated,
  Product,
  Treatment,
} from '~/types/api';

const api = useApi();
const toast = useToast();
const { date } = useFormat();

const tab = ref('operations');

const {
  data: operations,
  pending: pendingOps,
  refresh: refreshOps,
} = await useAsyncData('fieldbook-ops', () =>
  api.get<Paginated<FieldOperation>>('/operations/'),
);
const {
  data: treatments,
  pending: pendingTr,
  refresh: refreshTr,
} = await useAsyncData('fieldbook-treatments', () =>
  api.get<Paginated<Treatment>>('/treatments/'),
);
const { data: crops } = await useAsyncData('fieldbook-crops', () =>
  api.get<Paginated<Crop>>('/crops/'),
);
const { data: products } = await useAsyncData('fieldbook-products', () =>
  api.get<Paginated<Product>>('/products/'),
);

const tabs = computed(() => [
  { value: 'operations', label: 'Operaciones', count: operations.value?.count },
  {
    value: 'treatments',
    label: 'Tratamientos',
    count: treatments.value?.count,
  },
]);

const cropOptions = computed(() =>
  (crops.value?.results ?? []).map((c) => ({
    value: c.id,
    label: `${c.species} ${c.variety} — ${c.parcel_name}`,
  })),
);
const productOptions = computed(() =>
  (products.value?.results ?? []).map((p) => ({ value: p.id, label: p.name })),
);

const operationTypes = [
  { value: 'SOWING', label: 'Siembra' },
  { value: 'FERTILIZATION', label: 'Abonado' },
  { value: 'IRRIGATION', label: 'Riego' },
  { value: 'TREATMENT', label: 'Tratamiento fitosanitario' },
  { value: 'PRUNING', label: 'Poda' },
  { value: 'HARVEST', label: 'Cosecha' },
  { value: 'OTHER', label: 'Otro' },
];

const today = new Date().toISOString().slice(0, 10);
const saving = ref(false);

// --- Operation modal ---
const showOp = ref(false);
const opBlank = () => ({
  crop: '',
  operation_type: 'OTHER',
  date: today,
  description: '',
  area_ha: '',
});
const opForm = ref(opBlank());
function openOp() {
  opForm.value = opBlank();
  showOp.value = true;
}
async function submitOp() {
  if (!opForm.value.crop || !opForm.value.date) {
    toast.error('Selecciona cultivo y fecha.');
    return;
  }
  saving.value = true;
  try {
    const payload: Record<string, unknown> = { ...opForm.value };
    if (!payload.area_ha) delete payload.area_ha;
    await api.post('/operations/', payload);
    toast.success('Operación registrada.');
    showOp.value = false;
    await refreshOps();
  } catch {
    toast.error('No se pudo registrar la operación.');
  } finally {
    saving.value = false;
  }
}

// --- Treatment modal ---
const showTr = ref(false);
const trBlank = () => ({
  crop: '',
  product: '',
  date: today,
  dose: '',
  dose_unit: 'L/ha',
  total_quantity: '',
  target_pest: '',
  weather: '',
});
const trForm = ref(trBlank());
function openTr() {
  trForm.value = trBlank();
  showTr.value = true;
}
async function submitTr() {
  if (
    !trForm.value.crop ||
    !trForm.value.product ||
    !trForm.value.dose ||
    !trForm.value.total_quantity
  ) {
    toast.error('Cultivo, producto, dosis y cantidad son obligatorios.');
    return;
  }
  saving.value = true;
  try {
    await api.post('/treatments/', { ...trForm.value });
    toast.success('Tratamiento registrado. Stock consumido (FEFO).');
    showTr.value = false;
    await Promise.all([refreshTr(), refreshOps()]);
  } catch {
    toast.error('No se pudo registrar el tratamiento.');
  } finally {
    saving.value = false;
  }
}

// --- Search, filters & KPIs ---
const search = ref('');
const opTypeFilter = ref<string>('');
const cropFilter = ref<string>('');
const safetyFilter = ref<'all' | 'ok' | 'pending'>('all');

watch(tab, () => {
  search.value = '';
});

const opTypeFilterOptions = computed(() => [
  { value: '', label: 'Todos los tipos' },
  ...operationTypes,
]);
const cropFilterOptions = computed(() => [
  { value: '', label: 'Todos los cultivos' },
  ...cropOptions.value,
]);
const safetyFilterOptions = [
  { value: 'all', label: 'Todos los plazos' },
  { value: 'ok', label: 'Plazo cumplido' },
  { value: 'pending', label: 'Plazo pendiente' },
];

const filteredOperations = computed(() => {
  const q = search.value.trim().toLowerCase();
  return (operations.value?.results ?? []).filter((op) => {
    if (opTypeFilter.value && op.operation_type !== opTypeFilter.value)
      return false;
    if (cropFilter.value && op.crop !== cropFilter.value) return false;
    if (!q) return true;
    return [op.description, op.operation_type_display, op.performed_by]
      .filter(Boolean)
      .some((v) => String(v).toLowerCase().includes(q));
  });
});
const filteredTreatments = computed(() => {
  const q = search.value.trim().toLowerCase();
  return (treatments.value?.results ?? []).filter((t) => {
    if (cropFilter.value && t.crop !== cropFilter.value) return false;
    if (safetyFilter.value === 'ok' && !t.safety_interval_ok) return false;
    if (safetyFilter.value === 'pending' && t.safety_interval_ok) return false;
    if (!q) return true;
    return [t.product_name, t.crop_label, t.target_pest]
      .filter(Boolean)
      .some((v) => String(v).toLowerCase().includes(q));
  });
});

const kpis = computed(() => {
  const ops = operations.value?.results ?? [];
  const trs = treatments.value?.results ?? [];
  const monthAgo = Date.now() - 30 * 86_400_000;
  return {
    operations: ops.length,
    treatments: trs.length,
    pendingSafety: trs.filter((t) => !t.safety_interval_ok).length,
    recentOps: ops.filter((o) => new Date(o.date).getTime() >= monthAgo).length,
  };
});

const hasFilters = computed(() => {
  if (tab.value === 'operations')
    return !!search.value || !!opTypeFilter.value || !!cropFilter.value;
  return !!search.value || !!cropFilter.value || safetyFilter.value !== 'all';
});
function resetFilters() {
  search.value = '';
  opTypeFilter.value = '';
  cropFilter.value = '';
  safetyFilter.value = 'all';
}
</script>

<template>
  <div class="p-6 lg:p-8 space-y-6 w-full">
    <PageHeader
      title="Cuaderno de campo"
      subtitle="Registro digital de labores y tratamientos fitosanitarios"
    >
      <template #actions>
        <UiTabs v-model="tab" :tabs="tabs" />
        <button
          v-if="tab === 'operations'"
          class="text-sm px-3 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition shadow-glow"
          @click="openOp"
        >
          + Operación
        </button>
        <button
          v-else
          class="text-sm px-3 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition shadow-glow"
          @click="openTr"
        >
          + Tratamiento
        </button>
      </template>
    </PageHeader>

    <!-- KPI summary -->
    <div class="grid grid-cols-2 xl:grid-cols-4 gap-4">
      <StatCard label="Operaciones" :value="kpis.operations" tone="brand" />
      <StatCard label="Tratamientos" :value="kpis.treatments" tone="sky" />
      <StatCard
        label="Plazo pendiente"
        :value="kpis.pendingSafety"
        tone="red"
      />
      <StatCard label="Labores 30 días" :value="kpis.recentOps" tone="violet" />
    </div>

    <!-- Search & filters toolbar -->
    <div class="flex items-center flex-wrap gap-2.5">
      <UiSearchInput
        v-model="search"
        :placeholder="
          tab === 'operations'
            ? 'Buscar por descripción, tipo o responsable…'
            : 'Buscar por producto, cultivo u objetivo…'
        "
        class="w-full sm:w-72"
      />
      <UiFilterSelect
        v-if="tab === 'operations'"
        v-model="opTypeFilter"
        :options="opTypeFilterOptions"
        icon="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
        class="w-52"
      />
      <UiFilterSelect
        v-else
        v-model="safetyFilter"
        :options="safetyFilterOptions"
        icon="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
        class="w-48"
      />
      <UiFilterSelect
        v-model="cropFilter"
        :options="cropFilterOptions"
        icon="M12 2C8 6 8 10 12 14c4-4 4-8 0-12zM4 14c2 2 4 2 6 0M14 14c2 2 4 2 6 0"
        class="w-56"
      />
      <button
        v-if="hasFilters"
        class="inline-flex items-center gap-1.5 text-sm px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-500 transition"
        @click="resetFilters"
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
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
        Limpiar
      </button>
    </div>

    <Transition name="page" mode="out-in">
      <!-- Operations -->
      <UiCard v-if="tab === 'operations'" key="ops" :padded="false">
        <div class="p-5 pb-0" v-if="pendingOps"><UiSkeleton /></div>
        <table v-else class="w-full text-sm">
          <thead class="bg-slate-50 text-slate-500 text-left">
            <tr>
              <th class="px-5 py-3 font-medium">Fecha</th>
              <th class="px-5 py-3 font-medium">Tipo</th>
              <th class="px-5 py-3 font-medium">Descripción</th>
              <th class="px-5 py-3 font-medium text-right">Superficie (ha)</th>
              <th class="px-5 py-3 font-medium">Responsable</th>
            </tr>
          </thead>
          <TransitionGroup
            tag="tbody"
            name="list"
            class="divide-y divide-slate-100"
          >
            <tr
              v-for="op in filteredOperations"
              :key="op.id"
              class="hover:bg-slate-50/70 transition"
            >
              <td class="px-5 py-3 text-slate-500 whitespace-nowrap">
                {{ date(op.date) }}
              </td>
              <td class="px-5 py-3">
                <UiBadge tone="sky">{{ op.operation_type_display }}</UiBadge>
              </td>
              <td class="px-5 py-3 text-slate-700">
                {{ op.description || '—' }}
              </td>
              <td class="px-5 py-3 text-right">{{ op.area_ha || '—' }}</td>
              <td class="px-5 py-3 text-slate-500">
                {{ op.performed_by || '—' }}
              </td>
            </tr>
          </TransitionGroup>
        </table>
        <EmptyState
          v-if="!pendingOps && !filteredOperations.length"
          :title="hasFilters ? 'Sin coincidencias' : 'Sin operaciones'"
          :message="
            hasFilters
              ? 'Ninguna operación coincide con los filtros.'
              : 'Aún no se han registrado labores de campo.'
          "
        />
      </UiCard>

      <!-- Treatments -->
      <UiCard v-else key="tr" :padded="false">
        <div class="p-5 pb-0" v-if="pendingTr"><UiSkeleton /></div>
        <table v-else class="w-full text-sm">
          <thead class="bg-slate-50 text-slate-500 text-left">
            <tr>
              <th class="px-5 py-3 font-medium">Fecha</th>
              <th class="px-5 py-3 font-medium">Cultivo</th>
              <th class="px-5 py-3 font-medium">Producto</th>
              <th class="px-5 py-3 font-medium">Dosis</th>
              <th class="px-5 py-3 font-medium">Objetivo</th>
              <th class="px-5 py-3 font-medium">Plazo seguridad</th>
            </tr>
          </thead>
          <TransitionGroup
            tag="tbody"
            name="list"
            class="divide-y divide-slate-100"
          >
            <tr
              v-for="t in filteredTreatments"
              :key="t.id"
              class="hover:bg-slate-50/70 transition"
            >
              <td class="px-5 py-3 text-slate-500 whitespace-nowrap">
                {{ date(t.date) }}
              </td>
              <td class="px-5 py-3 text-slate-700">{{ t.crop_label }}</td>
              <td class="px-5 py-3 font-medium text-slate-700">
                {{ t.product_name }}
              </td>
              <td class="px-5 py-3 text-slate-500">
                {{ t.dose }} {{ t.dose_unit }}
              </td>
              <td class="px-5 py-3 text-slate-500">
                {{ t.target_pest || '—' }}
              </td>
              <td class="px-5 py-3">
                <UiBadge :tone="t.safety_interval_ok ? 'green' : 'red'" dot>
                  {{ t.safety_interval_ok ? 'Cumplido' : 'Pendiente' }}
                </UiBadge>
              </td>
            </tr>
          </TransitionGroup>
        </table>
        <EmptyState
          v-if="!pendingTr && !filteredTreatments.length"
          :title="hasFilters ? 'Sin coincidencias' : 'Sin tratamientos'"
          :message="
            hasFilters
              ? 'Ningún tratamiento coincide con los filtros.'
              : 'No hay tratamientos fitosanitarios registrados.'
          "
        />
      </UiCard>
    </Transition>

    <!-- Operation modal -->
    <UiModal v-model="showOp" title="Nueva operación de campo">
      <div class="space-y-4">
        <UiField label="Cultivo" required>
          <UiSelect
            v-model="opForm.crop"
            :options="cropOptions"
            placeholder="Selecciona un cultivo"
          />
        </UiField>
        <div class="grid grid-cols-2 gap-4">
          <UiField label="Tipo" required>
            <UiSelect
              v-model="opForm.operation_type"
              :options="operationTypes"
            />
          </UiField>
          <UiField label="Fecha" required>
            <UiInput v-model="opForm.date" type="date" />
          </UiField>
        </div>
        <UiField label="Superficie (ha)">
          <UiInput
            v-model="opForm.area_ha"
            type="number"
            step="0.0001"
            placeholder="Opcional"
          />
        </UiField>
        <UiField label="Descripción">
          <UiTextarea
            v-model="opForm.description"
            placeholder="Detalle de la labor…"
          />
        </UiField>
      </div>
      <template #footer>
        <button
          class="text-sm px-4 py-2 rounded-lg border border-slate-200 hover:bg-slate-50 transition"
          @click="showOp = false"
        >
          Cancelar
        </button>
        <button
          class="text-sm px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition disabled:opacity-50"
          :disabled="saving"
          @click="submitOp"
        >
          {{ saving ? 'Guardando…' : 'Registrar' }}
        </button>
      </template>
    </UiModal>

    <!-- Treatment modal -->
    <UiModal v-model="showTr" title="Nuevo tratamiento fitosanitario">
      <div class="space-y-4">
        <UiField label="Cultivo" required>
          <UiSelect
            v-model="trForm.crop"
            :options="cropOptions"
            placeholder="Selecciona un cultivo"
          />
        </UiField>
        <UiField label="Producto" required>
          <UiSelect
            v-model="trForm.product"
            :options="productOptions"
            placeholder="Selecciona un producto"
          />
        </UiField>
        <div class="grid grid-cols-2 gap-4">
          <UiField label="Fecha" required>
            <UiInput v-model="trForm.date" type="date" />
          </UiField>
          <UiField
            label="Cantidad total"
            required
            help="En la unidad del producto. Consume stock por FEFO."
          >
            <UiInput
              v-model="trForm.total_quantity"
              type="number"
              step="0.01"
              placeholder="0,00"
            />
          </UiField>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <UiField label="Dosis" required>
            <UiInput
              v-model="trForm.dose"
              type="number"
              step="0.0001"
              placeholder="0,00"
            />
          </UiField>
          <UiField label="Unidad de dosis">
            <UiInput v-model="trForm.dose_unit" placeholder="L/ha" />
          </UiField>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <UiField label="Objetivo / plaga">
            <UiInput v-model="trForm.target_pest" placeholder="Opcional" />
          </UiField>
          <UiField label="Meteorología">
            <UiInput v-model="trForm.weather" placeholder="Opcional" />
          </UiField>
        </div>
      </div>
      <template #footer>
        <button
          class="text-sm px-4 py-2 rounded-lg border border-slate-200 hover:bg-slate-50 transition"
          @click="showTr = false"
        >
          Cancelar
        </button>
        <button
          class="text-sm px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition disabled:opacity-50"
          :disabled="saving"
          @click="submitTr"
        >
          {{ saving ? 'Guardando…' : 'Registrar' }}
        </button>
      </template>
    </UiModal>
  </div>
</template>
