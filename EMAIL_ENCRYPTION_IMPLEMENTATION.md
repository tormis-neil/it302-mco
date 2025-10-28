# Email Encryption Implementation (MCO 1)

## Overview

This document describes the AES-256-GCM email encryption implementation for the Django café ordering system, created as part of the MCO 1 academic project to demonstrate data security through encryption techniques.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Implementation Details](#implementation-details)
3. [Security Features](#security-features)
4. [Usage Guide](#usage-guide)
5. [Testing](#testing)
6. [Troubleshooting](#troubleshooting)
7. [Future Improvements](#future-improvements)

---

## Architecture Overview

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                      Django Application                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │    Views     │───▶│    Forms     │───▶│  User Model  │  │
│  │              │    │              │    │              │  │
│  │ - Signup     │    │ - SignupForm │    │ - save()     │  │
│  │ - Login      │    │ - LoginForm  │    │ - find_by_  │  │
│  │              │    │              │    │   email()    │  │
│  └──────────────┘    └──────────────┘    └──────┬───────┘  │
│                                                   │          │
│                                                   ▼          │
│                                          ┌──────────────┐   │
│                                          │  Encryption  │   │
│                                          │   Module     │   │
│                                          │              │   │
│                                          │ - encrypt_   │   │
│                                          │   email()    │   │
│                                          │ - decrypt_   │   │
│                                          │   email()    │   │
│                                          │ - generate_  │   │
│                                          │   digest()   │   │
│                                          └──────┬───────┘   │
│                                                 │           │
└─────────────────────────────────────────────────┼───────────┘
                                                  │
                                                  ▼
                                    ┌──────────────────────┐
                                    │   Database (SQLite)  │
                                    ├──────────────────────┤
                                    │ User Table:          │
                                    │ - email (plaintext)  │
                                    │ - encrypted_email    │
                                    │   (BinaryField)      │
                                    │ - email_digest       │
                                    │   (CharField, index) │
                                    └──────────────────────┘
```

### Data Flow

#### Signup Flow
```
1. User submits email → Form validates
2. Form checks uniqueness via email_digest
3. User.objects.create_user(email=...)
4. User.save() → _encrypt_and_store_email()
5. encrypt_email() → AES-256-GCM encryption
6. generate_email_digest() → SHA-256 hash
7. Save encrypted_email + email_digest to DB
```

#### Login Flow
```
1. User submits email → Form validates
2. LoginForm.find_user() → generate_email_digest()
3. Query: User.objects.filter(email_digest=digest)
4. Found user → check password
5. Login successful
```

#### Email Access Flow
```
1. user.email_decrypted → Check cache
2. If not cached → decrypt_email(encrypted_email)
3. Cache result in _email_cache
4. Return decrypted email
```

---

## Implementation Details

### 1. Encryption Module (`accounts/encryption.py`)

#### Key Functions

**`encrypt_email(email: str) -> bytes`**
- Normalizes email to lowercase
- Generates unique 12-byte nonce (IV)
- Encrypts using AES-256-GCM
- Returns: `[nonce (12 bytes)][ciphertext + auth_tag]`

**`decrypt_email(encrypted_data: bytes) -> str`**
- Extracts nonce from first 12 bytes
- Extracts ciphertext from remaining bytes
- Decrypts using AES-256-GCM
- Verifies authentication tag
- Returns plaintext email

**`generate_email_digest(email: str) -> str`**
- Normalizes email to lowercase
- Computes SHA-256 hash
- Returns 64-character hex string

**`generate_encryption_key() -> str`**
- Generates 32 random bytes
- Encodes as base64
- Returns key suitable for environment variable

#### Error Handling

- `MissingEncryptionKeyError`: Key not configured or invalid
- `EmailEncryptionError`: Encryption failed
- `DecryptionFailedError`: Decryption failed (wrong key, corrupted data)

### 2. User Model Changes (`accounts/models.py`)

#### New Fields

```python
# Encrypted email storage
encrypted_email = models.BinaryField(blank=True, null=True)

# Email digest for lookups and uniqueness
email_digest = models.CharField(
    max_length=64,
    unique=True,
    blank=True,
    null=True,
    db_index=True
)

# In-memory cache
_email_cache: Optional[str] = None
```

#### Methods

**`_encrypt_and_store_email(plaintext_email: str)`**
- Called automatically by save()
- Encrypts email → encrypted_email
- Generates digest → email_digest
- Caches plaintext → _email_cache

**`email_decrypted` (property)**
- Returns cached email if available
- Otherwise decrypts encrypted_email
- Falls back to plaintext email field
- Caches result for future access

**`find_by_email(email: str)` (static method)**
- Generates digest of search email
- Queries User.objects.get(email_digest=digest)
- Returns matching user

**`save(*args, **kwargs)` (overridden)**
- Checks if email field has value
- Calls _encrypt_and_store_email()
- Calls parent save()

### 3. Form Updates (`accounts/forms.py`)

#### SignupForm

**`clean_email()` (modified)**
```python
email_digest = generate_email_digest(email)
if User.objects.filter(email_digest=email_digest).exists():
    raise ValidationError("That email is already registered.")
```

#### LoginForm

**`find_user()` (modified)**
```python
if "@" in identifier:
    email_digest = generate_email_digest(identifier)
    user = User.objects.filter(email_digest=email_digest).first()
else:
    user = User.objects.filter(username__iexact=identifier).first()
```

### 4. Database Migrations

#### Migration 0002: Add Fields
```python
operations = [
    migrations.AddField(
        model_name='user',
        name='encrypted_email',
        field=models.BinaryField(blank=True, null=True),
    ),
    migrations.AddField(
        model_name='user',
        name='email_digest',
        field=models.CharField(
            max_length=64,
            unique=True,
            blank=True,
            null=True,
            db_index=True
        ),
    ),
    migrations.AlterField(
        model_name='user',
        name='email',
        field=models.EmailField(unique=False, blank=True),
    ),
]
```

#### Migration 0003: Encrypt Existing Data
```python
def encrypt_existing_emails(apps, schema_editor):
    User = apps.get_model("accounts", "User")

    for user in User.objects.all():
        if user.email:
            user.encrypted_email = encrypt_email(user.email)
            user.email_digest = generate_email_digest(user.email)
            user.save(update_fields=['encrypted_email', 'email_digest'])
```

### 5. Settings Configuration (`brewschews/settings.py`)

```python
# Get encryption key from environment
ACCOUNT_EMAIL_ENCRYPTION_KEY = os.environ.get(
    "ACCOUNT_EMAIL_ENCRYPTION_KEY",
    _derive_default_account_key(SECRET_KEY)
)

# Validate key format
_key_bytes = base64.b64decode(ACCOUNT_EMAIL_ENCRYPTION_KEY)
if len(_key_bytes) != 32:
    raise ImproperlyConfigured("Key must be 32 bytes")

# Warn if using derived key in development
if not os.environ.get("ACCOUNT_EMAIL_ENCRYPTION_KEY"):
    if DEBUG:
        print("⚠️  WARNING: Using derived encryption key")
    else:
        raise ImproperlyConfigured("Set ACCOUNT_EMAIL_ENCRYPTION_KEY")
```

---

## Security Features

### Encryption Algorithm: AES-256-GCM

**Why AES-256-GCM?**
- **AES-256**: Industry-standard symmetric encryption with 256-bit keys
- **GCM mode**: Provides both confidentiality AND authenticity
- **Authentication tag**: Prevents tampering with encrypted data
- **NIST approved**: Widely trusted and supported

**Properties:**
- Each encryption uses unique nonce (12 bytes)
- Nonce stored with ciphertext (safe to store together)
- Authentication tag prevents modification attacks
- Fast encryption/decryption performance

### Email Digest: SHA-256

**Why SHA-256?**
- One-way hash function (cannot reverse to get email)
- Deterministic (same email → same digest)
- Fast for lookups (indexed in database)
- Collision-resistant (two emails won't have same digest)

**Use Cases:**
- Email uniqueness constraint
- Fast user lookup by email
- Case-insensitive matching

### Key Management

**Development:**
- Key stored in `.env` file
- Generated using `generate_encryption_key()`
- Base64-encoded for easy storage

**Production Recommendations:**
- Use environment variables
- Store key in secrets management service (AWS Secrets Manager, HashiCorp Vault)
- Different keys for dev/staging/prod
- Regular key rotation (requires re-encryption)
- Backup keys securely

**Key Requirements:**
- Must be 32 bytes (256 bits)
- Must be base64-encoded in settings
- Must be backed up (if lost, data cannot be decrypted)

---

## Usage Guide

### Setup

1. **Generate encryption key:**
```bash
python -c "from accounts.encryption import generate_encryption_key; print(generate_encryption_key())"
```

2. **Add to `.env` file:**
```bash
ACCOUNT_EMAIL_ENCRYPTION_KEY=<generated-key>
```

3. **Run migrations:**
```bash
python manage.py migrate accounts
```

### Creating Users

```python
from accounts.models import User

# Create user (email automatically encrypted)
user = User.objects.create_user(
    username="alice",
    email="alice@example.com",
    password="SecurePassword123!"
)

# Email is now encrypted in database
print(user.encrypted_email)  # b'\x...' (binary data)
print(user.email_digest)     # '7a3f...' (SHA-256 hex)
```

### Accessing Email

```python
# Get decrypted email
email = user.email_decrypted  # "alice@example.com"

# First access: decrypts from database
# Subsequent accesses: uses cache
```

### Finding Users by Email

```python
# Find by email (using digest)
user = User.find_by_email("alice@example.com")

# Case-insensitive
user = User.find_by_email("ALICE@EXAMPLE.COM")  # Same user
```

### Login Flow

```python
from accounts.forms import LoginForm

# Create form with email as identifier
form = LoginForm(data={
    "identifier": "alice@example.com",
    "password": "SecurePassword123!",
})

if form.is_valid():
    user = form.find_user()  # Uses digest lookup
    if user and user.check_password(form.cleaned_data["password"]):
        # Login successful
        login(request, user)
```

---

## Testing

### Run All Tests

```bash
# Run all accounts tests (including encryption)
python manage.py test accounts

# Run only encryption tests
python manage.py test accounts.test_encryption

# Run with verbose output
python manage.py test accounts.test_encryption -v 2
```

### Test Coverage

**Encryption Utilities (11 tests):**
- Key generation (32 bytes)
- Encrypt/decrypt roundtrip
- Email normalization (lowercase)
- Different emails → different ciphertexts
- Same email → different ciphertexts (unique nonces)
- Digest generation (deterministic)
- Digest case-insensitivity
- Error handling (invalid data, corrupted data)

**User Model (6 tests):**
- User creation encrypts email
- Email decryption works
- Caching prevents repeated decryption
- find_by_email() method
- Case-insensitive lookup
- Email uniqueness constraint

**Forms (5 tests):**
- SignupForm detects duplicate emails
- Case-insensitive duplicate detection
- SignupForm.save() encrypts email
- LoginForm finds user by email
- Case-insensitive email login

**Views (4 tests):**
- Signup creates encrypted email
- Login works with encrypted emails
- Case-insensitive login
- Duplicate email rejection

**Total: 26 encryption-specific tests**

### Demo Script

```bash
# Run comprehensive demonstration
python test_encryption_demo.py
```

This script demonstrates:
1. Encryption utilities
2. User creation with encrypted email
3. Database verification
4. Decryption
5. Digest-based lookups
6. Login form integration
7. Uniqueness constraint

---

## Troubleshooting

### Error: "ACCOUNT_EMAIL_ENCRYPTION_KEY not found"

**Solution:**
1. Generate a key: `python -c "from accounts.encryption import generate_encryption_key; print(generate_encryption_key())"`
2. Add to `.env`: `ACCOUNT_EMAIL_ENCRYPTION_KEY=<key>`
3. Restart Django

### Error: "Key must be 32 bytes"

**Cause:** Invalid encryption key format

**Solution:**
- Ensure key is base64-encoded
- Generate new key using `generate_encryption_key()`
- Do not manually edit the key

### Error: "Failed to decrypt email"

**Causes:**
- Wrong encryption key
- Corrupted encrypted_email field
- Key changed after encryption

**Solutions:**
1. Verify encryption key in `.env` matches original
2. Check encrypted_email field is not null
3. If key changed, re-encrypt all emails:
   ```bash
   python manage.py migrate accounts 0002  # Rollback
   python manage.py migrate accounts       # Re-run encryption
   ```

### Error: "That email is already registered"

**Expected behavior:** Email uniqueness is working correctly

**If unexpected:**
- Check if user already exists: `User.objects.filter(email_digest=generate_email_digest(email))`
- Delete duplicate if needed

### Emails not being encrypted

**Checklist:**
1. Migrations applied? `python manage.py migrate accounts`
2. User.save() being called?
3. email field populated before save()?
4. Check user.encrypted_email is not None

---

## Future Improvements

### Short-term

1. **Remove plaintext email field:**
   - After verifying all functionality works
   - Create migration to drop email column
   - Use email_decrypted exclusively

2. **Add management command:**
   ```bash
   python manage.py verify_email_encryption
   ```
   - Check all users have encrypted emails
   - Identify users needing re-encryption
   - Verify key is working

3. **Add logging:**
   - Log encryption/decryption operations
   - Monitor for errors
   - Track performance

### Long-term (Production)

1. **Key Rotation:**
   - Support multiple encryption keys
   - Gradual re-encryption
   - Zero-downtime rotation

2. **External Key Management:**
   - AWS KMS integration
   - HashiCorp Vault
   - Azure Key Vault

3. **Searchable Encryption:**
   - For admin searches
   - Encrypted search index
   - Privacy-preserving lookups

4. **Backup/Recovery:**
   - Encrypted backups
   - Key escrow for recovery
   - Disaster recovery procedures

---

## Academic Project Notes

### MCO 1 Requirements

**✅ Completed:**
- Data encryption demonstration (AES-256-GCM)
- Data decryption demonstration (authenticated decryption)
- Secure key management (environment variables)
- Comprehensive documentation (inline comments + this file)
- Test coverage (26 encryption-specific tests)
- Working demonstration (login/signup with encrypted emails)

### Learning Objectives

**Encryption Concepts:**
- Symmetric vs asymmetric encryption
- Block cipher modes (GCM)
- Authenticated encryption
- Nonce/IV management

**Security Practices:**
- Key management
- Environment variable usage
- Defense in depth
- Error handling

**Software Engineering:**
- Database migrations
- Backwards compatibility
- Testing strategies
- Documentation

---

## Files Modified

```
├── accounts/
│   ├── encryption.py              # NEW: Encryption utilities
│   ├── models.py                  # MODIFIED: Added encrypted fields
│   ├── forms.py                   # MODIFIED: Digest-based lookups
│   ├── test_encryption.py         # NEW: Encryption tests
│   └── migrations/
│       ├── 0002_add_email_encryption_fields.py  # NEW
│       └── 0003_encrypt_existing_emails.py      # NEW
├── brewschews/
│   └── settings.py                # MODIFIED: Key validation
├── .env.example                   # MODIFIED: Added key docs
├── test_encryption_demo.py        # NEW: Demo script
└── EMAIL_ENCRYPTION_IMPLEMENTATION.md  # NEW: This file
```

---

## References

- [NIST AES-GCM Specification](https://csrc.nist.gov/publications/detail/sp/800-38d/final)
- [Cryptography Python Library](https://cryptography.io/)
- [Django Encryption Best Practices](https://docs.djangoproject.com/en/stable/topics/security/)
- [OWASP Cryptographic Storage](https://owasp.org/www-project-top-ten/2017/A3_2017-Sensitive_Data_Exposure)

---

**Last Updated:** 2025-10-28
**Author:** Claude (Claude Code)
**Project:** IT302 MCO 1 - Email Encryption
