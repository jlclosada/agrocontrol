<script setup lang="ts">
const { toasts, dismiss } = useToast();

const styles: Record<string, { bg: string; icon: string }> = {
  success: {
    bg: 'bg-brand-600',
    icon: 'M5 13l4 4L19 7',
  },
  error: {
    bg: 'bg-red-600',
    icon: 'M6 18L18 6M6 6l12 12',
  },
  info: {
    bg: 'bg-slate-800',
    icon: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  },
};
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed bottom-4 right-4 z-[60] space-y-2 w-80 max-w-[calc(100vw-2rem)]"
    >
      <TransitionGroup name="list">
        <div
          v-for="t in toasts"
          :key="t.id"
          class="flex items-start gap-3 text-white rounded-xl shadow-lg px-4 py-3 cursor-pointer"
          :class="styles[t.type].bg"
          @click="dismiss(t.id)"
        >
          <svg
            class="w-5 h-5 shrink-0 mt-0.5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              :d="styles[t.type].icon"
            />
          </svg>
          <p class="text-sm flex-1">{{ t.message }}</p>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>
