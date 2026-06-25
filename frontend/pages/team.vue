<script setup lang="ts">
import { useAuthStore } from '~/stores/auth';
import type { Member, Paginated } from '~/types/api';

const api = useApi();
const toast = useToast();
const auth = useAuthStore();
const { date } = useFormat();

const isAdmin = computed(() =>
  ['SUPERADMIN', 'COOP_ADMIN'].includes(auth.role ?? ''),
);

const ROLES = [
  { value: 'COOP_ADMIN', label: 'Admin cooperativa' },
  { value: 'AGRONOMIST', label: 'Técnico agrónomo' },
  { value: 'FARMER', label: 'Agricultor' },
  { value: 'OPERATOR', label: 'Operario' },
  { value: 'AUDITOR', label: 'Auditor' },
];
const ROLE_TONE: Record<string, string> = {
  SUPERADMIN: 'violet',
  COOP_ADMIN: 'violet',
  AGRONOMIST: 'sky',
  FARMER: 'green',
  OPERATOR: 'amber',
  AUDITOR: 'slate',
};

const {
  data: membersData,
  pending,
  refresh,
} = await useAsyncData('team-members', () =>
  api.get<Paginated<Member> | Member[]>('/members/'),
);

const members = computed<Member[]>(() => {
  const d = membersData.value as Paginated<Member> | Member[] | null;
  if (!d) return [];
  return Array.isArray(d) ? d : (d.results ?? []);
});

// ---- Search & filters ----
const search = ref('');
const roleFilter = ref('');
const roleFilterOptions = computed(() => [
  { value: '', label: 'Todos los roles' },
  ...ROLES,
]);

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase();
  return members.value.filter((m) => {
    if (roleFilter.value && m.role !== roleFilter.value) return false;
    if (!q) return true;
    return [m.user_name, m.user_email, m.phone]
      .filter(Boolean)
      .some((v) => String(v).toLowerCase().includes(q));
  });
});

const kpis = computed(() => {
  const rows = members.value;
  return {
    total: rows.length,
    active: rows.filter((m) => m.is_active).length,
    admins: rows.filter((m) => ['SUPERADMIN', 'COOP_ADMIN'].includes(m.role))
      .length,
    technicians: rows.filter((m) => m.role === 'AGRONOMIST').length,
  };
});

// ---- Add member modal ----
const showForm = ref(false);
const saving = ref(false);
const blank = () => ({
  email: '',
  first_name: '',
  last_name: '',
  phone: '',
  role: 'FARMER',
  create_account: true,
  password: '',
});
const form = ref(blank());

function openAdd() {
  form.value = blank();
  showForm.value = true;
}

async function submit() {
  if (!form.value.email.trim()) {
    toast.error('El email es obligatorio.');
    return;
  }
  saving.value = true;
  try {
    await api.post('/members/add/', {
      email: form.value.email.trim(),
      first_name: form.value.first_name.trim(),
      last_name: form.value.last_name.trim(),
      phone: form.value.phone.trim(),
      role: form.value.role,
      create_account: form.value.create_account,
      password:
        form.value.create_account && form.value.password
          ? form.value.password
          : undefined,
    });
    toast.success('Miembro añadido al equipo.');
    showForm.value = false;
    await refresh();
  } catch (e: any) {
    toast.error(e?.data?.email?.[0] || 'No se pudo añadir el miembro.');
  } finally {
    saving.value = false;
  }
}

// ---- Member detail drawer ----
const showDetail = ref(false);
const selected = ref<Member | null>(null);
const accountPassword = ref('');
const generatedPassword = ref('');
const creatingAccount = ref(false);

function openDetail(m: Member) {
  selected.value = m;
  accountPassword.value = '';
  generatedPassword.value = '';
  showDetail.value = true;
}

function syncSelected() {
  if (selected.value) {
    selected.value =
      members.value.find((m) => m.id === selected.value?.id) ?? selected.value;
  }
}

