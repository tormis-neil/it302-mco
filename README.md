# Brews & Chews - Online Café Ordering System

A Django-based web application for café ordering with secure authentication, online payment processing, and order management.

---

## What is This?

**Brews & Chews** is an online ordering system for a café where customers can:
- Browse the menu (coffee, bakery items, etc.)
- Add items to their shopping cart
- Checkout and pay online via **PayMongo** (Card, GCash, PayMaya)
- Track their order history

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Django 4.2+ (Python) |
| Database | SQLite (development) |
| Payment | PayMongo API |
| Password Security | Argon2 hashing |
| Email Security | AES-256-GCM encryption |
| Frontend | HTML5, CSS3, JavaScript |

---

## Features

### User Authentication
- Sign up with email validation
- Login with username OR email
- Strong password requirements (12+ chars, uppercase, numbers, special chars)
- Secure password hashing (Argon2)
- Email encryption at rest (AES-256-GCM)

### Menu & Shopping
- Browse café menu by categories
- Add items to cart
- Update quantities or remove items
- Real-time price calculations (subtotal, tax, total)

### Checkout & Payment
- Contact information form
- PayMongo integration (Card, GCash, PayMaya)
- Unique order reference numbers (BC-YYMMDD-NNN format)
- Order history with status tracking

### Profile Management
- View/edit profile details
- Change username or password
- Delete account

---

## Quick Setup Guide (For Team Members)

### Prerequisites

- **Python 3.8+** installed
- **Git** installed
- A code editor (VS Code recommended)

---

### Step 1: Clone the Repository

```bash
git clone https://github.com/tormis-neil/it302-mco.git
cd it302-mco
```

---

### Step 2: Create Virtual Environment

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

You should see `(.venv)` at the start of your terminal prompt.

---

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Step 4: Create the .env File (IMPORTANT!)

This is the most important step. The website will NOT work without the `.env` file.

**Windows (Command Prompt):**
```cmd
copy .env.example .env
```

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**macOS/Linux:**
```bash
cp .env.example .env
```

---

### Step 5: Configure the .env File

Open the `.env` file in your code editor and fill in the values:

```env
# ========================================
# REQUIRED SETTINGS - MUST BE SET!
# ========================================

# Set this to 1 for development (REQUIRED!)
# If you don't set this, the system will ask for DJANGO_SECRET_KEY
DJANGO_DEBUG=1

# Secret key for security (Optional in development)
# Leave empty if DJANGO_DEBUG=1 - it will auto-generate
# To generate your own: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
DJANGO_SECRET_KEY=

# Allowed hosts (keep as is for local development)
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database filename (keep as is)
DJANGO_DB_NAME=db.sqlite3

# ========================================
# EMAIL ENCRYPTION (Optional)
# ========================================

# Leave empty - will auto-generate from SECRET_KEY
# Only set this if you're sharing a database with other team members
ACCOUNT_EMAIL_ENCRYPTION_KEY=

# ========================================
# PAYMONGO PAYMENT (Optional for testing)
# ========================================

# Get your test keys from: https://dashboard.paymongo.com/developers
# Without these, payment features won't work
PAYMONGO_SECRET_KEY=sk_test_your_key_here
PAYMONGO_PUBLIC_KEY=pk_test_your_key_here
PAYMONGO_WEBHOOK_SECRET=
```

**IMPORTANT:** The minimum required setting is `DJANGO_DEBUG=1`. Without this, you'll get an error asking for `DJANGO_SECRET_KEY`.

---

### Step 6: Run Database Migrations

```bash
python manage.py migrate
```

This creates the database and all the tables needed for the website.

---

### Step 7: Start the Development Server

```bash
python manage.py runserver
```

---

### Step 8: Open the Website

Open your browser and go to: **http://127.0.0.1:8000/**

---

## PayMongo Setup (For Payment Testing)

To test the payment features:

1. Create a **PayMongo** account at https://paymongo.com
2. Go to **Developers > API Keys** in the dashboard
3. Copy your **Test** keys (NOT live keys!)
4. Add them to your `.env` file:
   ```env
   PAYMONGO_SECRET_KEY=sk_test_xxxxx
   PAYMONGO_PUBLIC_KEY=pk_test_xxxxx
   ```
5. Restart the Django server

**Test Card for Development:**
| Field | Value |
|-------|-------|
| Card Number | `4343 4343 4343 4345` |
| Expiry | Any future date (e.g., 12/25) |
| CVV | Any 3 digits (e.g., 123) |
| Name | Any name |

---

## Running Tests

Run all automated tests:

```bash
python manage.py test
```

Expected output: `Ran 37 tests in X.XXXs - OK`

