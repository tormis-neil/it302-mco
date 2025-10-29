# Brews & Chews – Online Café Ordering System

A Django-based web application for managing café orders with secure user authentication, email encryption, and profile management.

---

## 🎯 **Project Status**

### ✅ **Fully Implemented Features**

**Authentication & Security**
- User signup with email validation and strong password requirements
- Login using username OR email
- Password strength validation (12+ chars, uppercase, numbers, special characters)
- Argon2 password hashing (memory-hard, GPU-resistant)
- AES-256-GCM email encryption for PII protection
- CSRF protection and secure session management
- Audit logging for all authentication events

**User Profile Management**
- View account information (username, email, join date, last login)
- Edit profile details (display name, phone number, favorite drink, bio)
- Change username with password confirmation
- Change password with current password verification
- Delete account with confirmation modal
- Automatic profile creation on signup

**Menu System**
- Browse café menu items organized by categories
- View item descriptions and prices in Philippine Pesos (₱)
- Responsive grid layout
- Query optimization (prefetch_related) for performance
- Category-based organization (Espresso, Brewed Coffee, Bakery, etc.)

**Security Implementation**
- Email encryption at rest (AES-256-GCM)
- SHA-256 email digest for lookups
- CSRF token validation
- HttpOnly and SameSite cookies
- Generic error messages (prevent username enumeration)
- Input validation and sanitization

### 🎨 **UI-Only Features (Visual Prototypes)**
These features have working interfaces but no backend functionality yet:
- Shopping Cart (shows placeholder data)
- Checkout Flow (form display only)
- Order History (shows sample orders)

### ❌ **Not Implemented**
- Add to cart functionality
- Real order processing
- Payment integration
- Email notifications
- Password reset via email
- Admin/staff dashboard
- Rate limiting (removed per feedback)

---

## 🛠️ **Tech Stack**

- **Backend:** Django 4.2+
- **Database:** SQLite3 (development), PostgreSQL/MySQL ready for production
- **Authentication:** Custom User model with Django's auth system
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Password Hashing:** Argon2 (102,400 iterations, 100 MB memory)
- **Email Encryption:** AES-256-GCM with SHA-256 digest
- **Security:** Audit logging, CSRF protection, HttpOnly cookies

---

## 📋 **Prerequisites**

Before setting up the project, ensure you have:

- **Python 3.8+** installed ([Download Python](https://www.python.org/downloads/))
- **pip** (comes with Python)
- **Git** installed ([Download Git](https://git-scm.com/downloads))
- A code editor (VS Code, PyCharm, etc.)

**Check your Python version:**
```bash
python --version
# or
python3 --version
# Should show: Python 3.8.0 or higher
```

---

## 🚀 **Quick Start for Team Members**

### **Step 1: Clone the Repository**

```bash
# Clone the project
git clone https://github.com/tormis-neil/it302-mco.git
cd it302-mco
```

### **Step 2: Create a Virtual Environment**

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**✅ You should see `(.venv)` appear at the start of your terminal prompt**

---

### **Step 3: Install Dependencies**

```bash
pip install -r requirements.txt
```

**This installs:**
- Django 4.2+
- argon2-cffi (password hashing)
- cryptography (email encryption)
- python-dotenv (environment variables)

**If installation fails:**
```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Then retry
pip install -r requirements.txt
```

---

### **Step 4: Configure Environment Variables** ⚙️

**IMPORTANT:** This step is **REQUIRED** for the application to run.

Create a `.env` file in the project root:

**Windows:**
```cmd
copy .env.example .env
```

**macOS/Linux:**
```bash
cp .env.example .env
```

**Edit the `.env` file** and configure the following:

```env
# Development Mode (REQUIRED)
DJANGO_DEBUG=1

# Secret Key (Optional - will auto-generate if empty)
DJANGO_SECRET_KEY=

# Allowed Hosts
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DJANGO_DB_NAME=db.sqlite3

# Email Encryption Key (Optional - will auto-generate with warning)
ACCOUNT_EMAIL_ENCRYPTION_KEY=
```

**Configuration Details:**

1. **DJANGO_DEBUG=1** (REQUIRED)
   - Must be set to `1` for development mode
   - Enables detailed error pages and auto-generates SECRET_KEY
   - Without this, you'll get `ImproperlyConfigured` error

2. **DJANGO_SECRET_KEY** (Optional)
   - Can be left empty for development (auto-generates with warning)
   - For production, generate a key:
     ```bash
     python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
     ```

3. **ACCOUNT_EMAIL_ENCRYPTION_KEY** (Optional)
   - Used for AES-256-GCM email encryption
   - Can be left empty (auto-derives from SECRET_KEY with warning)
   - For proper setup, generate a key:
     ```bash
     python -c "from accounts.encryption import generate_encryption_key; print(generate_encryption_key())"
     ```
   - Copy the output and paste into `.env` file

**Example `.env` for Development:**
```env
DJANGO_DEBUG=1
DJANGO_SECRET_KEY=
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_DB_NAME=db.sqlite3
ACCOUNT_EMAIL_ENCRYPTION_KEY=
```

**⚠️ CRITICAL NOTES:**
- **NEVER commit `.env` to Git** (already in `.gitignore`)
- Each team member should have their own `.env` file
- Production environment should use different keys
- Back up your encryption key - if lost, encrypted emails cannot be recovered!

---

### **Step 5: Run Database Migrations**

```bash
python manage.py migrate
```

**This will:**
- ✅ Create the SQLite database (`db.sqlite3`)
- ✅ Set up all required tables (User, Profile, Menu, Orders, etc.)
- ✅ Encrypt user email fields (AES-256-GCM migration)
- ✅ Populate the menu with sample coffee/food items

**Expected output:**
```
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying accounts.0001_initial... OK
  Applying accounts.0002_add_email_encryption_fields... OK
  Applying accounts.0003_encrypt_existing_emails... OK
  Applying accounts.0004_remove_security_fields... OK
  Applying menu.0001_initial... OK
  Applying menu.0002_seed_menu... OK
  Applying orders.0001_initial... OK
  ...
```

**If you see warnings about encryption key:**
```
⚠️  WARNING: Using derived encryption key from SECRET_KEY
   For production, set ACCOUNT_EMAIL_ENCRYPTION_KEY explicitly!
```
This is normal for development. For production, generate and set a proper key.

---

### **Step 6: Create a Test Account (Optional)**

```bash
python manage.py shell
```

```python
from accounts.models import User

# Create a test user
user = User.objects.create_user(
    username='testuser',
    email='test@example.com',
    password='TestPass123!'
)

# Verify email encryption
print(f"Email encrypted: {user.encrypted_email is not None}")  # True
print(f"Email decrypted: {user.email_decrypted}")  # test@example.com

# Exit shell
exit()
```

---

### **Step 7: Start the Development Server**

```bash
python manage.py runserver
```

**You should see:**
```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
October 29, 2025 - 12:00:00
Django version 4.2.x, using settings 'brewschews.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL+C.
```

**⚠️ If you see warnings:**
```
⚠️  WARNING: Using auto-generated SECRET_KEY for development only!
⚠️  WARNING: Using derived encryption key from SECRET_KEY
```
These are **normal for development**. Ignore them or configure proper keys in `.env`.

---

### **Step 8: Access the Website**

Open your web browser and visit:
```
http://127.0.0.1:8000/
```

**✅ You should see the Brews & Chews home page!**

**Try it out:**
1. Click "Sign Up" → Create an account
2. Fill in username, email, password (12+ chars, uppercase, number, special char)
3. Submit → Auto-logged in, redirected to menu
4. Browse menu items (Espresso, Brewed Coffee, etc.)
5. Click your username → View/edit profile
6. Try changing username/password
7. Log out → Log back in with new credentials

---

## 🧪 **Running Tests**

Verify everything works correctly:

**Run all tests:**
```bash
python manage.py test
```

**Run specific app tests:**
```bash
# Accounts tests (signup, login, profile, encryption)
python manage.py test accounts

# Menu tests
python manage.py test menu

# Orders tests
python manage.py test orders
```

**Expected output:**
```
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
........................
----------------------------------------------------------------------
Ran 24 tests in 3.456s

OK
Destroying test database for alias 'default'...
```

**Test email encryption:**
```bash
python accounts/test_encryption.py
```

**Expected output:**
```
=== Email Encryption Test ===
Original email: test@example.com
Encrypted (base64): ABC123...
Encrypted size: 48 bytes
SHA-256 digest: b4c9a289323b21a01c3e940f150eb9b8c542587f1abfd8f0e1cc1ffc5e475514
Decrypted email: test@example.com
Roundtrip successful: True
```

---

## 📚 **Documentation**

Comprehensive technical documentation is available in the `docs/` folder:

### **Feature Documentation**
- **[SIGNUP_FEATURE.md](docs/SIGNUP_FEATURE.md)** - User registration system
- **[LOGIN_FEATURE.md](docs/LOGIN_FEATURE.md)** - Authentication system
- **[PROFILE_MANAGEMENT.md](docs/PROFILE_MANAGEMENT.md)** - User profile features
- **[MENU_SYSTEM.md](docs/MENU_SYSTEM.md)** - Menu display system

### **Technical Documentation**
- **[DATABASE_ARCHITECTURE.md](docs/DATABASE_ARCHITECTURE.md)** - Data models and relationships
- **[SECURITY_IMPLEMENTATION.md](docs/SECURITY_IMPLEMENTATION.md)** - Security measures
- **[TESTING_PROCEDURES.md](docs/TESTING_PROCEDURES.md)** - QA and testing guide

Each document includes:
- What it is (overview)
- How it works (step-by-step)
- Key Q&A (common questions)
- Code references (file:line)
- Edge cases
- Testing procedures
- Debugging guides

---

## 🔧 **Important Configurations**

### **Email Encryption Setup**

The system encrypts user email addresses at rest using AES-256-GCM.

**Generate encryption key:**
```bash
python -c "from accounts.encryption import generate_encryption_key; print(generate_encryption_key())"
```

**Add to `.env`:**
```env
ACCOUNT_EMAIL_ENCRYPTION_KEY=generated_key_here
```

**Test encryption:**
```bash
python manage.py shell
```
```python
from accounts.encryption import test_encryption_roundtrip
test_encryption_roundtrip("test@example.com")
# Should print: Roundtrip successful: True
```

### **Password Hashing Configuration**

Passwords are hashed using Argon2 with these parameters:
- Algorithm: Argon2id (hybrid mode)
- Memory: 102,400 KB (~100 MB)
- Iterations: 2
- Parallelism: 8 threads
- Hashing time: ~0.5 seconds

**No additional configuration needed** - works out of the box.

### **Database Configuration**

**Development (SQLite):**
- Default: `db.sqlite3` in project root
- Auto-created on `python manage.py migrate`

**Production (PostgreSQL example):**
Update `brewschews/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'brewschews_db',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### **Static Files Configuration**

**Development:**
```bash
# Static files served automatically by Django
# No additional setup needed
```

**Production:**
```bash
# Collect static files
python manage.py collectstatic

# Configure web server (nginx, Apache) to serve /static/
```

---

## 🛠️ **Common Issues & Solutions**

### **Issue 1: "ModuleNotFoundError: No module named 'django'"**

**Cause:** Virtual environment not activated

**Solution:**
```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows Command Prompt
.venv\Scripts\activate.bat

# macOS/Linux
source .venv/bin/activate
```

**Verify:**
```bash
which python  # Should show path to .venv/bin/python
pip list | grep Django  # Should show Django version
```

---

### **Issue 2: "ImproperlyConfigured: DJANGO_SECRET_KEY environment variable is required!"**

**Cause:** Missing or incorrect `.env` file

**Solution:**
1. Create `.env` file:
   ```bash
   copy .env.example .env  # Windows
   cp .env.example .env    # macOS/Linux
   ```

2. Add to `.env`:
   ```env
   DJANGO_DEBUG=1
   ```

3. Restart server

---

### **Issue 3: Email encryption errors**

**Symptom:** `MissingEncryptionKeyError` or `DecryptionFailedError`

**Cause:** Missing or invalid encryption key

**Solution:**
```bash
# Generate new key
python -c "from accounts.encryption import generate_encryption_key; print(generate_encryption_key())"

# Add to .env
echo "ACCOUNT_EMAIL_ENCRYPTION_KEY=generated_key_here" >> .env

# Restart server
```

**Verify:**
```bash
python manage.py shell
```
```python
from accounts.encryption import test_encryption_roundtrip
test_encryption_roundtrip()  # Should succeed
```

---

### **Issue 4: "No such table" errors**

**Cause:** Migrations not applied

**Solution:**
```bash
# Delete database
rm db.sqlite3  # macOS/Linux
del db.sqlite3  # Windows

# Re-run migrations
python manage.py migrate
```

---

### **Issue 5: Port 8000 already in use**

**Cause:** Another process using port 8000

**Solution:**
```bash
# Use different port
python manage.py runserver 8080
# Visit: http://127.0.0.1:8080/

# Or kill existing process
# Windows
netstat -ano | findstr :8000
taskkill /PID <pid> /F

# macOS/Linux
lsof -i :8000
kill <pid>
```

---

### **Issue 6: Static files not loading**

**Symptom:** CSS/JavaScript not applied, 404 errors

**Solution:**
1. Check `STATIC_URL` in settings: `/static/`
2. Verify files exist in `static/` folder
3. Hard refresh browser (Ctrl+F5)
4. Check browser console for errors

---

### **Issue 7: Tests failing**

**Cause:** Database schema mismatch

**Solution:**
```bash
# Delete test database
rm test_db.sqlite3  # If it exists

# Run tests with verbose output
python manage.py test --verbosity=2
```

---

## 📁 **Project Structure**

```
it302-mco/
├── .venv/                      # Virtual environment (not in git)
├── brewschews/                 # Django project settings
│   ├── settings.py             # Main configuration (DEBUG, SECRET_KEY, encryption)
│   ├── urls.py                 # Root URL routing
│   ├── wsgi.py                 # WSGI config for deployment
│   └── asgi.py                 # ASGI config (async)
├── accounts/                   # User authentication app
│   ├── models.py               # User, Profile, AuthenticationEvent models
│   ├── views.py                # Login, signup, profile views
│   ├── forms.py                # Authentication forms
│   ├── encryption.py           # Email encryption utilities (AES-256-GCM)
│   ├── urls.py                 # Account-related URLs
│   ├── tests.py                # Automated tests
│   ├── test_encryption.py      # Encryption tests
│   └── migrations/             # Database migrations
│       ├── 0001_initial.py
│       ├── 0002_add_email_encryption_fields.py
│       ├── 0003_encrypt_existing_emails.py
│       └── 0004_remove_security_fields.py
├── menu/                       # Menu catalog app
│   ├── models.py               # Category, MenuItem models
│   ├── views.py                # Menu display views
│   ├── tests.py                # Automated tests
│   └── migrations/             # Database migrations
│       ├── 0001_initial.py
│       └── 0002_seed_menu.py   # Sample menu data
├── orders/                     # Cart & order management (UI only)
│   ├── models.py               # Cart, Order models
│   ├── views.py                # Placeholder views
│   ├── forms.py                # Cart forms
│   └── migrations/             # Database migrations
├── pages/                      # Public-facing pages
│   ├── views.py                # Home page view
│   └── urls.py                 # Public URLs
├── docs/                       # Technical documentation
│   ├── SIGNUP_FEATURE.md
│   ├── LOGIN_FEATURE.md
│   ├── PROFILE_MANAGEMENT.md
│   ├── MENU_SYSTEM.md
│   ├── DATABASE_ARCHITECTURE.md
│   ├── SECURITY_IMPLEMENTATION.md
│   ├── TESTING_PROCEDURES.md
│   └── database-plan.md
├── templates/                  # HTML templates
│   ├── base.html               # Base template with navigation
│   ├── accounts/               # Login, signup, profile templates
│   ├── menu/                   # Menu display template
│   ├── orders/                 # Cart, checkout, history templates
│   └── pages/                  # Home page template
├── static/                     # Static assets
│   ├── css/                    # Stylesheets
│   ├── js/                     # JavaScript files
│   └── img/                    # Images (logo, backgrounds)
├── db.sqlite3                  # SQLite database (not in git)
├── manage.py                   # Django management script
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (not in git, create from .env.example)
├── .env.example                # Example environment variables
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

---

## 🔐 **Security Best Practices**

1. **Never commit sensitive data to Git:**
   - `.env` file (contains keys)
   - `db.sqlite3` (contains user data)
   - `__pycache__/` (compiled Python files)
   - `.venv/` (virtual environment)

2. **Use different keys for dev/staging/prod:**
   - Development: Auto-generated keys (with warnings)
   - Production: Explicitly generated, stored securely

3. **Back up encryption keys:**
   - If `ACCOUNT_EMAIL_ENCRYPTION_KEY` is lost, emails cannot be decrypted!
   - Store key in secure password manager
   - Document key rotation procedures

4. **Enable HTTPS in production:**
   - Uncomment HTTPS settings in `brewschews/settings.py`
   - Set `SECURE_SSL_REDIRECT = True`
   - Set `SESSION_COOKIE_SECURE = True`

5. **Review security checklist before deployment:**
   - See `docs/SECURITY_IMPLEMENTATION.md`
   - Run `python manage.py check --deploy`

---

## 👥 **Team Collaboration**

### **Pull Latest Changes**

```bash
# Switch to main branch
git checkout main

# Pull latest changes
git pull origin main

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate.bat  # Windows

# Update dependencies (if changed)
pip install -r requirements.txt

# Run migrations (if new ones added)
python manage.py migrate

# Start server
python manage.py runserver
```

### **Merge Pull Requests from GitHub**

**Option 1: Command Line**
```bash
# Fetch the PR branch (example: claude/feature-branch)
git fetch origin branch-name

# Checkout the branch
git checkout branch-name

# Review changes in docs/ or code

# Switch back to main
git checkout main

# Merge the branch
git merge branch-name

# Push to GitHub
git push origin main
```

**Option 2: GitHub UI (Recommended)**
1. Go to repository on GitHub
2. Click "Pull requests" tab
3. Find and review the PR
4. Click "Merge pull request"
5. Confirm merge
6. Pull to local:
   ```bash
   git checkout main
   git pull origin main
   ```

---

## 🚀 **Next Steps**

After getting the project running:

1. **Read the documentation** (`docs/` folder)
2. **Run the tests** (`python manage.py test`)
3. **Create a test account** and explore features
4. **Review the code** to understand implementation
5. **Check out the security features** (encryption, hashing, audit logs)

For questions or issues, refer to the documentation or contact the team.

---

## 📝 **License**

This project is for educational purposes (IT302 MCO).

## 👨‍💻 **Contributors**

- Team Members: (Add your names here)
- Powered by Django 4.2+
- Documentation generated with assistance from Claude Code
