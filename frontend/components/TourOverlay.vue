<script setup lang="ts">
import { useTour } from '~/composables/useTour';

const tour = useTour();
const router = useRouter();

interface Rect {
  top: number;
  left: number;
  width: number;
  height: number;
}

const PAD = 8; // spotlight padding around the target
const rect = ref<Rect | null>(null);
const measuring = ref(false);

function readTarget(): Rect | null {
  const sel = tour.current.value?.target;
  if (!sel) return null;
  const el = document.querySelector(sel) as HTMLElement | null;
  if (!el) return null;
  const r = el.getBoundingClientRect();
  if (r.width === 0 && r.height === 0) return null;
  return {
    top: r.top - PAD,
    left: r.left - PAD,
    width: r.width + PAD * 2,
    height: r.height + PAD * 2,
  };
}

function scrollIntoView() {
  const sel = tour.current.value?.target;
  if (!sel) return;
  const el = document.querySelector(sel) as HTMLElement | null;
  el?.scrollIntoView({
    behavior: 'smooth',
    block: 'center',
    inline: 'nearest',
  });
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

/** Wait until the target element is in the DOM with a real size (or timeout). */
async function waitForTarget(timeout = 1600): Promise<HTMLElement | null> {
  const sel = tour.current.value?.target;
  if (!sel) return null;
  const start = performance.now();
  // eslint-disable-next-line no-constant-condition
  while (true) {
    const el = document.querySelector(sel) as HTMLElement | null;
    if (el) {
      const r = el.getBoundingClientRect();
      if (r.width > 0 || r.height > 0) return el;
    }
    if (performance.now() - start > timeout) return el ?? null;
    await new Promise((r) => requestAnimationFrame(() => r(null)));
  }
}

/** Poll the target rect until it stops moving (scroll/anim settled). */
async function waitUntilStable(timeout = 700) {
  const start = performance.now();
  let prev = readTarget();
  let stable = 0;
  // eslint-disable-next-line no-constant-condition
  while (performance.now() - start < timeout) {
    await new Promise((r) => requestAnimationFrame(() => r(null)));
    const cur = readTarget();
    if (
      cur &&
      prev &&
      Math.abs(cur.top - prev.top) < 0.5 &&
      Math.abs(cur.left - prev.left) < 0.5
    ) {
      stable += 1;
      if (stable >= 3) return cur; // 3 consecutive stable frames
    } else {
      stable = 0;
    }
    prev = cur;
  }
  return prev;
}

async function refresh(withNav = false) {
  if (!tour.active.value) return;
  measuring.value = true;
  const step = tour.current.value;
  if (withNav && step?.route && router.currentRoute.value.path !== step.route) {
    await router.push(step.route);
  }
  await nextTick();

  // Centered slide (no target): no measuring needed.
  if (!step?.target) {
    rect.value = null;
    await sleep(120);
    measuring.value = false;
    return;
  }

  // Wait for the element to mount with a real size, then scroll & settle.
  await waitForTarget();
  scrollIntoView();
  rect.value = await waitUntilStable();
  // Final read in case the last frame nudged it.
  rect.value = readTarget();
  measuring.value = false;
}

// Tooltip geometry derived from the spotlight rect + chosen placement.
const TIP_W = 340;
const tipStyle = computed(() => {
  if (!import.meta.client) return {};
  const vw = window.innerWidth;
  const vh = window.innerHeight;
  const margin = 16;
  if (!rect.value) {
    // Centered slide.
    return {
      top: `${vh / 2}px`,
      left: `${vw / 2}px`,
      transform: 'translate(-50%, -50%)',
    } as Record<string, string>;
  }
  const r = rect.value;
  let placement = tour.current.value?.placement ?? 'auto';
  if (placement === 'auto') {
    placement = r.top > vh / 2 ? 'top' : 'bottom';
  }
  // Space checks → fall back to opposite side if it would overflow.
  if (placement === 'right' && r.left + r.width + TIP_W + margin > vw)
    placement = 'left';
  if (placement === 'left' && r.left - TIP_W - margin < 0) placement = 'right';
  if (placement === 'bottom' && r.top + r.height + 200 > vh) placement = 'top';
  if (placement === 'top' && r.top - 200 < 0) placement = 'bottom';

  let top = 0;
  let left = 0;
  let transform = '';
  const cx = r.left + r.width / 2;
  const cy = r.top + r.height / 2;
  switch (placement) {
    case 'right':
      top = cy;
      left = r.left + r.width + margin;
      transform = 'translateY(-50%)';
      break;
    case 'left':
      top = cy;
      left = r.left - margin;
      transform = 'translate(-100%, -50%)';
      break;
    case 'top':
      top = r.top - margin;
      left = cx;
      transform = 'translate(-50%, -100%)';
      break;
    default: // bottom
      top = r.top + r.height + margin;
      left = cx;
      transform = 'translateX(-50%)';
  }
  // Clamp horizontally so the card never leaves the viewport.
  const halfNudge =
    transform.includes('-50%') && !transform.includes('-100%') ? TIP_W / 2 : 0;
  if (left - halfNudge < margin) left = margin + halfNudge;
  if (left + halfNudge > vw - margin) left = vw - margin - halfNudge;
  return { top: `${top}px`, left: `${left}px`, transform };
});

const spotlightStyle = computed(() => {
  if (!rect.value) return { opacity: '0' } as Record<string, string>;
  const r = rect.value;
  return {
    top: `${r.top}px`,
    left: `${r.left}px`,
    width: `${r.width}px`,
    height: `${r.height}px`,
    opacity: '1',
  };
});

const progress = computed(
  () => ((tour.stepIndex.value + 1) / tour.steps.value.length) * 100,
);

function onResize() {
  rect.value = readTarget();
}

watch(
  () => tour.stepIndex.value,
  () => refresh(true),
);
watch(
  () => tour.active.value,
  (on) => {
    if (on) {
      document.body.style.overflow = 'hidden';
      refresh(true);
      window.addEventListener('resize', onResize, { passive: true });
      window.addEventListener('scroll', onResize, { passive: true });
    } else {
      document.body.style.overflow = '';
      window.removeEventListener('resize', onResize);
      window.removeEventListener('scroll', onResize);
    }
  },
);

function onKey(e: KeyboardEvent) {
  if (!tour.active.value) return;
  if (e.key === 'Escape') tour.skip();
  else if (e.key === 'ArrowRight' || e.key === 'Enter') tour.next();
  else if (e.key === 'ArrowLeft') tour.prev();
}

onMounted(() => window.addEventListener('keydown', onKey));
onUnmounted(() => {
  window.removeEventListener('keydown', onKey);
  window.removeEventListener('resize', onResize);
  window.removeEventListener('scroll', onResize);
  if (import.meta.client) document.body.style.overflow = '';
});
</script>

<template>
  <Teleport to="body">
    <Transition name="tour-fade">
      <div
        v-if="tour.active.value"
        class="fixed inset-0 z-[100]"
        aria-live="polite"
      >
        <!-- Dim layer (covers everything when there's no target) -->
        <div
          class="absolute inset-0 transition-opacity duration-300"
          :class="rect ? 'bg-transparent' : 'bg-slate-900/70 backdrop-blur-sm'"
        />

        <!-- Spotlight cutout: the huge box-shadow dims everything around it -->
        <div
          v-show="rect"
          class="tour-spotlight pointer-events-none absolute rounded-2xl"
          :style="spotlightStyle"
        />

        <!-- Tooltip card -->
        <Transition name="tour-pop" appear>
          <div
            v-show="!measuring"
            class="tour-tip absolute w-[340px] max-w-[calc(100vw-2rem)]"
            :style="tipStyle"
          >
            <div
              class="relative bg-white rounded-2xl shadow-2xl ring-1 ring-slate-900/5 overflow-hidden"
            >
              <!-- progress -->
              <div class="h-1 bg-slate-100">
                <div
                  class="h-full bg-gradient-to-r from-brand-400 to-brand-600 transition-all duration-500 ease-out"
                  :style="{ width: `${progress}%` }"
                />
              </div>

              <div class="p-5">
                <div class="flex items-start gap-3">
                  <div
                    v-if="tour.current.value?.icon"
                    class="w-10 h-10 shrink-0 rounded-xl grid place-items-center bg-brand-50 text-brand-600 ring-1 ring-brand-100"
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
                        :d="tour.current.value.icon"
                      />
                    </svg>
                  </div>
                  <div class="min-w-0 flex-1">
                    <h3 class="font-bold text-slate-800 leading-snug">
                      {{ tour.current.value?.title }}
                    </h3>
                  </div>
                  <button
                    class="text-slate-300 hover:text-slate-600 transition -mt-1 -mr-1 p-1 rounded-lg"
                    aria-label="Cerrar demo"
                    @click="tour.skip()"
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
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </button>
                </div>

                <p class="mt-2 text-sm text-slate-500 leading-relaxed">
                  {{ tour.current.value?.body }}
                </p>

                <!-- step dots -->
                <div class="mt-4 flex items-center gap-1.5">
                  <button
                    v-for="(s, i) in tour.steps.value"
                    :key="i"
                    class="h-1.5 rounded-full transition-all duration-300"
                    :class="
                      i === tour.stepIndex.value
                        ? 'w-5 bg-brand-600'
                        : i < tour.stepIndex.value
                          ? 'w-1.5 bg-brand-300'
                          : 'w-1.5 bg-slate-200 hover:bg-slate-300'
                    "
                    :aria-label="`Paso ${i + 1}`"
                    @click="tour.goTo(i)"
                  />
                </div>

                <div class="mt-4 flex items-center justify-between gap-2">
                  <button
                    class="text-xs font-medium text-slate-400 hover:text-slate-600 transition"
                    @click="tour.skip()"
                  >
                    Saltar demo
                  </button>
                  <div class="flex items-center gap-2">
                    <button
                      v-if="!tour.isFirst.value"
                      class="text-sm px-3 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 transition"
                      @click="tour.prev()"
                    >
                      Atrás
                    </button>
                    <button
                      class="text-sm px-4 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-700 text-white font-medium transition shadow-glow"
                      @click="tour.next()"
                    >
                      {{ tour.isLast.value ? 'Finalizar' : 'Siguiente' }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.tour-spotlight {
  box-shadow:
    0 0 0 9999px rgba(15, 23, 42, 0.62),
    0 0 0 1px rgba(255, 255, 255, 0.25) inset;
  transition:
    top 0.45s cubic-bezier(0.16, 1, 0.3, 1),
    left 0.45s cubic-bezier(0.16, 1, 0.3, 1),
    width 0.45s cubic-bezier(0.16, 1, 0.3, 1),
    height 0.45s cubic-bezier(0.16, 1, 0.3, 1),
    opacity 0.3s ease;
}

.tour-tip {
  transition:
    top 0.45s cubic-bezier(0.16, 1, 0.3, 1),
    left 0.45s cubic-bezier(0.16, 1, 0.3, 1);
}

.tour-fade-enter-active,
.tour-fade-leave-active {
  transition: opacity 0.3s ease;
}
.tour-fade-enter-from,
.tour-fade-leave-to {
  opacity: 0;
}

.tour-pop-enter-active {
  transition:
    opacity 0.35s ease,
    transform 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}
.tour-pop-enter-from {
  opacity: 0;
  transform: scale(0.94) translateY(6px);
}
</style>
