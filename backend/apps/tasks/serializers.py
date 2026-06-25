from rest_framework import serializers

from apps.tasks.models import Task, TaskActivity


class TaskActivitySerializer(serializers.ModelSerializer):
    action_display = serializers.CharField(
        source="get_action_display", read_only=True
    )
    actor_name = serializers.SerializerMethodField()
    mentions_detail = serializers.SerializerMethodField()

    class Meta:
        model = TaskActivity
        fields = [
            "id", "action", "action_display", "field", "from_value",
            "to_value", "note", "actor", "actor_name", "mentions_detail",
            "created_at",
        ]

    def get_actor_name(self, obj) -> str | None:
        user = obj.actor
        if not user:
            return None
        full = f"{user.first_name} {user.last_name}".strip()
        return full or user.email

    def get_mentions_detail(self, obj) -> list[dict]:
        people = []
        for u in obj.mentions.all():
            name = f"{u.first_name} {u.last_name}".strip() or u.email
            initials = (
                (u.first_name[:1] or u.email[:1]).upper()
                + (u.last_name[:1] or u.email[1:2]).upper()
            )
            people.append({"id": str(u.id), "name": name, "initials": initials})
        return people


class TaskAssigneeSerializer(serializers.Serializer):
    """Compact representation of an assigned team member."""

    id = serializers.UUIDField()
    name = serializers.SerializerMethodField()
    email = serializers.EmailField()
    initials = serializers.SerializerMethodField()

    def get_name(self, obj) -> str:
        full = f"{obj.first_name} {obj.last_name}".strip()
        return full or obj.email

    def get_initials(self, obj) -> str:
        a = (obj.first_name[:1] or obj.email[:1]).upper()
        b = (obj.last_name[:1] or obj.email[1:2]).upper()
        return (a + b) or "·"


class TaskSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    priority_display = serializers.CharField(
        source="get_priority_display", read_only=True
    )
    category_display = serializers.CharField(
        source="get_category_display", read_only=True
    )
    parcel_name = serializers.CharField(source="parcel.name", read_only=True)
    crop_label = serializers.CharField(source="crop.__str__", read_only=True)
    assignees_detail = TaskAssigneeSerializer(
        source="assignees", many=True, read_only=True
    )
    is_overdue = serializers.BooleanField(read_only=True)
    activity_count = serializers.IntegerField(
        source="activities.count", read_only=True
    )

    class Meta:
        model = Task
        fields = [
            "id", "title", "description", "status", "status_display",
            "priority", "priority_display", "category", "category_display",
            "due_date", "parcel", "parcel_name", "crop", "crop_label",
            "assignees", "assignees_detail", "created_by", "completed_at",
            "is_overdue", "activity_count", "created_at",
        ]
        read_only_fields = ["id", "created_by", "completed_at", "created_at"]
        extra_kwargs = {"assignees": {"required": False}}


