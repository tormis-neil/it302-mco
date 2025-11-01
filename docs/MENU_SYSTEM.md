# Menu System Feature

## What It Is

The Menu System displays the café's product catalog to authenticated users, organized by categories (Espresso, Brewed Coffee, Bakery, etc.). It provides a read-only browsing interface showing menu items with descriptions, prices, and images. The system is built with query optimization to efficiently handle categories with multiple items.

## How It Works

### Database Structure

The menu system uses two related models:

1. **Category Model** (`menu.Category`) - Top-level grouping
   - name: Display name (e.g., "Espresso Drinks")
   - slug: URL-friendly identifier (e.g., "espresso-drinks")
   - kind: Classification (drink or food)
   - is_featured: Highlight on home page
   - display_order: Sort priority

2. **MenuItem Model** (`menu.MenuItem`) - Individual products
   - category: Foreign key to Category
   - name: Product name (e.g., "Cappuccino")
   - slug: URL-friendly identifier (e.g., "cappuccino")
   - description: Product details
   - base_price: Price in Philippine Pesos
   - image: Path to product image
   - is_available: Currently orderable
   - display_order: Sort priority within category

**Relationship**: Category (1) ← (Many) MenuItem

### Step-by-Step Menu Display Flow

**1. User Visits Menu Page** (`/menu/`)
   - GET request → `menu/views.py:57` (`catalog` view)
   - `@login_required` decorator checks authentication
   - If not logged in → Redirected to `/accounts/login/?next=/menu/`
   - If logged in → Menu page displayed

**2. Query Available Categories** (`menu/views.py:96`)
   ```python
   categories = _available_categories()
   ```

**3. Optimized Database Query** (`menu/views.py:28`)
   ```python
   def _available_categories():
       # Step 1: Create queryset for available items only
       item_queryset = MenuItem.objects.filter(is_available=True)

       # Step 2: Get categories that have available items
       # Step 3: Use prefetch_related to avoid N+1 queries
       return (
           Category.objects.filter(items__is_available=True)
           .distinct()  # Remove duplicate categories
           .prefetch_related(Prefetch("items", queryset=item_queryset))
           .order_by("display_order", "name")
       )
   ```

**Query Optimization Breakdown**:

**Without Optimization** (N+1 Problem):
```python
categories = Category.objects.all()  # 1 query

for cat in categories:
    items = cat.items.all()  # 1 query PER category!
# Total: 1 + N queries (where N = number of categories)
# Example: 6 categories = 7 queries
```

**With Optimization** (Prefetch Related):
```python
categories = Category.objects.prefetch_related('items').all()
# Query 1: SELECT * FROM menu_category
# Query 2: SELECT * FROM menu_menuitem WHERE category_id IN (1,2,3,4,5,6)
# Total: 2 queries (regardless of number of categories!)
```

**Additional Optimizations**:
- `.filter(items__is_available=True)`: Only categories with available items
- `.distinct()`: Remove duplicates from JOIN
- `Prefetch("items", queryset=...)`: Customize prefetched queryset
- `.order_by("display_order", "name")`: Consistent ordering

**4. Context Preparation** (`menu/views.py:99`)
   ```python
   context = {
       "categories": categories,  # QuerySet with prefetched items
   }
   ```

**5. Template Rendering** (`templates/menu/catalog.html`)
   ```django
   {% for category in categories %}
       <h2>{{ category.name }}</h2>
       <p>{{ category.description }}</p>

       {% for item in category.items.all %}
           <!-- No additional queries! Items already prefetched -->
           <div class="menu-item">
               <img src="{% static item.image %}" alt="{{ item.name }}">
               <h3>{{ item.name }}</h3>
               <p>{{ item.description }}</p>
               <p class="price">₱{{ item.base_price }}</p>
               <button disabled>Add to Cart</button> <!-- Placeholder -->
           </div>
       {% endfor %}
   {% endfor %}
   ```

### Menu Data Loading (Migration)

**Sample Data Seeded** (`menu/migrations/0002_seed_menu.py`):

**Categories Created**:
1. Espresso Drinks (kind=drink, display_order=1)
2. Brewed Coffee (kind=drink, display_order=2)
3. Specialty Drinks (kind=drink, display_order=3)
4. Bakery (kind=food, display_order=4)

**Sample Menu Items**:

**Espresso Category**:
- Espresso (₱95.00)
- Americano (₱115.00)
- Cappuccino (₱145.00)
- Latte (₱145.00)
- Mocha (₱165.00)

