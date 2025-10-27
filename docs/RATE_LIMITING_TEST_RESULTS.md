# Rate Limiting and Account Lockout - Test Results

## Test Summary

**Date:** October 26, 2025
**Test Suite:** Rate Limiting & Account Lockout
**Total Tests Run:** 23 (14 existing + 9 new scenario tests)
**Tests Passed:** ✅ 23/23 (100%)
**Tests Failed:** ❌ 0/23 (0%)

---

## Answers to Specific Questions

### 1. Is it per account?

**Answer:** There are TWO separate mechanisms:

- **IP Rate Limiting:** Per IP address (not per account)
  - Tracks all failed attempts from the same IP
  - Applies across all accounts accessed from that IP

- **Account Lockout:** Per account (not per IP)
  - Tracks failed login attempts for a specific user account
  - Applies regardless of which IP the attempts come from

### 2. Per failed attempts in one account?

**Answer:** Account lockout counts failed password attempts **for a specific account only**.

Example:
- 5 failed attempts on "alice" → Alice locked
- 5 failed attempts on "bob" → Bob locked
- Failed attempts on different accounts don't affect each other

**Test verification:** `test_account_lockout_is_per_account_not_per_ip`

### 3. From different accounts?

**Answer:**
- **IP Rate Limiting:** YES, counts attempts across different accounts from same IP
- **Account Lockout:** NO, each account has its own counter

Example for IP rate limiting:
```
IP 192.168.1.1 → 3 failed attempts on "alice"
IP 192.168.1.1 → 2 failed attempts on "bob"
Total from IP: 5 failed attempts → IP is rate limited
```

**Test verification:** `test_ip_rate_limiting_works_across_different_accounts`

### 4. How about if the user signed in 6 times with correct information?

**Answer:** **NO rate limiting triggered.** Successful logins do NOT count toward the login rate limit.

Why? Because login rate limiting only counts **failed** attempts. The code explicitly filters for `successful=False`:

```python
if _is_rate_limited(
    event_type=AuthenticationEvent.EventType.LOGIN,
    successful=False,  # Only counts failed attempts
    ...
):
```

**Test verification:** `test_successful_logins_do_not_trigger_rate_limit`
- Tested with 7 successful logins from same IP
- All 7 succeeded with no rate limiting

**Important exception for signup:** Signup rate limiting counts ALL attempts (both successful and failed) because it's designed to prevent mass account creation.

### 5. Where does it work? Sign in page? Sign up page?

**Answer:**

| Feature | Sign In Page | Sign Up Page |
|---------|-------------|--------------|
| **IP Rate Limiting** | ✅ YES<br>5 failed attempts / 15 min | ✅ YES<br>5 total attempts / 1 hour |
| **Account Lockout** | ✅ YES<br>5 failed attempts = 60 min lock | ❌ NO<br>(no account exists yet) |

**Sign In Page (`/accounts/login/`):**
- IP rate limiting: 5 failed logins per 15 minutes per IP
- Account lockout: 5 failed password attempts = account locked for 60 minutes
- Both mechanisms work together

**Sign Up Page (`/accounts/signup/`):**
- IP rate limiting: 5 signup attempts (successful or failed) per hour per IP
- No account lockout (doesn't make sense - account doesn't exist yet)

---

## Test Results Details

### Existing Tests (14 tests)

**SignupViewTests (4 tests):**
✅ test_signup_success_creates_user_and_logs_event
✅ test_signup_password_hashed_with_argon2
✅ test_signup_rejects_passwords_that_fail_validators
✅ test_signup_rate_limit_blocks_submission

**LoginViewTests (5 tests):**
✅ test_login_success_redirects_and_resets_failures
✅ test_login_with_email_identifier
✅ test_login_wrong_password_increments_failure
✅ test_login_rate_limit_blocks_attempt
✅ test_login_locks_account_after_threshold

**ProfileViewTests (2 tests):**
✅ test_profile_requires_login
✅ test_profile_update_persists_changes

**LogoutViewTests (2 tests):**
✅ test_logout_requires_post
✅ test_logout_clears_session

### New Scenario Tests (9 tests)

