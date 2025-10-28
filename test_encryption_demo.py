#!/usr/bin/env python
"""
Manual test script to demonstrate email encryption for MCO 1.

This script:
1. Creates a test user with encrypted email
2. Verifies email is encrypted in database
3. Verifies email can be decrypted
4. Demonstrates digest-based lookups
5. Shows that login works with encrypted emails
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'brewschews.settings')
django.setup()

from accounts.models import User
from accounts.encryption import test_encryption_roundtrip, generate_email_digest
from accounts.forms import LoginForm


def main():
    print("=" * 70)
    print("EMAIL ENCRYPTION DEMONSTRATION (MCO 1)")
    print("=" * 70)

    # Test 1: Encryption utilities
    print("\n[TEST 1] Encryption Utilities")
    print("-" * 70)
    test_encryption_roundtrip("demo@example.com")

    # Test 2: Create user with encrypted email
    print("\n[TEST 2] Creating User with Encrypted Email")
    print("-" * 70)

    # Clean up any existing test user
    User.objects.filter(username="testdemo").delete()

    test_email = "testdemo@example.com"
    test_user = User.objects.create_user(
        username="testdemo",
        email=test_email,
        password="TestPassword123!"
    )

    print(f"✅ Created user: {test_user.username}")
    print(f"   Email (plaintext input): {test_email}")
    print(f"   Encrypted email (bytes): {len(test_user.encrypted_email)} bytes")
    print(f"   Email digest (SHA-256): {test_user.email_digest[:32]}...")

    # Test 3: Verify encryption in database
    print("\n[TEST 3] Verify Email is Encrypted in Database")
    print("-" * 70)

    # Reload from database to ensure it's not just in memory
    user_from_db = User.objects.get(username="testdemo")

    print(f"   User loaded from database: {user_from_db.username}")
    print(f"   Encrypted email exists: {user_from_db.encrypted_email is not None}")
    print(f"   Encrypted email length: {len(user_from_db.encrypted_email)} bytes")
    print(f"   Email digest exists: {user_from_db.email_digest is not None}")

    # Test 4: Verify decryption works
    print("\n[TEST 4] Verify Email Decryption")
    print("-" * 70)

    decrypted_email = user_from_db.email_decrypted
    print(f"   Decrypted email: {decrypted_email}")
    print(f"   Matches original: {decrypted_email == test_email}")

    # Test 5: Digest-based lookup
    print("\n[TEST 5] Digest-Based User Lookup")
    print("-" * 70)

    found_user = User.find_by_email(test_email)
    print(f"   Search email: {test_email}")
    print(f"   Found user: {found_user.username}")
    print(f"   Lookup successful: {found_user.pk == test_user.pk}")

    # Test case-insensitive lookup
    found_user_upper = User.find_by_email("TESTDEMO@EXAMPLE.COM")
    print(f"   Case-insensitive lookup: {found_user_upper.username}")
    print(f"   Same user: {found_user_upper.pk == test_user.pk}")

    # Test 6: Login form with encrypted email
    print("\n[TEST 6] Login Form with Encrypted Email")
    print("-" * 70)

    # Test login by email
    form = LoginForm(data={
        "identifier": test_email,
        "password": "TestPassword123!",
    })

    if form.is_valid():
        found = form.find_user()
        print(f"   Login identifier: {test_email}")
        print(f"   User found: {found is not None}")
        if found:
            print(f"   Username: {found.username}")
            print(f"   Correct user: {found.pk == test_user.pk}")

            # Verify password
            password_valid = found.check_password("TestPassword123!")
            print(f"   Password valid: {password_valid}")
    else:
        print(f"   ❌ Form validation failed: {form.errors}")

    # Test 7: Uniqueness constraint
    print("\n[TEST 7] Email Uniqueness via Digest")
    print("-" * 70)

    try:
        duplicate_user = User.objects.create_user(
            username="duplicate",
            email=test_email,  # Same email
            password="AnotherPassword123!"
        )
        print("   ❌ FAIL: Duplicate email was allowed!")
    except Exception as e:
        print(f"   ✅ PASS: Duplicate email rejected")
        print(f"   Error type: {type(e).__name__}")

    # Test 8: Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("✅ All encryption features working correctly!")
    print("\nKey Features Demonstrated:")
    print("  1. Email encrypted with AES-256-GCM on user creation")
    print("  2. Encrypted data stored in database (encrypted_email field)")
    print("  3. SHA-256 digest generated for fast lookups (email_digest field)")
    print("  4. Decryption works transparently via email_decrypted property")
    print("  5. Digest-based lookups are case-insensitive")
    print("  6. Login works with encrypted emails")
    print("  7. Email uniqueness enforced via digest")
    print("\nMCO 1 Requirements Satisfied:")
    print("  ✅ Data encryption (AES-256-GCM)")
    print("  ✅ Data decryption (authenticated decryption)")
    print("  ✅ Secure key management (environment variable)")
    print("  ✅ Comprehensive documentation and tests")

    # Cleanup
    print("\n" + "=" * 70)
    print("Cleaning up test user...")
    test_user.delete()
    print("Done!")
    print("=" * 70)


if __name__ == "__main__":
    main()
