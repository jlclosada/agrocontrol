/**
 * Shared formatting helpers for the Spanish locale.
 */
export function useFormat() {
  const currency = (value: string | number | null | undefined) => {
    const n = typeof value === 'number' ? value : parseFloat(value ?? '0');
    return (Number.isFinite(n) ? n : 0).toLocaleString('es-ES', {
      style: 'currency',
      currency: 'EUR',
    });
  };

  const number = (value: string | number | null | undefined, decimals = 0) => {
    const n = typeof value === 'number' ? value : parseFloat(value ?? '0');
    return (Number.isFinite(n) ? n : 0).toLocaleString('es-ES', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  };

  const date = (value: string | null | undefined) => {
    if (!value) return '—';
    return new Date(value).toLocaleDateString('es-ES', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  };

  const dateTime = (value: string | null | undefined) => {
    if (!value) return '—';
    return new Date(value).toLocaleString('es-ES', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return { currency, number, date, dateTime };
}
