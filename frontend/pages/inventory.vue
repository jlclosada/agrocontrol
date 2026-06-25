<script setup lang="ts">
import type {
  Paginated,
  Product,
  StockBatch,
  StockMovement,
} from '~/types/api';

const api = useApi();
const toast = useToast();
const { date, currency, number } = useFormat();

const tab = ref('products');

const {
  data: products,
  pending: pendingProducts,
  refresh: refreshProducts,
} = await useAsyncData('inv-products', () =>
  api.get<Paginated<Product>>('/products/'),
);
const {
  data: batches,
  pending: pendingBatches,
  refresh: refreshBatches,
} = await useAsyncData('inv-batches', () =>
  api.get<Paginated<StockBatch>>('/stock-batches/'),
);
const {
  data: movements,
  pending: pendingMoves,
  refresh: refreshMoves,
} = await useAsyncData('inv-moves', () =>
  api.get<Paginated<StockMovement>>('/stock-movements/'),
);

const tabs = computed(() => [
  { value: 'products', label: 'Productos', count: products.value?.count },
  { value: 'batches', label: 'Lotes (FEFO)', count: batches.value?.count },
  { value: 'movements', label: 'Movimientos', count: movements.value?.count },
]);

const lowStockCount = computed(
  () => products.value?.results?.filter((p) => p.needs_reorder).length ?? 0,
);

const productOptions = computed(() =>
  (products.value?.results ?? []).map((p) => ({
    value: p.id,
    label: `${p.name} (${p.unit})`,
  })),
);
const batchOptions = computed(() =>
  (batches.value?.results ?? []).map((b) => ({
    value: b.id,
    label: `${b.product_name} · lote ${b.lot || '—'}`,
  })),
);

const categories = [
  { value: 'HERBICIDE', label: 'Herbicida' },
  { value: 'FUNGICIDE', label: 'Fungicida' },
  { value: 'INSECTICIDE', label: 'Insecticida' },
  { value: 'FERTILIZER', label: 'Fertilizante' },
  { value: 'OTHER', label: 'Otro' },
];
const movementTypes = [
  { value: 'IN', label: 'Entrada' },
  { value: 'OUT', label: 'Salida' },
  { value: 'ADJUST', label: 'Ajuste' },
];

const today = new Date().toISOString().slice(0, 10);
const saving = ref(false);

// --- Product modal ---
const showProduct = ref(false);
const productBlank = () => ({
  name: '',
  registration_number: '',
  active_ingredient: '',
  category: 'OTHER',
  unit: 'L',
  safety_interval_days: '0',
  reorder_level: '0',
  unit_cost: '0',
});
const productForm = ref(productBlank());
function openProduct() {
  productForm.value = productBlank();
  showProduct.value = true;
}
async function submitProduct() {
  if (!productForm.value.name) {
    toast.error('El nombre es obligatorio.');
    return;
  }
  saving.value = true;
  try {
    await api.post('/products/', { ...productForm.value });
    toast.success('Producto creado.');
    showProduct.value = false;
    await refreshProducts();
  } catch {
    toast.error('No se pudo crear el producto.');
  } finally {
    saving.value = false;
  }
}

// --- Batch modal ---
const showBatch = ref(false);
const batchBlank = () => ({
  product: '',
  lot: '',
  received_date: today,
  expiry_date: '',
});
const batchForm = ref(batchBlank());
function openBatch() {
  batchForm.value = batchBlank();
  showBatch.value = true;
}
async function submitBatch() {
  if (!batchForm.value.product) {
    toast.error('Selecciona un producto.');
    return;
  }
  saving.value = true;
  try {
    const payload: Record<string, unknown> = { ...batchForm.value };
    if (!payload.expiry_date) delete payload.expiry_date;
    if (!payload.received_date) delete payload.received_date;
    await api.post('/stock-batches/', payload);
    toast.success('Lote creado.');
    showBatch.value = false;
    await refreshBatches();
  } catch {
    toast.error('No se pudo crear el lote.');
  } finally {
    saving.value = false;
  }
}

