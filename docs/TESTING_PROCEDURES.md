# Testing Procedures & QA Guide

## What It Is

This guide provides testing procedures for the Brews & Chews café ordering system for MCO 1. It covers automated tests, manual testing checklists, security verification, and debugging to ensure all features work correctly before presentation.

---

## Testing Philosophy

```
┌─────────────────────────────────────────┐
│         Testing Pyramid                 │
├─────────────────────────────────────────┤
│                  E2E                    │ ← Full user workflows
│               (Manual)                  │
├───────────────────────────────────────┬─┤
│         Integration Tests             │ │ ← Feature interactions
│         (Django Tests)                │ │
├──────────────────────────────────────┬┼─┤
│           Unit Tests                 │││ │ ← Individual functions
│        (Django Tests)                │││ │
└──────────────────────────────────────┴┴─┴┘
   More tests, faster feedback ←→ Fewer tests, realistic scenarios
```

### Testing Best Practices

**Do's:**
✓ Run tests before committing changes
✓ Test edge cases (empty input, special characters)
✓ Use descriptive test names
✓ Keep tests independent
✓ Test security (injection, XSS, CSRF)

**Don'ts:**
✗ Don't skip tests because they're "too slow"
✗ Don't test Django's built-in functionality
✗ Don't use production database for testing
✗ Don't ignore failing tests

---

## 1. Automated Testing

### Running Django Tests

**Run all tests:**
```bash
python manage.py test
```

**Run specific app tests:**
```bash
python manage.py test accounts
python manage.py test menu
```

**Run specific test class:**
```bash
python manage.py test accounts.tests.SignupViewTests
python manage.py test accounts.test_encryption.EncryptionUtilitiesTestCase
```

**Run with verbose output:**
```bash
python manage.py test --verbosity=2
```

### Test File Locations

| App | Test File | Description |
|-----|-----------|-------------|
| accounts | `accounts/tests.py` | Authentication, profile tests (17 tests) |
| accounts | `accounts/test_encryption.py` | Email encryption tests (20 tests) |
| menu | `menu/tests.py` | Menu display tests |
| orders | `orders/tests.py` | Cart/order tests (minimal) |

### Test Classes Overview

**accounts/tests.py:**
- `SignupViewTests` - User registration (4 tests)
- `LoginViewTests` - User authentication (3 tests)
- `ProfileViewTests` - Profile management (2 tests)
- `LogoutViewTests` - Logout functionality (2 tests)

**accounts/test_encryption.py:**
- `EncryptionUtilitiesTestCase` - Encryption/decryption utilities
- `UserModelEncryptionTestCase` - User model with encryption
- `SignupFormEncryptionTestCase` - Signup with encrypted emails
- `LoginFormEncryptionTestCase` - Login with encrypted emails
- `LoginViewEncryptionTestCase` - Login view integration
- `SignupViewEncryptionTestCase` - Signup view integration

### Running Encryption Tests

```bash
# All encryption tests (20 tests)
python manage.py test accounts.test_encryption

# Specific test class
python manage.py test accounts.test_encryption.EncryptionUtilitiesTestCase
```

**What it tests:**
- Key generation (32 bytes, base64-encoded)
- Email encryption/decryption roundtrip
- SHA-256 digest generation
- Case insensitivity (TEST@EXAMPLE.COM == test@example.com)
- Unique nonces (same email → different ciphertext)
- Error handling (missing key, corrupted data)
- User model integration (auto-encrypt on save)
- Form validation (duplicate email detection via digest)
- Login functionality (find user by encrypted email)

**Expected output:**
```
Found 37 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.....................................
----------------------------------------------------------------------
Ran 37 tests in 2.571s

OK
Destroying test database for alias 'default'...
```

### Test Database

**Important:** Tests use a **separate test database**.

**Lifecycle:**
1. `python manage.py test` starts
2. Test database created (`:memory:` or `test_db.sqlite3`)
3. Migrations applied automatically
4. Tests run (each creates its own data)
5. Test database deleted automatically

**Benefits:**
- Tests don't affect development database
- Tests start with clean slate
- No login or existing users required
- Each test is isolated and independent

---