async function createAccount() {
  if (!selected.value) return;
  creatingAccount.value = true;
  generatedPassword.value = '';
  try {
    const res = await api.post<Member & { generated_password?: string }>(
      `/members/${selected.value.id}/create-account/`,
      { password: accountPassword.value || undefined },
    );
    if (res.generated_password)
      generatedPassword.value = res.generated_password;
    toast.success('Cuenta de acceso creada.');
    accountPassword.value = '';
    await refresh();
    syncSelected();
  } catch (e: any) {
    toast.error(e?.data?.detail || 'No se pudo crear la cuenta.');
  } finally {
    creatingAccount.value = false;
  }
}

async function changeRole(m: Member, role: string) {
  if (m.role === role) return;
  try {
    await api.patch(`/members/${m.id}/`, { role });
    toast.success('Rol actualizado.');
    await refresh();
    syncSelected();
  } catch {
    toast.error('No se pudo cambiar el rol.');
  }
}

async function toggleActive(m: Member) {
  try {
    await api.patch(`/members/${m.id}/`, { is_active: !m.is_active });
    toast.success(m.is_active ? 'Miembro desactivado.' : 'Miembro reactivado.');
    await refresh();
    syncSelected();
  } catch {
    toast.error('No se pudo actualizar el miembro.');
  }
}
</script>

