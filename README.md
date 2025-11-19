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

**✅ Phase 1: Shopping Cart Backend (COMPLETED)**
- Add items to cart from menu catalog
- Update item quantities (+/- controls)
- Remove items from cart
- Real-time cart total calculations (subtotal, tax, total)
- Database persistence (Cart and CartItem models)
- Transaction-safe operations (@transaction.atomic)

**✅ Phase 2: Checkout Flow (COMPLETED)**
- Contact information form (name, phone, special instructions)
- Order creation with unique reference numbers (BC-YYMMDD-NNN format)
- Price snapshots (OrderItem stores historical pricing)
- Order history display with real data
- Status tracking (Pending, Confirmed, Cancelled)
- Cart clearing after successful checkout

### ❌ **Not Implemented (Planned)**
- **Phase 3:** Admin/Staff Dashboard (order status management)
- **Phase 4:** Payment Integration (PayMongo)
- Email notifications
- Password reset via email
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

**Windows:**
```cmd
py --version
# or
python --version
# Should show: Python 3.8.0 or higher
```

**macOS/Linux:**
```bash
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
py -m venv .venv
# or
python -m venv .venv

# Activate the environment
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
py -m venv .venv
# or
python -m venv .venv

# Activate the environment
.venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
python3 -m venv .venv

# Activate the environment
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

     **Windows:**
     ```cmd
     py -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
     ```

     **macOS/Linux:**
     ```bash
     python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
     ```

3. **ACCOUNT_EMAIL_ENCRYPTION_KEY** (Optional)
   - Used for AES-256-GCM email encryption
   - Can be left empty (auto-derives from SECRET_KEY with warning)
   - For proper setup, generate a key:

     **Windows:**
     ```cmd
     py -c "from accounts.encryption import generate_encryption_key; print(generate_encryption_key())"
     ```

     **macOS/Linux:**
     ```bash
     python3 -c "from accounts.encryption import generate_encryption_key; print(generate_encryption_key())"
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

**⚠️ CRITICAL:** You must run migrations for Phase 1 & 2 to work properly!

**Windows:**
```cmd
py manage.py makemigrations orders
py manage.py migrate
```

**macOS/Linux:**
```bash
python3 manage.py makemigrations orders
python3 manage.py migrate
```

**What these commands do:**

1. **`makemigrations orders`** - Creates migration for order reference_number field (Phase 2 requirement)
2. **`migrate`** - Applies all migrations to create database tables

**This will:**
- ✅ Create the SQLite database (`db.sqlite3`)
- ✅ Set up all required tables (User, Profile, Menu, Cart, Order, etc.)
- ✅ Encrypt user email fields (AES-256-GCM migration)
- ✅ Populate the menu with sample coffee/food items
- ✅ Add reference_number field to Order model (Phase 2)

**Expected output:**
```
Migrations for 'orders':
  orders/migrations/0002_order_reference_number.py
    - Add field reference_number to order

Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying accounts.0001_initial... OK
  Applying accounts.0002_add_email_encryption_fields... OK
  Applying accounts.0003_encrypt_existing_emails... OK
  Applying accounts.0004_remove_security_fields... OK
  Applying menu.0001_initial... OK
  Applying menu.0002_seed_menu... OK
  Applying orders.0001_initial... OK
  Applying orders.0002_order_reference_number... OK
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

**Windows:**
```cmd
py manage.py shell
```

**macOS/Linux:**
```bash
python3 manage.py shell
```

**Then run:**
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

**Windows:**
```cmd
py manage.py runserver
```

**macOS/Linux:**
```bash
python3 manage.py runserver
```

**You should see:**
```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
November 19, 2025 - 12:00:00
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

**Basic Workflow:**
1. Click "Sign Up" → Create an account
2. Fill in username, email, password (12+ chars, uppercase, number, special char)
3. Submit → Auto-logged in, redirected to menu
4. Browse menu items (Espresso, Brewed Coffee, etc.)
5. Click your username → View/edit profile
6. Try changing username/password
7. Log out → Log back in with new credentials

---

## 🧪 **Testing Phase 1 & 2 (Cart & Checkout)**

Now that the server is running, you can test the fully implemented cart and checkout features!

### **Phase 1: Shopping Cart Testing**

