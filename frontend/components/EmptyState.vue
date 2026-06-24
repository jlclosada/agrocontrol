<script setup lang="ts">
defineProps<{ title?: string; message?: string; icon?: string }>();
</script>

<template>
  <div class="flex flex-col items-center justify-center text-center py-14 px-6">
    <div
      class="w-14 h-14 rounded-2xl bg-slate-100 grid place-items-center text-slate-400 mb-4"
    >
      <svg
        class="w-7 h-7"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="1.5"
          :d="
            icon ||
            'M9 13h6m-3-3v6m-7 4h14a2 2 0 002-2V7a2 2 0 00-2-2h-5l-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z'
          "
        />
      </svg>
    </div>
    <p class="font-semibold text-slate-700">{{ title || 'Sin datos' }}</p>
    <p v-if="message" class="text-sm text-slate-400 mt-1 max-w-sm">
      {{ message }}
    </p>
    <div class="mt-4">
      <slot name="action" />
    </div>
  </div>
</template>
