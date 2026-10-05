from django.urls import path
from . import api_views

urlpatterns = [
    path("", api_views.NotificationListAPIView.as_view(), name="api_notifications"),
    path("mark-read/", api_views.MarkReadAPIView.as_view(), name="api_notifications_mark_read"),
    path("unread-count/", api_views.UnreadCountAPIView.as_view(), name="api_notifications_unread_count"),
]
