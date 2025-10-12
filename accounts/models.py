"""Database models for the accounts app."""

from typing import Optional

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

class UserManager(BaseUserManager):
    """Custom manager for user creation."""

    use_in_migrations = True

    def _create_user(self, username: str, email: str, password: Optional[str], **extra_fields):
        if not username:
            raise ValueError("The username must be set")
        if not email:
            raise ValueError("The email must be set")

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username: str, email: str, password: Optional[str] = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username: str, email: str, password: Optional[str] = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(username, email, password, **extra_fields)

class User(AbstractUser):
    """Custom user with security features."""
    
    # Use standard Django email field (removed encryption)
    email = models.EmailField(unique=True, blank=False)
    
    # Security fields (keep these)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(blank=True, null=True)
    last_failed_login_at = models.DateTimeField(blank=True, null=True)

    # Standard Django configuration
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email']

    def mark_login_failure(self) -> None:
        """Record a failed login attempt and update lockout metadata."""
        self.failed_login_attempts += 1
        self.last_failed_login_at = timezone.now()
        self.save(update_fields=["failed_login_attempts", "last_failed_login_at"])

    def reset_login_failures(self) -> None:
        """Clear the failed login counter and lockout window."""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_failed_login_at = None
        self.save(update_fields=["failed_login_attempts", "locked_until", "last_failed_login_at"])

    def lock_for(self, duration) -> None:
        """Lock the account for a supplied :class:`datetime.timedelta`."""
        self.locked_until = timezone.now() + duration
        self.save(update_fields=["locked_until"])

    def is_locked(self) -> bool:
        """Check if account is currently locked."""
        return bool(self.locked_until and self.locked_until > timezone.now())


class AuthenticationEvent(models.Model):
    """Audit log for sign-up and sign-in attempts."""

    class EventType(models.TextChoices):
        SIGNUP = "signup", "Sign up"
        LOGIN = "login", "Login"

    event_type = models.CharField(max_length=16, choices=EventType.choices)
    ip_address = models.GenericIPAddressField()
    username_submitted = models.CharField(max_length=150, blank=True)
    email_submitted = models.EmailField(blank=True)  # ← CHANGED: was email_digest
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="authentication_events",
    )
    successful = models.BooleanField(default=False)
    user_agent = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_type", "ip_address", "created_at"]),
        ]

    def __str__(self) -> str:
        status = "success" if self.successful else "failure"
        return f"{self.get_event_type_display()} {status} from {self.ip_address}"


class Profile(models.Model):
    """Customer profile surfaced on the authenticated dashboard."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=120, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    favorite_drink = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover - human readable
        return f"Profile for {self.user.username}"


@receiver(post_save, sender=User)
def _ensure_profile(sender, instance: User, created: bool, **_: object) -> None:
    """Create a profile automatically when a user is provisioned."""
    if created:
        Profile.objects.create(user=instance, display_name=instance.username)