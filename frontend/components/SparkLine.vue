<script setup lang="ts">
/**
 * Minimal animated SVG sparkline with a soft gradient area fill.
 * Purely decorative trend visual — accepts a numeric series.
 */
const props = withDefaults(
  defineProps<{
    points: number[];
    width?: number;
    height?: number;
    stroke?: string;
    fill?: string;
  }>(),
  {
    width: 120,
    height: 36,
    stroke: 'rgb(var(--brand-500))',
    fill: 'rgb(var(--brand-500))',
  },
);

const gid = `spark-${Math.random().toString(36).slice(2, 8)}`;

const geometry = computed(() => {
  const pts = props.points.length ? props.points : [0, 0];
  const min = Math.min(...pts);
  const max = Math.max(...pts);
  const span = max - min || 1;
  const stepX = props.width / Math.max(1, pts.length - 1);
  const pad = 3;
  const usableH = props.height - pad * 2;
  const coords = pts.map((p, i) => {
    const x = i * stepX;
    const y = pad + usableH - ((p - min) / span) * usableH;
    return [x, y] as const;
  });
  const line = coords
    .map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`)
    .join(' ');
  const area = `${line} L${props.width},${props.height} L0,${props.height} Z`;
  return { line, area, last: coords[coords.length - 1] };
});
</script>

<template>
  <svg
    :viewBox="`0 0 ${width} ${height}`"
    :width="width"
    :height="height"
    fill="none"
    preserveAspectRatio="none"
    class="overflow-visible"
  >
    <defs>
      <linearGradient :id="gid" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" :stop-color="fill" stop-opacity="0.22" />
        <stop offset="100%" :stop-color="fill" stop-opacity="0" />
      </linearGradient>
    </defs>
    <path :d="geometry.area" :fill="`url(#${gid})`" class="spark-area" />
    <path
      :d="geometry.line"
      :stroke="stroke"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
      class="spark-line"
    />
    <circle
      v-if="geometry.last"
      :cx="geometry.last[0]"
      :cy="geometry.last[1]"
      r="2.6"
      :fill="stroke"
      class="spark-dot"
    />
  </svg>
</template>

<style scoped>
.spark-line {
  stroke-dasharray: 240;
  stroke-dashoffset: 240;
  animation: draw 1.1s cubic-bezier(0.16, 1, 0.3, 1) 0.1s forwards;
}
.spark-area {
  opacity: 0;
  animation: fade 0.8s ease 0.6s forwards;
}
.spark-dot {
  opacity: 0;
  animation: fade 0.4s ease 1.05s forwards;
}
@keyframes draw {
  to {
    stroke-dashoffset: 0;
  }
}
@keyframes fade {
  to {
    opacity: 1;
  }
}
@media (prefers-reduced-motion: reduce) {
  .spark-line,
  .spark-area,
  .spark-dot {
    animation: none;
    stroke-dashoffset: 0;
    opacity: 1;
  }
}
</style>
