"""Views for the accounts app."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Optional

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db import DatabaseError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .forms import LoginForm, ProfileForm, SignupForm
from .models import AuthenticationEvent, Profile, User, digest_email
from .utils import get_client_ip

SIGNUP_RATE_LIMIT = 5
SIGNUP_RATE_WINDOW = timedelta(hours=1)
LOGIN_RATE_LIMIT = 5
LOGIN_RATE_WINDOW = timedelta(minutes=15)
LOGIN_LOCK_THRESHOLD = 5
LOGIN_LOCK_DURATION = timedelta(hours=1)

logger = logging.getLogger(__name__)

def _record_event(
    *,
    event_type: str,
    ip_address: str,
    user_agent: str,
    username: str = "",
    email: Optional[str] = None,
    user: Optional[User] = None,
    successful: bool,
    reason: Optional[str] = None,
) -> None:
    """Persist an authentication audit event."""

    metadata = {"reason": reason} if reason else {}
    try:
        AuthenticationEvent.objects.create(
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent[:255],
            username_submitted=username,
            email_digest=digest_email(email) if email else None,
            user=user,
            successful=successful,
            metadata=metadata,
        )
    except DatabaseError:
        logger.exception("Unable to persist authentication audit event")

def _is_rate_limited(
    *,
    event_type: str,
    ip_address: str,
    window: timedelta,
    limit: int,
    successful: Optional[bool] = None,
) -> bool:
    cutoff = timezone.now() - window
    try:
        queryset = AuthenticationEvent.objects.filter(
            event_type=event_type,
            ip_address=ip_address,
            created_at__gte=cutoff,
        )
        if successful is not None:
            queryset = queryset.filter(successful=successful)
        return queryset.count() >= limit
    except DatabaseError:
        logger.exception("Unable to evaluate authentication rate limits")
        return False


@require_http_methods(["GET", "POST"])
def login_view(request: HttpRequest) -> HttpResponse:
    """Authenticate a user following the PRD's security requirements."""

    ip_address = get_client_ip(request)
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    form = LoginForm(request.POST or None)
    alert_message = ""

    if request.method == "POST":
        if _is_rate_limited(
            event_type=AuthenticationEvent.EventType.LOGIN,
            ip_address=ip_address,
            window=LOGIN_RATE_WINDOW,
            limit=LOGIN_RATE_LIMIT,
            successful=False,
        ):
            alert_message = "Too many sign-in attempts. Please try again in 15 minutes."
            _record_event(
                event_type=AuthenticationEvent.EventType.LOGIN,
                ip_address=ip_address,
                user_agent=user_agent,
                username=form.data.get("identifier", ""),
                successful=False,
                reason="ip_rate_limited",
            )
        elif form.is_valid():
            identifier = form.get_identifier()
            password = form.get_password()
            user = form.find_user()

            if user is None:
                alert_message = "Invalid username or password."
                _record_event(
                    event_type=AuthenticationEvent.EventType.LOGIN,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    username=identifier,
                    successful=False,
                    reason="unknown_identifier",
                )
            elif user.is_locked():
                remaining_seconds = int((user.locked_until - timezone.now()).total_seconds()) if user.locked_until else 0
                remaining_minutes = max(1, remaining_seconds // 60) if remaining_seconds > 0 else 60
                alert_message = f"Your account is locked. Try again in {remaining_minutes} minutes."
                _record_event(
                    event_type=AuthenticationEvent.EventType.LOGIN,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    username=identifier,
                    user=user,
                    successful=False,
                    reason="account_locked",
                )
            elif not user.check_password(password):
                user.mark_login_failure()
                locked_now = False
                if user.failed_login_attempts >= LOGIN_LOCK_THRESHOLD:
                    user.lock_for(LOGIN_LOCK_DURATION)
                    user.failed_login_attempts = 0
                    user.save(update_fields=["failed_login_attempts"])
                    locked_now = True

                alert_message = (
                    "Too many failed attempts. Your account is locked for 60 minutes."
                    if locked_now
                    else "Invalid username or password."
                )
                _record_event(
                    event_type=AuthenticationEvent.EventType.LOGIN,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    username=identifier,
                    user=user,
                    successful=False,
                    reason="password_mismatch" if not locked_now else "account_locked",
                )
            else:
                user.reset_login_failures()
                login(request, user)
                _record_event(
                    event_type=AuthenticationEvent.EventType.LOGIN,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    username=identifier,
                    user=user,
                    successful=True,
                )
                return redirect("menu:catalog")
        else:
            alert_message = "Enter your username/email and password to continue."

    context = {
        "form": form,
        "alert_message": alert_message,
    }
    return render(request, "accounts/login.html", context)


@require_http_methods(["GET", "POST"])
def signup_view(request: HttpRequest) -> HttpResponse:
    """Register a new user with rate limiting and auditing."""

    ip_address = get_client_ip(request)
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    form = SignupForm(request.POST or None)

    if request.method == "POST":
        if _is_rate_limited(
            event_type=AuthenticationEvent.EventType.SIGNUP,
            ip_address=ip_address,
            window=SIGNUP_RATE_WINDOW,
            limit=SIGNUP_RATE_LIMIT,
        ):
            form.add_error(None, "Too many sign-up attempts from this network. Please try again later.")
            _record_event(
                event_type=AuthenticationEvent.EventType.SIGNUP,
                ip_address=ip_address,
                user_agent=user_agent,
                username=form.data.get("username", ""),
                email=form.data.get("email"),
                successful=False,
                reason="ip_rate_limited",
            )
        elif form.is_valid():
            user = form.save()
            login(request, user)
            _record_event(
                event_type=AuthenticationEvent.EventType.SIGNUP,
                ip_address=ip_address,
                user_agent=user_agent,
                username=user.username,
                email=user.email,
                user=user,
                successful=True,
            )
            return redirect("menu:catalog")
        else:
            _record_event(
                event_type=AuthenticationEvent.EventType.SIGNUP,
                ip_address=ip_address,
                user_agent=user_agent,
                username=form.data.get("username", ""),
                email=form.data.get("email"),
                successful=False,
                reason="validation_error",
            )

    context = {
        "form": form,
    }
    return render(request, "accounts/signup.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def profile_view(request: HttpRequest) -> HttpResponse:
    """Render and update the authenticated user's profile."""

    profile, _ = Profile.objects.get_or_create(
        user=request.user,
        defaults={"display_name": request.user.username},
    )
    form = ProfileForm(request.POST or None, instance=profile)
    update_success = False

    if request.method == "POST" and form.is_valid():
        form.save()
        update_success = True

    recent_orders = request.user.orders.all()[:3]

    context = {
        "form": form,
        "update_success": update_success,
        "user_email": request.user.email,
        "recent_orders": recent_orders,
    }
    return render(request, "accounts/profile.html", context)


@require_http_methods(["POST"])
def logout_view(request: HttpRequest) -> HttpResponse:
    """Log out the current user using a POST-only endpoint."""

    logout(request)
    return redirect("pages:home")