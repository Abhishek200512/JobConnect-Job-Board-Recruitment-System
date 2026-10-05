"""DRF serializers for notifications."""
from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    ago = serializers.CharField(source="ago_display", read_only=True)

    class Meta:
        model = Notification
        fields = ["id", "title", "message", "url", "is_read", "created_at", "ago"]
