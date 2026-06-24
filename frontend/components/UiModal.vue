<script setup lang="ts">
const props = defineProps<{ modelValue: boolean; title?: string }>();
const emit = defineEmits<{ 'update:modelValue': [boolean] }>();

function close() {
  emit('update:modelValue', false);
}

watch(
  () => props.modelValue,
  (open) => {
    if (import.meta.client) {
      document.body.style.overflow = open ? 'hidden' : '';
    }
  },
);
onUnmounted(() => {
  if (import.meta.client) document.body.style.overflow = '';
});
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 grid place-items-center p-4 bg-slate-900/40 backdrop-blur-sm"
        @click.self="close"
      >
        <div
          class="modal-panel bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-auto"
        >
          <div
            class="flex items-center justify-between px-6 py-4 border-b border-slate-100 sticky top-0 bg-white/90 backdrop-blur"
          >
            <h3 class="font-semibold text-slate-800">{{ title }}</h3>
            <button
              class="text-slate-400 hover:text-slate-700 transition rounded-lg p-1"
              @click="close"
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
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
          <div class="p-6">
            <slot />
          </div>
          <div
            v-if="$slots.footer"
            class="px-6 py-4 border-t border-slate-100 flex justify-end gap-2"
          >
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