// --- Movement modal ---
const showMove = ref(false);
const moveBlank = () => ({
  product: '',
  batch: '',
  movement_type: 'IN',
  quantity: '',
  reason: '',
});
const moveForm = ref(moveBlank());
function openMove() {
  moveForm.value = moveBlank();
  showMove.value = true;
}
const moveBatchOptions = computed(() =>
  (batches.value?.results ?? [])
    .filter(
      (b) => !moveForm.value.product || b.product === moveForm.value.product,
    )
    .map((b) => ({ value: b.id, label: `lote ${b.lot || '—'}` })),
);
async function submitMove() {
  if (!moveForm.value.product || !moveForm.value.quantity) {
    toast.error('Producto y cantidad son obligatorios.');
    return;
  }
  saving.value = true;
  try {
    const payload: Record<string, unknown> = { ...moveForm.value };
    if (!payload.batch) delete payload.batch;
    await api.post('/stock-movements/', payload);
    toast.success('Movimiento registrado.');
    showMove.value = false;
    await Promise.all([refreshMoves(), refreshProducts(), refreshBatches()]);
  } catch {
    toast.error('No se pudo registrar el movimiento.');
  } finally {
    saving.value = false;
  }
}

function batchTone(b: StockBatch) {
  if (b.is_expired) return 'red';
  if (!b.expiry_date) return 'slate';
  const days = (new Date(b.expiry_date).getTime() - Date.now()) / 86_400_000;
  if (days <= 30) return 'amber';
  return 'green';
}
function batchLabel(b: StockBatch) {
  if (b.is_expired) return 'Caducado';
  if (!b.expiry_date) return 'Sin caducidad';
  const days = Math.round(
    (new Date(b.expiry_date).getTime() - Date.now()) / 86_400_000,
  );
  if (days <= 30) return `Caduca en ${days} d`;
  return 'Vigente';
}

const moveTone: Record<string, 'green' | 'red' | 'sky' | 'slate'> = {
  IN: 'green',
  OUT: 'red',
  ADJUST: 'sky',
};

// --- Search, filters & KPIs ---
const search = ref('');
const productCategory = ref<string>('');
const productStock = ref<'all' | 'low' | 'ok'>('all');
const batchStatus = ref<'all' | 'ok' | 'expiring' | 'expired'>('all');
const moveType = ref<string>('');

watch(tab, () => {
  search.value = '';
});

const categoryFilterOptions = computed(() => [
  { value: '', label: 'Todas las categorías' },
  ...categories,
]);
const productStockOptions = [
  { value: 'all', label: 'Todo el stock' },
  { value: 'low', label: 'Stock bajo' },
  { value: 'ok', label: 'Stock OK' },
];
const batchStatusOptions = [
  { value: 'all', label: 'Todos los estados' },
  { value: 'ok', label: 'Vigentes' },
  { value: 'expiring', label: 'Caduca <30 d' },
  { value: 'expired', label: 'Caducados' },
];
const moveTypeOptions = computed(() => [
  { value: '', label: 'Todos los tipos' },
  ...movementTypes,
]);

const filteredProducts = computed(() => {
  const q = search.value.trim().toLowerCase();
  return (products.value?.results ?? []).filter((p) => {
    if (productCategory.value && p.category !== productCategory.value)
      return false;
    if (productStock.value === 'low' && !p.needs_reorder) return false;
    if (productStock.value === 'ok' && p.needs_reorder) return false;
    if (!q) return true;
    return [p.name, p.active_ingredient, p.registration_number]
      .filter(Boolean)
      .some((v) => String(v).toLowerCase().includes(q));
  });
});