**Brewed Coffee Category**:
- Drip Coffee (₱105.00)
- French Press (₱125.00)
- Cold Brew (₱135.00)

**Specialty Category**:
- Caramel Macchiato (₱175.00)
- Vanilla Latte (₱165.00)
- Hazelnut Mocha (₱185.00)

**Bakery Category**:
- Croissant (₱85.00)
- Blueberry Muffin (₱95.00)
- Chocolate Chip Cookie (₱65.00)

**How Data is Loaded**:
```bash
python manage.py migrate menu
# Runs migration 0002_seed_menu.py
# Creates categories and menu items
```

### Slug Auto-Generation

**Purpose**: Create URL-friendly identifiers from names.

**Category Slug** (`menu/models.py:83`):
```python
def save(self, *args, **kwargs):
    if not self.slug:
        self.slug = slugify(self.name)
    super().save(*args, **kwargs)
```

**Example Transformations**:
- "Espresso Drinks" → "espresso-drinks"
- "Brewed Coffee" → "brewed-coffee"
- "Specialty Drinks" → "specialty-drinks"

**MenuItem Slug** (`menu/models.py:161`):
- "Caramel Macchiato" → "caramel-macchiato"
- "Chocolate Chip Cookie" → "chocolate-chip-cookie"

**Usage**: Prepared for potential detail page URLs (not implemented in MCO 1)

## Key Questions & Answers

### Q1: Why is the menu read-only?

**A:** **Cart functionality not implemented in MCO 1**.

**Current State**:
- Menu items displayed with prices
- "Add to Cart" buttons present but disabled (placeholder for UI)
- Focus is on displaying the menu catalog, not processing orders

**Code** (`templates/menu/catalog.html`):
```django
<button disabled class="btn-add-cart">Add to Cart</button>
<!-- Disabled - cart backend not implemented -->
```

### Q2: How does the query optimization work?

**A:** **Prefetch related** to avoid N+1 query problem.

**N+1 Problem Explained**:
```python
# BAD: Causes N+1 queries
categories = Category.objects.all()  # Query 1

for cat in categories:  # For each of N categories
    for item in cat.items.all():  # Query 2, 3, 4, ... N+1
        print(item.name)

# Result: 1 + N queries (slow!)
```

**Solution with Prefetch**:
```python
# GOOD: Only 2 queries
categories = Category.objects.prefetch_related('items').all()
# Query 1: SELECT * FROM menu_category
# Query 2: SELECT * FROM menu_menuitem WHERE category_id IN (...)

for cat in categories:  # For each category
    for item in cat.items.all():  # No query! Already loaded
        print(item.name)

# Result: 2 queries total (fast!)
```

**Even Better with Custom Queryset** (`menu/views.py:42`):
```python
item_queryset = MenuItem.objects.filter(is_available=True)

Category.objects.prefetch_related(
    Prefetch("items", queryset=item_queryset)
)
# Prefetch only available items, not all items
```

### Q3: Why use .distinct() in the query?

**A:** **Prevent duplicate categories** from JOIN.

**Problem Without distinct()**:
```python
Category.objects.filter(items__is_available=True)
# SQL: SELECT * FROM menu_category
#      INNER JOIN menu_menuitem ON ...
#      WHERE menu_menuitem.is_available = TRUE

# Result: If category has 3 items, category appears 3 times!
# Example:
# Espresso, Espresso, Espresso  (once per item)
# Brewed Coffee, Brewed Coffee
```

**Solution With distinct()**:
```python
Category.objects.filter(items__is_available=True).distinct()
# SQL adds: DISTINCT menu_category.id

# Result: Each category appears once
# Espresso
# Brewed Coffee
```

**Code** (`menu/views.py:47`):
```python
Category.objects.filter(items__is_available=True)
    .distinct()  # ← Removes duplicates from JOIN
```

### Q4: What happens if a category has no available items?

**A:** **Category is hidden** from menu.

**Filter Logic** (`menu/views.py:48`):
```python
Category.objects.filter(items__is_available=True)
# Only categories that have at least one available item
```

**Scenario**:
- Category: "Seasonal Specials"
- All items: `is_available=False` (out of season)
- Result: Category not shown on menu

**Use Case**: Temporarily hide categories without deleting them.

### Q5: How are prices stored and displayed?

**A:** **DecimalField** for accurate currency calculations.

