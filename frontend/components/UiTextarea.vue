<script setup lang="ts">
defineProps<{
  modelValue: string | null;
  placeholder?: string;
  rows?: number;
}>();
const emit = defineEmits<{ 'update:modelValue': [string] }>();
</script>

<template>
  <textarea
    :value="modelValue ?? ''"
    :placeholder="placeholder"
    :rows="rows ?? 3"
    class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition resize-y"
    @input="
      emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)
    "
  />
</template>
