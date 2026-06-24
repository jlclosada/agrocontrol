<script setup lang="ts">
defineProps<{
  modelValue: string;
  tabs: { value: string; label: string; count?: number }[];
}>();
const emit = defineEmits<{ 'update:modelValue': [string] }>();
</script>

<template>
  <div class="inline-flex p-1 bg-slate-100 rounded-xl gap-1">
    <button
      v-for="t in tabs"
      :key="t.value"
      class="relative px-3.5 py-1.5 rounded-lg text-sm font-medium transition"
      :class="
        modelValue === t.value
          ? 'bg-white text-brand-700 shadow-sm'
          : 'text-slate-500 hover:text-slate-700'
      "
      @click="emit('update:modelValue', t.value)"
    >
      {{ t.label }}
      <span v-if="t.count !== undefined" class="ml-1 text-xs opacity-70">{{
        t.count
      }}</span>
    </button>
  </div>
</template>
