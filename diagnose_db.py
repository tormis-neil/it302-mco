"""
Database Migration Diagnostic Script

This script checks for common issues that prevent Django migrations from working.
Run this script to diagnose why 'no such table: accounts_user' error occurs.

Usage:
    python diagnose_db.py
"""

import os
import sys
import subprocess
from pathlib import Path

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*70}")
    print(f" {title}")
    print('='*70)

def check_python_django():
    """Check Python and Django versions."""
    print_section("1. Python & Django Versions")
    print(f"Python: {sys.version}")

    try:
        import django
        print(f"Django: {django.get_version()}")
        print("✅ Django is installed")
    except ImportError:
        print("❌ Django is NOT installed!")
        print("   Run: pip install -r requirements.txt")
        return False

    return True

def check_virtual_env():
    """Check if virtual environment is activated."""
    print_section("2. Virtual Environment")

    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )

    if in_venv:
        print(f"✅ Virtual environment is ACTIVE")
        print(f"   Location: {sys.prefix}")
    else:
        print("⚠️  Virtual environment is NOT active")
        print("   Activate it first:")
        print("   Windows: .venv\\Scripts\\activate")
        print("   Linux/Mac: source .venv/bin/activate")

    return in_venv

def check_django_setup():
    """Check if Django can be set up."""
    print_section("3. Django Configuration")

    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'brewschews.settings')
        import django
        django.setup()
        print("✅ Django settings loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
        return False

def check_migrations():
    """Check migration files."""
    print_section("4. Migration Files")

    migrations_dir = Path("accounts/migrations")
    if not migrations_dir.exists():
        print("❌ accounts/migrations directory does NOT exist!")
        return False

    migration_files = list(migrations_dir.glob("*.py"))
    if not migration_files:
        print("❌ No migration files found!")
        return False

    print(f"✅ Found {len(migration_files)} migration file(s):")
    for f in sorted(migration_files):
        size = f.stat().st_size
        print(f"   - {f.name} ({size} bytes)")

    return True

def check_database_location():
    """Check database file location."""
    print_section("5. Database File Location")

    from django.conf import settings
    db_path = settings.DATABASES['default']['NAME']

    print(f"Expected location: {db_path}")

    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        print(f"✅ Database file EXISTS ({size:,} bytes)")
        return True, db_path
    else:
        print("❌ Database file does NOT exist!")
        print("   This is expected if you just deleted it.")
        return False, db_path

def check_migration_status():
    """Check which migrations have been applied."""
    print_section("6. Migration Status")

    try:
        from django.core.management import call_command
        from io import StringIO

        # Capture showmigrations output
        out = StringIO()
        call_command('showmigrations', stdout=out)
        output = out.getvalue()

        print(output)

        # Check if accounts migrations are applied
        if '[X]' in output and 'accounts' in output:
            print("✅ Some migrations have been applied")
            return True
        elif '[ ]' in output and 'accounts' in output:
            print("⚠️  Migrations exist but are NOT applied")
            print("   You need to run: python manage.py migrate")
            return False
        else:
            print("❌ Cannot determine migration status")
            return False

    except Exception as e:
        print(f"❌ Cannot check migration status: {e}")
        return False

def check_database_tables():
    """Check if database tables exist."""
    print_section("7. Database Tables")

    try:
        from django.db import connection

        with connection.cursor() as cursor:
            # Get list of tables
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = cursor.fetchall()

            if not tables:
                print("❌ Database has NO tables!")
                print("   You MUST run: python manage.py migrate")
                return False

            print(f"✅ Found {len(tables)} table(s):")
            for table in tables:
                print(f"   - {table[0]}")

            # Check for accounts_user specifically
            table_names = [t[0] for t in tables]
            if 'accounts_user' in table_names:
                print("\n✅ accounts_user table EXISTS")
                return True
            else:
                print("\n❌ accounts_user table does NOT exist!")
                print("   Run: python manage.py migrate")
                return False

    except Exception as e:
        print(f"❌ Cannot check tables: {e}")
        return False

def check_installed_apps():
    """Check if accounts app is in INSTALLED_APPS."""
    print_section("8. INSTALLED_APPS Configuration")

    try:
        from django.conf import settings

        installed = settings.INSTALLED_APPS
        print("Installed apps:")
        for app in installed:
            marker = "✅" if app == "accounts" else "  "
            print(f"{marker} {app}")

        if "accounts" in installed:
            print("\n✅ 'accounts' app is registered")
            return True
        else:
            print("\n❌ 'accounts' app is NOT registered!")
            return False

    except Exception as e:
        print(f"❌ Cannot check INSTALLED_APPS: {e}")
        return False

def check_auth_user_model():
    """Check AUTH_USER_MODEL setting."""
    print_section("9. Custom User Model")

    try:
        from django.conf import settings

        auth_model = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')
        print(f"AUTH_USER_MODEL = {auth_model}")

        if auth_model == "accounts.User":
            print("✅ Custom user model is correctly configured")
            return True
        else:
            print("❌ AUTH_USER_MODEL is not set to 'accounts.User'")
            return False

    except Exception as e:
        print(f"❌ Cannot check AUTH_USER_MODEL: {e}")
        return False

def provide_solution():
    """Provide step-by-step solution."""
    print_section("SOLUTION")

    print("""
Based on the diagnostic results above, follow these steps:

1. ACTIVATE VIRTUAL ENVIRONMENT (if not already active):
   Windows: .venv\\Scripts\\activate
   Linux/Mac: source .venv/bin/activate

2. DELETE OLD DATABASE (if it exists):
   Windows: del db.sqlite3
   Linux/Mac: rm db.sqlite3

3. RUN MIGRATIONS:
   python manage.py migrate

4. CREATE SUPERUSER (optional, for admin access):
   python manage.py createsuperuser

5. RUN SERVER:
   python manage.py runserver

6. TEST SIGNUP/LOGIN:
   Visit: http://127.0.0.1:8000/accounts/signup/

If the problem persists, check the output above for ❌ errors and fix them first.
    """)

def main():
    """Run all diagnostic checks."""
    print("="*70)
    print(" DATABASE MIGRATION DIAGNOSTIC TOOL")
    print(" For: Brews & Chews Django Project")
    print("="*70)

    # Change to project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    print(f"\nWorking directory: {project_root.absolute()}\n")

    # Run checks
    checks = [
        check_python_django(),
        check_virtual_env(),
        check_django_setup(),
        check_migrations(),
        check_installed_apps(),
        check_auth_user_model(),
    ]

    # Only check database if Django is set up
    if checks[2]:  # Django setup successful
        db_exists, db_path = check_database_location()
        if db_exists:
            checks.append(check_migration_status())
            checks.append(check_database_tables())

    # Summary
    print_section("SUMMARY")
    passed = sum(1 for c in checks if c)
    total = len(checks)

    print(f"\nChecks passed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All checks passed! The database should be working.")
        print("   If you're still seeing errors, try restarting the server.")
    else:
        print("\n⚠️  Some checks failed. See details above.")

    # Provide solution
    provide_solution()

if __name__ == "__main__":
    main()
