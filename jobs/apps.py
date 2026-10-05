"""JobConnect — jobs app: categories, jobs, search and recruiter CRUD."""
from django.apps import AppConfig


class JobsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "jobs"
