import { useAuthStore } from '~/stores/auth';

export default defineNuxtRouteMiddleware((to) => {
  // Session lives in localStorage and is restored by plugins/auth.client.ts,
  // so the auth guard only runs on the client.
  if (import.meta.server) return;
  const auth = useAuthStore();
  if (!auth.isAuthenticated && to.path !== '/login') {
    return navigateTo('/login');
  }
  if (auth.isAuthenticated && to.path === '/login') {
    return navigateTo('/');
  }
});
