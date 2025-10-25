"""
Django settings for the Brews & Chews project.

Configuration Sections:
- Basic Django settings (SECRET_KEY, DEBUG, ALLOWED_HOSTS)
- Installed apps and middleware
- Template configuration
- Database (SQLite3)
- Authentication settings
- Password hashing (Argon2)
- Password validators
- Internationalization
- Static files

Security Features:
- Argon2 password hashing (102,400 iterations)
- Strong password validation (12+ chars, uppercase, number, special)
- CSRF protection
- Session security

Environment Variables:
- DJANGO_SECRET_KEY: Secret key for cryptographic signing
- DJANGO_DEBUG: Debug mode (0/1)
- DJANGO_ALLOWED_HOSTS: Comma-separated list of allowed hosts
- DJANGO_DB_NAME: Database filename
- ACCOUNT_EMAIL_ENCRYPTION_KEY: (Optional) Key for email encryption
"""

from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - optional dependency for local dev
    def load_dotenv(*_args, **_kwargs):  # type: ignore[override]
        """Fallback load_dotenv if python-dotenv is unavailable."""
        return False

# Build paths inside the project like this: BASE_DIR / 'subdir'
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file (if exists)
load_dotenv(BASE_DIR / ".env")

# SECURITY WARNING: keep the secret key used in production secret!
# Used for: Cryptographic signing (sessions, CSRF tokens, password reset)
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

# Auto-generate a key for development if not provided
if not SECRET_KEY:
    import uuid
    from django.core.exceptions import ImproperlyConfigured

    # In development, auto-generate (shows warning)
    if os.environ.get("DJANGO_DEBUG", "0") == "1":
        SECRET_KEY = "dev-only-" + str(uuid.uuid4())
        print("⚠️  WARNING: Using auto-generated SECRET_KEY for development only!")
        print("   For production, set DJANGO_SECRET_KEY in your environment variables.")
    else:
        # In production, fail loudly if missing
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY environment variable is required!\n"
            "Generate one with: python -c 'from django.core.management.utils "
            "import get_random_secret_key; print(get_random_secret_key())'"
        )

# SECURITY WARNING: don't run with debug turned on in production!
# Debug mode shows detailed error pages with sensitive information
# Changed default from "1" to "0" for security (must explicitly enable debug)
DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"

# List of hosts/domains this site can serve
# Example: ['brewschews.com', 'www.brewschews.com']
ALLOWED_HOSTS = [
    host.strip() 
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") 
    if host.strip()
]


def _derive_default_account_key(secret: str) -> str:
    """
    Derive a deterministic base64 encoded 32-byte key for local development.
    
    Purpose: Generate encryption key from SECRET_KEY for email encryption
    Note: Currently not used (email stored as plaintext for development)
    
    Process:
    1. Create unique string from SECRET_KEY
    2. Hash with SHA-256 (produces 32 bytes)
    3. Encode as base64 for storage
    
    Args:
        secret: Django SECRET_KEY
    
    Returns:
        Base64-encoded 32-byte key
    """
    digest = hashlib.sha256(f"{secret}:accounts-email-key".encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii")


# Application definition
# Order matters: apps listed first can override templates from apps listed later
INSTALLED_APPS = [
    "django.contrib.auth",           # User authentication
    "django.contrib.contenttypes",   # Content type framework
    "django.contrib.sessions",       # Session management
    "django.contrib.messages",       # One-time notification messages
    "django.contrib.staticfiles",    # Static file management (CSS, JS, images)
    "accounts",                      # Custom user authentication app
    "menu",                          # Menu catalog app
    "orders",                        # Cart and order management app
    "pages",                         # Public-facing pages app
]

# Middleware: Request/response processing pipeline
# Order matters: middleware executes top-to-bottom on requests, bottom-to-top on responses
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",           # Security headers
    "django.contrib.sessions.middleware.SessionMiddleware",    # Session management
    "django.middleware.common.CommonMiddleware",               # Common operations
    "django.middleware.csrf.CsrfViewMiddleware",              # CSRF protection
    "django.contrib.auth.middleware.AuthenticationMiddleware", # User authentication
    "django.contrib.messages.middleware.MessageMiddleware",    # Message framework
    "django.middleware.clickjacking.XFrameOptionsMiddleware", # Clickjacking protection
]

# Root URL configuration module
ROOT_URLCONF = "brewschews.urls"

