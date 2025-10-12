# online-cafe-ordering-system
# Brews & Chews – Online Cafe Ordering System

This repository contains the in-progress implementation of the Brews & Chews web application. The current iteration introduces a Django project structure to support upcoming authentication and profile features while keeping the marketing and menu preview pages available for stakeholders.

## Project layout

```
it302-mco/
├── brewschews/           # Django project configuration
├── accounts/             # Authentication app (UI-only views for now)
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

4. **Run migrations and start the development server:**

   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

5. **Access the site:**

   Visit `http://127.0.0.1:8000/` for the landing page and `http://127.0.0.1:8000/menu/` for the menu preview.

## Database management

The project uses SQLite by default so new contributors can get started quickly without provisioning external services. The database file is intentionally excluded from version control—run `python manage.py migrate` locally to create or upgrade your own `db.sqlite3` after pulling new migrations.

You can change the database location by updating `DJANGO_DB_NAME` in your `.env`. For production deployments, point `DJANGO_DB_NAME` at a persistent volume or switch to a managed service such as PostgreSQL by adjusting `DATABASES` in `brewschews/settings.py` and setting the appropriate environment variables.

## Syncing these updates with your local clone

Because the code lives only in this workspace right now, there is no `work` branch on GitHub for you to pull. You have three ways to get the files locally:

1. **Apply the patch** – download `docs/work-update.patch` from this repo snapshot (or copy its contents) and run
   `git apply work-update.patch`. This recreates the Django restructure in your clone while preserving history. Full
   instructions live in [`docs/manual-sync-instructions.md`](docs/manual-sync-instructions.md).
2. **Import from a bundle** – if you receive an accompanying `it302-mco.bundle`, fetch it with
   `git fetch path/to/it302-mco.bundle work:agent-work` and merge/cherry-pick.
3. **Manual recreation** – only as a last resort, follow the manual steps in the same document to scaffold Django and move
   the templates/static assets by hand.

Once the changes exist on your machine, commit them to your own branch so future pulls work normally. When you're ready,
push that branch to GitHub and open a PR into `main`.

## Next steps

- Implement full authentication (Argon2 password hashing, encrypted email storage, rate limiting).
- Build the dynamic profile page and connect menu data to the database.
- Add automated tests to cover the authentication flows and key UX components.