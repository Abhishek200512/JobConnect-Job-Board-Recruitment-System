"""Serves the /api/ JSON index."""
from django.urls import path
from . import api_views

urlpatterns = [
    path("", api_views.api_index, name="api_index"),
]
