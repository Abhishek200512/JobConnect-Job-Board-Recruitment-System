from django.urls import path
from . import api_views

urlpatterns = [
    path("", api_views.ApplicationListCreateAPIView.as_view(), name="api_applications"),
    path("saved/", api_views.SavedJobListAPIView.as_view(), name="api_saved_jobs"),
    path("<int:pk>/status/", api_views.ApplicationStatusAPIView.as_view(), name="api_application_status"),
    path("<int:pk>/withdraw/", api_views.ApplicationWithdrawAPIView.as_view(), name="api_application_withdraw"),
]
