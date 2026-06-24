/**
 * Generates a full brand color ramp (50–900) from a single base hex color and
 * applies it as CSS variables on :root, so the whole UI re-themes at runtime
 * from the cooperative's configured `primary_color`.
 */

type Rgb = [number, number, number];

// How far each step is mixed toward white (lighter) or black (darker).
// Positive = mix with white, negative = mix with black. 500 is the base color.
const STEPS: Record<number, number> = {
  50: 0.92,
  100: 0.82,
  200: 0.65,
  300: 0.45,
  400: 0.22,
  500: 0,
  600: -0.18,
  700: -0.34,
  800: -0.5,
  900: -0.64,
};

function hexToRgb(hex: string): Rgb | null {
  const m = hex.trim().replace('#', '');
  const full =
    m.length === 3
      ? m
          .split('')
          .map((c) => c + c)
          .join('')
      : m;
  if (full.length !== 6 || /[^0-9a-fA-F]/.test(full)) return null;
  return [
    parseInt(full.slice(0, 2), 16),
    parseInt(full.slice(2, 4), 16),
    parseInt(full.slice(4, 6), 16),
  ];
}

function mix(base: number, target: number, amount: number): number {
  return Math.round(base + (target - base) * amount);
}

function ramp([r, g, b]: Rgb, amount: number): Rgb {
  const target = amount >= 0 ? 255 : 0;
  const a = Math.abs(amount);
  return [mix(r, target, a), mix(g, target, a), mix(b, target, a)];
}

export function useBrandTheme() {
  function apply(primaryColor?: string | null) {
    if (!import.meta.client) return;
    const base = hexToRgb(primaryColor || '#16a34a');
    if (!base) return;
    const root = document.documentElement;
    for (const [shade, amount] of Object.entries(STEPS)) {
      const [r, g, b] = ramp(base, amount);
      root.style.setProperty(`--brand-${shade}`, `${r} ${g} ${b}`);
    }
  }

  return { apply };
}
