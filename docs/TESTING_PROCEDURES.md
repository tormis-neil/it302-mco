# Testing Procedures & QA Guide

## What It Is

This guide provides comprehensive testing procedures for the Brews & Chews café ordering system. It includes manual testing checklists, automated test execution, debugging strategies, and quality assurance guidelines to ensure all features work correctly before presentation or deployment.

## Testing Levels

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

## 1. Automated Testing

### Running Django Tests

**Run all tests**:
```bash
python manage.py test
```

**Run specific app tests**:
```bash
python manage.py test accounts
python manage.py test menu
python manage.py test orders
```

**Run specific test class**:
```bash
python manage.py test accounts.tests.SignupViewTests
python manage.py test accounts.tests.LoginViewTests
python manage.py test accounts.test_encryption.EncryptionUtilitiesTestCase
```

**Run specific test method**:
```bash
python manage.py test accounts.tests.SignupViewTests.test_password_hashed_with_argon2
```

**Run with verbose output**:
```bash
python manage.py test --verbosity=2
```

**Run with code coverage**:
```bash
# Install coverage
pip install coverage

# Run tests with coverage
coverage run --source='.' manage.py test

# View coverage report
coverage report

# Generate HTML report
coverage html
# Open htmlcov/index.html in browser
```

### Test File Locations

| App | Test File | Description |
|-----|-----------|-------------|
| accounts | `accounts/tests.py` | Authentication, profile tests |
| accounts | `accounts/test_encryption.py` | Email encryption tests |
| menu | `menu/tests.py` | Menu display tests |
| orders | `orders/tests.py` | Cart/order tests (minimal) |

### Accounts App Tests

**Files**:
- `accounts/tests.py` - Main authentication tests
- `accounts/test_encryption.py` - Email encryption tests

**Test Classes** (accounts/tests.py):
- `SignupViewTests`: User registration
- `LoginViewTests`: User authentication
- `ProfileViewTests`: Profile management
- `LogoutViewTests`: Logout functionality

**Test Classes** (accounts/test_encryption.py):
- `EncryptionUtilitiesTestCase`: Encryption/decryption utilities
- `UserModelEncryptionTestCase`: User model with encryption
- `SignupFormEncryptionTestCase`: Signup with encrypted emails
- `LoginFormEncryptionTestCase`: Login with encrypted emails
- `LoginViewEncryptionTestCase`: Login view integration
- `SignupViewEncryptionTestCase`: Signup view integration

**Key Tests**:

**1. Valid Signup**:
```python
def test_valid_signup(self):
    response = self.client.post('/accounts/signup/', {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'SecurePass123!',
        'confirm_password': 'SecurePass123!',
    })
    # Should create user and redirect
    self.assertEqual(response.status_code, 302)
    self.assertTrue(User.objects.filter(username='testuser').exists())
```

**2. Duplicate Username**:
```python
def test_duplicate_username(self):
    User.objects.create_user('alice', 'alice@example.com', 'Pass123!')
    response = self.client.post('/accounts/signup/', {
        'username': 'alice',
        'email': 'different@example.com',
        'password': 'SecurePass123!',
        'confirm_password': 'SecurePass123!',
    })
    # Should reject with error
    self.assertContains(response, 'already taken')
```

**3. Weak Password**:
```python
def test_weak_password(self):
    response = self.client.post('/accounts/signup/', {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'short',
        'confirm_password': 'short',
    })
    # Should reject with validation errors
    self.assertContains(response, 'at least 12 characters')
```

**4. Valid Login**:
```python
def test_valid_login(self):
    user = User.objects.create_user('alice', 'alice@example.com', 'Pass123!')
    response = self.client.post('/accounts/login/', {
        'identifier': 'alice',
        'password': 'Pass123!',
    })
    # Should log in and redirect
    self.assertEqual(response.status_code, 302)
    self.assertTrue(response.wsgi_request.user.is_authenticated)
```

**5. Email Encryption**:
```python
def test_email_encryption(self):
    user = User.objects.create_user('bob', 'bob@example.com', 'Pass123!')
    # Email should be encrypted
    self.assertIsNotNone(user.encrypted_email)
    self.assertIsNotNone(user.email_digest)
    # Decryption should work
    self.assertEqual(user.email_decrypted, 'bob@example.com')
```

### Running Encryption Tests

**Run encryption test suite**:
```bash
python manage.py test accounts.test_encryption
```

**Run specific encryption tests**:
```bash
# Test encryption utilities
python manage.py test accounts.test_encryption.EncryptionUtilitiesTestCase

# Test user model encryption
python manage.py test accounts.test_encryption.UserModelEncryptionTestCase

# Test signup/login with encryption
python manage.py test accounts.test_encryption.SignupFormEncryptionTestCase
python manage.py test accounts.test_encryption.LoginFormEncryptionTestCase
```

**What it tests**:
- Key generation (32 bytes, base64-encoded)
- Email encryption/decryption roundtrip
- Digest generation (SHA-256)
- Case insensitivity (TEST@EXAMPLE.COM == test@example.com)
- Unique nonces (same email → different ciphertext)
- Error handling (missing key, corrupted data, invalid data)
- User model integration (auto-encrypt on save)
- Form validation (duplicate email detection via digest)
- Login functionality (find user by encrypted email)

**Expected output**:
```
Found 20 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
....................
----------------------------------------------------------------------
Ran 20 tests in 1.234s

OK
Destroying test database for alias 'default'...
```

### Test Database

**Important**: Tests use a separate test database.

**Test database lifecycle**:
1. `python manage.py test` starts
2. Test database created: `test_db.sqlite3`
3. Migrations applied
4. Tests run
5. Test database deleted

**Benefits**:
- Tests don't affect development database
- Tests start with clean slate
- Fast (in-memory database possible)

**Test database settings**:
```python
# In tests, Django automatically uses:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # Or test_db.sqlite3
    }
}
```

## 2. Manual Testing Procedures

### Pre-Test Setup

**1. Ensure Clean State**:
```bash
# Delete existing database
rm db.sqlite3

# Run migrations
python manage.py migrate

# Verify server starts
python manage.py runserver
```

**2. Open Browser Tools**:
- Chrome/Firefox DevTools (F12)
- Network tab (monitor requests)
- Console tab (watch for JavaScript errors)

### Feature Testing Checklist

#### Signup Feature

**Test Case 1: Valid Registration**
- [ ] Navigate to `/accounts/signup/`
- [ ] Enter valid data:
  - Username: `testuser1`
  - Email: `test1@example.com`
  - Password: `SecurePass123!`
  - Confirm: `SecurePass123!`
- [ ] Click "Sign Up"
- [ ] **Expected**: Redirected to `/menu/`, logged in
- [ ] **Verify**:
  - [ ] Navbar shows username "testuser1"
  - [ ] Can access `/accounts/profile/`
  - [ ] Email encrypted in database:
    ```bash
    python manage.py shell
    from accounts.models import User
    u = User.objects.get(username='testuser1')
    print(u.encrypted_email)  # Should show bytes
    print(u.email_decrypted)  # Should show test1@example.com
    ```

**Test Case 2: Duplicate Username**
- [ ] Try registering with `testuser1` again
- [ ] **Expected**: Error "That username is already taken."
- [ ] **Verify**: Form redisplayed, no new user created

**Test Case 3: Duplicate Email**
- [ ] Try registering with `test1@example.com` again (different username)
- [ ] **Expected**: Error "That email is already registered."
- [ ] **Verify**: Works even with different case (`TEST1@example.com`)

**Test Case 4: Password Strength**
- [ ] Try each weak password:
  - [ ] `short` → "at least 12 characters"
  - [ ] `password123` → "too common"
  - [ ] `longpassword` → "uppercase letter", "special character"
  - [ ] `12345678901234` → "entirely numeric"
- [ ] **Expected**: Specific error for each validation failure

**Test Case 5: Password Mismatch**
- [ ] Password: `SecurePass123!`
- [ ] Confirm: `DifferentPass123!`
- [ ] **Expected**: Error "Passwords do not match."

**Test Case 6: Invalid Username Format**
- [ ] Try: `ab` (too short) → Error
- [ ] Try: `user@name` (invalid char) → Error
- [ ] Try: `this_is_a_very_long_username_over_thirty_chars` → Error

**Test Case 7: Profile Auto-Creation**
- [ ] Register new user
- [ ] Visit `/accounts/profile/`
- [ ] **Expected**: Profile exists with display_name = username

**Test Case 8: Audit Logging**
- [ ] Register new user
- [ ] Check database:
  ```python
  from accounts.models import AuthenticationEvent
  events = AuthenticationEvent.objects.filter(event_type='signup', successful=True)
  print(events.latest('created_at'))
  ```
- [ ] **Expected**: Event logged with IP, user agent, timestamp

#### Login Feature

**Test Case 1: Valid Login (Username)**
- [ ] Navigate to `/accounts/login/`
- [ ] Enter:
  - Identifier: `testuser1`
  - Password: `SecurePass123!`
- [ ] Click "Log In"
- [ ] **Expected**: Redirected to `/menu/`, logged in
- [ ] **Verify**: Navbar shows username

**Test Case 2: Valid Login (Email)**
- [ ] Identifier: `test1@example.com`
- [ ] Password: `SecurePass123!`
- [ ] **Expected**: Login succeeds (same as username)

**Test Case 3: Invalid Username**
- [ ] Identifier: `nonexistent`
- [ ] Password: `anypassword`
- [ ] **Expected**: Error "Invalid username or password."

**Test Case 4: Wrong Password**
- [ ] Identifier: `testuser1`
- [ ] Password: `wrongpassword`
- [ ] **Expected**: Error "Invalid username or password." (same message as invalid username)

**Test Case 5: Case Insensitivity**
- [ ] Identifier: `TESTUSER1` (uppercase)
- [ ] Password: `SecurePass123!`
- [ ] **Expected**: Login succeeds

**Test Case 6: Email Case Insensitivity**
- [ ] Identifier: `TEST1@EXAMPLE.COM`
- [ ] Password: `SecurePass123!`
- [ ] **Expected**: Login succeeds

**Test Case 7: Session Persistence**
- [ ] Log in successfully
- [ ] Visit `/accounts/profile/`
- [ ] **Expected**: Page loads (no redirect to login)
- [ ] Refresh page
- [ ] **Expected**: Still logged in

**Test Case 8: Logout**
- [ ] Click "Log Out" in navbar
- [ ] **Expected**: Redirected to home, navbar shows "Log In"
- [ ] Try accessing `/accounts/profile/`
- [ ] **Expected**: Redirected to login page

**Test Case 9: Empty Form**
- [ ] Leave both fields blank
- [ ] Click "Log In"
- [ ] **Expected**: Validation errors shown

**Test Case 10: CSRF Protection**
- [ ] Open browser DevTools → Network tab
- [ ] Submit login form
- [ ] Check request payload
- [ ] **Expected**: Contains `csrfmiddlewaretoken`

#### Profile Feature

**Test Case 1: View Profile**
- [ ] Log in
- [ ] Visit `/accounts/profile/`
- [ ] **Expected**: Shows username, email, join date, last login

**Test Case 2: Update Profile Info**
- [ ] Update:
  - Display Name: "Test User"
  - Phone: "+1234567890"
  - Favorite Drink: "Cappuccino"
  - Bio: "Coffee enthusiast"
- [ ] Click "Save Profile"
- [ ] **Expected**: Success message, data saved
- [ ] Refresh page
- [ ] **Expected**: Updated data still shown

**Test Case 3: Change Username**
- [ ] New Username: `newusername`
- [ ] Password: `SecurePass123!`
- [ ] Click "Change Username"
- [ ] **Expected**: Success message
- [ ] **Verify**: Navbar shows "newusername"
- [ ] Log out and log in with new username
- [ ] **Expected**: Login succeeds

**Test Case 4: Change Username (Wrong Password)**
- [ ] New Username: `another`
- [ ] Password: `wrongpassword`
- [ ] **Expected**: Error "Incorrect password."

**Test Case 5: Change Password**
- [ ] Current Password: `SecurePass123!`
- [ ] New Password: `NewSecurePass456!`
- [ ] Confirm: `NewSecurePass456!`
- [ ] Click "Change Password"
- [ ] **Expected**: Success message, still logged in
- [ ] Log out and log in with new password
- [ ] **Expected**: Login succeeds

**Test Case 6: Delete Account**
- [ ] Click "Delete Account" button
- [ ] Enter password in modal
- [ ] Confirm deletion
- [ ] **Expected**: Redirected to home, logged out
- [ ] Try logging in with deleted username
- [ ] **Expected**: "Invalid username or password."

#### Menu Feature

**Test Case 1: View Menu**
- [ ] Log in
- [ ] Visit `/menu/`
- [ ] **Expected**: Categories and items displayed
- [ ] **Verify**: Images load, prices shown

**Test Case 2: Category Filtering** (if implemented)
- [ ] Click category filter
- [ ] **Expected**: Only items from that category shown

**Test Case 3: Item Details** (if implemented)
- [ ] Click menu item
- [ ] **Expected**: Details modal or page shown

#### Cart & Orders (UI Only)

**Note**: Cart/Order backend not implemented yet (Phase 2).

**Test Case 1: View Cart**
- [ ] Click "Cart" in navbar
- [ ] **Expected**: Placeholder cart page shown
- [ ] **Verify**: Shows sample data (not functional)

**Test Case 2: Checkout Flow**
- [ ] Navigate to checkout
- [ ] **Expected**: Checkout form shown
- [ ] **Verify**: Form display only (not functional)

**Test Case 3: Order History**
- [ ] Visit `/orders/history/`
- [ ] **Expected**: Sample orders shown
- [ ] **Verify**: Display only (not real orders)

### Browser Compatibility Testing

**Test on multiple browsers**:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Edge (latest)
- [ ] Safari (if on Mac)

**Test each browser**:
- [ ] Signup works
- [ ] Login works
- [ ] Profile works
- [ ] Menu displays correctly
- [ ] CSS renders correctly
- [ ] JavaScript works

### Mobile/Responsive Testing

**Test on different screen sizes**:
- [ ] Desktop (1920×1080)
- [ ] Laptop (1366×768)
- [ ] Tablet (768×1024)
- [ ] Mobile (375×667)

**For each size**:
- [ ] Navigation menu works
- [ ] Forms are usable
- [ ] Text is readable
- [ ] Images scale properly
- [ ] No horizontal scrolling

**Tools**:
- Chrome DevTools → Device Toolbar (Ctrl+Shift+M)
- Firefox Responsive Design Mode (Ctrl+Shift+M)

## 3. Security Testing

### Manual Security Tests

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
2. Open new tab, paste this HTML:
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

**Test 5: Password Brute Force**
```
1. Try logging in with wrong password 10 times
2. Check audit logs:
   from accounts.models import AuthenticationEvent
   failed = AuthenticationEvent.objects.filter(
       username_submitted='testuser1',
       successful=False
   ).count()
Expected: All attempts logged
```

**Test 6: Email Enumeration**
```
1. Try signing up with existing email
2. Note error message: "That email is already registered."
3. Try signing up with non-existing email + duplicate username
4. Note error message: "That username is already taken."
Expected: Different errors, but acceptable (email uniqueness must be enforced)
```

**Test 7: Username Enumeration via Login**
```
1. Try logging in with nonexistent username
   Error: "Invalid username or password."
2. Try logging in with existing username, wrong password
   Error: "Invalid username or password."
Expected: Same error message (prevents enumeration)
```

### Penetration Testing Tools

**Recommended tools** (use responsibly, only on your own system):

