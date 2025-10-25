# Database Planning Overview

This document summarizes the relational structure that currently powers the Brews & Chews Django project and highlights the next database milestones.

## Core Entities

| Model | Purpose | Key Fields |
| --- | --- | --- |
| `accounts.User` | Custom user model extending `AbstractUser` with enhanced security features. | `username`, `email` (plaintext EmailField), `password` (Argon2 hash), lockout metadata (`failed_login_attempts`, `locked_until`) |
| `accounts.AuthenticationEvent` | Persists every signup/login attempt for auditing and rate limiting. | `event_type`, `ip_address`, `user`, `successful`, `metadata`, `created_at` |
| `accounts.Profile` | Stores profile details surfaced on the dashboard. | `user` one-to-one FK, `display_name`, `phone_number`, `favorite_drink`, `bio`, timestamps |
| `menu.Category` | High-level grouping for drinks and food. | `name`, `slug`, `description`, ordering fields |
| `menu.MenuItem` | Individual catalogue items displayed post-login. | `category` FK, `name`, `slug`, `description`, `base_price`, availability flags |
| `orders.Cart` / `orders.CartItem` | Tracks in-progress selections per user. | `user` one-to-one FK, `items` related manager, quantities, timestamps |
| `orders.Order` / `orders.OrderItem` | Represents submitted orders shown on the profile/history pages. | `user` FK, status enum, contact fields, monetary totals, timestamps |

## Security Considerations

* **Password hashing**: `PASSWORD_HASHERS` is anchored on Argon2 with secure fallbacks. Signup enforces Django's password validators (12+ characters, similarity checks, numeric guard) plus uppercase/number/special-character requirements.
* **Email storage**: Email addresses are stored as plaintext for usability (frequently accessed for login). For production deployments requiring PII encryption, consider implementing field-level encryption with `django-encrypted-model-fields` or similar.
* **Rate limiting**: Authentication events feed IP-based throttling and hour-long lockouts after repeated failures.
* **PII safeguards**: Profiles expose only opt-in contact data, while order history pulls from immutable snapshots that omit payment details.

## Next Steps

Finalize CRUD workflows for carts and checkouts so the order models transition from placeholders to transactional records.
* Introduce staff management tooling (menu availability toggles, order state updates) with appropriate permissions.
* Extend automated testing to cover the orders app once business logic lands, and add smoke tests for responsive front-end layouts.