# Template configuration
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # Project-level templates directory
        "APP_DIRS": True,  # Look for templates in each app's templates/ folder
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",      # Debug info
                "django.template.context_processors.request",    # Request object
                "django.contrib.auth.context_processors.auth",   # User and perms
                "django.contrib.messages.context_processors.messages",  # Messages
            ],
            "builtins": [
                "django.templatetags.static",  # {% static %} tag available everywhere
            ],
        },
    }
]

# WSGI application path for deployment
WSGI_APPLICATION = "brewschews.wsgi.application"

# ASGI application path for async support
ASGI_APPLICATION = "brewschews.asgi.application"

# Database configuration
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",  # SQLite for development
        "NAME": BASE_DIR / os.environ.get("DJANGO_DB_NAME", "db.sqlite3"),
    }
}

# Email encryption key (optional feature, not currently used)
# If implemented, would encrypt email addresses at rest using AES-256-GCM
ACCOUNT_EMAIL_ENCRYPTION_KEY = os.environ.get(
    "ACCOUNT_EMAIL_ENCRYPTION_KEY", 
    _derive_default_account_key(SECRET_KEY)
)

# ═══════════════════════════════════════════════════════════════════
# AUTHENTICATION & SECURITY SETTINGS
# ═══════════════════════════════════════════════════════════════════

# Use custom User model instead of Django's default
# Points to: accounts.models.User
AUTH_USER_MODEL = "accounts.User"

# ═══════════════════════════════════════════════════════════════════
# PASSWORD HASHING CONFIGURATION
# ═══════════════════════════════════════════════════════════════════
"""
PASSWORD HASHERS: Algorithms used to hash passwords

Priority Order (top = preferred):
1. Argon2PasswordHasher - Primary hasher (most secure)
2-4. Fallback hashers for legacy password migration

Argon2 Details:
- Algorithm: Argon2id (hybrid mode, resistant to side-channel attacks)
- Version: 19 (latest as of 2023)
- Memory: 102,400 KB (~100 MB)
- Iterations: 2 (time cost)
- Parallelism: 8 threads
- Salt: 16 bytes (auto-generated, unique per password)

Why Argon2?
- Winner of Password Hashing Competition 2015
- Memory-hard: Expensive for GPU/ASIC attacks
- Resistant to: Rainbow tables, brute force, side-channel attacks
- Used by: Microsoft, 1Password, Bitwarden
- Recommended by: OWASP, security experts

Example Hash:
Input:  "MyPassword123!"
Output: "argon2$argon2id$v=19$m=102400,t=2,p=8$randomsalt$hashedvalue"
        └─────┬─────┘ └───┬───┘ └┬┘ └────┬────┘ └────┬────┘ └────┬────┘
         algorithm   variant ver  memory   time,para    salt        hash

Performance:
- Hashing time: ~0.5 seconds (intentionally slow to prevent brute force)
- Verification time: ~0.5 seconds (same as hashing)
- Computational cost: High (102,400 iterations × 100 MB memory)

Security Trade-off:
- Slower = More secure (harder to crack)
- User experience: 0.5s delay is acceptable for login/signup
- Attack resistance: Would take years to crack a single password

Where Used:
- accounts/models.py Line 42: user.set_password() - Hash new passwords
- accounts/views.py Line 161: user.check_password() - Verify login passwords
- accounts/forms.py Line 328: Password change hashing
"""
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",      # Primary (use this)
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",      # Fallback 1
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",  # Fallback 2
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",# Fallback 3
]

