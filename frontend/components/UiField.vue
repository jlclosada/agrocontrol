<script setup lang="ts">
defineProps<{
  label?: string;
  help?: string;
  error?: string;
  required?: boolean;
}>();
</script>

<template>
  <label class="block">
    <span v-if="label" class="block text-xs font-medium text-slate-600 mb-1">
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </span>
    <slot />
    <span v-if="error" class="block text-xs text-red-600 mt-1">{{
      error
    }}</span>
    <span v-else-if="help" class="block text-xs text-slate-400 mt-1">{{
      help
    }}</span>
  </label>
</template>
