"""
URL patterns for the accounts app.

This file defines all URL routes related to user authentication and profile management.

Routes:
-------
- /accounts/login/          → Login page (GET: show form, POST: authenticate)
- /accounts/signup/         → Signup page (GET: show form, POST: create account)
- /accounts/profile/        → Profile page (GET: view, POST: update)
- /accounts/profile/delete/ → Delete account (POST only: requires password)
- /accounts/logout/         → Logout (POST only: ends session)

Namespace:
----------
- app_name = "accounts"
- Usage in templates: {% url 'accounts:login' %}
- Usage in views: redirect('accounts:profile')

URL Structure:
--------------
These URLs are mounted under /accounts/ prefix in brewschews/urls.py
Example: /accounts/login/ calls views.login_view()

Related Files:
--------------
- accounts/views.py: View functions that handle these URLs
- templates/accounts/*.html: Templates rendered by views
- brewschews/urls.py: Includes these URLs with path("accounts/", ...)

Security Notes:
---------------
- logout and delete_account use POST only (CSRF protection)
- All views except login/signup require authentication
- Profile changes require password confirmation
"""

from django.urls import path

from . import views

# Namespace for reverse URL lookups
# Allows {% url 'accounts:login' %} in templates
app_name = "accounts"

urlpatterns = [
    # Login endpoint
    # URL: /accounts/login/
    # View: accounts.views.login_view
    # Methods: GET (show form), POST (authenticate)
    # Template: accounts/login.html
    # Redirect after success: menu:catalog
    path("login/", views.login_view, name="login"),
    
    # Signup endpoint
    # URL: /accounts/signup/
    # View: accounts.views.signup_view
    # Methods: GET (show form), POST (create user)
    # Template: accounts/signup.html
    # Redirect after success: menu:catalog
    path("signup/", views.signup_view, name="signup"),
    
    # Profile management endpoint
    # URL: /accounts/profile/
    # View: accounts.views.profile_view
    # Methods: GET (display), POST (update profile/username/password)
    # Template: accounts/profile.html
    # Requires: @login_required
    path("profile/", views.profile_view, name="profile"),
    
    # Delete account endpoint
    # URL: /accounts/profile/delete/
    # View: accounts.views.delete_account_view
    # Methods: POST only (security: prevents accidental deletion)
    # Requires: @login_required + password confirmation
    # Redirect after success: pages:home
    path("profile/delete/", views.delete_account_view, name="delete_account"),
    
    # Logout endpoint
    # URL: /accounts/logout/
    # View: accounts.views.logout_view
    # Methods: POST only (CSRF protection)
    # Redirect after success: pages:home
    path("logout/", views.logout_view, name="logout"),
]