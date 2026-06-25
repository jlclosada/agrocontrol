<script setup lang="ts">
import { useAuthStore } from '~/stores/auth';
import type {
  Crop,
  Member,
  Paginated,
  Parcel,
  Task,
  TaskActivity,
  TaskPriority,
  TaskStatus,
} from '~/types/api';

const route = useRoute();
const router = useRouter();
const api = useApi();
const toast = useToast();
const auth = useAuthStore();
const { date, dateTime } = useFormat();

const taskId = route.params.id as string;

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

interface StatusMeta {
  value: TaskStatus;
  label: string;
  dot: string;
  text: string;
  soft: string;
  ring: string;
}
const STATUS_FLOW: StatusMeta[] = [
  {
    value: 'TODO',
    label: 'Pendiente',
    dot: 'bg-slate-400',
    text: 'text-slate-600',
    soft: 'bg-slate-100',
    ring: 'ring-slate-300',
  },
  {
    value: 'IN_PROGRESS',
    label: 'En curso',
    dot: 'bg-blue-500',
    text: 'text-blue-700',
    soft: 'bg-blue-50',
    ring: 'ring-blue-300',
  },
  {
    value: 'BLOCKED',
    label: 'Bloqueada',
    dot: 'bg-red-500',
    text: 'text-red-700',
    soft: 'bg-red-50',
    ring: 'ring-red-300',
  },
  {
    value: 'DONE',
    label: 'Completada',
    dot: 'bg-emerald-500',
    text: 'text-emerald-700',
    soft: 'bg-emerald-50',
    ring: 'ring-emerald-300',
  },
];
const STATUS_BY: Record<TaskStatus, StatusMeta> = Object.fromEntries(
  STATUS_FLOW.map((s) => [s.value, s]),
) as Record<TaskStatus, StatusMeta>;

