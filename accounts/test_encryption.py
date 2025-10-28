"""
Tests for email encryption functionality (MCO 1).

Test Coverage:
- Encryption/decryption utilities
- User model encryption on save
- Email digest generation and lookups
- Form validation with encrypted emails
- Login with encrypted emails
- Uniqueness constraints
- Caching behavior
- Error handling
"""

import base64
from unittest.mock import patch

from django.contrib.auth import authenticate
from django.test import TestCase, Client
from django.urls import reverse

from accounts.encryption import (
    encrypt_email,
    decrypt_email,
    generate_email_digest,
    generate_encryption_key,
    EmailEncryptionError,
    DecryptionFailedError,
    MissingEncryptionKeyError,
)
from accounts.forms import SignupForm, LoginForm
from accounts.models import User


class EncryptionUtilitiesTestCase(TestCase):
    """Test encryption utility functions."""

    def test_generate_encryption_key(self):
        """Test that generated keys are 32 bytes when decoded."""
        key = generate_encryption_key()

        # Should be base64 encoded
        decoded = base64.b64decode(key)

        # Should be exactly 32 bytes (256 bits)
        self.assertEqual(len(decoded), 32)

    def test_encrypt_decrypt_roundtrip(self):
        """Test that encryption and decryption are inverses."""
        original_email = "test@example.com"

        # Encrypt
        encrypted = encrypt_email(original_email)

        # Should be bytes
        self.assertIsInstance(encrypted, bytes)

        # Should be longer than 12 bytes (nonce + ciphertext)
        self.assertGreater(len(encrypted), 12)

        # Decrypt
        decrypted = decrypt_email(encrypted)

        # Should match original (normalized to lowercase)
        self.assertEqual(decrypted, original_email.lower())

    def test_encrypt_normalizes_email(self):
        """Test that encryption normalizes email to lowercase."""
        emails = [
            "TEST@example.com",
            "Test@Example.Com",
            "test@EXAMPLE.COM",
        ]

        for email in emails:
            encrypted = encrypt_email(email)
            decrypted = decrypt_email(encrypted)
            self.assertEqual(decrypted, "test@example.com")

    def test_different_emails_produce_different_ciphertexts(self):
        """Test that different emails produce different encrypted values."""
        email1 = "alice@example.com"
        email2 = "bob@example.com"

        encrypted1 = encrypt_email(email1)
        encrypted2 = encrypt_email(email2)

        # Should be different
        self.assertNotEqual(encrypted1, encrypted2)

    def test_same_email_produces_different_ciphertexts(self):
        """Test that same email encrypted twice produces different ciphertexts (unique nonces)."""
        email = "test@example.com"

        encrypted1 = encrypt_email(email)
        encrypted2 = encrypt_email(email)

        # Should be different (due to unique nonces)
        self.assertNotEqual(encrypted1, encrypted2)

        # But both should decrypt to same value
        self.assertEqual(decrypt_email(encrypted1), decrypt_email(encrypted2))

    def test_generate_email_digest(self):
        """Test SHA-256 digest generation."""
        email = "test@example.com"

        digest = generate_email_digest(email)

        # Should be 64 hex characters (SHA-256)
        self.assertEqual(len(digest), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in digest))

    def test_email_digest_is_deterministic(self):
        """Test that same email always produces same digest."""
        email = "test@example.com"

        digest1 = generate_email_digest(email)
        digest2 = generate_email_digest(email)

        self.assertEqual(digest1, digest2)

    def test_email_digest_is_case_insensitive(self):
        """Test that email digest is case-insensitive."""
        emails = [
            "TEST@example.com",
            "Test@Example.Com",
            "test@example.com",
        ]

        digests = [generate_email_digest(email) for email in emails]

        # All should be the same
        self.assertEqual(len(set(digests)), 1)

    def test_decrypt_invalid_data_raises_error(self):
        """Test that decrypting invalid data raises DecryptionFailedError."""
        invalid_data = b"not valid encrypted data"

        with self.assertRaises(DecryptionFailedError):
            decrypt_email(invalid_data)

    def test_decrypt_empty_data_raises_error(self):
        """Test that decrypting empty data raises DecryptionFailedError."""
        with self.assertRaises(DecryptionFailedError):
            decrypt_email(b"")

    def test_decrypt_short_data_raises_error(self):
        """Test that decrypting data shorter than nonce raises DecryptionFailedError."""
        short_data = b"short"  # Less than 12 bytes

        with self.assertRaises(DecryptionFailedError):
            decrypt_email(short_data)


