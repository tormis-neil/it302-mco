"""
Database models for the accounts app.

Models:
- UserManager: Handles user creation
- User: Custom user with security features (lockout, failed attempts tracking)
- AuthenticationEvent: Logs all login/signup attempts
- Profile: User preferences and contact info
"""

from typing import Optional

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom manager for user creation with email."""

    use_in_migrations = True

    def _create_user(self, username: str, email: str, password: Optional[str], **extra_fields):
        """
        Create and save a user with hashed password.
        
        Process:
        1. Validate username and email
        2. Normalize email (lowercase)
        3. Hash password with Argon2
        4. Save to database
        """
        if not username:
            raise ValueError("The username must be set")
        if not email:
            raise ValueError("The email must be set")

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)  # Hashes password with Argon2
        user.save(using=self._db)
        return user

    def create_user(self, username: str, email: str, password: Optional[str] = None, **extra_fields):
        """Create regular user (not staff)."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username: str, email: str, password: Optional[str] = None, **extra_fields):
        """Create admin user with all permissions."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom user with security features.
    
    Security features:
    - Tracks failed login attempts
    - Locks account after 5 failures
    - Auto-unlocks after 60 minutes
    """
    
    # Email is unique and required
    # Note: Stored as plaintext for usability (frequently accessed for login).
    # For production requiring PII encryption, consider django-encrypted-model-fields.
    email = models.EmailField(unique=True, blank=False)
    
    # Security: Track failed login attempts
    failed_login_attempts = models.PositiveIntegerField(default=0)
    
    # Security: Store when lockout expires
    locked_until = models.DateTimeField(blank=True, null=True)
    
    # Security: Track last failed attempt
    last_failed_login_at = models.DateTimeField(blank=True, null=True)

    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email']

    def mark_login_failure(self) -> None:
        """
        Record a failed login attempt.
        
        Called when: User enters wrong password
        Updates: Increments counter, sets timestamp
        """
        self.failed_login_attempts += 1
        self.last_failed_login_at = timezone.now()
        self.save(update_fields=["failed_login_attempts", "last_failed_login_at"])

    def reset_login_failures(self) -> None:
        """
        Clear failed attempts and unlock account.
        
        Called when: Successful login
        Updates: Resets counter to 0, clears lockout
        """
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_failed_login_at = None
        self.save(update_fields=["failed_login_attempts", "locked_until", "last_failed_login_at"])

    def lock_for(self, duration) -> None:
        """
        Lock account for specified duration.
        
        Called when: 5 failed login attempts reached
        How: Sets locked_until = now + duration
        Example: lock_for(timedelta(hours=1)) locks for 60 minutes
        """
        self.locked_until = timezone.now() + duration
        self.save(update_fields=["locked_until"])

    def is_locked(self) -> bool:
        """
        Check if account is currently locked.
        
        Returns True if: locked_until exists and is in the future
        Returns False if: Not locked or lockout expired
        """
        return bool(self.locked_until and self.locked_until > timezone.now())


class AuthenticationEvent(models.Model):
    """
    Audit log for all authentication attempts.
    
    Purpose:
    - Rate limiting (count attempts per IP)
    - Security monitoring
    - Track login history
    """

    class EventType(models.TextChoices):
        SIGNUP = "signup", "Sign up"
        LOGIN = "login", "Login"

    # What happened: signup or login
    event_type = models.CharField(max_length=16, choices=EventType.choices)
    
    # Where from: IP address
    ip_address = models.GenericIPAddressField()
    
    # Who tried: username/email submitted
    username_submitted = models.CharField(max_length=150, blank=True)
    email_submitted = models.EmailField(blank=True)
    
    # Link to user (if found)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="authentication_events",
    )
    
    # Did it succeed?
    successful = models.BooleanField(default=False)
    
    # Browser info
    user_agent = models.CharField(max_length=255, blank=True)
    
    # Extra data (why it failed, etc.)
    metadata = models.JSONField(default=dict, blank=True)
    
    # When it happened
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]  # Most recent first
        # Index for fast rate limiting queries
        indexes = [
            models.Index(fields=["event_type", "ip_address", "created_at"]),
        ]

    def __str__(self) -> str:
        status = "success" if self.successful else "failure"
        return f"{self.get_event_type_display()} {status} from {self.ip_address}"


class Profile(models.Model):
    """
    User profile with preferences and contact info.
    
    Relationship: Each user has exactly one profile
    Created: Automatically when user signs up (via signal below)
    """

    # Link to user (OneToOne)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="profile"
    )
    
    # User preferences
    display_name = models.CharField(max_length=120, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    favorite_drink = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    
    # Last update time
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Profile for {self.user.username}"


@receiver(post_save, sender=User)
def _ensure_profile(sender, instance: User, created: bool, **kwargs) -> None:
    """
    Signal: Auto-create profile when user is created.
    
    How it works:
    1. User.objects.create_user() saves user
    2. Django sends post_save signal
    3. This function catches the signal
    4. Creates Profile with display_name = username
    
    Why: Ensures every user always has a profile
    """
    if created:
        Profile.objects.create(user=instance, display_name=instance.username)