**1. OWASP ZAP** (Zed Attack Proxy)
```bash
# Install and run
# Point browser to http://127.0.0.1:8000
# ZAP will intercept and test for vulnerabilities
```

**2. Burp Suite Community**
```bash
# Intercept HTTP requests
# Modify payloads to test injection
# Analyze responses for info leakage
```

**3. Nikto** (Web server scanner)
```bash
nikto -h http://127.0.0.1:8000
```

**4. SQLMap** (SQL injection testing)
```bash
# Only test on your own system!
sqlmap -u "http://127.0.0.1:8000/accounts/login/" --forms
```

**Warning**: Only use these tools on systems you own or have permission to test!

## 4. Performance Testing

### Page Load Time

**Manual measurement**:
1. Open DevTools → Network tab
2. Load page
3. Check "Load" time at bottom
4. **Target**: < 2 seconds for most pages

**Key pages to test**:
- [ ] Home page: `/`
- [ ] Signup: `/accounts/signup/`
- [ ] Login: `/accounts/login/`
- [ ] Profile: `/accounts/profile/`
- [ ] Menu: `/menu/`

### Database Query Optimization

**Enable query logging** (in development):
```python
# brewschews/settings.py (temporary)
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

**Then visit pages and check console for queries**.

**Look for**:
- N+1 query problems (many queries in loop)
- Missing indexes (slow WHERE clauses)
- Unnecessary JOINs

**Example optimization**:
```python
# Bad: N+1 queries
users = User.objects.all()
for user in users:
    print(user.profile.display_name)  # Query per user!

# Good: 1 query with JOIN
users = User.objects.select_related('profile').all()
for user in users:
    print(user.profile.display_name)  # No extra queries
```

### Load Testing (Future)

**Tools** (for production):
- Apache JMeter
- Locust
- wrk

**Example test**:
- 100 concurrent users
- Each user: signup → login → browse menu → logout
- Duration: 5 minutes
- Measure: Response times, error rates, throughput

## 5. Debugging Procedures

### Django Debug Toolbar (Recommended)

**Installation**:
```bash
pip install django-debug-toolbar
```

**Configuration** (`brewschews/settings.py`):
```python
INSTALLED_APPS = [
    # ...
    'debug_toolbar',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    # ...
]

INTERNAL_IPS = ['127.0.0.1']
```

**URL config** (`brewschews/urls.py`):
```python
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
```

**Features**:
- SQL queries panel (view all queries, execution time)
- Templates panel (which templates rendered)
- Signals panel (Django signals fired)
- Logging panel (log messages)
- Request/Response headers

### Common Issues & Solutions

#### Issue 1: "No such table" errors

**Symptom**: `django.db.utils.OperationalError: no such table: accounts_user`

**Cause**: Migrations not applied.

**Solution**:
```bash
python manage.py migrate
```

**Verify**:
```bash
python manage.py showmigrations
# All migrations should have [X] (applied)
```

#### Issue 2: Email encryption errors

**Symptom**: `MissingEncryptionKeyError` or `DecryptionFailedError`

**Cause**: Missing or invalid encryption key.

**Solution**:
```bash
# Generate new key
python -c "from accounts.encryption import generate_encryption_key; print(generate_encryption_key())"

# Add to .env file
echo "ACCOUNT_EMAIL_ENCRYPTION_KEY=generated_key_here" >> .env

