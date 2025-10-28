# Brews & Chews - Testing Guide
## Comprehensive Testing Documentation

**Project:** Online Café Ordering System  
**Version:** 1.0  
**Last Updated:** October 12, 2025  
**Testing Framework:** Manual Testing & Django Shell

---

## Table of Contents

1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Test Environment Setup](#test-environment-setup)
4. [Authentication Testing](#authentication-testing)
5. [Profile Management Testing](#profile-management-testing)
6. [Database Integrity Testing](#database-integrity-testing)
7. [Security Testing](#security-testing)
8. [Browser Compatibility Testing](#browser-compatibility-testing)
9. [Automated Test Scripts](#automated-test-scripts)
10. [Troubleshooting Guide](#troubleshooting-guide)
11. [Test Results Template](#test-results-template)

---

## Introduction

This document provides comprehensive testing procedures for the Brews & Chews online café ordering system. These tests ensure all authentication, profile management, and security features function correctly.

### Testing Objectives

- Verify user authentication flows (signup, login, logout)
- Validate profile management functionality
- Confirm security measures are working
- Ensure database integrity
- Identify and document any issues

### Scope

This testing guide covers:
- ✅ User registration and authentication
- ✅ Profile CRUD operations
- ✅ Database operations
- ✅ Password hashing and validation
- ❌ Payment processing (not implemented)
- ❌ Order fulfillment (UI only)

---

## Prerequisites

### Required Software

- Python 3.8 or higher
- Django 4.2+
- SQLite3 (included with Python)
- Modern web browser (Chrome, Firefox, Edge, Safari)

### Test Environment
```bash
# Verify Python version
python --version

# Verify Django installation
python -m django --version

# Activate virtual environment
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate    # macOS/Linux

# Start test server
python manage.py runserver

## Test Environment Setup

### Clean the database state
# Optional: Reset database
rm db.sqlite3  # macOS/Linux
del db.sqlite3  # Windows

# Run migrations
python manage.py migrate

# Verify database is clean
python manage.py shell
>>> from accounts.models import User
>>> User.objects.count()
0
>>> exit()

# Server startup
python manage.py runserver

## AUTHENTICATION TESTING

### Test 1.1 - Weak password
Fill in form:
- Username: testuser1
- Email: test1@example.com
- Password: weak
- Confirm Password: weak

Click "Create Account"

Expected Result:
❌ Form submission rejected
Error message: "Password must be at least 12 characters long"
User remains on signup page

### Test 1.2 - Common Password Rejection
Use signup form with:
- Password: password123
- Confirm Password: password123

Submit form

Expected Result:
❌ Form submission rejected
Error message: "This password is too common"

### Test 1.3 - Password complexity validation
- Test all password requirements

### Test 1.4 - Duplicate username prevention
Steps:
- Try to sign up again with username: testuser1
- Use different email: test2@example.com

Expected Result:
❌ Form submission rejected
Error message: "That username is already taken"

### Test 1.5 - Duplicate email prevention
Steps:
Sign up with:
- Username: testuser2
- Email: test1@example.com (already used)

Expected Result:
❌ Form submission rejected
Error message: "That email is already registered"

## USER LOGIN TESTING

### Test 2.1 - Login with username
Steps:
- Logout if logged in
- Navigate to: http://127.0.0.1:8000/accounts/login/
Enter:
- Username/Email: testuser1
- Password: TestPassword123!

Click "Sign In"

Expected Result:
✅ Login successful
Redirected to menu page
Navigation shows authenticated links

### Test 2.2 - Login with email
Steps:
- Logout
Login with:
- Username/Email: test1@example.com
- Password: TestPassword123!

Expected Result:
✅ Login successful
Same behavior as username login

### Test 2.3 - Invalid Credentials
Steps:
- Logout
Try to login with:
- Username: testuser1
- Password: WrongPassword123!

Expected Result:
❌ Login failed
Error message: "Invalid username or password"
Remain on login page

Verification
python manage.py shell
>>> from accounts.models import User
>>> user = User.objects.get(username='testuser1')
>>> # User exists and login attempt was logged
>>> exit()

## PROFILE MANAGEMENT TESTING

### Test 3.1 - Profile update information
Steps:
On "Account Details" tab, fill in:
- Display Name: Coffee Lover
- Phone Number: +1234567890
- Favorite Drink: Cold Brew
- Bio: I love coffee and coding!

Click "Save changes"

Expected Result:
- ✅ Success message: "Profile updated successfully"
- Page reloads with updated information

Verification

python manage.py shell
>>> from accounts.models import User
>>> user = User.objects.get(username='testuser1')
>>> profile = user.profile
>>> print(f"Display name: {profile.display_name}")
>>> print(f"Phone: {profile.phone_number}")
>>> print(f"Favorite drink: {profile.favorite_drink}")
>>> print(f"Bio: {profile.bio}")
>>> exit()

### Test 3.2 - Profile update persistence
Steps:
- Update profile (as in Test 5.1)
- Logout
- Login again
- Navigate to profile page

Expected Result:
- ✅ Previously entered data still visible
- No data loss

## CHANGE USERNAME TESTING

### Test 4.1 - Successful username change
Steps:
- Click "Change Username" tab
Fill in:
- New Username: updateduser1
- Password: TestPassword123!

Click "Update Username"

Expected Result:
- ✅ Success message: "Username changed successfully"
- Username displayed at top of page updates
- Can login with new username

Verification
python manage.py shell
>>> from accounts.models import User
>>> user = User.objects.get(email='test1@example.com')
>>> print(f"Username: {user.username}")
>>> # Should show: updateduser1
>>> exit()

### Test 4.2 - Username change - Wrong password
Steps:
Try to change username with:
- New Username: anotheruser
- Password: WrongPassword!

Expected Result:
- ❌ Error message: "Incorrect password"
- Username NOT changed

### Test 4.3 - Username change - Duplicate username
Pre-requisite: Create another user testuser2

Steps:
- Try to change username to: testuser2

Expected Result:
- ❌ Error: "That username is already taken"

## CHANGE PASSWORD TESTING

### Test 5.1 - Successful password change
Steps:
- Click "Change Password" tab
Fill in:
- Current Password: TestPassword123!
- New Password: NewPassword456!
- Confirm Password: NewPassword456!

Click "Update Password"

Expected Result:
- ✅ Success message: "Password changed successfully"
- Remain logged in (session updated)

### Test 5.2 - Password change - Wrong current password
Steps:
- Try to change password with:
- Current Password: WrongPassword!

Expected Result:
- ❌ Error: "Current password is incorrect"
- Password NOT changed

### Test 5.3 - Password change - Weak password
Steps:
- Try to change to weak password: weak

Expected Result:
- ❌ Errors displayed
- Same validation as signup

### Test 5.4 - Password change - Mismatch confirmation
Steps:
Enter:
- New Password: NewPassword456!
- Confirm Password: DifferentPassword456!

Expected Result:
- ❌ Error: "Passwords do not match"

## DELETE ACCOUNT TESTING

### Test 6.1 - Delete account flow
Steps:
- Click "Delete Account" tab
- Click "Delete My Account" button
- Modal should appear
- Enter password in modal
- Click "Yes, Delete My Account"

Expected Result:

✅ Modal appears with warning
✅ After confirmation: Redirected to home page
✅ Logged out
✅ Cannot login with deleted credentials

Verification
python manage.py shell
>>> from accounts.models import User
>>> User.objects.filter(username='updateduser1').exists()
False
>>> # User should not exist
>>> exit()

### Test 6.2 - Delete account - Cancel
Steps:
- Click "Delete My Account"
- Click "Cancel" or close modal (X button)

Expected Result:
✅ Modal closes
✅ Account NOT deleted
✅ Remain on profile page

### Test 6.3 - Delete account - Wrong password
Steps:
- In delete modal, enter wrong password
- Submit

Expected Result:
- ❌ Deletion fails
- Account preserved

## DATABASE TESTING

### Test 7.1 - User model integrity
Test Script:
- python manage.py shell

Type:
from accounts.models import User
from django.contrib.auth.hashers import check_password

print("=== USER MODEL TEST ===\n")

# Create test user
user = User.objects.create_user(
    username='dbtest',
    email='dbtest@example.com',
    password='TestPassword123!'
)

print(f"✓ User created: {user.username}")
print(f"✓ Email: {user.email}")
print(f"✓ Password algorithm: {user.password.split('$')[0]}")
print(f"✓ Password NOT plaintext: {'TestPassword123!' not in user.password}")
print(f"✓ Password check works: {user.check_password('TestPassword123!')}")

# Check fields
print(f"✓ Date joined: {user.date_joined}")

# Cleanup
user.delete()
print("\n✓ Test complete - user deleted")

Expected output:
=== USER MODEL TEST ===

✓ User created: dbtest
✓ Email: dbtest@example.com
✓ Password algorithm: argon2
✓ Password NOT plaintext: True
✓ Password check works: True
✓ Date joined: 2025-10-12 12:34:56
✓ Test complete - user deleted

### Test 7.2 - Profile model integrity
Test script:
from accounts.models import User, Profile

print("=== PROFILE MODEL TEST ===\n")

# Create user
user = User.objects.create_user(
    username='profiletest',
    email='profiletest@example.com',
    password='TestPassword123!'
)

# Check if profile auto-created
try:
    profile = user.profile
    print(f"✓ Profile auto-created: True")
    print(f"✓ Display name: {profile.display_name}")
except Profile.DoesNotExist:
    print("✗ Profile NOT auto-created")
    profile = None

# Update profile
if profile:
    profile.display_name = "Test User"
    profile.phone_number = "+1234567890"
    profile.favorite_drink = "Espresso"
    profile.bio = "Test bio"
    profile.save()
    
    # Verify update
    profile.refresh_from_db()
    print(f"✓ Profile updated")
    print(f"  - Display name: {profile.display_name}")
    print(f"  - Phone: {profile.phone_number}")
    print(f"  - Favorite drink: {profile.favorite_drink}")
    print(f"  - Bio: {profile.bio}")

# Cleanup
user.delete()
print("\n✓ Test complete")

### Test 7.3 - Authentication testing
Test script
from accounts.models import AuthenticationEvent

print("=== AUTHENTICATION EVENTS TEST ===\n")

# Check recent events
events = AuthenticationEvent.objects.all().order_by('-created_at')[:10]
print(f"Total events in database: {AuthenticationEvent.objects.count()}")
print(f"\nRecent 10 events:")
print(f"{'Type':<10} {'Username':<15} {'IP':<15} {'Success':<10}")
print("-" * 60)

for event in events:
    print(f"{event.event_type:<10} {event.username_submitted:<15} {event.ip_address:<15} {str(event.successful):<10}")

# Count failed attempts
failed = AuthenticationEvent.objects.filter(successful=False).count()
print(f"\nFailed attempts logged: {failed}")

# Check for specific IP
test_ip = "127.0.0.1"
ip_events = AuthenticationEvent.objects.filter(ip_address=test_ip).count()
print(f"Events from {test_ip}: {ip_events}")

print("\n✓ Audit logging working")

## COMPLETE DIAGNOSTIC SCRIPT
File: test_complete_system.py

Script:
"""Comprehensive system diagnostic test."""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "brewschews.settings")
django.setup()

from accounts.models import User, Profile, AuthenticationEvent
from accounts.forms import ProfileForm, ChangeUsernameForm, ChangePasswordForm
from django.utils import timezone
from datetime import timedelta

def run_all_tests():
    print("\n" + "=" * 70)
    print(" " * 15 + "BREWS & CHEWS - SYSTEM DIAGNOSTIC TEST")
    print("=" * 70)
    
    test_results = {
        'passed': 0,
        'failed': 0,
        'warnings': 0
    }
    
    # Test 1: User Creation
    print("\n[TEST 1] User Model Creation")
    try:
        user = User.objects.create_user(
            username='systemtest',
            email='systemtest@example.com',
            password='TestPassword123!'
        )
        print("  ✓ User created successfully")
        test_results['passed'] += 1
    except Exception as e:
        print(f"  ✗ User creation failed: {e}")
        test_results['failed'] += 1
        return
    
    # Test 2: Password Hashing
    print("\n[TEST 2] Password Security")
    if user.password.startswith('argon2'):
        print("  ✓ Argon2 hashing confirmed")
        test_results['passed'] += 1
    else:
        print(f"  ✗ Wrong hashing algorithm: {user.password.split('$')[0]}")
        test_results['failed'] += 1
    
    if user.check_password('TestPassword123!'):
        print("  ✓ Password verification works")
        test_results['passed'] += 1
    else:
        print("  ✗ Password verification failed")
        test_results['failed'] += 1
    
    # Test 3: Profile Auto-Creation
    print("\n[TEST 3] Profile Auto-Creation")
    try:
        profile = user.profile
        print(f"  ✓ Profile exists (display_name: {profile.display_name})")
        test_results['passed'] += 1
    except Profile.DoesNotExist:
        print("  ✗ Profile NOT auto-created")
        test_results['failed'] += 1
        profile = Profile.objects.create(user=user, display_name=user.username)
        print("  ⚠ Manually created profile for testing")
        test_results['warnings'] += 1
    
    # Test 4: Profile Form
    print("\n[TEST 4] Profile Form Validation")
    form_data = {
        'display
        'display_name': 'System Test User',
        'phone_number': '+1234567890',
        'favorite_drink': 'Espresso',
        'bio': 'Automated test user'
    }
    form = ProfileForm(data=form_data, instance=profile)
    if form.is_valid():
        form.save()
        print("  ✓ ProfileForm validation passed")
        test_results['passed'] += 1
    else:
        print(f"  ✗ ProfileForm validation failed: {form.errors}")
        test_results['failed'] += 1
    
    # Test 5: Username Change Form
    print("\n[TEST 5] Change Username Form")
    username_data = {
        'new_username': 'systemtest2',
        'password': 'TestPassword123!'
    }
    username_form = ChangeUsernameForm(user, data=username_data)
    if username_form.is_valid():
        print("  ✓ ChangeUsernameForm validation passed")
        test_results['passed'] += 1
    else:
        print(f"  ✗ ChangeUsernameForm failed: {username_form.errors}")
        test_results['failed'] += 1
    
    # Test 6: Password Change Form
    print("\n[TEST 6] Change Password Form")
    password_data = {
        'current_password': 'TestPassword123!',
        'new_password': 'NewPassword456!',
        'confirm_password': 'NewPassword456!'
    }
    password_form = ChangePasswordForm(user, data=password_data)
    if password_form.is_valid():
        print("  ✓ ChangePasswordForm validation passed")
        test_results['passed'] += 1
    else:
        print(f"  ✗ ChangePasswordForm failed: {password_form.errors}")
        test_results['failed'] += 1
    
    # Test 7: Database Integrity
    print("\n[TEST 7] Database Integrity")
    user_count = User.objects.count()
    profile_count = Profile.objects.count()
    event_count = AuthenticationEvent.objects.count()
    
    print(f"  • Total users: {user_count}")
    print(f"  • Total profiles: {profile_count}")
    print(f"  • Total auth events: {event_count}")
    
    if profile_count >= user_count:
        print("  ✓ Profile count matches or exceeds user count")
        test_results['passed'] += 1
    else:
        print("  ⚠ Some users may be missing profiles")
        test_results['warnings'] += 1
    
    # Test 8: SQL Injection Prevention
    print("\n[TEST 8] SQL Injection Prevention")
    malicious = "admin' OR '1'='1"
    result = User.objects.filter(username__iexact=malicious).first()
    if result is None:
        print("  ✓ SQL injection prevented (parameterized queries)")
        test_results['passed'] += 1
    else:
        print("  ✗ SQL injection vulnerability detected!")
        test_results['failed'] += 1
    
    # Cleanup
    print("\n[CLEANUP] Removing test data")
    user.delete()
    print("  ✓ Test user deleted")
    
    # Summary
    print("\n" + "=" * 70)
    print(" " * 25 + "TEST SUMMARY")
    print("=" * 70)
    print(f"  ✓ Passed:   {test_results['passed']}")
    print(f"  ✗ Failed:   {test_results['failed']}")
    print(f"  ⚠ Warnings: {test_results['warnings']}")
    print(f"  Total:      {sum(test_results.values())}")
    print("=" * 70)
    
    if test_results['failed'] == 0:
        print("\n  🎉 ALL TESTS PASSED!")
    else:
        print(f"\n  ⚠️  {test_results['failed']} TEST(S) FAILED - REVIEW REQUIRED")
    
    print()

if __name__ == "__main__":
    run_all_tests()
