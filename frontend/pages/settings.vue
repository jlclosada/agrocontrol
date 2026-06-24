<script setup lang="ts">
import { useAuthStore } from '~/stores/auth';
import type { CooperativeSettings, MfaDevice } from '~/types/api';

const auth = useAuthStore();
const { dateTime } = useFormat();
const toast = useToast();

const isAdmin = computed(() =>
  ['SUPERADMIN', 'COOP_ADMIN'].includes(auth.role ?? ''),
);

const cfg = reactive({
  display_name: '',
  tagline: '',
  primary_color: '#16a34a',
  logo_emoji: '🌱',
  currency: 'EUR',
  default_operation_cost: '25.00',
  expiry_alert_days: 30,
  stock_alerts_enabled: true,
  expiry_alerts_enabled: true,
  safety_alerts_enabled: true,
  agents_enabled: true,
  traceability_enabled: true,
});
const savingCfg = ref(false);

function syncCfg() {
  const s = auth.settings;
  if (!s) return;
  cfg.display_name = s.display_name;
  cfg.tagline = s.tagline;
  cfg.primary_color = s.primary_color;
  cfg.logo_emoji = s.logo_emoji;
  cfg.currency = s.currency;
  cfg.default_operation_cost = s.default_operation_cost;
  cfg.expiry_alert_days = s.expiry_alert_days;
  cfg.stock_alerts_enabled = s.stock_alerts_enabled;
  cfg.expiry_alerts_enabled = s.expiry_alerts_enabled;
  cfg.safety_alerts_enabled = s.safety_alerts_enabled;
  cfg.agents_enabled = s.agents_enabled;
  cfg.traceability_enabled = s.traceability_enabled;
}

async function saveCfg() {
  savingCfg.value = true;
  try {
    await auth.updateSettings({ ...cfg } as Partial<CooperativeSettings>);
    toast.success('Configuración guardada correctamente.');
  } catch {
    toast.error('No se pudo guardar la configuración.');
  } finally {
    savingCfg.value = false;
  }
}

const currencyOptions = [
  { value: 'EUR', label: 'Euro (€)' },
  { value: 'USD', label: 'Dólar ($)' },
  { value: 'GBP', label: 'Libra (£)' },
];

const devices = ref<MfaDevice[]>([]);
const loading = ref(true);

const enrolling = ref(false);
const provisioningUri = ref('');
const secret = ref('');
const deviceId = ref('');
const code = ref('');
const confirming = ref(false);
const error = ref('');
const success = ref('');
const qrCanvas = ref<HTMLCanvasElement | null>(null);

const hasConfirmed = computed(() => devices.value.some((d) => d.confirmed));

async function load() {
  loading.value = true;
  try {
    devices.value = await auth.mfaDevices();
  } finally {
    loading.value = false;
  }
}

async function renderQr() {
  if (!provisioningUri.value || !qrCanvas.value) return;
  try {
    const QR = await import('qrcode');
    await QR.toCanvas(qrCanvas.value, provisioningUri.value, {
      width: 200,
      margin: 1,
      color: { dark: '#166534', light: '#ffffff' },
    });
  } catch {
    /* QR rendering optional; secret is shown as fallback */
  }
}

async function startEnroll() {
  error.value = '';
  success.value = '';
  enrolling.value = true;
  try {
    const res = await auth.enrollMfa();
    deviceId.value = res.device_id;
    provisioningUri.value = res.provisioning_uri;
    const match = res.provisioning_uri.match(/secret=([^&]+)/);
    secret.value = match ? match[1] : '';
    await nextTick();
    await renderQr();
  } catch {
    error.value = 'No se pudo iniciar la configuración.';
    enrolling.value = false;
  }
}

async function confirm() {
  error.value = '';
  confirming.value = true;
  try {
    await auth.confirmMfa(deviceId.value, code.value);
    success.value = 'Verificación en dos pasos activada correctamente.';
    enrolling.value = false;
    provisioningUri.value = '';
    secret.value = '';
    code.value = '';
    await load();
  } catch {
    error.value = 'Código incorrecto. Inténtalo de nuevo.';
  } finally {
    confirming.value = false;
  }
}

