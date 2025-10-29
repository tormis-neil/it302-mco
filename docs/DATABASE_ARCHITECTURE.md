# Database Architecture

## What It Is

The Brews & Chews database architecture implements a normalized relational schema using Django's ORM (Object-Relational Mapping) with SQLite as the database engine. The architecture supports user authentication, profile management, menu catalogs, shopping carts, and order processing with built-in email encryption for PII protection.

## Database Technology Stack

- **Database Engine**: SQLite 3 (development), PostgreSQL/MySQL ready for production
- **ORM Framework**: Django ORM 4.2+
- **Migration System**: Django migrations for schema versioning
- **Query Builder**: Django QuerySet API (SQL abstraction layer)
- **Database File**: `db.sqlite3` (located in project root)

## Core Database Models

### 1. User Model (`accounts.User`)

**Purpose**: Custom user model extending Django's `AbstractUser` with email encryption.

**File**: `accounts/models.py:82`

**Fields**:

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | BigAutoField | Primary key | Auto-increment |
| `username` | CharField(150) | Unique username | Unique, indexed |
| `password` | CharField(128) | Argon2 password hash | Required |
| `email` | EmailField | Plaintext email (legacy) | Deprecated |
| `encrypted_email` | BinaryField | AES-256-GCM encrypted email | Nullable |
| `email_digest` | CharField(64) | SHA-256 email digest | Unique, indexed |
| `first_name` | CharField(150) | First name | Optional |
| `last_name` | CharField(150) | Last name | Optional |
| `is_staff` | BooleanField | Staff access flag | Default: False |
| `is_superuser` | BooleanField | Admin access flag | Default: False |
| `is_active` | BooleanField | Account active flag | Default: True |
| `date_joined` | DateTimeField | Registration timestamp | Auto-set |
| `last_login` | DateTimeField | Last login timestamp | Auto-updated |

**Indexes**:
- Primary key: `id`
- Unique: `username`, `email_digest`
- Indexed: `username`, `email_digest` (for fast lookups)

**Relationships**:
- OneToOne → `Profile` (via `user.profile`)
- OneToMany → `AuthenticationEvent` (via `user.authentication_events.all()`)
- OneToOne → `Cart` (via `user.cart`)
- OneToMany → `Order` (via `user.orders.all()`)

**Email Encryption Details**:
- **encrypted_email**: Stores AES-256-GCM encrypted email
  - Format: `[12-byte nonce][ciphertext][16-byte auth tag]`
  - Total length: ~40-60 bytes (depends on email length)
- **email_digest**: SHA-256 hash for lookups
  - Length: Exactly 64 hex characters
  - Allows uniqueness checks without decryption
  - Case-insensitive (email normalized before hashing)

**Code Reference**: `accounts/models.py:82-260`

### 2. Profile Model (`accounts.Profile`)

**Purpose**: Extended user information and preferences.

**File**: `accounts/models.py:318`

**Fields**:

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | BigAutoField | Primary key | Auto-increment |
| `user` | OneToOneField | Link to User | Unique, CASCADE |
| `display_name` | CharField(120) | Display name | Optional |
| `phone_number` | CharField(20) | Contact phone | Optional |
| `favorite_drink` | CharField(120) | Preferred drink | Optional |
| `bio` | TextField | User bio | Optional |
| `updated_at` | DateTimeField | Last update time | Auto-updated |

**Relationships**:
- OneToOne → `User` (via `profile.user`)
- Reverse access: `user.profile`

**Auto-Creation**: Created automatically via signal when User is created (`accounts/models.py:347`)

**Code Reference**: `accounts/models.py:318-360`

### 3. AuthenticationEvent Model (`accounts.AuthenticationEvent`)

**Purpose**: Audit log for all authentication attempts (signup, login).

**File**: `accounts/models.py:262`

**Fields**:

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | BigAutoField | Primary key | Auto-increment |
| `event_type` | CharField(16) | 'signup' or 'login' | Choices |
| `ip_address` | GenericIPAddressField | Client IP (IPv4/IPv6) | Required |
| `username_submitted` | CharField(150) | Username entered | Optional |
| `email_submitted` | EmailField | Email entered | Optional |
| `user` | ForeignKey | Link to User (if found) | Nullable, SET_NULL |
| `successful` | BooleanField | Success flag | Default: False |
| `user_agent` | CharField(255) | Browser/device info | Optional |
| `metadata` | JSONField | Extra data | Default: {} |
| `created_at` | DateTimeField | Event timestamp | Auto-set |

