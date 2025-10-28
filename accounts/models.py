"""
Database models for the accounts app.

Models:
- UserManager: Handles user creation
- User: Custom user with security features (lockout, failed attempts tracking)
- AuthenticationEvent: Logs all login/signup attempts
- Profile: User preferences and contact info

Security Features (MCO 1):
- AES-256-GCM email encryption for PII protection
- SHA-256 email digest for lookups and uniqueness
- Transparent encryption/decryption on save/access
"""

import logging
from typing import Optional

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .encryption import (
    encrypt_email,
    decrypt_email,
    generate_email_digest,
    DecryptionFailedError,
    EmailEncryptionError,
)

logger = logging.getLogger(__name__)


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
    - AES-256-GCM email encryption (MCO 1)
    - SHA-256 email digest for lookups

    Email Encryption (MCO 1 Academic Project):
    - email: Plaintext field (kept for backwards compatibility, will be deprecated)
    - encrypted_email: AES-256-GCM encrypted email (BinaryField)
    - email_digest: SHA-256 hash for lookups and uniqueness (CharField)

    How it works:
    1. On save(): email is encrypted -> encrypted_email, digest generated -> email_digest
    2. On access: user.email_decrypted returns decrypted email (cached in memory)
    3. For lookups: Use email_digest (e.g., User.objects.get(email_digest=digest))
    """

    # Email fields (plaintext for backwards compatibility during migration)
    # TODO: Remove this field after full migration to encrypted_email
    email = models.EmailField(unique=False, blank=True)  # unique=False to avoid conflicts with digest

    # Encrypted email storage (AES-256-GCM)
    # Format: [12 bytes nonce][variable length ciphertext + auth_tag]
    encrypted_email = models.BinaryField(blank=True, null=True)

    # Email digest for lookups and uniqueness (SHA-256)
    # This allows us to check uniqueness and search by email without decrypting
    email_digest = models.CharField(
        max_length=64,
        unique=True,
        blank=True,
        null=True,
        db_index=True,  # Index for fast lookups
        help_text="SHA-256 digest of email for lookups"
    )

    # Security: Track failed login attempts
    failed_login_attempts = models.PositiveIntegerField(default=0)

    # Security: Store when lockout expires
    locked_until = models.DateTimeField(blank=True, null=True)

    # Security: Track last failed attempt
    last_failed_login_at = models.DateTimeField(blank=True, null=True)

    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email']

    # Cache for decrypted email (avoid repeated decryption)
    _email_cache: Optional[str] = None

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

    # ===== Email Encryption Methods (MCO 1) =====

    def _encrypt_and_store_email(self, plaintext_email: str) -> None:
        """
        Encrypt email and generate digest for storage.

        This method:
        1. Encrypts the email using AES-256-GCM
        2. Generates SHA-256 digest for lookups
        3. Stores both in database fields

        Called automatically by save() method.

        Args:
            plaintext_email: Email address to encrypt

        Raises:
            EmailEncryptionError: If encryption fails
        """
        try:
            # Encrypt email using AES-256-GCM
            self.encrypted_email = encrypt_email(plaintext_email)

            # Generate digest for lookups and uniqueness
            self.email_digest = generate_email_digest(plaintext_email)

            # Keep plaintext in cache for immediate access
            self._email_cache = plaintext_email.lower().strip()

            logger.debug(f"Encrypted email for user {self.username}")

        except EmailEncryptionError as e:
            logger.error(f"Failed to encrypt email for user {self.username}: {e}")
            raise

    @property
    def email_decrypted(self) -> str:
        """
        Get decrypted email address (cached for performance).

        This property provides transparent access to the encrypted email:
        - First access: Decrypts from encrypted_email and caches result
        - Subsequent accesses: Returns cached value (no decryption needed)
        - Falls back to plaintext email field if encrypted_email not set

        Returns:
            str: Decrypted email address

        Example:
            >>> user = User.objects.get(username="alice")
            >>> email = user.email_decrypted  # Decrypts once
            >>> email2 = user.email_decrypted  # Uses cache

        Note:
            Cache is cleared when object is reloaded from database.
        """
        # Return cached value if available
        if self._email_cache:
            return self._email_cache

        # Try to decrypt from encrypted_email
        if self.encrypted_email:
            try:
                self._email_cache = decrypt_email(self.encrypted_email)
                return self._email_cache
            except DecryptionFailedError as e:
                logger.error(f"Failed to decrypt email for user {self.username}: {e}")
                # Fall through to plaintext fallback

        # Fallback to plaintext email (backwards compatibility)
        if self.email:
            logger.warning(
                f"Using plaintext email for user {self.username} "
                "(encrypted_email not available)"
            )
            return self.email

        # No email available
        return ""

    @staticmethod
    def find_by_email(email: str):
        """
        Find user by email address using digest lookup.

        This method searches for a user by email without needing to decrypt
        all emails in the database. It generates the digest of the search
        email and looks it up directly.

        Args:
            email: Email address to search for

        Returns:
            User: User object if found

        Raises:
            User.DoesNotExist: If no user with that email exists

        Example:
            >>> user = User.find_by_email("alice@example.com")
            >>> user.username
            'alice'
        """
        digest = generate_email_digest(email)
        return User.objects.get(email_digest=digest)

    def save(self, *args, **kwargs):
        """
        Override save to automatically encrypt email before storing.

        This ensures email is always encrypted when saving to database:
        1. Check if email field has a value
        2. If yes, encrypt it and generate digest
        3. Save to database

        The encryption happens transparently - callers don't need to
        manually call encryption methods.

        Example:
            >>> user = User(username="bob", email="bob@example.com")
            >>> user.save()  # Email automatically encrypted
            >>> user.encrypted_email  # Contains encrypted bytes
            b'\\x...'
        """
        # If email is set, encrypt it before saving
        if self.email:
            self._encrypt_and_store_email(self.email)

        # Call parent save method
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """String representation showing username."""
        return self.username


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