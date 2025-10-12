"""URL patterns for the accounts app."""
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/delete/", views.delete_account_view, name="delete_account"),  # ← ADD THIS LINE
    path("logout/", views.logout_view, name="logout"),
]