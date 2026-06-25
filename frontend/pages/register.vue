<script setup lang="ts">
import { useAuthStore } from '~/stores/auth';

definePageMeta({ layout: false });

const auth = useAuthStore();

const form = ref({
  first_name: '',
  last_name: '',
  email: '',
  password: '',
  password2: '',
  cooperative_name: '',
});
const error = ref('');
const loading = ref(false);

const passwordStrength = computed(() => {
  const p = form.value.password;
  let score = 0;
  if (p.length >= 8) score++;
  if (/[A-Z]/.test(p)) score++;
  if (/[0-9]/.test(p)) score++;
  if (/[^A-Za-z0-9]/.test(p)) score++;
  return score; // 0–4
});
const strengthLabel = computed(
  () =>
    ['Muy débil', 'Débil', 'Aceptable', 'Fuerte', 'Excelente'][
      passwordStrength.value
    ],
);

async function submit() {
  error.value = '';
  if (form.value.password.length < 8) {
    error.value = 'La contraseña debe tener al menos 8 caracteres.';
    return;
  }
  if (form.value.password !== form.value.password2) {
    error.value = 'Las contraseñas no coinciden.';
    return;
  }
  loading.value = true;
  try {
    await auth.register({
      email: form.value.email.trim(),
      password: form.value.password,
      first_name: form.value.first_name.trim(),
      last_name: form.value.last_name.trim(),
      cooperative_name: form.value.cooperative_name.trim(),
    });
    await navigateTo('/');
  } catch (err: any) {
    const data = err?.response?._data;
    if (data?.email) error.value = String(data.email[0] ?? data.email);
    else if (data?.password)
      error.value = String(data.password[0] ?? data.password);
    else if (data?.cooperative_name)
      error.value = String(data.cooperative_name[0] ?? data.cooperative_name);
    else error.value = 'No se pudo completar el registro. Revisa los datos.';
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div
    class="min-h-screen grid lg:grid-cols-2 bg-gradient-to-br from-brand-700 to-brand-900"
  >
    <!-- Brand panel -->
    <div
      class="hidden lg:flex flex-col justify-between p-12 text-white relative overflow-hidden"
    >
      <div
        class="absolute -top-24 -right-24 w-96 h-96 rounded-full bg-brand-500/20 blur-3xl"
      />
      <div
        class="absolute bottom-0 -left-20 w-80 h-80 rounded-full bg-brand-400/10 blur-3xl"
      />
      <div class="relative">
        <p class="text-2xl font-extrabold tracking-tight">🌱 AgroControl OS</p>
      </div>
      <div class="relative space-y-4 animate-fade-in-up">
        <h2 class="text-4xl font-extrabold leading-tight">
          Crea tu cooperativa<br />y empieza en minutos.
        </h2>
        <p class="text-brand-100/90 max-w-md">
          Registra tu explotación o cooperativa y obtén al instante
          trazabilidad, cuaderno de campo, inventario, costes, mapas catastrales
          y clima agronómico.
        </p>
        <ul class="space-y-2 pt-2 text-brand-100/90">
          <li
            v-for="t in [
              'Sin tarjeta de crédito',
              'Datos públicos de Catastro y SIGPAC',
              'Clima y riego por parcela',
            ]"
            :key="t"
            class="flex items-center gap-2 text-sm"
          >
            <span class="text-brand-300">✓</span> {{ t }}
          </li>
        </ul>
      </div>
      <p class="relative text-xs text-brand-100/70">
        © {{ new Date().getFullYear() }} AgroControl OS
      </p>
    </div>

    <!-- Form panel -->
    <div class="grid place-items-center p-6">
      <form
        class="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md space-y-5 animate-scale-in"
        @submit.prevent="submit"
      >
        <div class="text-center lg:hidden">
          <h1 class="text-2xl font-bold text-brand-700">🌱 AgroControl OS</h1>
        </div>

        <div>
          <h1 class="text-xl font-bold text-slate-800">Crear cuenta</h1>
          <p class="text-sm text-slate-500 mt-1">
            Da de alta tu usuario y tu cooperativa
          </p>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-medium text-slate-600 mb-1"
              >Nombre</label
            >
            <input
              v-model="form.first_name"
              type="text"
              required
              autocomplete="given-name"
              class="w-full rounded-lg border border-slate-300 px-3 py-2.5 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition"
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-slate-600 mb-1"
              >Apellidos</label
            >
            <input
              v-model="form.last_name"
              type="text"
              autocomplete="family-name"
              class="w-full rounded-lg border border-slate-300 px-3 py-2.5 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition"
            />
          </div>
        </div>

        <div>
          <label class="block text-xs font-medium text-slate-600 mb-1"
            >Nombre de la cooperativa / explotación</label
          >
          <input
            v-model="form.cooperative_name"
            type="text"
            required
            placeholder="Ej. Cooperativa San Isidro"
            class="w-full rounded-lg border border-slate-300 px-3 py-2.5 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition"
          />
        </div>

        <div>
          <label class="block text-xs font-medium text-slate-600 mb-1"
            >Email</label
          >
          <input
            v-model="form.email"
            type="email"
            required
            autocomplete="email"
            class="w-full rounded-lg border border-slate-300 px-3 py-2.5 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition"
          />
        </div>

        <div>
          <label class="block text-xs font-medium text-slate-600 mb-1"
            >Contraseña</label
          >
          <input
            v-model="form.password"
            type="password"
            required
            autocomplete="new-password"
            class="w-full rounded-lg border border-slate-300 px-3 py-2.5 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition"
          />
          <div v-if="form.password" class="mt-1.5 flex items-center gap-2">
            <div class="flex-1 h-1.5 rounded-full bg-slate-100 overflow-hidden">
              <div
                class="h-full rounded-full transition-all duration-300"
                :class="
                  [
                    'bg-red-500',
                    'bg-red-500',
                    'bg-amber-500',
                    'bg-brand-500',
                    'bg-brand-600',
                  ][passwordStrength]
                "
                :style="{ width: `${(passwordStrength / 4) * 100}%` }"
              />
            </div>
            <span class="text-[11px] text-slate-400">{{ strengthLabel }}</span>
          </div>
        </div>

        <div>
          <label class="block text-xs font-medium text-slate-600 mb-1"
            >Repetir contraseña</label
          >
          <input
            v-model="form.password2"
            type="password"
            required
            autocomplete="new-password"
            class="w-full rounded-lg border border-slate-300 px-3 py-2.5 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition"
          />
        </div>

        <Transition name="page">
          <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
        </Transition>

        <button
          type="submit"
          :disabled="loading"
          class="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 font-medium transition disabled:opacity-60 shadow-glow active:scale-[0.99]"
        >
          {{ loading ? 'Creando cuenta…' : 'Crear cuenta' }}
        </button>

        <p class="text-center text-sm text-slate-500">
          ¿Ya tienes cuenta?
          <NuxtLink
            to="/login"
            class="font-medium text-brand-700 hover:text-brand-800 transition"
          >
            Inicia sesión
          </NuxtLink>
        </p>
      </form>
    </div>
  </div>
</template>