# Restart server
```

**Verify**:
```python
python manage.py shell
from accounts.encryption import test_encryption_roundtrip
test_encryption_roundtrip()
# Should print "Roundtrip successful: True"
```

#### Issue 3: CSRF verification failed

**Symptom**: `403 Forbidden: CSRF verification failed`

**Cause**: Missing CSRF token in form or cookie.

**Solution**:
- Ensure `{% csrf_token %}` in all POST forms
- Check CSRF middleware enabled (`brewschews/settings.py:127`)
- Check cookies enabled in browser
- Clear browser cookies and retry

**Debug**:
```python
# Check CSRF middleware
from django.conf import settings
print('django.middleware.csrf.CsrfViewMiddleware' in settings.MIDDLEWARE)
# Should print: True
```

#### Issue 4: Static files not loading

**Symptom**: CSS/JavaScript not applied, 404 errors in console.

**Cause**: Static files not collected or STATIC_URL misconfigured.

**Solution** (development):
```python
# Ensure in settings.py:
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Ensure in templates:
{% load static %}
<link rel="stylesheet" href="{% static 'css/style.css' %}">
```

**Solution** (production):
```bash
python manage.py collectstatic
```

#### Issue 5: Import errors

**Symptom**: `ModuleNotFoundError: No module named 'django'`

**Cause**: Virtual environment not activated.

**Solution**:
```bash
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# Verify
python -c "import django; print(django.get_version())"
```

#### Issue 6: Port already in use

**Symptom**: `Error: That port is already in use.`

**Cause**: Server already running or port used by another process.

**Solution**:
```bash
# Use different port
python manage.py runserver 8080

# Or kill existing process
# Windows
netstat -ano | findstr :8000
taskkill /PID <pid> /F

# macOS/Linux
lsof -i :8000
kill <pid>
```

#### Issue 7: Database locked

**Symptom**: `database is locked` (SQLite only)

**Cause**: Multiple processes accessing database simultaneously.

**Solution**:
- Close other Django shells
- Stop background tasks
- Restart server
- If persists, delete and recreate database:
  ```bash
  rm db.sqlite3
  python manage.py migrate
  ```

## 6. Pre-Presentation Checklist

### Code Quality

- [ ] All tests passing: `python manage.py test`
- [ ] No console errors in browser DevTools
- [ ] No Python warnings when running server
- [ ] Code follows PEP 8 style (run `flake8` or `black`)
- [ ] No hardcoded secrets (check .env usage)
- [ ] Comments explain complex logic
- [ ] README.md updated with setup instructions

### Feature Completeness

**Implemented Features**:
- [ ] User signup works (valid data creates account)
- [ ] User login works (username and email)
- [ ] Profile view shows user info
- [ ] Profile edit saves changes
- [ ] Username change works
- [ ] Password change works
- [ ] Account deletion works
- [ ] Logout works
- [ ] Menu displays items
- [ ] Password strength validated
- [ ] Email encrypted in database
- [ ] Audit logging records events

**UI-Only Features** (acknowledge limitations):
- [ ] Cart shows placeholder data
- [ ] Checkout shows form (not functional)
- [ ] Order history shows samples (not real orders)

### Security Verification

- [ ] Passwords hashed with Argon2
- [ ] Emails encrypted with AES-256-GCM
- [ ] CSRF protection enabled
- [ ] Session cookies HttpOnly
- [ ] Generic error messages (no info leak)
- [ ] Input validation on all forms
- [ ] SQL injection prevented (ORM)
- [ ] XSS prevented (template auto-escape)

### Database Verification

- [ ] Migrations applied: `python manage.py showmigrations`
- [ ] Sample menu data loaded
- [ ] Test accounts created (for demo)
- [ ] Email encryption working
- [ ] Profile auto-creation working

### Documentation Review

- [ ] README.md accurate
- [ ] docs/database-plan.md reviewed
- [ ] Feature documentation complete (this docs folder)
- [ ] Comments in code explain "why" not just "what"

### Demo Preparation

**Create demo accounts**:
```python
python manage.py shell

from accounts.models import User

# Admin account (for demo)
User.objects.create_superuser(
    username='admin',
    email='admin@brewschews.com',
    password='AdminPass123!'
)

# Regular user account
User.objects.create_user(
    username='demo',
    email='demo@brewschews.com',
    password='DemoPass123!'
)

