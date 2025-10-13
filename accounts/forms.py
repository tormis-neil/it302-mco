"""End-user authentication forms for the Brews & Chews project."""

from __future__ import annotations

import re
from typing import Optional

from django import forms
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError

from .models import Profile, User

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9._-]{3,30}$")
PASSWORD_SPECIAL_PATTERN = re.compile(r"[!@#$%^&*]")


class SignupForm(forms.Form):
    """Validate data submitted from the public sign-up page."""

    username = forms.CharField(max_length=30)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean_username(self) -> str:
        username = self.cleaned_data["username"].strip()
        if not USERNAME_PATTERN.match(username):
            raise ValidationError(
                "Choose 3-30 characters using letters, numbers, periods, underscores, or hyphens."
            )
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("That username is already taken.")
        return username

    def clean_email(self) -> str:
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("That email is already registered.")
        return email

    def clean(self) -> dict[str, str]:  # type: ignore[override]
        data = super().clean()
        password = data.get("password", "")
        confirm = data.get("confirm_password", "")
        if password:
            try:
                password_validation.validate_password(password)
            except ValidationError as exc:
                self.add_error("password", exc)
            try:
                self._validate_password_strength(password)
            except ValidationError as exc:
                self.add_error("password", exc)
        if password and confirm and password != confirm:
            self.add_error("confirm_password", "Passwords do not match.")
        return data

    def _validate_password_strength(self, password: str) -> None:
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
        if not self.is_valid():  # pragma: no cover - guard for misuse
            raise ValueError("Cannot save an invalid form")
        return User.objects.create_user(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password"],
        )


class LoginForm(forms.Form):
    """Validate the public sign-in form submission."""

    identifier = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

    def clean_identifier(self) -> str:
        return self.cleaned_data["identifier"].strip()

    def get_identifier(self) -> str:
        if not self.is_bound:
            raise ValueError("LoginForm must be bound before accessing the identifier")
        return self.cleaned_data.get("identifier", "")

    def get_password(self) -> str:
        if not self.is_bound:
            raise ValueError("LoginForm must be bound before accessing the password")
        return self.cleaned_data.get("password", "")

    def find_user(self) -> Optional[User]:
        if not self.is_valid():
            return None
        identifier = self.get_identifier()
        user: Optional[User]
        if "@" in identifier:
            user = User.objects.filter(email__iexact=identifier).first()
        else:
            user = User.objects.filter(username__iexact=identifier).first()
        return user


class ProfileForm(forms.ModelForm):
    """Edit the authenticated user's profile details."""

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
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            classes = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"dashboard-input {classes}".strip()


class ChangeUsernameForm(forms.Form):
    """Form for changing username with password confirmation."""
    
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
        self.user = user
        super().__init__(*args, **kwargs)
        # Add CSS classes
        for field in self.fields.values():
            classes = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"dashboard-input {classes}".strip()

    def clean_new_username(self) -> str:
        username = self.cleaned_data["new_username"].strip()
        
        # Check pattern
        if not USERNAME_PATTERN.match(username):
            raise ValidationError(
                "Username must be 3-30 characters using letters, numbers, periods, underscores, or hyphens."
            )
        
        # Check if username is the same
        if username.lower() == self.user.username.lower():
            raise ValidationError("This is already your current username.")
        
        # Check if username is taken
        if User.objects.filter(username__iexact=username).exclude(pk=self.user.pk).exists():
            raise ValidationError("That username is already taken.")
        
        return username

    def clean_password(self) -> str:
        password = self.cleaned_data.get("password")
        if not self.user.check_password(password):
            raise ValidationError("Incorrect password.")
        return password


class ChangePasswordForm(forms.Form):
    """
    Form for securely changing user password.
    
    Validates:
    - Current password is correct
    - New password meets strength requirements
    - Password confirmation matches
    
    Requirements:
    - 12+ characters
    - At least one uppercase letter
    - At least one number
    - At least one special character (!@#$%^&*)
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
        self.user = user
        super().__init__(*args, **kwargs)
        # Add CSS classes
        for field in self.fields.values():
            classes = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"dashboard-input {classes}".strip()

    def clean_current_password(self) -> str:
        """Verify the current password is correct."""
        password = self.cleaned_data.get("current_password")
        if not self.user.check_password(password):
            raise ValidationError("Current password is incorrect.")
        return password

    def clean_new_password(self) -> str:
        """Validate new password meets all requirements."""
        password = self.cleaned_data.get("new_password", "")
        
        if password:
            # Use Django's built-in validators
            try:
                password_validation.validate_password(password, self.user)
            except ValidationError as exc:
                raise exc
            
            # Apply custom strength requirements
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
        Validate custom password strength requirements.
        Same validation rules as signup form.
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
        Update user password securely.
        Uses Django's set_password() which handles hashing with Argon2.
        """
        new_password = self.cleaned_data["new_password"]
        
        # Use Django's built-in method for secure password hashing
        self.user.set_password(new_password)
        
        # Save to database
        self.user.save(update_fields=['password'])


__all__ = ["SignupForm", "LoginForm", "ProfileForm", "ChangeUsernameForm", "ChangePasswordForm"]