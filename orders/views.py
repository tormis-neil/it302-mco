"""Placeholder ordering views for the authenticated dashboard."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import List

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from menu.models import MenuItem

SALES_TAX_RATE = Decimal("0.08")


@dataclass
class SampleCartEntry:
    """Serializable representation of a cart line item."""

    menu_item: MenuItem
    quantity: int
    line_total: Decimal


def _sample_cart() -> tuple[list[SampleCartEntry], Decimal, Decimal, Decimal]:
    """Create a deterministic cart preview using available menu items."""

    menu_items = list(MenuItem.objects.filter(is_available=True)[:3])
    if not menu_items:
        return [], Decimal("0.00"), Decimal("0.00"), Decimal("0.00")

    quantities = [1, 2, 1]
    entries: List[SampleCartEntry] = []
    subtotal = Decimal("0.00")
    for index, item in enumerate(menu_items):
        quantity = quantities[index % len(quantities)]
        line_total = (item.base_price * quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        subtotal += line_total
        entries.append(SampleCartEntry(menu_item=item, quantity=quantity, line_total=line_total))

    tax = (subtotal * SALES_TAX_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total = subtotal + tax
    return entries, subtotal, tax, total


def _sample_history() -> list[dict[str, object]]:
    """Build illustrative history entries for the dashboard UI."""

    cart_entries, _, _, _ = _sample_cart()
    if not cart_entries:
        return []

    now = timezone.now()
    history: list[dict[str, object]] = []
    status_cycle = [
        ("processing", "Processing"),
        ("confirmed", "Confirmed"),
        ("ready", "Ready for Pickup"),
    ]

    for index in range(1, min(3, len(cart_entries) + 1)):
        items_snapshot = []
        total = Decimal("0.00")
        for offset, entry in enumerate(cart_entries[: index]):
            quantity = entry.quantity + offset
            line_total = (entry.menu_item.base_price * quantity).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            total += line_total
            items_snapshot.append(
                {
                    "name": entry.menu_item.name,
                    "quantity": quantity,
                    "line_total": line_total,
                }
            )

        status_code, status_label = status_cycle[(index - 1) % len(status_cycle)]
        history.append(
            {
                "reference": f"BC-{now.strftime('%y%m%d')}-{index:03d}",
                "placed_at": now - timedelta(days=index),
                "status": status_code,
                "status_label": status_label,
                "items": items_snapshot,
                "total": total,
                "notes": "Pay on pickup" if index % 2 else "Add oat milk",
            }
        )

    return history


@login_required
@require_GET
def cart_view(request: HttpRequest) -> HttpResponse:
    """Display the cart UI using placeholder data."""

    items, subtotal, tax, total = _sample_cart()
    context = {
        "sample_items": items,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
    }
    return render(request, "orders/cart.html", context)


@login_required
@require_GET
def checkout(request: HttpRequest) -> HttpResponse:
    """Show the checkout layout without capturing real orders."""

    items, subtotal, tax, total = _sample_cart()
    profile = getattr(request.user, "profile", None)
    contact_example = {
        "name": profile.display_name or request.user.get_full_name() or request.user.username
        if profile
        else request.user.get_full_name() or request.user.username,
        "phone": getattr(profile, "phone_number", ""),
        "instructions": "We'll confirm your order details at the counter.",
    }
    context = {
        "sample_items": items,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
        "contact_example": contact_example,
    }
    return render(request, "orders/checkout.html", context)


@login_required
@require_GET
def history(request: HttpRequest) -> HttpResponse:
    """Render recent order history cards with illustrative content."""

    context = {
        "history_entries": _sample_history(),
    }
    return render(request, "orders/history.html", context)