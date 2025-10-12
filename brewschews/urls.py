"""Root URL configuration for the Brews & Chews project."""
from django.urls import include, path

urlpatterns = [
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("", include("pages.urls", namespace="pages")),
]