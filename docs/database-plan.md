# Database Planning Overview

This document summarizes the relational structure we will implement in Django once we move from the static prototype to the fully functional reservation flow described in the PRD.

## Core Entities

| Model | Purpose | Key Fields |
| --- | --- | --- |
| `accounts.User` | Custom user model extending `AbstractUser` so we can enforce PRD security requirements. | `username`, `email` (AES-256 encrypted), `password` (Argon2 hash), `is_email_verified`, `failed_attempts`, `locked_until`, timestamps |
| `accounts.LoginAttempt` | Tracks authentication attempts for rate limiting and audit logs. | `user` FK (nullable for unknown users), `ip_address`, `user_agent`, `is_successful`, `created_at` |
| `accounts.Profile` | Stores customer-facing profile details surfaced in the PRD. | `user` OneToOne FK, `display_name`, `phone_number`, `favorite_drink`, `avatar` |
| `menu.Category` | Normalized grouping for menu items (drinks vs food). | `name`, `slug`, `type` (`Enum`: `drink`, `food`), `description`, `is_featured`, ordering fields |
| `menu.MenuItem` | Individual drink/food entries. | `category` FK, `name`, `slug`, `description`, `base_price`, `image`, `is_available`, `display_order` |
| `reservations.Reservation` | Represents the table/ drink reservation request from the PRD. | `user` FK, `menu_item` FK (nullable for table-only reservations), `party_size`, `reservation_at`, `special_request`, status fields |
| `reservations.Payment` | Stores payment confirmation metadata once the online payment flow is enabled. | `reservation` OneToOne FK, `provider_reference`, `amount`, `currency`, `status`, timestamps |

## Security Considerations

* **Password hashing**: Configure `PASSWORD_HASHERS` to prefer `argon2.PasswordHasher` with a fallback to Django’s defaults. This satisfies the PRD requirement for Argon2.
* **Email encryption**: Use `django-fernet-fields` or a lightweight wrapper around `cryptography.fernet` to transparently encrypt/decrypt the `email` field at rest. The sample static menu data shows how we will ultimately hydrate menu items before a database is ready.
* **Login throttling**: Store failed attempts in `LoginAttempt` and update `User.locked_until` after five failed tries within 15 minutes. The login form already surfaces the user-facing messaging for this behaviour.
* **PII separation**: Keep reservation/payment tables in a dedicated app (`reservations`) so we can apply stricter access controls and auditing middleware.

## Initial Migration Plan

1. **Custom user**: Create the `accounts` app migration that swaps in our custom user (`AUTH_USER_MODEL`). Include fields for lockouts and audit timestamps from the start to avoid disruptive schema changes later.
2. **Profile + LoginAttempt**: Add supporting tables and signals (e.g., create a `Profile` row on user creation).
3. **Menu scaffolding**: Port the structures from `pages/menu_data.py` into actual `Category` and `MenuItem` models. Seed fixtures with the existing sample content so the UI remains populated.
4. **Reservations**: Introduce reservation/payment tables with status enums (`pending`, `confirmed`, `cancelled`) and indexes on `reservation_at` + `user` for quick lookups.
5. **Data privacy**: Configure database-level constraints (unique email, unique reservation per timeslot + table) and add custom managers for filtering available menu items.

## Next Steps

* Finalize field choices (e.g., decimal precision for pricing, phone validation) and document them in model docstrings.
* Determine whether we need a separate table for `Table` inventory or if reservations are per menu item only; the PRD hints at table reservations, so we likely introduce a `Table` model with capacity + availability windows.
* Prepare ERD diagrams once migrations are drafted to keep documentation in sync with the PRD and onboarding material in the README.