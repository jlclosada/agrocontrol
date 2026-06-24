<script setup lang="ts">
import type { Farm, Paginated, Parcel } from '~/types/api';

const api = useApi();
const toast = useToast();
const { number } = useFormat();
const { data, pending, refresh } = await useAsyncData('parcels-page', () =>
  api.get<Paginated<Parcel>>('/parcels/'),
);
const { data: farms } = await useAsyncData('parcels-farms', () =>
  api.get<Paginated<Farm>>('/farms/'),
);

const totalArea = computed(() =>
  (data.value?.results ?? []).reduce((s, p) => s + Number(p.area_ha), 0),
);

const farmOptions = computed(() =>
  (farms.value?.results ?? []).map((f) => ({ value: f.id, label: f.name })),
);

const showCreate = ref(false);
const saving = ref(false);

const showDetail = ref(false);
const detailParcel = ref<Parcel | null>(null);
function openDetail(p: Parcel) {
  detailParcel.value = p;
  showDetail.value = true;
}

const blank = () => ({
  farm: '',
  name: '',
  sigpac_ref: '',
  area_ha: '',
  soil_type: '',
  latitude: null as string | null,
  longitude: null as string | null,
  polygon: null as number[][] | null,
});
const form = ref(blank());

function openCreate() {
  form.value = blank();
  showMap.value = false;
  lookupError.value = '';
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
}

const looking = ref(false);
const lookupError = ref('');
const showMap = ref(false);

function applyResult(res: CadastreResult) {
  if (res.area_ha) form.value.area_ha = res.area_ha;
  form.value.latitude = res.latitude;
  form.value.longitude = res.longitude;
  form.value.polygon = res.polygon;
  form.value.sigpac_ref = res.reference;
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
  <div class="p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
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
          class="text-sm px-3 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition shadow-glow"
          @click="openCreate"
        >
          + Nueva parcela
        </button>
      </template>
    </PageHeader>

    <UiCard :padded="false">
      <div class="p-5" v-if="pending"><UiSkeleton /></div>
      <table v-else class="w-full text-sm">
        <thead class="bg-slate-50 text-slate-500 text-left">
          <tr>
            <th class="px-5 py-3 font-medium">Nombre</th>
            <th class="px-5 py-3 font-medium">Explotación</th>
            <th class="px-5 py-3 font-medium">SIGPAC</th>
            <th class="px-5 py-3 font-medium text-right">Superficie (ha)</th>
            <th class="px-5 py-3 font-medium">Suelo</th>
            <th class="px-5 py-3 font-medium">Estado</th>
          </tr>
        </thead>
        <TransitionGroup
          tag="tbody"
          name="list"
          class="divide-y divide-slate-100"
        >
          <tr
            v-for="p in data?.results"
            :key="p.id"
            class="hover:bg-brand-50/50 transition cursor-pointer group"
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
          </tr>
        </TransitionGroup>
      </table>
      <EmptyState
        v-if="!pending && !data?.results?.length"
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
          <UiSelect
            v-model="form.farm"
            :options="farmOptions"
            placeholder="Selecciona una explotación"
          />
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
              Autocompleta superficie y geometría desde datos públicos.
            </p>
          </UiField>
        </div>

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

    <ParcelDetail v-model="showDetail" :parcel="detailParcel" />
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
