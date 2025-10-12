"""End-user authentication forms for the Brews & Chews project."""

from __future__ import annotations

import re
from typing import Optional

from django import forms
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError

from .models import Profile, User, digest_email

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
            email_digest = digest_email(identifier.lower())
            user = User.objects.filter(email_digest=email_digest).first()
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


__all__ = ["SignupForm", "LoginForm", "ProfileForm"]