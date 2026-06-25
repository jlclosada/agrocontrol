<script setup lang="ts">
import { useTour } from '~/composables/useTour';
import { useAuthStore } from '~/stores/auth';

const auth = useAuthStore();
const route = useRoute();
const brandTheme = useBrandTheme();
const tour = useTour();

watch(
  () => auth.branding.color,
  (color) => brandTheme.apply(color),
  { immediate: true },
);

const adminRoles = ['SUPERADMIN', 'COOP_ADMIN', 'AGRONOMIST', 'AUDITOR'];
const canSeeAdmin = computed(() => adminRoles.includes(auth.role ?? ''));

interface NavItem {
  to: string;
  label: string;
  icon: string;
  show?: () => boolean;
}
interface NavGroup {
  title: string;
  items: NavItem[];
}

const groups = computed<NavGroup[]>(() =>
  [
    {
      title: '',
      items: [
        {
          to: '/',
          label: 'Dashboard',
          icon: 'M3 12l9-9 9 9M5 10v10h14V10',
        },
      ],
    },
    {
      title: 'Operación',
      items: [
        { to: '/parcels', label: 'Parcelas', icon: 'M4 6h16M4 12h16M4 18h16' },
        {
          to: '/fieldbook',
          label: 'Cuaderno',
          icon: 'M12 6.5C9 4 4 4 4 4v14s5 0 8 2.5M12 6.5C15 4 20 4 20 4v14s-5 0-8 2.5M12 6.5v14',
        },
        {
          to: '/tasks',
          label: 'Tareas',
          icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01',
        },
        {
          to: '/inventory',
          label: 'Inventario',
          icon: 'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4',
        },
      ],
    },
    {
      title: 'Análisis',
      items: [
        {
          to: '/costs',
          label: 'Costes y rentabilidad',
          icon: 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1',
        },
        {
          to: '/traceability',
          label: 'Trazabilidad',
          icon: 'M13 10V3L4 14h7v7l9-11h-7z',
        },
        {
          to: '/alerts',
          label: 'Alertas',
          icon: 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1',
        },
      ],
    },
    {
      title: 'Inteligencia',
      items: [
        {
          to: '/agents',
          label: 'Agentes IA',
          icon: 'M12 2a5 5 0 015 5v2a5 5 0 01-10 0V7a5 5 0 015-5z',
        },
      ],
    },
    {
      title: 'Administración',
      items: [
        {
          to: '/team',
          label: 'Equipo',
          icon: 'M17 20h5v-2a4 4 0 00-3-3.87M9 20H4v-2a4 4 0 013-3.87m6-1.13a4 4 0 10-4-4 4 4 0 004 4zm6 0a3 3 0 10-2.5-1.34M7 11a3 3 0 11.5-1.34',
        },
        {
          to: '/audit',
          label: 'Auditoría',
          icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
          show: () => canSeeAdmin.value,
        },
        {
          to: '/settings',
          label: 'Ajustes',
          icon: 'M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z',
        },
      ],
    },
  ]
    .map((g) => ({
      ...g,
      items: g.items.filter((i) => !i.show || i.show()),
    }))
    .filter((g) => g.items.length),
);

const mobileOpen = ref(false);
watch(
  () => route.path,
  () => (mobileOpen.value = false),
);

function isActive(to: string) {
  return to === '/' ? route.path === '/' : route.path.startsWith(to);
}
</script>

