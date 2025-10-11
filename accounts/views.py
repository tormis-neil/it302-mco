"""Views for the accounts app."""
from django.shortcuts import render
from django.views.decorators.http import require_GET


@require_GET
def login_view(request):
    """Render the sign-in page (UI only for now)."""
    return render(request, "accounts/login.html")


@require_GET
def signup_view(request):
    """Render the sign-up page (UI only for now)."""
    return render(request, "accounts/signup.html")


@require_GET
def profile_view(request):
    """Render the placeholder profile page until functionality is implemented."""
    return render(request, "accounts/profile.html")