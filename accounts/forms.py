"""
End-user authentication forms for the Brews & Chews project.

Forms:
- SignupForm: User registration with password validation
- LoginForm: User authentication (username or email)
- ProfileForm: Update profile info
- ChangeUsernameForm: Change username with password confirmation
- ChangePasswordForm: Change password with validation
"""

from __future__ import annotations

import re
from typing import Optional

from django import forms
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError

from .models import Profile, User
from .encryption import generate_email_digest

# Validation patterns
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9._-]{3,30}$")
PASSWORD_SPECIAL_PATTERN = re.compile(r"[!@#$%^&*]")


class SignupForm(forms.Form):
    """
    Validate user registration form.
    
    Validates:
    - Username: 3-30 chars, alphanumeric with ._-
    - Email: Valid format, not already used
    - Password: 12+ chars, uppercase, number, special char
    - Confirm password: Must match password
    """

    username = forms.CharField(max_length=30)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean_username(self) -> str:
        """
        Validate username format and uniqueness.
        
        Checks:
        - Matches pattern (3-30 chars, letters, numbers, ._-)
        - Not already taken (case-insensitive)
        """
        username = self.cleaned_data["username"].strip()
        
        if not USERNAME_PATTERN.match(username):
            raise ValidationError(
                "Choose 3-30 characters using letters, numbers, periods, underscores, or hyphens."
            )
        
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("That username is already taken.")
        
        return username

    def clean_email(self) -> str:
        """
        Validate email format and uniqueness.

        Process:
        - Strip whitespace, convert to lowercase
        - Generate SHA-256 digest
        - Check if already registered (using digest for encrypted emails)

        Note: Uses email_digest field for uniqueness check since emails
        are encrypted and can't be directly compared.
        """
        email = self.cleaned_data["email"].strip().lower()

        # Generate digest to check uniqueness
        # This works with encrypted emails since digest is deterministic
        email_digest = generate_email_digest(email)

        # Check if digest already exists (means email is registered)
        if User.objects.filter(email_digest=email_digest).exists():
            raise ValidationError("That email is already registered.")

        return email

    def clean(self) -> dict[str, str]:
        """
        Validate password strength and confirmation.
        
        Runs after individual field validation.
        Checks:
        - Django's built-in password validators
        - Our custom strength requirements
        - Password and confirmation match
        """
        data = super().clean()
        password = data.get("password", "")
        confirm = data.get("confirm_password", "")
        
        if password:
            # Django validators (common passwords, similarity)
            try:
                password_validation.validate_password(password)
            except ValidationError as exc:
                self.add_error("password", exc)
            
            # Our custom requirements
            try:
                self._validate_password_strength(password)
            except ValidationError as exc:
                self.add_error("password", exc)
        
        # Check passwords match
        if password and confirm and password != confirm:
            self.add_error("confirm_password", "Passwords do not match.")
        
        return data

    def _validate_password_strength(self, password: str) -> None:
        """
        Check custom password requirements.
        
        Requirements:
        - 12+ characters
        - At least one uppercase letter
        - At least one number
        - At least one special character (!@#$%^&*)
        """
        errors = []
        
        if len(password) < 12:
            errors.append("Password must be at least 12 characters long.")
        
        if password.lower() == password:
            errors.append("Include at least one uppercase letter.")
        
        if not any(ch.isdigit() for ch in password):
            errors.append("Include at least one number.")
        
        if not PASSWORD_SPECIAL_PATTERN.search(password):
            errors.append("Include at least one special character (!@#$%^&*).")
        
        if errors:
            raise ValidationError(errors)

    def save(self) -> User:
        """
        Create new user with validated data.
        
        Process:
        - Calls User.objects.create_user()
        - Password automatically hashed with Argon2
        - Profile auto-created via signal
        """
        if not self.is_valid():
            raise ValueError("Cannot save an invalid form")
        
        return User.objects.create_user(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password"],
        )


class LoginForm(forms.Form):
    """
    Validate login form.
    
    Accepts: Username OR email
    Password: Any string (checked by User.check_password)
    """

    identifier = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

    def clean_identifier(self) -> str:
        """Strip whitespace from username/email."""
        return self.cleaned_data["identifier"].strip()

    def get_identifier(self) -> str:
        """Get submitted username or email."""
        if not self.is_bound:
            raise ValueError("LoginForm must be bound before accessing the identifier")
        return self.cleaned_data.get("identifier", "")

    def get_password(self) -> str:
        """Get submitted password."""
        if not self.is_bound:
            raise ValueError("LoginForm must be bound before accessing the password")
        return self.cleaned_data.get("password", "")

    def find_user(self) -> Optional[User]:
        """
        Find user by username or email.

        Logic:
        - If identifier contains @: Search by email (using digest)
        - Otherwise: Search by username
        - Case-insensitive search

        Note: Email search uses email_digest field since emails are encrypted.
        The digest is deterministic (same email -> same digest) so lookups work.
        """
        if not self.is_valid():
            return None

        identifier = self.get_identifier()
        user: Optional[User]

        if "@" in identifier:
            # Search by email using digest (for encrypted emails)
            email_digest = generate_email_digest(identifier)
            user = User.objects.filter(email_digest=email_digest).first()
        else:
            # Search by username
            user = User.objects.filter(username__iexact=identifier).first()

        return user


