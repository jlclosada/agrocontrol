from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, F
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.common.viewsets import TenantScopedViewSet
from apps.tasks import services
from apps.tasks.models import Task, TaskPriority, TaskStatus
from apps.tasks.serializers import TaskActivitySerializer, TaskSerializer
from apps.tenants.models import CooperativeMembership, Role

User = get_user_model()


class TaskViewSet(TenantScopedViewSet):
    serializer_class = TaskSerializer
    queryset = Task.objects.select_related("parcel", "crop").prefetch_related(
        "assignees"
    )
    filterset_fields = ["status", "priority", "category", "parcel", "crop", "assignees"]
    search_fields = ["title", "description"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.get_role() == Role.FARMER:
            qs = qs.filter(parcel__farm__owner=self.request.user)
        return qs.distinct()

    def perform_create(self, serializer):
        task = serializer.save(
            cooperative=self.get_cooperative(),
            created_by=self.request.user,
        )
        services.log_created(task, self.request.user)
        if task.assignees.exists():
            services.log_assignee_changes(task, self.request.user, set(), {})

    def perform_update(self, serializer):
        instance = serializer.instance
        before = services.snapshot(instance)
        before_ids, before_labels = services.assignee_snapshot(instance)
        task = serializer.save()
        services.log_changes(task, self.request.user, before)
        if "assignees" in serializer.validated_data:
            services.log_assignee_changes(
                task, self.request.user, before_ids, before_labels
            )

    @action(detail=True, methods=["get"], url_path="activity")
    def activity(self, request, pk=None):
        """Full audit timeline for a single ticket."""
        task = self.get_object()
        qs = task.activities.select_related("actor").prefetch_related("mentions").all()
        return Response(TaskActivitySerializer(qs, many=True).data)

    @action(detail=True, methods=["post"], url_path="comment")
    def comment(self, request, pk=None):
        """Add a comment to the ticket's audited activity timeline.

        Optionally mentions (@) team members by id; only members of the active
        cooperative are accepted.
        """
        task = self.get_object()
        text = (request.data.get("note") or "").strip()
        if not text:
            raise ValidationError({"note": "El comentario no puede estar vacío."})

        mention_ids = request.data.get("mentions") or []
        mentions = []
        if mention_ids:
            valid_ids = CooperativeMembership.objects.filter(
                cooperative=self.get_cooperative(),
                user_id__in=mention_ids,
                is_active=True,
            ).values_list("user_id", flat=True)
            mentions = list(User.objects.filter(id__in=list(valid_ids)))

        entry = services.log_comment(task, request.user, text, mentions=mentions)
        return Response(TaskActivitySerializer(entry).data, status=201)

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        """Counts by status plus overdue total, for dashboards and badges."""
        qs = self.get_queryset()
        by_status = {
            row["status"]: row["n"]
            for row in qs.values("status").annotate(n=Count("id"))
        }
        overdue = sum(1 for t in qs.exclude(status=TaskStatus.DONE) if t.is_overdue)
        return Response(
            {
                "todo": by_status.get(TaskStatus.TODO, 0),
                "in_progress": by_status.get(TaskStatus.IN_PROGRESS, 0),
                "blocked": by_status.get(TaskStatus.BLOCKED, 0),
                "done": by_status.get(TaskStatus.DONE, 0),
                "overdue": overdue,
                "total": qs.count(),
            }
        )

    @action(detail=False, methods=["get"], url_path="metrics")
    def metrics(self, request):
        """Professional KPI bundle for the board header and dashboards."""
        qs = self.get_queryset()
        total = qs.count()
        by_status = {
            row["status"]: row["n"]
            for row in qs.values("status").annotate(n=Count("id"))
        }
        by_priority = {
            row["priority"]: row["n"]
            for row in qs.values("priority").annotate(n=Count("id"))
        }
        done = by_status.get(TaskStatus.DONE, 0)
        active = qs.exclude(status=TaskStatus.DONE)
        overdue = sum(1 for t in active if t.is_overdue)

        # Average cycle time (creation -> completion) in days.
        cycle = qs.filter(
            status=TaskStatus.DONE, completed_at__isnull=False
        ).aggregate(avg=Avg(F("completed_at") - F("created_at")))["avg"]
        avg_cycle_days = round(cycle.total_seconds() / 86400, 1) if cycle else None

        # Throughput: tasks completed in the last 7 / 30 days.
        now = timezone.now()
        completed_7d = qs.filter(
            status=TaskStatus.DONE, completed_at__gte=now - timedelta(days=7)
        ).count()
        completed_30d = qs.filter(
            status=TaskStatus.DONE, completed_at__gte=now - timedelta(days=30)
        ).count()

        # Due soon: not done, due within 3 days and not already overdue.
        today = timezone.localdate()
        due_soon = active.filter(
            due_date__gte=today, due_date__lte=today + timedelta(days=3)
        ).count()

        completion_rate = round(done / total * 100, 1) if total else 0.0

        return Response(
            {
                "total": total,
                "todo": by_status.get(TaskStatus.TODO, 0),
                "in_progress": by_status.get(TaskStatus.IN_PROGRESS, 0),
                "blocked": by_status.get(TaskStatus.BLOCKED, 0),
                "done": done,
                "overdue": overdue,
                "due_soon": due_soon,
                "completion_rate": completion_rate,
                "avg_cycle_days": avg_cycle_days,
                "completed_7d": completed_7d,
                "completed_30d": completed_30d,
                "by_priority": {
                    "high": by_priority.get(TaskPriority.HIGH, 0),
                    "medium": by_priority.get(TaskPriority.MEDIUM, 0),
                    "low": by_priority.get(TaskPriority.LOW, 0),
                },
            }
        )

