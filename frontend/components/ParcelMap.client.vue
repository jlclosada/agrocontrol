<script setup lang="ts">
import L from 'leaflet';

interface SubPolygon {
  id: string;
  name: string;
  color?: string;
  points: number[][]; // [lon, lat]
}

const props = withDefaults(
  defineProps<{
    polygon?: number[][] | null; // parcel boundary [lon, lat]
    subPolygons?: SubPolygon[];
    center?: [number, number] | null;
    loading?: boolean;
    mode?: 'pick' | 'draw' | 'view';
    height?: number;
  }>(),
  { mode: 'pick', height: 320, subPolygons: () => [] },
);

const emit = defineEmits<{
  pick: [{ lat: number; lon: number }];
  'draw-progress': [{ points: number[][]; areaHa: number }];
  'draw-complete': [{ points: number[][]; areaHa: number }];
}>();

const el = ref<HTMLElement | null>(null);
let map: L.Map | null = null;
let polyLayer: L.Polygon | null = null;
let zonesLayer: L.LayerGroup | null = null;

// Drawing state
let drawPts: L.LatLng[] = [];
let drawLine: L.Polyline | null = null;
let drawMarkers: L.CircleMarker[] = [];

const SPAIN_CENTER: [number, number] = [40.0, -3.7];

function brandColor(): string {
  if (!import.meta.client) return '#16a34a';
  const v = getComputedStyle(document.documentElement)
    .getPropertyValue('--brand-600')
    .trim();
  return v ? `rgb(${v})` : '#16a34a';
}

/** Spherical polygon area in hectares for a ring of [lon, lat] points. */
function ringAreaHa(lonlat: number[][]): number {
  if (lonlat.length < 3) return 0;
  const R = 6378137;
  const toRad = (d: number) => (d * Math.PI) / 180;
  let total = 0;
  const n = lonlat.length;
  for (let i = 0; i < n; i++) {
    const [lon1, lat1] = lonlat[i];
    const [lon2, lat2] = lonlat[(i + 1) % n];
    total +=
      toRad(lon2 - lon1) * (2 + Math.sin(toRad(lat1)) + Math.sin(toRad(lat2)));
  }
  return Math.abs((total * R * R) / 2) / 10000;
}

function drawPolygon(points: number[][]) {
  if (!map) return;
  if (polyLayer) {
    map.removeLayer(polyLayer);
    polyLayer = null;
  }
  if (!points?.length) return;
  // Service/store keep [lon, lat]; Leaflet wants [lat, lon].
  const latlngs = points.map((p) => [p[1], p[0]] as [number, number]);
  const color = brandColor();
  polyLayer = L.polygon(latlngs, {
    color,
    weight: 2.5,
    fillColor: color,
    fillOpacity: props.subPolygons.length ? 0.04 : 0.18,
    dashArray: props.subPolygons.length ? '5,5' : undefined,
  }).addTo(map);
  map.fitBounds(polyLayer.getBounds(), { padding: [24, 24], maxZoom: 18 });
}

function renderZones() {
  if (!map) return;
  if (!zonesLayer) zonesLayer = L.layerGroup().addTo(map);
  zonesLayer.clearLayers();
  for (const z of props.subPolygons) {
    if (!z.points?.length) continue;
    const latlngs = z.points.map((p) => [p[1], p[0]] as [number, number]);
    const color = z.color || brandColor();
    const poly = L.polygon(latlngs, {
      color,
      weight: 2,
      fillColor: color,
      fillOpacity: 0.35,
    });
    poly.bindTooltip(z.name, {
      permanent: true,
      direction: 'center',
      className: 'zone-label',
    });
    zonesLayer.addLayer(poly);
  }
}

// ---- Drawing API (exposed to parent) ----
function clearDrawingLayers() {
  if (!map) return;
  if (drawLine) {
    map.removeLayer(drawLine);
    drawLine = null;
  }
  drawMarkers.forEach((m) => map?.removeLayer(m));
  drawMarkers = [];
}

function redrawDrawing() {
  if (!map) return;
  const latlngs = drawPts;
  if (drawLine) map.removeLayer(drawLine);
  drawLine = L.polyline(
    [...latlngs, ...(latlngs.length > 2 ? [latlngs[0]] : [])],
    { color: '#f59e0b', weight: 2.5, dashArray: '6,4' },
  ).addTo(map);
  drawMarkers.forEach((m) => map?.removeLayer(m));
  drawMarkers = latlngs.map((ll, i) =>
    L.circleMarker(ll, {
      radius: 5,
      color: '#f59e0b',
      fillColor: '#fff',
      fillOpacity: 1,
      weight: 2,
    })
      .addTo(map!)
      .on('click', () => {
        if (i === 0 && drawPts.length >= 3) finishDraw();
      }),
  );
  emitProgress();
}

