# User Registration (Signup) Feature

## What It Is

The signup system allows new users to create accounts for the Brews & Chews café ordering platform. It implements comprehensive validation, secure password hashing, and automatic email encryption to ensure data security from the moment users register.

## How It Works

### Step-by-Step Registration Flow

1. **User Visits Signup Page** (`/accounts/signup/`)
   - GET request → `accounts/views.py:118` (`signup_view`)
   - Empty `SignupForm` displayed with username, email, password fields

2. **User Submits Registration Form**
   - POST request → `accounts/views.py:118`
   - Form data: `username`, `email`, `password`, `confirm_password`

3. **Form Validation** (`accounts/forms.py:29` - `SignupForm`)

   **Username Validation** (`accounts/forms.py:45`)
   - Must match pattern: 3-30 characters, alphanumeric with `._-`
   - Case-insensitive uniqueness check
   - Rejected examples: "ab" (too short), "user@name" (invalid char)

   **Email Validation** (`accounts/forms.py:65`)
   - Normalized to lowercase
   - Generates SHA-256 digest for uniqueness check
   - Checks against `email_digest` field (works with encrypted emails)
   - Prevents duplicate registrations

   **Password Validation** (`accounts/forms.py:99`)
   - Django built-in validators (settings.py:339):
     - Not similar to username/email
     - Minimum 12 characters
     - Not in common password list (~20,000 passwords)
     - Not entirely numeric

   - Custom strength requirements (`accounts/forms.py:122`):
     - At least one uppercase letter (A-Z)
     - At least one number (0-9)
     - At least one special character (!@#$%^&*)

   **Password Confirmation** (`accounts/forms.py:117`)
   - Must exactly match password field

4. **User Creation** (if validation passes)
   - Calls `User.objects.create_user()` (`accounts/models.py:63`)
   - Password hashed with Argon2 (`accounts/models.py:59`)
   - Email encrypted with AES-256-GCM (`accounts/models.py:252`)
   - Email digest generated for lookups (`accounts/models.py:150`)

5. **Profile Auto-Creation**
   - Signal triggered after user save (`accounts/models.py:347`)
   - `Profile` created with `display_name = username`
   - OneToOne relationship established

6. **Audit Logging**
   - Success/failure recorded in `AuthenticationEvent` table
   - Captures: IP address, user agent, timestamp (`accounts/views.py:143`)

7. **Auto-Login & Redirect**
   - User automatically logged in after signup (`accounts/views.py:140`)
   - Session created
   - Redirected to menu catalog (`/menu/`)

## Key Questions & Answers

### Q1: How are passwords stored securely?

**A:** Passwords are hashed using **Argon2id**, the winner of the 2015 Password Hashing Competition.

**Process** (`accounts/models.py:59`):
```python
user.set_password(password)  # Hashes with Argon2
```

**Hash Format**:
```
argon2$argon2id$v=19$m=102400,t=2,p=8$[16-byte-salt]$[hash]
```

**Security Parameters** (`brewschews/settings.py:282`):
- Algorithm: Argon2id (hybrid mode, resistant to GPU attacks)
- Memory cost: 102,400 KB (~100 MB)
- Time cost: 2 iterations
- Parallelism: 8 threads
- Hashing time: ~0.5 seconds (intentionally slow to prevent brute force)

**Why Argon2?**
- Memory-hard: Expensive for GPU/ASIC cracking attempts
- Resistant to rainbow tables, brute force, side-channel attacks
- Industry standard (used by Microsoft, 1Password, Bitwarden)
- OWASP recommended

### Q2: Why is email encrypted, and how does uniqueness checking work?

**A:** Emails are encrypted for PII (Personally Identifiable Information) protection as an academic demonstration (MCO 1 requirement).

**Encryption Process** (`accounts/models.py:128`):
1. User submits email: `alice@example.com`
2. On save, email encrypted with AES-256-GCM (`accounts/encryption.py:88`)
3. SHA-256 digest generated: `generate_email_digest(email)` (`accounts/encryption.py:220`)
4. Both stored in database:
   - `encrypted_email`: Binary field with encrypted data
   - `email_digest`: 64-char hex string for lookups

**Uniqueness Check** (`accounts/forms.py:81`):
```python
email_digest = generate_email_digest(email)
if User.objects.filter(email_digest=email_digest).exists():
    raise ValidationError("That email is already registered.")
```

**Why digest?** Encrypted emails can't be compared directly. The digest provides a deterministic fingerprint for each unique email, enabling fast database lookups without decryption.

### Q3: What happens if validation fails?

**A:** Multiple scenarios:

**Duplicate Username** (`accounts/forms.py:60`):
- Error: "That username is already taken."
- Form redisplayed with error message
- AuthenticationEvent logged with `successful=False`

**Weak Password** (`accounts/forms.py:134`):
- Errors listed:
  - "Password must be at least 12 characters long."
  - "Include at least one uppercase letter."
  - "Include at least one number."
  - "Include at least one special character (!@#$%^&*)."
- All errors shown to user
- Form redisplayed

**Password Mismatch** (`accounts/forms.py:118`):
- Error: "Passwords do not match."
- Shown on confirm_password field

**Network/Database Errors**:
- Caught and logged (`accounts/views.py:57`)
- Generic error shown to user (prevents information disclosure)

### Q4: Can users register with the same email twice?

**A:** No. The system prevents duplicate emails at multiple levels:

1. **Form Validation** (`accounts/forms.py:84`):
   - Generates digest of submitted email
   - Queries: `User.objects.filter(email_digest=digest).exists()`
   - Raises ValidationError if found

2. **Database Constraint** (`accounts/models.py:111`):
   - `email_digest` field has `unique=True`
   - Database-level enforcement (last line of defense)

3. **Case-Insensitive Matching**:
   - Emails normalized to lowercase before hashing
   - `Alice@Example.com` = `alice@example.com` (same digest)

## Code References

| Component | File:Line | Description |
|-----------|-----------|-------------|
| Signup View | `accounts/views.py:118` | Handles GET/POST requests |
| Signup Form | `accounts/forms.py:29` | Validation logic |
| Username Validation | `accounts/forms.py:45` | Pattern matching, uniqueness |
| Email Validation | `accounts/forms.py:65` | Digest generation, uniqueness |
| Password Validation | `accounts/forms.py:99` | Django + custom validators |
| User Creation | `accounts/forms.py:149` | `User.objects.create_user()` |
| Password Hashing | `accounts/models.py:59` | `set_password()` with Argon2 |
| Email Encryption | `accounts/models.py:128` | `_encrypt_and_store_email()` |
| Profile Creation Signal | `accounts/models.py:347` | Auto-creates profile |
| Audit Logging | `accounts/views.py:143` | Records signup events |

## Edge Cases

### 1. What if two users submit the same username simultaneously?

**Scenario**: User A and User B both submit username "john" at the exact same time.

**Handling**:
- Form validation runs first for both (may both pass if timing is tight)
- Database has `unique=True` on username field
- Database rejects second INSERT
- Django raises `IntegrityError`
- One user sees: "That username is already taken." (error bubbles up)
- Form redisplays with error

**Code**: Database constraint is the final authority (`accounts/models.py` inherits from `AbstractUser` with unique username)

### 2. What if email encryption fails?

**Scenario**: Encryption key missing or corrupted.

**Handling** (`accounts/encryption.py:145`):
```python
def _encrypt_and_store_email(self, plaintext_email: str) -> None:
    try:
        self.encrypted_email = encrypt_email(plaintext_email)
        self.email_digest = generate_email_digest(plaintext_email)
    except EmailEncryptionError as e:
        logger.error(f"Failed to encrypt email for user {self.username}: {e}")
        raise  # Prevents user creation if encryption fails
```

**Result**:
- User creation fails
- Error logged
- User sees generic error message
- No partial data saved (database transaction rolled back)

### 3. What if user enters uppercase email?

**Scenario**: User enters `Alice@EXAMPLE.COM`

**Handling**:
- Email normalized to lowercase (`accounts/forms.py:77`): `email.strip().lower()`
- Stored as: `alice@example.com`
- Digest generated from lowercase version
- Ensures `Alice@example.com` = `alice@example.com` (same account)

### 4. What if profile creation signal fails?

**Scenario**: Profile creation signal raises exception.

**Handling** (`accounts/models.py:359`):
```python
if created:
    Profile.objects.create(user=instance, display_name=instance.username)
```

**Result**:
- If Profile creation fails, exception propagates
- User creation rolled back (atomic transaction)
- Prevents orphaned User without Profile
- Error logged and shown to user

## Testing Guide

### Manual Testing Checklist

#### Test 1: Valid Registration
1. Navigate to `/accounts/signup/`
2. Enter valid data:
   - Username: `testuser123`
   - Email: `test@example.com`
   - Password: `SecurePass123!`
   - Confirm: `SecurePass123!`
3. Click "Sign Up"
4. **Expected**: Redirected to `/menu/`, logged in automatically
5. **Verify**:
   - Check navbar shows username
   - Visit `/accounts/profile/` to confirm profile exists
   - Check database: `python manage.py shell`
     ```python
     from accounts.models import User
     u = User.objects.get(username='testuser123')
     print(u.email_decrypted)  # Should show test@example.com
     print(u.profile.display_name)  # Should show testuser123
     ```

#### Test 2: Duplicate Username
1. Try registering with existing username (e.g., `testuser123`)
2. **Expected**: Error message "That username is already taken."
3. **Verify**: Form redisplayed, no new user created

#### Test 3: Duplicate Email
1. Try registering with existing email (e.g., `test@example.com`)
2. **Expected**: Error message "That email is already registered."
3. **Verify**: Works even with different case (`TEST@example.com`)

#### Test 4: Weak Password
1. Try each weak password:
   - `short` - Too short
   - `password123` - Too common
   - `longpassword` - No uppercase, no special char
   - `LONGPASSWORD` - No number, no special char
   - `12345678901234` - Entirely numeric
2. **Expected**: Specific error messages for each validation failure
3. **Verify**: Form shows multiple errors if multiple rules broken

#### Test 5: Password Mismatch
1. Enter password: `SecurePass123!`
2. Enter confirm: `SecurePass123@`
3. **Expected**: Error "Passwords do not match."

#### Test 6: Invalid Username Format
1. Try usernames:
   - `ab` - Too short
   - `user@name` - Invalid character
   - `this_is_a_very_long_username_that_exceeds_thirty_characters` - Too long
2. **Expected**: Error "Choose 3-30 characters using letters, numbers, periods, underscores, or hyphens."

#### Test 7: Email Case Insensitivity
1. Register: `test2@example.com`
2. Try registering: `TEST2@EXAMPLE.COM`
3. **Expected**: Error "That email is already registered."
4. **Verify**: Case doesn't matter for uniqueness

### Automated Testing

Run the signup tests:
```bash
python manage.py test accounts.tests.SignupTestCase
```

**Test Coverage** (`accounts/tests.py`):
- Valid registration
- Duplicate username/email
- Password validation
- Form field validation
- Profile auto-creation
- Audit logging

## Debugging Common Issues

### Issue 1: "That email is already registered" but I can't find the user

**Cause**: Email stored encrypted, can't query directly.

**Solution**: Search by digest
```python
from accounts.models import User
from accounts.encryption import generate_email_digest

email = "alice@example.com"
digest = generate_email_digest(email)
user = User.objects.filter(email_digest=digest).first()
print(user.email_decrypted if user else "Not found")
```

### Issue 2: Signup succeeds but no redirect

**Cause**: Template issue or JavaScript error.

**Debug**:
1. Check browser console for errors
2. Verify `LOGIN_REDIRECT_URL` setting (`brewschews/settings.py:401`)
3. Check view redirects to `menu:catalog` (`accounts/views.py:152`)

### Issue 3: Password validation inconsistent

**Cause**: JavaScript client-side validation differs from server-side.

**Debug**:
1. Check `static/js/auth.js` for client-side rules
2. Ensure matches `accounts/forms.py:122` server-side validation
3. Server-side is authoritative (JavaScript is UX enhancement only)

### Issue 4: Email encryption error

**Cause**: Missing or invalid encryption key.

**Debug**:
```bash
python manage.py shell
```
```python
from accounts.encryption import get_encryption_key, test_encryption_roundtrip

# Test key is valid
key = get_encryption_key()
print(f"Key length: {len(key)} bytes (should be 32)")

# Test encryption works
test_encryption_roundtrip("test@example.com")
```

**Fix**: Set valid key in `.env`:
```bash
python -c "from accounts.encryption import generate_encryption_key; print(generate_encryption_key())"
# Copy output to .env file:
# ACCOUNT_EMAIL_ENCRYPTION_KEY=generated_key_here
```

## Security Best Practices Followed

1. **Password Hashing**: Argon2id with high memory cost (resistant to GPU attacks)
2. **Email Encryption**: AES-256-GCM for PII protection
3. **CSRF Protection**: Django's CSRF middleware prevents forged requests
4. **Audit Logging**: All signup attempts logged (IP, timestamp, success/failure)
5. **Rate Limiting**: (Previously implemented, removed per feedback - consider re-implementing)
6. **Input Validation**: Server-side validation (client-side is UX only)
7. **Error Messages**: Generic errors prevent information disclosure (don't reveal if username exists)
8. **Session Security**: HttpOnly cookies, SameSite=Lax (`brewschews/settings.py:424`)

## Git Commands for Pulling Changes

### Pull this branch to your local VSCode:

```bash
# Fetch the branch from GitHub
git fetch origin claude/create-tech-docs-011CUaWbQgguXDLkLTq9Jafv

# Checkout the branch
git checkout claude/create-tech-docs-011CUaWbQgguXDLkLTq9Jafv

# Or pull directly if you're already on another branch
git pull origin claude/create-tech-docs-011CUaWbQgguXDLkLTq9Jafv
```

### Merge to your main branch:

```bash
# Switch to your main branch
git checkout main

# Merge the documentation branch
git merge claude/create-tech-docs-011CUaWbQgguXDLkLTq9Jafv

# Push to GitHub
git push origin main
```

### Or use GitHub Pull Request (Recommended):

1. Go to GitHub repository
2. Click "Pull requests" tab
3. Find the pull request for this branch
4. Click "Merge pull request"
5. Confirm merge
6. Pull updated main to local:
   ```bash
   git checkout main
   git pull origin main
   ```
