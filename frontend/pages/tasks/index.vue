<script setup lang="ts">
import { useAuthStore } from '~/stores/auth';
import type {
  Crop,
  Paginated,
  Parcel,
  Task,
  TaskMetrics,
  TaskPriority,
  TaskStatus,
} from '~/types/api';

const api = useApi();
const toast = useToast();
const auth = useAuthStore();
const { date } = useFormat();

const {
  data: tasksData,
  pending,
  refresh,
} = await useAsyncData('tasks', () => api.get<Paginated<Task>>('/tasks/'));
const { data: metrics, refresh: refreshMetrics } = await useAsyncData(
  'tasks-metrics',
  () => api.get<TaskMetrics>('/tasks/metrics/'),
);
const { data: parcels } = await useAsyncData('tasks-parcels', () =>
  api.get<Paginated<Parcel>>('/parcels/'),
);
const { data: crops } = await useAsyncData('tasks-crops', () =>
  api.get<Paginated<Crop>>('/crops/'),
);

const CATEGORIES = [
  { value: 'SOWING', label: 'Siembra' },
  { value: 'FERTILIZATION', label: 'Abonado' },
  { value: 'IRRIGATION', label: 'Riego' },
  { value: 'TREATMENT', label: 'Tratamiento fitosanitario' },
  { value: 'PRUNING', label: 'Poda' },
  { value: 'HARVEST', label: 'Cosecha' },
  { value: 'MAINTENANCE', label: 'Mantenimiento' },
  { value: 'OTHER', label: 'Otro' },
];
const PRIORITIES = [
  { value: 'LOW', label: 'Baja' },
  { value: 'MEDIUM', label: 'Media' },
  { value: 'HIGH', label: 'Alta' },
];

interface Column {
  value: TaskStatus;
  label: string;
  /** Solid accent color (header bar, dot, drag ring). */
  accent: string;
  dot: string;
  bar: string;
  ring: string;
  headBg: string;
  headText: string;
  headBorder: string;
  badge: string;
  colBg: string;
  dropBg: string;
  stripe: string;
  icon: string;
}
const STATUSES: Column[] = [
  {
    value: 'TODO',
    label: 'Pendiente',
    accent: 'slate',
    dot: 'bg-slate-400',
    bar: 'bg-slate-400',
    ring: 'ring-slate-400',
    headBg: 'bg-slate-100',
    headText: 'text-slate-600',
    headBorder: 'border-slate-200',
    badge: 'bg-slate-200 text-slate-700',
    colBg: 'bg-slate-50/70 border-slate-200',
    dropBg: 'bg-slate-100',
    stripe: 'bg-slate-300',
    icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2',
  },
  {
    value: 'IN_PROGRESS',
    label: 'En curso',
    accent: 'blue',
    dot: 'bg-blue-500',
    bar: 'bg-blue-500',
    ring: 'ring-blue-400',
    headBg: 'bg-blue-50',
    headText: 'text-blue-700',
    headBorder: 'border-blue-200',
    badge: 'bg-blue-100 text-blue-700',
    colBg: 'bg-blue-50/40 border-blue-200',
    dropBg: 'bg-blue-100/70',
    stripe: 'bg-blue-500',
    icon: 'M13 10V3L4 14h7v7l9-11h-7z',
  },
  {
    value: 'BLOCKED',
    label: 'Bloqueada',
    accent: 'red',
    dot: 'bg-red-500',
    bar: 'bg-red-500',
    ring: 'ring-red-400',
    headBg: 'bg-red-50',
    headText: 'text-red-700',
    headBorder: 'border-red-200',
    badge: 'bg-red-100 text-red-700',
    colBg: 'bg-red-50/40 border-red-200',
    dropBg: 'bg-red-100/70',
    stripe: 'bg-red-500',
    icon: 'M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z',
  },
  {
    value: 'DONE',
    label: 'Completada',
    accent: 'emerald',
    dot: 'bg-emerald-500',
    bar: 'bg-emerald-500',
    ring: 'ring-emerald-400',
    headBg: 'bg-emerald-50',
    headText: 'text-emerald-700',
    headBorder: 'border-emerald-200',
    badge: 'bg-emerald-100 text-emerald-700',
    colBg: 'bg-emerald-50/40 border-emerald-200',
    dropBg: 'bg-emerald-100/70',
    stripe: 'bg-emerald-500',
    icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
  },
];