**Indexes**:
- Primary key: `id`
- Composite index: `(event_type, ip_address, created_at)` for rate limiting queries

**Ordering**: Most recent first (`-created_at`)

**Use Cases**:
- Security monitoring (detect brute force attacks)
- Compliance (audit trail)
- User login history
- Forensics (investigate unauthorized access)

**Code Reference**: `accounts/models.py:262-316`

### 4. Category Model (`menu.Category`)

**Purpose**: Top-level grouping for menu items (e.g., "Espresso", "Bakery").

**File**: `menu/models.py:25`

**Fields**:

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | BigAutoField | Primary key | Auto-increment |
| `name` | CharField(100) | Display name | Unique |
| `slug` | SlugField(120) | URL-friendly name | Unique |
| `description` | TextField | Category description | Optional |
| `kind` | CharField(10) | 'drink' or 'food' | Choices |
| `is_featured` | BooleanField | Show on home page | Default: False |
| `display_order` | PositiveIntegerField | Sort order | Default: 0 |

**Relationships**:
- OneToMany → `MenuItem` (via `category.items.all()`)

**Ordering**: By `display_order`, then `name` alphabetically

**Slug Auto-Generation**: Slug created from name if not provided (`menu/models.py:89`)
- Example: `name="Brewed Coffee"` → `slug="brewed-coffee"`

**Code Reference**: `menu/models.py:25-92`

### 5. MenuItem Model (`menu.MenuItem`)

**Purpose**: Individual menu entries available for ordering.

**File**: `menu/models.py:94`

**Fields**:

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | BigAutoField | Primary key | Auto-increment |
| `category` | ForeignKey | Link to Category | CASCADE |
| `name` | CharField(120) | Product name | Required |
| `slug` | SlugField(140) | URL-friendly name | Unique |
| `description` | TextField | Product details | Required |
| `base_price` | DecimalField(6,2) | Price in PHP | Default: 0.00 |
| `image` | CharField(255) | Image path | Optional |
| `is_available` | BooleanField | Available for order | Default: True |
| `display_order` | PositiveIntegerField | Sort order | Default: 0 |

**Relationships**:
- ManyToOne → `Category` (via `menu_item.category`)
- Reverse: `category.items.all()`
- Referenced by: `CartItem`, `OrderItem`

**Constraints**:
- Unique together: `(category, name)` - No duplicate items in same category
- `base_price`: Max value 9999.99 PHP

**Ordering**: By `display_order`, then `name` alphabetically

**Code Reference**: `menu/models.py:94-169`

### 6. Cart Model (`orders.Cart`)

**Purpose**: Active shopping cart for a user.

**File**: `orders/models.py:42`

**Status**: Model exists, not yet used in views (Phase 2)

**Fields**:

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | BigAutoField | Primary key | Auto-increment |
| `user` | OneToOneField | Link to User | Unique, CASCADE |
| `created_at` | DateTimeField | Cart creation time | Auto-set |
| `updated_at` | DateTimeField | Last modification | Auto-updated |

**Relationships**:
- OneToOne → `User` (via `cart.user`)
- Reverse: `user.cart`
- OneToMany → `CartItem` (via `cart.items.all()`)

**Methods**:
- `total_items()`: Returns sum of all item quantities

**Lifecycle**:
- Created: When user first adds item
- Updated: When items added/removed/modified
- Cleared: After successful checkout

**Code Reference**: `orders/models.py:42-100`

### 7. CartItem Model (`orders.CartItem`)

**Purpose**: Individual items in a user's cart.

**File**: `orders/models.py:102`

**Status**: Model exists, not yet used in views (Phase 2)

**Fields**:

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | BigAutoField | Primary key | Auto-increment |
| `cart` | ForeignKey | Link to Cart | CASCADE |
| `menu_item` | ForeignKey | Link to MenuItem | CASCADE |
| `quantity` | PositiveIntegerField | Item quantity | Default: 1 |
| `added_at` | DateTimeField | When added to cart | Auto-set |

**Relationships**:
- ManyToOne → `Cart` (via `cart_item.cart`)
- ManyToOne → `MenuItem` (via `cart_item.menu_item`)

**Constraints**:
- Unique together: `(cart, menu_item)` - Can't add same item twice (update quantity instead)

**Ordering**: Newest items first (`-added_at`)

**Computed Property**:
- `line_total`: Returns `menu_item.base_price × quantity`

**Code Reference**: `orders/models.py:102-172`

