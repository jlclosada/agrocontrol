<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    value: number | string;
    duration?: number;
    decimals?: number;
    prefix?: string;
    suffix?: string;
  }>(),
  { duration: 900, decimals: 0, prefix: '', suffix: '' },
);

const display = ref(0);

function animate(to: number) {
  const from = display.value;
  const start = performance.now();
  const step = (now: number) => {
    const t = Math.min(1, (now - start) / props.duration);
    const eased = 1 - Math.pow(1 - t, 3);
    display.value = from + (to - from) * eased;
    if (t < 1) requestAnimationFrame(step);
    else display.value = to;
  };
  requestAnimationFrame(step);
}

const target = computed(() => {
  const n =
    typeof props.value === 'number' ? props.value : parseFloat(props.value);
  return Number.isFinite(n) ? n : 0;
});

const formatted = computed(() =>
  display.value.toLocaleString('es-ES', {
    minimumFractionDigits: props.decimals,
    maximumFractionDigits: props.decimals,
  }),
);

onMounted(() => animate(target.value));
watch(target, (v) => animate(v));
</script>

<template>
  <span>{{ prefix }}{{ formatted }}{{ suffix }}</span>
</template>
