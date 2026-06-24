import { useAuthStore } from '~/stores/auth';

/**
 * Thin typed wrapper around $fetch that injects the JWT access token and the
 * active cooperative header, and transparently refreshes expired tokens.
 */
export function useApi() {
  const config = useRuntimeConfig();
  const auth = useAuthStore();
  const baseURL = config.public.apiBase;

  async function request<T>(path: string, options: any = {}): Promise<T> {
    const headers: Record<string, string> = { ...(options.headers || {}) };
    if (auth.accessToken) headers.Authorization = `Bearer ${auth.accessToken}`;
    if (auth.cooperativeSlug) headers['X-Cooperative'] = auth.cooperativeSlug;

    try {
      return await $fetch<T>(path, { baseURL, ...options, headers });
    } catch (err: any) {
      if (err?.response?.status === 401 && auth.refreshToken) {
        await auth.refresh();
        headers.Authorization = `Bearer ${auth.accessToken}`;
        return await $fetch<T>(path, { baseURL, ...options, headers });
      }
      throw err;
    }
  }

  return {
    get: <T>(path: string, query?: Record<string, any>) =>
      request<T>(path, { method: 'GET', query }),
    post: <T>(path: string, body?: any) =>
      request<T>(path, { method: 'POST', body }),
    patch: <T>(path: string, body?: any) =>
      request<T>(path, { method: 'PATCH', body }),
    del: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
    async download(path: string, filename: string) {
      const headers: Record<string, string> = {};
      if (auth.accessToken)
        headers.Authorization = `Bearer ${auth.accessToken}`;
      if (auth.cooperativeSlug) headers['X-Cooperative'] = auth.cooperativeSlug;
      const blob = await $fetch<Blob>(path, {
        baseURL,
        responseType: 'blob',
        headers,
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    },
  };
}
