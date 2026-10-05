"""Notification model."""
from django.conf import settings
from django.db import models


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    title = models.CharField(max_length=150)
    message = models.TextField()
    url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read"])]

    def __str__(self):
        return f"To {self.user}: {self.title}"

    @classmethod
    def notify(cls, user, title, message, url=""):
        return cls.objects.create(user=user, title=title, message=message, url=url)

    def ago_display(self):
        from django.utils.timesince import timesince

        return timesince(self.created_at) + " ago"
