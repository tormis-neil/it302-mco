"""
Views for the accounts app.

Handles:
- Signup: User registration with rate limiting
- Login: Authentication with account lockout
- Profile: Update user info, change username/password, delete account
- Logout: End user session
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Optional

from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db import DatabaseError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .forms import LoginForm, ProfileForm, SignupForm, ChangeUsernameForm, ChangePasswordForm
from .models import AuthenticationEvent, Profile, User
from .utils import get_client_ip

# Rate limiting settings
SIGNUP_RATE_LIMIT = 5  # Max 5 signups per hour per IP
SIGNUP_RATE_WINDOW = timedelta(hours=1)

LOGIN_RATE_LIMIT = 5  # Max 5 failed logins per 15 min per IP
LOGIN_RATE_WINDOW = timedelta(minutes=15)

LOGIN_LOCK_THRESHOLD = 5  # Lock account after 5 failed attempts
LOGIN_LOCK_DURATION = timedelta(hours=1)  # Lock for 60 minutes

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
    """
    Save authentication attempt to database.
    
    Called: Every signup/login attempt (success or failure)
    Saves: IP, username, timestamp, success/failure, reason
    Used for: Rate limiting and security monitoring
    """
    metadata = {"reason": reason} if reason else {}
    try:
        AuthenticationEvent.objects.create(
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent[:255],
            username_submitted=username,
            email_submitted=email or "",
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
    """
    Check if IP has exceeded rate limit.
    
    How it works:
    1. Calculate cutoff time (now - window)
    2. Count events from this IP since cutoff
    3. Return True if count >= limit
    
    Example: 
    - window = 15 minutes, limit = 5
    - Counts failed logins from IP in last 15 minutes
    - Returns True if 5 or more found
    """
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
    """
    Handle user login with security checks.
    
    Security features:
    1. Rate limiting: Block IP after 5 failed attempts in 15 min
    2. Account lockout: Lock account after 5 wrong passwords
    3. Audit logging: Record all attempts
    
    Flow:
    - GET: Show login form
    - POST: Validate credentials and login
    """
    ip_address = get_client_ip(request)
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    form = LoginForm(request.POST or None)
    alert_message = ""

    if request.method == "POST":
        # Security Check 1: IP rate limiting
        # Block if too many failed attempts from this IP
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
            user = form.find_user()  # Find by username or email

            # Check 1: User exists?
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
            
            # Check 2: Account locked?
            elif user.is_locked():
                # Calculate remaining lockout time
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
            
            # Check 3: Password correct?
            elif not user.check_password(password):
                # Wrong password: increment failed attempts
                user.mark_login_failure()
                
                # Check if we should lock the account now
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
            
            # All checks passed: Login successful
            else:
                user.reset_login_failures()  # Clear failed attempts
                login(request, user)  # Create session
                _record_event(
                    event_type=AuthenticationEvent.EventType.LOGIN,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    username=identifier,
                    user=user,
                    successful=True,
                )
                return redirect("menu:catalog")  # Redirect to menu
        else:
            alert_message = "Enter your username/email and password to continue."

    context = {
        "form": form,
        "alert_message": alert_message,
    }
    return render(request, "accounts/login.html", context)


@require_http_methods(["GET", "POST"])
def signup_view(request: HttpRequest) -> HttpResponse:
    """
    Handle user registration.
    
    Security features:
    - Rate limiting: Max 5 signups per hour per IP
    - Password validation: 12+ chars, uppercase, number, special char
    - Audit logging: Record all attempts
    
    Flow:
    - GET: Show signup form
    - POST: Validate, create user, auto-login
    """
    ip_address = get_client_ip(request)
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    form = SignupForm(request.POST or None)

    if request.method == "POST":
        # Security: Check IP rate limit
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
            # Create user (password automatically hashed)
            user = form.save()
            
            # Auto-login after signup
            login(request, user)
            
            # Log successful signup
            _record_event(
                event_type=AuthenticationEvent.EventType.SIGNUP,
                ip_address=ip_address,
                user_agent=user_agent,
                username=user.username,
                email=user.email,
                user=user,
                successful=True,
            )
            return redirect("menu:catalog")  # Redirect to menu
        else:
            # Form validation failed (duplicate username, weak password, etc.)
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
    """
    Display and update user profile.
    
    Handles three types of updates:
    1. Profile info (display name, phone, bio) - Simple save
    2. Username change - Requires password confirmation
    3. Password change - Requires current password, updates session
    
    Security:
    - @login_required: Must be logged in to access
    - Password confirmation for username changes
    - Current password verification for password changes
    - Session hash updated after password change (keeps user logged in)
    """
    # Get or create profile
    profile, _ = Profile.objects.get_or_create(
        user=request.user,
        defaults={"display_name": request.user.username},
    )
    
    # Initialize forms
    profile_form = ProfileForm(request.POST or None, instance=profile)
    username_form = ChangeUsernameForm(request.user)
    password_form = ChangePasswordForm(request.user)
    
    update_success = False
    update_message = ""
    
    # Determine which form was submitted based on button name
    if request.method == "POST" and "update_profile" in request.POST:
        # Update profile info
        if profile_form.is_valid():
            profile_form.save()
            update_success = True
            update_message = "Profile updated successfully."
    
    elif request.method == "POST" and "change_username" in request.POST:
        # Change username (requires password)
        username_form = ChangeUsernameForm(request.user, request.POST)
        if username_form.is_valid():
            request.user.username = username_form.cleaned_data["new_username"]
            request.user.save(update_fields=['username'])
            update_success = True
            update_message = "Username changed successfully."
    
    elif request.method == "POST" and "change_password" in request.POST:
        # Change password (requires current password)
        password_form = ChangePasswordForm(request.user, request.POST)
        if password_form.is_valid():
            # Save new password (hashed automatically)
            password_form.save()
            
            # CRITICAL: Update session so user stays logged in
            # Without this, changing password logs user out
            update_session_auth_hash(request, request.user)
            
            update_success = True
            update_message = "Password changed successfully."
    
    # Get recent orders for display
    recent_orders = request.user.orders.all()[:3]

    context = {
        "profile_form": profile_form,
        "username_form": username_form,
        "password_form": password_form,
        "update_success": update_success,
        "update_message": update_message,
        "user_email": request.user.email,
        "recent_orders": recent_orders,
    }
    return render(request, "accounts/profile.html", context)


@require_http_methods(["POST"])
def logout_view(request: HttpRequest) -> HttpResponse:
    """
    Log out user and redirect to home.
    
    POST only: Prevents CSRF attacks
    Clears: User session
    """
    logout(request)
    return redirect("pages:home")


@login_required
@require_http_methods(["POST"])
def delete_account_view(request: HttpRequest) -> HttpResponse:
    """
    Delete user account after password confirmation.
    
    Security: Requires password to confirm deletion
    Cascade: Deletes user, profile, and all related data
    """
    password = request.POST.get("password", "")
    
    # Validate password provided
    if not password:
        return redirect("accounts:profile")
    
    # Verify password is correct
    if not request.user.check_password(password):
        return redirect("accounts:profile")
    
    # Delete user account (CASCADE deletes profile too)
    username = request.user.username
    request.user.delete()
    
    # Logout and redirect to home
    logout(request)
    return redirect("pages:home")