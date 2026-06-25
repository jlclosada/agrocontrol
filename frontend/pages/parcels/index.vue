<script setup lang="ts">
import type { Farm, Paginated, Parcel } from '~/types/api';

const api = useApi();
const toast = useToast();
const { number, date } = useFormat();
const { data, pending, refresh } = await useAsyncData('parcels-page', () =>
  api.get<Paginated<Parcel>>('/parcels/'),
);
const { data: farms, refresh: refreshFarms } = await useAsyncData(
  'parcels-farms',
  () => api.get<Paginated<Farm>>('/farms/'),
);

const totalArea = computed(() =>
  (data.value?.results ?? []).reduce((s, p) => s + Number(p.area_ha), 0),
);

const farmOptions = computed(() =>
  (farms.value?.results ?? []).map((f) => ({ value: f.id, label: f.name })),
);

// ---- Search, filters & sorting ----
const search = ref('');
const statusFilter = ref<'all' | 'active' | 'inactive'>('all');
const farmFilter = ref<string>('');
const sortKey = ref<'name' | 'farm_name' | 'area_ha' | 'soil_type'>('name');
const sortDir = ref<'asc' | 'desc'>('asc');

const statusFilterOptions = [
  { value: 'all', label: 'Todos los estados' },
  { value: 'active', label: 'Solo activas' },
  { value: 'inactive', label: 'Solo inactivas' },
];
const farmFilterOptions = computed(() => [
  { value: '', label: 'Todas las explotaciones' },
  ...farmOptions.value,
]);

function toggleSort(key: typeof sortKey.value) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey.value = key;
    sortDir.value = 'asc';
  }
}

function sortIndicator(key: typeof sortKey.value) {
  if (sortKey.value !== key) return '';
  return sortDir.value === 'asc' ? '▲' : '▼';
}

const filteredParcels = computed(() => {
  const q = search.value.trim().toLowerCase();
  let rows = (data.value?.results ?? []).filter((p) => {
    if (statusFilter.value === 'active' && !p.is_active) return false;
    if (statusFilter.value === 'inactive' && p.is_active) return false;
    if (farmFilter.value && p.farm !== farmFilter.value) return false;
    if (!q) return true;
    return [
      p.name,
      p.farm_name,
      p.sigpac_ref,
      p.soil_type,
      p.municipality,
      p.province,
    ]
      .filter(Boolean)
      .some((v) => String(v).toLowerCase().includes(q));
  });
  const dir = sortDir.value === 'asc' ? 1 : -1;
  rows = [...rows].sort((a, b) => {
    const k = sortKey.value;
    let av: string | number = (a as any)[k] ?? '';
    let bv: string | number = (b as any)[k] ?? '';
    if (k === 'area_ha') {
      av = Number(a.area_ha);
      bv = Number(b.area_ha);
    } else {
      av = String(av).toLowerCase();
      bv = String(bv).toLowerCase();
    }
    if (av < bv) return -1 * dir;
    if (av > bv) return 1 * dir;
    return 0;
  });
  return rows;
});

const filteredArea = computed(() =>
  filteredParcels.value.reduce((s, p) => s + Number(p.area_ha), 0),
);

const kpis = computed(() => {
  const rows = data.value?.results ?? [];
  return {
    total: rows.length,
    active: rows.filter((p) => p.is_active).length,
    area: totalArea.value,
    geo: rows.filter(
      (p) =>
        (p.polygon as number[][] | null)?.length || (p.latitude && p.longitude),
    ).length,
    farms: farms.value?.results?.length ?? 0,
  };
});

function resetFilters() {
  search.value = '';
  statusFilter.value = 'all';
  farmFilter.value = '';
}
const hasFilters = computed(
  () => !!search.value || statusFilter.value !== 'all' || !!farmFilter.value,
);

// ---- Farm (explotación) creation ----
const showFarm = ref(false);
const savingFarm = ref(false);
const farmForm = ref({ name: '', description: '' });

