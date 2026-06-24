<script setup lang="ts">
withDefaults(
  defineProps<{
    modelValue: string | number | null;
    type?: string;
    placeholder?: string;
    step?: string;
    min?: string;
    max?: string;
    maxlength?: number;
    disabled?: boolean;
  }>(),
  { type: 'text' },
);
const emit = defineEmits<{ 'update:modelValue': [string] }>();
</script>

<template>
  <input
    :value="modelValue ?? ''"
    :type="type"
    :placeholder="placeholder"
    :step="step"
    :min="min"
    :max="max"
    :maxlength="maxlength"
    :disabled="disabled"
    class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition disabled:bg-slate-50 disabled:text-slate-400"
    @input="
      emit('update:modelValue', ($event.target as HTMLInputElement).value)
    "
  />
</template>
