<script setup lang="ts">
defineProps<{ rows?: number; cols?: number }>();
</script>

<template>
  <div class="space-y-3">
    <div
      v-for="r in rows ?? 5"
      :key="r"
      class="flex gap-3"
      :style="{ '--i': r }"
    >
      <div
        v-for="c in cols ?? 4"
        :key="c"
        class="relative h-10 flex-1 rounded-lg bg-slate-100 overflow-hidden"
      >
        <div
          class="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/70 to-transparent animate-shimmer"
        />
      </div>
    </div>
  </div>
</template>
