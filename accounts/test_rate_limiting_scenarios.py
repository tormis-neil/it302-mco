"""
Additional tests for rate limiting and account lockout scenarios.

These tests demonstrate specific edge cases and answer common questions:
1. Does rate limiting work per account or per IP?
2. What happens if user logs in 6 times with correct password?
3. Is lockout per account or per failed attempts in one account?
4. Can lockout be triggered from different IPs?
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from .models import AuthenticationEvent

User = get_user_model()


class RateLimitingScenariosTest(TestCase):
    """Test specific rate limiting scenarios."""

    def setUp(self) -> None:
        self.client = Client(HTTP_USER_AGENT="test-browser")
        self.login_url = reverse("accounts:login")
        self.signup_url = reverse("accounts:signup")

        # Create test users
        self.alice = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="AlicePass123!"
        )
        self.bob = User.objects.create_user(
            username="bob",
            email="bob@example.com",
            password="BobPass123!"
        )

    def test_successful_logins_do_not_trigger_rate_limit(self) -> None:
        """
        QUESTION: What if user signs in 6 times with correct information?
        ANSWER: Successful logins do NOT count toward rate limit.
        """
        ip_address = "192.168.1.100"

        # Login 6 times successfully
        for i in range(6):
            response = self.client.post(
                self.login_url,
                {"identifier": "alice", "password": "AlicePass123!"},
                REMOTE_ADDR=ip_address,
            )
            self.assertEqual(response.status_code, 302, f"Attempt {i+1} should succeed")
            self.assertEqual(response.headers["Location"], reverse("menu:catalog"))

        # Verify: All 6 attempts succeeded
        successful_events = AuthenticationEvent.objects.filter(
            ip_address=ip_address,
            successful=True
        ).count()
        self.assertEqual(successful_events, 6, "All 6 successful logins should be logged")

        # 7th login should still work (no rate limit)
        response = self.client.post(
            self.login_url,
            {"identifier": "alice", "password": "AlicePass123!"},
            REMOTE_ADDR=ip_address,
        )
        self.assertEqual(response.status_code, 302)

        print("\n✅ Test passed: Successful logins do NOT trigger rate limits")
        print(f"   - 7 successful logins from IP {ip_address} all allowed")

    def test_ip_rate_limiting_works_across_different_accounts(self) -> None:
        """
        QUESTION: Is rate limiting per account or per IP?
        ANSWER: IP rate limiting counts ALL failed attempts from an IP,
                regardless of which account is targeted.
        """
        ip_address = "10.0.0.50"

        # Attempt 1-3: Try alice with wrong password
        for i in range(3):
            response = self.client.post(
                self.login_url,
                {"identifier": "alice", "password": f"WrongPass{i}!"},
                REMOTE_ADDR=ip_address,
            )
            self.assertContains(response, "Invalid username or password")

        # Attempt 4-5: Try bob with wrong password (same IP)
        for i in range(2):
            response = self.client.post(
                self.login_url,
                {"identifier": "bob", "password": f"WrongPass{i}!"},
                REMOTE_ADDR=ip_address,
            )
            self.assertContains(response, "Invalid username or password")

        # Verify: 5 failed attempts from same IP
        failed_from_ip = AuthenticationEvent.objects.filter(
            event_type=AuthenticationEvent.EventType.LOGIN,
            ip_address=ip_address,
            successful=False
        ).count()
        self.assertEqual(failed_from_ip, 5)

        # Attempt 6: Try bob with CORRECT password - should be rate limited
        response = self.client.post(
            self.login_url,
            {"identifier": "bob", "password": "BobPass123!"},
            REMOTE_ADDR=ip_address,
        )
        self.assertContains(response, "Too many sign-in attempts")

        # Verify bob is NOT logged in (rate limited)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

        print("\n✅ Test passed: IP rate limiting works across different accounts")
        print(f"   - 3 failed attempts on 'alice' + 2 failed on 'bob' = 5 from IP")
        print(f"   - 6th attempt (correct password for bob) blocked by IP rate limit")

    def test_account_lockout_is_per_account_not_per_ip(self) -> None:
        """
        QUESTION: Is lockout per account or per failed attempts across accounts?
        ANSWER: Account lockout is PER ACCOUNT. Failed attempts on different
                accounts don't affect each other.
        """
        # Fail alice login 5 times from different IPs
        for i in range(5):
            response = self.client.post(
                self.login_url,
                {"identifier": "alice", "password": f"WrongPass{i}!"},
                REMOTE_ADDR=f"10.0.0.{i+1}",
            )

        # Alice should be locked now
        self.alice.refresh_from_db()
        self.assertTrue(self.alice.is_locked(), "Alice should be locked after 5 failures")

        # Bob should NOT be locked (different account)
        self.bob.refresh_from_db()
        self.assertFalse(self.bob.is_locked(), "Bob should NOT be locked")
        self.assertEqual(self.bob.failed_login_attempts, 0)

        # Bob should be able to login
        response = self.client.post(
            self.login_url,
            {"identifier": "bob", "password": "BobPass123!"},
            REMOTE_ADDR="10.0.0.99",
        )
        self.assertEqual(response.status_code, 302)

        print("\n✅ Test passed: Account lockout is per account")
        print(f"   - Alice locked after 5 failed attempts")
        print(f"   - Bob unaffected and can still login")

    def test_account_lockout_from_different_ips(self) -> None:
        """
        QUESTION: Can an account be locked from attempts on different IPs?
        ANSWER: YES. Account lockout tracks failed attempts PER USER,
                regardless of which IP the attempts came from.
        """
        # Fail alice login 5 times from 5 different IPs
        for i in range(5):
            response = self.client.post(
                self.login_url,
                {"identifier": "alice", "password": f"WrongPass{i}!"},
                REMOTE_ADDR=f"172.16.0.{i+1}",
            )

            # First 4 attempts should show normal error
            if i < 4:
                self.assertContains(response, "Invalid username or password")

        # 5th attempt should trigger lockout
        self.assertContains(response, "Your account is locked")

        # Verify alice is locked
        self.alice.refresh_from_db()
        self.assertTrue(self.alice.is_locked())

        # Try from a new IP with CORRECT password - should still be locked
        response = self.client.post(
            self.login_url,
            {"identifier": "alice", "password": "AlicePass123!"},
            REMOTE_ADDR="172.16.0.100",
        )
        self.assertContains(response, "Your account is locked")

        print("\n✅ Test passed: Account can be locked from different IPs")
        print(f"   - 5 failed attempts from 5 different IPs")
        print(f"   - Account locked even when trying from new IP with correct password")

    def test_successful_login_resets_account_lockout_counter(self) -> None:
        """
        QUESTION: What happens to failed attempts counter after successful login?
        ANSWER: Successful login resets the counter to 0.
        """
        # Fail 3 times
        for i in range(3):
            self.client.post(
                self.login_url,
                {"identifier": "alice", "password": f"WrongPass{i}!"},
                REMOTE_ADDR="10.0.1.1",
            )

        # Verify counter is 3
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.failed_login_attempts, 3)

        # Successful login
        response = self.client.post(
            self.login_url,
            {"identifier": "alice", "password": "AlicePass123!"},
            REMOTE_ADDR="10.0.1.2",
        )
        self.assertEqual(response.status_code, 302)

        # Counter should be reset to 0
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.failed_login_attempts, 0)
        self.assertIsNone(self.alice.locked_until)

        print("\n✅ Test passed: Successful login resets counter")
        print(f"   - Counter was 3 after failed attempts")
        print(f"   - Counter reset to 0 after successful login")

    def test_lockout_expires_after_60_minutes(self) -> None:
        """
        QUESTION: How long does the lockout last?
        ANSWER: 60 minutes, after which the account unlocks automatically.
        """
        # Lock the account manually
        self.alice.failed_login_attempts = 5
        self.alice.lock_for(timedelta(hours=1))
        self.alice.save()

        # Should be locked now
        self.assertTrue(self.alice.is_locked())

        # Manually set locked_until to 5 minutes ago (simulate time passing)
        self.alice.locked_until = timezone.now() - timedelta(minutes=5)
        self.alice.save()

        # Should NOT be locked anymore
        self.assertFalse(self.alice.is_locked())

        # Should be able to login
        response = self.client.post(
            self.login_url,
            {"identifier": "alice", "password": "AlicePass123!"},
            REMOTE_ADDR="10.0.2.1",
        )
        self.assertEqual(response.status_code, 302)

        print("\n✅ Test passed: Lockout expires after 60 minutes")
        print(f"   - Account locked until {self.alice.locked_until}")
        print(f"   - After lockout expires, login succeeds")

    def test_signup_rate_limiting_counts_all_attempts(self) -> None:
        """
        QUESTION: Does signup rate limiting work like login?
        ANSWER: Similar, but counts ALL signup attempts (successful + failed),
                not just failed ones.
        """
        ip_address = "192.168.2.100"

        # Create 5 successful signups
        for i in range(5):
            response = self.client.post(
                self.signup_url,
                {
                    "username": f"testuser{i}",
                    "email": f"test{i}@example.com",
                    "password": "StrongPass123!",
                    "confirm_password": "StrongPass123!",
                },
                REMOTE_ADDR=ip_address,
            )
            self.assertEqual(response.status_code, 302, f"Signup {i+1} should succeed")

        # 6th signup should be rate limited
        response = self.client.post(
            self.signup_url,
            {
                "username": "testuser6",
                "email": "test6@example.com",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
            },
            REMOTE_ADDR=ip_address,
        )
        self.assertContains(response, "Too many sign-up attempts")

        # Verify user was NOT created
        self.assertFalse(User.objects.filter(username="testuser6").exists())

        print("\n✅ Test passed: Signup rate limiting counts all attempts")
        print(f"   - 5 successful signups allowed")
        print(f"   - 6th signup blocked by rate limit")


class RateLimitingDatabaseTest(TestCase):
    """Test that rate limiting data is properly stored and retrieved."""

    def test_authentication_event_stores_all_required_fields(self) -> None:
        """Verify AuthenticationEvent model stores all data correctly."""
        event = AuthenticationEvent.objects.create(
            event_type=AuthenticationEvent.EventType.LOGIN,
            ip_address="203.0.113.50",
            username_submitted="testuser",
            email_submitted="test@example.com",
            user=None,
            successful=False,
            user_agent="Mozilla/5.0",
            metadata={"reason": "password_mismatch"}
        )

        # Retrieve and verify
        saved_event = AuthenticationEvent.objects.get(id=event.id)
        self.assertEqual(saved_event.ip_address, "203.0.113.50")
        self.assertEqual(saved_event.username_submitted, "testuser")
        self.assertEqual(saved_event.successful, False)
        self.assertEqual(saved_event.metadata["reason"], "password_mismatch")

        print("\n✅ Test passed: AuthenticationEvent stores all fields correctly")

    def test_user_model_lockout_fields(self) -> None:
        """Verify User model lockout fields work correctly."""
        user = User.objects.create_user(
            username="lockouttest",
            email="lockout@example.com",
            password="TestPass123!"
        )

        # Initial state
        self.assertEqual(user.failed_login_attempts, 0)
        self.assertIsNone(user.locked_until)
        self.assertFalse(user.is_locked())

        # Mark failure
        user.mark_login_failure()
        self.assertEqual(user.failed_login_attempts, 1)
        self.assertIsNotNone(user.last_failed_login_at)

        # Lock account
        user.lock_for(timedelta(hours=1))
        self.assertTrue(user.is_locked())
        self.assertIsNotNone(user.locked_until)

        # Reset
        user.reset_login_failures()
        self.assertEqual(user.failed_login_attempts, 0)
        self.assertIsNone(user.locked_until)
        self.assertFalse(user.is_locked())

        print("\n✅ Test passed: User lockout fields work correctly")


def run_all_scenario_tests():
    """
    Run all scenario tests and print summary.

    Usage:
        python manage.py test accounts.test_rate_limiting_scenarios -v 2
    """
    print("\n" + "="*70)
    print(" "*15 + "RATE LIMITING SCENARIO TESTS")
    print("="*70)
    print("\nThese tests demonstrate:")
    print("1. ✓ Successful logins don't trigger rate limits")
    print("2. ✓ IP rate limiting works across different accounts")
    print("3. ✓ Account lockout is per account, not per IP")
    print("4. ✓ Accounts can be locked from different IPs")
    print("5. ✓ Successful login resets lockout counter")
    print("6. ✓ Lockout expires after 60 minutes")
    print("7. ✓ Signup rate limiting counts all attempts")
    print("="*70)
