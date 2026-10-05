"""Jobs API: /api/jobs/."""
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from applications.models import SavedJob

from .models import Job, Category
from .serializers import JobListSerializer, JobDetailSerializer, CategorySerializer
from .views import _filtered_jobs


class JobListAPIView(generics.ListAPIView):
    """GET /api/jobs/ — supports all the same filters as the website."""
    serializer_class = JobListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return _filtered_jobs(self.request)


class JobDetailAPIView(generics.RetrieveAPIView):
    queryset = Job.objects.filter(status=Job.Status.ACTIVE)
    serializer_class = JobDetailSerializer
    permission_classes = [permissions.AllowAny]


class SaveJobAPIView(APIView):
    """POST /api/jobs/<pk>/save/ — toggle saved job (seeker only)."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        if not request.user.is_seeker:
            return Response({"success": False, "error": "Only job seekers can save jobs."}, status=403)
        from .models import Job
        job = Job.objects.filter(pk=pk, status=Job.Status.ACTIVE).first()
        if not job:
            return Response({"success": False, "error": "Job not found."}, status=404)
        saved, created = SavedJob.objects.get_or_create(user=request.user, job=job)
        if not created:
            saved.delete()
            return Response({"success": True, "saved": False})
        return Response({"success": True, "saved": True})


class CategoryListAPIView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
