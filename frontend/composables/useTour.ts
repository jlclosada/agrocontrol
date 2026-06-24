/**
 * Guided product tour engine (singleton, module-level state à la useToast).
 *
 * A step can target a DOM element by CSS selector (spotlight + tooltip) or be
 * "centered" (no target → welcome/closing slide). Steps may navigate to a
 * route before being shown. State (completed) persists in localStorage so the
 * welcome prompt only appears for first-time users, but the tour can always be
 * relaunched from the "Ver demo" button.
 */

export interface TourStep {
  /** CSS selector of the element to highlight. Omit for a centered slide. */
  target?: string;
  title: string;
  body: string;
  /** Preferred tooltip placement relative to the target. */
  placement?: 'top' | 'bottom' | 'left' | 'right' | 'auto';
  /** Navigate here before showing the step. */
  route?: string;
  /** Heroicon-style path drawn in the step badge. */
  icon?: string;
}

const STORAGE_KEY = 'agro_tour_done_v1';

// Heroicon outline paths reused across steps.
const ICONS = {
  spark:
    'M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z',
  home: 'M3 12l9-9 9 9M5 10v10h14V10',
  layers: 'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4',
  book: 'M12 6.5C9 4 4 4 4 4v14s5 0 8 2.5M12 6.5C15 4 20 4 20 4v14s-5 0-8 2.5M12 6.5v14',
  chart: 'M3 3v18h18M7 14l3-3 3 3 5-6',
  shield:
    'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
  bell: 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1',
  bolt: 'M13 10V3L4 14h7v7l9-11h-7z',
  cpu: 'M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 7h10v10H7zM10 10h4v4h-4z',
  flag: 'M3 21v-4m0 0V5a2 2 0 012-2h11l-2 4 2 4H5a2 2 0 00-2 2z',
};

const DEFAULT_STEPS: TourStep[] = [
  {
    title: '¡Bienvenido a AgroControl OS! 🌱',
    body: 'Te enseñamos en 60 segundos cómo gestionar tu cooperativa: parcelas, cuaderno de campo, inventario, costes y alertas inteligentes. Pulsa "Siguiente" para empezar.',
    icon: ICONS.spark,
    route: '/',
  },
  {
    target: '[data-tour="brand"]',
    title: 'Tu cooperativa',
    body: 'Aquí ves la identidad de tu cooperativa. Todo —nombre, color y módulos— es configurable desde Ajustes.',
    placement: 'right',
    icon: ICONS.home,
  },
  {
    target: '[data-tour="kpis"]',
    title: 'Indicadores clave',
    body: 'Un vistazo a parcelas, superficie, cultivos y producción. Los números se animan al cargar para destacar los cambios.',
    placement: 'bottom',
    icon: ICONS.chart,
    route: '/',
  },
  {
    target: '[data-tour="economics"]',
    title: 'Economía en tiempo real',
    body: 'Coste, ingresos y beneficio agregados de toda la explotación. El detalle por cultivo está en la sección de Costes.',
    placement: 'bottom',
    icon: ICONS.chart,
  },
  {
    target: '[data-tour="nav-/parcels"]',
    title: 'Parcelas y cultivos',
    body: 'Gestiona fincas, parcelas (con referencia SIGPAC) y los cultivos de cada campaña.',
    placement: 'right',
    icon: ICONS.layers,
  },
  {
    target: '[data-tour="nav-/fieldbook"]',
    title: 'Cuaderno de campo',
    body: 'Registra operaciones y tratamientos fitosanitarios. El stock se descuenta solo (FEFO) y se valida el plazo de seguridad.',
    placement: 'right',
    icon: ICONS.book,
  },
  {
    target: '[data-tour="nav-/inventory"]',
    title: 'Inventario inteligente',
    body: 'Controla productos y lotes con caducidad. Te avisamos antes de quedarte sin stock o de que caduque un lote.',
    placement: 'right',
    icon: ICONS.layers,
  },
  {
    target: '[data-tour="nav-/costs"]',
    title: 'Costes y rentabilidad',
    body: 'Imputación automática de costes y cálculo de rentabilidad por cultivo. Exporta a CSV cuando quieras.',
    placement: 'right',
    icon: ICONS.chart,
  },
  {
    target: '[data-tour="nav-/alerts"]',
    title: 'Alertas que trabajan por ti',
    body: 'Stock bajo, caducidades y plazos de seguridad se evalúan automáticamente y aparecen aquí priorizadas.',
    placement: 'right',
    icon: ICONS.bell,
  },
  {
    target: '[data-tour="nav-/traceability"]',
    title: 'Trazabilidad inmutable',
    body: 'Cada evento queda encadenado con un hash verificable: trazabilidad a prueba de auditorías.',
    placement: 'right',
    icon: ICONS.bolt,
  },
  {
    target: '[data-tour="nav-/agents"]',
    title: 'Agentes de IA',
    body: 'Asistentes especializados que analizan tus datos y te ayudan en las decisiones del día a día.',
    placement: 'right',
    icon: ICONS.cpu,
  },
  {
    target: '[data-tour="user"]',
    title: 'Tu sesión',
    body: 'Tu perfil, rol y acceso a la verificación en dos pasos. Desde aquí también cierras sesión de forma segura.',
    placement: 'top',
    icon: ICONS.shield,
  },
  {
    title: '¡Listo para empezar! 🚀',
    body: 'Ya conoces lo esencial. Puedes relanzar esta demo cuando quieras desde el botón "Ver demo" del menú lateral. ¡A cultivar!',
    icon: ICONS.flag,
  },
];

const active = ref(false);
const stepIndex = ref(0);
const steps = ref<TourStep[]>(DEFAULT_STEPS);
const completed = ref(false);

export function useTour() {
  function hydrate() {
    if (!import.meta.client) return;
    completed.value = localStorage.getItem(STORAGE_KEY) === '1';
  }

  function markCompleted() {
    completed.value = true;
    if (import.meta.client) localStorage.setItem(STORAGE_KEY, '1');
  }

  function start() {
    stepIndex.value = 0;
    active.value = true;
  }

  function next() {
    if (stepIndex.value < steps.value.length - 1) {
      stepIndex.value += 1;
    } else {
      finish();
    }
  }

  function prev() {
    if (stepIndex.value > 0) stepIndex.value -= 1;
  }

  function goTo(i: number) {
    stepIndex.value = Math.min(Math.max(0, i), steps.value.length - 1);
  }

  function skip() {
    active.value = false;
    markCompleted();
  }

  function finish() {
    active.value = false;
    markCompleted();
  }

  const current = computed(() => steps.value[stepIndex.value]);
  const isFirst = computed(() => stepIndex.value === 0);
  const isLast = computed(() => stepIndex.value === steps.value.length - 1);

  return {
    active,
    stepIndex,
    steps,
    completed,
    current,
    isFirst,
    isLast,
    hydrate,
    start,
    next,
    prev,
    goTo,
    skip,
    finish,
    markCompleted,
  };
}