### 8. Order Model (`orders.Order`)

**Purpose**: Completed checkout captured for history.

**File**: `orders/models.py:174`

**Status**: Model exists, not yet used in views (Phase 2)

**Fields**:

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | BigAutoField | Primary key (order number) | Auto-increment |
| `user` | ForeignKey | Link to User | CASCADE |
| `status` | CharField(20) | Order status | Choices, default: 'pending' |
| `contact_name` | CharField(120) | Customer name | Required |
| `contact_phone` | CharField(20) | Customer phone | Optional |
| `special_instructions` | TextField | Order notes | Optional |
| `subtotal` | DecimalField(8,2) | Items total | Default: 0.00 |
| `tax` | DecimalField(8,2) | Sales tax | Default: 0.00 |
| `total` | DecimalField(8,2) | Grand total | Default: 0.00 |
| `created_at` | DateTimeField | Order placed time | Auto-set |
| `updated_at` | DateTimeField | Last update time | Auto-updated |

**Status Choices**:
- `pending`: Order placed, awaiting confirmation
- `confirmed`: Staff confirmed, preparing
- `cancelled`: Order cancelled

**Relationships**:
- ManyToOne → `User` (via `order.user`)
- Reverse: `user.orders.all()`
- OneToMany → `OrderItem` (via `order.items.all()`)

**Ordering**: Newest orders first (`-created_at`)

**Methods**:
- `mark_confirmed()`: Updates status to 'confirmed'

**Code Reference**: `orders/models.py:174-302`

### 9. OrderItem Model (`orders.OrderItem`)

**Purpose**: Line items in a completed order (price snapshot).

**File**: `orders/models.py:304`

**Status**: Model exists, not yet used in views (Phase 2)

**Fields**:

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | BigAutoField | Primary key | Auto-increment |
| `order` | ForeignKey | Link to Order | CASCADE |
| `menu_item` | ForeignKey | Link to MenuItem | PROTECT |
| `menu_item_name` | CharField(120) | Name at time of order | Snapshot |
| `unit_price` | DecimalField(8,2) | Price at time of order | Snapshot |
| `quantity` | PositiveIntegerField | Quantity ordered | Required |

**Why Snapshots?**:
- Stores name and price **at time of order**
- Prevents issues if menu item name/price changes later
- Order history always shows what customer actually paid

**Relationships**:
- ManyToOne → `Order` (via `order_item.order`)
- ManyToOne → `MenuItem` (via `order_item.menu_item`, PROTECT)

**PROTECT Constraint**: Can't delete MenuItem if it's referenced in any order (prevents breaking order history)

**Ordering**: Alphabetically by `menu_item_name`

**Computed Property**:
- `line_total`: Returns `unit_price × quantity` (uses snapshot price)

**Code Reference**: `orders/models.py:304-390`

## Entity Relationship Diagram

```
┌─────────────────┐
│      User       │
│  (Custom Auth)  │
├─────────────────┤
│ id (PK)         │
│ username (UQ)   │
│ password        │
│ encrypted_email │
│ email_digest(UQ)│
└────────┬────────┘
         │ 1:1
         ├───────────────┐
         │               │
         ▼ 1:1           ▼ 1:N
  ┌──────────────┐  ┌──────────────────────┐
  │   Profile    │  │ AuthenticationEvent  │
  ├──────────────┤  ├──────────────────────┤
  │ id (PK)      │  │ id (PK)              │
  │ user (FK,UQ) │  │ user (FK,NULL)       │
  │ display_name │  │ event_type           │
  │ phone_number │  │ ip_address           │
  └──────────────┘  │ successful           │
                    │ created_at           │
                    └──────────────────────┘

┌──────────────┐
│   Category   │
├──────────────┤
│ id (PK)      │
│ name (UQ)    │
│ slug (UQ)    │
│ kind         │
└──────┬───────┘
       │ 1:N
       ▼
┌──────────────┐
│  MenuItem    │
├──────────────┤
│ id (PK)      │
│ category(FK) │
│ name         │
│ base_price   │
│ is_available │
└──────┬───────┘
       │
       │ Referenced by CartItem & OrderItem
       │
       ├────────────────┬────────────────┐
       │                │                │
       ▼                ▼                ▼
  ┌─────────┐    ┌──────────┐    ┌─────────────┐
  │  Cart   │ 1:N│ CartItem │    │  OrderItem  │
  ├─────────┤◄───┤──────────┤    ├─────────────┤
  │ id (PK) │    │ id (PK)  │    │ id (PK)     │
  │ user(FK)│    │ cart(FK) │    │ order (FK)  │
  └─────────┘    │ item(FK) │    │ item (FK)   │
                 │ quantity │    │ name        │
                 └──────────┘    │ unit_price  │
                                 │ quantity    │
       ┌─────────┐               └─────────────┘
       │  Order  │ 1:N                 ▲
       ├─────────┤─────────────────────┘
       │ id (PK) │
       │ user(FK)│
       │ status  │
       │ total   │
       └─────────┘
```

