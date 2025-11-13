#!/usr/bin/env python3
"""
Script to view and verify all stored accounts in the database.
Shows encrypted/decrypted emails and password hashes.

Usage: python view_accounts.py
"""

import os
import sys
import sqlite3
from pathlib import Path
from tabulate import tabulate

# Setup Django environment
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'brewschews.settings')

import django
django.setup()

from accounts.models import User
from accounts.encryption import decrypt_email, encrypt_email, generate_email_digest
from django.contrib.auth.hashers import check_password


def print_separator(char='=', length=100):
    """Print a separator line."""
    print(char * length)


def view_all_accounts():
    """Display all accounts with decrypted information."""
    print_separator()
    print("📊 STORED ACCOUNTS IN DATABASE")
    print_separator()

    users = User.objects.all()

    if not users.exists():
        print("\n⚠️  No accounts found in database.\n")
        return

    print(f"\nTotal accounts: {users.count()}\n")

    for idx, user in enumerate(users, 1):
        print_separator('-')
        print(f"🔹 ACCOUNT #{idx}")
        print_separator('-')

        # Basic info
        print(f"👤 Username:        {user.username}")
        print(f"🆔 User ID:         {user.id}")
        print(f"📅 Date Joined:     {user.date_joined.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔓 Active:          {user.is_active}")
        print(f"👑 Staff:           {user.is_staff}")
        print(f"🔐 Superuser:       {user.is_superuser}")

        # Email information
        print(f"\n📧 EMAIL INFORMATION:")
        print(f"   ├─ Decrypted Email:      {user.email_decrypted or '(not set)'}")

        if user.encrypted_email:
            encrypted_hex = user.encrypted_email.hex()
            print(f"   ├─ Encrypted (hex):      {encrypted_hex[:60]}..." if len(encrypted_hex) > 60 else f"   ├─ Encrypted (hex):      {encrypted_hex}")
            print(f"   ├─ Encrypted (length):   {len(user.encrypted_email)} bytes")
        else:
            print(f"   ├─ Encrypted (hex):      (not set)")

        if user.email_digest:
            print(f"   └─ Email Digest (SHA256): {user.email_digest}")
        else:
            print(f"   └─ Email Digest (SHA256): (not set)")

        # Password information
        print(f"\n🔒 PASSWORD INFORMATION:")
        print(f"   ├─ Hash Algorithm:       {user.password.split('$')[0] if '$' in user.password else 'unknown'}")
        print(f"   ├─ Full Hash:            {user.password}")
        print(f"   └─ Hash Length:          {len(user.password)} characters")

        # Profile information (if exists)
        if hasattr(user, 'profile'):
            profile = user.profile
            print(f"\n👨‍💼 PROFILE INFORMATION:")
            print(f"   ├─ Display Name:         {profile.display_name or '(not set)'}")
            print(f"   ├─ Phone Number:         {profile.phone_number or '(not set)'}")
            print(f"   ├─ Favorite Drink:       {profile.favorite_drink or '(not set)'}")
            print(f"   └─ Bio:                  {profile.bio[:50] + '...' if profile.bio and len(profile.bio) > 50 else profile.bio or '(not set)'}")

        print()

    print_separator()


def view_raw_database():
    """View raw database entries directly from SQLite."""
    print_separator()
    print("🗄️  RAW DATABASE VIEW (SQLite Direct Access)")
    print_separator()

    db_path = PROJECT_ROOT / 'db.sqlite3'

    if not db_path.exists():
        print(f"\n⚠️  Database file not found: {db_path}\n")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all users from accounts_user table
    cursor.execute("""
        SELECT id, username, email, encrypted_email, email_digest, password,
               is_active, is_staff, is_superuser, date_joined
        FROM accounts_user
        ORDER BY id
    """)

    rows = cursor.fetchall()

    if not rows:
        print("\n⚠️  No accounts found in database.\n")
        conn.close()
        return

    print(f"\nTotal records: {len(rows)}\n")

    for row in rows:
        user_id, username, email, encrypted_email, email_digest, password, is_active, is_staff, is_superuser, date_joined = row

        print(f"ID: {user_id}")
        print(f"  Username:          {username}")
        print(f"  Email (plaintext): {email or '(empty)'}")
        print(f"  Encrypted Email:   {encrypted_email.hex()[:60] + '...' if encrypted_email else '(null)'}")
        print(f"  Email Digest:      {email_digest or '(null)'}")
        print(f"  Password Hash:     {password[:80]}...")
        print(f"  Active/Staff/Super: {is_active}/{is_staff}/{is_superuser}")
        print(f"  Date Joined:       {date_joined}")
        print()

    conn.close()
    print_separator()


