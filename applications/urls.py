from django.urls import path
from . import views

urlpatterns = [
    # Seeker
    path("apply/<int:pk>/", views.apply_job, name="apply_job"),
    path("applied/", views.applied_jobs, name="applied_jobs"),
    path("saved/", views.saved_jobs, name="saved_jobs"),
    path("withdraw/<int:pk>/", views.withdraw_application, name="withdraw_application"),

    # Recruiter
    path("manage/", views.applicants, name="applicants"),
    path("manage/<int:pk>/", views.job_applicants, name="job_applicants"),
    path("status/<int:pk>/update/", views.update_status, name="update_status"),
    path("interview/<int:pk>/invite/", views.send_interview_invite, name="send_interview_invite"),
    path("resume/<int:pk>/download/", views.download_resume, name="download_resume"),
]
