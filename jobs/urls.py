from django.urls import path
from . import views

urlpatterns = [
    path("", views.job_list, name="job_list"),
    path("ajax/", views.jobs_ajax, name="jobs_ajax"),
    path("<int:pk>/", views.job_detail, name="job_detail"),
    path("<int:pk>/save/", views.toggle_save_job, name="toggle_save_job"),

    # Recruiter
    path("manage/", views.manage_jobs, name="manage_jobs"),
    path("post/", views.post_job, name="post_job"),
    path("<int:pk>/edit/", views.edit_job, name="edit_job"),
    path("<int:pk>/delete/", views.delete_job, name="delete_job"),
    path("<int:pk>/toggle-status/", views.toggle_job_status, name="toggle_job_status"),
]