---

## Common Issues & Solutions

### Issue: "DJANGO_SECRET_KEY environment variable is required"

**Cause:** `DJANGO_DEBUG=1` is NOT set in your `.env` file.

**Solution:**
1. Make sure you created the `.env` file (Step 4)
2. Make sure `DJANGO_DEBUG=1` is in your `.env` file
3. Make sure there's no typo (it must be exactly `DJANGO_DEBUG=1`)

---

### Issue: "ModuleNotFoundError: No module named 'django'"

**Cause:** Virtual environment not activated.

**Solution:**
```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows Command Prompt
.venv\Scripts\activate.bat

# macOS/Linux
source .venv/bin/activate
```

---

### Issue: "No such table" errors

**Cause:** Database migrations not applied.

**Solution:**
```bash
python manage.py migrate
```

---

### Issue: Payment not working / "API key" error

**Cause:** PayMongo keys not configured.

**Solution:**
1. Get test API keys from PayMongo dashboard
2. Add to `.env` file
3. Restart the server

---

### Issue: Port 8000 already in use

**Solution:** Use a different port:
```bash
python manage.py runserver 8080
```
Then visit: http://127.0.0.1:8080/

---

### Issue: ".env file not found" or settings not loading

**Cause:** `.env` file doesn't exist or is in wrong location.

**Solution:**
1. Make sure `.env` file is in the project root (same folder as `manage.py`)
2. Make sure the file is named exactly `.env` (not `.env.txt`)

---

## Project Structure

```
it302-mco/
├── brewschews/          # Django project settings
├── accounts/            # User authentication (login, signup, profile)
├── menu/                # Menu catalog
├── orders/              # Cart, checkout, payments, order history
├── pages/               # Public pages (home)
├── templates/           # HTML templates
├── static/              # CSS, JavaScript, images
├── docs/                # Technical documentation
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
├── .env                 # Your local settings (don't commit!)
└── README.md            # This file
```

---

## For Team Members

### After Cloning (First Time Setup)

```bash
# 1. Create virtual environment
python -m venv .venv

# 2. Activate it
# Windows: .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
# Windows: copy .env.example .env
# Mac/Linux: cp .env.example .env

# 5. Edit .env and set DJANGO_DEBUG=1

# 6. Run migrations
python manage.py migrate

# 7. Start server
python manage.py runserver
```

### Pulling Latest Changes

```bash
git checkout main
git pull origin main
pip install -r requirements.txt  # In case new packages were added
python manage.py migrate          # In case database changed
python manage.py runserver
```

### Before Committing

1. Run tests: `python manage.py test`
2. Make sure all tests pass
3. **NEVER commit these files:**
   - `.env` (contains secrets)
   - `db.sqlite3` (local database)
   - `.venv/` (virtual environment)

---

## Environment Variables Summary

| Variable | Required | Description |
|----------|----------|-------------|
| `DJANGO_DEBUG` | **YES** | Set to `1` for development |
| `DJANGO_SECRET_KEY` | No* | Auto-generates if DEBUG=1 |
| `DJANGO_ALLOWED_HOSTS` | No | Defaults to localhost |
| `DJANGO_DB_NAME` | No | Defaults to db.sqlite3 |
| `ACCOUNT_EMAIL_ENCRYPTION_KEY` | No | Auto-generates from SECRET_KEY |
| `PAYMONGO_SECRET_KEY` | For payments | Get from PayMongo dashboard |
| `PAYMONGO_PUBLIC_KEY` | For payments | Get from PayMongo dashboard |
| `PAYMONGO_WEBHOOK_SECRET` | No | For webhook verification |

*Required if DJANGO_DEBUG is not set to 1

---

## Security Notes

- **Never commit** `.env`, `db.sqlite3`, or API keys to Git
- Use different keys for development and production
- Back up your `ACCOUNT_EMAIL_ENCRYPTION_KEY` - if lost, encrypted emails cannot be recovered

---

## Technical Documentation

See the `docs/` folder for detailed documentation:
- `DATABASE_ARCHITECTURE.md` - Database models and relationships
- `SECURITY_IMPLEMENTATION.md` - Security features explained
- `PAYMENT_SYSTEM.md` - PayMongo payment integration
- `LOGIN_FEATURE.md` - Login functionality
- `SIGNUP_FEATURE.md` - Registration process
- `PROFILE_MANAGEMENT.md` - User profile features
- `MENU_SYSTEM.md` - Menu and cart system
- `TESTING_PROCEDURES.md` - Testing guide

---

## License

This project is for educational purposes (IT302 MCO).

## Contributors

- Team Members: (Add your names here)