function openFarm() {
  farmForm.value = { name: '', description: '' };
  showFarm.value = true;
}

async function submitFarm() {
  if (!farmForm.value.name.trim()) {
    toast.error('Indica el nombre de la explotación.');
    return;
  }
  savingFarm.value = true;
  try {
    const created = await api.post<Farm>('/farms/', {
      name: farmForm.value.name.trim(),
      description: farmForm.value.description.trim(),
    });
    toast.success('Explotación creada.');
    showFarm.value = false;
    await refreshFarms();
    // Preselect it if we were creating a parcel.
    if (showCreate.value) form.value.farm = created.id;
  } catch {
    toast.error('No se pudo crear la explotación.');
  } finally {
    savingFarm.value = false;
  }
}

const showCreate = ref(false);
const saving = ref(false);

function openDetail(p: Parcel) {
  navigateTo(`/parcels/${p.id}`);
}

// ---- List / map view ----
const view = ref<'table' | 'map'>('table');
const geoParcels = computed(() =>
  filteredParcels.value.filter(
    (p) =>
      (p.polygon as number[][] | null)?.length || (p.latitude && p.longitude),
  ),
);

// ---- Expandable row ----
const expandedId = ref<string | null>(null);
function toggleExpand(p: Parcel) {
  expandedId.value = expandedId.value === p.id ? null : p.id;
}
function isGeolocated(p: Parcel) {
  return !!(
    (p.polygon as number[][] | null)?.length ||
    (p.latitude && p.longitude)
  );
}

// ---- Focus a parcel on the map ----
const focusedId = ref<string | null>(null);
function viewOnMap(p: Parcel) {
  view.value = 'map';
  // Re-trigger the watcher even if the same parcel is selected again.
  focusedId.value = null;
  nextTick(() => {
    focusedId.value = p.id;
  });
}

const blank = () => ({
  farm: '',
  name: '',
  sigpac_ref: '',
  area_ha: '',
  soil_type: '',
  province: '',
  municipality: '',
  address: '',
  latitude: null as string | null,
  longitude: null as string | null,
  polygon: null as number[][] | null,
});
const form = ref(blank());

function openCreate() {
  form.value = blank();
  showMap.value = false;
  lookupError.value = '';
  zoneInfo.value = null;
  if (farmOptions.value.length === 1)
    form.value.farm = String(farmOptions.value[0].value);
  showCreate.value = true;
}

interface CadastreResult {
  reference: string;
  area_ha: string | null;
  polygon: number[][] | null;
  latitude: string | null;
  longitude: string | null;
  source: string;
  province?: string | null;
  municipality?: string | null;
  address?: string | null;
  paraje?: string | null;
  classification?: string | null;
  uses?: string[] | null;
}

const looking = ref(false);
const lookupError = ref('');
const showMap = ref(false);
const zoneInfo = ref<{
  province?: string | null;
  municipality?: string | null;
  address?: string | null;
  paraje?: string | null;
  classification?: string | null;
  uses?: string[] | null;
} | null>(null);

function applyResult(res: CadastreResult) {
  if (res.area_ha) form.value.area_ha = res.area_ha;
  form.value.latitude = res.latitude;
  form.value.longitude = res.longitude;
  form.value.polygon = res.polygon;
  form.value.sigpac_ref = res.reference;
  form.value.province = res.province ?? '';
  form.value.municipality = res.municipality ?? '';
  form.value.address = res.address ?? '';
  if (!form.value.soil_type && res.classification)
    form.value.soil_type = res.classification;
  zoneInfo.value = {
    province: res.province,
    municipality: res.municipality,
    address: res.address,
    paraje: res.paraje,
    classification: res.classification,
    uses: res.uses,
  };
}

function handleLookupError(status?: number) {
  lookupError.value =
    status === 404
      ? 'No se encontró ninguna parcela catastral.'
      : 'No se pudo consultar el catastro. Inténtalo de nuevo.';
  form.value.polygon = null;
}

