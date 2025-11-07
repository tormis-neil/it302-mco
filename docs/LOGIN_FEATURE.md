# User Authentication (Login) Feature

## What It Is

The login system authenticates registered users and grants them access to the Brews & Chews ordering platform. It supports login with either username or email, implements secure password verification, and includes comprehensive audit logging for security monitoring.

## How It Works

### Step-by-Step Authentication Flow

1. **User Visits Login Page** (`/accounts/login/`)
   - GET request → `accounts/views.py:62` (`login_view`)
   - Empty `LoginForm` displayed with identifier and password fields

2. **User Submits Credentials**
   - POST request → `accounts/views.py:62`
   - Form data: `identifier` (username or email), `password`

3. **Form Validation** (`accounts/forms.py:168` - `LoginForm`)
   - Basic field validation (non-empty, trimmed)
   - Note: Password correctness checked later, not in form validation

4. **User Lookup** (`accounts/forms.py:195` - `find_user()`)

   **Email Detection** (`accounts/forms.py:213`):
   - If identifier contains `@` → Search by email
   - Generates digest: `generate_email_digest(identifier)`
   - Queries: `User.objects.filter(email_digest=digest).first()`

   **Username Search** (`accounts/forms.py:218`):
   - Otherwise → Search by username
   - Case-insensitive: `User.objects.filter(username__iexact=identifier).first()`
   - Example: "JohnDoe" finds user with username "johndoe"

5. **Password Verification** (`accounts/views.py:85`)
   ```python
   if user is None or not user.check_password(password):
       # Login failed
   ```

   **Process**:
   - `user.check_password(password)` retrieves stored hash from database
   - Hashes submitted password with same salt and parameters
   - Compares hashes (constant-time comparison, prevents timing attacks)
   - Returns True if match, False otherwise

6. **Login Success** (`accounts/views.py:96`)
   - `login(request, user)` creates session
   - Session ID stored in cookie (HttpOnly, SameSite=Lax)
   - User object attached to request for subsequent requests
   - Audit log: `successful=True` (`accounts/views.py:98`)
   - Redirect to menu catalog (`/menu/`)

7. **Login Failure** (`accounts/views.py:86`)
   - Generic error: "Invalid username or password."
   - No distinction between "user not found" vs "wrong password" (prevents username enumeration)
   - Audit log: `successful=False` (`accounts/views.py:87`)
   - Form redisplayed with error

## Key Questions & Answers

### Q1: How does login with email work when emails are encrypted?

**A:** The system uses **email digests** (SHA-256 hashes) for lookups without decryption.

**Process** (`accounts/forms.py:213`):
```python
if "@" in identifier:
    # User entered email
    email_digest = generate_email_digest(identifier)
    user = User.objects.filter(email_digest=email_digest).first()
```

**Why this works**:
1. During signup: Email `alice@example.com` → Digest `abc123...def` → Stored in `email_digest` field
2. During login: User enters `alice@example.com` → Generate digest `abc123...def`
3. Query database: `WHERE email_digest = 'abc123...def'`
4. Match found → User retrieved
5. **No decryption needed** for login!

**Case insensitivity**: Emails normalized to lowercase before hashing
```python
email = "ALICE@Example.COM"
normalized = email.lower().strip()  # "alice@example.com"
digest = hashlib.sha256(normalized.encode()).hexdigest()
```

### Q2: Why doesn't the error message distinguish between "user not found" and "wrong password"?

**A:** **Security best practice** to prevent **username enumeration attacks**.

**Without generic errors** (INSECURE):
```
User enters: alice / wrongpass
Error: "Incorrect password"  ← Attacker learns "alice" exists!

User enters: bob / wrongpass
Error: "User not found"  ← Attacker learns "bob" doesn't exist!
```

**With generic errors** (SECURE) (`accounts/views.py:86`):
```python
alert_message = "Invalid username or password."  # Same for both cases
```

**Result**: Attacker can't determine if username exists or password is wrong.

**Trade-off**: Slightly less helpful UX, but significantly more secure.

### Q3: How are sessions managed after login?

**A:** Django's built-in session framework with secure cookie settings.

**Session Creation** (`accounts/views.py:97`):
```python
login(request, user)
```

**What happens**:
1. Session ID generated (cryptographically random)
2. Session data stored server-side (database or cache):
   - User ID
   - Login timestamp
   - Session expiration time
