"""
Tests for countdown timer functionality in rate limiting and account lockout.

These tests verify that:
1. Timer values are correctly calculated and passed to templates
2. IP rate limiting triggers timer display
3. Account lockout triggers timer display
4. Timer values are accurate based on window/lockout duration
"""
from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import AuthenticationEvent

User = get_user_model()


class RateLimitingTimerTests(TestCase):
    """Test timer functionality for IP rate limiting."""

    def setUp(self) -> None:
        self.client = Client(HTTP_USER_AGENT="test-browser")
        self.login_url = reverse("accounts:login")
        self.signup_url = reverse("accounts:signup")

    def test_login_rate_limit_returns_lockout_seconds(self) -> None:
        """
        When IP is rate limited on login, response should include lockout_seconds.
        """
        ip_address = "192.168.1.100"

        # Create 5 failed login attempts to trigger rate limit
        for i in range(5):
            AuthenticationEvent.objects.create(
                event_type=AuthenticationEvent.EventType.LOGIN,
                ip_address=ip_address,
                username_submitted=f"user{i}",
                successful=False,
            )

        # 6th attempt should be rate limited
        response = self.client.post(
            self.login_url,
            {"identifier": "test", "password": "WrongPass123!"},
            REMOTE_ADDR=ip_address,
        )

        # Check response contains lockout_seconds
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Too many sign-in attempts")
        self.assertIn("lockout_seconds", response.context)
        self.assertIsNotNone(response.context["lockout_seconds"])

        # Verify lockout_seconds is a positive number
        lockout_seconds = response.context["lockout_seconds"]
        self.assertGreater(lockout_seconds, 0)
        # Should be close to 15 minutes (900 seconds) but not exact due to time passing
        self.assertLessEqual(lockout_seconds, 900)

        print(f"\n✅ IP rate limit lockout_seconds: {lockout_seconds} seconds ({lockout_seconds//60} minutes)")

    def test_signup_rate_limit_returns_lockout_seconds(self) -> None:
        """
        When IP is rate limited on signup, response should include lockout_seconds.
        """
        ip_address = "10.0.0.50"

        # Create 5 signup attempts to trigger rate limit
        for i in range(5):
            AuthenticationEvent.objects.create(
                event_type=AuthenticationEvent.EventType.SIGNUP,
                ip_address=ip_address,
                username_submitted=f"user{i}",
                successful=True,  # Even successful signups count
            )

        # 6th attempt should be rate limited
        response = self.client.post(
            self.signup_url,
            {
                "username": "newuser",
                "email": "new@example.com",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
            },
            REMOTE_ADDR=ip_address,
        )

        # Check response contains lockout_seconds
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Too many sign-up attempts")
        self.assertIn("lockout_seconds", response.context)
        self.assertIsNotNone(response.context["lockout_seconds"])

        # Verify lockout_seconds is positive and close to 1 hour (3600 seconds)
        lockout_seconds = response.context["lockout_seconds"]
        self.assertGreater(lockout_seconds, 0)
        self.assertLessEqual(lockout_seconds, 3600)

        print(f"\n✅ Signup rate limit lockout_seconds: {lockout_seconds} seconds ({lockout_seconds//60} minutes)")

    def test_login_template_contains_timer_when_rate_limited(self) -> None:
        """
        Login template should include timer HTML when rate limited.
        """
        ip_address = "203.0.113.100"

        # Trigger rate limit
        for i in range(5):
            AuthenticationEvent.objects.create(
                event_type=AuthenticationEvent.EventType.LOGIN,
                ip_address=ip_address,
                username_submitted=f"user{i}",
                successful=False,
            )

        response = self.client.post(
            self.login_url,
            {"identifier": "test", "password": "WrongPass!"},
            REMOTE_ADDR=ip_address,
        )

        # Check HTML contains timer elements
        self.assertContains(response, 'data-lockout-timer=')
        self.assertContains(response, 'id="timer-display"')
        self.assertContains(response, 'Time remaining:')

        print("\n✅ Login template includes timer HTML when rate limited")

    def test_signup_template_contains_timer_when_rate_limited(self) -> None:
        """
        Signup template should include timer HTML when rate limited.
        """
        ip_address = "172.16.0.100"

        # Trigger rate limit
        for i in range(5):
            AuthenticationEvent.objects.create(
                event_type=AuthenticationEvent.EventType.SIGNUP,
                ip_address=ip_address,
                username_submitted=f"user{i}",
                successful=True,
            )

        response = self.client.post(
            self.signup_url,
            {
                "username": "test",
                "email": "test@example.com",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
            },
            REMOTE_ADDR=ip_address,
        )

        # Check HTML contains timer elements
        self.assertContains(response, 'data-lockout-timer=')
        self.assertContains(response, 'id="timer-display"')
        self.assertContains(response, 'Time remaining:')

        print("\n✅ Signup template includes timer HTML when rate limited")


