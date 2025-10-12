"""Models to support cart management and order history."""
from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from menu.models import MenuItem


class Cart(models.Model):
    """Active shopping cart for a user."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover - human readable
        return f"Cart({self.user.username})"

    def total_items(self) -> int:
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    """Item stored in a user's cart."""

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["cart", "menu_item"]
        ordering = ["-added_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.menu_item.name} x{self.quantity}"

    @property
    def line_total(self) -> Decimal:
        return self.menu_item.base_price * self.quantity


class Order(models.Model):
    """Completed checkout captured for history purposes."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    contact_name = models.CharField(max_length=120)
    contact_phone = models.CharField(max_length=20, blank=True)
    special_instructions = models.TextField(blank=True)
    subtotal = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    tax = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Order #{self.pk} ({self.user.username})"

    def mark_confirmed(self) -> None:
        self.status = self.Status.CONFIRMED
        self.updated_at = timezone.now()
        self.save(update_fields=["status", "updated_at"])


class OrderItem(models.Model):
    """Line item captured at the time of checkout."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    menu_item_name = models.CharField(max_length=120)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField()

    class Meta:
        ordering = ["menu_item_name"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.menu_item_name} x{self.quantity}"

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity