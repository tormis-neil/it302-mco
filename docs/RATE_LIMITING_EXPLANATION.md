# Rate Limiting and Account Lockout - Comprehensive Explanation

## Overview

The Brews & Chews application implements **two separate security mechanisms** to protect against brute-force attacks and abuse:

1. **IP-based Rate Limiting** - Limits requests from a single IP address
2. **Account Lockout** - Locks individual user accounts after repeated failed login attempts

---

## 1. IP-Based Rate Limiting

### What is it?
IP-based rate limiting **tracks and limits the number of authentication attempts from a single IP address** within a specific time window, regardless of which accounts are being accessed.

### Where does it apply?
- **Login page** (`/accounts/login/`)
- **Signup page** (`/accounts/signup/`)

### Configuration
Located in `accounts/views.py:29-37`:

```python
# Signup rate limiting
SIGNUP_RATE_LIMIT = 5         # Max 5 signup attempts
SIGNUP_RATE_WINDOW = 1 hour   # Per hour per IP

# Login rate limiting
LOGIN_RATE_LIMIT = 5          # Max 5 failed login attempts
LOGIN_RATE_WINDOW = 15 minutes # Per 15 minutes per IP
```

### How it works

#### Technical Implementation
1. Every authentication attempt (signup/login) is logged in the `AuthenticationEvent` table with:
   - IP address
   - Event type (signup/login)
   - Timestamp
   - Success/failure status
   - Username/email submitted

2. Before processing a request, the system:
   - Counts recent events from the same IP within the time window
   - Blocks the request if the limit is exceeded
   - Logs the rate-limited attempt

#### Code Flow (`accounts/views.py`)
```python
def _is_rate_limited(*, event_type, ip_address, window, limit, successful=None):
    """
    Check if IP has exceeded rate limit.

    Example:
    - window = 15 minutes, limit = 5
    - Counts failed logins from IP in last 15 minutes
    - Returns True if 5 or more found
    """
    cutoff = timezone.now() - window
    queryset = AuthenticationEvent.objects.filter(
        event_type=event_type,
        ip_address=ip_address,
        created_at__gte=cutoff,
    )
    if successful is not None:
        queryset = queryset.filter(successful=successful)
    return queryset.count() >= limit
```

### Examples

#### Example 1: Failed logins from one IP to different accounts
**Scenario:** An attacker tries to login to multiple accounts from IP `192.168.1.100`

```
Attempt 1: Login to "alice" with wrong password - IP: 192.168.1.100 ✗
Attempt 2: Login to "bob" with wrong password   - IP: 192.168.1.100 ✗
Attempt 3: Login to "charlie" with wrong password - IP: 192.168.1.100 ✗
Attempt 4: Login to "dave" with wrong password   - IP: 192.168.1.100 ✗
Attempt 5: Login to "eve" with wrong password    - IP: 192.168.1.100 ✗
Attempt 6: Login to "frank" with correct password - IP: 192.168.1.100 🔒 BLOCKED
```

**Result:** The 6th attempt is blocked with message:
```
"Too many sign-in attempts. Please try again in 15 minutes."
```

**Why?** The IP `192.168.1.100` made 5 failed login attempts within 15 minutes, regardless of which accounts were targeted.

#### Example 2: Signup rate limiting
**Scenario:** Someone tries to create multiple accounts from IP `10.0.0.50`

```
Attempt 1: Create account "user1" - IP: 10.0.0.50 ✓ Success
Attempt 2: Create account "user2" - IP: 10.0.0.50 ✓ Success
Attempt 3: Create account "user3" - IP: 10.0.0.50 ✓ Success
Attempt 4: Create account "user4" - IP: 10.0.0.50 ✓ Success
Attempt 5: Create account "user5" - IP: 10.0.0.50 ✓ Success
Attempt 6: Create account "user6" - IP: 10.0.0.50 🔒 BLOCKED
```

**Result:** The 6th signup attempt is blocked with message:
```
"Too many sign-up attempts from this network. Please try again later."
```

**Why?** The IP made 5 signup attempts (successful or failed) within 1 hour.

#### Example 3: Successful logins don't count toward rate limit
**Scenario:** User successfully logs in 6 times from IP `172.16.0.10`

```
Attempt 1: Login to "alice" with correct password - IP: 172.16.0.10 ✓
Attempt 2: Login to "alice" with correct password - IP: 172.16.0.10 ✓
Attempt 3: Login to "alice" with correct password - IP: 172.16.0.10 ✓
Attempt 4: Login to "alice" with correct password - IP: 172.16.0.10 ✓
Attempt 5: Login to "alice" with correct password - IP: 172.16.0.10 ✓
Attempt 6: Login to "alice" with correct password - IP: 172.16.0.10 ✓ Success
```

**Result:** All 6 attempts succeed. No rate limiting applied.

**Why?** Login rate limiting only counts **failed** attempts (`successful=False`). See `accounts/views.py:138`:

```python
if _is_rate_limited(
    event_type=AuthenticationEvent.EventType.LOGIN,
    ip_address=ip_address,
    window=LOGIN_RATE_WINDOW,
    limit=LOGIN_RATE_LIMIT,
    successful=False,  # ← Only counts failed attempts
):
```

---

## 2. Account Lockout

### What is it?
Account lockout **temporarily disables a specific user account** after too many failed password attempts, regardless of which IP address the attempts came from.

### Where does it apply?
- **Login page only** (`/accounts/login/`)
- **NOT** signup page (no account exists yet)

### Configuration
Located in `accounts/views.py:36-37`:

```python
LOGIN_LOCK_THRESHOLD = 5          # Lock after 5 failed attempts
LOGIN_LOCK_DURATION = 60 minutes  # Lock for 1 hour
```

### How it works

#### Database Fields (`accounts/models.py:82-88`)
Each `User` model has:
```python
failed_login_attempts = models.PositiveIntegerField(default=0)
locked_until = models.DateTimeField(blank=True, null=True)
last_failed_login_at = models.DateTimeField(blank=True, null=True)
```

#### Account State Transitions

**Normal State:**
- `failed_login_attempts = 0`
- `locked_until = None`
- Can login with correct password

**After Failed Login:**
```python
user.mark_login_failure()  # Increments failed_login_attempts
```

**After 5th Failed Login:**
```python
if user.failed_login_attempts >= 5:
    user.lock_for(timedelta(hours=1))  # Sets locked_until = now + 1 hour
    user.failed_login_attempts = 0     # Reset counter
```

**Account Locked:**
- `locked_until = future timestamp`
- `is_locked() = True`
- Cannot login even with correct password

**After Successful Login:**
```python
user.reset_login_failures()  # Resets all counters and unlocks
```

### Examples

#### Example 4: Account lockout on single account
**Scenario:** Someone tries to login to "alice" with wrong passwords

```
Attempt 1: Login to "alice" with "wrong1" ✗ (failed_attempts = 1)
Attempt 2: Login to "alice" with "wrong2" ✗ (failed_attempts = 2)
Attempt 3: Login to "alice" with "wrong3" ✗ (failed_attempts = 3)
Attempt 4: Login to "alice" with "wrong4" ✗ (failed_attempts = 4)
Attempt 5: Login to "alice" with "wrong5" ✗ (failed_attempts = 5)
  → Account locked for 60 minutes
Attempt 6: Login to "alice" with CORRECT password 🔒 BLOCKED
```

**Result:** After 5 failed attempts, the account is locked. The 6th attempt shows:
```
"Your account is locked. Try again in X minutes."
```

**Why?** The account "alice" reached the lockout threshold (5 failed attempts).

#### Example 5: Lockout is per account, not per IP
**Scenario:** Attacker tries "alice" from different IPs

```
Attempt 1: Login to "alice" from IP 10.0.0.1 ✗ (failed_attempts = 1)
Attempt 2: Login to "alice" from IP 10.0.0.2 ✗ (failed_attempts = 2)
Attempt 3: Login to "alice" from IP 10.0.0.3 ✗ (failed_attempts = 3)
Attempt 4: Login to "alice" from IP 10.0.0.4 ✗ (failed_attempts = 4)
Attempt 5: Login to "alice" from IP 10.0.0.5 ✗ (failed_attempts = 5)
  → Account "alice" locked
Attempt 6: Login to "alice" from IP 10.0.0.6 🔒 BLOCKED
```

**Result:** Account "alice" is locked, even though each attempt came from a different IP.

**Why?** Account lockout tracks failed attempts **per user account**, not per IP.

#### Example 6: Successful login resets lockout counter
**Scenario:** User makes mistakes but eventually logs in correctly

```
Attempt 1: Login to "bob" with "wrong1" ✗ (failed_attempts = 1)
Attempt 2: Login to "bob" with "wrong2" ✗ (failed_attempts = 2)
Attempt 3: Login to "bob" with "wrong3" ✗ (failed_attempts = 3)
Attempt 4: Login to "bob" with CORRECT password ✓
  → failed_attempts reset to 0
  → locked_until reset to None
Attempt 5: Login to "bob" with "wrong4" ✗ (failed_attempts = 1)
```

**Result:** After the successful login, the counter resets. The next failed attempt starts counting from 1 again.

#### Example 7: Lockout auto-expires after 60 minutes
**Scenario:** Account locked at 2:00 PM

```
2:00 PM: 5th failed login → Account locked until 3:00 PM
2:30 PM: Login attempt → "Locked. Try again in 30 minutes."
3:00 PM: Login attempt → "Locked. Try again in 1 minute."
3:01 PM: Login with correct password → ✓ Success
```

**Result:** After 60 minutes, the lockout expires and the user can login normally.

**Why?** The `is_locked()` method checks if current time is before `locked_until`:

```python
def is_locked(self):
    return bool(self.locked_until and self.locked_until > timezone.now())
```

---

## 3. How Both Mechanisms Work Together

