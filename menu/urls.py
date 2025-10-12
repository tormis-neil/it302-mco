"""URL patterns for the authenticated menu."""
from django.urls import path

from . import views

app_name = "menu"

urlpatterns = [
    path("", views.catalog, name="catalog"),
]