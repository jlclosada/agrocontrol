interface Toast {
  id: number;
  type: 'success' | 'error' | 'info';
  message: string;
}

const toasts = ref<Toast[]>([]);
let seq = 0;

export function useToast() {
  function push(message: string, type: Toast['type'] = 'info', timeout = 3500) {
    const id = ++seq;
    toasts.value.push({ id, type, message });
    if (timeout) {
      setTimeout(() => dismiss(id), timeout);
    }
  }
  function dismiss(id: number) {
    toasts.value = toasts.value.filter((t) => t.id !== id);
  }
  return {
    toasts,
    dismiss,
    success: (m: string) => push(m, 'success'),
    error: (m: string) => push(m, 'error'),
    info: (m: string) => push(m, 'info'),
  };
}