class UserModelEncryptionTestCase(TestCase):
    """Test User model encryption functionality."""

    def test_user_creation_encrypts_email(self):
        """Test that creating a user encrypts the email."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPassword123!"
        )

        # Should have encrypted email
        self.assertIsNotNone(user.encrypted_email)
        self.assertIsInstance(user.encrypted_email, bytes)
        self.assertGreater(len(user.encrypted_email), 12)

        # Should have email digest
        self.assertIsNotNone(user.email_digest)
        self.assertEqual(len(user.email_digest), 64)

    def test_user_email_decrypted_property(self):
        """Test that email_decrypted property returns plaintext email."""
        email = "test@example.com"
        user = User.objects.create_user(
            username="testuser",
            email=email,
            password="TestPassword123!"
        )

        # Reload from database to clear cache
        user = User.objects.get(pk=user.pk)

        # Should decrypt correctly
        self.assertEqual(user.email_decrypted, email)

    def test_email_decrypted_caching(self):
        """Test that email_decrypted caches the decrypted value."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPassword123!"
        )

        # Reload from database
        user = User.objects.get(pk=user.pk)

        # First access should decrypt and cache
        with patch('accounts.models.decrypt_email') as mock_decrypt:
            mock_decrypt.return_value = "test@example.com"
            email1 = user.email_decrypted
            self.assertEqual(mock_decrypt.call_count, 1)

            # Second access should use cache (no additional decryption)
            email2 = user.email_decrypted
            self.assertEqual(mock_decrypt.call_count, 1)  # Still 1, not 2

            self.assertEqual(email1, email2)

    def test_find_by_email_method(self):
        """Test User.find_by_email() static method."""
        email = "alice@example.com"
        user = User.objects.create_user(
            username="alice",
            email=email,
            password="TestPassword123!"
        )

        # Should find user by email
        found_user = User.find_by_email(email)
        self.assertEqual(found_user.pk, user.pk)
        self.assertEqual(found_user.username, "alice")

    def test_find_by_email_case_insensitive(self):
        """Test that find_by_email is case-insensitive."""
        user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="TestPassword123!"
        )

        # Should find with different cases
        variations = [
            "ALICE@example.com",
            "Alice@Example.Com",
            "alice@EXAMPLE.COM",
        ]

        for email in variations:
            found_user = User.find_by_email(email)
            self.assertEqual(found_user.pk, user.pk)

    def test_email_digest_uniqueness_constraint(self):
        """Test that email_digest enforces uniqueness."""
        email = "test@example.com"

        # Create first user
        User.objects.create_user(
            username="user1",
            email=email,
            password="TestPassword123!"
        )

        # Try to create second user with same email (should fail)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username="user2",
                email=email,
                password="TestPassword123!"
            )


class SignupFormEncryptionTestCase(TestCase):
    """Test SignupForm with encrypted emails."""

    def test_signup_form_detects_duplicate_email(self):
        """Test that SignupForm detects duplicate emails using digest."""
        # Create existing user
        User.objects.create_user(
            username="existing",
            email="test@example.com",
            password="TestPassword123!"
        )

        # Try to sign up with same email
        form = SignupForm(data={
            "username": "newuser",
            "email": "test@example.com",
            "password": "NewPassword123!",
            "confirm_password": "NewPassword123!",
        })

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertIn("already registered", str(form.errors["email"]))

    def test_signup_form_case_insensitive_duplicate_detection(self):
        """Test that duplicate detection is case-insensitive."""
        # Create user with lowercase email
        User.objects.create_user(
            username="existing",
            email="test@example.com",
            password="TestPassword123!"
        )

        # Try to sign up with uppercase email
        form = SignupForm(data={
            "username": "newuser",
            "email": "TEST@EXAMPLE.COM",
            "password": "NewPassword123!",
            "confirm_password": "NewPassword123!",
        })

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_signup_form_save_encrypts_email(self):
        """Test that SignupForm.save() creates user with encrypted email."""
        form = SignupForm(data={
            "username": "newuser",
            "email": "new@example.com",
            "password": "NewPassword123!",
            "confirm_password": "NewPassword123!",
        })

        self.assertTrue(form.is_valid())

        user = form.save()

        # Should have encrypted email
        self.assertIsNotNone(user.encrypted_email)
        self.assertIsNotNone(user.email_digest)

        # Should be able to decrypt
        self.assertEqual(user.email_decrypted, "new@example.com")


