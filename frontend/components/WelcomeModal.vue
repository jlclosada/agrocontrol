<script setup lang="ts">
import { useTour } from '~/composables/useTour';
import { useAuthStore } from '~/stores/auth';

const tour = useTour();
const auth = useAuthStore();
const open = ref(false);

// Show once for first-time users, after auth + cooperative are ready.
onMounted(() => {
  tour.hydrate();
  watch(
    [
      () => auth.isAuthenticated,
      () => tour.completed.value,
      () => tour.active.value,
    ],
    ([authed, done, active]) => {
      open.value = !!authed && !done && !active;
    },
    { immediate: true },
  );
});

function startTour() {
  open.value = false;
  tour.start();
}

function dismiss() {
  open.value = false;
  tour.markCompleted();
}

const highlights = [
  {
    icon: 'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10',
    label: 'Inventario FEFO',
  },
  {
    icon: 'M3 3v18h18M7 14l3-3 3 3 5-6',
    label: 'Costes y rentabilidad',
  },
  {
    icon: 'M13 10V3L4 14h7v7l9-11h-7z',
    label: 'Trazabilidad',
  },
  {
    icon: 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5',
    label: 'Alertas IA',
  },
];
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="open"
        class="fixed inset-0 z-[90] grid place-items-center p-4 bg-slate-900/50 backdrop-blur-sm"
      >
        <div
          class="welcome-panel relative w-full max-w-md bg-white rounded-3xl shadow-2xl ring-1 ring-slate-900/5 overflow-hidden"
        >
          <!-- Decorative header -->
          <div
            class="relative h-32 bg-gradient-to-br from-brand-500 to-brand-700 overflow-hidden"
          >
            <div
              class="absolute -top-10 -right-8 w-40 h-40 rounded-full bg-white/10 blur-2xl"
            />
            <div
              class="absolute -bottom-12 -left-6 w-40 h-40 rounded-full bg-white/10 blur-2xl"
            />
            <div
              class="absolute inset-0 grid place-items-center text-6xl select-none animate-float"
            >
              {{ auth.branding.emoji }}
            </div>
          </div>

          <div class="p-6 -mt-4">
            <h2 class="text-xl font-extrabold text-slate-800 text-center">
              Bienvenido a {{ auth.branding.appName }}
            </h2>
            <p
              class="mt-1.5 text-sm text-slate-500 text-center leading-relaxed"
            >
              ¿Es tu primera vez? Te mostramos cómo sacar el máximo partido a la
              plataforma con una demo guiada de un minuto.
            </p>

            <div class="mt-5 grid grid-cols-2 gap-2.5">
              <div
                v-for="h in highlights"
                :key="h.label"
                class="flex items-center gap-2.5 rounded-xl bg-slate-50 px-3 py-2.5 ring-1 ring-slate-100"
              >
                <div
                  class="w-8 h-8 shrink-0 rounded-lg grid place-items-center bg-brand-50 text-brand-600"
                >
                  <svg
                    class="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      :d="h.icon"
                    />
                  </svg>
                </div>
                <span class="text-xs font-medium text-slate-600">{{
                  h.label
                }}</span>
              </div>
            </div>

            <div class="mt-6 flex flex-col gap-2">
              <button
                class="w-full py-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-semibold transition shadow-glow flex items-center justify-center gap-2 group"
                @click="startTour"
              >
                <svg
                  class="w-5 h-5 transition-transform group-hover:scale-110"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                  />
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                Ver demo guiada
              </button>
              <button
                class="w-full py-2.5 rounded-xl text-slate-500 hover:text-slate-700 hover:bg-slate-50 font-medium transition"
                @click="dismiss"
              >
                Saltar por ahora
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.welcome-panel {
  animation: welcome-in 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
}
@keyframes welcome-in {
  0% {
    opacity: 0;
    transform: scale(0.92) translateY(16px);
  }
  100% {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}
.animate-float {
  animation: float 3.5s ease-in-out infinite;
}
@keyframes float {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-8px);
  }
}
</style>
