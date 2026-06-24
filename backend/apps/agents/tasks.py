from celery import shared_task


@shared_task
def run_agent_task(run_id: str):
    """Execute an agent run asynchronously (heavy LLM work off the request)."""
    from apps.agents.models import AgentRun
    from apps.agents.runtime import AgentRuntime

    run = AgentRun.objects.select_related("agent", "user", "cooperative").get(id=run_id)
    runtime = AgentRuntime(
        agent=run.agent,
        user=run.user,
        cooperative=run.cooperative,
    )
    runtime.run(run.input_text, run=run)
    return str(run.id)


@shared_task
def dispatch_event_to_agents(event_name: str, cooperative_id: str, payload: dict):
    """Trigger agents subscribed to a domain event (e.g. 'treatment_registered')."""
    from apps.agents.models import Agent, AgentRun
    from apps.agents.runtime import AgentRuntime
    from apps.tenants.models import Cooperative

    cooperative = Cooperative.objects.get(id=cooperative_id)
    agents = [
        agent
        for agent in Agent.objects.filter(cooperative=cooperative, is_active=True)
        if event_name in (agent.listens_to or [])
    ]
    for agent in agents:
        run = AgentRun.objects.create(
            cooperative=cooperative,
            agent=agent,
            input_text=f"Evento '{event_name}': {payload}",
            context={"event": event_name, "payload": payload},
        )
        AgentRuntime(agent=agent, user=None, cooperative=cooperative).run(
            run.input_text, run=run
        )