**RateLimitingScenariosTest (7 tests):**
✅ test_successful_logins_do_not_trigger_rate_limit
✅ test_ip_rate_limiting_works_across_different_accounts
✅ test_account_lockout_is_per_account_not_per_ip
✅ test_account_lockout_from_different_ips
✅ test_successful_login_resets_account_lockout_counter
✅ test_lockout_expires_after_60_minutes
✅ test_signup_rate_limiting_counts_all_attempts

**RateLimitingDatabaseTest (2 tests):**
✅ test_authentication_event_stores_all_required_fields
✅ test_user_model_lockout_fields

---

## Key Findings

### 1. Successful Logins Are NOT Rate Limited
- ✅ Verified: 7 consecutive successful logins from same IP all allowed
- Login rate limiting only counts **failed** attempts
- Prevents false positives for legitimate users

### 2. IP Rate Limiting Is Cross-Account
- ✅ Verified: 3 failures on alice + 2 failures on bob = 5 from IP
- 6th attempt blocked even with correct password
- Protects against distributed brute-force targeting multiple accounts

### 3. Account Lockout Is Independent Per Account
- ✅ Verified: Locking alice does NOT affect bob
- Each account maintains its own failed attempt counter
- Protects individual accounts from targeted attacks

### 4. Account Lockout Works Across IPs
- ✅ Verified: 5 failed attempts from 5 different IPs still locks account
- Cannot bypass lockout by changing IP addresses
- Prevents distributed attacks on single account

### 5. Successful Login Resets Counters
- ✅ Verified: Counter at 3 → successful login → counter reset to 0
- Prevents lockout from accumulating over long periods
- User-friendly: honest mistakes don't permanently affect account

### 6. Lockout Auto-Expires After 60 Minutes
- ✅ Verified: Account automatically unlocks after lockout period
- No manual intervention required
- Balances security with usability

### 7. Signup Rate Limiting Is More Restrictive
- ✅ Verified: Counts ALL attempts (successful + failed)
- Prevents mass account creation
- Longer window (1 hour vs 15 minutes)

---

## Security Verification

### IP Spoofing Protection
✅ Implementation uses `REMOTE_ADDR` (cannot be spoofed by client)
✅ Does NOT use `X-Forwarded-For` (prevents header spoofing attacks)
✅ Code location: `accounts/utils.py:30`

### Password Hashing
✅ Uses Argon2 algorithm (industry standard)
✅ Verified: All passwords start with "argon2"
✅ No plaintext passwords stored

### Audit Logging
✅ All authentication attempts logged in `AuthenticationEvent` table
✅ Includes: IP, timestamp, success/failure, reason
✅ Enables security monitoring and forensics

### Defense in Depth
✅ Two independent mechanisms (IP + account lockout)
✅ Cannot bypass one by circumventing the other
✅ Layered security approach

---

## Configuration Summary

### Rate Limiting Settings
```python
# accounts/views.py:29-37

# Signup
SIGNUP_RATE_LIMIT = 5          # attempts
SIGNUP_RATE_WINDOW = 1 hour    # time window

# Login
LOGIN_RATE_LIMIT = 5           # failed attempts
LOGIN_RATE_WINDOW = 15 minutes # time window

# Account Lockout
LOGIN_LOCK_THRESHOLD = 5       # failed password attempts
LOGIN_LOCK_DURATION = 60 minutes # lockout duration
```

### Database Tables
- `User` - Stores: failed_login_attempts, locked_until, last_failed_login_at
- `AuthenticationEvent` - Stores: All login/signup attempts with IP, timestamp, success/failure

---

## How to Run Tests

### Run all authentication tests:
```bash
python manage.py test accounts.tests -v 2
```

### Run scenario tests:
```bash
python manage.py test accounts.test_rate_limiting_scenarios -v 2
```

### Run all tests:
```bash
python manage.py test accounts -v 2
```

---

## Conclusion

✅ **All security mechanisms working as designed**
✅ **IP rate limiting protects against distributed attacks**
✅ **Account lockout protects individual accounts**
✅ **Successful logins do NOT trigger rate limits**
✅ **Works on both sign in and sign up pages**
✅ **Comprehensive test coverage (23/23 tests passing)**

The rate limiting and account lockout functionality is fully functional, well-tested, and provides robust protection against brute-force attacks while maintaining a good user experience for legitimate users.