# Add profile data
demo = User.objects.get(username='demo')
demo.profile.display_name = 'Demo User'
demo.profile.phone_number = '+1234567890'
demo.profile.favorite_drink = 'Cappuccino'
demo.profile.save()
```

**Test demo flow**:
1. [ ] Show signup (live registration)
2. [ ] Show login (with demo account)
3. [ ] Show profile (with filled data)
4. [ ] Show menu browsing
5. [ ] Show email encryption (Django shell demo)
6. [ ] Show audit logs (Django shell demo)

### Backup

**Before presentation**:
```bash
# Backup database
cp db.sqlite3 db.sqlite3.backup

# Backup .env file
cp .env .env.backup

# Create git tag
git tag -a presentation-ready -m "Ready for presentation"
git push origin presentation-ready
```

## 7. Continuous Testing

### Test-Driven Development (TDD)

**Workflow**:
1. Write test for new feature (test fails - RED)
2. Write minimum code to pass test (GREEN)
3. Refactor code (REFACTOR)
4. Repeat

**Example**:
```python
# 1. Write test first (RED)
def test_username_change_requires_password(self):
    response = self.client.post('/accounts/profile/change-username/', {
        'new_username': 'newname',
        'password': '',  # Empty password
    })
    self.assertContains(response, 'Incorrect password')

# 2. Implement feature (GREEN)
# Add password check in view

# 3. Refactor (REFACTOR)
# Extract password check to helper function
```

### Regression Testing

**After each change**:
```bash
# Run all tests
python manage.py test

# Run tests for changed app
python manage.py test accounts
```

**Manual regression checklist** (quick smoke test):
- [ ] Can signup
- [ ] Can login
- [ ] Can view profile
- [ ] Can view menu

### CI/CD Integration (Future)

**GitHub Actions** (`.github/workflows/django-tests.yml`):
```yaml
name: Django Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    - name: Run migrations
      run: python manage.py migrate
    - name: Run tests
      run: python manage.py test
```

**Benefits**:
- Automatic test execution on every commit
- Prevents merging broken code
- Ensures tests pass on clean environment

## 8. Testing Best Practices

### Do's

✓ **Write tests for new features** before merging
✓ **Run tests before committing** changes
✓ **Test edge cases** (empty input, very long input, special characters)
✓ **Test error handling** (what happens when things go wrong?)
✓ **Use descriptive test names** (`test_signup_rejects_duplicate_email`)
✓ **Keep tests independent** (don't rely on test execution order)
✓ **Use test fixtures** for common setup (Django TestCase)
✓ **Mock external services** (email, payment gateways)
✓ **Test security** (injection, XSS, CSRF)
✓ **Document manual test procedures** (this guide!)

### Don'ts

✗ **Don't skip tests** because they're "too slow"
✗ **Don't test implementation details** (test behavior, not internals)
✗ **Don't write tests that depend on each other**
✗ **Don't commit commented-out tests** (fix or delete them)
✗ **Don't test Django's built-in functionality** (trust the framework)
✗ **Don't use production database** for testing
✗ **Don't hardcode test data** (use factories or fixtures)
✗ **Don't ignore failing tests** ("I'll fix it later")

## Summary Checklists

### Quick Smoke Test (5 minutes)

- [ ] Server starts without errors
- [ ] Home page loads
- [ ] Can signup new user
- [ ] Can login with new user
- [ ] Can view profile
- [ ] Can view menu
- [ ] Can logout

### Full Manual Test (30 minutes)

- [ ] All signup test cases (8 cases)
- [ ] All login test cases (10 cases)
- [ ] All profile test cases (6 cases)
- [ ] Menu display works
- [ ] Security tests pass (7 tests)
- [ ] Browser compatibility (3+ browsers)
- [ ] Responsive design (4 screen sizes)

### Automated Test Suite (2 minutes)

```bash
python manage.py test --verbosity=2
```

- [ ] All tests pass
- [ ] No warnings
- [ ] Coverage > 80% (if tracking)

### Pre-Deploy Checklist

- [ ] All automated tests pass
- [ ] Manual smoke test completes
- [ ] Security checklist reviewed
- [ ] Database migrations applied
- [ ] Static files collected
- [ ] .env configured correctly
- [ ] Demo accounts created
- [ ] Backup created

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
