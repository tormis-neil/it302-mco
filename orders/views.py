"""
Placeholder ordering views for the authenticated dashboard.

Views:
- cart_view(): Display cart with sample data
- checkout(): Display checkout form with sample data
- history(): Display order history with sample data

Current Status: UI PROTOTYPE ONLY
- Shows placeholder/sample data
- Cannot actually add items to cart
- Cannot process real orders
- All data is generated on-the-fly for display

Purpose: Demonstrate UI layout and user experience
Future: Will connect to Cart and Order models (Phase 2)

Related Files:
- orders/models.py: Cart and Order models (not used yet)
- orders/forms.py: Cart and checkout forms (not used yet)
- templates/orders/*.html: Display templates
"""

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

# Sales tax rate for calculations (8%)
SALES_TAX_RATE = Decimal("0.08")


@dataclass
class SampleCartEntry:
    """
    Serializable representation of a cart line item.
    
    Purpose: Temporary data structure for displaying sample cart data
    
    Fields:
    - menu_item: MenuItem object from database
    - quantity: How many of this item
    - line_total: Calculated total (price × quantity)
    
    Note: This is NOT the real CartItem model
    Future: Will be replaced by actual Cart/CartItem queries
    """
    menu_item: MenuItem
    quantity: int
    line_total: Decimal


def _sample_cart() -> tuple[list[SampleCartEntry], Decimal, Decimal, Decimal]:
    """
    Create a deterministic cart preview using available menu items.
    
    Purpose: Generate fake cart data to show UI layout
    
    Process:
    1. Get first 3 available menu items from database
    2. Assign quantities [1, 2, 1] to each item
    3. Calculate line totals (price × quantity)
    4. Calculate subtotal (sum of line totals)
    5. Calculate tax (subtotal × 8%)
    6. Calculate total (subtotal + tax)
    
    Returns:
        Tuple of (cart_entries, subtotal, tax, total)
    
    Example Output:
        entries = [
            SampleCartEntry(cappuccino, 1, 145.00),
            SampleCartEntry(croissant, 2, 170.00),
            SampleCartEntry(cold_brew, 1, 150.00)
        ]
        subtotal = 465.00
        tax = 37.20 (465.00 × 0.08)
        total = 502.20
    
    Note: Data is generated fresh on each page load (not persistent)
    """
    # Get first 3 available menu items
    menu_items = list(MenuItem.objects.filter(is_available=True)[:3])
    
    # If no menu items exist, return empty cart
    if not menu_items:
        return [], Decimal("0.00"), Decimal("0.00"), Decimal("0.00")

    # Assign quantities to items
    quantities = [1, 2, 1]
    entries: List[SampleCartEntry] = []
    subtotal = Decimal("0.00")
    
    # Create cart entries
    for index, item in enumerate(menu_items):
        quantity = quantities[index % len(quantities)]
        
        # Calculate line total and round to 2 decimals
        line_total = (item.base_price * quantity).quantize(
            Decimal("0.01"), 
            rounding=ROUND_HALF_UP
        )
        
        subtotal += line_total
        
        entries.append(
            SampleCartEntry(
                menu_item=item, 
                quantity=quantity, 
                line_total=line_total
            )
        )

    # Calculate tax (8% of subtotal)
    tax = (subtotal * SALES_TAX_RATE).quantize(
        Decimal("0.01"), 
        rounding=ROUND_HALF_UP
    )
    
    # Calculate total
    total = subtotal + tax
    
    return entries, subtotal, tax, total


def _sample_history() -> list[dict[str, object]]:
    """
    Build illustrative history entries for the dashboard UI.
    
    Purpose: Generate fake order history to show UI layout
    
    Process:
    1. Get sample cart data
    2. Create 2 fake orders with different statuses
    3. Generate order references (e.g., "BC-251018-001")
    4. Assign varying quantities and totals
    5. Add sample notes/instructions
    
    Returns:
        List of order dictionaries with sample data
    
    Example Output:
        [
            {
                'reference': 'BC-251018-001',
                'placed_at': datetime(2025, 10, 17, 14, 30),
                'status': 'processing',
                'status_label': 'Processing',
                'items': [
                    {'name': 'Cappuccino', 'quantity': 1, 'line_total': 145.00},
                    {'name': 'Croissant', 'quantity': 2, 'line_total': 170.00}
                ],
                'total': 315.00,
                'notes': 'Pay on pickup'
            },
            ...
        ]
    
    Note: Data is generated fresh on each page load (not from database)
    """
    # Get sample cart to use as base data
    cart_entries, _, _, _ = _sample_cart()
    
    # If no cart data, return empty history
    if not cart_entries:
        return []

    now = timezone.now()
    history: list[dict[str, object]] = []
    
    # Status options for sample orders
    status_cycle = [
        ("processing", "Processing"),
        ("confirmed", "Confirmed"),
        ("ready", "Ready for Pickup"),
    ]

    # Create 2 sample orders
    for index in range(1, min(3, len(cart_entries) + 1)):
        items_snapshot = []
        total = Decimal("0.00")
        
        # Build items for this order
        for offset, entry in enumerate(cart_entries[: index]):
            # Vary quantity to make orders look different
            quantity = entry.quantity + offset
            
            # Calculate line total
            line_total = (entry.menu_item.base_price * quantity).quantize(
                Decimal("0.01"), 
                rounding=ROUND_HALF_UP
            )
            
            total += line_total
            
            items_snapshot.append({
                "name": entry.menu_item.name,
                "quantity": quantity,
                "line_total": line_total,
            })

        # Get status for this order (cycles through status_cycle)
        status_code, status_label = status_cycle[(index - 1) % len(status_cycle)]
        
        # Create order dictionary
        history.append({
            "reference": f"BC-{now.strftime('%y%m%d')}-{index:03d}",  # e.g., "BC-251018-001"
            "placed_at": now - timedelta(days=index),  # Order from X days ago
            "status": status_code,
            "status_label": status_label,
            "items": items_snapshot,
            "total": total,
            "notes": "Pay on pickup" if index % 2 else "Add oat milk",  # Alternate notes
        })

    return history


