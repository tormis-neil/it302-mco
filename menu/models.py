"""
Database models representing the café menu.

Models:
- Category: Top-level grouping for menu items (e.g., "Brewed Coffee", "Espresso")
- MenuItem: Individual products available for ordering (e.g., "Cappuccino", "Cold Brew")

Relationships:
- Category (1) ←→ (Many) MenuItem via ForeignKey

Used by:
- menu/views.py: Queries categories and items for display
- orders/models.py: References MenuItem for cart/order items
- Migration 0002_seed_menu.py: Seeds sample menu data
"""

from __future__ import annotations

from decimal import Decimal

from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    """
    Top-level grouping for menu items (e.g., "Espresso", "Bakery").
    
    Purpose: Organizes menu items into logical groups for browsing
    
    Fields:
    - name: Display name (e.g., "Brewed Coffee")
    - slug: URL-friendly version (e.g., "brewed-coffee")
    - kind: Type classification (drink or food)
    - is_featured: Whether to highlight on home page
    - display_order: Sort order (lower numbers appear first)
    
    Relationships:
    - Has many MenuItems via category.items.all()
    - CASCADE delete: When category deleted, all its items deleted too
    
    Example:
        category = Category.objects.get(slug='espresso')
        items = category.items.all()  # Get all espresso drinks
    """

    class Kind(models.TextChoices):
        """
        Classification types for categories.
        
        DRINK: Beverages (coffee, tea, smoothies)
        FOOD: Edible items (bakery, sandwiches)
        """
        DRINK = "drink", "Drink"
        FOOD = "food", "Food"

    # Display name shown to users
    name = models.CharField(max_length=100, unique=True)
    
    # URL-friendly identifier (auto-generated from name)
    slug = models.SlugField(max_length=120, unique=True)
    
    # Optional description for category
    description = models.TextField(blank=True)
    
    # Classification: drink or food
    kind = models.CharField(max_length=10, choices=Kind.choices)
    
    # Whether to highlight this category on home page
    is_featured = models.BooleanField(default=False)
    
    # Sort order (lower = appears first)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        # Default ordering: by display_order, then name alphabetically
        ordering = ["display_order", "name"]

    def __str__(self) -> str:
        """Human-readable representation for Django admin."""
        return self.name

    def save(self, *args, **kwargs):
        """
        Auto-generate slug from name if not provided.
        
        Example: name="Brewed Coffee" → slug="brewed-coffee"
        """
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class MenuItem(models.Model):
    """
    Individual menu entry available for ordering.
    
    Purpose: Represents a single product customers can order
    
    Fields:
    - name: Product name (e.g., "Cappuccino")
    - description: Product details
    - base_price: Price in Philippine Pesos (e.g., 145.00)
    - is_available: Whether item can currently be ordered
    - image: Path to product image
    
    Relationships:
    - Belongs to one Category via ForeignKey
    - CASCADE delete: When category deleted, items deleted too
    - Referenced by CartItem and OrderItem (orders app)
    
    Example:
        item = MenuItem.objects.get(slug='cappuccino')
        print(f"{item.name}: ₱{item.base_price}")
        # Output: "Cappuccino: ₱145.00"
    """

    # Link to parent category (CASCADE: delete item if category deleted)
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name="items"
    )
    
    # Product name displayed to customers
    name = models.CharField(max_length=120)
    
    # URL-friendly identifier (auto-generated from name)
    slug = models.SlugField(max_length=140, unique=True)
    
    # Product description and details
    description = models.TextField()
    
    # Price in Philippine Pesos (max: 9999.99)
    base_price = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        default=Decimal("0.00")
    )
    
    # Path to product image (e.g., "img/cappuccino.jpg")
    image = models.CharField(max_length=255, blank=True)
    
    # Whether item is currently available for ordering
    is_available = models.BooleanField(default=True)
    
    # Sort order within category (lower = appears first)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        # Default ordering: by display_order, then name alphabetically
        ordering = ["display_order", "name"]
        
        # Prevent duplicate item names within same category
        unique_together = ["category", "name"]

    def __str__(self) -> str:
        """Human-readable representation for Django admin."""
        return self.name

    def save(self, *args, **kwargs):
        """
        Auto-generate slug from name if not provided.
        
        Example: name="Cold Brew" → slug="cold-brew"
        """
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)