## 2. Manual Testing Procedures

### Pre-Test Setup

**1. Ensure clean state:**
```bash
# Delete existing database (optional)
rm db.sqlite3

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver
```

**2. Open browser tools:**
- Chrome DevTools (F12)
- Network tab (monitor requests)
- Console tab (watch for errors)

### Feature Testing Checklist

#### 2.1 Signup Feature

**Test Case 1: Valid Registration**
- [ ] Navigate to `/accounts/signup/`
- [ ] Enter valid data:
  - Username: `testuser1`
  - Email: `test1@example.com`
  - Password: `SecurePass123!`
  - Confirm: `SecurePass123!`
- [ ] Click "Sign Up"
- [ ] **Expected:** Redirected to `/menu/`, logged in, navbar shows "testuser1"

**Test Case 2: Duplicate Username**
- [ ] Try registering with `testuser1` again
- [ ] **Expected:** Error "That username is already taken."

**Test Case 3: Duplicate Email**
- [ ] Try registering with `test1@example.com` (different username)
- [ ] **Expected:** Error "That email is already registered."
- [ ] Works with different case: `TEST1@example.com`

**Test Case 4: Password Strength**
- [ ] `short` → "at least 12 characters"
- [ ] `password123` → "too common"
- [ ] `longpassword` → "uppercase letter", "special character"
- [ ] `12345678901234` → "entirely numeric"

**Test Case 5: Password Mismatch**
- [ ] Password: `SecurePass123!`, Confirm: `DifferentPass123!`
- [ ] **Expected:** Error "Passwords do not match."

**Test Case 6: Profile Auto-Creation**
- [ ] Register new user
- [ ] Visit `/accounts/profile/`
- [ ] **Expected:** Profile exists with display_name = username

#### 2.2 Login Feature

**Test Case 1: Valid Login (Username)**
- [ ] Navigate to `/accounts/login/`
- [ ] Identifier: `testuser1`, Password: `SecurePass123!`
- [ ] **Expected:** Redirected to `/menu/`, logged in

**Test Case 2: Valid Login (Email)**
- [ ] Identifier: `test1@example.com`, Password: `SecurePass123!`
- [ ] **Expected:** Login succeeds (same as username)

**Test Case 3: Wrong Credentials**
- [ ] Identifier: `nonexistent`, Password: `anypassword`
- [ ] **Expected:** Error "Invalid username or password."

**Test Case 4: Case Insensitivity**
- [ ] Identifier: `TESTUSER1` or `TEST1@EXAMPLE.COM`
- [ ] **Expected:** Login succeeds

**Test Case 5: Session Persistence**
- [ ] Log in successfully
- [ ] Visit `/accounts/profile/`
- [ ] Refresh page
- [ ] **Expected:** Still logged in (no redirect)

**Test Case 6: Logout**
- [ ] Click "Log Out" in navbar
- [ ] **Expected:** Redirected to home, navbar shows "Log In"
- [ ] Try accessing `/accounts/profile/`
- [ ] **Expected:** Redirected to login page

**Test Case 7: CSRF Protection**
- [ ] Open DevTools → Network tab
- [ ] Submit login form
- [ ] Check request payload
- [ ] **Expected:** Contains `csrfmiddlewaretoken`

#### 2.3 Profile Feature

**Test Case 1: View Profile**
- [ ] Log in and visit `/accounts/profile/`
- [ ] **Expected:** Shows username, email, join date, last login

**Test Case 2: Update Profile Info**
- [ ] Update: Display Name, Phone, Favorite Drink, Bio
- [ ] Click "Save Profile"
- [ ] **Expected:** Success message, data saved
- [ ] Refresh page → data still shown

**Test Case 3: Change Username**
- [ ] New Username: `newusername`, Password: `SecurePass123!`
- [ ] Click "Change Username"
- [ ] **Expected:** Success message, navbar updates
- [ ] Log out and log in with new username → succeeds

**Test Case 4: Change Password**
- [ ] Current: `SecurePass123!`, New: `NewSecurePass456!`
- [ ] Click "Change Password"
- [ ] **Expected:** Success message, still logged in
- [ ] Log out and log in with new password → succeeds