**Storage** (`menu/models.py:135`):
```python
base_price = models.DecimalField(
    max_digits=6,   # Total digits: 999999
    decimal_places=2,  # 2 decimals: .99
    default=Decimal("0.00")
)
# Max value: ₱9999.99
```

**Why DecimalField (not FloatField)?**
- FloatField: Binary representation, rounding errors
  ```python
  # Float arithmetic errors
  0.1 + 0.2  # = 0.30000000000000004 (not exactly 0.3!)
  ```
- DecimalField: Exact decimal representation
  ```python
  # Decimal arithmetic exact
  Decimal("0.1") + Decimal("0.2")  # = 0.3 (exactly!)
  ```

**Display in Template**:
```django
<p class="price">₱{{ item.base_price }}</p>
<!-- Output: ₱145.00 -->

<!-- With formatting -->
<p class="price">₱{{ item.base_price|floatformat:2 }}</p>
<!-- Always shows 2 decimals: ₱145.00 -->
```

**Calculations** (future cart feature):
```python
# Line total
quantity = 2
line_total = item.base_price * quantity  # Decimal("290.00")

# Cart total
from django.db.models import Sum
total = cart.items.aggregate(
    total=Sum(F('menu_item__base_price') * F('quantity'))
)['total']
```

### Q6: Can menu items belong to multiple categories?

**A:** **No**, each item belongs to exactly one category.

**Relationship** (`menu/models.py:119`):
```python
category = models.ForeignKey(
    Category,
    on_delete=models.CASCADE,
    related_name="items"
)
# ForeignKey = Many-to-One (many items → one category)
```

**Constraint** (`menu/models.py:155`):
```python
class Meta:
    unique_together = ["category", "name"]
    # Can't have two items with same name in same category
```

**Why Not Many-to-Many?**
- Menu organization: Items logically belong to one category
- Simplicity: Easier to query and display
- Pricing: Price may differ if item in multiple categories
- If needed: Create separate MenuItem entry for each category

**Alternative Design** (if needed in future):
```python
# Many-to-Many relationship
categories = models.ManyToManyField(Category)

# Item can be in: Espresso AND Specialty
cappuccino.categories.add(espresso_category, specialty_category)
```

## Code References

| Component | File:Line | Description |
|-----------|-----------|-------------|
| Menu View | `menu/views.py:57` | Catalog display handler |
| Available Categories | `menu/views.py:28` | Optimized category query |
| Category Model | `menu/models.py:25` | Category data model |
| MenuItem Model | `menu/models.py:94` | Menu item data model |
| Menu Migration | `menu/migrations/0002_seed_menu.py` | Sample data seeding |
| Menu URL | `menu/urls.py` | `/menu/` route |
| Menu Template | `templates/menu/catalog.html` | Display template |

## Edge Cases

### 1. What if all items are unavailable?

**Scenario**: All menu items have `is_available=False`.

**Handling** (`menu/views.py:48`):
```python
Category.objects.filter(items__is_available=True)
# No items available → No categories returned
```

**Result**: Empty menu page with message "No items available."

**Template** (`templates/menu/catalog.html`):
```django
{% if categories %}
    {% for category in categories %}
        <!-- Display items -->
    {% endfor %}
{% else %}
    <p>No menu items available at this time.</p>
{% endif %}
```

### 2. What if category deleted?

**Scenario**: Admin deletes a category.

**Cascade Behavior** (`menu/models.py:119`):
```python
category = models.ForeignKey(Category, on_delete=models.CASCADE)
# CASCADE: Delete all items when category deleted
```

