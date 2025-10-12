# online-cafe-ordering-system
# Brews & Chews – Online Cafe Ordering System

This repository contains the in-progress implementation of the Brews & Chews web application. The current iteration introduces a Django project structure to support upcoming authentication and profile features while keeping the marketing and menu preview pages available for stakeholders.

## Project layout

```
it302-mco/
├── brewschews/           # Django project configuration
├── accounts/             # Authentication app with secure signup/login and profiles
├── menu/                 # Authenticated menu UI fed by seeded catalog data
├── orders/               # Read-only cart, checkout, and history dashboard views
├── pages/                # Public marketing and menu views
├── templates/            # HTML templates grouped by app
├── static/               # Consolidated CSS and image assets
├── manage.py             # Django management utility
├── requirements.txt      # Python dependencies
└── .env.example          # Sample environment configuration
```

## Getting started

1. **Create a virtual environment** (recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .venv\\Scripts\\activate   # Windows
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**

   - Copy `.env.example` to `.env` and adjust the values as needed (secret key, debug flag, allowed hosts, database name).
   - Optionally set `ACCOUNT_EMAIL_ENCRYPTION_KEY` to a base64-encoded 32-byte key if you need to rotate the default derived from
     the secret key. This key powers the AES-256 encryption used for stored email addresses.

4. **Run migrations and start the development server:**

   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

5. **Access the site:**

   Visit `http://127.0.0.1:8000/` for the landing page, `http://127.0.0.1:8000/pages/menu/preview/` for the public menu preview,
   and sign in to explore the authenticated dashboard at `/menu/`, `/orders/cart/`, `/orders/checkout/`, and `/orders/history/`.

## Authenticated user journey

The current build focuses on finalizing the secure authentication experience while presenting the post-login UI as a clickable
prototype. The expected flow is:

1. Browse the **Menu Preview** without signing in to see a snapshot of the café offerings.
2. Create an account or sign in—rate limiting and audit logging are enabled to satisfy the security requirements.
3. After authentication, explore the **Order Menu**, **Cart**, **Checkout**, and **History** pages. Buttons and forms are
   intentionally disabled while the transactional back-end is still under construction.
4. Visit the **Profile** page to review and update account details that are stored securely in the database.
5. Sign out using the navigation menu when finished.

## Database management

The project uses SQLite by default so new contributors can get started quickly without provisioning external services. The database file is intentionally excluded from version control—run `python manage.py migrate` locally to create or upgrade your own `db.sqlite3` after pulling new migrations.

You can change the database location by updating `DJANGO_DB_NAME` in your `.env`. For production deployments, point `DJANGO_DB_NAME` at a persistent volume or switch to a managed service such as PostgreSQL by adjusting `DATABASES` in `brewschews/settings.py` and setting the appropriate environment variables.

## Security highlights

- **Encrypted email addresses** – the custom user model stores email addresses using AES-256-GCM. Only the SHA-256 digest is used for lookups, protecting the plaintext value.
- **Strong password policy** – the signup form enforces Django’s configured password validators (12+ characters, complexity checks, similarity checks) alongside additional uppercase/number/special-character requirements.
- **Audit logging and throttling** – every login and signup attempt is persisted with IP information, while rate limiting and account lockouts protect against brute-force attacks.

## Testing

- Run `python manage.py test` to execute the Django unit tests that cover signup, login, profile updates, and logout.
- Use `python manage.py check` to run Django’s system checks before deployment.

## Next steps

- Connect the cart, checkout, and history interfaces to the underlying order models.
- Add staff tooling for managing menu availability and order status updates.
- Expand automated test coverage to include front-end interactions and regression checks.