const parcelOptions = computed(() =>
  (parcels.value?.results ?? []).map((p) => ({ value: p.id, label: p.name })),
);
const cropOptions = computed(() =>
  (crops.value?.results ?? []).map((c) => ({
    value: c.id,
    label: `${c.species} ${c.variety} — ${c.parcel_name}`,
  })),
);
const parcelFormOptions = computed(() => [
  { value: '', label: 'Sin parcela' },
  ...parcelOptions.value,
]);
const cropFormOptions = computed(() => [
  { value: '', label: 'Sin cultivo' },
  ...cropOptions.value,
]);

const priorityBar: Record<TaskPriority, string> = {
  HIGH: 'bg-rose-400',
  MEDIUM: 'bg-amber-400',
  LOW: 'bg-slate-300',
};
const priorityChip: Record<TaskPriority, string> = {
  HIGH: 'bg-rose-50 text-rose-600',
  MEDIUM: 'bg-amber-50 text-amber-600',
  LOW: 'bg-slate-100 text-slate-500',
};
const CATEGORY_ICONS: Record<string, string> = {
  SOWING:
    'M12 2C8 6 8 10 12 14c4-4 4-8 0-12zM4 14c2 2 4 2 6 0M14 14c2 2 4 2 6 0',
  FERTILIZATION:
    'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10',
  IRRIGATION: 'M12 2.69l5.66 5.66a8 8 0 11-11.31 0z',
  TREATMENT:
    'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
  PRUNING:
    'M14.121 14.121L19 19m-7-7l7-7m-7 7l-2.879 2.879M12 12L9.121 9.121m0 0a3 3 0 10-4.243 4.243 3 3 0 004.243-4.243zm6.758-1.758a3 3 0 104.243-4.243 3 3 0 00-4.243 4.243z',
  HARVEST: 'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10',
  MAINTENANCE:
    'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z',
  OTHER:
    'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2',
};

// ---- Search & filters ----
const search = ref('');
const priorityFilter = ref<string>('');
const categoryFilter = ref<string>('');
const parcelFilter = ref<string>('');
const onlyMine = ref(false);
const onlyOverdue = ref(false);

const priorityFilterOptions = computed(() => [
  { value: '', label: 'Todas las prioridades' },
  ...PRIORITIES,
]);
const categoryFilterOptions = computed(() => [
  { value: '', label: 'Todas las categorías' },
  ...CATEGORIES,
]);
const parcelFilterOptions = computed(() => [
  { value: '', label: 'Todas las parcelas' },
  ...parcelOptions.value,
]);

const filteredTasks = computed(() => {
  const q = search.value.trim().toLowerCase();
  return (tasksData.value?.results ?? []).filter((t) => {
    if (priorityFilter.value && t.priority !== priorityFilter.value)
      return false;
    if (categoryFilter.value && t.category !== categoryFilter.value)
      return false;
    if (parcelFilter.value && t.parcel !== parcelFilter.value) return false;
    if (onlyMine.value && !t.assignees.includes(auth.user?.id ?? ''))
      return false;
    if (onlyOverdue.value && !t.is_overdue) return false;
    if (!q) return true;
    return [t.title, t.description, t.parcel_name, t.crop_label]
      .filter(Boolean)
      .some((v) => String(v).toLowerCase().includes(q));
  });
});

function columnTasks(status: TaskStatus) {
  return filteredTasks.value.filter((t) => t.status === status);
}

const hasFilters = computed(
  () =>
    !!search.value ||
    !!priorityFilter.value ||
    !!categoryFilter.value ||
    !!parcelFilter.value ||
    onlyMine.value ||
    onlyOverdue.value,
);
function resetFilters() {
  search.value = '';
  priorityFilter.value = '';
  categoryFilter.value = '';
  parcelFilter.value = '';
  onlyMine.value = false;
  onlyOverdue.value = false;
}

