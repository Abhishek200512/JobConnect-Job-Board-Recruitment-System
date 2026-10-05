"""Notification views."""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
def notification_list(request):
    items = request.user.notifications.all()[:100]
    return render(request, "dashboard/notifications.html", {"notifications": items})


@login_required
@require_POST
def mark_read(request, pk=None):
    if pk:
        request.user.notifications.filter(pk=pk).update(is_read=True)
        return JsonResponse({"success": True, "message": "Notification marked as read."})
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return JsonResponse({"success": True, "message": "All notifications marked as read."})


@login_required
def notifications_count(request):
    return JsonResponse({"count": request.user.notifications.filter(is_read=False).count()})
