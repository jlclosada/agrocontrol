<script setup lang="ts">
import L from 'leaflet';
import type { Parcel } from '~/types/api';

const props = withDefaults(
  defineProps<{
    parcels: Parcel[];
    height?: number;
    focusId?: string | null;
  }>(),
  { height: 420, focusId: null },
);

const emit = defineEmits<{ select: [Parcel] }>();

const el = ref<HTMLElement | null>(null);
let map: L.Map | null = null;
let featureLayer: L.LayerGroup | null = null;
const layersById = new Map<string, L.Path>();
const boundsById = new Map<string, L.LatLngBounds>();

const SPAIN_CENTER: [number, number] = [40.0, -3.7];

function brandColor(): string {
  if (!import.meta.client) return '#16a34a';
  const v = getComputedStyle(document.documentElement)
    .getPropertyValue('--brand-600')
    .trim();
  return v ? `rgb(${v})` : '#16a34a';
}

function render() {
  if (!map) return;
  if (!featureLayer) featureLayer = L.layerGroup().addTo(map);
  featureLayer.clearLayers();
  layersById.clear();
  boundsById.clear();

  const bounds = L.latLngBounds([]);
  const color = brandColor();

  for (const p of props.parcels) {
    const active = p.is_active;
    const stroke = active ? color : '#94a3b8';
    const poly = (p.polygon as number[][] | null) ?? null;

    if (poly?.length) {
      // Stored as [lon, lat]; Leaflet wants [lat, lon].
      const latlngs = poly.map((pt) => [pt[1], pt[0]] as [number, number]);
      const shape = L.polygon(latlngs, {
        color: stroke,
        weight: 2,
        fillColor: stroke,
        fillOpacity: active ? 0.25 : 0.12,
      });
      bindParcel(shape, p);
      featureLayer.addLayer(shape);
      shape.getLatLngs() && bounds.extend(shape.getBounds());
      layersById.set(p.id, shape);
      boundsById.set(p.id, shape.getBounds());
    } else if (p.latitude && p.longitude) {
      const ll: [number, number] = [Number(p.latitude), Number(p.longitude)];
      const marker = L.circleMarker(ll, {
        radius: 8,
        color: stroke,
        fillColor: stroke,
        fillOpacity: active ? 0.8 : 0.4,
        weight: 2,
      });
      bindParcel(marker, p);
      featureLayer.addLayer(marker);
      bounds.extend(ll);
      layersById.set(p.id, marker);
      boundsById.set(p.id, L.latLngBounds([ll, ll]));
    }
  }

  if (props.focusId && boundsById.has(props.focusId)) {
    focusParcel(props.focusId);
  } else if (bounds.isValid()) {
    map.fitBounds(bounds, { padding: [32, 32], maxZoom: 16 });
  } else {
    map.setView(SPAIN_CENTER, 6);
  }
}

function focusParcel(id: string) {
  if (!map) return;
  const b = boundsById.get(id);
  const layer = layersById.get(id);
  if (!b) return;
  // The map container may have just become visible; make sure Leaflet knows
  // its real size before fitting bounds, otherwise the centering is off.
  map.invalidateSize();
  if (b.getNorthEast().equals(b.getSouthWest())) {
    // Point geometry: center with a close zoom.
    map.setView(b.getCenter(), 17, { animate: true });
  } else {
    map.fitBounds(b, { padding: [48, 48], maxZoom: 18, animate: true });
  }
  if (layer) {
    layer.setStyle({ weight: 4 });
    layer.openTooltip?.();
    window.setTimeout(() => layer.setStyle({ weight: 2 }), 2200);
  }
}

function bindParcel(layer: L.Path, p: Parcel) {
  layer.bindTooltip(
    `<strong>${escapeHtml(p.name)}</strong><br>${escapeHtml(
      p.farm_name,
    )} · ${Number(p.area_ha).toLocaleString('es-ES', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })} ha`,
    { direction: 'top', sticky: true },
  );
  layer.on('click', () => emit('select', p));
  layer.on('mouseover', () => layer.setStyle({ weight: 3.5 }));
  layer.on('mouseout', () => layer.setStyle({ weight: 2 }));
}

function escapeHtml(s: string): string {
  return (s ?? '').replace(
    /[&<>"']/g,
    (c) =>
      ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
      })[c] || c,
  );
}

onMounted(() => {
  if (!el.value) return;
  map = L.map(el.value, { zoomControl: true }).setView(SPAIN_CENTER, 6);

  const sat = L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    { maxZoom: 19, attribution: 'Esri, Maxar — World Imagery' },
  ).addTo(map);

  const osm = L.tileLayer(
    'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    {
      maxZoom: 19,
      attribution: '© OpenStreetMap',
    },
  );

  const catastro = L.tileLayer.wms(
    'https://ovc.catastro.meh.es/Cartografia/WMS/ServidorWMS.aspx',
    {
      layers: 'Catastro',
      format: 'image/png',
      transparent: true,
      opacity: 0.5,
      attribution: 'Dirección General del Catastro',
    },
  );

  L.control
    .layers(
      { Satélite: sat, Mapa: osm },
      { 'Parcelas catastrales': catastro },
      { collapsed: true },
    )
    .addTo(map);

  render();
  nextTick(() => map?.invalidateSize());
  setTimeout(() => map?.invalidateSize(), 250);
});

watch(() => props.parcels, render, { deep: true });

watch(
  () => props.focusId,
  (id) => {
    if (id) nextTick(() => focusParcel(id));
  },
);

onUnmounted(() => {
  map?.remove();
  map = null;
  featureLayer = null;
});
</script>

<template>
  <div class="relative">
    <div ref="el" class="overview-map" :style="{ height: `${height}px` }" />
    <p
      class="absolute bottom-2 left-2 z-[500] text-[11px] text-white/90 bg-slate-900/55 px-2 py-1 rounded-md pointer-events-none"
    >
      Haz clic en una parcela para abrir su detalle
    </p>
  </div>
</template>

<style scoped>
.overview-map {
  width: 100%;
  border-radius: 0.75rem;
  overflow: hidden;
  z-index: 0;
}
</style>
