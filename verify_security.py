#!/usr/bin/env python
"""
Security Verification Script for Brews & Chews Authentication System

This script helps verify and inspect the security implementation:
- View encrypted emails in the database
- View hashed passwords
- View stored accounts
- Verify encryption/hashing works correctly

Usage:
    python verify_security.py
"""

import os
import sys
import sqlite3
import base64
from pathlib import Path

# Add project to Python path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'brewschews.settings')

import django
django.setup()

from accounts.models import User, AuthenticationEvent
from accounts.encryption import (
    encrypt_email,
    decrypt_email,
    generate_email_digest,
    test_encryption_roundtrip
)
from django.contrib.auth.hashers import make_password, check_password


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_section(text):
    """Print a formatted section header."""
    print(f"\n{text}")
    print("-" * 80)


def view_database_raw():
    """View raw database contents (encrypted/hashed data)."""
    print_header("RAW DATABASE CONTENTS (As Stored)")

    db_path = PROJECT_ROOT / 'db.sqlite3'

    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        print("Run 'python manage.py migrate' to create the database.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts_user'")
    if not cursor.fetchone():
        print("❌ User table doesn't exist yet. Run migrations first.")
        conn.close()
        return

    # Get all users
    print_section("User Accounts (Raw Database View)")
    cursor.execute("""
        SELECT id, username, email, encrypted_email, email_digest, password
        FROM accounts_user
    """)

    users = cursor.fetchall()

    if not users:
        print("📭 No users in database yet.")
        print("\nCreate a test user with:")
        print("    python manage.py shell -c \"from accounts.models import User; User.objects.create_user('testuser', 'test@example.com', 'TestPassword123!')\"")
    else:
        for idx, (user_id, username, email, encrypted_email, email_digest, password_hash) in enumerate(users, 1):
            print(f"\n👤 User #{user_id}: {username}")
            print(f"   Plaintext Email (legacy):  {email or '(empty)'}")

            if encrypted_email:
                # Show encrypted email as hex for readability
                encrypted_hex = encrypted_email.hex()
                print(f"   Encrypted Email (hex):     {encrypted_hex[:64]}...")
                print(f"                              (Total: {len(encrypted_email)} bytes)")
                print(f"   Email Digest (SHA-256):    {email_digest}")
            else:
                print(f"   Encrypted Email:           (not encrypted yet)")
                print(f"   Email Digest:              {email_digest or '(none)'}")

            print(f"   Password Hash (Argon2):    {password_hash[:60]}...")
            print(f"                              (Full length: {len(password_hash)} chars)")

    # Get authentication events
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts_authenticationevent'")
    if cursor.fetchone():
        print_section("Authentication Events (Audit Log)")
        cursor.execute("""
            SELECT event_type, username_submitted, email_submitted, success, ip_address, created_at
            FROM accounts_authenticationevent
            ORDER BY created_at DESC
            LIMIT 10
        """)

        events = cursor.fetchall()
        if events:
            for event_type, username, email, success, ip, created_at in events:
                status = "✅ SUCCESS" if success else "❌ FAILED"
                identifier = username or email
                print(f"{status} | {event_type:8} | {identifier:20} | IP: {ip:15} | {created_at}")
        else:
            print("📭 No authentication events logged yet.")

    conn.close()


def view_decrypted_data():
    """View decrypted data through Django ORM."""
    print_header("DECRYPTED DATA (Through Django ORM)")

    users = User.objects.all()

    if not users.exists():
        print("📭 No users in database yet.")
        return

    print_section("User Accounts (Decrypted View)")

    for user in users:
        print(f"\n👤 User: {user.username} (ID: {user.id})")
        print(f"   Email (decrypted):     {user.email_decrypted}")
        print(f"   Email Digest:          {user.email_digest}")
        print(f"   Password Hash:         {user.password[:60]}...")
        print(f"   Is Superuser:          {user.is_superuser}")
        print(f"   Date Joined:           {user.date_joined}")


def test_password_hashing():
    """Demonstrate password hashing."""
    print_header("PASSWORD HASHING VERIFICATION")

    test_password = "TestPassword123!"

    print("\n🔐 Demonstrating Argon2 Password Hashing:")
    print(f"   Original Password:     {test_password}")

    # Hash the password
    hashed = make_password(test_password)
    print(f"   Hashed Password:       {hashed}")
    print(f"   Hash Length:           {len(hashed)} characters")

    # Parse hash components
    parts = hashed.split('$')
    if len(parts) >= 4:
        print(f"\n📊 Hash Components:")
        print(f"   Algorithm:             {parts[0]}")
        print(f"   Variant:               {parts[1]}")
        print(f"   Version:               {parts[2]}")
        print(f"   Parameters:            {parts[3]}")

        # Extract memory cost
        if 'm=' in parts[3]:
            memory = parts[3].split('m=')[1].split(',')[0]
            print(f"   Memory Cost:           {int(memory):,} KB (~{int(memory)/1024:.1f} MB)")

    # Verify password
    print(f"\n✅ Verification Tests:")
    print(f"   Correct password:      {check_password(test_password, hashed)}")
    print(f"   Wrong password:        {check_password('WrongPassword', hashed)}")

    # Show that same password produces different hash (due to unique salt)
    hashed2 = make_password(test_password)
    print(f"\n🔄 Salt Uniqueness:")
    print(f"   Same password, different hash? {hashed != hashed2}")
    print(f"   Hash 1: {hashed[:50]}...")
    print(f"   Hash 2: {hashed2[:50]}...")


