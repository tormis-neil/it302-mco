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

### Check Your Python Version:
```bash
python --version
# or
python3 --version

### Set Up Instructions:

git clone https://github.com/YOUR_USERNAME/online-cafe-ordering-system.git
cd online-cafe-ordering-system

# Create a Virtual Environment
- Windows (PowerShell):
- bashpython -m venv .venv
- .venv\Scripts\Activate.ps1

# Install Dependecies
- pip install -r requirements.txt

# Run Database Migrations
- python manage.py migrate

This will:

- Create the SQLite database (db.sqlite3)
- Set up all required tables
- Populate the menu with sample items

# Start the Development Server
python manage.py runserver

You Should See:
- Starting development server at http://127.0.0.1:8000/
- Quit the server with CTRL-BREAK.

### Common Issues & Solutions

# "ModuleNotFoundError: No module named 'django'"
- Windows PowerShell
.venv\Scripts\Activate.ps1
- macOS/Linux
source .venv/bin/activate

# "python: command not found"
- python3 -m venv .venv
- python3 manage.py runserver

# "Execution of scripts is disabled on this system" (Windows)
# Run PowerShell as Administrator, then:
- Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Or use Command Prompt instead:
- .venv\Scripts\activate.bat

#  "No such table" errors
# Delete database
rm db.sqlite3         # macOS/Linux
del db.sqlite3        # Windows

# Re-run migrations
python manage.py migrate

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