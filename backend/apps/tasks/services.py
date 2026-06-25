"""Audit/activity logging for tasks.

Records an immutable :class:`TaskActivity` entry for every meaningful change so
each ticket has a professional activity timeline (who, what, when, before/after).
"""
from __future__ import annotations

from apps.tasks.models import Task, TaskActivity, TaskActivityAction

# Scalar fields tracked for the activity timeline, mapped to a human label and
# the activity action recorded when they change. Assignees (M2M) are handled
# separately by ``log_assignee_changes``.
TRACKED_FIELDS = {
    "status": ("Estado", TaskActivityAction.STATUS_CHANGED),
    "priority": ("Prioridad", TaskActivityAction.PRIORITY_CHANGED),
    "category": ("Categoría", TaskActivityAction.CATEGORY_CHANGED),
    "due_date": ("Fecha límite", TaskActivityAction.DUE_DATE_CHANGED),
    "title": ("Título", TaskActivityAction.EDITED),
    "description": ("Descripción", TaskActivityAction.EDITED),
}


def user_label(user) -> str:
    if not user:
        return "Sin asignar"
    full = f"{user.first_name} {user.last_name}".strip()
    return full or user.email


def _display(task: Task, field: str, value) -> str:
    """Human-readable representation of a field value for the timeline."""
    if value in (None, ""):
        return "—"
    if field in {"status", "priority", "category"}:
        return dict(task._meta.get_field(field).choices).get(value, value)
    if field == "due_date":
        return value.isoformat() if hasattr(value, "isoformat") else str(value)
    text = str(value)
    return (text[:60] + "…") if len(text) > 60 else text


def log_created(task: Task, actor) -> None:
    TaskActivity.objects.create(
        task=task,
        actor=actor,
        action=TaskActivityAction.CREATED,
        note="Tarea creada",
    )


def log_comment(task: Task, actor, text: str, mentions=None) -> TaskActivity:
    entry = TaskActivity.objects.create(
        task=task,
        actor=actor,
        action=TaskActivityAction.COMMENT,
        note=text[:255],
    )
    if mentions:
        entry.mentions.set(mentions)
    return entry


def log_changes(task: Task, actor, before: dict) -> list[TaskActivity]:
    """Compare a pre-save snapshot with the saved task and log each change."""
    entries: list[TaskActivity] = []
    for field, (label, action) in TRACKED_FIELDS.items():
        old = before.get(field)
        new = getattr(task, field)
        if old == new:
            continue
        entries.append(
            TaskActivity(
                task=task,
                actor=actor,
                action=action,
                field=label,
                from_value=_display(task, field, old),
                to_value=_display(task, field, new),
            )
        )
    if entries:
        TaskActivity.objects.bulk_create(entries)
    return entries


def log_assignee_changes(
    task: Task, actor, before_ids: set, before_labels: dict
) -> None:
    """Record assignments and removals after an M2M update."""
    after = {u.id: user_label(u) for u in task.assignees.all()}
    after_ids = set(after.keys())
    entries = []
    for uid in after_ids - before_ids:
        entries.append(
            TaskActivity(
                task=task,
                actor=actor,
                action=TaskActivityAction.ASSIGNED,
                field="Responsable",
                to_value=after.get(uid, ""),
            )
        )
    for uid in before_ids - after_ids:
        entries.append(
            TaskActivity(
                task=task,
                actor=actor,
                action=TaskActivityAction.UNASSIGNED,
                field="Responsable",
                from_value=before_labels.get(uid, ""),
            )
        )
    if entries:
        TaskActivity.objects.bulk_create(entries)


def snapshot(task: Task) -> dict:
    """Capture tracked scalar field values before an update for comparison."""
    return {
        "status": task.status,
        "priority": task.priority,
        "category": task.category,
        "due_date": task.due_date,
        "title": task.title,
        "description": task.description,
    }


def assignee_snapshot(task: Task) -> tuple[set, dict]:
    """Capture current assignees (ids + labels) before an M2M update."""
    labels = {u.id: user_label(u) for u in task.assignees.all()}
    return set(labels.keys()), labels