**Legend**:
- `PK`: Primary Key
- `FK`: Foreign Key
- `UQ`: Unique constraint
- `1:1`: One-to-One relationship
- `1:N`: One-to-Many relationship
- `CASCADE`: Delete cascade
- `PROTECT`: Prevent deletion
- `NULL/SET_NULL`: Nullable, set to NULL on delete

## Key Database Relationships

### 1. User → Profile (OneToOne)

**Relationship**: Each user has exactly one profile.

**Implementation**:
```python
# models.py
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
```

**Access**:
```python
# Forward: Profile → User
profile.user.username

# Reverse: User → Profile
user.profile.display_name
```

**Cascade Behavior**: Deleting user deletes profile (`CASCADE`)

**Auto-Creation**: Signal creates profile when user created (`accounts/models.py:347`)

### 2. User → AuthenticationEvent (OneToMany)

**Relationship**: User has many authentication events (login history).

**Implementation**:
```python
class AuthenticationEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="authentication_events")
```

**Access**:
```python
# All login events for user
user.authentication_events.all()

# Recent successful logins
user.authentication_events.filter(successful=True)[:5]
```

**Cascade Behavior**: Deleting user sets `user` field to NULL (`SET_NULL`)
- Events preserved for audit trail even if user deleted

### 3. Category → MenuItem (OneToMany)

**Relationship**: Category contains many menu items.

**Implementation**:
```python
class MenuItem(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="items")
```

**Access**:
```python
# All items in category
category.items.all()

# Available items only
category.items.filter(is_available=True)
```

**Cascade Behavior**: Deleting category deletes all its items (`CASCADE`)

**Constraint**: Unique together `(category, name)` prevents duplicate item names per category

### 4. User → Cart (OneToOne)

**Relationship**: Each user has exactly one cart.

**Implementation**:
```python
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cart")
```

**Access**:
```python
# Get user's cart (creates if doesn't exist)
cart, created = Cart.objects.get_or_create(user=request.user)

# Access via user
request.user.cart
```

**Cascade Behavior**: Deleting user deletes cart (`CASCADE`)

### 5. Cart → CartItem (OneToMany)

**Relationship**: Cart contains many cart items.

**Implementation**:
```python
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
```

**Access**:
```python
# All items in cart
cart.items.all()

# Total quantity
sum(item.quantity for item in cart.items.all())
```

**Constraint**: Unique together `(cart, menu_item)` prevents duplicate items

**Cascade Behavior**: Deleting cart deletes all cart items (`CASCADE`)

### 6. User → Order (OneToMany)

**Relationship**: User has many orders (order history).

**Implementation**:
```python
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
```

**Access**:
```python
# All orders for user
user.orders.all()

# Recent 5 orders
user.orders.all()[:5]

# Pending orders only
user.orders.filter(status='pending')
```

**Cascade Behavior**: Deleting user deletes orders (`CASCADE`)
- Consider `PROTECT` in production to preserve order records

### 7. Order → OrderItem (OneToMany)

**Relationship**: Order contains many order items (line items).

**Implementation**:
```python
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
```

**Access**:
```python
# All items in order
order.items.all()

# Calculate order total
sum(item.line_total for item in order.items.all())
```

**Cascade Behavior**:
- Deleting order deletes order items (`CASCADE`)
- **Cannot** delete menu item if referenced in order (`PROTECT`)

## Database Migrations

### Migration System

Django uses version-controlled migration files to track schema changes.

**Migration Files Location**:
- `accounts/migrations/`
- `menu/migrations/`
- `orders/migrations/`
- `pages/migrations/`

### Key Migrations

**1. Initial User Model** (`accounts/migrations/0001_initial.py`)
- Creates custom User model
- Creates Profile model
- Creates AuthenticationEvent model
- Sets up indexes and constraints

**2. Email Encryption** (`accounts/migrations/0002_add_email_encryption_fields.py`)
- Adds `encrypted_email` BinaryField
- Adds `email_digest` CharField with unique constraint
- Creates index on `email_digest`