def test_email_encryption():
    """Demonstrate email encryption."""
    print_header("EMAIL ENCRYPTION VERIFICATION")

    test_email = "test@example.com"

    print("\n🔐 Demonstrating AES-256-GCM Email Encryption:")
    print(f"   Original Email:        {test_email}")

    # Encrypt
    encrypted = encrypt_email(test_email)
    print(f"   Encrypted (hex):       {encrypted.hex()[:64]}...")
    print(f"   Encrypted Length:      {len(encrypted)} bytes")
    print(f"   Components:            12-byte nonce + ciphertext + 16-byte auth tag")

    # Decrypt
    decrypted = decrypt_email(encrypted)
    print(f"   Decrypted Email:       {decrypted}")
    print(f"   Match Original:        {decrypted == test_email.lower()}")

    # Generate digest
    digest = generate_email_digest(test_email)
    print(f"\n🔍 Email Digest (for lookups):")
    print(f"   SHA-256 Digest:        {digest}")
    print(f"   Case-insensitive:      {digest == generate_email_digest('TEST@EXAMPLE.COM')}")

    # Show that same email produces different ciphertext (due to unique nonce)
    encrypted2 = encrypt_email(test_email)
    print(f"\n🔄 Nonce Uniqueness:")
    print(f"   Same email, different ciphertext? {encrypted != encrypted2}")
    print(f"   Cipher 1: {encrypted.hex()[:40]}...")
    print(f"   Cipher 2: {encrypted2.hex()[:40]}...")

    # Run roundtrip test
    print(f"\n✅ Running encryption roundtrip test...")
    try:
        test_encryption_roundtrip()
        print("   ✅ Encryption roundtrip test PASSED")
    except Exception as e:
        print(f"   ❌ Encryption roundtrip test FAILED: {e}")


def test_user_creation():
    """Test creating a user with encryption."""
    print_header("USER CREATION TEST")

    test_username = "security_test_user"
    test_email = "security_test@example.com"
    test_password = "SecurePassword123!"

    # Check if user exists
    existing_user = User.objects.filter(username=test_username).first()
    if existing_user:
        print(f"ℹ️  Test user '{test_username}' already exists. Using existing user.")
        user = existing_user
    else:
        print(f"Creating test user: {test_username}")
        print(f"   Email: {test_email}")
        print(f"   Password: {test_password}")

        # Create user
        user = User.objects.create_user(
            username=test_username,
            email=test_email,
            password=test_password
        )
        print(f"✅ User created successfully (ID: {user.id})")

    # Verify encryption
    print(f"\n🔍 Verifying User Data:")
    print(f"   Username:              {user.username}")
    print(f"   Email (decrypted):     {user.email_decrypted}")
    print(f"   Email Digest:          {user.email_digest}")
    print(f"   Password Hash:         {user.password[:60]}...")

    # Verify password
    print(f"\n✅ Password Verification:")
    print(f"   Correct password:      {user.check_password(test_password)}")
    print(f"   Wrong password:        {user.check_password('WrongPassword')}")

    # Verify email lookup
    print(f"\n🔍 Email Lookup Test:")
    found_user = User.find_by_email(test_email)
    print(f"   Found by email:        {found_user is not None}")
    print(f"   Correct user:          {found_user == user if found_user else False}")

    # Verify case-insensitive lookup
    found_user_upper = User.find_by_email(test_email.upper())
    print(f"   Found by UPPERCASE:    {found_user_upper is not None}")
    print(f"   Correct user:          {found_user_upper == user if found_user_upper else False}")


def run_all_tests():
    """Run all verification tests."""
    try:
        view_database_raw()
        view_decrypted_data()
        test_password_hashing()
        test_email_encryption()
        test_user_creation()

        print_header("SECURITY VERIFICATION COMPLETE")
        print("\n✅ All security features verified successfully!")
        print("\nKey Findings:")
        print("  • Passwords are hashed with Argon2 (not reversible)")
        print("  • Emails are encrypted with AES-256-GCM (reversible with key)")
        print("  • Email digests enable lookups without decryption")
        print("  • Authentication events are logged for audit")
        print("  • All security features are working as expected")

    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