**Test Case 5: Delete Account**
- [ ] Click "Delete Account", enter password, confirm
- [ ] **Expected:** Redirected to home, logged out
- [ ] Try logging in → "Invalid username or password."

#### 2.4 Menu Feature

**Test Case 1: View Menu**
- [ ] Log in and visit `/menu/`
- [ ] **Expected:** Categories and items displayed
- [ ] Images load, prices shown in ₱

### Browser Testing

**Test on 2 browsers:**
- [ ] Chrome (latest)
- [ ] Firefox (latest)

**For each browser:**
- [ ] Signup, login, profile, menu work correctly
- [ ] CSS renders correctly
- [ ] No JavaScript errors in console

### Responsive Testing

**Test on 2 screen sizes:**
- [ ] Desktop (1920×1080)
- [ ] Mobile (375×667)

**Tools:** Chrome DevTools → Device Toolbar (Ctrl+Shift+M)

**For each size:**
- [ ] Navigation menu works
- [ ] Forms are usable
- [ ] Text is readable
- [ ] No horizontal scrolling

---

## 3. Security Testing & Verification

### 3.1 Manual Security Tests

**Test 1: SQL Injection**
```
Username: admin' OR '1'='1
Password: anything
Expected: Login fails, no SQL execution
```

**Test 2: XSS Attack**
```
Profile Bio: <script>alert('XSS')</script>
Expected: Displayed as text, not executed
```

**Test 3: CSRF Attack**
```
1. Log in to Brews & Chews
2. Open new tab, paste:
   <form action="http://127.0.0.1:8000/accounts/profile/delete/" method="post">
       <input type="hidden" name="password" value="SecurePass123!">
   </form>
   <script>document.forms[0].submit()</script>
3. Expected: 403 Forbidden (CSRF token missing)
```

**Test 4: Session Hijacking**
```
1. Log in, copy session cookie (DevTools → Application → Cookies)
2. Log out
3. Manually add cookie back
4. Refresh page
Expected: Not logged in (session destroyed on logout)
```

**Test 5: Username Enumeration Prevention**
```
1. Login with nonexistent username → "Invalid username or password."
2. Login with existing username, wrong password → "Invalid username or password."
Expected: Same error message (prevents enumeration)
```

### 3.2 Verifying Email Encryption

**Prerequisites:** Database migrated, at least one user exists

**View encrypted email:**
```bash
python manage.py shell
```
```python
from accounts.models import User

user = User.objects.first()

# View encrypted (binary data)
print(f"Encrypted (hex): {user.encrypted_email.hex()}")
print(f"Length: {len(user.encrypted_email)} bytes")

# View decrypted (plaintext)
print(f"Decrypted: {user.email_decrypted}")

# View digest (for lookups)
print(f"Digest: {user.email_digest}")
```

**Expected output:**
```
Encrypted (hex): 123456789abcdef0123456789abcdef0...
Length: 45 bytes
Decrypted: testuser@example.com
Digest: a3f8b2c9d1e4f5a6b7c8d9e0f1a2b3c4...
```

**Test encryption works:**
```python
from accounts.encryption import encrypt_email, decrypt_email

# Test roundtrip
original = "test@example.com"
encrypted = encrypt_email(original)
decrypted = decrypt_email(encrypted)

print(f"Encryption works: {decrypted == original.lower()}")  # True

# Test unique nonces
enc1 = encrypt_email(original)
enc2 = encrypt_email(original)
print(f"Unique nonces: {enc1 != enc2}")  # True
```

**Run automated encryption tests:**
```bash
python manage.py test accounts.test_encryption
# Expected: Ran 20 tests in 1.234s - OK
```

### 3.3 Verifying Password Hashing

**View hashed password:**
```bash
python manage.py shell
```
```python
from accounts.models import User

user = User.objects.first()
print(f"Password hash: {user.password}")
```

**Expected output:**
```
Password hash: argon2$argon2id$v=19$m=102400,t=2,p=8$randomsalt$hash
```