class AccountLockoutTimerTests(TestCase):
    """Test timer functionality for account lockout."""

    def setUp(self) -> None:
        self.client = Client(HTTP_USER_AGENT="test-browser")
        self.login_url = reverse("accounts:login")

        # Create test user
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="CorrectPass123!"
        )

    def test_account_lockout_returns_lockout_seconds(self) -> None:
        """
        When account is locked, response should include lockout_seconds.
        """
        # Lock the account
        self.user.lock_for(timedelta(hours=1))
        self.user.save()

        response = self.client.post(
            self.login_url,
            {"identifier": "testuser", "password": "CorrectPass123!"},
            REMOTE_ADDR="10.0.0.1",
        )

        # Check response contains lockout_seconds
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your account is locked")
        self.assertIn("lockout_seconds", response.context)
        self.assertIsNotNone(response.context["lockout_seconds"])

        # Verify lockout_seconds is close to 1 hour
        lockout_seconds = response.context["lockout_seconds"]
        self.assertGreater(lockout_seconds, 0)
        self.assertLessEqual(lockout_seconds, 3600)

        print(f"\n✅ Account lockout lockout_seconds: {lockout_seconds} seconds ({lockout_seconds//60} minutes)")

    def test_account_lockout_template_contains_timer(self) -> None:
        """
        Login template should include timer HTML when account is locked.
        """
        # Lock the account
        self.user.lock_for(timedelta(hours=1))
        self.user.save()

        response = self.client.post(
            self.login_url,
            {"identifier": "testuser", "password": "CorrectPass123!"},
            REMOTE_ADDR="10.0.0.1",
        )

        # Check HTML contains timer elements
        self.assertContains(response, 'data-lockout-timer=')
        self.assertContains(response, 'id="timer-display"')
        self.assertContains(response, 'Time remaining:')

        print("\n✅ Account lockout template includes timer HTML")

    def test_timer_accuracy_for_partial_lockout(self) -> None:
        """
        Timer should reflect remaining time accurately for partial lockout periods.
        """
        # Lock account for 30 minutes from now
        lockout_duration = timedelta(minutes=30)
        self.user.lock_for(lockout_duration)
        self.user.save()

        response = self.client.post(
            self.login_url,
            {"identifier": "testuser", "password": "CorrectPass123!"},
            REMOTE_ADDR="10.0.0.1",
        )

        lockout_seconds = response.context["lockout_seconds"]

        # Should be close to 30 minutes (1800 seconds)
        expected_seconds = 30 * 60
        # Allow 5 seconds variance for test execution time
        self.assertGreater(lockout_seconds, expected_seconds - 5)
        self.assertLessEqual(lockout_seconds, expected_seconds)

        print(f"\n✅ Timer accuracy: {lockout_seconds}s for 30-minute lockout (expected ~{expected_seconds}s)")

    def test_no_timer_when_not_rate_limited(self) -> None:
        """
        Timer should not appear when user is not rate limited or locked.
        """
        response = self.client.post(
            self.login_url,
            {"identifier": "testuser", "password": "WrongPass!"},
            REMOTE_ADDR="10.0.0.1",
        )

        # Check lockout_seconds is None
        self.assertIsNone(response.context.get("lockout_seconds"))

        # Check HTML does NOT contain timer elements
        self.assertNotContains(response, 'data-lockout-timer=')

        print("\n✅ No timer displayed when not rate limited")


class TimerCalculationTests(TestCase):
    """Test timer calculation logic."""

    def setUp(self) -> None:
        self.client = Client(HTTP_USER_AGENT="test-browser")
        self.login_url = reverse("accounts:login")

    def test_timer_uses_oldest_event_in_window(self) -> None:
        """
        Timer should be based on when the oldest event in the window expires.
        """
        ip_address = "192.168.5.100"

        # Create 5 events to trigger rate limit
        # All created at current time
        for i in range(5):
            AuthenticationEvent.objects.create(
                event_type=AuthenticationEvent.EventType.LOGIN,
                ip_address=ip_address,
                username_submitted=f"user{i}",
                successful=False,
            )

        response = self.client.post(
            self.login_url,
            {"identifier": "test", "password": "WrongPass!"},
            REMOTE_ADDR=ip_address,
        )

        lockout_seconds = response.context["lockout_seconds"]

        # All events were just created, so timer should be close to full window (15 minutes = 900 seconds)
        expected_seconds = 15 * 60
        # Allow 10 seconds variance for test execution time
        self.assertGreater(lockout_seconds, expected_seconds - 10)
        self.assertLessEqual(lockout_seconds, expected_seconds)

        print(f"\n✅ Timer correctly calculated: {lockout_seconds}s (expected ~{expected_seconds}s)")
        print(f"   All events just created, rate limit window = 15 minutes")

    def test_timer_minimum_value_is_one_second(self) -> None:
        """
        Timer should never be less than 1 second (prevents showing 0 or negative).
        """
        ip_address = "192.168.10.100"

        # Create event almost 15 minutes ago (just about to expire)
        old_time = timezone.now() - timedelta(minutes=14, seconds=59)
        AuthenticationEvent.objects.create(
            event_type=AuthenticationEvent.EventType.LOGIN,
            ip_address=ip_address,
            username_submitted="user1",
            successful=False,
            created_at=old_time,
        )

        # Create 4 more events to trigger rate limit
        for i in range(4):
            AuthenticationEvent.objects.create(
                event_type=AuthenticationEvent.EventType.LOGIN,
                ip_address=ip_address,
                username_submitted=f"user{i}",
                successful=False,
            )

        response = self.client.post(
            self.login_url,
            {"identifier": "test", "password": "WrongPass!"},
            REMOTE_ADDR=ip_address,
        )

        lockout_seconds = response.context["lockout_seconds"]

        # Should be at least 1 second
        self.assertGreaterEqual(lockout_seconds, 1)

        print(f"\n✅ Minimum timer value enforced: {lockout_seconds}s (>= 1)")


def run_timer_tests():
    """
    Run all timer tests and print summary.

    Usage:
        python manage.py test accounts.test_timer_functionality -v 2
    """
    print("\n" + "="*70)
    print(" "*20 + "TIMER FUNCTIONALITY TESTS")
    print("="*70)
    print("\nThese tests verify:")
    print("1. ✓ IP rate limiting includes timer in response")
    print("2. ✓ Account lockout includes timer in response")
    print("3. ✓ Timer values are accurate")
    print("4. ✓ Templates display timer HTML")
    print("5. ✓ Timer calculations account for elapsed time")
    print("6. ✓ Minimum timer value is enforced")
    print("="*70)
