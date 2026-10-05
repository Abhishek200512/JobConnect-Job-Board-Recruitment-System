"""Applications API: /api/applications/."""
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from jobs.models import Job
from jobs.serializers import JobListSerializer
from notifications.models import Notification

from .models import Application, SavedJob
from .serializers import (
    ApplicationCreateSerializer,
    ApplicationListSerializer,
    ApplicationStatusSerializer,
)


class ApplicationListCreateAPIView(generics.ListCreateAPIView):
    """
    GET  /api/applications/  — seeker: own applications; recruiter: applicants to their jobs
    POST /api/applications/  — seeker creates an application (multipart/form-data for resume)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ApplicationCreateSerializer
        return ApplicationListSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Application.objects.select_related("job", "job__company", "applicant")
        if user.is_seeker:
            return qs.filter(applicant=user)
        if user.is_recruiter:
            return qs.filter(job__posted_by=user)
        return qs.none()

    def create(self, request, *args, **kwargs):
        if not request.user.is_seeker:
            return Response({"success": False, "error": "Only job seekers can apply."}, status=403)
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        app = serializer.save(applicant=request.user)
        Notification.notify(
            app.job.posted_by, "New application received",
            f"{request.user.display_name} applied for {app.job.title}.",
            url=f"/applications/manage/{app.job.pk}/",
        )
        out = ApplicationListSerializer(app, context=self.get_serializer_context())
        return Response(
            {"success": True, "message": "Application submitted successfully.", "application": out.data},
            status=status.HTTP_201_CREATED,
        )


class ApplicationStatusAPIView(APIView):
    """PATCH /api/applications/<pk>/status/ — recruiter updates status + notifies applicant."""
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        app = get_object_or_404(Application, pk=pk, job__posted_by=request.user)
        s = ApplicationStatusSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        old = app.get_status_display()
        app.status = s.validated_data["status"]
        if s.validated_data.get("note"):
            app.recruiter_note = s.validated_data["note"]
        app.save()

        labels = dict(Application.Status.choices)
        Notification.notify(
            app.applicant, "Application update",
            f"Your application for {app.job.title} moved from “{old}” to “{labels[app.status]}”.",
            url="/applications/applied/",
        )
        return Response({"success": True, "status": app.status, "status_display": labels[app.status]})


class ApplicationWithdrawAPIView(APIView):
    """DELETE /api/applications/<pk>/withdraw/ — seeker withdraws an early-stage application."""
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        app = get_object_or_404(Application, pk=pk, applicant=request.user)
        if app.status not in (Application.Status.APPLIED, Application.Status.UNDER_REVIEW):
            return Response({"success": False, "error": "Application can no longer be withdrawn."}, status=400)
        app.delete()
        return Response({"success": True, "message": "Application withdrawn."})


class SavedJobOutSerializer(serializers.ModelSerializer):
    job = JobListSerializer(read_only=True)

    class Meta:
        model = SavedJob
        fields = ["id", "job", "created_at"]


class SavedJobListAPIView(generics.ListAPIView):
    """GET /api/applications/saved/ — seeker's saved jobs."""
    serializer_class = SavedJobOutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SavedJob.objects.filter(user=self.request.user).select_related("job", "job__company")
