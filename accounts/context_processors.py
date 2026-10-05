"""Context processor: unread notifications count for the navbar bell."""
from notifications.models import Notification  # noqa: F401


def unread_notifications(request):
    count = 0
    recent = []
    if request.user.is_authenticated:
        recent = request.user.notifications.filter(is_read=False)[:5]
        count = request.user.notifications.filter(is_read=False).count()
    return {
        "unread_notifications_count": count,
        "recent_notifications": recent,
    }
