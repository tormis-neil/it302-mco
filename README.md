# Brews & Chews – Online Café Ordering System

A Django-based web application for managing café orders with secure user authentication and profile management.

---

## 🎯 **Project Status**

### ✅ **Fully Implemented Features**
- **User Authentication**
  - Sign up with email validation and strong password requirements
  - Sign in using username OR email
  - Password strength indicator with real-time validation
  - Account lockout after 5 failed login attempts (60-minute lockout)
  - Rate limiting on signup and login attempts
  - Secure logout functionality

- **User Profile Management**
  - View account information (username, email, join date, last login)
  - Edit profile details (display name, phone number, favorite drink, bio)
  - Change username with password confirmation
  - Change password with current password verification
  - Delete account with confirmation modal

- **Menu Display**
  - Browse café menu items organized by categories
  - View item descriptions and prices
  - Responsive grid layout

- **Security Features**
  - Audit logging for all authentication events
  - IP-based rate limiting
  - Strong password validation (12+ chars, uppercase, numbers, special characters)
  - Session management

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

---

## 🛠️ **Tech Stack**

- **Backend:** Django 4.2+
- **Database:** SQLite3 (development)
- **Authentication:** Custom User model with Django's auth system
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Password Hashing:** Argon2
- **Security:** Rate limiting, audit logging, CSRF protection

---

## 📋 **Prerequisites**

Before setting up the project, ensure you have:

- **Python 3.8+** installed ([Download Python](https://www.python.org/downloads/))
- **pip** (comes with Python)
- **Git** installed ([Download Git](https://git-scm.com/downloads))
- A code editor (VS Code, PyCharm, etc.)

---

## 🚀 **Setup Instructions**

Follow these steps to run the project on your computer:

### **Prerequisites**

Before you begin, ensure you have:
- **Python 3.8 or higher** installed ([Download Python](https://www.python.org/downloads/))
- **Git** installed ([Download Git](https://git-scm.com/downloads))

**Check your Python version:**
```bash
python --version
# or
python3 --version
# Should show: Python 3.8.0 or higher
```

---

### **Step 1: Clone the Repository**

```bash
# Clone the project
git clone https://github.com/YOUR_USERNAME/it302-mco.git
cd it302-mco
```

---

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
- cryptography (security utilities)
- python-dotenv (environment variables)

---

### **Step 4: Set Up Environment Variables (REQUIRED for Development)**

Create a `.env` file in the project root:

```bash
# Windows PowerShell
copy .env.example .env

# Windows Command Prompt
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

**The `.env` file should contain:**
```env
DJANGO_DEBUG=1
DJANGO_SECRET_KEY=
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_DB_NAME=db.sqlite3
```

**⚠️ IMPORTANT:**
- `DJANGO_DEBUG=1` is **REQUIRED** for development mode
- `DJANGO_SECRET_KEY` can be left empty (will auto-generate with a warning - safe for development)
- Skipping this step will cause `ImproperlyConfigured` errors

---

### **Step 5: Run Database Migrations**

```bash
python manage.py migrate
```

**This will:**
- ✅ Create the SQLite database (`db.sqlite3`)
- ✅ Set up all required tables (User, Profile, Menu, Orders, etc.)
- ✅ Populate the menu with sample coffee/food items

**Expected output:**
```
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying accounts.0001_initial... OK
  Applying menu.0001_initial... OK
  Applying menu.0002_seed_menu... OK
  ...
```

---

### **Step 6: Start the Development Server**

```bash
python manage.py runserver
```

**You should see:**
```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
October 22, 2025 - 12:00:00
Django version 4.2.x, using settings 'brewschews.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

---

### **Step 7: Access the Website**

Open your web browser and visit:
```
http://127.0.0.1:8000/
```

**✅ You should see the Brews & Chews home page!**

---

## 🧪 **Running Tests**

Verify everything works correctly:

```bash
python manage.py test accounts
```

**Expected output:**
```
Ran 8 tests in 2.341s

OK
```

---

## 🛠️ **Common Issues & Solutions**

### **Issue 1: "ModuleNotFoundError: No module named 'django'"**

**Solution:** Activate your virtual environment first
```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows Command Prompt
.venv\Scripts\activate.bat

# macOS/Linux
source .venv/bin/activate
```

---

### **Issue 2: "python: command not found"**

**Solution:** Use `python3` instead
```bash
python3 -m venv .venv
python3 manage.py runserver
```

---

### **Issue 3: "Execution of scripts is disabled" (Windows PowerShell)**

**Solution:** Enable script execution
```powershell
# Run PowerShell as Administrator, then:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Or use Command Prompt instead:**
```cmd
.venv\Scripts\activate.bat
```

---

### **Issue 4: "No such table" errors**

**Solution:** Delete database and re-run migrations
```bash
# Windows
del db.sqlite3
python manage.py migrate

# macOS/Linux
rm db.sqlite3
python manage.py migrate
```

---

### **Issue 5: Port 8000 already in use**

**Solution:** Use a different port
```bash
python manage.py runserver 8080
# Then visit: http://127.0.0.1:8080/
```

---

### **Issue 6: "ImproperlyConfigured: DJANGO_SECRET_KEY environment variable is required!"**

**Solution:** You need to create a `.env` file with `DJANGO_DEBUG=1`
```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

**Make sure your `.env` contains:**
```env
DJANGO_DEBUG=1
```

This tells Django to run in development mode (which auto-generates SECRET_KEY).

---

### **Issue 7: "WARNING: Using auto-generated SECRET_KEY"**

**Solution:** This is normal for development. To remove the warning:
1. Generate a secret key:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
2. Add it to your `.env` file:
   ```
   DJANGO_SECRET_KEY=your-generated-key-here
   ```

### Project Structure
online-cafe-ordering-system/
├── .venv/                      # Virtual environment (not in git)
├── brewschews/                 # Django project settings
│   ├── settings.py             # Main configuration
│   ├── urls.py                 # Root URL routing
│   ├── wsgi.py                 # WSGI config for deployment
│   └── asgi.py                 # ASGI config (async)
├── accounts/                   # User authentication app
│   ├── models.py               # User, Profile, AuthenticationEvent models
│   ├── views.py                # Login, signup, profile views
│   ├── forms.py                # Authentication forms
│   ├── urls.py                 # Account-related URLs
│   └── migrations/             # Database migrations
├── menu/                       # Menu catalog app
│   ├── models.py               # Category, MenuItem models
│   ├── views.py                # Menu display views
│   └── migrations/             # Database migrations (includes seed data)
├── orders/                     # Cart & order management (UI only)
│   ├── models.py               # Cart, Order models
│   ├── views.py                # Placeholder views
│   └── migrations/             # Database migrations
├── pages/                      # Public-facing pages
│   ├── views.py                # Home page view
│   └── urls.py                 # Public URLs
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
├── .env.example                # Example environment variables
├── .gitignore                  # Git ignore rules
└── README.md                   # This file