class LoginFormEncryptionTestCase(TestCase):
    """Test LoginForm with encrypted emails."""

    def test_login_form_finds_user_by_email(self):
        """Test that LoginForm.find_user() works with encrypted emails."""
        # Create user
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPassword123!"
        )

        # Search by email
        form = LoginForm(data={
            "identifier": "test@example.com",
            "password": "TestPassword123!",
        })

        self.assertTrue(form.is_valid())

        found_user = form.find_user()
        self.assertIsNotNone(found_user)
        self.assertEqual(found_user.pk, user.pk)

    def test_login_form_email_case_insensitive(self):
        """Test that email login is case-insensitive."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPassword123!"
        )

        # Try different cases
        emails = ["TEST@example.com", "Test@Example.Com", "test@EXAMPLE.COM"]

        for email in emails:
            form = LoginForm(data={
                "identifier": email,
                "password": "TestPassword123!",
            })

            self.assertTrue(form.is_valid())

            found_user = form.find_user()
            self.assertIsNotNone(found_user, f"Failed to find user with email: {email}")
            self.assertEqual(found_user.pk, user.pk)


class LoginViewEncryptionTestCase(TestCase):
    """Test login view with encrypted emails."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPassword123!"
        )

    def test_login_with_email_identifier(self):
        """Test logging in with email as identifier."""
        response = self.client.post(reverse("accounts:login"), {
            "identifier": "test@example.com",
            "password": "TestPassword123!",
        })

        # Should redirect on success
        self.assertEqual(response.status_code, 302)

        # Should be logged in
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.pk, self.user.pk)

    def test_login_with_email_case_insensitive(self):
        """Test login with different email cases."""
        emails = ["TEST@example.com", "Test@Example.Com"]

        for email in emails:
            # Logout first
            self.client.logout()

            response = self.client.post(reverse("accounts:login"), {
                "identifier": email,
                "password": "TestPassword123!",
            })

            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.wsgi_request.user.is_authenticated)


class SignupViewEncryptionTestCase(TestCase):
    """Test signup view with encrypted emails."""

    def setUp(self):
        self.client = Client()

    def test_signup_creates_encrypted_email(self):
        """Test that signup creates user with encrypted email."""
        response = self.client.post(reverse("accounts:signup"), {
            "username": "newuser",
            "email": "new@example.com",
            "password": "NewPassword123!",
            "confirm_password": "NewPassword123!",
        })

        # Should redirect on success
        self.assertEqual(response.status_code, 302)

        # User should exist with encrypted email
        user = User.objects.get(username="newuser")
        self.assertIsNotNone(user.encrypted_email)
        self.assertIsNotNone(user.email_digest)
        self.assertEqual(user.email_decrypted, "new@example.com")

    def test_signup_rejects_duplicate_email(self):
        """Test that signup rejects duplicate emails."""
        # Create existing user
        User.objects.create_user(
            username="existing",
            email="test@example.com",
            password="TestPassword123!"
        )

        # Try to sign up with same email
        response = self.client.post(reverse("accounts:signup"), {
            "username": "newuser",
            "email": "test@example.com",
            "password": "NewPassword123!",
            "confirm_password": "NewPassword123!",
        })

        # Should show form with errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already registered")

        # User should not be created
        self.assertFalse(User.objects.filter(username="newuser").exists())