<template>
  <div class="p-6 lg:p-8 space-y-6 w-full">
    <PageHeader
      title="Equipo"
      subtitle="Gestiona los miembros de la cooperativa, sus datos y sus roles"
    >
      <template #actions>
        <button
          class="text-sm px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 transition"
          @click="refresh()"
        >
          Refrescar
        </button>
        <button
          v-if="isAdmin"
          class="text-sm px-3 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition shadow-glow"
          @click="openAdd"
        >
          + Añadir miembro
        </button>
      </template>
    </PageHeader>

    <!-- KPIs -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <StatCard label="Miembros" :value="kpis.total" tone="brand" />
      <StatCard label="Activos" :value="kpis.active" tone="sky" />
      <StatCard label="Administradores" :value="kpis.admins" tone="violet" />
      <StatCard label="Técnicos" :value="kpis.technicians" tone="amber" />
    </div>

    <!-- Toolbar -->
    <div class="flex items-center flex-wrap gap-2.5">
      <UiSearchInput
        v-model="search"
        placeholder="Buscar por nombre, email o teléfono…"
        class="w-full sm:w-80"
      />
      <UiFilterSelect
        v-model="roleFilter"
        :options="roleFilterOptions"
        icon="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
        class="w-52"
      />
    </div>

    <!-- Members grid -->
    <div v-if="pending"><UiSkeleton :rows="3" :cols="3" /></div>
    <div
      v-else-if="filtered.length"
      class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3"
    >
      <article
        v-for="m in filtered"
        :key="m.id"
        class="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 transition hover:shadow-md hover:border-brand-200 cursor-pointer"
        :class="m.is_active ? '' : 'opacity-60'"
        @click="openDetail(m)"
      >
        <div class="flex items-start gap-3.5">
          <span
            class="w-12 h-12 shrink-0 rounded-full bg-gradient-to-br from-brand-400 to-brand-600 text-white grid place-items-center text-base font-semibold ring-2 ring-white shadow"
          >
            {{ m.initials }}
          </span>
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2">
              <h3 class="text-sm font-semibold text-slate-800 truncate">
                {{ m.user_name || m.user_email }}
              </h3>
              <UiBadge v-if="!m.is_active" tone="slate">Inactivo</UiBadge>
            </div>
            <p class="text-xs text-slate-400 truncate">{{ m.user_email }}</p>
            <p
              v-if="m.phone"
              class="text-xs text-slate-400 mt-0.5 flex items-center gap-1"
            >
              <svg
                class="w-3 h-3"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
                />
              </svg>
              {{ m.phone }}
            </p>
          </div>
        </div>

        <div class="flex items-center justify-between gap-2 mt-4">
          <div class="flex items-center gap-1.5 flex-wrap">
            <UiBadge :tone="ROLE_TONE[m.role] || 'slate'" dot>
              {{ m.role_display }}
            </UiBadge>
            <UiBadge v-if="!m.has_account" tone="amber">Sin cuenta</UiBadge>
          </div>
          <span class="text-[11px] text-slate-400">
            Desde {{ date(m.created_at) }}
          </span>
        </div>

        <!-- Admin controls -->
        <div
          v-if="isAdmin"
          class="flex items-center gap-2 mt-4 pt-4 border-t border-slate-100"
          @click.stop
        >
          <UiSelect
            :model-value="m.role"
            :options="ROLES"
            class="flex-1"
            @update:model-value="(v: string) => changeRole(m, v)"
          />
          <button
            class="text-xs px-2.5 py-2 rounded-lg border transition shrink-0"
            :class="
              m.is_active
                ? 'border-red-200 text-red-600 hover:bg-red-50'
                : 'border-emerald-200 text-emerald-600 hover:bg-emerald-50'
            "
            @click="toggleActive(m)"
          >
            {{ m.is_active ? 'Desactivar' : 'Reactivar' }}
          </button>
        </div>
      </article>
    </div>

    <EmptyState
      v-else
      title="Sin miembros"
      message="Añade el primer miembro a tu equipo para empezar a colaborar."
    >
      <template #action>
        <button
          v-if="isAdmin"
          class="text-sm px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition"
          @click="openAdd"
        >
          + Añadir miembro
        </button>
      </template>
    </EmptyState>

    <!-- Add member modal -->
    <UiModal v-model="showForm" title="Añadir miembro al equipo">
      <div class="space-y-4">
        <p class="text-xs text-slate-500">
          Si el email ya existe, se añadirá al equipo. Si no, se dará de alta un
          nuevo usuario con los datos indicados.
        </p>
        <UiField label="Email" required>
          <UiInput
            v-model="form.email"
            type="email"
            placeholder="persona@cooperativa.es"
          />
        </UiField>
        <div class="grid grid-cols-2 gap-4">
          <UiField label="Nombre">
            <UiInput v-model="form.first_name" placeholder="Nombre" />
          </UiField>
          <UiField label="Apellidos">
            <UiInput v-model="form.last_name" placeholder="Apellidos" />
          </UiField>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <UiField label="Teléfono">
            <UiInput v-model="form.phone" placeholder="+34 600 000 000" />
          </UiField>
          <UiField label="Rol">
            <UiSelect v-model="form.role" :options="ROLES" />
          </UiField>
        </div>

        <div
          class="rounded-xl border border-slate-200 bg-slate-50 p-3.5 space-y-3"
        >
          <label class="flex items-start gap-2.5 cursor-pointer">
            <input
              v-model="form.create_account"
              type="checkbox"
              class="mt-0.5 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
            />
            <span class="text-sm text-slate-700">
              Crear cuenta de acceso
              <span class="block text-xs text-slate-400">
                El usuario podrá iniciar sesión. Si lo dejas desmarcado, solo se
                registra como miembro del equipo.
              </span>
            </span>
          </label>
          <UiField
            v-if="form.create_account"
            label="Contraseña inicial (opcional)"
          >
            <UiInput
              v-model="form.password"
              type="password"
              placeholder="Se genera una aleatoria si se deja vacío"
            />
          </UiField>
        </div>
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
          {{ saving ? 'Guardando…' : 'Añadir miembro' }}
        </button>
      </template>
    </UiModal>

    <!-- Member detail -->
    <UiModal
      v-model="showDetail"
      :title="selected?.user_name || 'Detalle del miembro'"
    >
      <div v-if="selected" class="space-y-5">
        <!-- Identity -->
        <div class="flex items-center gap-4">
          <span
            class="w-16 h-16 shrink-0 rounded-2xl bg-gradient-to-br from-brand-400 to-brand-600 text-white grid place-items-center text-xl font-semibold ring-2 ring-white shadow"
          >
            {{ selected.initials }}
          </span>
          <div class="min-w-0">
            <h3 class="text-base font-semibold text-slate-800 truncate">
              {{ selected.user_name }}
            </h3>
            <p class="text-sm text-slate-400 truncate">
              {{ selected.user_email }}
            </p>
            <div class="flex items-center gap-1.5 flex-wrap mt-2">
              <UiBadge :tone="ROLE_TONE[selected.role] || 'slate'" dot>
                {{ selected.role_display }}
              </UiBadge>
              <UiBadge :tone="selected.is_active ? 'green' : 'slate'">
                {{ selected.is_active ? 'Activo' : 'Inactivo' }}
              </UiBadge>
              <UiBadge :tone="selected.has_account ? 'sky' : 'amber'">
                {{ selected.has_account ? 'Con cuenta' : 'Sin cuenta' }}
              </UiBadge>
            </div>
          </div>
        </div>

        <!-- Info grid -->
        <dl class="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
          <div>
            <dt class="text-xs text-slate-400">Teléfono</dt>
            <dd class="text-slate-700">{{ selected.phone || '—' }}</dd>
          </div>
          <div>
            <dt class="text-xs text-slate-400">Idioma</dt>
            <dd class="text-slate-700 uppercase">
              {{ selected.locale || '—' }}
            </dd>
          </div>
          <div>
            <dt class="text-xs text-slate-400">Miembro desde</dt>
            <dd class="text-slate-700">{{ date(selected.created_at) }}</dd>
          </div>
          <div>
            <dt class="text-xs text-slate-400">Último acceso</dt>
            <dd class="text-slate-700">
              {{ selected.last_login ? date(selected.last_login) : 'Nunca' }}
            </dd>
          </div>
        </dl>

        <!-- Admin actions -->
        <div v-if="isAdmin" class="space-y-4 pt-4 border-t border-slate-100">
          <UiField label="Rol">
            <UiSelect
              :model-value="selected.role"
              :options="ROLES"
              @update:model-value="(v: string) => changeRole(selected!, v)"
            />
          </UiField>

          <!-- Create account -->
          <div
            v-if="!selected.has_account"
            class="rounded-xl border border-amber-200 bg-amber-50 p-3.5 space-y-3"
          >
            <p class="text-xs text-amber-700">
              Este miembro aún no puede iniciar sesión. Crea una cuenta de
              acceso indicando una contraseña o deja el campo vacío para generar
              una automáticamente.
            </p>
            <UiInput
              v-model="accountPassword"
              type="password"
              placeholder="Contraseña (opcional)"
            />
            <p
              v-if="generatedPassword"
              class="text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2"
            >
              Contraseña generada:
              <span class="font-mono font-semibold">{{
                generatedPassword
              }}</span>
              · cópiala y compártela de forma segura.
            </p>
            <button
              class="text-sm px-3 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition disabled:opacity-50"
              :disabled="creatingAccount"
              @click="createAccount"
            >
              {{ creatingAccount ? 'Creando…' : 'Crear cuenta de acceso' }}
            </button>
          </div>

          <button
            class="w-full text-sm px-3 py-2 rounded-lg border transition"
            :class="
              selected.is_active
                ? 'border-red-200 text-red-600 hover:bg-red-50'
                : 'border-emerald-200 text-emerald-600 hover:bg-emerald-50'
            "
            @click="toggleActive(selected)"
          >
            {{
              selected.is_active ? 'Desactivar miembro' : 'Reactivar miembro'
            }}
          </button>
        </div>
      </div>

      <template #footer>
        <button
          class="text-sm px-4 py-2 rounded-lg border border-slate-200 hover:bg-slate-50 transition"
          @click="showDetail = false"
        >
          Cerrar
        </button>
      </template>
    </UiModal>
  </div>
</template>