function cancel() {
  enrolling.value = false;
  provisioningUri.value = '';
  secret.value = '';
  code.value = '';
  error.value = '';
}

onMounted(() => {
  load();
  syncCfg();
});
watch(() => auth.settings, syncCfg, { immediate: true });
</script>
<template>
  <div class="p-6 lg:p-8 space-y-6 max-w-3xl mx-auto">
    <PageHeader
      title="Seguridad"
      subtitle="Gestiona la verificación en dos pasos de tu cuenta"
    />

    <Transition name="page">
      <div
        v-if="success"
        class="rounded-xl bg-brand-50 border border-brand-100 text-brand-700 px-4 py-3 text-sm"
      >
        {{ success }}
      </div>
    </Transition>

    <!-- Cooperative configuration (admins only) -->
    <UiCard v-if="isAdmin" :padded="false">
      <div class="px-5 py-4 border-b border-slate-100">
        <h2 class="font-semibold text-slate-700">
          Configuración de la cooperativa
        </h2>
        <p class="text-xs text-slate-400 mt-0.5">
          Personaliza la marca, la economía y los módulos activos.
        </p>
      </div>
      <div class="p-5 space-y-6">
        <div>
          <p
            class="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3"
          >
            Marca
          </p>
          <div class="grid sm:grid-cols-2 gap-4">
            <UiField label="Nombre visible">
              <UiInput
                v-model="cfg.display_name"
                placeholder="AgroControl OS"
              />
            </UiField>
            <UiField label="Eslogan">
              <UiInput
                v-model="cfg.tagline"
                placeholder="Sistema operativo agrícola"
              />
            </UiField>
            <UiField label="Emoji / logo">
              <UiInput
                v-model="cfg.logo_emoji"
                maxlength="4"
                placeholder="🌱"
              />
            </UiField>
            <UiField label="Color principal">
              <div class="flex items-center gap-2">
                <input
                  v-model="cfg.primary_color"
                  type="color"
                  class="h-9 w-12 rounded border border-slate-300 cursor-pointer"
                />
                <UiInput v-model="cfg.primary_color" placeholder="#16a34a" />
              </div>
            </UiField>
          </div>
        </div>

        <div>
          <p
            class="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3"
          >
            Economía
          </p>
          <div class="grid sm:grid-cols-3 gap-4">
            <UiField label="Moneda">
              <UiSelect v-model="cfg.currency" :options="currencyOptions" />
            </UiField>
            <UiField label="Coste operación por defecto">
              <UiInput
                v-model="cfg.default_operation_cost"
                type="number"
                step="0.01"
                min="0"
              />
            </UiField>
            <UiField label="Días aviso de caducidad">
              <UiInput v-model="cfg.expiry_alert_days" type="number" min="1" />
            </UiField>
          </div>
        </div>

        <div>
          <p
            class="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3"
          >
            Alertas y módulos
          </p>
          <div class="space-y-2">
            <label
              v-for="t in [
                { key: 'stock_alerts_enabled', label: 'Alertas de stock' },
                { key: 'expiry_alerts_enabled', label: 'Alertas de caducidad' },
                { key: 'safety_alerts_enabled', label: 'Alertas de seguridad' },
                { key: 'agents_enabled', label: 'Agentes de IA' },
                { key: 'traceability_enabled', label: 'Trazabilidad' },
              ]"
              :key="t.key"
              class="flex items-center gap-3 text-sm text-slate-700"
            >
              <input
                v-model="(cfg as any)[t.key]"
                type="checkbox"
                class="rounded border-slate-300 text-brand-600 focus:ring-brand-500"
              />
              {{ t.label }}
            </label>
          </div>
        </div>

        <div class="flex justify-end pt-2 border-t border-slate-100">
          <button
            class="text-sm px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition shadow-glow disabled:opacity-50"
            :disabled="savingCfg"
            @click="saveCfg"
          >
            {{ savingCfg ? 'Guardando…' : 'Guardar configuración' }}
          </button>
        </div>
      </div>
    </UiCard>

    <!-- Status card -->
    <UiCard>
      <div class="flex items-start justify-between gap-4">
        <div class="flex items-start gap-4">
          <div
            class="w-12 h-12 rounded-xl grid place-items-center shrink-0"
            :class="
              hasConfirmed
                ? 'bg-brand-50 text-brand-600'
                : 'bg-amber-50 text-amber-600'
            "
          >
            <svg
              class="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
              />
            </svg>
          </div>
          <div>
            <h2 class="font-semibold text-slate-800">
              Verificación en dos pasos (TOTP)
            </h2>
            <p class="text-sm text-slate-500 mt-0.5">
              Añade una capa extra de seguridad con una app de autenticación.
            </p>
            <div class="mt-2">
              <UiBadge :tone="hasConfirmed ? 'green' : 'amber'" dot>
                {{ hasConfirmed ? 'Activada' : 'No configurada' }}
              </UiBadge>
            </div>
          </div>
        </div>
        <button
          v-if="!enrolling"
          class="text-sm px-3 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition shadow-glow shrink-0"
          @click="startEnroll"
        >
          {{ hasConfirmed ? 'Añadir dispositivo' : 'Activar' }}
        </button>
      </div>

      <!-- Enrollment flow -->
      <Transition name="page">
        <div v-if="enrolling" class="mt-6 pt-6 border-t border-slate-100">
          <div class="grid sm:grid-cols-[auto,1fr] gap-6 items-start">
            <div
              class="rounded-xl border border-slate-100 p-3 bg-white grid place-items-center"
            >
              <canvas ref="qrCanvas" class="rounded-lg" />
            </div>
            <div class="space-y-4">
              <div>
                <p class="text-sm text-slate-600">
                  1. Escanea el código QR con tu app de autenticación (Google
                  Authenticator, Authy, 1Password…).
                </p>
                <p class="text-xs text-slate-400 mt-2">
                  ¿No puedes escanear? Introduce esta clave manualmente:
                </p>
                <code
                  class="mt-1 inline-block text-xs font-mono bg-slate-100 px-2 py-1 rounded select-all break-all"
                  >{{ secret }}</code
                >
              </div>
              <div>
                <label class="block text-sm text-slate-600 mb-1">
                  2. Introduce el código de 6 dígitos
                </label>
                <input
                  v-model="code"
                  inputmode="numeric"
                  maxlength="6"
                  placeholder="000000"
                  class="w-40 text-center tracking-[0.4em] text-xl font-semibold rounded-lg border border-slate-300 px-3 py-2.5 focus:ring-2 focus:ring-brand-500 outline-none transition"
                />
              </div>
              <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
              <div class="flex gap-2">
                <button
                  class="text-sm px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white transition disabled:opacity-50"
                  :disabled="confirming || code.length < 6"
                  @click="confirm"
                >
                  {{ confirming ? 'Verificando…' : 'Confirmar' }}
                </button>
                <button
                  class="text-sm px-4 py-2 rounded-lg border border-slate-200 hover:bg-slate-50 transition"
                  @click="cancel"
                >
                  Cancelar
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </UiCard>

    <!-- Devices -->
    <UiCard :padded="false">
      <div class="px-5 py-4 border-b border-slate-100">
        <h2 class="font-semibold text-slate-700">Dispositivos registrados</h2>
      </div>
      <div v-if="loading" class="p-5"><UiSkeleton :rows="2" :cols="1" /></div>
      <ul v-else-if="devices.length" class="divide-y divide-slate-100">
        <li
          v-for="d in devices"
          :key="d.id"
          class="px-5 py-3 flex items-center justify-between"
        >
          <div>
            <p class="font-medium text-slate-700">{{ d.name }}</p>
            <p class="text-xs text-slate-400">
              Registrado {{ dateTime(d.created_at) }}
            </p>
          </div>
          <UiBadge :tone="d.confirmed ? 'green' : 'amber'" dot>
            {{ d.confirmed ? 'Confirmado' : 'Pendiente' }}
          </UiBadge>
        </li>
      </ul>
      <EmptyState
        v-else
        title="Sin dispositivos"
        message="No has registrado ningún dispositivo de autenticación."
      />
    </UiCard>
  </div>
</template>
