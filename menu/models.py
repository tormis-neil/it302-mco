"""Database models representing the café menu."""
from __future__ import annotations

from decimal import Decimal

from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    """Top-level grouping for menu items."""

    class Kind(models.TextChoices):
        DRINK = "drink", "Drink"
        FOOD = "food", "Food"

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    kind = models.CharField(max_length=10, choices=Kind.choices)
    is_featured = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self) -> str:  # pragma: no cover - human readable
        return self.name

    def save(self, *args, **kwargs):  # pragma: no cover - slug autopopulate convenience
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class MenuItem(models.Model):
    """Individual menu entry available for ordering."""

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="items")
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField()
    base_price = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("0.00"))
    image = models.CharField(max_length=255, blank=True)
    is_available = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "name"]
        unique_together = ["category", "name"]

    def __str__(self) -> str:  # pragma: no cover - human readable
        return self.name

    def save(self, *args, **kwargs):  # pragma: no cover - slug autopopulate convenience
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)