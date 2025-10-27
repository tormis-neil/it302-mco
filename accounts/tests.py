"""Tests for the accounts app authentication flows."""
from __future__ import annotations

from unittest import mock

from django.contrib.auth import get_user_model
from django.db.utils import OperationalError
from django.test import Client, TestCase
from django.urls import reverse

from .models import AuthenticationEvent, Profile

User = get_user_model()


class SignupViewTests(TestCase):
    def setUp(self) -> None:
        self.client = Client(HTTP_USER_AGENT="pytest")
        self.url = reverse("accounts:signup")

    def test_signup_success_creates_user_and_logs_event(self) -> None:
        response = self.client.post(
            self.url,
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "StrongPass1!",
                "confirm_password": "StrongPass1!",
            },
            REMOTE_ADDR="198.51.100.10",
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("menu:catalog"))

        user = User.objects.get(username="newuser")
        self.assertTrue(user.check_password("StrongPass1!"))
        self.assertEqual(AuthenticationEvent.objects.filter(user=user, successful=True).count(), 1)

    def test_signup_password_hashed_with_argon2(self) -> None:
        response = self.client.post(
            self.url,
            {
                "username": "argonuser",
                "email": "argon@example.com",
                "password": "StrongPass1!",
                "confirm_password": "StrongPass1!",
            },
            REMOTE_ADDR="198.51.100.13",
        )
        self.assertEqual(response.status_code, 302)

        user = User.objects.get(username="argonuser")
        self.assertTrue(user.password.startswith("argon2"))

    def test_signup_rejects_passwords_that_fail_validators(self) -> None:
        response = self.client.post(
            self.url,
            {
                "username": "weakpass",
                "email": "weak@example.com",
                "password": "Short1!",
                "confirm_password": "Short1!",
            },
            REMOTE_ADDR="198.51.100.14",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Password must be at least 12 characters long.")
        self.assertFalse(User.objects.filter(username="weakpass").exists())

    def test_signup_rate_limit_blocks_submission(self) -> None:
        ip_address = "198.51.100.12"
        for _ in range(5):
            AuthenticationEvent.objects.create(
                event_type=AuthenticationEvent.EventType.SIGNUP,
                ip_address=ip_address,
                username_submitted="someone",
                successful=False,
            )

        response = self.client.post(
            self.url,
            {
                "username": "limited",
                "email": "limited@example.com",
                "password": "StrongPass1!",
                "confirm_password": "StrongPass1!",
            },
            REMOTE_ADDR=ip_address,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Too many sign-up attempts from this network")
        self.assertFalse(User.objects.filter(username="limited").exists())

    def test_signup_gracefully_handles_missing_audit_table(self) -> None:
        with mock.patch(
            "accounts.views.AuthenticationEvent.objects.filter",
            side_effect=OperationalError("no such table"),
        ), mock.patch(
            "accounts.views.AuthenticationEvent.objects.create",
            side_effect=OperationalError("no such table"),
        ):
            response = self.client.post(
                self.url,
                {
                    "username": "resilient",
                    "email": "resilient@example.com",
                    "password": "StrongPass1!",
                    "confirm_password": "StrongPass1!",
                },
                REMOTE_ADDR="198.51.100.99",
            )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="resilient").exists())

class LoginViewTests(TestCase):
    def setUp(self) -> None:
        self.client = Client(HTTP_USER_AGENT="pytest")
        self.url = reverse("accounts:login")
        self.user = User.objects.create_user(
            username="existing",
            email="existing@example.com",
            password="ComplexPass1!",
        )

    def test_login_success_redirects_and_resets_failures(self) -> None:
        self.user.failed_login_attempts = 2
        self.user.save(update_fields=["failed_login_attempts"])

        response = self.client.post(
            self.url,
            {"identifier": "existing", "password": "ComplexPass1!"},
            REMOTE_ADDR="203.0.113.5",
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("menu:catalog"))

        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 0)
        self.assertTrue(AuthenticationEvent.objects.filter(user=self.user, successful=True).exists())

    def test_login_with_email_identifier(self) -> None:
        response = self.client.post(
            self.url,
            {"identifier": "existing@example.com", "password": "ComplexPass1!"},
            REMOTE_ADDR="203.0.113.15",
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("menu:catalog"))

        event = AuthenticationEvent.objects.get(user=self.user, successful=True)
        self.assertEqual(event.username_submitted, "existing@example.com")

    def test_login_wrong_password_increments_failure(self) -> None:
        response = self.client.post(
            self.url,
            {"identifier": "existing", "password": "WrongPass1!"},
            REMOTE_ADDR="203.0.113.6",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password")

        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 1)
        event = AuthenticationEvent.objects.get(user=self.user, successful=False)
        self.assertEqual(event.metadata.get("reason"), "password_mismatch")

    def test_login_rate_limit_blocks_attempt(self) -> None:
        ip_address = "203.0.113.44"
        for _ in range(5):
            AuthenticationEvent.objects.create(
                event_type=AuthenticationEvent.EventType.LOGIN,
                ip_address=ip_address,
                username_submitted="existing",
                successful=False,
            )

        response = self.client.post(
            self.url,
            {"identifier": "existing", "password": "ComplexPass1!"},
            REMOTE_ADDR=ip_address,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Too many sign-in attempts")

    def test_login_locks_account_after_threshold(self) -> None:
        ip_address = "203.0.113.60"
        for attempt in range(5):
            response = self.client.post(
                self.url,
                {"identifier": "existing", "password": f"WrongPass{attempt}!"},
                REMOTE_ADDR=ip_address,
            )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your account is locked")

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_locked())
        self.assertGreaterEqual(AuthenticationEvent.objects.filter(user=self.user, successful=False).count(), 5)


class ProfileViewTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = User.objects.create_user(
            username="profileuser",
            email="profile@example.com",
            password="ComplexPass1!",
        )
        self.url = reverse("accounts:profile")

    def test_profile_requires_login(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.headers["Location"])

    def test_profile_update_persists_changes(self) -> None:
        self.client.login(username="profileuser", password="ComplexPass1!")
        response = self.client.post(
            self.url,
            {
                "display_name": "Brews Fan",
                "phone_number": "+639171234567",
                "favorite_drink": "Cold Brew",
                "bio": "Prefers light roast beans.",
                "update_profile": "true",  # Required to identify which form is being submitted
            },
        )
        self.assertEqual(response.status_code, 200)
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.display_name, "Brews Fan")
        self.assertEqual(profile.phone_number, "+639171234567")
        self.assertEqual(profile.favorite_drink, "Cold Brew")
        self.assertIn("Prefers light roast beans.", profile.bio)


class LogoutViewTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = User.objects.create_user(
            username="logoutuser",
            email="logout@example.com",
            password="ComplexPass1!",
        )
        self.url = reverse("accounts:logout")

    def test_logout_requires_post(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_logout_clears_session(self) -> None:
        self.client.login(username="logoutuser", password="ComplexPass1!")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("pages:home"))
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 302)