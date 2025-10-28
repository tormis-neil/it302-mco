"""
Views for the accounts app.

Handles:
- Signup: User registration
- Login: Authentication
- Profile: Update user info, change username/password, delete account
- Logout: End user session
"""

from __future__ import annotations

import logging
from typing import Optional

from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db import DatabaseError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import LoginForm, ProfileForm, SignupForm, ChangeUsernameForm, ChangePasswordForm
from .models import AuthenticationEvent, Profile, User
from .utils import get_client_ip

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
) -> None:
    """
    Save authentication attempt to database.

    Called: Every signup/login attempt (success or failure)
    Saves: IP, username, timestamp, success/failure
    Used for: Audit logging and security monitoring
    """
    try:
        AuthenticationEvent.objects.create(
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent[:255],
            username_submitted=username,
            email_submitted=email or "",
            user=user,
            successful=successful,
        )
    except DatabaseError:
        logger.exception("Unable to persist authentication audit event")


@require_http_methods(["GET", "POST"])
def login_view(request: HttpRequest) -> HttpResponse:
    """
    Handle user login.

    Security features:
    - Audit logging: Record all attempts

    Flow:
    - GET: Show login form
    - POST: Validate credentials and login
    """
    ip_address = get_client_ip(request)
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    form = LoginForm(request.POST or None)
    alert_message = ""

    if request.method == "POST":
        if form.is_valid():
            identifier = form.get_identifier()
            password = form.get_password()
            user = form.find_user()  # Find by username or email

            # Check if user exists and password is correct
            if user is None or not user.check_password(password):
                alert_message = "Invalid username or password."
                _record_event(
                    event_type=AuthenticationEvent.EventType.LOGIN,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    username=identifier,
                    user=user,
                    successful=False,
                )
            else:
                # Login successful
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
        if form.is_valid():
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