const kpis = computed(() => {
  const rows = tasksData.value?.results ?? [];
  return {
    total: rows.length,
    todo: rows.filter((t) => t.status === 'TODO').length,
    inProgress: rows.filter((t) => t.status === 'IN_PROGRESS').length,
    blocked: rows.filter((t) => t.status === 'BLOCKED').length,
    done: rows.filter((t) => t.status === 'DONE').length,
    overdue: rows.filter((t) => t.is_overdue).length,
  };
});

// ---- Drag & drop ----
const draggingId = ref<string | null>(null);
const dragOverStatus = ref<TaskStatus | null>(null);

function onDragStart(t: Task, e: DragEvent) {
  draggingId.value = t.id;
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', t.id);
  }
}
function onDragEnd() {
  draggingId.value = null;
  dragOverStatus.value = null;
}
function onDragOver(status: TaskStatus, e: DragEvent) {
  e.preventDefault();
  if (e.dataTransfer) e.dataTransfer.dropEffect = 'move';
  if (dragOverStatus.value !== status) dragOverStatus.value = status;
}
function onDrop(status: TaskStatus) {
  const id = draggingId.value;
  dragOverStatus.value = null;
  draggingId.value = null;
  if (!id) return;
  const task = tasksData.value?.results.find((t) => t.id === id);
  if (!task || task.status === status) return;
  moveTask(task, status);
}

// ---- Create modal (quick add) ----
const showForm = ref(false);
const saving = ref(false);
const today = new Date().toISOString().slice(0, 10);

const blank = () => ({
  title: '',
  description: '',
  priority: 'MEDIUM' as TaskPriority,
  category: 'OTHER',
  due_date: '',
  parcel: '',
  crop: '',
  assign_to_me: false,
});
const form = ref(blank());

function openCreate() {
  form.value = blank();
  showForm.value = true;
}

function openDetail(t: Task) {
  navigateTo(`/tasks/${t.id}`);
}

async function submit() {
  if (!form.value.title.trim()) {
    toast.error('El título es obligatorio.');
    return;
  }
  saving.value = true;
  try {
    const payload: Record<string, unknown> = {
      title: form.value.title.trim(),
      description: form.value.description.trim(),
      priority: form.value.priority,
      category: form.value.category,
      parcel: form.value.parcel || null,
      crop: form.value.crop || null,
      assignees: form.value.assign_to_me && auth.user?.id ? [auth.user.id] : [],
    };
    if (form.value.due_date) payload.due_date = form.value.due_date;
    await api.post('/tasks/', payload);
    toast.success('Tarea creada.');
    showForm.value = false;
    await Promise.all([refresh(), refreshMetrics()]);
  } catch {
    toast.error('No se pudo crear la tarea.');
  } finally {
    saving.value = false;
  }
}

async function moveTask(t: Task, status: TaskStatus) {
  if (t.status === status) return;
  const previous = t.status;
  // Optimistic update for a fluid feel.
  t.status = status;
  if (status === 'DONE') t.is_overdue = false;
  try {
    const updated = await api.patch<Task>(`/tasks/${t.id}/`, { status });
    Object.assign(t, updated);
    refreshMetrics();
  } catch {
    t.status = previous;
    toast.error('No se pudo cambiar el estado.');
  }
}

const showDelete = ref(false);
const deleteTarget = ref<Task | null>(null);
const deleting = ref(false);
function askDelete(t: Task) {
  deleteTarget.value = t;
  showDelete.value = true;
}
async function confirmDelete() {
  if (!deleteTarget.value) return;
  deleting.value = true;
  try {
    await api.del(`/tasks/${deleteTarget.value.id}/`);
    toast.success('Tarea eliminada.');
    showDelete.value = false;
    deleteTarget.value = null;
    await Promise.all([refresh(), refreshMetrics()]);
  } catch {
    toast.error('No se pudo eliminar la tarea.');
  } finally {
    deleting.value = false;
  }
}

// Reset crop when parcel changes and crop doesn't belong to it.
watch(
  () => form.value.parcel,
  (p) => {
    if (!p) return;
    const c = crops.value?.results?.find((x) => x.id === form.value.crop);
    if (c && c.parcel !== p) form.value.crop = '';
  },
);
</script>

