import { useAuthStore } from '~/stores/auth';

/**
 * Restores the persisted session (tokens → user + cooperative) before the app
 * renders, so a full page reload keeps the user logged in instead of bouncing
 * to /login. Runs only on the client because the session lives in localStorage.
 */
export default defineNuxtPlugin(async () => {
  const auth = useAuthStore();
  await auth.restoreSession();
});