**3. Encrypt Existing Emails** (`accounts/migrations/0003_encrypt_existing_emails.py`)
- Data migration: Encrypts existing plaintext emails
- Generates digests for existing users
- Non-reversible (one-way migration)

**4. Remove Legacy Security Fields** (`accounts/migrations/0004_remove_security_fields.py`)
- Removes deprecated rate limiting fields
- Cleans up legacy security implementation

**5. Menu Seeding** (`menu/migrations/0002_seed_menu.py`)
- Data migration: Populates sample menu items
- Creates categories: Espresso, Brewed Coffee, Bakery, etc.
- Creates menu items: Cappuccino, Latte, Croissant, etc.

### Running Migrations

```bash
# Apply all pending migrations
python manage.py migrate

# Create new migration after model changes
python manage.py makemigrations

# Show migration status
python manage.py showmigrations

# Reverse migration (rollback)
python manage.py migrate accounts 0001

# Show SQL for migration
python manage.py sqlmigrate accounts 0002
```

## Database Queries

### Common Query Patterns

**1. User Lookup by Email (with encryption)**:
```python
from accounts.models import User
from accounts.encryption import generate_email_digest

email = "alice@example.com"
digest = generate_email_digest(email)
user = User.objects.get(email_digest=digest)
```

**2. Get User Profile**:
```python
# Via reverse relationship
user = User.objects.get(username="alice")
profile = user.profile

# Or with select_related for efficiency
user = User.objects.select_related('profile').get(username="alice")
```

**3. Menu Items by Category**:
```python
from menu.models import Category, MenuItem

# Get category
category = Category.objects.get(slug='espresso')

# Get all items in category
items = category.items.filter(is_available=True)

# Or direct query
items = MenuItem.objects.filter(category__slug='espresso', is_available=True)
```

**4. User Order History**:
```python
# Get user's orders (newest first)
orders = user.orders.all()

# With items (avoid N+1 queries)
orders = user.orders.prefetch_related('items').all()

# Specific status
pending_orders = user.orders.filter(status='pending')
```

**5. Cart Operations**:
```python
from orders.models import Cart, CartItem

# Get or create cart
cart, created = Cart.objects.get_or_create(user=request.user)

# Add item to cart
item = MenuItem.objects.get(slug='cappuccino')
cart_item, created = CartItem.objects.get_or_create(
    cart=cart,
    menu_item=item,
    defaults={'quantity': 1}
)

# Update quantity if already in cart
if not created:
    cart_item.quantity += 1
    cart_item.save()

# Get cart total
total = sum(item.line_total for item in cart.items.all())
```

**6. Authentication Events**:
```python
from accounts.models import AuthenticationEvent

# Recent login attempts
recent = AuthenticationEvent.objects.filter(event_type='login')[:10]

# Failed login attempts from IP
failed = AuthenticationEvent.objects.filter(
    ip_address='192.168.1.100',
    successful=False,
    event_type='login'
)

# User login history
user.authentication_events.filter(successful=True).order_by('-created_at')
```

### Query Optimization Tips

**1. Use select_related for OneToOne/ForeignKey**:
```python
# Bad: N+1 queries
users = User.objects.all()
for user in users:
    print(user.profile.display_name)  # Query per user!

# Good: 1 query with JOIN
users = User.objects.select_related('profile').all()
for user in users:
    print(user.profile.display_name)  # No extra queries
```

**2. Use prefetch_related for Many relationships**:
```python
# Bad: N+1 queries
categories = Category.objects.all()
for cat in categories:
    items = cat.items.all()  # Query per category!

# Good: 2 queries total
categories = Category.objects.prefetch_related('items').all()
for cat in categories:
    items = cat.items.all()  # No extra queries
```

**3. Use only() to fetch specific fields**:
```python
# Bad: Fetch all fields
users = User.objects.all()  # Fetches all columns including encrypted_email

# Good: Fetch only needed fields
users = User.objects.only('id', 'username', 'email_digest')
```

**4. Use count() instead of len()**:
```python
# Bad: Fetches all records then counts in Python
count = len(User.objects.all())  # SELECT * then count in memory

# Good: COUNT(*) in database
count = User.objects.count()  # SELECT COUNT(*)
```

## Testing the Database

### Django Shell Queries

```bash
python manage.py shell
```