function batchDays(b: StockBatch) {
  if (!b.expiry_date) return Infinity;
  return (new Date(b.expiry_date).getTime() - Date.now()) / 86_400_000;
}
const filteredBatches = computed(() => {
  const q = search.value.trim().toLowerCase();
  return (batches.value?.results ?? []).filter((b) => {
    if (batchStatus.value === 'expired' && !b.is_expired) return false;
    if (batchStatus.value === 'ok' && (b.is_expired || batchDays(b) <= 30))
      return false;
    if (
      batchStatus.value === 'expiring' &&
      (b.is_expired || batchDays(b) > 30 || !b.expiry_date)
    )
      return false;
    if (!q) return true;
    return [b.product_name, b.lot]
      .filter(Boolean)
      .some((v) => String(v).toLowerCase().includes(q));
  });
});

const filteredMovements = computed(() => {
  const q = search.value.trim().toLowerCase();
  return (movements.value?.results ?? []).filter((m) => {
    if (moveType.value && m.movement_type !== moveType.value) return false;
    if (!q) return true;
    return [m.product_name, m.reason]
      .filter(Boolean)
      .some((v) => String(v).toLowerCase().includes(q));
  });
});

const kpis = computed(() => {
  const prods = products.value?.results ?? [];
  const batchRows = batches.value?.results ?? [];
  return {
    products: prods.length,
    lowStock: prods.filter((p) => p.needs_reorder).length,
    batches: batchRows.length,
    expiring: batchRows.filter(
      (b) => !b.is_expired && b.expiry_date && batchDays(b) <= 30,
    ).length,
    stockValue: prods.reduce(
      (s, p) => s + Number(p.current_stock) * Number(p.unit_cost),
      0,
    ),
  };
});

const hasFilters = computed(() => {
  if (tab.value === 'products')
    return (
      !!search.value || !!productCategory.value || productStock.value !== 'all'
    );
  if (tab.value === 'batches')
    return !!search.value || batchStatus.value !== 'all';
  return !!search.value || !!moveType.value;
});
function resetFilters() {
  search.value = '';
  productCategory.value = '';
  productStock.value = 'all';
  batchStatus.value = 'all';
  moveType.value = '';
}
</script>