3. Session ID sent to browser in cookie:
   - Cookie name: `sessionid`
   - HttpOnly: `True` (JavaScript can't read it)
   - SameSite: `Lax` (CSRF protection)
   - Secure: `True` in production (HTTPS only)

**Session Settings** (`brewschews/settings.py:424`):
```python
SESSION_COOKIE_HTTPONLY = True  # Prevents XSS attacks
SESSION_COOKIE_SAMESITE = 'Lax'  # Prevents CSRF attacks
```

**Session Persistence**:
- Subsequent requests include session cookie
- Django's `AuthenticationMiddleware` reads cookie (`brewschews/settings.py:128`)
- User object attached to `request.user`
- Views check `request.user.is_authenticated`

### Q4: What is audit logging, and what information is captured?

**A:** **Audit logging** records all authentication attempts for security monitoring and forensics.

**Captured Data** (`accounts/models.py:262` - `AuthenticationEvent`):
- `event_type`: "login" or "signup"
- `ip_address`: Client IP (IPv4 or IPv6)
- `user_agent`: Browser/device info
- `username_submitted`: What user entered (even if wrong)
- `email_submitted`: Email if provided
- `user`: Link to User object (if found)
- `successful`: True/False
- `created_at`: Timestamp

**Recording** (`accounts/views.py:87-104`):
```python
_record_event(
    event_type=AuthenticationEvent.EventType.LOGIN,
    ip_address=ip_address,
    user_agent=user_agent,
    username=identifier,
    user=user,
    successful=False,  # Or True if login succeeded
)
```

**Use Cases**:
- Detect brute force attacks (many failed attempts from same IP)
- Investigate unauthorized access
- Compliance requirements (audit trail)
- Track login history per user

**Viewing Logs** (Django shell):
```python
from accounts.models import AuthenticationEvent

# Recent login attempts
recent = AuthenticationEvent.objects.filter(event_type='login')[:10]
for event in recent:
    print(f"{event.created_at}: {event.username_submitted} - {'✓' if event.successful else '✗'}")

# Failed login attempts for specific user
User.objects.get(username='alice').authentication_events.filter(successful=False)
```

### Q5: Can users stay logged in across browser sessions?

**A:** By default, **sessions expire when browser closes**. This can be changed.

**Current Behavior**:
- Session cookie has no `Max-Age` or `Expires` attribute
- Browser deletes cookie when closed (session cookie)
- User must log in again after closing browser

**To Enable "Remember Me"** (not currently implemented):
1. Add checkbox to login form: "Keep me logged in"
2. Set session expiry in view:
   ```python
   if remember_me:
       request.session.set_expiry(1209600)  # 2 weeks
   else:
       request.session.set_expiry(0)  # Browser close
   ```

**Setting** (`brewschews/settings.py` - not currently set):
```python
SESSION_COOKIE_AGE = 1209600  # 2 weeks in seconds
```

## Code References

| Component | File:Line | Description |
|-----------|-----------|-------------|
| Login View | `accounts/views.py:62` | Handles GET/POST requests |
| Login Form | `accounts/forms.py:168` | Validates identifier and password |
| User Lookup (Email) | `accounts/forms.py:213` | Finds user by email digest |
| User Lookup (Username) | `accounts/forms.py:218` | Finds user by username |
| Password Verification | `accounts/views.py:85` | `user.check_password()` |
| Session Creation | `accounts/views.py:97` | `login(request, user)` |
| Audit Logging | `accounts/views.py:87` | Records login attempts |
| Get Client IP | `accounts/utils.py` | Extracts IP from request |
| Session Settings | `brewschews/settings.py:424` | Cookie security config |

## Edge Cases

### 1. What if user enters email with different case?

**Scenario**: User registered with `alice@example.com`, logs in with `ALICE@EXAMPLE.COM`

**Handling**:
- Identifier normalized to lowercase (`accounts/forms.py:181`): `identifier.strip()`
- Digest generated from lowercase version
- Email lookup succeeds
- **Result**: Login succeeds (case-insensitive)

**Code**:
```python
def clean_identifier(self) -> str:
    return self.cleaned_data["identifier"].strip()
```

Digest generation normalizes: `generate_email_digest()` lowercases before hashing.

### 2. What if user account is deleted while logged in?

**Scenario**: User logged in, admin deletes their account.

**Handling**:
- Session still contains user ID
- On next request, `AuthenticationMiddleware` tries to load user
- User doesn't exist → `request.user` becomes `AnonymousUser`
- `@login_required` decorator redirects to login page
- **Result**: User automatically logged out

### 3. What if database is down during login?

**Scenario**: Database connection fails during `user.check_password()`.

**Handling**:
- Database exception raised
- Django error handling catches exception
- If `DEBUG=True`: Detailed error page shown
- If `DEBUG=False`: Generic 500 error page
- Audit logging wrapped in try/except (`accounts/views.py:57`):
  ```python
  try:
      AuthenticationEvent.objects.create(...)
  except DatabaseError:
      logger.exception("Unable to persist authentication audit event")
  ```
- **Result**: Login fails, error logged, user sees error page

### 4. What if user logs in from two devices?

**Scenario**: User logs in on phone, then logs in on laptop.

**Handling**:
- Each login creates separate session
- Both sessions active simultaneously
- Both devices can access account concurrently
- **Result**: Multiple concurrent sessions allowed

**To prevent** (not currently implemented):
- Store session key in user profile
- On new login, invalidate previous session
- Only one active session per user

### 5. What if attacker brute forces passwords?

**Scenario**: Attacker tries 1000 passwords for username "alice".

**Current Protection**:
- Argon2 hashing is slow (~0.5s per attempt)
- 1000 attempts = ~500 seconds minimum
- All attempts logged in `AuthenticationEvent`
- Can detect pattern in audit logs

**Previously Implemented** (removed per feedback):
- Rate limiting: Max 5 failed attempts per 15 minutes
- Account lockout after X failures
- IP-based throttling

**Consider re-implementing** for production security.

## Testing Guide

### Manual Testing Checklist

#### Test 1: Valid Login with Username
1. Navigate to `/accounts/login/`
2. Enter valid credentials:
   - Identifier: `testuser123`
   - Password: `SecurePass123!`
3. Click "Log In"
4. **Expected**: Redirected to `/menu/`, logged in
5. **Verify**:
   - Navbar shows username
   - Can access `/accounts/profile/`
   - Session cookie present (browser dev tools → Application → Cookies)

#### Test 2: Valid Login with Email
1. Navigate to `/accounts/login/`
2. Enter:
   - Identifier: `test@example.com`
   - Password: `SecurePass123!`
3. Click "Log In"
4. **Expected**: Redirected to `/menu/`, logged in
5. **Verify**: Same as Test 1

#### Test 3: Invalid Username
1. Enter:
   - Identifier: `nonexistentuser`
   - Password: `anypassword`
2. **Expected**: Error "Invalid username or password."
3. **Verify**:
   - Not logged in
   - Form redisplayed
   - Check audit log:
     ```python
     from accounts.models import AuthenticationEvent
     AuthenticationEvent.objects.filter(username_submitted='nonexistentuser', successful=False).exists()
     # Should return True
     ```

#### Test 4: Wrong Password
1. Enter:
   - Identifier: `testuser123` (valid user)
   - Password: `wrongpassword`
2. **Expected**: Error "Invalid username or password." (same as Test 3)
3. **Verify**:
   - Not logged in
   - Error message identical to invalid username case

#### Test 5: Case Insensitive Username
1. Register user: `testuser123`
2. Login with: `TESTUSER123`
3. **Expected**: Login succeeds
4. **Verify**: Username lookup is case-insensitive

#### Test 6: Case Insensitive Email
1. Register: `test@example.com`
2. Login with: `TEST@example.com`
3. **Expected**: Login succeeds
4. **Verify**: Email digest matches regardless of case

#### Test 7: Session Persistence
1. Log in successfully
2. Navigate to protected page (e.g., `/accounts/profile/`)
3. **Expected**: Page loads without redirect to login
4. Close browser (not tab, entire browser)
5. Reopen browser, visit protected page
6. **Expected**: Redirected to login (session expired)

#### Test 8: Logout
1. Log in successfully
2. Click "Log Out" in navbar
3. **Expected**:
   - Redirected to home page
   - Navbar shows "Log In" and "Sign Up" links
   - Session cookie deleted
   - Can't access `/accounts/profile/` without redirect

#### Test 9: Empty Form Submission
1. Leave identifier and password blank
2. Click "Log In"
3. **Expected**: Error "Enter your username/email and password to continue."
4. **Verify**: Form redisplayed with validation errors

#### Test 10: Audit Log Verification
1. Perform failed login attempt
2. Check audit log:
   ```python
   from accounts.models import AuthenticationEvent
   from accounts.utils import get_client_ip

   events = AuthenticationEvent.objects.filter(event_type='login').order_by('-created_at')[:5]
   for event in events:
       print(f"{event.created_at} - {event.username_submitted} - {'Success' if event.successful else 'Failed'} - {event.ip_address}")
   ```
3. **Expected**: Entry exists with correct data

### Automated Testing

Run the login tests:
```bash
python manage.py test accounts.tests.LoginViewTests
```

**Test Coverage** (`accounts/tests.py`):
- Valid login (username and email)
- Invalid credentials
- Case sensitivity
- Session creation
- Audit logging
- Redirect after login

## Debugging Common Issues

### Issue 1: Login succeeds but user immediately logged out

**Cause**: Session middleware not enabled or session backend issue.

**Debug**:
1. Check `MIDDLEWARE` includes `SessionMiddleware` (`brewschews/settings.py:124`)
2. Check session backend configured:
   ```python
   python manage.py shell
   from django.contrib.sessions.models import Session
   print(Session.objects.count())  # Should show active sessions
   ```
3. Check cookies enabled in browser
4. Check `SESSION_COOKIE_HTTPONLY` not blocking legitimate access

**Fix**: Ensure middleware order is correct (SessionMiddleware before AuthenticationMiddleware).

### Issue 2: Can't find user by email

**Cause**: Email digest mismatch (wrong key used for encryption, or digest not generated).

**Debug**:
```python
from accounts.models import User
from accounts.encryption import generate_email_digest

email = "test@example.com"
digest = generate_email_digest(email)
print(f"Looking for digest: {digest}")

# Check if digest exists in database
users = User.objects.filter(email_digest=digest)
print(f"Found {users.count()} users")

# Check what digests exist
all_digests = User.objects.values_list('email_digest', flat=True)
print(f"Total users with digest: {len([d for d in all_digests if d])}")
```

**Fix**: If digest missing, run migration to generate digests for existing users.

### Issue 3: Constant "Invalid username or password" even with correct credentials

**Cause**: Password hash algorithm mismatch or database corruption.

**Debug**:
```python
from accounts.models import User

user = User.objects.get(username='testuser123')
print(f"Password hash: {user.password[:50]}...")  # Should start with "argon2$"

# Test password check
correct = user.check_password('SecurePass123!')
print(f"Password check result: {correct}")  # Should be True
```

**Fix**:
- If hash doesn't start with `argon2$`, password hasher issue
- Reset password via Django shell:
  ```python
  user.set_password('SecurePass123!')
  user.save()
  ```

### Issue 4: Audit log not recording events

**Cause**: Database error or `_record_event` function failing silently.

**Debug**:
1. Check logs for exceptions
2. Manually test audit logging:
   ```python
   from accounts.views import _record_event
   from accounts.models import AuthenticationEvent

   _record_event(
       event_type=AuthenticationEvent.EventType.LOGIN,
       ip_address="127.0.0.1",
       user_agent="Test",
       username="test",
       successful=True
   )

   # Check if created
   AuthenticationEvent.objects.filter(username_submitted='test').exists()
   ```

**Fix**: Check database permissions, ensure table exists (`python manage.py migrate`).

### Issue 5: Login form not submitting

**Cause**: JavaScript error or CSRF token missing.

**Debug**:
1. Check browser console for errors
2. Inspect form HTML, ensure CSRF token present:
   ```html
   <input type="hidden" name="csrfmiddlewaretoken" value="...">
   ```
3. Check `CsrfViewMiddleware` enabled (`brewschews/settings.py:127`)

**Fix**: Ensure `{% csrf_token %}` in form template.

## Security Best Practices Followed

1. **Password Verification**: Uses `check_password()` with constant-time comparison (prevents timing attacks)
2. **Generic Error Messages**: Prevents username enumeration
3. **Audit Logging**: All login attempts recorded for security monitoring
4. **Session Security**: HttpOnly cookies (prevents XSS), SameSite=Lax (prevents CSRF)
5. **Slow Password Hashing**: Argon2 (~0.5s) makes brute force impractical
6. **Case-Insensitive Lookups**: Prevents "Alice" vs "alice" confusion
7. **Email Encryption**: Protects PII even during authentication
8. **IP Logging**: Tracks source of authentication attempts
9. **No Password Hints**: System never reveals password information
10. **CSRF Protection**: Middleware validates CSRF token on POST requests

## Future Enhancements

1. **Two-Factor Authentication (2FA)**
   - TOTP (Google Authenticator)
   - SMS verification
   - Email verification codes

2. **Rate Limiting** (previously implemented, consider re-adding)
   - Max 5 failed attempts per 15 minutes
   - Account lockout after 10 failures
   - IP-based throttling

3. **Password Reset**
   - Email verification
   - Time-limited reset tokens
   - Audit logging for reset attempts

4. **Remember Me**
   - Extended session duration
   - Device fingerprinting
   - Trust this device option

5. **Login Notifications**
   - Email alerts for new logins
   - Suspicious activity detection
   - Login from new device alerts
