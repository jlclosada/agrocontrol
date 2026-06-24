"""AgentRuntime — orchestrates an agent execution (ReAct tool-calling loop).

Flow:
  1. Build the message list: system prompt + injected memory context + user input.
  2. Call the LLM with the agent's advertised tools.
  3. If the model requests tool calls, execute them, append results, loop.
  4. Persist the full transcript (AgentMessage) and the AgentRun result.

If ``OPENAI_API_KEY`` is not configured, a deterministic offline fallback runs so
the platform is fully usable in development without external calls.
"""
from __future__ import annotations

import json

from django.conf import settings

from apps.agents import tools as tool_registry
from apps.agents.models import AgentMessage, AgentRun, MessageRole, RunStatus
from apps.agents.tools import ToolContext

MAX_ITERATIONS = 5


class AgentRuntime:
    def __init__(self, agent, user, cooperative, role=None):
        self.agent = agent
        self.user = user
        self.cooperative = cooperative
        self.role = role
        self.ctx = ToolContext(cooperative=cooperative, user=user, role=role)

    # -- public API -------------------------------------------------------
    def run(self, input_text: str, *, run: AgentRun | None = None) -> AgentRun:
        run = run or AgentRun.objects.create(
            cooperative=self.cooperative,
            agent=self.agent,
            user=self.user,
            input_text=input_text,
        )
        run.status = RunStatus.RUNNING
        run.save(update_fields=["status"])
        try:
            messages = self._build_initial_messages(input_text)
            self._persist(run, MessageRole.SYSTEM, messages[0]["content"])
            self._persist(run, MessageRole.USER, input_text)

            if not settings.OPENAI_API_KEY:
                output = self._offline_fallback(input_text)
            else:
                output = self._run_llm_loop(run, messages)

            run.output_text = output
            run.status = RunStatus.COMPLETED
            self._persist(run, MessageRole.ASSISTANT, output)
        except Exception as exc:  # noqa: BLE001
            run.status = RunStatus.FAILED
            run.error = str(exc)
        run.save()
        return run

    # -- prompt construction ---------------------------------------------
    def _build_initial_messages(self, input_text: str) -> list[dict]:
        memory_ctx = self.ctx.memory.summarize(query=input_text, limit=6)
        system = (
            f"{self.agent.system_prompt}\n\n"
            f"Eres '{self.agent.name}'. Propósito: {self.agent.purpose}\n"
            f"Habilidades: {', '.join(self.agent.skills) or 'generales'}.\n"
            f"Responde en español, de forma concreta y accionable.\n\n"
            f"Memoria relevante:\n{memory_ctx}"
        )
        return [{"role": "system", "content": system}]

    # -- LLM loop ---------------------------------------------------------
    def _run_llm_loop(self, run: AgentRun, messages: list[dict]) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        schema = tool_registry.openai_schema(self.agent.tools)
        messages.append({"role": "user", "content": run.input_text})

        for _ in range(MAX_ITERATIONS):
            kwargs = {"model": self.agent.model or settings.OPENAI_MODEL, "messages": messages}
            if schema:
                kwargs["tools"] = schema
            response = client.chat.completions.create(**kwargs)
            choice = response.choices[0].message
            run.tokens_used += getattr(response.usage, "total_tokens", 0) or 0

            if not choice.tool_calls:
                return choice.content or ""

            messages.append({
                "role": "assistant",
                "content": choice.content or "",
                "tool_calls": [tc.model_dump() for tc in choice.tool_calls],
            })
            self._persist(
                run, MessageRole.ASSISTANT, choice.content or "",
                tool_calls=[tc.model_dump() for tc in choice.tool_calls],
            )

            for call in choice.tool_calls:
                args = json.loads(call.function.arguments or "{}")
                result = tool_registry.execute(call.function.name, self.ctx, **args)
                result_str = json.dumps(result, ensure_ascii=False, default=str)
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result_str,
                })
                self._persist(
                    run, MessageRole.TOOL, result_str,
                    tool_name=call.function.name, tool_call_id=call.id,
                )

        return "He alcanzado el límite de pasos sin una conclusión definitiva."

    # -- offline fallback -------------------------------------------------
    def _offline_fallback(self, input_text: str) -> str:
        """Deterministic response so the system works without an OpenAI key."""
        hints = []
        if any(w in input_text.lower() for w in ("stock", "producto", "existencias")):
            low = tool_registry.execute("list_low_stock", self.ctx)
            hints.append(f"Productos bajo mínimos: {json.dumps(low, ensure_ascii=False)}")
        if "parcela" in input_text.lower() or "cultivo" in input_text.lower():
            parcels = tool_registry.execute("list_parcels", self.ctx, limit=5)
            hints.append(f"Parcelas: {json.dumps(parcels, ensure_ascii=False)}")
        body = " ".join(hints) or "Sin acceso a un modelo LLM (configura OPENAI_API_KEY)."
        return (
            f"[{self.agent.name} · modo offline] He recibido: '{input_text}'. {body}"
        )

    # -- persistence ------------------------------------------------------
    def _persist(self, run, role, content, **extra):
        AgentMessage.objects.create(
            cooperative=self.cooperative,
            run=run,
            role=role,
            content=content,
            tool_name=extra.get("tool_name", ""),
            tool_calls=extra.get("tool_calls"),
            tool_call_id=extra.get("tool_call_id", ""),
        )