<template>
  <div class="p-6 lg:p-8 space-y-6 w-full">
    <PageHeader
      title="Inventario"
      subtitle="Productos fitosanitarios, lotes con caducidad y movimientos de stock"
    >
      <template #actions>
        <UiBadge v-if="lowStockCount" tone="amber" dot>
          {{ lowStockCount }} con stock bajo
        </UiBadge>
        <UiTabs v-model="tab" :tabs="tabs" />
        <button
          v-if="tab === 'products'"
          class="text-sm px-3 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition shadow-glow"
          @click="openProduct"
        >
          + Producto
        </button>
        <button
          v-else-if="tab === 'batches'"
          class="text-sm px-3 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition shadow-glow"
          @click="openBatch"
        >
          + Lote
        </button>
        <button
          v-else
          class="text-sm px-3 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition shadow-glow"
          @click="openMove"
        >
          + Movimiento
        </button>
      </template>
    </PageHeader>

    <!-- KPI summary -->
    <div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-4">
      <StatCard label="Productos" :value="kpis.products" tone="brand" />
      <StatCard label="Stock bajo" :value="kpis.lowStock" tone="amber" />
      <StatCard label="Lotes" :value="kpis.batches" tone="sky" />
      <StatCard label="Caducan <30d" :value="kpis.expiring" tone="red" />
      <StatCard
        label="Valor stock"
        :value="kpis.stockValue"
        :decimals="2"
        prefix="€ "
        tone="violet"
      />
    </div>

    <!-- Search & filters toolbar -->
    <div class="flex items-center flex-wrap gap-2.5">
      <UiSearchInput
        v-model="search"
        :placeholder="
          tab === 'products'
            ? 'Buscar producto, materia activa…'
            : tab === 'batches'
              ? 'Buscar por producto o lote…'
              : 'Buscar por producto o motivo…'
        "
        class="w-full sm:w-72"
      />
      <template v-if="tab === 'products'">
        <UiFilterSelect
          v-model="productCategory"
          :options="categoryFilterOptions"
          icon="M7 7h.01M7 3h5a1.99 1.99 0 011.414.586l7 7a2 2 0 010 2.828l-5 5a2 2 0 01-2.828 0l-7-7A1.99 1.99 0 014 9V5a2 2 0 012-2z"
          class="w-48"
        />
        <UiFilterSelect
          v-model="productStock"
          :options="productStockOptions"
          icon="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10"
          class="w-44"
        />
      </template>
      <UiFilterSelect
        v-else-if="tab === 'batches'"
        v-model="batchStatus"
        :options="batchStatusOptions"
        icon="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
        class="w-48"
      />
      <UiFilterSelect
        v-else
        v-model="moveType"
        :options="moveTypeOptions"
        icon="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"
        class="w-48"
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
      <!-- Products -->
      <UiCard v-if="tab === 'products'" key="prod" :padded="false">
        <div class="p-5" v-if="pendingProducts"><UiSkeleton /></div>
        <table v-else class="w-full text-sm">
          <thead class="bg-slate-50 text-slate-500 text-left">
            <tr>
              <th class="px-5 py-3 font-medium">Producto</th>
              <th class="px-5 py-3 font-medium">Materia activa</th>
              <th class="px-5 py-3 font-medium text-right">Stock</th>
              <th class="px-5 py-3 font-medium text-right">Reorden</th>
              <th class="px-5 py-3 font-medium text-right">Coste ud.</th>
              <th class="px-5 py-3 font-medium">Estado</th>
            </tr>
          </thead>
          <TransitionGroup
            tag="tbody"
            name="list"
            class="divide-y divide-slate-100"
          >
            <tr
              v-for="p in filteredProducts"
              :key="p.id"
              class="hover:bg-slate-50/70 transition"
            >
              <td class="px-5 py-3">
                <p class="font-medium text-slate-700">{{ p.name }}</p>
                <p class="text-xs text-slate-400">
                  {{ p.registration_number || '—' }}
                </p>
              </td>
              <td class="px-5 py-3 text-slate-500">
                {{ p.active_ingredient || '—' }}
              </td>
              <td class="px-5 py-3 text-right font-medium">
                {{ number(p.current_stock, 2) }} {{ p.unit }}
              </td>
              <td class="px-5 py-3 text-right text-slate-500">
                {{ number(p.reorder_level, 2) }}
              </td>
              <td class="px-5 py-3 text-right text-slate-500">
                {{ currency(p.unit_cost) }}
              </td>
              <td class="px-5 py-3">
                <UiBadge :tone="p.needs_reorder ? 'amber' : 'green'" dot>
                  {{ p.needs_reorder ? 'Stock bajo' : 'OK' }}
                </UiBadge>
              </td>
            </tr>
          </TransitionGroup>
        </table>
        <EmptyState
          v-if="!pendingProducts && !filteredProducts.length"
          :title="hasFilters ? 'Sin coincidencias' : 'Sin productos'"
          :message="
            hasFilters
              ? 'Ningún producto coincide con los filtros.'
              : 'Aún no hay productos en el inventario.'
          "
        />
      </UiCard>

      <!-- Batches -->
      <UiCard v-else-if="tab === 'batches'" key="batch" :padded="false">
        <div class="p-5" v-if="pendingBatches"><UiSkeleton /></div>
        <table v-else class="w-full text-sm">
          <thead class="bg-slate-50 text-slate-500 text-left">
            <tr>
              <th class="px-5 py-3 font-medium">Producto</th>
              <th class="px-5 py-3 font-medium">Lote</th>
              <th class="px-5 py-3 font-medium">Recepción</th>
              <th class="px-5 py-3 font-medium">Caducidad</th>
              <th class="px-5 py-3 font-medium text-right">Cantidad</th>
              <th class="px-5 py-3 font-medium">Estado</th>
            </tr>
          </thead>
          <TransitionGroup
            tag="tbody"
            name="list"
            class="divide-y divide-slate-100"
          >
            <tr
              v-for="b in filteredBatches"
              :key="b.id"
              class="hover:bg-slate-50/70 transition"
            >
              <td class="px-5 py-3 font-medium text-slate-700">
                {{ b.product_name }}
              </td>
              <td class="px-5 py-3 font-mono text-xs text-slate-500">
                {{ b.lot }}
              </td>
              <td class="px-5 py-3 text-slate-500">
                {{ date(b.received_date) }}
              </td>
              <td class="px-5 py-3 text-slate-500">
                {{ date(b.expiry_date) }}
              </td>
              <td class="px-5 py-3 text-right font-medium">
                {{ number(b.quantity, 2) }}
              </td>
              <td class="px-5 py-3">
                <UiBadge :tone="batchTone(b)" dot>{{ batchLabel(b) }}</UiBadge>
              </td>
            </tr>
          </TransitionGroup>
        </table>
        <EmptyState
          v-if="!pendingBatches && !filteredBatches.length"
          :title="hasFilters ? 'Sin coincidencias' : 'Sin lotes'"
          :message="
            hasFilters
              ? 'Ningún lote coincide con los filtros.'
              : 'No hay lotes de stock registrados.'
          "
        />
      </UiCard>

      <!-- Movements -->
      <UiCard v-else key="move" :padded="false">
        <div class="p-5" v-if="pendingMoves"><UiSkeleton /></div>
        <table v-else class="w-full text-sm">
          <thead class="bg-slate-50 text-slate-500 text-left">
            <tr>
              <th class="px-5 py-3 font-medium">Fecha</th>
              <th class="px-5 py-3 font-medium">Producto</th>
              <th class="px-5 py-3 font-medium">Tipo</th>
              <th class="px-5 py-3 font-medium text-right">Cantidad</th>
              <th class="px-5 py-3 font-medium">Motivo</th>
            </tr>
          </thead>
          <TransitionGroup
            tag="tbody"
            name="list"
            class="divide-y divide-slate-100"
          >
            <tr
              v-for="m in filteredMovements"
              :key="m.id"
              class="hover:bg-slate-50/70 transition"
            >
              <td class="px-5 py-3 text-slate-500 whitespace-nowrap">
                {{ date(m.created_at) }}
              </td>
              <td class="px-5 py-3 font-medium text-slate-700">
                {{ m.product_name }}
              </td>
              <td class="px-5 py-3">
                <UiBadge :tone="moveTone[m.movement_type] ?? 'slate'">{{
                  m.movement_type
                }}</UiBadge>
              </td>
              <td
                class="px-5 py-3 text-right font-medium"
                :class="
                  Number(m.signed_quantity) < 0
                    ? 'text-red-600'
                    : 'text-brand-700'
                "
              >
                {{ number(m.signed_quantity, 2) }}
              </td>
              <td class="px-5 py-3 text-slate-500">{{ m.reason || '—' }}</td>
            </tr>
          </TransitionGroup>
        </table>
        <EmptyState
          v-if="!pendingMoves && !filteredMovements.length"
          :title="hasFilters ? 'Sin coincidencias' : 'Sin movimientos'"
          :message="
            hasFilters
              ? 'Ningún movimiento coincide con los filtros.'
              : 'No hay movimientos de stock registrados.'
          "
        />
      </UiCard>
    </Transition>

    <!-- Product modal -->
    <UiModal v-model="showProduct" title="Nuevo producto">
      <div class="space-y-4">
        <UiField label="Nombre" required>
          <UiInput v-model="productForm.name" placeholder="Ej. Glifosato 36%" />
        </UiField>
        <div class="grid grid-cols-2 gap-4">
          <UiField label="Materia activa">
            <UiInput
              v-model="productForm.active_ingredient"
              placeholder="Opcional"
            />
          </UiField>
          <UiField label="Nº registro">
            <UiInput
              v-model="productForm.registration_number"
              placeholder="Opcional"
            />
          </UiField>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <UiField label="Categoría">
            <UiSelect v-model="productForm.category" :options="categories" />
          </UiField>
          <UiField label="Unidad">
            <UiInput v-model="productForm.unit" placeholder="L, kg, ud…" />
          </UiField>
        </div>
        <div class="grid grid-cols-3 gap-4">
          <UiField label="Plazo seg. (días)">
            <UiInput
              v-model="productForm.safety_interval_days"
              type="number"
              min="0"
            />
          </UiField>
          <UiField label="Nivel reorden">
            <UiInput
              v-model="productForm.reorder_level"
              type="number"
              step="0.01"
            />
          </UiField>
          <UiField label="Coste ud. (€)">
            <UiInput
              v-model="productForm.unit_cost"
              type="number"
              step="0.0001"
            />
          </UiField>
        </div>
      </div>
      <template #footer>
        <button
          class="text-sm px-4 py-2 rounded-lg border border-slate-200 hover:bg-slate-50 transition"
          @click="showProduct = false"
        >
          Cancelar
        </button>
        <button
          class="text-sm px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition disabled:opacity-50"
          :disabled="saving"
          @click="submitProduct"
        >
          {{ saving ? 'Guardando…' : 'Crear producto' }}
        </button>
      </template>
    </UiModal>

    <!-- Batch modal -->
    <UiModal v-model="showBatch" title="Nuevo lote">
      <div class="space-y-4">
        <UiField label="Producto" required>
          <UiSelect
            v-model="batchForm.product"
            :options="productOptions"
            placeholder="Selecciona un producto"
          />
        </UiField>
        <UiField label="Lote">
          <UiInput
            v-model="batchForm.lot"
            placeholder="Identificador del lote"
          />
        </UiField>
        <div class="grid grid-cols-2 gap-4">
          <UiField label="Fecha de recepción">
            <UiInput v-model="batchForm.received_date" type="date" />
          </UiField>
          <UiField label="Caducidad" help="Usada para el orden FEFO.">
            <UiInput v-model="batchForm.expiry_date" type="date" />
          </UiField>
        </div>
        <p class="text-xs text-slate-400">
          La cantidad del lote se gestiona con movimientos de entrada.
        </p>
      </div>
      <template #footer>
        <button
          class="text-sm px-4 py-2 rounded-lg border border-slate-200 hover:bg-slate-50 transition"
          @click="showBatch = false"
        >
          Cancelar
        </button>
        <button
          class="text-sm px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition disabled:opacity-50"
          :disabled="saving"
          @click="submitBatch"
        >
          {{ saving ? 'Guardando…' : 'Crear lote' }}
        </button>
      </template>
    </UiModal>

    <!-- Movement modal -->
    <UiModal v-model="showMove" title="Nuevo movimiento de stock">
      <div class="space-y-4">
        <UiField label="Producto" required>
          <UiSelect
            v-model="moveForm.product"
            :options="productOptions"
            placeholder="Selecciona un producto"
          />
        </UiField>
        <div class="grid grid-cols-2 gap-4">
          <UiField label="Tipo" required>
            <UiSelect
              v-model="moveForm.movement_type"
              :options="movementTypes"
            />
          </UiField>
          <UiField label="Cantidad" required>
            <UiInput
              v-model="moveForm.quantity"
              type="number"
              step="0.01"
              placeholder="0,00"
            />
          </UiField>
        </div>
        <UiField
          label="Lote"
          help="Opcional; recomendado para entradas con caducidad."
        >
          <UiSelect
            v-model="moveForm.batch"
            :options="moveBatchOptions"
            placeholder="Sin lote"
          />
        </UiField>
        <UiField label="Motivo">
          <UiInput v-model="moveForm.reason" placeholder="Opcional" />
        </UiField>
      </div>
      <template #footer>
        <button
          class="text-sm px-4 py-2 rounded-lg border border-slate-200 hover:bg-slate-50 transition"
          @click="showMove = false"
        >
          Cancelar
        </button>
        <button
          class="text-sm px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition disabled:opacity-50"
          :disabled="saving"
          @click="submitMove"
        >
          {{ saving ? 'Guardando…' : 'Registrar' }}
        </button>
      </template>
    </UiModal>
  </div>
</template>
