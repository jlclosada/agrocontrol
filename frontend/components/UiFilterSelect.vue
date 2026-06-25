<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    modelValue: string | number | null;
    options: { value: string | number; label: string }[];
    placeholder?: string;
    icon?: string;
    align?: 'left' | 'right';
  }>(),
  { align: 'left' },
);
const emit = defineEmits<{ 'update:modelValue': [string | number] }>();

const open = ref(false);
const root = ref<HTMLElement | null>(null);

const selected = computed(() =>
  props.options.find((o) => String(o.value) === String(props.modelValue)),
);
const buttonLabel = computed(
  () => selected.value?.label ?? props.placeholder ?? 'Seleccionar',
);

function choose(value: string | number) {
  emit('update:modelValue', value);
  open.value = false;
}

function onDocClick(e: MouseEvent) {
  if (root.value && !root.value.contains(e.target as Node)) open.value = false;
}
function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') open.value = false;
}

onMounted(() => {
  document.addEventListener('click', onDocClick);
  document.addEventListener('keydown', onKey);
});
onBeforeUnmount(() => {
  document.removeEventListener('click', onDocClick);
  document.removeEventListener('keydown', onKey);
});
</script>

<template>
  <div ref="root" class="relative">
    <button
      type="button"
      class="inline-flex items-center gap-2 w-full pl-3 pr-2.5 py-2 text-sm rounded-lg border bg-white transition whitespace-nowrap"
      :class="
        open
          ? 'border-brand-400 ring-2 ring-brand-500/30'
          : 'border-slate-200 hover:border-slate-300'
      "
      @click="open = !open"
    >
      <svg
        v-if="icon"
        class="w-4 h-4 text-slate-400 shrink-0"
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
      <span
        class="flex-1 text-left truncate"
        :class="selected ? 'text-slate-700 font-medium' : 'text-slate-400'"
      >
        {{ buttonLabel }}
      </span>
      <svg
        class="w-4 h-4 text-slate-400 shrink-0 transition-transform"
        :class="open ? 'rotate-180' : ''"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M19 9l-7 7-7-7"
        />
      </svg>
    </button>

    <Transition name="dropdown">
      <div
        v-if="open"
        class="absolute z-30 mt-2 min-w-full max-w-[18rem] w-max rounded-xl border border-slate-100 bg-white shadow-lg shadow-slate-200/60 p-1.5 max-h-72 overflow-y-auto"
        :class="align === 'right' ? 'right-0' : 'left-0'"
      >
        <button
          v-for="o in options"
          :key="o.value"
          type="button"
          class="flex items-center gap-2 w-full text-left px-2.5 py-2 rounded-lg text-sm transition"
          :class="
            String(o.value) === String(modelValue)
              ? 'bg-brand-50 text-brand-700 font-medium'
              : 'text-slate-600 hover:bg-slate-50'
          "
          @click="choose(o.value)"
        >
          <span class="flex-1 truncate">{{ o.label }}</span>
          <svg
            v-if="String(o.value) === String(modelValue)"
            class="w-4 h-4 text-brand-500 shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M5 13l4 4L19 7"
            />
          </svg>
        </button>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.dropdown-enter-active,
.dropdown-leave-active {
  transition:
    opacity 0.15s ease,
    transform 0.15s ease;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.98);
}
@media (prefers-reduced-motion: reduce) {
  .dropdown-enter-active,
  .dropdown-leave-active {
    transition: none;
  }
}
</style>
