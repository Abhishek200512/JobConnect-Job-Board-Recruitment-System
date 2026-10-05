from django.urls import path
from . import api_views

urlpatterns = [
    path("summary/", api_views.AnalyticsSummaryAPIView.as_view(), name="api_analytics_summary"),
    path("recruiter/", api_views.RecruiterAnalyticsAPIView.as_view(), name="api_analytics_recruiter"),
]