<template>
  <div class="min-h-screen flex bg-slate-50">
    <!-- Mobile backdrop -->
    <Transition name="modal">
      <div
        v-if="mobileOpen"
        class="fixed inset-0 z-30 bg-slate-900/40 lg:hidden"
        @click="mobileOpen = false"
      />
    </Transition>

    <!-- Sidebar -->
    <aside
      class="fixed lg:static inset-y-0 left-0 z-40 w-64 bg-gradient-to-b from-brand-800 to-brand-900 text-white flex flex-col transition-transform duration-300 lg:translate-x-0 shadow-xl lg:shadow-none"
      :class="mobileOpen ? 'translate-x-0' : '-translate-x-full'"
    >
      <div
        class="px-5 py-5 flex items-center gap-3 border-b border-white/5"
        data-tour="brand"
      >
        <div
          class="w-10 h-10 shrink-0 rounded-xl grid place-items-center text-xl bg-white/10 ring-1 ring-white/15 backdrop-blur"
        >
          {{ auth.branding.emoji }}
        </div>
        <div class="min-w-0">
          <p class="font-extrabold tracking-tight leading-tight truncate">
            {{ auth.branding.appName }}
          </p>
          <p class="text-[11px] text-brand-200/80 truncate">
            {{ auth.branding.tagline }}
          </p>
        </div>
      </div>

      <nav class="flex-1 px-3 py-4 space-y-5 overflow-auto">
        <div v-for="group in groups" :key="group.title">
          <p
            v-if="group.title"
            class="px-3 mb-1 text-[10px] font-semibold uppercase tracking-wider text-brand-300/70"
          >
            {{ group.title }}
          </p>
          <div class="space-y-0.5">
            <NuxtLink
              v-for="item in group.items"
              :key="item.to"
              :to="item.to"
              :data-tour="`nav-${item.to}`"
              class="group flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition relative"
              :class="
                isActive(item.to)
                  ? 'bg-white/10 text-white font-medium'
                  : 'text-brand-100/80 hover:bg-white/5 hover:text-white'
              "
            >
              <span
                v-if="isActive(item.to)"
                class="absolute left-0 top-1.5 bottom-1.5 w-1 rounded-r-full bg-brand-300"
              />
              <svg
                class="w-5 h-5 shrink-0 transition group-hover:scale-110"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  :d="item.icon"
                />
              </svg>
              {{ item.label }}
            </NuxtLink>
          </div>
        </div>
      </nav>

      <div class="p-3 border-t border-white/10" data-tour="user">
        <div class="flex items-center gap-3 px-2 py-2">
          <img
            v-if="auth.avatarUrl"
            :src="auth.avatarUrl"
            alt="Avatar"
            class="w-9 h-9 rounded-full object-cover shrink-0 ring-1 ring-white/20"
          />
          <div
            v-else
            class="w-9 h-9 rounded-full bg-brand-500 grid place-items-center text-sm font-semibold shrink-0"
          >
            {{ auth.initials }}
          </div>
          <div class="min-w-0">
            <p class="text-sm font-medium truncate">{{ auth.user?.email }}</p>
            <p class="text-brand-100/70 text-xs truncate">
              {{ auth.cooperative?.name }} · {{ auth.role }}
            </p>
          </div>
        </div>
        <button
          class="mt-1 w-full flex items-center gap-2 text-left text-xs text-brand-100/80 hover:text-white px-2 py-1.5 rounded-lg hover:bg-white/5 transition"
          @click="tour.start()"
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
              d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
            />
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          Ver demo
        </button>
        <button
          class="mt-0.5 w-full text-left text-xs text-brand-100/70 hover:text-white px-2 py-1.5 rounded-lg hover:bg-white/5 transition"
          @click="auth.logout()"
        >
          Cerrar sesión
        </button>
      </div>
    </aside>

    <!-- Main -->
    <div class="flex-1 flex flex-col min-w-0">
      <header
        class="lg:hidden sticky top-0 z-20 bg-white/80 backdrop-blur border-b border-slate-100 px-4 py-3 flex items-center gap-3"
      >
        <button
          class="p-2 rounded-lg hover:bg-slate-100 transition"
          @click="mobileOpen = true"
        >
          <svg
            class="w-5 h-5 text-slate-700"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M4 6h16M4 12h16M4 18h16"
            />
          </svg>
        </button>
        <span class="font-bold text-slate-800 flex items-center gap-1.5">
          <span>{{ auth.branding.emoji }}</span>
          <span>{{ auth.branding.appName }}</span>
        </span>
      </header>

      <main class="flex-1 overflow-auto">
        <slot />
      </main>
    </div>

    <ToastHost />
    <WelcomeModal />
    <TourOverlay />
  </div>
</template>
