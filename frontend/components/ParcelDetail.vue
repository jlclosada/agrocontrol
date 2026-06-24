<script setup lang="ts">
import type { Crop, Paginated, Parcel, Sector } from '~/types/api';

const props = defineProps<{ modelValue: boolean; parcel: Parcel | null }>();
const emit = defineEmits<{ 'update:modelValue': [boolean] }>();

const api = useApi();
const toast = useToast();
const { number, date } = useFormat();

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

const STATUS_META: Record<string, { label: string; tone: string }> = {
  PLANNED: { label: 'Planificado', tone: 'sky' },
  GROWING: { label: 'En crecimiento', tone: 'green' },
  HARVESTED: { label: 'Cosechado', tone: 'violet' },
  FAILED: { label: 'Fallido', tone: 'red' },
};

const tab = ref<'zones' | 'crops' | 'data'>('zones');
const loading = ref(false);
const sectors = ref<Sector[]>([]);
const crops = ref<Crop[]>([]);

const mapRef = ref<any>(null);

function close() {
  emit('update:modelValue', false);
}

const parcelPolygon = computed<number[][] | null>(
  () => (props.parcel?.polygon as number[][] | null) ?? null,
);
const parcelCenter = computed<[number, number] | null>(() => {
  const p = props.parcel;
  if (p?.latitude && p?.longitude)
    return [Number(p.latitude), Number(p.longitude)];
  return null;
});

// ---- Digitizing state ----
const digitizing = ref(false);
const drawArea = ref(0);
const pending = ref<{ points: number[][]; areaHa: number } | null>(null);
const zoneForm = ref({ name: '', color: ZONE_COLORS[0] });
const savingZone = ref(false);

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

const cropsBySector = computed(() => {
  const map: Record<string, Crop[]> = { _none: [] };
  for (const s of sectors.value) map[s.id] = [];
  for (const c of crops.value) {
    const key = c.sector && map[c.sector] ? c.sector : '_none';
    map[key].push(c);
  }
  return map;
});

async function load() {
  if (!props.parcel) return;
  loading.value = true;
  try {
    const [sec, cr] = await Promise.all([
      api.get<Paginated<Sector>>('/sectors/', { parcel: props.parcel.id }),
      api.get<Paginated<Crop>>('/crops/', { parcel: props.parcel.id }),
    ]);
    sectors.value = sec.results ?? [];
    crops.value = cr.results ?? [];
  } catch {
    toast.error('No se pudo cargar el detalle de la parcela.');
  } finally {
    loading.value = false;
  }
}

watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      tab.value = 'zones';
      resetDigitizing();
      load();
    }
  },
);

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
  if (!props.parcel || !pending.value) return;
  if (!zoneForm.value.name.trim()) {
    toast.error('Ponle un nombre a la zona.');
    return;
  }
  savingZone.value = true;
  try {
    await api.post<Sector>('/sectors/', {
      parcel: props.parcel.id,
      name: zoneForm.value.name.trim(),
      area_ha: pending.value.areaHa.toFixed(4),
      color: zoneForm.value.color,
      polygon: pending.value.points,
    });
    toast.success('Zona digitalizada.');
    pending.value = null;
    drawArea.value = 0;
    await load();
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
    await load();
  } catch {
    toast.error('No se pudo eliminar la zona.');
  }
}

// ---- Crop creation ----
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
  if (!props.parcel) return;
  if (!cropForm.value.species.trim() || !cropForm.value.campaign.trim()) {
    toast.error('Indica al menos especie y campaña.');
    return;
  }
  savingCrop.value = true;
  try {
    const payload: Record<string, unknown> = {
      parcel: props.parcel.id,
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
    await load();
  } catch {
    toast.error('No se pudo añadir el cultivo.');
  } finally {
    savingCrop.value = false;
  }
}

const digitizedArea = computed(() =>
  sectors.value.reduce((s, z) => s + Number(z.area_ha || 0), 0),
);
</script>

