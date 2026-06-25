from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.models import TenantScopedModel, TimeStampedModel


class TaskStatus(models.TextChoices):
    TODO = "TODO", "Pendiente"
    IN_PROGRESS = "IN_PROGRESS", "En curso"
    BLOCKED = "BLOCKED", "Bloqueada"
    DONE = "DONE", "Completada"


class TaskPriority(models.TextChoices):
    LOW = "LOW", "Baja"
    MEDIUM = "MEDIUM", "Media"
    HIGH = "HIGH", "Alta"


class TaskCategory(models.TextChoices):
    SOWING = "SOWING", "Siembra"
    FERTILIZATION = "FERTILIZATION", "Abonado"
    IRRIGATION = "IRRIGATION", "Riego"
    TREATMENT = "TREATMENT", "Tratamiento fitosanitario"
    PRUNING = "PRUNING", "Poda"
    HARVEST = "HARVEST", "Cosecha"
    MAINTENANCE = "MAINTENANCE", "Mantenimiento"
    OTHER = "OTHER", "Otro"


class Task(TenantScopedModel):
    """A planned piece of farm work.

    Complements the field notebook (which records what already happened): tasks
    plan what still needs to be done, optionally tied to a parcel or crop and
    assigned to a team member.
    """

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=TaskStatus.choices, default=TaskStatus.TODO
    )
    priority = models.CharField(
        max_length=10, choices=TaskPriority.choices, default=TaskPriority.MEDIUM
    )
    category = models.CharField(
        max_length=20, choices=TaskCategory.choices, default=TaskCategory.OTHER
    )
    due_date = models.DateField(null=True, blank=True)
    parcel = models.ForeignKey(
        "farms.Parcel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    crop = models.ForeignKey(
        "farms.Crop",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    assignees = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="assigned_tasks",
        help_text="Team members responsible for this task (zero, one or many).",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_tasks",
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta(TenantScopedModel.Meta):
        ordering = ["status", "due_date", "-priority", "-created_at"]

    def __str__(self) -> str:
        return self.title

    @property
    def is_overdue(self) -> bool:
        if self.status == TaskStatus.DONE or not self.due_date:
            return False
        return self.due_date < timezone.localdate()

    def save(self, *args, **kwargs):
        # Keep completed_at in sync with the DONE status.
        if self.status == TaskStatus.DONE and self.completed_at is None:
            self.completed_at = timezone.now()
        elif self.status != TaskStatus.DONE:
            self.completed_at = None
        super().save(*args, **kwargs)


class TaskActivityAction(models.TextChoices):
    CREATED = "CREATED", "Creada"
    STATUS_CHANGED = "STATUS_CHANGED", "Cambio de estado"
    PRIORITY_CHANGED = "PRIORITY_CHANGED", "Cambio de prioridad"
    CATEGORY_CHANGED = "CATEGORY_CHANGED", "Cambio de categoría"
    ASSIGNED = "ASSIGNED", "Asignación"
    UNASSIGNED = "UNASSIGNED", "Desasignación"
    DUE_DATE_CHANGED = "DUE_DATE_CHANGED", "Cambio de fecha límite"
    EDITED = "EDITED", "Edición"
    COMMENT = "COMMENT", "Comentario"


class TaskActivity(TimeStampedModel):
    """An immutable audit entry for every change made to a task.

    Provides a professional ticket-style activity timeline: who did what and
    when, with the previous and new values for each tracked field.
    """

    task = models.ForeignKey(
        "tasks.Task",
        on_delete=models.CASCADE,
        related_name="activities",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="task_activities",
    )
    action = models.CharField(max_length=24, choices=TaskActivityAction.choices)
    field = models.CharField(max_length=40, blank=True)
    from_value = models.CharField(max_length=255, blank=True)
    to_value = models.CharField(max_length=255, blank=True)
    note = models.CharField(max_length=255, blank=True)
    mentions = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="task_mentions",
        help_text="Team members mentioned (via @) in a comment.",
    )

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["task", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_action_display()} · {self.task_id}"

