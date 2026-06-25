<script setup lang="ts">
import type { Agent, AgentRun, Paginated } from '~/types/api';

const api = useApi();
const { data: agents } = await useAsyncData('agents-chat', () =>
  api.get<Paginated<Agent>>('/agents/'),
);

const selectedAgent = ref<Agent | null>(null);
const message = ref('');
const sending = ref(false);
const history = ref<{ role: string; text: string }[]>([]);

watchEffect(() => {
  if (!selectedAgent.value && agents.value?.results?.length) {
    selectedAgent.value = agents.value.results[0];
  }
});

async function send() {
  if (!selectedAgent.value || !message.value.trim()) return;
  const text = message.value;
  history.value.push({ role: 'user', text });
  message.value = '';
  sending.value = true;
  try {
    const run = await api.post<AgentRun>(
      `/agents/${selectedAgent.value.id}/chat/`,
      {
        message: text,
      },
    );
    history.value.push({ role: 'assistant', text: run.output_text });
  } catch {
    history.value.push({
      role: 'assistant',
      text: '⚠️ Error al contactar al agente.',
    });
  } finally {
    sending.value = false;
  }
}
</script>

<template>
  <div class="p-6 lg:p-8 h-[100dvh] flex flex-col w-full">
    <PageHeader
      title="Agentes IA"
      subtitle="Consulta a tus agentes especializados"
    />

    <div class="flex gap-6 mt-6 flex-1 min-h-0">
      <!-- Agent list -->
      <div class="w-72 space-y-2 overflow-auto">
        <button
          v-for="a in agents?.results"
          :key="a.id"
          class="w-full text-left bg-white rounded-xl border p-4 transition"
          :class="
            selectedAgent?.id === a.id
              ? 'border-brand-500 ring-2 ring-brand-100'
              : 'border-slate-100 hover:border-brand-300'
          "
          @click="
            selectedAgent = a;
            history = [];
          "
        >
          <p class="font-semibold text-slate-700">{{ a.name }}</p>
          <p class="text-xs text-slate-500 mt-1">{{ a.purpose }}</p>
          <div class="flex flex-wrap gap-1 mt-2">
            <span
              v-for="s in a.skills"
              :key="s"
              class="text-[10px] bg-brand-50 text-brand-700 px-2 py-0.5 rounded-full"
            >
              {{ s }}
            </span>
          </div>
        </button>
      </div>

      <!-- Chat -->
      <div
        class="flex-1 flex flex-col bg-white rounded-xl border border-slate-100 min-h-0"
      >
        <div class="flex-1 overflow-auto p-5 space-y-3">
          <p v-if="!history.length" class="text-center text-slate-400 mt-10">
            Escribe un mensaje para {{ selectedAgent?.name }}.
          </p>
          <div
            v-for="(m, i) in history"
            :key="i"
            :class="m.role === 'user' ? 'text-right' : 'text-left'"
          >
            <span
              class="inline-block px-4 py-2 rounded-2xl text-sm max-w-[80%] whitespace-pre-wrap"
              :class="
                m.role === 'user'
                  ? 'bg-brand-600 text-white'
                  : 'bg-slate-100 text-slate-700'
              "
            >
              {{ m.text }}
            </span>
          </div>
          <p v-if="sending" class="text-sm text-slate-400">
            El agente está pensando…
          </p>
        </div>

        <form
          class="border-t border-slate-100 p-4 flex gap-2"
          @submit.prevent="send"
        >
          <input
            v-model="message"
            placeholder="Escribe tu consulta…"
            class="flex-1 rounded-lg border border-slate-300 px-3 py-2 focus:ring-2 focus:ring-brand-500 outline-none"
          />
          <button
            type="submit"
            :disabled="sending"
            class="bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-5 py-2 text-sm disabled:opacity-60"
          >
            Enviar
          </button>
        </form>
      </div>
    </div>
  </div>
</template>
