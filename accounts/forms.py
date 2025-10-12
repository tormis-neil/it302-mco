"""Custom authentication forms will live here once backend work begins."""
"""End-user forms for authentication workflows."""

from __future__ import annotations

import re
from typing import Optional

from django import forms
from django.core.exceptions import ValidationError

from .models import User, digest_email

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
        if User.objects.filter(email_digest=digest_email(email)).exists():
            raise ValidationError("That email is already registered.")
        return email

    def clean(self) -> dict[str, str]:  # type: ignore[override]
        data = super().clean()
        password = data.get("password", "")
        confirm = data.get("confirm_password", "")
        if password:
            self._validate_password_strength(password)
        if password and confirm and password != confirm:
            self.add_error("confirm_password", "Passwords do not match.")
        return data

    def _validate_password_strength(self, password: str) -> None:
        if len(password) < 8:
            raise ValidationError({"password": "Password must be at least 8 characters long."})
        if password.lower() == password:
            raise ValidationError({"password": "Include at least one uppercase letter."})
        if not any(ch.isdigit() for ch in password):
            raise ValidationError({"password": "Include at least one number."})
        if not PASSWORD_SPECIAL_PATTERN.search(password):
            raise ValidationError({"password": "Include at least one special character (!@#$%^&*)."})

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
            email_digest = digest_email(identifier.lower())
            user = User.objects.filter(email_digest=email_digest).first()
        else:
            user = User.objects.filter(username__iexact=identifier).first()
        return user


__all__ = ["SignupForm", "LoginForm"]