"""Database models for the accounts app."""
from __future__ import annotations

import hashlib
from typing import Optional

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .security import decrypt_email, encrypt_email


def digest_email(value: str) -> str:
    """Return a deterministic SHA-256 digest for the supplied email."""
    normalized = value.strip().lower()
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return digest


class UserManager(BaseUserManager):
    """Custom manager that understands the encrypted email workflow."""

    use_in_migrations = True

    def _create_user(self, username: str, email: Optional[str], password: Optional[str], **extra_fields):
        if not username:
            raise ValueError("The username must be set")

        email = self.normalize_email(email)
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        if email:
            user.email = email
        user.save(using=self._db)
        return user

    def create_user(self, username: str, email: Optional[str] = None, password: Optional[str] = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username: str, email: Optional[str] = None, password: Optional[str] = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        if not email:
            raise ValueError("Superuser accounts require an email address.")

        return self._create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    """Custom user storing encrypted email addresses and lockout metadata."""

    email = None  # remove the plaintext email column from the parent class

    encrypted_email = models.BinaryField(blank=True, null=True, editable=False)
    email_digest = models.CharField(max_length=64, unique=True, blank=True, null=True, editable=False)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(blank=True, null=True)
    last_failed_login_at = models.DateTimeField(blank=True, null=True)

    objects = UserManager()

    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["email"]

    @property
    def email(self) -> str:  # type: ignore[override]
        return decrypt_email(self.encrypted_email)

    @email.setter
    def email(self, value: Optional[str]) -> None:  # type: ignore[override]
        normalized = self.__class__.objects.normalize_email(value)
        if normalized:
            self.encrypted_email = encrypt_email(normalized)
            self.email_digest = digest_email(normalized)
        else:
            self.encrypted_email = b""
            self.email_digest = None

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
        return bool(self.locked_until and self.locked_until > timezone.now())


class AuthenticationEvent(models.Model):
    """Audit log for sign-up and sign-in attempts."""

    class EventType(models.TextChoices):
        SIGNUP = "signup", "Sign up"
        LOGIN = "login", "Login"

    event_type = models.CharField(max_length=16, choices=EventType.choices)
    ip_address = models.GenericIPAddressField()
    username_submitted = models.CharField(max_length=150, blank=True)
    email_digest = models.CharField(max_length=64, blank=True, null=True)
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

    def __str__(self) -> str:  # pragma: no cover - human-readable debugging only
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