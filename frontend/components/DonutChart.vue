<script setup lang="ts">
/**
 * Animated SVG donut chart. Each segment draws its arc with a smooth
 * stroke-dashoffset transition. A default slot renders centered content.
 */
const props = withDefaults(
  defineProps<{
    segments: { value: number; color: string; label?: string }[];
    size?: number;
    thickness?: number;
    gap?: number;
  }>(),
  { size: 160, thickness: 16, gap: 2 },
);

const radius = computed(() => (props.size - props.thickness) / 2);
const circumference = computed(() => 2 * Math.PI * radius.value);
const total = computed(
  () => props.segments.reduce((s, x) => s + Math.max(0, x.value), 0) || 1,
);

const arcs = computed(() => {
  let offset = 0;
  return props.segments.map((seg) => {
    const frac = Math.max(0, seg.value) / total.value;
    const len = frac * circumference.value;
    const dash = Math.max(0, len - props.gap);
    const arc = {
      color: seg.color,
      dasharray: `${dash} ${circumference.value - dash}`,
      dashoffset: -offset,
    };
    offset += len;
    return arc;
  });
});
</script>

<template>
  <div
    class="relative grid place-items-center"
    :style="{ width: `${size}px`, height: `${size}px` }"
  >
    <svg
      :width="size"
      :height="size"
      :viewBox="`0 0 ${size} ${size}`"
      class="-rotate-90"
    >
      <circle
        :cx="size / 2"
        :cy="size / 2"
        :r="radius"
        fill="none"
        stroke="rgb(241 245 249)"
        :stroke-width="thickness"
      />
      <circle
        v-for="(a, i) in arcs"
        :key="i"
        :cx="size / 2"
        :cy="size / 2"
        :r="radius"
        fill="none"
        :stroke="a.color"
        :stroke-width="thickness"
        stroke-linecap="round"
        :stroke-dasharray="a.dasharray"
        :stroke-dashoffset="a.dashoffset"
        class="donut-arc"
        :style="{ '--i': i }"
      />
    </svg>
    <div class="absolute inset-0 grid place-items-center text-center">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.donut-arc {
  transition:
    stroke-dasharray 1s cubic-bezier(0.16, 1, 0.3, 1),
    stroke-dashoffset 1s cubic-bezier(0.16, 1, 0.3, 1);
  animation: donut-in 1s cubic-bezier(0.16, 1, 0.3, 1) both;
  animation-delay: calc(var(--i, 0) * 120ms);
}
@keyframes donut-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
@media (prefers-reduced-motion: reduce) {
  .donut-arc {
    animation: none;
  }
}
</style>