<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div
        v-if="modelValue && parcel"
        class="fixed inset-0 z-50 flex justify-end"
      >
        <div
          class="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
          @click="close"
        />
        <div
          class="drawer-panel relative h-full w-full max-w-2xl bg-slate-50 shadow-2xl flex flex-col"
        >
          <!-- Header -->
          <div
            class="px-6 py-4 bg-white border-b border-slate-100 flex items-start justify-between gap-3"
          >
            <div class="min-w-0">
              <p class="text-xs font-medium text-brand-600">
                {{ parcel.farm_name }}
              </p>
              <h2 class="text-lg font-bold text-slate-800 truncate">
                {{ parcel.name }}
              </h2>
              <div class="mt-1 flex flex-wrap items-center gap-2 text-xs">
                <UiBadge :tone="parcel.is_active ? 'green' : 'slate'" dot>
                  {{ parcel.is_active ? 'Activa' : 'Inactiva' }}
                </UiBadge>
                <span class="text-slate-400"
                  >{{ number(Number(parcel.area_ha), 2) }} ha</span
                >
                <span v-if="parcel.sigpac_ref" class="text-slate-400 font-mono">
                  · {{ parcel.sigpac_ref }}
                </span>
              </div>
            </div>
            <button
              class="shrink-0 text-slate-400 hover:text-slate-700 transition rounded-lg p-1"
              @click="close"
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
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          <div class="flex-1 overflow-auto p-6 space-y-5">
            <!-- Map -->
            <div class="relative">
              <ClientOnly>
                <ParcelMap
                  ref="mapRef"
                  :polygon="parcelPolygon"
                  :sub-polygons="subPolygons"
                  :center="parcelCenter"
                  :mode="digitizing ? 'draw' : 'view'"
                  :height="300"
                  @draw-progress="onDrawProgress"
                  @draw-complete="onDrawComplete"
                />
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

            <!-- Pending zone save form -->
            <div
              v-if="pending"
              class="rounded-xl bg-amber-50 ring-1 ring-amber-200 p-4 space-y-3"
            >
              <p class="text-sm font-medium text-amber-800">
                Nueva zona · ≈ {{ number(pending.areaHa, 4) }} ha
              </p>
              <div class="flex items-end gap-3">
                <div class="flex-1">
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

            <!-- Tabs -->
            <div class="flex items-center justify-between">
              <UiTabs
                v-model="tab"
                :tabs="[
                  { value: 'zones', label: 'Zonas', count: sectors.length },
                  { value: 'crops', label: 'Cultivos', count: crops.length },
                  { value: 'data', label: 'Datos' },
                ]"
              />
              <button
                v-if="tab === 'zones' && !digitizing && !pending"
                class="text-sm px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition shadow-glow inline-flex items-center gap-1.5"
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
                v-else-if="tab === 'crops'"
                class="text-sm px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition shadow-glow"
                @click="openCropForm()"
              >
                + Añadir cultivo
              </button>
            </div>

            <div v-if="loading" class="py-8"><UiSkeleton /></div>

            <!-- Zones tab -->
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
                  <p class="font-medium text-slate-700 truncate">
                    {{ s.name }}
                  </p>
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

            <!-- Crops tab -->
            <div v-else-if="tab === 'crops'" class="space-y-2">
              <div
                v-for="c in crops"
                :key="c.id"
                class="bg-white rounded-xl ring-1 ring-slate-100 p-3 flex items-center gap-3"
              >
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
                      ·
                      {{ sectors.find((s) => s.id === c.sector)?.name }}
                    </span>
                    <span v-if="c.sowing_date">
                      · siembra {{ date(c.sowing_date) }}</span
                    >
                  </p>
                </div>
                <UiBadge
                  :tone="(STATUS_META[c.status]?.tone as any) || 'slate'"
                >
                  {{ STATUS_META[c.status]?.label || c.status }}
                </UiBadge>
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

            <!-- Data tab -->
            <div
              v-else
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
                <span class="text-slate-700">{{
                  parcel.soil_type || '—'
                }}</span>
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
                <span class="text-slate-400">Alta</span>
                <span class="text-slate-700">{{
                  date(parcel.created_at)
                }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>

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
  </Teleport>
</template>

<style scoped>
.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.3s ease;
}
.drawer-enter-active .drawer-panel,
.drawer-leave-active .drawer-panel {
  transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}
.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}
.drawer-enter-from .drawer-panel,
.drawer-leave-to .drawer-panel {
  transform: translateX(100%);
}
</style>
