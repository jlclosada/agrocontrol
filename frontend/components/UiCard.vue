<script setup lang="ts">
defineProps<{
  padded?: boolean;
  hover?: boolean;
}>();
</script>

<template>
  <div
    class="bg-white rounded-2xl border border-slate-100 shadow-card transition-all duration-300"
    :class="[
      padded === false ? '' : 'p-5',
      hover
        ? 'hover:-translate-y-0.5 hover:shadow-glow hover:border-brand-100'
        : '',
    ]"
  >
    <slot />
  </div>
</template>
