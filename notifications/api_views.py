"""Notifications API: /api/notifications/."""
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListAPIView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class MarkReadAPIView(APIView):
    """POST /api/notifications/mark-read/  body: {"id": 5} or {} for all."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        pk = request.data.get("id")
        if pk:
            updated = Notification.objects.filter(user=request.user, pk=pk).update(is_read=True)
            return Response({"success": True, "updated": updated})
        updated = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"success": True, "updated": updated, "message": "All notifications marked as read."})


class UnreadCountAPIView(APIView):
    """GET /api/notifications/unread-count/"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({"count": Notification.objects.filter(user=request.user, is_read=False).count()})