const priorityChip: Record<TaskPriority, string> = {
  HIGH: 'bg-rose-50 text-rose-600 ring-rose-100',
  MEDIUM: 'bg-amber-50 text-amber-600 ring-amber-100',
  LOW: 'bg-slate-100 text-slate-500 ring-slate-200',
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
const ACTIVITY_ICONS: Record<string, string> = {
  CREATED: 'M12 4v16m8-8H4',
  STATUS_CHANGED:
    'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15',
  PRIORITY_CHANGED:
    'M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z',
  CATEGORY_CHANGED:
    'M7 7h.01M7 3h5a1.99 1.99 0 011.414.586l7 7a2 2 0 010 2.828l-5 5a2 2 0 01-2.828 0l-7-7A1.99 1.99 0 014 9V5a2 2 0 012-2z',
  ASSIGNED:
    'M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z',
  UNASSIGNED:
    'M13 7a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1zM16 11h6',
  DUE_DATE_CHANGED:
    'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z',
  EDITED:
    'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z',
  COMMENT:
    'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.86 9.86 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z',
};

// ---- Data ----
const {
  data: task,
  pending,
  error,
  refresh: refreshTask,
} = await useAsyncData(`task-${taskId}`, () =>
  api.get<Task>(`/tasks/${taskId}/`),
);
const { data: activity, refresh: refreshActivity } = await useAsyncData(
  `task-activity-${taskId}`,
  () => api.get<TaskActivity[]>(`/tasks/${taskId}/activity/`),
);
const { data: membersData } = await useAsyncData('team-members', () =>
  api.get<Paginated<Member> | Member[]>('/members/'),
);
const { data: parcels } = await useAsyncData('tasks-parcels', () =>
  api.get<Paginated<Parcel>>('/parcels/'),
);
const { data: crops } = await useAsyncData('tasks-crops', () =>
  api.get<Paginated<Crop>>('/crops/'),
);

const members = computed<Member[]>(() => {
  const d = membersData.value as Paginated<Member> | Member[] | null;
  if (!d) return [];
  return (Array.isArray(d) ? d : (d.results ?? [])).filter((m) => m.is_active);
});
const parcelOptions = computed(() => [
  { value: '', label: 'Sin parcela' },
  ...(parcels.value?.results ?? []).map((p) => ({
    value: p.id,
    label: p.name,
  })),
]);
const cropOptions = computed(() => [
  { value: '', label: 'Sin cultivo' },
  ...(crops.value?.results ?? []).map((c) => ({
    value: c.id,
    label: `${c.species} ${c.variety} — ${c.parcel_name}`,
  })),
]);

async function reloadAll() {
  await Promise.all([refreshTask(), refreshActivity()]);
}

// ---- Field auto-save ----
const savingField = ref<string | null>(null);
async function patchTask(payload: Record<string, unknown>, field?: string) {
  savingField.value = field ?? null;
  try {
    await api.patch(`/tasks/${taskId}/`, payload);
    await reloadAll();
  } catch {
    toast.error('No se pudo guardar el cambio.');
  } finally {
    savingField.value = null;
  }
}

function setStatus(status: TaskStatus) {
  if (task.value?.status === status) return;
  patchTask({ status }, 'status');
}

// ---- Title / description editing ----
const editingTitle = ref(false);
const titleDraft = ref('');
function startTitle() {
  titleDraft.value = task.value?.title ?? '';
  editingTitle.value = true;
}
async function saveTitle() {
  const v = titleDraft.value.trim();
  if (!v || v === task.value?.title) {
    editingTitle.value = false;
    return;
  }
  await patchTask({ title: v }, 'title');
  editingTitle.value = false;
}

const editingDesc = ref(false);
const descDraft = ref('');
function startDesc() {
  descDraft.value = task.value?.description ?? '';
  editingDesc.value = true;
}
async function saveDesc() {
  await patchTask({ description: descDraft.value.trim() }, 'description');
  editingDesc.value = false;
}

// ---- Assignees ----
const showAssignees = ref(false);
function isAssigned(userId: string) {
  return (task.value?.assignees ?? []).includes(userId);
}
async function toggleAssignee(userId: string) {
  const current = new Set(task.value?.assignees ?? []);
  if (current.has(userId)) current.delete(userId);
  else current.add(userId);
  await patchTask({ assignees: [...current] }, 'assignees');
}

// ---- Comments & @mentions ----
const commentText = ref('');
const postingComment = ref(false);
const taRef = ref<HTMLTextAreaElement | null>(null);

const mentionOpen = ref(false);
const mentionQuery = ref('');
const mentionStart = ref(-1);
const mentionActive = ref(0);
const mentionMap = reactive<Record<string, string>>({});

const mentionMatches = computed(() => {
  if (!mentionOpen.value) return [];
  const q = mentionQuery.value.toLowerCase();
  return members.value
    .filter((m) => {
      if (!q) return true;
      return (
        m.user_name.toLowerCase().includes(q) ||
        m.user_email.toLowerCase().includes(q)
      );
    })
    .slice(0, 6);
});

function onCommentInput(e: Event) {
  const el = e.target as HTMLTextAreaElement;
  commentText.value = el.value;
  const caret = el.selectionStart ?? el.value.length;
  const upto = el.value.slice(0, caret);
  const at = upto.lastIndexOf('@');
  if (
    at >= 0 &&
    (at === 0 || /\s/.test(upto[at - 1])) &&
    !/\s/.test(upto.slice(at + 1))
  ) {
    mentionOpen.value = true;
    mentionQuery.value = upto.slice(at + 1);
    mentionStart.value = at;
    mentionActive.value = 0;
  } else {
    mentionOpen.value = false;
  }
}

function selectMention(m: Member) {
  const el = taRef.value;
  const caret = el?.selectionStart ?? commentText.value.length;
  const before = commentText.value.slice(0, mentionStart.value);
  const after = commentText.value.slice(caret);
  const inserted = `@${m.user_name} `;
  commentText.value = before + inserted + after;
  mentionMap[m.user] = m.user_name;
  mentionOpen.value = false;
  nextTick(() => {
    const pos = (before + inserted).length;
    el?.focus();
    el?.setSelectionRange(pos, pos);
  });
}

function onCommentKeydown(e: KeyboardEvent) {
  if (!mentionOpen.value || !mentionMatches.value.length) return;
  if (e.key === 'ArrowDown') {
    e.preventDefault();
    mentionActive.value =
      (mentionActive.value + 1) % mentionMatches.value.length;
  } else if (e.key === 'ArrowUp') {
    e.preventDefault();
    mentionActive.value =
      (mentionActive.value - 1 + mentionMatches.value.length) %
      mentionMatches.value.length;
  } else if (e.key === 'Enter') {
    e.preventDefault();
    selectMention(mentionMatches.value[mentionActive.value]);
  } else if (e.key === 'Escape') {
    mentionOpen.value = false;
  }
}

async function postComment() {
  const text = commentText.value.trim();
  if (!text) return;
  postingComment.value = true;
  try {
    const mentions = Object.keys(mentionMap).filter((id) =>
      text.includes(`@${mentionMap[id]}`),
    );
    await api.post(`/tasks/${taskId}/comment/`, { note: text, mentions });
    commentText.value = '';
    Object.keys(mentionMap).forEach((k) => delete mentionMap[k]);
    mentionOpen.value = false;
    await refreshActivity();
  } catch {
    toast.error('No se pudo publicar el comentario.');
  } finally {
    postingComment.value = false;
  }
}

/** Split a comment note into plain and @mention segments for highlighting. */
function commentSegments(c: TaskActivity): { t: string; m: boolean }[] {
  const names = (c.mentions_detail ?? []).map((p) => p.name);
  if (!names.length || !c.note) return [{ t: c.note, m: false }];
  const esc = names
    .map((n) => n.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
    .sort((a, b) => b.length - a.length);
  const re = new RegExp(`@(?:${esc.join('|')})`, 'g');
  const segs: { t: string; m: boolean }[] = [];
  let last = 0;
  let match: RegExpExecArray | null;
  while ((match = re.exec(c.note))) {
    if (match.index > last)
      segs.push({ t: c.note.slice(last, match.index), m: false });
    segs.push({ t: match[0], m: true });
    last = match.index + match[0].length;
  }
  if (last < c.note.length) segs.push({ t: c.note.slice(last), m: false });
  return segs;
}

// ---- Delete ----
const showDelete = ref(false);
const deleting = ref(false);
async function confirmDelete() {
  deleting.value = true;
  try {
    await api.del(`/tasks/${taskId}/`);
    toast.success('Tarea eliminada.');
    router.push('/tasks');
  } catch {
    toast.error('No se pudo eliminar la tarea.');
    deleting.value = false;
  }
}

// Reset crop if it no longer belongs to the selected parcel.
function onParcelChange(parcelId: string) {
  const payload: Record<string, unknown> = { parcel: parcelId || null };
  const c = crops.value?.results?.find((x) => x.id === task.value?.crop);
  if (c && c.parcel !== parcelId) payload.crop = null;
  patchTask(payload, 'parcel');
}

const comments = computed(() =>
  (activity.value ?? []).filter((a) => a.action === 'COMMENT'),
);
const history = computed(() =>
  (activity.value ?? []).filter((a) => a.action !== 'COMMENT'),
);

useHead({
  title: () => (task.value ? `${task.value.title} · Tarea` : 'Tarea'),
});
</script>

<template>
  <div class="p-6 lg:p-8 w-full">
    <!-- Breadcrumb -->
    <div class="flex items-center gap-2 text-sm text-slate-400 mb-4">
      <NuxtLink to="/tasks" class="hover:text-brand-600 transition"
        >Tareas</NuxtLink
      >
      <span>/</span>
      <span class="text-slate-500 font-mono"
        >#{{ taskId.slice(0, 6).toUpperCase() }}</span
      >
    </div>

    <div v-if="pending" class="space-y-4">
      <UiSkeleton :rows="2" :cols="1" />
      <UiSkeleton :rows="4" :cols="2" />
    </div>

    <EmptyState
      v-else-if="error || !task"
      title="No encontrada"
      message="La tarea no existe o no tienes acceso."
    >
      <template #action>
        <NuxtLink
          to="/tasks"
          class="text-sm px-4 py-2 rounded-lg bg-brand-600 text-white"
        >
          Volver al tablero
        </NuxtLink>
      </template>
    </EmptyState>

    <div v-else class="grid lg:grid-cols-3 gap-6 items-start">
      <!-- Main column -->
      <div class="lg:col-span-2 space-y-6">
        <!-- Header card -->
        <div class="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div class="flex items-start gap-3">
            <span
              class="mt-1 w-10 h-10 shrink-0 rounded-xl grid place-items-center bg-brand-50 text-brand-600 ring-1 ring-brand-100"
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
                  :d="CATEGORY_ICONS[task.category] ?? CATEGORY_ICONS.OTHER"
                />
              </svg>
            </span>
            <div class="min-w-0 flex-1">
              <div v-if="editingTitle" class="flex items-center gap-2">
                <UiInput
                  v-model="titleDraft"
                  class="flex-1"
                  @keyup.enter="saveTitle"
                />
                <button
                  class="text-sm px-3 py-2 rounded-lg bg-brand-600 text-white"
                  @click="saveTitle"
                >
                  Guardar
                </button>
                <button
                  class="text-sm px-3 py-2 rounded-lg border border-slate-200"
                  @click="editingTitle = false"
                >
                  Cancelar
                </button>
              </div>
              <h1
                v-else
                class="text-xl font-bold text-slate-800 leading-tight group cursor-text"
                @click="startTitle"
              >
                {{ task.title }}
                <svg
                  class="inline w-4 h-4 text-slate-300 opacity-0 group-hover:opacity-100 transition align-middle ml-1"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                  />
                </svg>
              </h1>
              <div class="flex items-center flex-wrap gap-2 mt-2">
                <span
                  class="inline-flex items-center gap-1.5 text-xs font-semibold px-2 py-1 rounded-md"
                  :class="
                    STATUS_BY[task.status].soft +
                    ' ' +
                    STATUS_BY[task.status].text
                  "
                >
                  <span
                    class="w-1.5 h-1.5 rounded-full"
                    :class="STATUS_BY[task.status].dot"
                  />
                  {{ task.status_display }}
                </span>
                <span
                  class="inline-flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-md ring-1"
                  :class="priorityChip[task.priority]"
                >
                  {{ task.priority_display }}
                </span>
                <span class="text-xs text-slate-400 font-mono"
                  >#{{ taskId.slice(0, 6).toUpperCase() }}</span
                >
              </div>
            </div>
          </div>

          <!-- Status tracker -->
          <div class="mt-6">
            <p
              class="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-2"
            >
              Seguimiento de estado
            </p>
            <div class="flex items-center gap-1.5">
              <template v-for="(s, i) in STATUS_FLOW" :key="s.value">
                <button
                  class="flex-1 group relative"
                  :title="`Marcar como ${s.label}`"
                  @click="setStatus(s.value)"
                >
                  <div
                    class="h-2 rounded-full transition-all duration-300"
                    :class="
                      task.status === s.value
                        ? s.dot
                        : 'bg-slate-200 group-hover:bg-slate-300'
                    "
                  />
                  <span
                    class="mt-1.5 block text-[11px] font-medium text-center transition"
                    :class="task.status === s.value ? s.text : 'text-slate-400'"
                  >
                    {{ s.label }}
                  </span>
                </button>
              </template>
            </div>
          </div>
        </div>

        <!-- Description -->
        <div class="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div class="flex items-center justify-between mb-3">
            <h2 class="text-sm font-semibold text-slate-700">Descripción</h2>
            <button
              v-if="!editingDesc"
              class="text-xs text-brand-600 hover:text-brand-700"
              @click="startDesc"
            >
              Editar
            </button>
          </div>
          <div v-if="editingDesc" class="space-y-2">
            <UiTextarea v-model="descDraft" :rows="5" />
            <div class="flex justify-end gap-2">
              <button
                class="text-sm px-3 py-1.5 rounded-lg border border-slate-200"
                @click="editingDesc = false"
              >
                Cancelar
              </button>
              <button
                class="text-sm px-3 py-1.5 rounded-lg bg-brand-600 text-white"
                @click="saveDesc"
              >
                Guardar
              </button>
            </div>
          </div>
          <p
            v-else-if="task.description"
            class="text-sm text-slate-600 leading-relaxed whitespace-pre-wrap"
          >
            {{ task.description }}
          </p>
          <p v-else class="text-sm text-slate-400 italic">
            Sin descripción. Añade detalles, indicaciones o materiales.
          </p>
        </div>

        <!-- Comments -->
        <div class="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <h2 class="text-sm font-semibold text-slate-700 mb-4">
            Comentarios
            <span class="text-slate-400 font-normal"
              >({{ comments.length }})</span
            >
          </h2>

          <div class="flex gap-3 mb-5">
            <span
              class="w-8 h-8 shrink-0 rounded-full bg-gradient-to-br from-brand-400 to-brand-600 text-white grid place-items-center text-xs font-semibold"
            >
              {{ auth.initials }}
            </span>
            <div class="flex-1">
              <div class="relative">
                <textarea
                  ref="taRef"
                  :value="commentText"
                  :rows="2"
                  placeholder="Escribe un comentario… usa @ para mencionar"
                  class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition resize-y"
                  @input="onCommentInput"
                  @keydown="onCommentKeydown"
                />
                <ul
                  v-if="mentionOpen && mentionMatches.length"
                  class="absolute z-20 left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-lg overflow-hidden"
                >
                  <li
                    v-for="(m, i) in mentionMatches"
                    :key="m.id"
                    class="flex items-center gap-2 px-3 py-2 cursor-pointer text-sm"
                    :class="
                      i === mentionActive ? 'bg-brand-50' : 'hover:bg-slate-50'
                    "
                    @mousedown.prevent="selectMention(m)"
                  >
                    <span
                      class="w-6 h-6 shrink-0 rounded-full bg-gradient-to-br from-brand-400 to-brand-600 text-white grid place-items-center text-[10px] font-semibold"
                    >
                      {{ m.initials }}
                    </span>
                    <span class="font-medium text-slate-700 truncate">{{
                      m.user_name
                    }}</span>
                    <span class="text-xs text-slate-400 truncate ml-auto">{{
                      m.user_email
                    }}</span>
                  </li>
                </ul>
              </div>
              <div class="flex items-center justify-between gap-2 mt-2">
                <p class="text-[11px] text-slate-400">
                  Escribe <span class="font-semibold">@</span> para mencionar a
                  un miembro del equipo
                </p>
                <button
                  class="text-sm px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition disabled:opacity-50"
                  :disabled="postingComment || !commentText.trim()"
                  @click="postComment"
                >
                  {{ postingComment ? 'Publicando…' : 'Comentar' }}
                </button>
              </div>
            </div>
          </div>

          <div v-if="comments.length" class="space-y-4">
            <div v-for="c in comments" :key="c.id" class="flex gap-3">
              <span
                class="w-8 h-8 shrink-0 rounded-full bg-slate-200 text-slate-600 grid place-items-center text-xs font-semibold"
              >
                {{ (c.actor_name || 'S').charAt(0).toUpperCase() }}
              </span>
              <div class="flex-1 bg-slate-50 rounded-xl rounded-tl-sm p-3">
                <div class="flex items-center gap-2 mb-0.5">
                  <span class="text-xs font-semibold text-slate-700">{{
                    c.actor_name || 'Sistema'
                  }}</span>
                  <span class="text-[11px] text-slate-400">{{
                    dateTime(c.created_at)
                  }}</span>
                </div>
                <p class="text-sm text-slate-600 whitespace-pre-wrap">
                  <template v-for="(seg, i) in commentSegments(c)" :key="i"
                    ><span
                      v-if="seg.m"
                      class="font-semibold text-brand-600 bg-brand-50 rounded px-1"
                      >{{ seg.t }}</span
                    ><span v-else>{{ seg.t }}</span></template
                  >
                </p>
              </div>
            </div>
          </div>
          <p v-else class="text-sm text-slate-400 italic">
            Sé el primero en comentar.
          </p>
        </div>

        <!-- Audit timeline -->
        <div class="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <h2 class="text-sm font-semibold text-slate-700 mb-4">
            Historial de auditoría
            <span class="text-slate-400 font-normal"
              >({{ history.length }})</span
            >
          </h2>
          <ol v-if="history.length" class="relative space-y-4">
            <li
              v-for="(a, i) in history"
              :key="a.id"
              class="relative flex gap-3 pl-6"
            >
              <span
                v-if="i < history.length - 1"
                class="absolute left-[9px] top-6 bottom-[-16px] w-px bg-slate-200"
              />
              <span
                class="absolute left-0 top-0.5 w-[18px] h-[18px] rounded-full grid place-items-center ring-2 ring-white"
                :class="
                  a.action === 'CREATED'
                    ? 'bg-emerald-100 text-emerald-600'
                    : a.action === 'STATUS_CHANGED'
                      ? 'bg-blue-100 text-blue-600'
                      : a.action === 'UNASSIGNED'
                        ? 'bg-red-100 text-red-600'
                        : 'bg-slate-100 text-slate-500'
                "
              >
                <svg
                  class="w-2.5 h-2.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2.5"
                    :d="ACTIVITY_ICONS[a.action] ?? ACTIVITY_ICONS.EDITED"
                  />
                </svg>
              </span>
              <div class="min-w-0 flex-1">
                <p class="text-sm text-slate-700 leading-snug">
                  <template v-if="a.action === 'CREATED'"
                    >Tarea creada</template
                  >
                  <template v-else-if="a.action === 'ASSIGNED'">
                    Asignada a
                    <span class="font-semibold">{{ a.to_value }}</span>
                  </template>
                  <template v-else-if="a.action === 'UNASSIGNED'">
                    Desasignada de
                    <span class="font-semibold">{{ a.from_value }}</span>
                  </template>
                  <template v-else>
                    <span class="font-medium">{{ a.field }}</span>
                    <span class="text-slate-400"> · </span>
                    <span class="text-slate-500 line-through">{{
                      a.from_value
                    }}</span>
                    <svg
                      class="inline w-3.5 h-3.5 mx-0.5 text-slate-300"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M14 5l7 7m0 0l-7 7m7-7H3"
                      />
                    </svg>
                    <span class="font-semibold text-slate-700">{{
                      a.to_value
                    }}</span>
                  </template>
                </p>
                <p class="text-[11px] text-slate-400 mt-0.5">
                  {{ a.actor_name || 'Sistema' }} · {{ dateTime(a.created_at) }}
                </p>
              </div>
            </li>
          </ol>
          <p v-else class="text-sm text-slate-400 italic">
            Sin movimientos registrados.
          </p>
        </div>
      </div>

      <!-- Sidebar -->
      <aside class="space-y-4 lg:sticky lg:top-6">
        <!-- Properties -->
        <div
          class="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-4"
        >
          <div class="flex items-center justify-between">
            <h2 class="text-sm font-semibold text-slate-700">Propiedades</h2>
            <span
              v-if="savingField"
              class="text-[11px] text-slate-400 animate-pulse"
              >Guardando…</span
            >
          </div>

          <UiField label="Estado">
            <UiSelect
              :model-value="task.status"
              :options="
                STATUS_FLOW.map((s) => ({ value: s.value, label: s.label }))
              "
              @update:model-value="(v: TaskStatus) => setStatus(v)"
            />
          </UiField>
          <div class="grid grid-cols-2 gap-3">
            <UiField label="Prioridad">
              <UiSelect
                :model-value="task.priority"
                :options="PRIORITIES"
                @update:model-value="
                  (v: string) => patchTask({ priority: v }, 'priority')
                "
              />
            </UiField>
            <UiField label="Categoría">
              <UiSelect
                :model-value="task.category"
                :options="CATEGORIES"
                @update:model-value="
                  (v: string) => patchTask({ category: v }, 'category')
                "
              />
            </UiField>
          </div>
          <UiField label="Fecha límite">
            <UiInput
              :model-value="task.due_date || ''"
              type="date"
              @update:model-value="
                (v: string) => patchTask({ due_date: v || null }, 'due_date')
              "
            />
          </UiField>
          <p
            v-if="task.is_overdue"
            class="text-xs text-red-600 flex items-center gap-1 -mt-2"
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
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            Vencida
          </p>
          <UiField label="Parcela">
            <UiSelect
              :model-value="task.parcel || ''"
              :options="parcelOptions"
              @update:model-value="onParcelChange"
            />
          </UiField>
          <UiField label="Cultivo">
            <UiSelect
              :model-value="task.crop || ''"
              :options="cropOptions"
              @update:model-value="
                (v: string) => patchTask({ crop: v || null }, 'crop')
              "
            />
          </UiField>
        </div>

        <!-- Assignees -->
        <div class="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
          <div class="flex items-center justify-between mb-3">
            <h2 class="text-sm font-semibold text-slate-700">Responsables</h2>
            <button
              class="text-xs text-brand-600 hover:text-brand-700"
              @click="showAssignees = !showAssignees"
            >
              {{ showAssignees ? 'Cerrar' : 'Gestionar' }}
            </button>
          </div>

          <div v-if="task.assignees_detail.length" class="flex flex-wrap gap-2">
            <span
              v-for="a in task.assignees_detail"
              :key="a.id"
              class="inline-flex items-center gap-1.5 bg-slate-50 rounded-full pl-1 pr-2.5 py-1 ring-1 ring-slate-100"
            >
              <span
                class="w-6 h-6 rounded-full bg-gradient-to-br from-brand-400 to-brand-600 text-white grid place-items-center text-[10px] font-semibold"
              >
                {{ a.initials }}
              </span>
              <span class="text-xs text-slate-600">{{ a.name }}</span>
            </span>
          </div>
          <p v-else class="text-sm text-slate-400 italic">Sin asignar</p>

          <!-- Member picker -->
          <div
            v-if="showAssignees"
            class="mt-4 pt-4 border-t border-slate-100 space-y-1 max-h-64 overflow-auto"
          >
            <button
              v-for="m in members"
              :key="m.id"
              class="w-full flex items-center gap-2.5 p-2 rounded-lg hover:bg-slate-50 transition text-left"
              @click="toggleAssignee(m.user)"
            >
              <span
                class="w-7 h-7 shrink-0 rounded-full grid place-items-center text-[10px] font-semibold"
                :class="
                  isAssigned(m.user)
                    ? 'bg-gradient-to-br from-brand-400 to-brand-600 text-white'
                    : 'bg-slate-100 text-slate-500'
                "
              >
                {{ m.initials }}
              </span>
              <span class="min-w-0 flex-1">
                <span class="block text-sm text-slate-700 truncate">{{
                  m.user_name || m.user_email
                }}</span>
                <span class="block text-[11px] text-slate-400">{{
                  m.role_display
                }}</span>
              </span>
              <svg
                v-if="isAssigned(m.user)"
                class="w-4 h-4 text-brand-600 shrink-0"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </button>
            <p v-if="!members.length" class="text-xs text-slate-400 p-2">
              No hay miembros activos.
              <NuxtLink to="/team" class="text-brand-600"
                >Ir al equipo</NuxtLink
              >
            </p>
          </div>
        </div>

        <!-- Metadata -->
        <div
          class="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-2.5"
        >
          <h2 class="text-sm font-semibold text-slate-700 mb-1">Detalles</h2>
          <div class="flex justify-between text-xs">
            <span class="text-slate-400">Creada</span>
            <span class="text-slate-600">{{ dateTime(task.created_at) }}</span>
          </div>
          <div v-if="task.completed_at" class="flex justify-between text-xs">
            <span class="text-slate-400">Completada</span>
            <span class="text-slate-600">{{
              dateTime(task.completed_at)
            }}</span>
          </div>
          <div class="flex justify-between text-xs">
            <span class="text-slate-400">Movimientos</span>
            <span class="text-slate-600">{{ task.activity_count }}</span>
          </div>
        </div>

        <button
          class="w-full text-sm px-4 py-2.5 rounded-xl border border-red-200 text-red-600 hover:bg-red-50 transition inline-flex items-center justify-center gap-2"
          @click="showDelete = true"
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
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
            />
          </svg>
          Eliminar tarea
        </button>
      </aside>
    </div>

    <!-- Delete confirmation -->
    <UiModal v-model="showDelete" title="Eliminar tarea">
      <p class="text-sm text-slate-600">
        ¿Seguro que quieres eliminar
        <strong>{{ task?.title }}</strong
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