**Understanding the hash:**
- `argon2` - Algorithm (memory-hard, GPU-resistant)
- `argon2id` - Variant (hybrid mode, best security)
- `v=19` - Argon2 version
- `m=102400` - Memory cost (102,400 KB ≈ 100 MB)
- `t=2` - Time cost (iterations)
- `p=8` - Parallelism (8 threads)

**Test password verification:**
```python
from accounts.models import User

user = User.objects.get(username='testuser')

# Test correct password
print(user.check_password('SecurePass123!'))  # True

# Test wrong password
print(user.check_password('WrongPassword'))  # False

# Verify Argon2
print(user.password.startswith('argon2'))  # True
```

**Test hash uniqueness:**
```python
from django.contrib.auth.hashers import make_password, check_password

password = "SamePassword123!"
hash1 = make_password(password)
hash2 = make_password(password)

# Different hashes (unique salt)
print(f"Different: {hash1 != hash2}")  # True

# But both verify correctly
print(f"Hash 1 valid: {check_password(password, hash1)}")  # True
print(f"Hash 2 valid: {check_password(password, hash2)}")  # True
```

### 3.4 Verifying Audit Logging

```bash
python manage.py shell
```
```python
from accounts.models import AuthenticationEvent

# View recent events
events = AuthenticationEvent.objects.all().order_by('-created_at')[:10]

for event in events:
    status = "✅" if event.successful else "❌"
    print(f"{status} {event.event_type} | {event.username_submitted or event.email_submitted} | {event.ip_address}")
```

### 3.5 Quick Reference Commands

**View encrypted email:**
```bash
python manage.py shell -c "from accounts.models import User; u=User.objects.first(); print(f'Encrypted: {u.encrypted_email.hex()[:40]}...\nDecrypted: {u.email_decrypted}')"
```

**View hashed password:**
```bash
python manage.py shell -c "from accounts.models import User; u=User.objects.first(); print(u.password)"
```

**Count users:**
```bash
python manage.py shell -c "from accounts.models import User; print(f'Total users: {User.objects.count()}')"
```

**Test encryption:**
```bash
python manage.py shell -c "from accounts.encryption import test_encryption_roundtrip; test_encryption_roundtrip()"
```

### 3.6 Security Checklist

- [ ] Passwords hashed with Argon2
- [ ] Emails encrypted with AES-256-GCM
- [ ] CSRF protection enabled
- [ ] Session cookies HttpOnly
- [ ] Generic error messages (no info leak)
- [ ] Input validation on all forms
- [ ] SQL injection prevented (ORM)
- [ ] XSS prevented (template auto-escape)

---

## 4. Debugging & Troubleshooting

### Common Issues & Solutions

#### Issue 1: "No such table" errors

**Symptom:** `django.db.utils.OperationalError: no such table: accounts_user`

**Solution:**
```bash
python manage.py migrate
```

**Verify:**
```bash
python manage.py showmigrations
# All migrations should have [X]
```

#### Issue 2: Email encryption errors

**Symptom:** `MissingEncryptionKeyError` or `DecryptionFailedError`

**Solution:**
```bash
# Generate new key
python -c "from accounts.encryption import generate_encryption_key; print(generate_encryption_key())"

# Add to .env file
echo "ACCOUNT_EMAIL_ENCRYPTION_KEY=generated_key_here" >> .env

# Restart server
```

#### Issue 3: CSRF verification failed

**Symptom:** `403 Forbidden: CSRF verification failed`

**Solution:**
- Ensure `{% csrf_token %}` in all POST forms
- Check CSRF middleware enabled in settings.py
- Clear browser cookies and retry

#### Issue 4: Static files not loading

**Symptom:** CSS/JavaScript not applied, 404 errors

**Solution (development):**
```python
# Ensure in settings.py:
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
```

Hard refresh browser (Ctrl+F5)

#### Issue 5: Import errors

**Symptom:** `ModuleNotFoundError: No module named 'django'`

**Solution:**
```bash
# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Verify
python -c "import django; print(django.get_version())"
```

#### Issue 6: Port already in use

**Symptom:** `Error: That port is already in use.`

**Solution:**
```bash
# Use different port
python manage.py runserver 8080

# Or kill existing process (macOS/Linux)
lsof -i :8000
kill <pid>
```

