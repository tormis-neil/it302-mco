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

## Quick Setup Guide

### Prerequisites

- **Python 3.8+** installed
- **Git** installed
- A code editor (VS Code recommended)

### Step 1: Clone the Repository

```bash
git clone https://github.com/tormis-neil/it302-mco.git
cd it302-mco
```

### Step 2: Create Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` at the start of your terminal prompt.

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

Edit `.env` with these settings:

```env
# Required for development
DJANGO_DEBUG=1
DJANGO_SECRET_KEY=
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_DB_NAME=db.sqlite3

# Email encryption (optional - auto-generates if empty)
ACCOUNT_EMAIL_ENCRYPTION_KEY=

# PayMongo API Keys (get from https://dashboard.paymongo.com)
PAYMONGO_SECRET_KEY=sk_test_your_secret_key_here
PAYMONGO_PUBLIC_KEY=pk_test_your_public_key_here
PAYMONGO_WEBHOOK_SECRET=
```

### Step 5: Run Database Migrations

**Windows:**
```cmd
python manage.py migrate
```

**macOS/Linux:**
```bash
python3 manage.py migrate
```

### Step 6: Start the Server

**Windows:**
```cmd
python manage.py runserver
```

**macOS/Linux:**
```bash
python3 manage.py runserver
```

### Step 7: Open the Website

Visit: **http://127.0.0.1:8000/**

---

## PayMongo Setup (Payment System)

To enable online payments:

1. Create a **PayMongo** account at https://paymongo.com
2. Go to **Developers > API Keys** in the dashboard
3. Copy your **Test** keys (for development)
4. Add them to your `.env` file:
   ```env
   PAYMONGO_SECRET_KEY=sk_test_xxxxx
   PAYMONGO_PUBLIC_KEY=pk_test_xxxxx
   ```
5. Restart the Django server

**Test Card for Development:**
- Card Number: `4343 4343 4343 4345`
- Expiry: Any future date
- CVV: Any 3 digits

---

## Running Tests

Run all automated tests:

**Windows:**
```cmd
python manage.py test
```

**macOS/Linux:**
```bash
python3 manage.py test
```

Expected output: `Ran 37 tests in X.XXXs - OK`

---

## Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'django'"

**Cause:** Virtual environment not activated.

**Solution:**
```bash
# Windows
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

---

### Issue: "DJANGO_SECRET_KEY environment variable is required"

**Cause:** Missing `.env` file or `DJANGO_DEBUG` not set.

**Solution:**
1. Create `.env` file from `.env.example`
2. Make sure `DJANGO_DEBUG=1` is set

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
1. Get API keys from PayMongo dashboard
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
└── README.md            # This file
```

---

## For Team Members

### Pulling Latest Changes

```bash
git checkout main
git pull origin main
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Before Committing

1. Run tests: `python manage.py test`
2. Make sure all tests pass
3. Never commit `.env` or `db.sqlite3`

---

## Security Notes

- **Never commit** `.env`, `db.sqlite3`, or API keys to Git
- Use different keys for development and production
- Back up your `ACCOUNT_EMAIL_ENCRYPTION_KEY` - if lost, encrypted emails cannot be recovered

---

## License

This project is for educational purposes (IT302 MCO).

## Contributors

- Team Members: (Add your names here)
