<script setup lang="ts">
withDefaults(
  defineProps<{
    label: string;
    value: number | string;
    decimals?: number;
    prefix?: string;
    suffix?: string;
    icon?: string;
    tone?: 'brand' | 'amber' | 'red' | 'sky' | 'violet';
    spark?: number[];
    delta?: string;
    deltaUp?: boolean;
  }>(),
  { tone: 'brand', decimals: 0 },
);

const tones: Record<string, { icon: string; spark: string; glow: string }> = {
  brand: {
    icon: 'bg-brand-50 text-brand-600 ring-brand-100',
    spark: 'rgb(var(--brand-500))',
    glow: 'before:from-brand-500/[0.07]',
  },
  amber: {
    icon: 'bg-amber-50 text-amber-600 ring-amber-100',
    spark: '#f59e0b',
    glow: 'before:from-amber-500/[0.07]',
  },
  red: {
    icon: 'bg-red-50 text-red-600 ring-red-100',
    spark: '#ef4444',
    glow: 'before:from-red-500/[0.07]',
  },
  sky: {
    icon: 'bg-sky-50 text-sky-600 ring-sky-100',
    spark: '#0ea5e9',
    glow: 'before:from-sky-500/[0.07]',
  },
  violet: {
    icon: 'bg-violet-50 text-violet-600 ring-violet-100',
    spark: '#8b5cf6',
    glow: 'before:from-violet-500/[0.07]',
  },
};
</script>

<template>
  <div
    class="group relative bg-white rounded-2xl border border-slate-100 shadow-card p-5 overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:shadow-glow hover:border-brand-100 before:absolute before:inset-0 before:bg-gradient-to-br before:to-transparent before:opacity-0 before:transition-opacity before:duration-300 hover:before:opacity-100"
    :class="tones[tone].glow"
  >
    <div class="relative flex items-start justify-between gap-3">
      <div class="min-w-0">
        <p class="text-[13px] font-medium text-slate-400">{{ label }}</p>
        <p
          class="text-[28px] leading-tight font-extrabold text-slate-800 mt-1 tabular-nums tracking-tight"
        >
          <AnimatedNumber
            :value="value"
            :decimals="decimals"
            :prefix="prefix"
            :suffix="suffix"
          />
        </p>
        <div v-if="delta" class="mt-1.5 flex items-center gap-1">
          <span
            class="inline-flex items-center gap-0.5 text-[11px] font-semibold px-1.5 py-0.5 rounded-md"
            :class="
              deltaUp ? 'bg-brand-50 text-brand-700' : 'bg-red-50 text-red-600'
            "
          >
            <svg
              class="w-3 h-3"
              :class="deltaUp ? '' : 'rotate-180'"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2.5"
                d="M5 15l7-7 7 7"
              />
            </svg>
            {{ delta }}
          </span>
          <span class="text-[11px] text-slate-400">vs. mes anterior</span>
        </div>
      </div>
      <div
        v-if="icon"
        class="w-11 h-11 shrink-0 rounded-xl grid place-items-center ring-1 transition-transform duration-300 group-hover:scale-110 group-hover:-rotate-3"
        :class="tones[tone].icon"
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
            :d="icon"
          />
        </svg>
      </div>
    </div>

    <div v-if="spark?.length" class="relative mt-3 -mb-1 -mx-1">
      <SparkLine
        :points="spark"
        :width="240"
        :height="40"
        :stroke="tones[tone].spark"
        :fill="tones[tone].spark"
        class="w-full"
      />
    </div>
  </div>
</template>