#### Issue 7: Database locked

**Symptom:** `database is locked` (SQLite only)

**Solution:**
- Close other Django shells
- Restart server
- If persists: `rm db.sqlite3 && python manage.py migrate`

---

## 5. Pre-Presentation Checklist

### Quick Smoke Test (5 minutes)

- [ ] Server starts without errors
- [ ] Home page loads
- [ ] Can signup new user
- [ ] Can login with new user
- [ ] Can view profile
- [ ] Can view menu
- [ ] Can add items to cart
- [ ] Can view cart
- [ ] Can proceed to checkout
- [ ] Can logout

### Full Testing Checklist (30 minutes)

**Automated Tests:**
- [ ] All tests passing: `python manage.py test`
- [ ] No warnings or errors

**Feature Completeness:**
- [ ] User signup works (creates account, encrypts email)
- [ ] User login works (username and email)
- [ ] Profile view/edit works
- [ ] Username change works (requires password)
- [ ] Password change works (updates session)
- [ ] Account deletion works
- [ ] Logout works
- [ ] Menu displays items with images and prices
- [ ] Add to cart works (quantity updates)
- [ ] Cart displays items with totals
- [ ] Cart update/remove works
- [ ] Checkout form pre-fills contact info
- [ ] PayMongo payment redirect works
- [ ] Payment success page shows order details
- [ ] Order history shows completed orders

**Security Verification:**
- [ ] Passwords hashed with Argon2
- [ ] Emails encrypted with AES-256-GCM
- [ ] CSRF protection enabled
- [ ] Session cookies HttpOnly
- [ ] No console errors in browser DevTools

**Database:**
- [ ] Migrations applied: `python manage.py showmigrations`
- [ ] Email encryption working
- [ ] Profile auto-creation working

**Code Quality:**
- [ ] No Python warnings when running server
- [ ] No hardcoded secrets (check .env usage)
- [ ] README.md updated

### Demo Preparation

**Create demo account:**
```python
python manage.py shell

from accounts.models import User

# Create demo user
demo = User.objects.create_user(
    username='demo',
    email='demo@brewschews.com',
    password='DemoPass123!'
)

# Add profile data
demo.profile.display_name = 'Demo User'
demo.profile.phone_number = '+1234567890'
demo.profile.favorite_drink = 'Cappuccino'
demo.profile.bio = 'Coffee enthusiast'
demo.profile.save()
```

**Test demo flow:**
1. [ ] Show signup (live registration)
2. [ ] Show login (with demo account)
3. [ ] Show profile (with filled data)
4. [ ] Show menu browsing
5. [ ] Show add to cart (click "Add to Cart")
6. [ ] Show cart page (view items, totals)
7. [ ] Show checkout (fill contact info)
8. [ ] Show payment (PayMongo test card)
9. [ ] Show order history (completed order)
10. [ ] Show email encryption (Django shell)
11. [ ] Show audit logs (Django shell)

**Backup before presentation:**
```bash
# Backup database
cp db.sqlite3 db.sqlite3.backup

# Backup .env file
cp .env .env.backup
```

---

## Summary

### Test Execution

**Automated (2 minutes):**
```bash
python manage.py test
```
Expected: 37 tests pass, no warnings

**Manual (30 minutes):**
- Signup (6 test cases)
- Login (7 test cases)
- Profile (5 test cases)
- Menu (3 test cases)
- Cart (4 test cases)
- Checkout/Payment (5 test cases)
- Security (5 tests)
- Browser (2 browsers)
- Responsive (2 sizes)

**Security Verification:**
- View encrypted emails (Django shell)
- Verify password hashing (Argon2)
- Test encryption roundtrip
- Check audit logging

### All Features Verified

**Implemented & Tested:**
- User signup with email encryption
- Login (username/email, case-insensitive)
- Profile management (view/edit/delete)
- Password strength validation
- Argon2 password hashing
- AES-256-GCM email encryption
- Audit logging
- CSRF protection
- Session management
- Menu browsing with categories
- Shopping cart (add/update/remove items)
- Checkout with contact form
- PayMongo payment integration (Card, GCash, PayMaya)
- Order history with status tracking
