<template>
  <div>
    <NuxtRouteAnnouncer />
    <!-- The app is fully behind JWT auth held in localStorage, so rendering and
         data fetching happen on the client after the session is restored. This
         keeps a page reload from bouncing to /login during server render. -->
    <ClientOnly>
      <NuxtLayout>
        <NuxtPage />
      </NuxtLayout>
      <template #fallback>
        <div class="min-h-screen grid place-items-center bg-slate-50">
          <span
            class="inline-flex items-center gap-2 text-sm font-medium text-slate-400"
          >
            <svg class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
              />
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            Cargando…
          </span>
        </div>
      </template>
    </ClientOnly>
  </div>
</template>
