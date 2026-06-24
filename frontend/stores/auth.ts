import { defineStore } from 'pinia';
import type {
  Cooperative,
  CooperativeSettings,
  MfaDevice,
  TokenPair,
  User,
} from '~/types/api';

export class MfaRequiredError extends Error {
  constructor() {
    super('mfa_required');
    this.name = 'MfaRequiredError';
  }
}

export const useAuthStore = defineStore('auth', () => {
  const config = useRuntimeConfig();
  const baseURL = config.public.apiBase;

  const accessToken = ref<string | null>(null);
  const refreshToken = ref<string | null>(null);
  const user = ref<User | null>(null);
  const cooperative = ref<Cooperative | null>(null);

  const isAuthenticated = computed(() => !!accessToken.value);
  const cooperativeSlug = computed(() => cooperative.value?.slug ?? null);
  const role = computed(() => cooperative.value?.role ?? null);
  const settings = computed(() => cooperative.value?.settings ?? null);
  const branding = computed(() => ({
    appName:
      settings.value?.brand_name || cooperative.value?.name || 'AgroControl OS',
    tagline: settings.value?.tagline || 'Sistema operativo agrícola',
    emoji: settings.value?.logo_emoji || '🌱',
    color: settings.value?.primary_color || '#16a34a',
  }));
  const initials = computed(() => {
    const u = user.value;
    if (!u) return '··';
    const a = (u.first_name?.[0] ?? u.email?.[0] ?? '').toUpperCase();
    const b = (u.last_name?.[0] ?? u.email?.[1] ?? '').toUpperCase();
    return a + b || '··';
  });

  function persist() {
    if (import.meta.client) {
      localStorage.setItem(
        'agro_auth',
        JSON.stringify({
          access: accessToken.value,
          refresh: refreshToken.value,
          coop: cooperative.value?.slug ?? null,
        }),
      );
    }
  }

  function hydrate() {
    if (!import.meta.client) return;
    const raw = localStorage.getItem('agro_auth');
    if (!raw) return;
    const data = JSON.parse(raw);
    accessToken.value = data.access;
    refreshToken.value = data.refresh;
  }

  function clearTokens() {
    accessToken.value = null;
    refreshToken.value = null;
    user.value = null;
    cooperative.value = null;
    if (import.meta.client) localStorage.removeItem('agro_auth');
  }

  /**
   * Restore a persisted session on app startup: reads the tokens from storage
   * and reloads the user + cooperative. Transparently refreshes an expired
   * access token, and clears everything if the session is no longer valid so
   * the route guard sends the user to /login.
   */
  async function restoreSession() {
    if (!import.meta.client) return;
    hydrate();
    if (!accessToken.value) return;
    try {
      await loadProfile();
      await loadCooperative();
    } catch {
      if (refreshToken.value) {
        try {
          await refresh();
          await loadProfile();
          await loadCooperative();
          return;
        } catch {
          clearTokens();
          return;
        }
      }
      clearTokens();
    }
  }

  async function login(email: string, password: string, otp?: string) {
    let tokens: TokenPair;
    try {
      tokens = await $fetch<TokenPair>('/auth/token/', {
        baseURL,
        method: 'POST',
        body: { email, password, otp: otp ?? '' },
      });
    } catch (err: any) {
      if (err?.response?.status === 401 && err?.response?._data?.mfa_required) {
        throw new MfaRequiredError();
      }
      throw err;
    }
    accessToken.value = tokens.access;
    refreshToken.value = tokens.refresh;
    await loadProfile();
    await loadCooperative();
    persist();
  }

  async function refresh() {
    const tokens = await $fetch<{ access: string }>('/auth/token/refresh/', {
      baseURL,
      method: 'POST',
      body: { refresh: refreshToken.value },
    });
    accessToken.value = tokens.access;
    persist();
  }

  async function loadProfile() {
    user.value = await $fetch<User>('/auth/me/', {
      baseURL,
      headers: { Authorization: `Bearer ${accessToken.value}` },
    });
  }

  async function loadCooperative() {
    const data = await $fetch<{ results: Cooperative[] }>('/cooperatives/', {
      baseURL,
      headers: { Authorization: `Bearer ${accessToken.value}` },
    });
    cooperative.value = data.results?.[0] ?? null;
  }

  async function updateSettings(payload: Partial<CooperativeSettings>) {
    const updated = await $fetch<CooperativeSettings>(
      '/cooperatives/settings/',
      {
        baseURL,
        method: 'PATCH',
        headers: { Authorization: `Bearer ${accessToken.value}` },
        body: payload,
      },
    );
    if (cooperative.value) cooperative.value.settings = updated;
    return updated;
  }

  async function enrollMfa() {
    return await $fetch<{ device_id: string; provisioning_uri: string }>(
      '/auth/mfa/enroll/',
      {
        baseURL,
        method: 'POST',
        headers: { Authorization: `Bearer ${accessToken.value}` },
      },
    );
  }

  async function confirmMfa(deviceId: string, code: string) {
    return await $fetch<MfaDevice>('/auth/mfa/confirm/', {
      baseURL,
      method: 'POST',
      headers: { Authorization: `Bearer ${accessToken.value}` },
      body: { device_id: deviceId, code },
    });
  }

  async function mfaDevices() {
    const data = await $fetch<{ results: MfaDevice[] }>('/auth/mfa/devices/', {
      baseURL,
      headers: { Authorization: `Bearer ${accessToken.value}` },
    });
    return data.results ?? [];
  }

  function logout() {
    accessToken.value = null;
    refreshToken.value = null;
    user.value = null;
    cooperative.value = null;
    if (import.meta.client) localStorage.removeItem('agro_auth');
    navigateTo('/login');
  }

  return {
    accessToken,
    refreshToken,
    user,
    cooperative,
    isAuthenticated,
    cooperativeSlug,
    role,
    settings,
    branding,
    initials,
    login,
    refresh,
    logout,
    hydrate,
    restoreSession,
    loadProfile,
    loadCooperative,
    updateSettings,
    enrollMfa,
    confirmMfa,
    mfaDevices,
  };
});