<template>
  <div class="p-6 lg:p-8 space-y-6 w-full">
    <PageHeader
      title="Tareas"
      subtitle="Planifica y organiza las labores del equipo por estado, prioridad y parcela"
    >
      <template #actions>
        <button
          class="text-sm px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 transition"
          @click="refresh()"
        >
          Refrescar
        </button>
        <button
          class="text-sm px-3 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition shadow-glow"
          @click="openCreate"
        >
          + Nueva tarea
        </button>
      </template>
    </PageHeader>

    <!-- KPI summary -->
    <div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
      <StatCard label="Total" :value="kpis.total" tone="brand" />
      <StatCard label="Pendientes" :value="kpis.todo" tone="amber" />
      <StatCard label="En curso" :value="kpis.inProgress" tone="sky" />
      <StatCard label="Bloqueadas" :value="kpis.blocked" tone="violet" />
      <StatCard label="Completadas" :value="kpis.done" tone="brand" />
      <StatCard label="Vencidas" :value="kpis.overdue" tone="red" />
    </div>

    <!-- Professional metrics strip -->
    <div
      v-if="metrics"
      class="grid grid-cols-2 lg:grid-cols-4 gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
    >
      <!-- Completion rate with ring -->
      <div class="flex items-center gap-3">
        <div class="relative w-14 h-14 shrink-0">
          <svg class="w-14 h-14 -rotate-90" viewBox="0 0 36 36">
            <circle
              cx="18"
              cy="18"
              r="15.9155"
              fill="none"
              stroke="currentColor"
              stroke-width="3"
              class="text-slate-100"
            />
            <circle
              cx="18"
              cy="18"
              r="15.9155"
              fill="none"
              stroke="currentColor"
              stroke-width="3"
              stroke-linecap="round"
              class="text-emerald-500 transition-all duration-700"
              :stroke-dasharray="`${metrics.completion_rate}, 100`"
            />
          </svg>
          <span
            class="absolute inset-0 grid place-items-center text-xs font-bold text-slate-700"
          >
            {{ Math.round(metrics.completion_rate) }}%
          </span>
        </div>
        <div>
          <p class="text-xs text-slate-400 font-medium">Tasa de finalización</p>
          <p class="text-sm font-semibold text-slate-700">
            {{ metrics.done }} de {{ metrics.total }} completadas
          </p>
        </div>
      </div>

      <!-- Avg cycle time -->
      <div
        class="flex items-center gap-3 lg:border-l lg:border-slate-100 lg:pl-4"
      >
        <span
          class="w-10 h-10 shrink-0 rounded-xl grid place-items-center bg-sky-50 text-sky-600"
        >
          <svg
            class="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </span>
        <div>
          <p class="text-xs text-slate-400 font-medium">Ciclo medio</p>
          <p class="text-sm font-semibold text-slate-700">
            {{
              metrics.avg_cycle_days != null
                ? `${metrics.avg_cycle_days} días`
                : '—'
            }}
          </p>
        </div>
      </div>

      <!-- Due soon -->
      <div
        class="flex items-center gap-3 lg:border-l lg:border-slate-100 lg:pl-4"
      >
        <span
          class="w-10 h-10 shrink-0 rounded-xl grid place-items-center bg-amber-50 text-amber-600"
        >
          <svg
            class="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </span>
        <div>
          <p class="text-xs text-slate-400 font-medium">Vencen pronto</p>
          <p class="text-sm font-semibold text-slate-700">
            {{ metrics.due_soon }} en 3 días · {{ metrics.overdue }} vencidas
          </p>
        </div>
      </div>

      <!-- Throughput -->
      <div
        class="flex items-center gap-3 lg:border-l lg:border-slate-100 lg:pl-4"
      >
        <span
          class="w-10 h-10 shrink-0 rounded-xl grid place-items-center bg-violet-50 text-violet-600"
        >
          <svg
            class="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
            />
          </svg>
        </span>
        <div>
          <p class="text-xs text-slate-400 font-medium">Productividad</p>
          <p class="text-sm font-semibold text-slate-700">
            {{ metrics.completed_7d }} en 7 d · {{ metrics.completed_30d }} en
            30 d
          </p>
        </div>
      </div>
    </div>

    <!-- Search & filters toolbar -->
    <div class="flex items-center flex-wrap gap-2.5">
      <UiSearchInput
        v-model="search"
        placeholder="Buscar tarea, parcela o cultivo…"
        class="w-full sm:w-72"
      />
      <UiFilterSelect
        v-model="priorityFilter"
        :options="priorityFilterOptions"
        icon="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
        class="w-48"
      />
      <UiFilterSelect
        v-model="categoryFilter"
        :options="categoryFilterOptions"
        icon="M7 7h.01M7 3h5a1.99 1.99 0 011.414.586l7 7a2 2 0 010 2.828l-5 5a2 2 0 01-2.828 0l-7-7A1.99 1.99 0 014 9V5a2 2 0 012-2z"
        class="w-52"
      />
      <UiFilterSelect
        v-model="parcelFilter"
        :options="parcelFilterOptions"
        icon="M4 6h16M4 12h16M4 18h16"
        class="w-48"
      />
      <button
        class="inline-flex items-center gap-1.5 text-sm px-3 py-2 rounded-lg border transition"
        :class="
          onlyMine
            ? 'border-brand-300 bg-brand-50 text-brand-700'
            : 'border-slate-200 bg-white text-slate-500 hover:bg-slate-50'
        "
        @click="onlyMine = !onlyMine"
      >
        Mis tareas
      </button>
      <button
        class="inline-flex items-center gap-1.5 text-sm px-3 py-2 rounded-lg border transition"
        :class="
          onlyOverdue
            ? 'border-red-300 bg-red-50 text-red-600'
            : 'border-slate-200 bg-white text-slate-500 hover:bg-slate-50'
        "
        @click="onlyOverdue = !onlyOverdue"
      >
        Vencidas
      </button>
      <button
        v-if="hasFilters"
        class="inline-flex items-center gap-1.5 text-sm px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-500 transition"
        @click="resetFilters"
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
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
        Limpiar
      </button>
    </div>

    <!-- Board -->
    <div v-if="pending"><UiSkeleton :rows="3" :cols="4" /></div>
    <div v-else class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4 items-start">
      <section
        v-for="col in STATUSES"
        :key="col.value"
        class="flex flex-col rounded-2xl border transition-all duration-200 overflow-hidden"
        :class="
          dragOverStatus === col.value
            ? `${col.dropBg} ring-2 ${col.ring} border-transparent shadow-md`
            : col.colBg
        "
        @dragover="onDragOver(col.value, $event)"
        @drop="onDrop(col.value)"
        @dragleave="dragOverStatus = null"
      >
        <!-- Colored column header -->
        <div
          class="flex items-center justify-between px-3 py-2.5 border-b"
          :class="[col.headBg, col.headBorder]"
        >
          <div class="flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full" :class="col.dot" />
            <h3 class="text-sm font-bold tracking-tight" :class="col.headText">
              {{ col.label }}
            </h3>
          </div>
          <span
            class="text-xs font-bold rounded-full px-2 py-0.5 min-w-[1.5rem] text-center"
            :class="col.badge"
          >
            {{ columnTasks(col.value).length }}
          </span>
        </div>

        <!-- Cards -->
        <TransitionGroup
          tag="div"
          name="card"
          class="space-y-2.5 min-h-[3rem] relative p-2.5"
        >
          <article
            v-for="t in columnTasks(col.value)"
            :key="t.id"
            draggable="true"
            class="ticket group relative bg-white rounded-lg border border-slate-200 shadow-sm cursor-grab active:cursor-grabbing select-none transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5"
            :class="
              draggingId === t.id
                ? 'opacity-70 scale-[0.98] rotate-[1.2deg] shadow-xl ring-2 ' +
                  col.ring
                : ''
            "
            @dragstart="onDragStart(t, $event)"
            @dragend="onDragEnd"
            @click="openDetail(t)"
          >
            <!-- Status stripe (left edge) -->
            <span
              class="absolute left-0 top-0 bottom-0 w-1 rounded-l-lg"
              :class="col.stripe"
            />

            <!-- Ticket header: id + priority + delete -->
            <div
              class="flex items-center gap-2 px-3 pt-2.5 pb-1.5 border-b border-dashed border-slate-100"
            >
              <span
                class="font-mono text-[10px] font-semibold text-slate-400 tracking-wider"
              >
                #{{ t.id.slice(0, 6).toUpperCase() }}
              </span>
              <span
                class="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wide px-1.5 py-0.5 rounded"
                :class="priorityChip[t.priority]"
              >
                <span
                  class="w-1.5 h-1.5 rounded-full"
                  :class="priorityBar[t.priority]"
                />
                {{ t.priority_display }}
              </span>
              <button
                class="ml-auto opacity-0 group-hover:opacity-100 transition text-slate-300 hover:text-red-500 shrink-0"
                title="Eliminar"
                @click.stop="askDelete(t)"
              >
                <svg
                  class="w-3.5 h-3.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
              </button>
            </div>

            <!-- Ticket body -->
            <div class="px-3 py-2.5">
              <div class="flex items-start gap-2">
                <span
                  class="mt-0.5 w-7 h-7 shrink-0 rounded-md grid place-items-center bg-slate-50 text-slate-500 ring-1 ring-slate-100"
                  :title="t.category_display"
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
                      :d="CATEGORY_ICONS[t.category] ?? CATEGORY_ICONS.OTHER"
                    />
                  </svg>
                </span>
                <p
                  class="text-sm font-semibold text-slate-800 leading-snug line-clamp-2"
                >
                  {{ t.title }}
                </p>
              </div>
              <p
                v-if="t.parcel_name || t.crop_label"
                class="text-xs text-slate-400 mt-1.5 truncate flex items-center gap-1"
              >
                <svg
                  class="w-3 h-3 shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M17.657 16.657L13.414 20.9a2 2 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                  />
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                </svg>
                {{ t.crop_label || t.parcel_name }}
              </p>
            </div>

            <!-- Ticket footer: meta -->
            <div
              class="flex items-center gap-2 px-3 py-2 border-t border-dashed border-slate-100 bg-slate-50/50 rounded-b-lg"
            >
              <span
                v-if="t.due_date"
                class="inline-flex items-center gap-1 text-[11px] font-medium px-1.5 py-0.5 rounded"
                :class="
                  t.is_overdue
                    ? 'text-red-600 bg-red-50 ring-1 ring-red-100'
                    : 'text-slate-500'
                "
              >
                <svg
                  class="w-3.5 h-3.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                  />
                </svg>
                {{ date(t.due_date) }}
              </span>
              <span
                v-if="t.activity_count"
                class="inline-flex items-center gap-1 text-[11px] text-slate-400"
                :title="`${t.activity_count} movimientos auditados`"
              >
                <svg
                  class="w-3.5 h-3.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                {{ t.activity_count }}
              </span>
              <span
                v-if="t.assignees_detail?.length"
                class="ml-auto flex items-center -space-x-2"
                :title="t.assignees_detail.map((a) => a.name).join(', ')"
              >
                <span
                  v-for="a in t.assignees_detail.slice(0, 3)"
                  :key="a.id"
                  class="w-6 h-6 rounded-full bg-gradient-to-br from-brand-400 to-brand-600 text-white grid place-items-center text-[10px] font-semibold ring-2 ring-white shadow-sm"
                >
                  {{ a.initials }}
                </span>
                <span
                  v-if="t.assignees_detail.length > 3"
                  class="w-6 h-6 rounded-full bg-slate-200 text-slate-600 grid place-items-center text-[10px] font-semibold ring-2 ring-white shadow-sm"
                >
                  +{{ t.assignees_detail.length - 3 }}
                </span>
              </span>
              <span v-else class="ml-auto text-[11px] text-slate-300 italic">
                Sin asignar
              </span>
            </div>
          </article>
        </TransitionGroup>

        <!-- Empty / drop hint -->
        <div
          v-if="!columnTasks(col.value).length"
          class="flex flex-col items-center justify-center gap-1 text-center rounded-xl border-2 border-dashed py-7 px-3 mx-2.5 mb-2.5 transition-colors"
          :class="
            dragOverStatus === col.value
              ? `${col.ring} border-current ${col.headText}`
              : 'border-slate-200 text-slate-300'
          "
        >
          <svg
            class="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              :d="col.icon"
            />
          </svg>
          <span class="text-[11px] font-medium">
            {{ dragOverStatus === col.value ? 'Suelta aquí' : 'Sin tareas' }}
          </span>
        </div>

        <button
          v-if="col.value === 'TODO'"
          class="mx-2.5 mb-2.5 text-sm text-slate-400 hover:text-brand-600 hover:bg-white rounded-xl border border-dashed border-slate-200 hover:border-brand-300 py-2.5 transition inline-flex items-center justify-center gap-1.5"
          @click="openCreate"
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
              d="M12 4v16m8-8H4"
            />
          </svg>
          Añadir tarea
        </button>
      </section>
    </div>

    <EmptyState
      v-if="!pending && !tasksData?.results?.length"
      title="Sin tareas"
      message="Crea tu primera tarea para empezar a planificar las labores."
    >
      <template #action>
        <button
          class="text-sm px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition"
          @click="openCreate"
        >
          + Nueva tarea
        </button>
      </template>
    </EmptyState>

    <!-- Create modal -->
    <UiModal v-model="showForm" title="Nueva tarea">
      <div class="space-y-4">
        <UiField label="Título" required>
          <UiInput
            v-model="form.title"
            placeholder="Ej. Abonar parcela La Vega"
          />
        </UiField>
        <UiField label="Descripción">
          <UiTextarea
            v-model="form.description"
            placeholder="Detalles, indicaciones, materiales…"
          />
        </UiField>
        <div class="grid grid-cols-2 gap-4">
          <UiField label="Categoría">
            <UiSelect v-model="form.category" :options="CATEGORIES" />
          </UiField>
          <UiField label="Prioridad">
            <UiSelect v-model="form.priority" :options="PRIORITIES" />
          </UiField>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <UiField label="Fecha límite">
            <UiInput v-model="form.due_date" type="date" :min="today" />
          </UiField>
          <UiField label="Parcela">
            <UiSelect v-model="form.parcel" :options="parcelFormOptions" />
          </UiField>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <UiField label="Cultivo">
            <UiSelect v-model="form.crop" :options="cropFormOptions" />
          </UiField>
          <div></div>
        </div>
        <label class="flex items-center gap-2 text-sm text-slate-600">
          <input
            v-model="form.assign_to_me"
            type="checkbox"
            class="rounded border-slate-300 text-brand-600 focus:ring-brand-500"
          />
          Asignármela a mí
        </label>
      </div>

      <template #footer>
        <button
          class="text-sm px-4 py-2 rounded-lg border border-slate-200 hover:bg-slate-50 transition"
          @click="showForm = false"
        >
          Cancelar
        </button>
        <button
          class="text-sm px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition disabled:opacity-50"
          :disabled="saving"
          @click="submit"
        >
          {{ saving ? 'Guardando…' : 'Crear tarea' }}
        </button>
      </template>
    </UiModal>

    <!-- Delete confirmation -->
    <UiModal v-model="showDelete" title="Eliminar tarea">
      <p class="text-sm text-slate-600">
        ¿Seguro que quieres eliminar
        <strong>{{ deleteTarget?.title }}</strong
        >? Esta acción no se puede deshacer.
      </p>
      <template #footer>
        <button
          class="text-sm px-4 py-2 rounded-lg border border-slate-200 hover:bg-slate-50 transition"
          @click="showDelete = false"
        >
          Cancelar
        </button>
        <button
          class="text-sm px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white transition disabled:opacity-50"
          :disabled="deleting"
          @click="confirmDelete"
        >
          {{ deleting ? 'Eliminando…' : 'Eliminar' }}
        </button>
      </template>
    </UiModal>
  </div>
</template>

<style scoped>
/* Smooth Kanban card transitions (enter/leave/reorder). */
.card-move,
.card-enter-active,
.card-leave-active {
  transition:
    transform 0.28s cubic-bezier(0.22, 1, 0.36, 1),
    opacity 0.22s ease;
}
.card-enter-from {
  opacity: 0;
  transform: translateY(8px) scale(0.97);
}
.card-leave-to {
  opacity: 0;
  transform: scale(0.95);
}
/* Keep leaving items out of layout flow so siblings glide into place. */
.card-leave-active {
  position: absolute;
  width: calc(100% - 0px);
}

@media (prefers-reduced-motion: reduce) {
  .card-move,
  .card-enter-active,
  .card-leave-active {
    transition: none;
  }
}
</style>
