"""Analytics API: /api/analytics/."""
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from datetime import date
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from applications.models import Application
from companies.models import Company
from jobs.models import Job

User = get_user_model()


class AnalyticsSummaryAPIView(APIView):
    """GET /api/analytics/summary/ — admin dashboard analytics payload."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_admin_role:
            return Response({"success": False, "error": "Admin access required."}, status=403)

        users = User.objects.all()
        jobs = Job.objects.all()
        apps = Application.objects.all()

        today = date.today()
        months, reg, jobs_m, apps_m = [], [], [], []
        for i in range(5, -1, -1):
            m = (today.month - i - 1) % 12 + 1
            y = today.year + (today.month - i - 1) // 12
            months.append(date(y, m, 1).strftime("%b"))
            reg.append(users.filter(created_at__year=y, created_at__month=m).count())
            jobs_m.append(jobs.filter(created_at__year=y, created_at__month=m).count())
            apps_m.append(apps.filter(applied_at__year=y, applied_at__month=m).count())

        by_cat = jobs.values("category__name").annotate(n=Count("id")).order_by("-n")[:8]
        by_status = apps.values("status").annotate(n=Count("id"))

        return Response({
            "counts": {
                "users": users.count(),
                "seekers": users.filter(role=User.Role.SEEKER).count(),
                "recruiters": users.filter(role=User.Role.RECRUITER).count(),
                "companies": Company.objects.count(),
                "jobs": jobs.count(),
                "active_jobs": jobs.filter(status=Job.Status.ACTIVE).count(),
                "applications": apps.count(),
                "selected": apps.filter(status=Application.Status.SELECTED).count(),
            },
            "trends": {"months": months, "registrations": reg, "jobs_created": jobs_m, "applications": apps_m},
            "jobs_by_category": {r["category__name"] or "Other": r["n"] for r in by_cat},
            "applications_by_status": {Application.Status(s["status"]).label: s["n"] for s in by_status},
        })


class RecruiterAnalyticsAPIView(APIView):
    """GET /api/analytics/recruiter/ — analytics scoped to the logged-in recruiter."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_recruiter:
            return Response({"success": False, "error": "Recruiter access required."}, status=403)

        jobs = Job.objects.filter(posted_by=request.user)
        apps = Application.objects.filter(job__posted_by=request.user)
        by_status = apps.values("status").annotate(n=Count("id"))
        return Response({
            "counts": {
                "total_jobs": jobs.count(),
                "active_jobs": jobs.filter(status=Job.Status.ACTIVE).count(),
                "applicants": apps.count(),
                "shortlisted": apps.filter(status=Application.Status.SHORTLISTED).count(),
                "interviews": apps.filter(status=Application.Status.INTERVIEW).count(),
                "selected": apps.filter(status=Application.Status.SELECTED).count(),
            },
            "applications_by_status": {Application.Status(s["status"]).label: s["n"] for s in by_status},
        })


def api_index(request):
    """Simple JSON index of API endpoints (used by /api/)."""
    from django.http import JsonResponse

    return JsonResponse({
        "name": "JobConnect API",
        "endpoints": {
            "auth": ["/api/auth/register/", "/api/auth/otp/request/", "/api/auth/otp/verify/", "/api/auth/login-status/"],
            "users": ["/api/users/me/", "/api/users/profile/", "/api/users/seekers/"],
            "jobs": ["/api/jobs/", "/api/jobs/<id>/", "/api/jobs/<id>/save/", "/api/jobs/categories/"],
            "companies": ["/api/companies/", "/api/companies/<id>/"],
            "applications": ["/api/applications/", "/api/applications/<id>/status/", "/api/applications/<id>/withdraw/", "/api/applications/saved/"],
            "notifications": ["/api/notifications/", "/api/notifications/mark-read/", "/api/notifications/unread-count/"],
            "analytics": ["/api/analytics/summary/", "/api/analytics/recruiter/"],
        },
    })
