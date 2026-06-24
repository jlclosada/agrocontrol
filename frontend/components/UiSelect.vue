<script setup lang="ts">
defineProps<{
  modelValue: string | number | null;
  options: { value: string | number; label: string }[];
  placeholder?: string;
  disabled?: boolean;
}>();
const emit = defineEmits<{ 'update:modelValue': [string] }>();
</script>

<template>
  <select
    :value="modelValue ?? ''"
    :disabled="disabled"
    class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition disabled:bg-slate-50 disabled:text-slate-400"
    @change="
      emit('update:modelValue', ($event.target as HTMLSelectElement).value)
    "
  >
    <option v-if="placeholder" value="" disabled>{{ placeholder }}</option>
    <option v-for="o in options" :key="o.value" :value="o.value">
      {{ o.label }}
    </option>
  </select>
</template>