# ═══════════════════════════════════════════════════════════════════
# PASSWORD VALIDATION RULES
# ═══════════════════════════════════════════════════════════════════
"""
PASSWORD VALIDATORS: Enforce strong password requirements

These validators run during:
- Signup (accounts/forms.py Line 62)
- Password change (accounts/forms.py Line 205)
- Django admin user creation

Validation Rules:
1. UserAttributeSimilarityValidator
   - Prevents: Password too similar to username/email
   - Example: username="johndoe" + password="johndoe123" → Rejected

2. MinimumLengthValidator (min_length=12)
   - Requires: At least 12 characters
   - Example: "short" → Rejected, "LongPassword123!" → Accepted

3. CommonPasswordValidator
   - Prevents: Commonly used passwords (e.g., "password123")
   - Uses: List of ~20,000 most common passwords
   - Example: "password" → Rejected, "MyUniquePass123!" → Accepted

4. NumericPasswordValidator
   - Prevents: Passwords that are entirely numeric
   - Example: "12345678" → Rejected, "Pass123!" → Accepted

Custom Requirements (accounts/forms.py):
- At least one uppercase letter (A-Z)
- At least one number (0-9)
- At least one special character (!@#$%^&*)

Combined Requirements:
✓ 12+ characters
✓ Not too similar to username/email
✓ Not in common password list
✓ Not entirely numeric
✓ Has uppercase letter
✓ Has number
✓ Has special character

Example Valid Password: "CoffeeTime2024!"
Example Invalid Passwords:
- "short" (too short)
- "password123" (too common)
- "12345678901234" (entirely numeric)
- "longpassword" (no uppercase, no number, no special)
"""
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},  # Require 12+ characters
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# ═══════════════════════════════════════════════════════════════════
# INTERNATIONALIZATION & LOCALIZATION
# ═══════════════════════════════════════════════════════════════════

# Language code for this installation
LANGUAGE_CODE = "en-us"

# Time zone for this installation
# Used for: timestamp display, scheduling, date filtering
TIME_ZONE = "Asia/Manila"

# Enable Django translation system
USE_I18N = True

# Enable timezone-aware datetimes
# All datetime objects will be timezone-aware (not naive)
USE_TZ = True

# ═══════════════════════════════════════════════════════════════════
# STATIC FILES (CSS, JavaScript, Images)
# ═══════════════════════════════════════════════════════════════════

# URL prefix for static files (e.g., /static/css/style.css)
STATIC_URL = "/static/"

# Directories where Django looks for static files during development
STATICFILES_DIRS = [BASE_DIR / "static"]

# Directory where collectstatic will collect files for production
STATIC_ROOT = BASE_DIR / "staticfiles"

# ═══════════════════════════════════════════════════════════════════
# AUTHENTICATION URL CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# URL to redirect to for login (@login_required decorator)
# If user tries to access @login_required view while not logged in:
# → Redirect to /accounts/login/?next=/original/url/
LOGIN_URL = "accounts:login"

# URL to redirect to after successful login
# Default destination after user logs in
LOGIN_REDIRECT_URL = "menu:catalog"

# URL to redirect to after logout
# Where users go after clicking logout
LOGOUT_REDIRECT_URL = "pages:home"

# ═══════════════════════════════════════════════════════════════════
# SECURITY HEADERS & COOKIE PROTECTION
# ═══════════════════════════════════════════════════════════════════
"""
These settings implement defense-in-depth security for session and CSRF cookies.

HTTPONLY cookies prevent JavaScript from accessing sensitive cookies, protecting
against XSS attacks that attempt to steal session tokens.

SAMESITE='Lax' prevents cookies from being sent on cross-site requests, which
protects against CSRF attacks initiated from external websites.

In production with HTTPS, additional SECURE flags should be enabled to ensure
cookies are only transmitted over encrypted connections.
"""

# Cookie security flags (work in both development and production)
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript from reading session cookie
CSRF_COOKIE_HTTPONLY = True     # Prevent JavaScript from reading CSRF token
SESSION_COOKIE_SAMESITE = 'Lax' # Prevent CSRF via cross-site requests
CSRF_COOKIE_SAMESITE = 'Lax'    # Prevent CSRF via cross-site requests

# Additional security settings for production (HTTPS required)
# Uncomment these when deploying with HTTPS:
# if not DEBUG:
#     SECURE_SSL_REDIRECT = True              # Force all traffic to HTTPS
#     SECURE_HSTS_SECONDS = 31536000          # Tell browsers to use HTTPS for 1 year
#     SECURE_HSTS_INCLUDE_SUBDOMAINS = True   # Apply HSTS to all subdomains
#     SECURE_HSTS_PRELOAD = True              # Enable HSTS preload
#     SESSION_COOKIE_SECURE = True            # Only send session cookie over HTTPS
#     CSRF_COOKIE_SECURE = True               # Only send CSRF cookie over HTTPS
#     SECURE_CONTENT_TYPE_NOSNIFF = True      # Prevent MIME type sniffing
#     SECURE_BROWSER_XSS_FILTER = True        # Enable browser XSS filtering
#     X_FRAME_OPTIONS = 'DENY'                # Prevent clickjacking attacks