async function lookupCadastre() {
  const refValue = form.value.sigpac_ref.trim();
  if (!refValue) {
    lookupError.value = 'Introduce una referencia catastral.';
    return;
  }
  looking.value = true;
  lookupError.value = '';
  try {
    const res = await api.get<CadastreResult>('/parcels/lookup/', {
      ref: refValue,
    });
    applyResult(res);
    toast.success(`Recinto localizado · ${res.area_ha ?? '—'} ha`);
  } catch (err: any) {
    handleLookupError(err?.response?.status);
  } finally {
    looking.value = false;
  }
}

async function pickFromMap(coord: { lat: number; lon: number }) {
  looking.value = true;
  lookupError.value = '';
  try {
    const res = await api.get<CadastreResult>('/parcels/lookup/', {
      lat: coord.lat,
      lon: coord.lon,
    });
    applyResult(res);
    toast.success(`Parcela seleccionada · ${res.area_ha ?? '—'} ha`);
  } catch (err: any) {
    handleLookupError(err?.response?.status);
  } finally {
    looking.value = false;
  }
}

const mapCenter = computed<[number, number] | null>(() => {
  if (form.value.latitude && form.value.longitude)
    return [Number(form.value.latitude), Number(form.value.longitude)];
  return null;
});

// Build an SVG path for the recovered polygon (normalised to a 0–100 box,
// latitude inverted because SVG y grows downwards).
const polygonPath = computed(() => {
  const pts = form.value.polygon;
  if (!pts || pts.length < 3) return '';
  const lons = pts.map((p) => p[0]);
  const lats = pts.map((p) => p[1]);
  const minLon = Math.min(...lons);
  const maxLon = Math.max(...lons);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const w = maxLon - minLon || 1e-6;
  const h = maxLat - minLat || 1e-6;
  const scale = 100 / Math.max(w, h);
  const offX = (100 - w * scale) / 2;
  const offY = (100 - h * scale) / 2;
  const coords = pts.map((p) => {
    const x = offX + (p[0] - minLon) * scale;
    const y = offY + (maxLat - p[1]) * scale; // invert lat
    return `${x.toFixed(2)},${y.toFixed(2)}`;
  });
  return `M${coords.join('L')}Z`;
});