**Test adding items to cart:**
1. Go to **Menu** (http://127.0.0.1:8000/menu/)
2. Click **"Add to Cart"** on any menu item (e.g., Cappuccino)
3. You should see the item added successfully
4. Add 2-3 more items from different categories

**Test viewing cart:**
1. Click **"Cart"** in the navigation menu
2. You should see all items you added with:
   - Item name and category
   - Unit price in ₱
   - Quantity controls (+/- buttons)
   - Line total (price × quantity)
   - Remove button
   - Order summary with subtotal, tax (8%), and total

**Test quantity updates:**
1. Click **"+"** button on any item → Quantity should increase, totals update
2. Click **"-"** button on any item → Quantity should decrease, totals update
3. Try clicking **"-"** when quantity is 1 → Button should be disabled (prevents quantity 0)

**Test removing items:**
1. Click **"Remove"** button on any item
2. Item should disappear from cart immediately
3. Totals should recalculate automatically

**Test empty cart:**
1. Remove all items from cart
2. You should see: "Your cart is currently empty"
3. Click **"Browse the menu"** → Returns to menu

### **Phase 2: Checkout Flow Testing**

**Test checkout process:**
1. Add 2-3 items to cart
2. Click **"Proceed to Checkout"** from cart page
3. You should see:
   - Contact information form (name, phone, special instructions)
   - Order summary sidebar showing all cart items
   - Subtotal, tax, and total amounts

**Test order placement:**
1. Fill in contact form:
   - **Full name:** Your name (required, 2-120 chars)
   - **Phone number:** Your phone (required, max 20 chars)
   - **Special instructions:** Optional (e.g., "Extra hot", "No sugar")
2. Click **"Place Order"**
3. You should be redirected to **Order History**

**Test order history:**
1. After placing order, you should see your order with:
   - **Order reference:** BC-YYMMDD-NNN format (e.g., BC-251119-001)
   - **Placed on:** Date and time
   - **Status:** "Pending" (yellow badge)
   - **Items list:** All items you ordered with quantities
   - **Order total:** Final amount you paid
   - **Special instructions:** If you added any

**Test multiple orders:**
1. Go back to menu → Add new items → Checkout again
2. Your cart should be empty after first checkout
3. Place second order with different items
4. Check order history → Should show both orders
5. Reference numbers should increment (BC-251119-001, BC-251119-002, etc.)

**Test order reference numbering:**
1. Order reference format: **BC-YYMMDD-NNN**
   - BC = Brews & Chews
   - YYMMDD = Year Month Day (e.g., 251119 = November 19, 2025)
   - NNN = Daily sequential number (001, 002, 003...)
2. Each day starts counting from 001
3. References are unique across all orders

### **Edge Cases to Test**

**Empty cart checkout:**
1. Clear all items from cart
2. Try to access checkout URL directly: http://127.0.0.1:8000/orders/checkout/
3. You should be redirected to cart with message

**Form validation:**
1. In checkout, try submitting with empty name → Should show error
2. Try submitting with empty phone → Should show error
3. Special instructions are optional (can be blank)

**Database persistence:**
1. Add items to cart → Stop server (Ctrl+C)
2. Restart server → Go to cart
3. Items should still be there (cart saved in database)

**Multiple users:**
1. Create second account (different username/email)
2. Each user has separate cart and order history
3. User A's cart doesn't show in User B's account

### **What You Should See**

**Working Features:**
- ✅ Add to cart from menu
- ✅ Update quantities in cart
- ✅ Remove items from cart
- ✅ Real-time total calculations
- ✅ Checkout form validation
- ✅ Order creation with unique references
- ✅ Order history display
- ✅ Price snapshots (orders show historical prices)
- ✅ Cart clearing after checkout
- ✅ Transaction safety (no data loss on errors)

**Current Limitations:**
- ⏳ Order status is always "Pending" (admin dashboard coming in Phase 3)
- ⏳ No payment processing yet (PayMongo integration in Phase 4)
- ⏳ No email notifications (out of scope)

---

## 🧪 **Running Automated Tests**

Verify everything works correctly with automated tests:

**Run all tests:**

**Windows:**
```cmd
py manage.py test
```

**macOS/Linux:**
```bash
python3 manage.py test
```

**Run specific app tests:**

**Windows:**
```cmd
# Accounts tests (signup, login, profile, encryption)
py manage.py test accounts

# Menu tests
py manage.py test menu

# Orders tests (cart, checkout, order creation)
py manage.py test orders
```

**macOS/Linux:**
```bash
# Accounts tests (signup, login, profile, encryption)
python3 manage.py test accounts

# Menu tests
python3 manage.py test menu

# Orders tests (cart, checkout, order creation)
python3 manage.py test orders
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

**Windows:**
```cmd
py manage.py test accounts.test_encryption
```

**macOS/Linux:**
```bash
python3 manage.py test accounts.test_encryption
```

**Expected output:**
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

**Manual encryption test:**

**Windows:**
```cmd
py manage.py shell
```

**macOS/Linux:**
```bash
python3 manage.py shell
```

**Then run:**
```python
from accounts.encryption import test_encryption_roundtrip
test_encryption_roundtrip()
# Should print: "Roundtrip successful: True"
exit()
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

**Windows:**
```cmd
py -c "from accounts.encryption import generate_encryption_key; print(generate_encryption_key())"
```

**macOS/Linux:**
```bash
python3 -c "from accounts.encryption import generate_encryption_key; print(generate_encryption_key())"
```

**Add to `.env`:**
```env
ACCOUNT_EMAIL_ENCRYPTION_KEY=generated_key_here
```

**Test encryption:**

**Windows:**
```cmd
py manage.py shell
```

**macOS/Linux:**
```bash
python3 manage.py shell
```

**Then run:**
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

**Windows:**
```cmd
# Collect static files
py manage.py collectstatic

# Configure web server (nginx, Apache) to serve /static/
```

**macOS/Linux:**
```bash
# Collect static files
python3 manage.py collectstatic

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

**Windows:**
```cmd
# Generate new key
py -c "from accounts.encryption import generate_encryption_key; print(generate_encryption_key())"

# Add to .env (edit .env file manually and paste the key)
# Or use: echo ACCOUNT_EMAIL_ENCRYPTION_KEY=generated_key_here >> .env

# Restart server (Ctrl+C then py manage.py runserver)
```

**macOS/Linux:**
```bash
# Generate new key
python3 -c "from accounts.encryption import generate_encryption_key; print(generate_encryption_key())"

# Add to .env
echo "ACCOUNT_EMAIL_ENCRYPTION_KEY=generated_key_here" >> .env

# Restart server (Ctrl+C then python3 manage.py runserver)
```

**Verify:**

**Windows:**
```cmd
py manage.py shell
```

**macOS/Linux:**
```bash
python3 manage.py shell
```

**Then run:**
```python
from accounts.encryption import test_encryption_roundtrip
test_encryption_roundtrip()  # Should succeed
```

---

### **Issue 4: "No such table" errors**

**Cause:** Migrations not applied

**Solution:**

**Windows:**
```cmd
# Delete database
del db.sqlite3

# Re-run migrations
py manage.py makemigrations orders
py manage.py migrate
```

**macOS/Linux:**
```bash
# Delete database
rm db.sqlite3

# Re-run migrations
python3 manage.py makemigrations orders
python3 manage.py migrate
```

---

### **Issue 5: Port 8000 already in use**

**Cause:** Another process using port 8000

**Solution Option 1: Use different port**

**Windows:**
```cmd
py manage.py runserver 8080
# Visit: http://127.0.0.1:8080/
```

**macOS/Linux:**
```bash
python3 manage.py runserver 8080
# Visit: http://127.0.0.1:8080/
```

**Solution Option 2: Kill existing process**

**Windows:**
```cmd
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace <PID> with actual process ID)
taskkill /PID <PID> /F
```

**macOS/Linux:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process (replace <PID> with actual process ID)
kill <PID>
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

**Windows:**
```cmd
# Delete test database (if it exists)
del test_db.sqlite3

