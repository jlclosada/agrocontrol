<script setup lang="ts">
withDefaults(
  defineProps<{
    label?: string;
    tone?: 'green' | 'red' | 'amber' | 'sky' | 'slate' | 'violet';
    dot?: boolean;
  }>(),
  { tone: 'slate' },
);

const tones: Record<string, string> = {
  green: 'bg-brand-50 text-brand-700 ring-brand-600/20',
  red: 'bg-red-50 text-red-600 ring-red-600/20',
  amber: 'bg-amber-50 text-amber-700 ring-amber-600/20',
  sky: 'bg-sky-50 text-sky-700 ring-sky-600/20',
  slate: 'bg-slate-100 text-slate-600 ring-slate-500/15',
  violet: 'bg-violet-50 text-violet-700 ring-violet-600/20',
};
const dots: Record<string, string> = {
  green: 'bg-brand-500',
  red: 'bg-red-500',
  amber: 'bg-amber-500',
  sky: 'bg-sky-500',
  slate: 'bg-slate-400',
  violet: 'bg-violet-500',
};
</script>

<template>
  <span
    class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ring-1 ring-inset"
    :class="tones[tone]"
  >
    <span v-if="dot" class="w-1.5 h-1.5 rounded-full" :class="dots[tone]" />
    <slot>{{ label }}</slot>
  </span>
</template>