async function submit() {
  if (!form.value.farm || !form.value.name || !form.value.area_ha) {
    toast.error('Completa explotación, nombre y superficie.');
    return;
  }
  saving.value = true;
  try {
    await api.post<Parcel>('/parcels/', { ...form.value });
    toast.success('Parcela creada.');
    showCreate.value = false;
    await refresh();
  } catch {
    toast.error('No se pudo crear la parcela.');
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <div class="p-6 lg:p-8 space-y-6 w-full">
    <PageHeader
      title="Parcelas"
      :subtitle="`${data?.count ?? 0} recintos · ${number(totalArea, 2)} ha totales`"
    >
      <template #actions>
        <button
          class="text-sm px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 transition"
          @click="refresh()"
        >
          Refrescar
        </button>
        <button
          class="text-sm px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 transition"
          @click="openFarm"
        >
          + Nueva explotación
        </button>
        <button
          class="text-sm px-3 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition shadow-glow"
          @click="openCreate"
        >
          + Nueva parcela
        </button>
      </template>
    </PageHeader>

    <!-- KPI summary -->
    <div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-4">
      <StatCard label="Parcelas" :value="kpis.total" tone="brand" />
      <StatCard label="Activas" :value="kpis.active" tone="sky" />
      <StatCard
        label="Superficie"
        :value="kpis.area"
        :decimals="2"
        suffix=" ha"
        tone="violet"
      />
      <StatCard label="Geolocalizadas" :value="kpis.geo" tone="amber" />
      <StatCard label="Explotaciones" :value="kpis.farms" tone="brand" />
    </div>

    <div class="flex items-center justify-between flex-wrap gap-3">
      <UiTabs
        v-model="view"
        :tabs="[
          { value: 'table', label: 'Tabla', count: filteredParcels.length },
          { value: 'map', label: 'Mapa', count: geoParcels.length },
        ]"
      />
      <p v-if="view === 'map'" class="text-xs text-slate-400">
        {{ geoParcels.length }} de {{ data?.count ?? 0 }} parcelas
        geolocalizadas
      </p>
    </div>

    <!-- Search & filters toolbar -->
    <div class="flex items-center flex-wrap gap-2.5">
      <UiSearchInput
        v-model="search"
        placeholder="Buscar parcela, explotación, SIGPAC…"
        class="w-full sm:w-72"
      />
      <UiFilterSelect
        v-model="statusFilter"
        :options="statusFilterOptions"
        icon="M3 4a1 1 0 011-1h16a1 1 0 011 1v2a1 1 0 01-.293.707L14 13.414V19a1 1 0 01-.553.894l-4 2A1 1 0 018 21v-7.586L3.293 6.707A1 1 0 013 6V4z"
        class="w-44"
      />
      <UiFilterSelect
        v-model="farmFilter"
        :options="farmFilterOptions"
        icon="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0H5m14 0h2m-2 0h-3m-9 0H3m2 0h3M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5"
        class="w-52"
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
      <span class="text-xs text-slate-400 ml-auto">
        {{ filteredParcels.length }} resultado{{
          filteredParcels.length === 1 ? '' : 's'
        }}
        · {{ number(filteredArea, 2) }} ha
      </span>
    </div>

    <!-- Map view -->
    <UiCard v-if="view === 'map'" :padded="false">
      <div class="p-5" v-if="pending"><UiSkeleton /></div>
      <ClientOnly v-else-if="geoParcels.length">
        <ParcelsOverviewMap
          :parcels="geoParcels"
          :height="520"
          :focus-id="focusedId"
          @select="openDetail"
        />
        <template #fallback>
          <div class="h-[520px] grid place-items-center bg-slate-50">
            <UiSkeleton />
          </div>
        </template>
      </ClientOnly>
      <EmptyState
        v-else
        title="Sin parcelas geolocalizadas"
        message="Localiza tus parcelas en el catastro o dibújalas para verlas en el mapa."
      >
        <template #action>
          <button
            class="text-sm px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition"
            @click="openCreate"
          >
            + Nueva parcela
          </button>
        </template>
      </EmptyState>
    </UiCard>

    <!-- Table view -->
    <UiCard v-else :padded="false">
      <div class="p-5" v-if="pending"><UiSkeleton /></div>
      <table v-else class="w-full text-sm">
        <thead class="bg-slate-50 text-slate-500 text-left">
          <tr>
            <th class="px-5 py-3 font-medium">
              <button
                class="inline-flex items-center gap-1 hover:text-slate-700 transition"
                @click="toggleSort('name')"
              >
                Nombre
                <span class="text-brand-500 w-2">{{
                  sortIndicator('name')
                }}</span>
              </button>
            </th>
            <th class="px-5 py-3 font-medium">
              <button
                class="inline-flex items-center gap-1 hover:text-slate-700 transition"
                @click="toggleSort('farm_name')"
              >
                Explotación
                <span class="text-brand-500 w-2">{{
                  sortIndicator('farm_name')
                }}</span>
              </button>
            </th>
            <th class="px-5 py-3 font-medium">SIGPAC</th>
            <th class="px-5 py-3 font-medium text-right">
              <button
                class="inline-flex items-center gap-1 hover:text-slate-700 transition"
                @click="toggleSort('area_ha')"
              >
                Superficie (ha)
                <span class="text-brand-500 w-2">{{
                  sortIndicator('area_ha')
                }}</span>
              </button>
            </th>
            <th class="px-5 py-3 font-medium">
              <button
                class="inline-flex items-center gap-1 hover:text-slate-700 transition"
                @click="toggleSort('soil_type')"
              >
                Suelo
                <span class="text-brand-500 w-2">{{
                  sortIndicator('soil_type')
                }}</span>
              </button>
            </th>
            <th class="px-5 py-3 font-medium">Estado</th>
            <th class="px-5 py-3 font-medium w-10"></th>
          </tr>
        </thead>
        <TransitionGroup
          tag="tbody"
          name="list"
          class="divide-y divide-slate-100"
        >
          <template v-for="p in filteredParcels" :key="p.id">
            <tr
              class="hover:bg-brand-50/50 transition cursor-pointer group"
              :class="expandedId === p.id ? 'bg-brand-50/40' : ''"
              @click="openDetail(p)"
            >
              <td class="px-5 py-3 font-medium text-slate-700">
                <span class="inline-flex items-center gap-2">
                  {{ p.name }}
                  <svg
                    class="w-4 h-4 text-slate-300 group-hover:text-brand-500 transition"
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
                </span>
                <p
                  v-if="p.municipality || p.province"
                  class="text-xs font-normal text-slate-400 mt-0.5 flex items-center gap-1"
                >
                  <svg
                    class="w-3 h-3 shrink-0"
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
                  {{ [p.municipality, p.province].filter(Boolean).join(', ') }}
                </p>
              </td>
              <td class="px-5 py-3 text-slate-500">{{ p.farm_name }}</td>
              <td class="px-5 py-3 font-mono text-xs text-slate-400">
                {{ p.sigpac_ref || '—' }}
              </td>
              <td class="px-5 py-3 text-right">{{ number(p.area_ha, 2) }}</td>
              <td class="px-5 py-3 text-slate-500">{{ p.soil_type || '—' }}</td>
              <td class="px-5 py-3">
                <UiBadge :tone="p.is_active ? 'green' : 'slate'" dot>
                  {{ p.is_active ? 'Activa' : 'Inactiva' }}
                </UiBadge>
              </td>
              <td class="px-3 py-3 text-right">
                <button
                  type="button"
                  class="p-1.5 rounded-lg text-slate-400 hover:bg-brand-100 hover:text-brand-600 transition"
                  :title="
                    expandedId === p.id
                      ? 'Ocultar detalles'
                      : 'Ver más detalles'
                  "
                  @click.stop="toggleExpand(p)"
                >
                  <svg
                    class="w-4 h-4 transition-transform"
                    :class="expandedId === p.id ? 'rotate-180' : ''"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </button>
              </td>
            </tr>
            <tr
              v-if="expandedId === p.id"
              :key="`${p.id}-exp`"
              class="bg-slate-50/70"
            >
              <td colspan="7" class="px-5 py-4">
                <div class="grid sm:grid-cols-2 xl:grid-cols-4 gap-4">
                  <div>
                    <p
                      class="text-[11px] uppercase tracking-wide text-slate-400 mb-0.5"
                    >
                      Ubicación catastral
                    </p>
                    <p class="text-sm text-slate-700">{{ p.address || '—' }}</p>
                  </div>
                  <div>
                    <p
                      class="text-[11px] uppercase tracking-wide text-slate-400 mb-0.5"
                    >
                      Municipio · Provincia
                    </p>
                    <p class="text-sm text-slate-700">
                      {{
                        [p.municipality, p.province]
                          .filter(Boolean)
                          .join(' · ') || '—'
                      }}
                    </p>
                  </div>
                  <div>
                    <p
                      class="text-[11px] uppercase tracking-wide text-slate-400 mb-0.5"
                    >
                      Coordenadas
                    </p>
                    <p class="text-sm font-mono text-slate-700">
                      {{
                        p.latitude && p.longitude
                          ? `${Number(p.latitude).toFixed(5)}, ${Number(
                              p.longitude,
                            ).toFixed(5)}`
                          : '—'
                      }}
                    </p>
                  </div>
                  <div>
                    <p
                      class="text-[11px] uppercase tracking-wide text-slate-400 mb-0.5"
                    >
                      Geolocalización · Alta
                    </p>
                    <p class="text-sm text-slate-700 flex items-center gap-2">
                      <UiBadge :tone="isGeolocated(p) ? 'green' : 'amber'" dot>
                        {{
                          isGeolocated(p) ? 'Geolocalizada' : 'Sin localizar'
                        }}
                      </UiBadge>
                      <span class="text-slate-400">{{
                        date(p.created_at)
                      }}</span>
                    </p>
                  </div>
                </div>
                <div class="flex items-center gap-2 mt-4">
                  <button
                    type="button"
                    class="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition"
                    @click.stop="openDetail(p)"
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
                        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                      />
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                      />
                    </svg>
                    Ver detalle
                  </button>
                  <button
                    v-if="isGeolocated(p)"
                    type="button"
                    class="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 transition"
                    @click.stop="viewOnMap(p)"
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
                        d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
                      />
                    </svg>
                    Ver en el mapa
                  </button>
                </div>
              </td>
            </tr>
          </template>
        </TransitionGroup>
      </table>
      <EmptyState
        v-if="!pending && !filteredParcels.length && hasFilters"
        title="Sin coincidencias"
        message="Ninguna parcela coincide con los filtros aplicados."
      >
        <template #action>
          <button
            class="text-sm px-4 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 transition"
            @click="resetFilters"
          >
            Limpiar filtros
          </button>
        </template>
      </EmptyState>
      <EmptyState
        v-else-if="!pending && !data?.results?.length"
        title="Sin parcelas"
        message="Aún no se han registrado recintos."
      >
        <template #action>
          <button
            class="text-sm px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition"
            @click="openCreate"
          >
            + Nueva parcela
          </button>
        </template>
      </EmptyState>
    </UiCard>

    <UiModal v-model="showCreate" title="Nueva parcela">
      <div class="space-y-4">
        <UiField label="Explotación" required>
          <div v-if="farmOptions.length" class="flex items-center gap-2">
            <UiSelect
              v-model="form.farm"
              :options="farmOptions"
              placeholder="Selecciona una explotación"
              class="flex-1"
            />
            <button
              type="button"
              class="shrink-0 px-3 py-2 rounded-lg bg-brand-50 text-brand-700 ring-1 ring-brand-200 hover:bg-brand-100 transition text-sm font-medium"
              title="Crear nueva explotación"
              @click="openFarm"
            >
              + Nueva
            </button>
          </div>
          <div
            v-else
            class="rounded-lg bg-amber-50 ring-1 ring-amber-200 p-3 text-sm text-amber-800 flex items-center justify-between gap-3"
          >
            <span>Aún no tienes explotaciones.</span>
            <button
              type="button"
              class="shrink-0 px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition text-sm font-medium"
              @click="openFarm"
            >
              + Crear explotación
            </button>
          </div>
        </UiField>
        <UiField label="Nombre" required>
          <UiInput v-model="form.name" placeholder="Ej. La Vega" />
        </UiField>
        <div class="grid grid-cols-2 gap-4">
          <UiField label="Superficie (ha)" required>
            <UiInput
              v-model="form.area_ha"
              type="number"
              step="0.0001"
              placeholder="0,00"
            />
          </UiField>
          <UiField label="Referencia catastral / SIGPAC">
            <div class="flex gap-2">
              <UiInput
                v-model="form.sigpac_ref"
                placeholder="Ej. 13077A018000090000FP"
                class="flex-1"
                @keydown.enter.prevent="lookupCadastre"
              />
              <button
                type="button"
                class="shrink-0 px-3 rounded-lg bg-brand-50 text-brand-700 ring-1 ring-brand-200 hover:bg-brand-100 transition disabled:opacity-50 text-sm font-medium inline-flex items-center gap-1.5"
                :disabled="looking"
                title="Buscar geometría en el Catastro"
                @click="lookupCadastre"
              >
                <svg
                  v-if="!looking"
                  class="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M21 21l-4.35-4.35M11 18a7 7 0 100-14 7 7 0 000 14z"
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
                Buscar
              </button>
            </div>
            <p v-if="lookupError" class="mt-1 text-xs text-red-500">
              {{ lookupError }}
            </p>
            <p v-else class="mt-1 text-xs text-slate-400">
              Autocompleta superficie, geometría y datos de la zona desde el
              Catastro.
            </p>
          </UiField>
        </div>

        <!-- Recovered zone info -->
        <Transition name="fade-pop">
          <div
            v-if="
              zoneInfo &&
              (zoneInfo.province ||
                zoneInfo.municipality ||
                zoneInfo.address ||
                zoneInfo.uses?.length)
            "
            class="rounded-xl border border-brand-100 bg-brand-50/50 p-4"
          >
            <div class="flex items-center gap-2 mb-3">
              <svg
                class="w-4 h-4 text-brand-600"
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
              <h4 class="text-sm font-semibold text-slate-700">
                Información de la zona
              </h4>
              <UiBadge
                v-if="zoneInfo.classification"
                :tone="zoneInfo.classification === 'Rústico' ? 'green' : 'sky'"
              >
                {{ zoneInfo.classification }}
              </UiBadge>
            </div>
            <dl class="grid sm:grid-cols-2 gap-x-6 gap-y-2 text-sm">
              <div v-if="zoneInfo.province" class="flex justify-between gap-3">
                <dt class="text-slate-400">Provincia</dt>
                <dd class="font-medium text-slate-700 text-right">
                  {{ zoneInfo.province }}
                </dd>
              </div>
              <div
                v-if="zoneInfo.municipality"
                class="flex justify-between gap-3"
              >
                <dt class="text-slate-400">Municipio</dt>
                <dd class="font-medium text-slate-700 text-right">
                  {{ zoneInfo.municipality }}
                </dd>
              </div>
              <div v-if="zoneInfo.paraje" class="flex justify-between gap-3">
                <dt class="text-slate-400">Paraje</dt>
                <dd class="font-medium text-slate-700 text-right">
                  {{ zoneInfo.paraje }}
                </dd>
              </div>
              <div
                v-if="zoneInfo.address"
                class="flex justify-between gap-3 sm:col-span-2"
              >
                <dt class="text-slate-400 shrink-0">Ubicación</dt>
                <dd class="font-medium text-slate-700 text-right">
                  {{ zoneInfo.address }}
                </dd>
              </div>
            </dl>
            <div
              v-if="zoneInfo.uses?.length"
              class="mt-3 pt-3 border-t border-brand-100"
            >
              <p class="text-xs text-slate-400 mb-1.5">Usos / cultivos</p>
              <div class="flex flex-wrap gap-1.5">
                <UiBadge v-for="u in zoneInfo.uses" :key="u" tone="slate">
                  {{ u }}
                </UiBadge>
              </div>
            </div>
          </div>
        </Transition>

        <!-- Map toggle -->
        <button
          type="button"
          class="inline-flex items-center gap-1.5 text-sm font-medium text-brand-700 hover:text-brand-800 transition"
          @click="showMap = !showMap"
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
              d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
            />
          </svg>
          {{ showMap ? 'Ocultar mapa' : 'Seleccionar en el mapa' }}
        </button>

        <Transition name="fade-pop">
          <ClientOnly v-if="showMap">
            <ParcelMap
              :polygon="form.polygon"
              :center="mapCenter"
              :loading="looking"
              @pick="pickFromMap"
            />
          </ClientOnly>
        </Transition>

        <!-- Recovered geometry preview -->
        <Transition name="fade-pop">
          <div
            v-if="polygonPath"
            class="flex items-center gap-4 rounded-xl bg-slate-50 ring-1 ring-slate-100 p-3"
          >
            <svg
              viewBox="0 0 100 100"
              class="w-24 h-24 shrink-0"
              aria-label="Geometría de la parcela"
            >
              <defs>
                <linearGradient id="parcelFill" x1="0" y1="0" x2="0" y2="1">
                  <stop
                    offset="0%"
                    stop-color="rgb(var(--brand-400))"
                    stop-opacity="0.45"
                  />
                  <stop
                    offset="100%"
                    stop-color="rgb(var(--brand-600))"
                    stop-opacity="0.25"
                  />
                </linearGradient>
              </defs>
              <path
                :d="polygonPath"
                fill="url(#parcelFill)"
                stroke="rgb(var(--brand-600))"
                stroke-width="1.5"
                stroke-linejoin="round"
                class="parcel-draw"
              />
            </svg>
            <div class="min-w-0 text-sm">
              <p class="font-medium text-slate-700 flex items-center gap-1.5">
                <UiBadge tone="green" dot>Recinto verificado</UiBadge>
              </p>
              <p class="mt-1 text-slate-500">
                Superficie oficial:
                <span class="font-semibold text-slate-700"
                  >{{ number(Number(form.area_ha), 4) }} ha</span
                >
              </p>
              <p
                v-if="form.latitude && form.longitude"
                class="text-xs text-slate-400 font-mono mt-0.5"
              >
                {{ Number(form.latitude).toFixed(5) }},
                {{ Number(form.longitude).toFixed(5) }}
              </p>
            </div>
          </div>
        </Transition>

        <UiField label="Tipo de suelo">
          <UiInput v-model="form.soil_type" placeholder="Opcional" />
        </UiField>
      </div>
      <template #footer>
        <button
          class="text-sm px-4 py-2 rounded-lg border border-slate-200 hover:bg-slate-50 transition"
          @click="showCreate = false"
        >
          Cancelar
        </button>
        <button
          class="text-sm px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition disabled:opacity-50"
          :disabled="saving"
          @click="submit"
        >
          {{ saving ? 'Guardando…' : 'Crear parcela' }}
        </button>
      </template>
    </UiModal>

    <!-- New farm (explotación) -->
    <UiModal v-model="showFarm" title="Nueva explotación">
      <div class="space-y-4">
        <p class="text-sm text-slate-500">
          Una explotación agrupa las parcelas de un titular dentro de tu
          cooperativa. Quedará a tu nombre como responsable.
        </p>
        <UiField label="Nombre" required>
          <UiInput
            v-model="farmForm.name"
            placeholder="Ej. Explotación La Vega"
            @keydown.enter.prevent="submitFarm"
          />
        </UiField>
        <UiField label="Descripción">
          <UiTextarea
            v-model="farmForm.description"
            placeholder="Notas opcionales sobre la explotación"
            :rows="3"
          />
        </UiField>
      </div>
      <template #footer>
        <button
          class="text-sm px-4 py-2 rounded-lg border border-slate-200 hover:bg-slate-50 transition"
          @click="showFarm = false"
        >
          Cancelar
        </button>
        <button
          class="text-sm px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition disabled:opacity-50"
          :disabled="savingFarm"
          @click="submitFarm"
        >
          {{ savingFarm ? 'Guardando…' : 'Crear explotación' }}
        </button>
      </template>
    </UiModal>
  </div>
</template>

<style scoped>
.parcel-draw {
  stroke-dasharray: 400;
  stroke-dashoffset: 400;
  animation: parcel-draw 1.1s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
@keyframes parcel-draw {
  to {
    stroke-dashoffset: 0;
  }
}

.fade-pop-enter-active {
  transition:
    opacity 0.35s ease,
    transform 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}
.fade-pop-enter-from {
  opacity: 0;
  transform: translateY(6px) scale(0.98);
}
.fade-pop-leave-active {
  transition: opacity 0.2s ease;
}
.fade-pop-leave-to {
  opacity: 0;
}

@media (prefers-reduced-motion: reduce) {
  .parcel-draw {
    animation: none;
    stroke-dashoffset: 0;
  }
}
</style>