**Process**:
1. Category "Espresso" deleted
2. All items in that category deleted (Cappuccino, Latte, etc.)
3. Orders referencing those items: PROTECTED (can't delete if in orders)

**Protection** (`orders/models.py:351`):
```python
menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
# PROTECT: Can't delete item if referenced in any order
```

### 3. What if duplicate item names in different categories?

**Scenario**: "Latte" in both Espresso and Specialty categories.

**Allowed**:
```python
# Unique constraint only within category
class Meta:
    unique_together = ["category", "name"]

# This is allowed:
MenuItem.objects.create(category=espresso, name="Latte", price=145)
MenuItem.objects.create(category=specialty, name="Latte", price=175)

# This is NOT allowed (duplicate in same category):
MenuItem.objects.create(category=espresso, name="Latte", price=155)  # Error!
```

### 4. What if item price changes after order placed?

**Scenario**: Cappuccino price changes from ₱145 to ₱155.

**Protection** (`orders/models.py:353`):
```python
# OrderItem stores snapshot at time of order
menu_item_name = models.CharField(max_length=120)  # Snapshot name
unit_price = models.DecimalField(max_digits=8, decimal_places=2)  # Snapshot price
```

**Process**:
1. User orders Cappuccino at ₱145 (Jan 1)
2. Price increased to ₱155 (Feb 1)
3. User's order history shows ₱145 (what they paid)
4. New orders show ₱155 (current price)

**Code** (future cart feature):
```python
# When creating order
OrderItem.objects.create(
    order=order,
    menu_item=cappuccino,  # Reference for item
    menu_item_name=cappuccino.name,  # Snapshot name
    unit_price=cappuccino.base_price,  # Snapshot price (₱145)
    quantity=2
)
```

### 5. What if no categories exist?

**Scenario**: Database empty, no categories created.

**Handling**:
```python
categories = _available_categories()
# Returns empty QuerySet []
```

**Result**: Empty menu page.

**Solution**: Run migration to seed data:
```bash
python manage.py migrate menu
# Runs 0002_seed_menu.py, creates sample data
```

## Testing Guide

### Manual Testing Checklist

#### Test 1: View Menu
1. [ ] Log out (if logged in)
2. [ ] Visit `/menu/`
3. [ ] **Expected**: Redirected to `/accounts/login/?next=/menu/`
4. [ ] Log in
5. [ ] **Expected**: Redirected to `/menu/`, menu displayed
6. [ ] **Verify**:
   - [ ] Categories shown (Espresso, Brewed Coffee, etc.)
   - [ ] Items shown under each category
   - [ ] Prices displayed (₱95.00 format)
   - [ ] Images loaded (if configured)
   - [ ] "Add to Cart" buttons disabled

#### Test 2: Menu Data Verification
1. [ ] Check categories exist:
   ```python
   from menu.models import Category
   Category.objects.all().count()  # Should be 4+
   ```
2. [ ] Check items exist:
   ```python
   from menu.models import MenuItem
   MenuItem.objects.all().count()  # Should be 15+
   ```
3. [ ] Check category-item relationships:
   ```python
   espresso = Category.objects.get(slug='espresso-drinks')
   espresso.items.count()  # Should be 5 (Espresso, Americano, etc.)
   ```

#### Test 3: Query Optimization
1. [ ] Enable query logging:
   ```python
   # Add to settings.py temporarily
   LOGGING = {
       'version': 1,
       'handlers': {'console': {'class': 'logging.StreamHandler'}},
       'loggers': {
           'django.db.backends': {
               'handlers': ['console'],
               'level': 'DEBUG',
           }
       }
   }
   ```
2. [ ] Visit `/menu/`
3. [ ] Check console output
4. [ ] **Expected**: Only 2-3 queries (not 1 per category)

#### Test 4: Item Availability
1. [ ] Mark item unavailable:
   ```python
   from menu.models import MenuItem
   item = MenuItem.objects.get(slug='cappuccino')
   item.is_available = False
   item.save()
   ```
2. [ ] Visit `/menu/`
3. [ ] **Expected**: Cappuccino not shown
4. [ ] Mark available again:
   ```python
   item.is_available = True
   item.save()
   ```
5. [ ] Refresh page
6. [ ] **Expected**: Cappuccino shown again

#### Test 5: Category Ordering
1. [ ] Check display order:
   ```python
   from menu.models import Category
   cats = Category.objects.order_by('display_order', 'name')
   for cat in cats:
       print(f"{cat.display_order}: {cat.name}")
   ```
2. [ ] Visit `/menu/`
3. [ ] **Expected**: Categories appear in display_order sequence

#### Test 6: Slug Generation
1. [ ] Create new category without slug:
   ```python
   cat = Category.objects.create(
       name="Test Category",
       kind="drink"
   )
   print(cat.slug)  # Should be "test-category"
   ```
2. [ ] Create new item without slug:
   ```python
   item = MenuItem.objects.create(
       category=cat,
       name="Test Item",
       base_price=100.00
   )
   print(item.slug)  # Should be "test-item"
   ```

#### Test 7: Price Display
1. [ ] Visit `/menu/`
2. [ ] Check price format
3. [ ] **Expected**: All prices show ₱ symbol and 2 decimals
4. [ ] Check HTML source
5. [ ] **Verify**: Prices not rounded incorrectly

#### Test 8: Empty Menu
1. [ ] Mark all items unavailable:
   ```python
   MenuItem.objects.update(is_available=False)
   ```
2. [ ] Visit `/menu/`
3. [ ] **Expected**: "No items available" message
4. [ ] Mark items available:
   ```python
   MenuItem.objects.update(is_available=True)
   ```

### Automated Testing

Run menu tests:
```bash
python manage.py test menu
```

**Test Coverage** (`menu/tests.py`):
- Menu view requires login
- Categories displayed
- Available items shown
- Unavailable items hidden
- Query optimization (prefetch_related)

## Debugging Common Issues

### Issue 1: Menu page blank

**Symptom**: Visit `/menu/`, page loads but no items shown.

**Cause**: No menu data seeded.

**Solution**:
```bash
# Check if data exists
python manage.py shell
from menu.models import Category, MenuItem
print(Category.objects.count())  # Should be > 0
print(MenuItem.objects.count())  # Should be > 0

# If zero, run migration
python manage.py migrate menu
```

### Issue 2: N+1 query problem

**Symptom**: Many database queries when loading menu.

**Cause**: Missing `prefetch_related`.

**Debug**:
```python
# Check query count
from django.db import connection
from django.test.utils import override_settings

with override_settings(DEBUG=True):
    # Load menu page
    response = client.get('/menu/')
    print(f"Queries: {len(connection.queries)}")
    # Should be 2-3, not 10+
```

**Solution**: Ensure using `_available_categories()` helper (`menu/views.py:96`).

### Issue 3: Duplicate categories shown

**Symptom**: Same category appears multiple times.

**Cause**: Missing `.distinct()` in query.

**Solution** (`menu/views.py:49`):
```python
Category.objects.filter(items__is_available=True).distinct()
#                                               ^^^^^^^^^^^
```

### Issue 4: Images not loading

**Symptom**: Broken image icons on menu items.

**Cause**: Static files not configured or images missing.

**Debug**:
1. Check `STATIC_URL` in settings: `/static/`
2. Check image path in database: `img/cappuccino.jpg`
3. Verify file exists: `static/img/cappuccino.jpg`
4. Check template uses `{% static %}`:
   ```django
   {% load static %}
   <img src="{% static item.image %}">
   ```

**Solution**:
- Add images to `static/img/` folder
- Or update `item.image` to correct path
- Run `python manage.py collectstatic` (production)

### Issue 5: Price showing too many decimals

**Symptom**: Price shows as ₱145.000000

**Cause**: Template not formatting decimal.

**Solution** (`templates/menu/catalog.html`):
```django
<!-- Good -->
₱{{ item.base_price|floatformat:2 }}

<!-- Or -->
₱{{ item.base_price|floatformat }}
```

## Database Schema

### Category Table

```sql
CREATE TABLE menu_category (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(120) UNIQUE NOT NULL,
    description TEXT,
    kind VARCHAR(10) NOT NULL,  -- 'drink' or 'food'
    is_featured BOOLEAN DEFAULT 0,
    display_order INTEGER DEFAULT 0
);

CREATE INDEX menu_category_slug_idx ON menu_category(slug);
```

### MenuItem Table

```sql
CREATE TABLE menu_menuitem (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    name VARCHAR(120) NOT NULL,
    slug VARCHAR(140) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    base_price DECIMAL(6,2) DEFAULT 0.00,
    image VARCHAR(255),
    is_available BOOLEAN DEFAULT 1,
    display_order INTEGER DEFAULT 0,

    FOREIGN KEY (category_id) REFERENCES menu_category(id) ON DELETE CASCADE,
    UNIQUE (category_id, name)  -- No duplicate names per category
);

CREATE INDEX menu_menuitem_slug_idx ON menu_menuitem(slug);
CREATE INDEX menu_menuitem_category_idx ON menu_menuitem(category_id);
```

## Security Best Practices

1. **Authentication Required**:
   - `@login_required` decorator on view
   - Menu only accessible to logged-in users
   - Prevents public scraping of menu/prices

2. **Read-Only Access**:
   - `@require_GET` decorator (no POST)
   - Users cannot modify menu via this view
   - Admin panel required for menu changes

3. **Input Validation**:
   - Slug auto-generated (no user input)
   - Price stored as Decimal (no injection)
   - Category kind restricted to choices

4. **Query Optimization**:
   - Prefetch related (performance security)
   - Prevents DoS via N+1 queries
   - Fast response times
