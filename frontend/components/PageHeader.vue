<script setup lang="ts">
defineProps<{
  title: string;
  subtitle?: string;
}>();
</script>

<template>
  <div
    class="flex flex-wrap items-end justify-between gap-4 animate-fade-in-up"
  >
    <div class="flex items-stretch gap-3">
      <span
        class="w-1 rounded-full bg-gradient-to-b from-brand-400 to-brand-600 shrink-0"
      />
      <div>
        <h1 class="text-2xl font-bold text-slate-800 tracking-tight">
          {{ title }}
        </h1>
        <p v-if="subtitle" class="text-slate-500 mt-0.5 text-sm">
          {{ subtitle }}
        </p>
      </div>
    </div>
    <div class="flex items-center gap-2">
      <slot name="actions" />
    </div>
  </div>
</template>