@login_required  # Requires authentication
@require_GET     # Only allows GET requests
def cart_view(request: HttpRequest) -> HttpResponse:
    """
    Display the cart UI using placeholder data.
    
    Purpose: Show what cart will look like (UI prototype)
    
    Flow:
    1. Generate sample cart data
    2. Calculate totals (subtotal, tax, total)
    3. Pass to template for display
    
    Template Context:
    - sample_items: List of SampleCartEntry objects
    - subtotal: Sum of all line totals
    - tax: 8% of subtotal
    - total: subtotal + tax
    
    Current Limitations:
    - Shows sample data only (not user's real cart)
    - "Update" and "Remove" buttons disabled
    - "Proceed to Checkout" button disabled
    - Cannot actually modify cart
    
    URL: /orders/cart/
    
    Future Implementation (Phase 2):
    - Query user's actual Cart and CartItems
    - Enable add/remove/update functionality
    - Save changes to database
    - Redirect to real checkout
    
    Example:
        User visits: http://127.0.0.1:8000/orders/cart/
        Sees: Sample items with calculated totals
        Banner: "This is a preview mode..."
    """
    # Generate sample cart data
    items, subtotal, tax, total = _sample_cart()
    
    # Prepare context for template
    context = {
        "sample_items": items,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
    }
    
    # Render cart template
    return render(request, "orders/cart.html", context)


@login_required  # Requires authentication
@require_GET     # Only allows GET requests
def checkout(request: HttpRequest) -> HttpResponse:
    """
    Show the checkout layout without capturing real orders.
    
    Purpose: Show what checkout will look like (UI prototype)
    
    Flow:
    1. Generate sample cart data
    2. Get user's profile information for prefill
    3. Create sample contact info
    4. Pass to template for display
    
    Template Context:
    - sample_items: Items to be ordered (from cart)
    - subtotal, tax, total: Financial breakdown
    - contact_example: Pre-filled contact information
    
    Current Limitations:
    - Shows sample data only
    - Form fields are disabled
    - "Place Order" button disabled
    - Cannot actually submit order
    
    URL: /orders/checkout/
    
    Future Implementation (Phase 2):
    - Load user's real cart
    - Enable form fields
    - Validate checkout form
    - Create Order and OrderItems
    - Clear cart after successful order
    - Send confirmation email
    - Redirect to order confirmation page
    
    Example:
        User visits: http://127.0.0.1:8000/orders/checkout/
        Sees: Sample order summary + disabled checkout form
        Banner: "Checkout is in staging mode..."
    """
    # Generate sample cart data
    items, subtotal, tax, total = _sample_cart()
    
    # Get user's profile for contact info prefill
    profile = getattr(request.user, "profile", None)
    
    # Build sample contact info (prefilled from profile if exists)
    contact_example = {
        "name": (
            profile.display_name or 
            request.user.get_full_name() or 
            request.user.username
        ) if profile else (
            request.user.get_full_name() or 
            request.user.username
        ),
        "phone": getattr(profile, "phone_number", ""),
        "instructions": "We'll confirm your order details at the counter.",
    }
    
    # Prepare context for template
    context = {
        "sample_items": items,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
        "contact_example": contact_example,
    }
    
    # Render checkout template
    return render(request, "orders/checkout.html", context)


@login_required  # Requires authentication
@require_GET     # Only allows GET requests
def history(request: HttpRequest) -> HttpResponse:
    """
    Render recent order history cards with illustrative content.
    
    Purpose: Show what order history will look like (UI prototype)
    
    Flow:
    1. Generate sample order history
    2. Pass to template for display
    
    Template Context:
    - history_entries: List of sample order dictionaries
    
    Current Limitations:
    - Shows sample data only (not user's real orders)
    - Cannot view order details
    - Cannot reorder
    - Cannot cancel orders
    
    URL: /orders/history/
    
    Future Implementation (Phase 2):
    - Query user's actual orders from database
    - Show real order data with correct prices
    - Enable "Reorder" functionality
    - Enable "Cancel" for pending orders
    - Add order detail page
    - Add filtering (by status, date range)
    - Add pagination for many orders
    
    Example:
        User visits: http://127.0.0.1:8000/orders/history/
        Sees: 2 sample orders with different statuses
        Banner: "Showing sample order history..."
    """
    # Generate sample order history
    context = {
        "history_entries": _sample_history(),
    }
    
    # Render history template
    return render(request, "orders/history.html", context)