def test_password_verification(username, test_password):
    """Test password verification for a specific user."""
    print_separator()
    print("🔐 PASSWORD VERIFICATION TEST")
    print_separator()

    try:
        user = User.objects.get(username=username)
        is_valid = check_password(test_password, user.password)

        print(f"\nUsername:       {username}")
        print(f"Test Password:  {test_password}")
        print(f"Stored Hash:    {user.password}")
        print(f"✅ Valid:       {is_valid}")

        if is_valid:
            print(f"\n✅ Password '{test_password}' is CORRECT for user '{username}'")
        else:
            print(f"\n❌ Password '{test_password}' is INCORRECT for user '{username}'")

    except User.DoesNotExist:
        print(f"\n❌ User '{username}' not found in database.")

    print()
    print_separator()


def test_email_encryption_decryption():
    """Test email encryption and decryption process."""
    print_separator()
    print("🔐 EMAIL ENCRYPTION/DECRYPTION TEST")
    print_separator()

    test_email = "test@example.com"

    print(f"\nOriginal Email:    {test_email}")

    # Encrypt
    encrypted = encrypt_email(test_email)
    print(f"Encrypted (hex):   {encrypted.hex()}")
    print(f"Encrypted (len):   {len(encrypted)} bytes")

    # Decrypt
    decrypted = decrypt_email(encrypted)
    print(f"Decrypted Email:   {decrypted}")

    # Digest
    digest = generate_email_digest(test_email)
    print(f"Email Digest:      {digest}")

    # Verify
    if test_email.lower().strip() == decrypted.lower().strip():
        print(f"\n✅ Encryption/Decryption working correctly!")
    else:
        print(f"\n❌ Encryption/Decryption FAILED!")

    print()
    print_separator()


def export_accounts_summary():
    """Export a summary table of all accounts."""
    print_separator()
    print("📋 ACCOUNTS SUMMARY TABLE")
    print_separator()

    users = User.objects.all()

    if not users.exists():
        print("\n⚠️  No accounts found.\n")
        return

    table_data = []
    headers = ["ID", "Username", "Email (Decrypted)", "Active", "Staff", "Superuser", "Date Joined"]

    for user in users:
        table_data.append([
            user.id,
            user.username,
            user.email_decrypted or "(not set)",
            "✓" if user.is_active else "✗",
            "✓" if user.is_staff else "✗",
            "✓" if user.is_superuser else "✗",
            user.date_joined.strftime('%Y-%m-%d')
        ])

    print()
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print()
    print_separator()


def main():
    """Main function to run all viewing operations."""
    print("\n")
    print("=" * 100)
    print(" " * 30 + "🔍 ACCOUNT DATABASE VIEWER")
    print("=" * 100)
    print("\nThis script displays all stored accounts with encryption details.")
    print("Note: Passwords are hashed with Argon2 (one-way) - plaintext cannot be retrieved.\n")

    # Main account view
    view_all_accounts()

    # Summary table
    export_accounts_summary()

    # Raw database view
    view_raw_database()

    # Email encryption test
    test_email_encryption_decryption()

    # Optional: Test password verification
    print("\n💡 To test password verification for a specific user, run:")
    print("   python view_accounts.py --test-password <username> <password>")
    print("\n")


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--test-password":
        username = sys.argv[2]
        password = sys.argv[3]
        test_password_verification(username, password)
    else:
        main()