class ProfileForm(forms.ModelForm):
    """
    Edit user profile information.
    
    Fields: display_name, phone_number, favorite_drink, bio
    All fields optional
    """

    phone_number = forms.CharField(
        max_length=20,
        required=False,
        help_text="Optional: include country code",
    )

    class Meta:
        model = Profile
        fields = ["display_name", "phone_number", "favorite_drink", "bio"]
        widgets = {
            "display_name": forms.TextInput(attrs={"placeholder": "How should we address you?"}),
            "favorite_drink": forms.TextInput(attrs={"placeholder": "Your go-to order"}),
            "bio": forms.Textarea(attrs={"rows": 3, "placeholder": "Share a short note for our baristas."}),
        }

    def __init__(self, *args, **kwargs):
        """Add CSS classes to form fields."""
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            classes = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"dashboard-input {classes}".strip()


class ChangeUsernameForm(forms.Form):
    """
    Change username with password confirmation.
    
    Validates:
    - New username meets requirements
    - New username not already taken
    - Password is correct
    """
    
    new_username = forms.CharField(
        max_length=150,
        label="New Username",
        help_text="Choose a new username (3-30 characters, letters, numbers, ._- only)"
    )
    password = forms.CharField(
        widget=forms.PasswordInput,
        label="Confirm Password",
        help_text="Enter your current password to confirm"
    )

    def __init__(self, user, *args, **kwargs):
        """Store user for validation."""
        self.user = user
        super().__init__(*args, **kwargs)
        # Add CSS classes
        for field in self.fields.values():
            classes = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"dashboard-input {classes}".strip()

    def clean_new_username(self) -> str:
        """
        Validate new username.
        
        Checks:
        - Matches pattern
        - Different from current username
        - Not taken by another user
        """
        username = self.cleaned_data["new_username"].strip()
        
        if not USERNAME_PATTERN.match(username):
            raise ValidationError(
                "Username must be 3-30 characters using letters, numbers, periods, underscores, or hyphens."
            )
        
        if username.lower() == self.user.username.lower():
            raise ValidationError("This is already your current username.")
        
        if User.objects.filter(username__iexact=username).exclude(pk=self.user.pk).exists():
            raise ValidationError("That username is already taken.")
        
        return username

    def clean_password(self) -> str:
        """Verify current password is correct."""
        password = self.cleaned_data.get("password")
        
        if not self.user.check_password(password):
            raise ValidationError("Incorrect password.")
        
        return password


class ChangePasswordForm(forms.Form):
    """
    Change password with validation.
    
    Validates:
    - Current password is correct
    - New password meets strength requirements
    - Confirmation matches new password
    """
    
    current_password = forms.CharField(
        widget=forms.PasswordInput,
        label="Current Password",
        help_text="Enter your current password"
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput,
        label="New Password",
        help_text="Must be at least 12 characters with uppercase, number, and special character"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        label="Confirm New Password",
        help_text="Re-enter your new password"
    )

    def __init__(self, user, *args, **kwargs):
        """Store user for validation."""
        self.user = user
        super().__init__(*args, **kwargs)
        # Add CSS classes
        for field in self.fields.values():
            classes = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"dashboard-input {classes}".strip()

    def clean_current_password(self) -> str:
        """Verify current password is correct."""
        password = self.cleaned_data.get("current_password")
        
        if not self.user.check_password(password):
            raise ValidationError("Current password is incorrect.")
        
        return password

    def clean_new_password(self) -> str:
        """
        Validate new password meets requirements.
        
        Checks:
        - Django's built-in validators
        - Our custom strength requirements
        """
        password = self.cleaned_data.get("new_password", "")
        
        if password:
            # Django validators
            try:
                password_validation.validate_password(password, self.user)
            except ValidationError as exc:
                raise exc
            
            # Custom strength requirements
            try:
                self._validate_password_strength(password)
            except ValidationError as exc:
                raise exc
        
        return password

    def clean(self) -> dict:
        """Validate password confirmation matches."""
        data = super().clean()
        new_password = data.get("new_password", "")
        confirm = data.get("confirm_password", "")
        
        if new_password and confirm and new_password != confirm:
            self.add_error("confirm_password", "Passwords do not match.")
        
        return data

    def _validate_password_strength(self, password: str) -> None:
        """
        Check custom password requirements.
        
        Same validation as signup form.
        """
        errors = []
        
        if len(password) < 12:
            errors.append("Password must be at least 12 characters long.")
        
        if password.lower() == password:
            errors.append("Include at least one uppercase letter.")
        
        if not any(ch.isdigit() for ch in password):
            errors.append("Include at least one number.")
        
        if not PASSWORD_SPECIAL_PATTERN.search(password):
            errors.append("Include at least one special character (!@#$%^&*).")
        
        if errors:
            raise ValidationError(errors)

    def save(self) -> None:
        """
        Update user password.
        
        Process:
        - Uses set_password() to hash with Argon2
        - Saves only password field to database
        """
        new_password = self.cleaned_data["new_password"]
        
        # Hash password with Argon2
        self.user.set_password(new_password)
        
        # Save to database
        self.user.save(update_fields=['password'])


__all__ = ["SignupForm", "LoginForm", "ProfileForm", "ChangeUsernameForm", "ChangePasswordForm"]