function currentLonLat(): number[][] {
  return drawPts.map((ll) => [ll.lng, ll.lat]);
}

function emitProgress() {
  const pts = currentLonLat();
  emit('draw-progress', { points: pts, areaHa: ringAreaHa(pts) });
}

function startDraw() {
  drawPts = [];
  clearDrawingLayers();
  emitProgress();
}

function undoPoint() {
  drawPts.pop();
  redrawDrawing();
}

function finishDraw() {
  const pts = currentLonLat();
  if (pts.length < 3) return;
  emit('draw-complete', { points: pts, areaHa: ringAreaHa(pts) });
  drawPts = [];
  clearDrawingLayers();
}

function cancelDraw() {
  drawPts = [];
  clearDrawingLayers();
  emitProgress();
}

defineExpose({ startDraw, finishDraw, cancelDraw, undoPoint });

onMounted(() => {
  if (!el.value) return;
  map = L.map(el.value, { zoomControl: true }).setView(
    props.center ?? SPAIN_CENTER,
    props.center ? 16 : 6,
  );

  const sat = L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    { maxZoom: 19, attribution: 'Esri, Maxar — World Imagery' },
  ).addTo(map);

  const catastro = L.tileLayer
    .wms('https://ovc.catastro.meh.es/Cartografia/WMS/ServidorWMS.aspx', {
      layers: 'Catastro',
      format: 'image/png',
      transparent: true,
      opacity: 0.6,
      attribution: 'Dirección General del Catastro',
    })
    .addTo(map);

  L.control
    .layers(
      { Satélite: sat },
      { 'Parcelas catastrales': catastro },
      { collapsed: true },
    )
    .addTo(map);

  map.on('click', (e: L.LeafletMouseEvent) => {
    if (props.mode === 'draw') {
      drawPts.push(e.latlng);
      redrawDrawing();
    } else if (props.mode === 'pick') {
      emit('pick', { lat: e.latlng.lat, lon: e.latlng.lng });
    }
  });
  map.on('dblclick', () => {
    if (props.mode === 'draw' && drawPts.length >= 3) finishDraw();
  });
  if (props.mode === 'draw') map.doubleClickZoom.disable();

  if (props.polygon?.length) drawPolygon(props.polygon);
  if (props.subPolygons.length) renderZones();
  // Fix sizing when mounted inside a freshly-opened modal/drawer.
  nextTick(() => map?.invalidateSize());
  setTimeout(() => map?.invalidateSize(), 250);
});

watch(
  () => props.polygon,
  (p) => p?.length && drawPolygon(p),
  { deep: true },
);
watch(
  () => props.subPolygons,
  () => renderZones(),
  { deep: true },
);
watch(
  () => props.mode,
  (m) => {
    if (!map) return;
    if (m === 'draw') map.doubleClickZoom.disable();
    else {
      map.doubleClickZoom.enable();
      cancelDraw();
    }
  },
);

onUnmounted(() => {
  map?.remove();
  map = null;
  polyLayer = null;
  zonesLayer = null;
});
</script>

<template>
  <div class="relative">
    <div ref="el" class="parcel-map" :style="{ height: `${height}px` }" />
    <div
      v-if="loading"
      class="absolute inset-0 z-[500] grid place-items-center bg-white/40 backdrop-blur-[1px] rounded-xl"
    >
      <span
        class="inline-flex items-center gap-2 text-sm font-medium text-brand-700 bg-white/90 px-3 py-1.5 rounded-full shadow ring-1 ring-slate-100"
      >
        <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
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
        Consultando catastro…
      </span>
    </div>
    <p
      v-if="mode === 'pick'"
      class="absolute bottom-2 left-2 z-[500] text-[11px] text-white/90 bg-slate-900/55 px-2 py-1 rounded-md pointer-events-none"
    >
      Haz clic en una parcela para seleccionarla
    </p>
    <p
      v-else-if="mode === 'draw'"
      class="absolute bottom-2 left-2 z-[500] text-[11px] text-white/90 bg-amber-600/85 px-2 py-1 rounded-md pointer-events-none"
    >
      Clic para añadir vértices · doble clic o clic en el primer punto para
      cerrar
    </p>
  </div>
</template>

<style scoped>
.parcel-map {
  width: 100%;
  border-radius: 0.75rem;
  overflow: hidden;
  z-index: 0;
}
:deep(.zone-label) {
  background: transparent;
  border: none;
  box-shadow: none;
  color: #fff;
  font-weight: 600;
  font-size: 11px;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.7);
}
</style>
