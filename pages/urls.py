"""URL patterns for the public-facing pages."""
from django.urls import path

from . import views

app_name = "pages"

urlpatterns = [
    path("", views.home, name="home"),
    path("menu/preview/", views.menu_preview, name="menu_preview"),
]