```python
# Test user creation
from accounts.models import User
user = User.objects.create_user(
    username='testuser',
    email='test@example.com',
    password='TestPass123!'
)
print(user.email_decrypted)  # Verify email encryption
print(user.profile.display_name)  # Verify profile auto-creation

# Test menu queries
from menu.models import Category, MenuItem
categories = Category.objects.all()
for cat in categories:
    print(f"{cat.name}: {cat.items.count()} items")

# Test authentication events
from accounts.models import AuthenticationEvent
events = AuthenticationEvent.objects.filter(event_type='login')[:5]
for event in events:
    print(f"{event.created_at}: {event.username_submitted} - {'✓' if event.successful else '✗'}")
```

### Database Inspection

```bash
# Open SQLite database
sqlite3 db.sqlite3

# List all tables
.tables

# Show table schema
.schema accounts_user

# Query users
SELECT id, username, email_digest FROM accounts_user;

# Count records
SELECT COUNT(*) FROM accounts_user;
SELECT COUNT(*) FROM menu_menuitem;

# Exit
.quit
```

### Manual Testing Checklist

**1. User Creation & Email Encryption**:
```python
from accounts.models import User
user = User.objects.create_user('alice', 'alice@example.com', 'Pass123!')
assert user.encrypted_email is not None
assert user.email_digest is not None
assert user.email_decrypted == 'alice@example.com'
```

**2. Profile Auto-Creation**:
```python
assert hasattr(user, 'profile')
assert user.profile.display_name == 'alice'
```

**3. Menu Relationships**:
```python
from menu.models import Category
cat = Category.objects.get(slug='espresso')
assert cat.items.count() > 0
```

**4. Unique Constraints**:
```python
# Try creating duplicate user (should fail)
try:
    User.objects.create_user('alice', 'alice2@example.com', 'Pass')
    assert False, "Should have raised IntegrityError"
except Exception as e:
    assert 'UNIQUE constraint' in str(e)
```

## Security Considerations

**1. Email Encryption**:
- Emails encrypted with AES-256-GCM before storage
- Digest allows lookups without decryption
- Encryption key stored in environment variable (never committed)

**2. Password Hashing**:
- Passwords hashed with Argon2 (memory-hard, GPU-resistant)
- Never stored in plaintext
- Hashes include unique salt per password

**3. Audit Logging**:
- All authentication attempts logged
- Enables security monitoring and forensics
- IP addresses tracked for rate limiting

**4. Cascade Deletes**:
- User deletion cascades to Profile, Cart
- AuthenticationEvents preserved (SET_NULL) for audit trail
- OrderItems protected from menu item deletion (PROTECT)

**5. Indexes**:
- `email_digest` indexed for fast lookups
- Composite index on AuthenticationEvent for rate limiting queries

## Debugging Database Issues

### Issue 1: "No such table" errors

**Cause**: Migrations not applied.

**Fix**:
```bash
python manage.py migrate
```

### Issue 2: Email encryption errors

**Cause**: Missing or invalid encryption key.

**Debug**:
```python
from django.conf import settings
import base64

key = settings.ACCOUNT_EMAIL_ENCRYPTION_KEY
key_bytes = base64.b64decode(key)
print(f"Key length: {len(key_bytes)} bytes (should be 32)")
```

**Fix**: Set valid key in `.env`.

### Issue 3: Duplicate key errors

**Cause**: Violating unique constraint.

**Debug**:
```python
# Check existing values
User.objects.filter(username__iexact='alice').exists()
User.objects.filter(email_digest='abc123...').exists()
```

**Fix**: Use different username/email.

### Issue 4: Migration conflicts

**Cause**: Conflicting migration files.

**Fix**:
```bash
# Show migration status
python manage.py showmigrations

# Fake migration if already applied manually
python manage.py migrate --fake accounts 0003

# Or squash migrations
python manage.py squashmigrations accounts 0001 0004
```

## Production Considerations

**1. Database Engine**:
- SQLite: Development only (not recommended for production)
- PostgreSQL: Recommended for production
- MySQL: Alternative option

**2. Database Optimization**:
- Add database indexes for frequently queried fields
- Use connection pooling
- Configure query caching
- Monitor slow queries

**3. Backup Strategy**:
- Regular automated backups
- Point-in-time recovery
- Backup encryption key separately
- Test restore procedures

**4. Scaling**:
- Read replicas for query distribution
- Database connection pooling
- Query optimization
- Caching layer (Redis/Memcached)

**5. Security**:
- Restrict database access (firewall rules)
- Use read-only credentials where possible
- Rotate encryption keys periodically
- Audit database access logs