# Run tests with verbose output
py manage.py test --verbosity=2
```

**macOS/Linux:**
```bash
# Delete test database (if it exists)
rm test_db.sqlite3

# Run tests with verbose output
python3 manage.py test --verbosity=2
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
├── orders/                     # Cart & order management (Phase 1 & 2 complete)
│   ├── models.py               # Cart, CartItem, Order, OrderItem models
│   ├── views.py                # Cart operations, checkout, order history
│   ├── forms.py                # Cart and checkout forms
│   ├── urls.py                 # Order-related URLs
│   └── migrations/             # Database migrations
│       ├── 0001_initial.py
│       └── 0002_order_reference_number.py  # Phase 2 migration
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

**Step 1: Pull from GitHub**
```bash
# Switch to main branch
git checkout main

# Pull latest changes
git pull origin main
```

**Step 2: Activate virtual environment**

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
.venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

**Step 3: Update dependencies (if requirements.txt changed)**
```bash
pip install -r requirements.txt
```

**Step 4: Run migrations (if new migrations added)**

**Windows:**
```cmd
py manage.py migrate
```

**macOS/Linux:**
```bash
python3 manage.py migrate
```

**Step 5: Start server**

**Windows:**
```cmd
py manage.py runserver
```

**macOS/Linux:**
```bash
python3 manage.py runserver
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