### Layered Security
Both mechanisms work **independently** and provide defense-in-depth:

1. **First line of defense:** IP rate limiting
   - Blocks distributed attacks from one IP
   - Limits 5 failed attempts per 15 minutes per IP

2. **Second line of defense:** Account lockout
   - Protects specific accounts from distributed attacks
   - Locks account after 5 failed attempts (from any IP)

### Example 8: Both mechanisms triggered
**Scenario:** Attacker targets "alice" from IP `203.0.113.50`

```
Attempt 1: IP: 203.0.113.50 → alice (wrong password) ✗
  - IP rate limit: 1/5 failed attempts from IP
  - Account lockout: alice has 1/5 failed attempts

Attempt 2: IP: 203.0.113.50 → alice (wrong password) ✗
  - IP rate limit: 2/5 from IP
  - Account lockout: alice has 2/5 failed attempts

...

Attempt 5: IP: 203.0.113.50 → alice (wrong password) ✗
  - IP rate limit: 5/5 from IP (limit reached)
  - Account lockout: alice has 5/5 (account locked)

Attempt 6: IP: 203.0.113.50 → alice (correct password) 🔒
  - BLOCKED by IP rate limit first
  - Message: "Too many sign-in attempts. Please try again in 15 minutes."
```

**Result:** The 6th attempt is blocked by **IP rate limiting** before even checking the account lockout.

**Order of checks in code (`accounts/views.py:132-182`):**
```python
# Check 1: IP rate limiting (blocks immediately)
if _is_rate_limited(...):
    return "Too many sign-in attempts..."

# Check 2: User exists?
user = form.find_user()
if user is None:
    return "Invalid username or password"

# Check 3: Account locked?
if user.is_locked():
    return "Your account is locked..."

# Check 4: Password correct?
if not user.check_password(password):
    user.mark_login_failure()
    # Lock if threshold reached
    if user.failed_login_attempts >= 5:
        user.lock_for(timedelta(hours=1))
```

---

## 4. Summary Table

| Feature | IP Rate Limiting | Account Lockout |
|---------|-----------------|-----------------|
| **What it protects** | Network/IP address | Individual user account |
| **Scope** | All login/signup attempts from IP | One specific account |
| **Applies to** | Login page ✓<br>Signup page ✓ | Login page ✓<br>Signup page ✗ |
| **Threshold** | 5 failed attempts (login)<br>5 total attempts (signup) | 5 failed password attempts |
| **Time window** | 15 minutes (login)<br>1 hour (signup) | No window, just count |
| **Duration** | Until window expires | 60 minutes |
| **Counts successful attempts?** | No for login<br>Yes for signup | No |
| **Reset condition** | Wait for time window | Successful login |
| **Stored in** | `AuthenticationEvent` table | `User` table fields |
| **Can be bypassed by changing IP?** | Yes | No |
| **Can be bypassed by targeting different accounts?** | No | Yes |

---

## 5. Security Considerations

### Strengths
✅ **Defense in depth:** Two independent mechanisms
✅ **Prevents brute force:** Both IP-based and account-based attacks
✅ **Audit logging:** All attempts tracked in `AuthenticationEvent`
✅ **Auto-recovery:** Lockouts expire automatically
✅ **User-friendly:** Legitimate users can still access after lockout expires

### Limitations
⚠️ **Shared IPs:** Multiple users behind NAT/proxy share IP, may affect legitimate users
⚠️ **Distributed attacks:** Attacker with many IPs can bypass IP rate limiting
⚠️ **Account enumeration:** Error messages reveal which accounts exist (design trade-off for usability)

### IP Spoofing Protection
The implementation uses `REMOTE_ADDR` which **cannot be spoofed** by the client. See `accounts/utils.py:9-31`:

```python
def get_client_ip(request):
    """
    Uses REMOTE_ADDR which cannot be spoofed by the client.
    Does NOT use X-Forwarded-For to prevent bypass attacks.
    """
    return request.META.get("REMOTE_ADDR") or "0.0.0.0"
```

---

## 6. Testing Verification

All functionality is verified by automated tests in `accounts/tests.py`:

✅ **test_signup_rate_limit_blocks_submission** (line 70)
✅ **test_login_rate_limit_blocks_attempt** (line 168)
✅ **test_login_locks_account_after_threshold** (line 186)
✅ **test_login_wrong_password_increments_failure** (line 154)
✅ **test_login_success_redirects_and_resets_failures** (line 126)

Run tests with:
```bash
python manage.py test accounts.tests -v 2
```

---

## Conclusion

The Brews & Chews application implements comprehensive rate limiting and account lockout to protect against brute-force attacks:

- **IP rate limiting** prevents attacks from a single IP address
- **Account lockout** protects individual accounts from distributed attacks
- Both work **independently** and provide layered security
- Failed attempts are tracked per IP (for rate limiting) and per account (for lockout)
- Successful logins do NOT count toward login rate limits
- All attempts are logged for security monitoring
