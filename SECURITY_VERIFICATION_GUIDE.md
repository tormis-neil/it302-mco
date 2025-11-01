# Security Verification Guide
## How to View and Verify Encrypted Data, Hashed Passwords, and Security Implementation

This guide answers common questions about verifying the security implementation in Brews & Chews.

---

## Table of Contents
1. [How to View Encrypted Emails](#1-how-to-view-encrypted-emails)
2. [How to View Hashed Passwords](#2-how-to-view-hashed-passwords)
3. [How to View Stored Accounts](#3-how-to-view-stored-accounts)
4. [How to Confirm Encryption Works](#4-how-to-confirm-encryption-works)
5. [How to Confirm Password Hashing Works](#5-how-to-confirm-password-hashing-works)
6. [Running Tests Without Logged-In Users](#6-running-tests-without-logged-in-users)
7. [Complete Verification Workflow](#7-complete-verification-workflow)

---

## 1. How to View Encrypted Emails

### Method 1: Using Django Shell (Recommended)

```bash
python manage.py shell
```

```python
from accounts.models import User

# Get a user
user = User.objects.first()  # or User.objects.get(username='testuser')

# View encrypted email (binary data)
print("Encrypted email (binary):", user.encrypted_email)
print("Encrypted email (hex):", user.encrypted_email.hex())
print("Encrypted email (length):", len(user.encrypted_email), "bytes")

# View decrypted email
print("Decrypted email:", user.email_decrypted)

# View email digest (used for lookups)
print("Email digest (SHA-256):", user.email_digest)

# Exit
exit()
```

**Expected Output:**
```
Encrypted email (binary): b'\x12\x34\x56...'
Encrypted email (hex): 123456789abcdef0123456789abcdef0...
Encrypted email (length): 45 bytes
Decrypted email: testuser@example.com
Email digest (SHA-256): a3f8b2c9d1e4f5a6b7c8d9e0f1a2b3c4...
```

### Method 2: Using SQLite Command Line

```bash
# Open database
sqlite3 db.sqlite3
```

```sql
-- View raw encrypted data
SELECT
    id,
    username,
    email,                          -- Legacy plaintext (empty on new users)
    HEX(encrypted_email) as encrypted_hex,
    email_digest,
    substr(password, 1, 50) as password_preview
FROM accounts_user
LIMIT 3;

-- Exit
.quit
```

### Method 3: Using Python Script

```bash
# View database directly
python -c "
import sqlite3
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()
cursor.execute('SELECT id, username, encrypted_email FROM accounts_user LIMIT 1')
user_id, username, encrypted = cursor.fetchone()
print(f'User: {username}')
print(f'Encrypted email (hex): {encrypted.hex()}')
print(f'Length: {len(encrypted)} bytes')
conn.close()
"
```

---

## 2. How to View Hashed Passwords

### Using Django Shell

```bash
python manage.py shell
```

```python
from accounts.models import User

# Get a user
user = User.objects.first()

# View hashed password
print("Password hash:", user.password)
print("Hash length:", len(user.password), "characters")

# Parse hash components
parts = user.password.split('$')
print("\nHash breakdown:")
print("  Algorithm:", parts[0])
print("  Variant:", parts[1])
print("  Version:", parts[2])
print("  Parameters:", parts[3])
print("  Salt:", parts[4][:20], "...")
print("  Hash:", parts[5][:20], "...")

# Exit
exit()
```

**Expected Output:**
```
Password hash: argon2$argon2id$v=19$m=102400,t=2,p=8$randomsalthere$hashvaluehere
Hash length: 97 characters

Hash breakdown:
  Algorithm: argon2
  Variant: argon2id
  Version: v=19
  Parameters: m=102400,t=2,p=8
  Salt: randomsalthere ...
  Hash: hashvaluehere ...
```

### Understanding the Hash

- **argon2**: Algorithm (memory-hard, GPU-resistant)
- **argon2id**: Variant (hybrid mode, best security)
- **v=19**: Argon2 version
- **m=102400**: Memory cost (102,400 KB ≈ 100 MB)
- **t=2**: Time cost (iterations)
- **p=8**: Parallelism (8 threads)
- **Salt**: Random 16-byte salt (unique per password)
- **Hash**: The actual hashed password

### Using SQLite

```bash
sqlite3 db.sqlite3
```

```sql
SELECT
    username,
    substr(password, 1, 60) as password_hash_preview,
    length(password) as hash_length
FROM accounts_user;

.quit
```

---

## 3. How to View Stored Accounts

### View All Accounts (Django Shell)

```bash
python manage.py shell
```

```python
from accounts.models import User

# View all users
users = User.objects.all()

print(f"Total users: {users.count()}\n")

for user in users:
    print(f"{'='*60}")
    print(f"ID: {user.id}")
    print(f"Username: {user.username}")
    print(f"Email (decrypted): {user.email_decrypted}")
    print(f"Email Digest: {user.email_digest}")
    print(f"Password Hash: {user.password[:50]}...")
    print(f"Is Superuser: {user.is_superuser}")
    print(f"Date Joined: {user.date_joined}")
    print(f"Last Login: {user.last_login}")
    print(f"Profile: {user.profile.display_name}")
    print()

exit()
```

### View Specific Account

```python
from accounts.models import User

# Get user by username
user = User.objects.get(username='testuser')

# Or by email (uses encrypted lookup)
user = User.find_by_email('test@example.com')

# Print all details
print(f"User ID: {user.id}")
print(f"Username: {user.username}")
print(f"Email: {user.email_decrypted}")
print(f"Encrypted Email (hex): {user.encrypted_email.hex()}")
print(f"Email Digest: {user.email_digest}")
print(f"Password Hash: {user.password}")
print(f"Joined: {user.date_joined}")

# View profile
print(f"\nProfile:")
print(f"  Display Name: {user.profile.display_name}")
print(f"  Phone: {user.profile.phone_number}")
print(f"  Favorite Drink: {user.profile.favorite_drink}")
print(f"  Bio: {user.profile.bio}")

exit()
```

### View Database Tables

```bash
sqlite3 db.sqlite3
```

```sql
-- List all tables
.tables

-- View accounts_user table structure
.schema accounts_user

-- Count users
SELECT COUNT(*) as total_users FROM accounts_user;

-- View recent users
SELECT id, username, email_digest, date_joined
FROM accounts_user
ORDER BY date_joined DESC
LIMIT 5;

-- View authentication events (audit log)
SELECT event_type, username_submitted, ip_address, successful, created_at
FROM accounts_authenticationevent
ORDER BY created_at DESC
LIMIT 10;

.quit
```

---

## 4. How to Confirm Encryption Works

### Test 1: Roundtrip Encryption Test

```bash
python manage.py shell
```

```python
from accounts.encryption import encrypt_email, decrypt_email, generate_email_digest

# Test email
test_email = "verification@test.com"

# Encrypt
encrypted = encrypt_email(test_email)
print(f"Original: {test_email}")
print(f"Encrypted (hex): {encrypted.hex()}")
print(f"Encrypted length: {len(encrypted)} bytes")

# Decrypt
decrypted = decrypt_email(encrypted)
print(f"Decrypted: {decrypted}")
print(f"Match: {decrypted == test_email.lower()}")

# Generate digest
digest = generate_email_digest(test_email)
print(f"Digest: {digest}")

exit()
```

### Test 2: Unique Nonce Verification

```python
from accounts.encryption import encrypt_email

email = "same@example.com"

# Encrypt same email twice
encrypted1 = encrypt_email(email)
encrypted2 = encrypt_email(email)

print(f"Email: {email}")
print(f"Encrypted 1: {encrypted1.hex()}")
print(f"Encrypted 2: {encrypted2.hex()}")
print(f"Different ciphertext: {encrypted1 != encrypted2}")  # Should be True
print("\nThis proves each encryption uses a unique nonce (Initialization Vector)")

exit()
```

### Test 3: User Creation with Encryption

```python
from accounts.models import User

# Create test user
user = User.objects.create_user(
    username='encryption_test',
    email='encryption_test@example.com',
    password='TestPassword123!'
)

# Verify encryption
print(f"User created: {user.username}")
print(f"Email encrypted: {user.encrypted_email is not None}")
print(f"Email digest generated: {user.email_digest is not None}")
print(f"Can decrypt: {user.email_decrypted == 'encryption_test@example.com'}")

# Verify lookup works
found = User.find_by_email('encryption_test@example.com')
print(f"Find by email works: {found == user}")

# Cleanup (optional)
user.delete()
exit()
```

### Test 4: Run Automated Encryption Tests

```bash
python manage.py test accounts.test_encryption -v 2
```

This runs 20+ tests covering:
- Key generation
- Encryption/decryption roundtrip
- Digest generation
- Case insensitivity
- Nonce uniqueness
- Error handling
- User model integration
- Form validation
- Login functionality

---

## 5. How to Confirm Password Hashing Works

### Test 1: Verify Hash Algorithm

```bash
python manage.py shell
```

```python
from accounts.models import User

user = User.objects.first()

# Check hash format
print(f"Password hash: {user.password}")
print(f"Uses Argon2: {user.password.startswith('argon2')}")

# Extract parameters
if user.password.startswith('argon2'):
    parts = user.password.split('$')
    params = parts[3]
    print(f"Parameters: {params}")

    # Parse memory cost
    memory = params.split(',')[0].split('=')[1]
    print(f"Memory cost: {int(memory):,} KB ≈ {int(memory)/1024:.1f} MB")

exit()
```

### Test 2: Verify Password Check Works

```python
from accounts.models import User

user = User.objects.get(username='testuser')

# Test correct password
correct = user.check_password('TestPassword123!')
print(f"Correct password verified: {correct}")

# Test wrong password
wrong = user.check_password('WrongPassword')
print(f"Wrong password rejected: {not wrong}")

exit()
```

### Test 3: Verify Hash Uniqueness

```python
from django.contrib.auth.hashers import make_password

# Hash same password twice
password = "SamePassword123!"
hash1 = make_password(password)
hash2 = make_password(password)

print(f"Hash 1: {hash1}")
print(f"Hash 2: {hash2}")
print(f"Different hashes (unique salt): {hash1 != hash2}")

# But both verify correctly
from django.contrib.auth.hashers import check_password
print(f"Hash 1 verifies: {check_password(password, hash1)}")
print(f"Hash 2 verifies: {check_password(password, hash2)}")

exit()
```

### Test 4: Measure Hash Time (Performance)

```python
import time
from django.contrib.auth.hashers import make_password

password = "TestPassword123!"

start = time.time()
hashed = make_password(password)
end = time.time()

print(f"Hashing time: {end - start:.3f} seconds")
print(f"Hash: {hashed[:60]}...")
print("\nIntentionally slow (prevents brute force attacks)")

exit()
```

### Test 5: Run Password Tests

```bash
python manage.py test accounts.tests.SignupViewTests.test_password_hashed_with_argon2 -v 2
```

---

## 6. Running Tests Without Logged-In Users

### Important: Tests Use Separate Database

**Django tests automatically create a clean test database** and do NOT require any logged-in users or existing data.

```bash
# Run all tests (uses test database, not db.sqlite3)
python manage.py test

# Run accounts tests
python manage.py test accounts

# Run encryption tests
python manage.py test accounts.test_encryption
```

**What happens when tests run:**

1. **Test database created** (`test_db.sqlite3` or in-memory)
2. **Migrations applied** (creates tables)
3. **Each test creates its own data** (isolated)
4. **Tests run** (create users, test features, check results)
5. **Test database destroyed** (clean up)

**You do NOT need:**
- Any existing user accounts
- To be logged in
- To run the development server
- To have data in db.sqlite3

### Example Test Workflow

```python
# From accounts/tests.py - SignupViewTests

class SignupViewTests(TestCase):
    def test_password_hashed_with_argon2(self):
        # Test creates its own user (no pre-existing data needed)
        response = self.client.post('/accounts/signup/', {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPassword123!',
            'confirm_password': 'TestPassword123!',
        })

        # Verify user was created
        user = User.objects.get(username='testuser')

        # Check password is hashed with Argon2
        self.assertTrue(user.password.startswith('argon2'))

        # User is automatically cleaned up after test
```

### Running Specific Test Groups

```bash
# All signup tests (creates test users automatically)
python manage.py test accounts.tests.SignupViewTests

# All login tests (creates test users automatically)
python manage.py test accounts.tests.LoginViewTests

# All profile tests (creates test users automatically)
python manage.py test accounts.tests.ProfileViewTests

# All encryption tests (creates test users automatically)
python manage.py test accounts.test_encryption
```

**Every test is independent and creates its own test data!**

---

## 7. Complete Verification Workflow

### Step-by-Step Security Verification

**1. Setup Environment**

```bash
# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate.bat  # Windows

# Ensure database exists
python manage.py migrate
```

**2. Create Test Account**

```bash
python manage.py shell
```

```python
from accounts.models import User

# Create test user
user = User.objects.create_user(
    username='verify_user',
    email='verify@test.com',
    password='VerifyPassword123!'
)

print(f"✅ User created: {user.username}")
exit()
```

**3. Verify Email Encryption**

```bash
python manage.py shell
```

```python
from accounts.models import User

user = User.objects.get(username='verify_user')

# Check encrypted
assert user.encrypted_email is not None, "❌ Email not encrypted!"
print(f"✅ Email encrypted: {user.encrypted_email.hex()[:40]}...")

# Check digest
assert user.email_digest is not None, "❌ Digest not generated!"
print(f"✅ Email digest: {user.email_digest}")

# Check decryption
assert user.email_decrypted == 'verify@test.com', "❌ Decryption failed!"
print(f"✅ Decrypted email: {user.email_decrypted}")

# Check lookup
found = User.find_by_email('verify@test.com')
assert found == user, "❌ Email lookup failed!"
print(f"✅ Find by email works")

# Check case-insensitive
found_upper = User.find_by_email('VERIFY@TEST.COM')
assert found_upper == user, "❌ Case-insensitive lookup failed!"
print(f"✅ Case-insensitive lookup works")

print("\n🎉 All email encryption checks passed!")
exit()
```

**4. Verify Password Hashing**

```bash
python manage.py shell
```

```python
from accounts.models import User

user = User.objects.get(username='verify_user')

# Check Argon2
assert user.password.startswith('argon2'), "❌ Not using Argon2!"
print(f"✅ Using Argon2: {user.password[:50]}...")

# Check password verification
assert user.check_password('VerifyPassword123!'), "❌ Correct password failed!"
print(f"✅ Correct password verifies")

assert not user.check_password('WrongPassword'), "❌ Wrong password accepted!"
print(f"✅ Wrong password rejected")

# Check hash parameters
parts = user.password.split('$')
params = parts[3]
print(f"✅ Hash parameters: {params}")

print("\n🎉 All password hashing checks passed!")
exit()
```

**5. Run Automated Tests**

```bash
# Run all tests
python manage.py test

# Run encryption tests
python manage.py test accounts.test_encryption

# Run auth tests
python manage.py test accounts.tests
```

**Expected:**
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

**6. Verify Audit Logging**

```bash
python manage.py shell
```

```python
from accounts.models import AuthenticationEvent

# View recent events
events = AuthenticationEvent.objects.all().order_by('-created_at')[:5]

print(f"Recent authentication events:\n")
for event in events:
    status = "✅ SUCCESS" if event.successful else "❌ FAILED"
    print(f"{status} | {event.event_type:8} | {event.username_submitted or event.email_submitted:20} | {event.created_at}")

exit()
```

**7. Test Login Functionality**

```bash
# Start server
python manage.py runserver
```

Then in browser:
1. Go to `http://127.0.0.1:8000/accounts/login/`
2. Login with `verify_user` / `VerifyPassword123!`
3. Should redirect to menu and show username in nav
4. Go to `http://127.0.0.1:8000/accounts/profile/`
5. Should show decrypted email: `verify@test.com`

**8. Final Verification Summary**

```bash
python manage.py shell
```

```python
from accounts.models import User, AuthenticationEvent
from accounts.encryption import test_encryption_roundtrip

print("="*60)
print("SECURITY VERIFICATION SUMMARY")
print("="*60)

# Count users
user_count = User.objects.count()
print(f"✅ Total users: {user_count}")

# Check encryption
user = User.objects.first()
if user:
    has_encryption = user.encrypted_email is not None
    can_decrypt = user.email_decrypted is not None
    print(f"✅ Email encryption active: {has_encryption}")
    print(f"✅ Email decryption works: {can_decrypt}")
    print(f"✅ Password hashing: Argon2")

# Check audit logging
event_count = AuthenticationEvent.objects.count()
print(f"✅ Authentication events logged: {event_count}")

# Test encryption roundtrip
try:
    test_encryption_roundtrip()
    print(f"✅ Encryption roundtrip: PASSED")
except Exception as e:
    print(f"❌ Encryption roundtrip: FAILED - {e}")

print("\n🎉 Security implementation verified!")
print("="*60)
exit()
```

---

## Quick Reference Commands

### View Encrypted Email
```bash
python manage.py shell -c "from accounts.models import User; u=User.objects.first(); print(u.encrypted_email.hex())"
```

### View Hashed Password
```bash
python manage.py shell -c "from accounts.models import User; u=User.objects.first(); print(u.password)"
```

### Count Users
```bash
python manage.py shell -c "from accounts.models import User; print(f'Total users: {User.objects.count()}')"
```

### Test Encryption
```bash
python manage.py shell -c "from accounts.encryption import test_encryption_roundtrip; test_encryption_roundtrip()"
```

### Run All Tests
```bash
python manage.py test accounts
```

---

## Summary

**Encrypted Emails:**
- Stored as binary data (BinaryField)
- Encrypted with AES-256-GCM
- Decrypted via `user.email_decrypted` property
- Lookup via SHA-256 digest (indexed, unique)

**Hashed Passwords:**
- Stored as string (format: `argon2$variant$version$params$salt$hash`)
- Hashed with Argon2id (102,400 iterations, 100 MB memory)
- Cannot be reversed (one-way hash)
- Verified with `user.check_password(password)`

**Testing:**
- Uses separate test database
- No login required
- Each test creates its own data
- All tests pass independently

**All security features work correctly and can be verified!** ✅
