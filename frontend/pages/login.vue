<script setup lang="ts">
import { MfaRequiredError, useAuthStore } from '~/stores/auth';

definePageMeta({ layout: false });

const auth = useAuthStore();
const email = ref('');
const password = ref('');
const otp = ref('');
const mfaStep = ref(false);
const error = ref('');
const loading = ref(false);

async function submit() {
  error.value = '';
  loading.value = true;
  try {
    await auth.login(email.value, password.value, otp.value || undefined);
    await navigateTo('/');
  } catch (err) {
    if (err instanceof MfaRequiredError) {
      mfaStep.value = true;
      error.value = '';
    } else if (mfaStep.value) {
      error.value = 'Código de verificación incorrecto.';
    } else {
      error.value = 'Credenciales no válidas.';
    }
  } finally {
    loading.value = false;
  }
}

function back() {
  mfaStep.value = false;
  otp.value = '';
  error.value = '';
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
          La plataforma definitiva<br />para tu cooperativa agrícola.
        </h2>
        <p class="text-brand-100/90 max-w-md">
          Trazabilidad inmutable, cuaderno de campo, inventario FEFO, costes,
          rentabilidad y alertas inteligentes — todo en un único lugar.
        </p>
        <div class="flex gap-2 pt-2">
          <span
            v-for="t in [
              'Trazabilidad',
              'Inventario FEFO',
              'Rentabilidad',
              'Alertas',
            ]"
            :key="t"
            class="text-xs bg-white/10 backdrop-blur px-3 py-1 rounded-full border border-white/15"
          >
            {{ t }}
          </span>
        </div>
      </div>
      <p class="relative text-xs text-brand-100/70">
        © {{ new Date().getFullYear() }} AgroControl OS
      </p>
    </div>

    <!-- Form panel -->
    <div class="grid place-items-center p-6">
      <form
        class="bg-white rounded-2xl shadow-xl p-8 w-full max-w-sm space-y-5 animate-scale-in"
        @submit.prevent="submit"
      >
        <div class="text-center lg:hidden">
          <h1 class="text-2xl font-bold text-brand-700">🌱 AgroControl OS</h1>
        </div>

        <Transition name="page" mode="out-in">
          <div v-if="!mfaStep" key="credentials" class="space-y-5">
            <div>
              <h1 class="text-xl font-bold text-slate-800">
                Bienvenido de nuevo
              </h1>
              <p class="text-sm text-slate-500 mt-1">
                Inicia sesión en tu cooperativa
              </p>
            </div>

            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1"
                >Email</label
              >
              <input
                v-model="email"
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
                v-model="password"
                type="password"
                required
                autocomplete="current-password"
                class="w-full rounded-lg border border-slate-300 px-3 py-2.5 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition"
              />
            </div>
          </div>

          <div v-else key="mfa" class="space-y-5">
            <div>
              <h1 class="text-xl font-bold text-slate-800">
                Verificación en dos pasos
              </h1>
              <p class="text-sm text-slate-500 mt-1">
                Introduce el código de 6 dígitos de tu app de autenticación.
              </p>
            </div>
            <input
              v-model="otp"
              inputmode="numeric"
              maxlength="6"
              placeholder="000000"
              class="w-full text-center tracking-[0.5em] text-2xl font-semibold rounded-lg border border-slate-300 px-3 py-3 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition"
            />
            <button
              type="button"
              class="text-xs text-slate-500 hover:text-brand-700 transition"
              @click="back"
            >
              ← Usar otra cuenta
            </button>
          </div>
        </Transition>

        <Transition name="page">
          <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
        </Transition>

        <button
          type="submit"
          :disabled="loading"
          class="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg py-2.5 font-medium transition disabled:opacity-60 shadow-glow active:scale-[0.99]"
        >
          {{ loading ? 'Comprobando…' : mfaStep ? 'Verificar' : 'Entrar' }}
        </button>
      </form>
    </div>
  </div>
</template>
