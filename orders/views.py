"""
Order management views for the authenticated dashboard.

Views:
- add_to_cart(): Add menu item to user's cart
- update_cart_item(): Update item quantity in cart
- remove_from_cart(): Remove item from cart
- cart_view(): Display user's shopping cart
- checkout(): Process checkout and create order
- payment_success(): Handle successful payment return
- payment_cancel(): Handle cancelled payment
- retry_payment(): Retry payment for pending order
- history(): Display user's order history

Current Status: FULLY IMPLEMENTED
- Real cart functionality with database persistence
- PayMongo payment integration (Card, GCash, PayMaya)
- Order creation with reference numbers
- Order history with status tracking

Related Files:
- orders/models.py: Cart, CartItem, Order, OrderItem models
- orders/forms.py: CheckoutForm for contact information
- orders/payments.py: PayMongo API integration
- orders/webhooks.py: Payment webhook handlers
- templates/orders/*.html: Display templates
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import List

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from menu.models import MenuItem
from orders.forms import CheckoutForm
from orders.models import Cart, CartItem, Order, OrderItem

# Sales tax rate from settings (default 8%)
SALES_TAX_RATE = Decimal(getattr(settings, 'SALES_TAX_RATE', '0.08'))

# Order reference prefix from settings (default 'BC')
ORDER_PREFIX = getattr(settings, 'ORDER_REFERENCE_PREFIX', 'BC')


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_order_reference() -> str:
    """
    Generate a unique order reference number.

    Format: BC-YYMMDD-NNN
    - BC: Brews & Chews
    - YYMMDD: Year, Month, Day (e.g., 251116 = Nov 16, 2025)
    - NNN: Sequential number for that day (001, 002, etc.)

    Process:
    1. Get today's date in YYMMDD format
    2. Count existing orders created today
    3. Increment counter and zero-pad to 3 digits
    4. Combine into reference format

    Returns:
        Unique order reference string (e.g., "BC-251116-001")

    Example:
        First order on Nov 16, 2025 → "BC-251116-001"
        Second order same day → "BC-251116-002"
        First order next day → "BC-251117-001"
    """
    from datetime import date

    # Get today's date
    today = date.today()
    date_str = today.strftime("%y%m%d")  # YYMMDD format

    # Count orders created today
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = timezone.now().replace(hour=23, minute=59, second=59, microsecond=999999)

    order_count = Order.objects.filter(
        created_at__gte=today_start,
        created_at__lte=today_end
    ).count()

    # Next order number (1-indexed)
    next_number = order_count + 1

    # Format: {PREFIX}-YYMMDD-NNN (e.g., BC-251204-001)
    reference = f"{ORDER_PREFIX}-{date_str}-{next_number:03d}"

    return reference


# ============================================================================
# CART OPERATION VIEWS (Phase 1)
# ============================================================================

@login_required
@require_POST
@transaction.atomic
def add_to_cart(request: HttpRequest) -> HttpResponse:
    """
    Add a menu item to the user's cart or update quantity if already exists.

    Purpose: Handle "Add to Cart" button clicks from menu page

    Process:
    1. Get or create Cart for logged-in user
    2. Validate menu item exists and is available
    3. Check if item already in cart
    4. If exists: increase quantity
    5. If new: create CartItem
    6. Save changes and redirect back to menu

    POST Parameters:
    - menu_item_id: ID of menu item to add (required)
    - quantity: Number to add (default: 1)

    Returns:
        Redirect to menu page with success/error message

    Error Handling:
    - Invalid menu_item_id → 404 error
    - Item unavailable → error message, redirect to menu
    - Invalid quantity → validation error

    URL: /orders/cart/add/

    Example:
        POST /orders/cart/add/
        Data: {menu_item_id: 5, quantity: 2}
        Result: Adds 2x item #5 to user's cart
    """
    # Get menu item ID from POST data
    menu_item_id = request.POST.get('menu_item_id')

    if not menu_item_id:
        messages.error(request, "No item specified")
        return redirect('menu:catalog')

    # Get menu item or return 404
    menu_item = get_object_or_404(MenuItem, pk=menu_item_id)

    # Check if item is available
    if not menu_item.is_available:
        messages.error(request, f"{menu_item.name} is currently unavailable")
        return redirect('menu:catalog')

    # Get quantity from POST data (default: 1)
    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity < 1:
            raise ValueError("Quantity must be at least 1")
    except (ValueError, TypeError):
        messages.error(request, "Invalid quantity")
        return redirect('menu:catalog')

    # Get or create cart for user
    cart, created = Cart.objects.get_or_create(user=request.user)

    # Get or create cart item
    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart,
        menu_item=menu_item,
        defaults={'quantity': quantity}
    )

    # If item already exists, increase quantity
    if not item_created:
        cart_item.quantity += quantity
        cart_item.save()
        messages.success(request, f"Updated {menu_item.name} quantity to {cart_item.quantity}")
    else:
        messages.success(request, f"{menu_item.name} added to cart")

    return redirect('menu:catalog')


@login_required
@require_POST
@transaction.atomic
def update_cart_item(request: HttpRequest, cart_item_id: int) -> HttpResponse:
    """
    Update quantity of an existing cart item or delete if quantity is 0.

    Purpose: Handle quantity +/- buttons in cart page

    Process:
    1. Get CartItem by ID
    2. Verify it belongs to user's cart (security check)
    3. Get new quantity from POST data
    4. If quantity = 0: delete item
    5. If quantity > 0: update item
    6. Redirect back to cart

    POST Parameters:
    - quantity: New quantity (required)

    Security:
    - Verifies CartItem belongs to user's cart
    - Returns 403 if user tries to modify another user's cart

    Returns:
        Redirect to cart page with success/error message

    URL: /orders/cart/update/<cart_item_id>/

    Example:
        POST /orders/cart/update/5/
        Data: {quantity: 3}
        Result: Updates cart item #5 to quantity 3
    """
    # Get cart item or return 404
    cart_item = get_object_or_404(CartItem, pk=cart_item_id)

    # Security: Verify cart item belongs to user's cart
    if cart_item.cart.user != request.user:
        messages.error(request, "You don't have permission to modify this cart")
        return redirect('orders:cart')

    # Get new quantity from POST data
    try:
        new_quantity = int(request.POST.get('quantity', 0))
        if new_quantity < 0:
            raise ValueError("Quantity cannot be negative")
    except (ValueError, TypeError):
        messages.error(request, "Invalid quantity")
        return redirect('orders:cart')

    # If quantity is 0, delete the item
    if new_quantity == 0:
        item_name = cart_item.menu_item.name
        cart_item.delete()
        messages.success(request, f"{item_name} removed from cart")
    else:
        # Update quantity
        cart_item.quantity = new_quantity
        cart_item.save()
        messages.success(request, f"Updated {cart_item.menu_item.name} quantity to {new_quantity}")

    return redirect('orders:cart')


@login_required
@require_POST
@transaction.atomic
def remove_from_cart(request: HttpRequest, cart_item_id: int) -> HttpResponse:
    """
    Remove an item from the user's cart.

    Purpose: Handle "Remove" button clicks in cart page

    Process:
    1. Get CartItem by ID
    2. Verify it belongs to user's cart (security check)
    3. Delete the CartItem
    4. Redirect back to cart

    Security:
    - Verifies CartItem belongs to user's cart
    - Returns 403 if user tries to delete from another user's cart

    Returns:
        Redirect to cart page with success/error message

    URL: /orders/cart/remove/<cart_item_id>/

    Example:
        POST /orders/cart/remove/5/
        Result: Deletes cart item #5
    """
    # Get cart item or return 404
    cart_item = get_object_or_404(CartItem, pk=cart_item_id)

    # Security: Verify cart item belongs to user's cart
    if cart_item.cart.user != request.user:
        messages.error(request, "You don't have permission to modify this cart")
        return redirect('orders:cart')

    # Store item name before deleting
    item_name = cart_item.menu_item.name

    # Delete the cart item
    cart_item.delete()

    messages.success(request, f"{item_name} removed from cart")

    return redirect('orders:cart')


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
    Display the user's shopping cart with real data.

    Purpose: Show user's actual cart items and totals (Phase 1 Implementation)

    Flow:
    1. Get or create Cart for logged-in user
    2. Query CartItems with menu item details (optimized)
    3. Calculate totals (subtotal, tax, total)
    4. Pass to template for display

    Template Context:
    - cart_items: QuerySet of CartItem objects
    - subtotal: Sum of all line totals
    - tax: 8% of subtotal
    - total: subtotal + tax
    - item_count: Total number of items in cart

    Query Optimization:
    - Uses select_related('menu_item') to avoid N+1 queries
    - Loads cart items and menu details in single query

    URL: /orders/cart/

    Example:
        User visits: http://127.0.0.1:8000/orders/cart/
        Sees: Their actual cart items with real totals
        Can: Update quantities, remove items, proceed to checkout
    """
    # Get or create cart for user
    cart, created = Cart.objects.get_or_create(user=request.user)

    # Get cart items with menu item details (optimized query)
    cart_items = cart.items.select_related('menu_item').all()

    # Calculate totals
    subtotal = sum(item.line_total for item in cart_items)
    tax = (subtotal * SALES_TAX_RATE).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )
    total = subtotal + tax

    # Prepare context for template
    context = {
        "cart_items": cart_items,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
        "item_count": cart.total_items(),
    }

    # Render cart template
    return render(request, "orders/cart.html", context)


@login_required
@require_http_methods(["GET", "POST"])
@transaction.atomic
def checkout(request: HttpRequest) -> HttpResponse:
    """
    Handle checkout process - display form (GET) and create order with payment (POST).

    Purpose: Convert user's cart into an order and redirect to PayMongo for payment.

    GET Request Flow:
    1. Get user's cart (redirect if empty)
    2. Load cart items and calculate totals
    3. Pre-fill form with user's profile data
    4. Display checkout form

    POST Request Flow:
    1. Validate checkout form using CheckoutForm
    2. Create Order with status='pending'
    3. Create PayMongo checkout session
    4. Store checkout_session_id in order
    5. Clear user's cart
    6. Redirect to PayMongo checkout URL

    Template Context:
    - form: CheckoutForm instance
    - cart_items: User's cart items
    - subtotal, tax, total: Calculated totals

    Returns:
        GET: Checkout form template
        POST: Redirect to PayMongo checkout (success) or form with errors

    URL: /orders/checkout/
    """
    from orders.payments import create_checkout_session, PayMongoError

    # Get user's cart with items in single query
    cart = Cart.objects.filter(user=request.user).prefetch_related('items__menu_item').first()

    # Check if cart exists and has items
    if not cart or not cart.items.exists():
        messages.error(request, "Your cart is empty. Please add items before checkout.")
        return redirect('menu:catalog')

    # Get cart items (already prefetched)
    cart_items = cart.items.all()

    # Calculate totals
    subtotal = sum(item.line_total for item in cart_items)
    tax = (subtotal * SALES_TAX_RATE).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )
    total = subtotal + tax

    # Get profile for pre-filling form
    profile = getattr(request.user, "profile", None)

    # Pre-fill initial data from profile
    initial_data = {
        "contact_name": (
            profile.display_name or
            request.user.get_full_name() or
            request.user.username
        ) if profile else (
            request.user.get_full_name() or
            request.user.username
        ),
        "contact_phone": getattr(profile, "phone_number", "") if profile else "",
        "special_instructions": "",
    }

    # Handle POST request (create order and payment)
    if request.method == 'POST':
        form = CheckoutForm(request.POST)

        if form.is_valid():
            # Generate order reference
            order_reference = generate_order_reference()

            # Create order with validated form data
            order = Order.objects.create(
                user=request.user,
                status=Order.Status.PENDING,
                reference_number=order_reference,
                contact_name=form.cleaned_data['contact_name'],
                contact_phone=form.cleaned_data['contact_phone'],
                special_instructions=form.cleaned_data.get('special_instructions', ''),
                subtotal=subtotal,
                tax=tax,
                total=total,
            )

            # Create OrderItems from CartItems (snapshot pricing)
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    menu_item=cart_item.menu_item,
                    menu_item_name=cart_item.menu_item.name,
                    unit_price=cart_item.menu_item.base_price,
                    quantity=cart_item.quantity,
                )

            # Build callback URLs for PayMongo
            # Use the request to get the full URL with ngrok domain
            base_url = request.build_absolute_uri('/')[:-1]  # Remove trailing slash
            success_url = f"{base_url}/orders/payment/success/?order_id={order.pk}"
            cancel_url = f"{base_url}/orders/payment/cancel/?order_id={order.pk}"

            try:
                # Create PayMongo checkout session
                checkout_session_id, checkout_url = create_checkout_session(
                    order=order,
                    success_url=success_url,
                    cancel_url=cancel_url,
                )

                # Store checkout session ID in order
                order.checkout_session_id = checkout_session_id
                order.save(update_fields=['checkout_session_id'])

                # Clear cart (order is created, payment pending)
                cart_items.delete()

                # Redirect to PayMongo checkout
                return redirect(checkout_url)

            except PayMongoError as e:
                # Payment session creation failed - delete the order
                order.delete()
                messages.error(request, f"Payment initialization failed: {e.message}")

        else:
            # Form validation failed - show errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        # GET request - create form with pre-filled data
        form = CheckoutForm(initial=initial_data)

    # Prepare context
    context = {
        "form": form,
        "cart_items": cart_items,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
        # Keep contact_info for backwards compatibility with template
        "contact_info": {
            "name": form.data.get('contact_name', initial_data['contact_name']),
            "phone": form.data.get('contact_phone', initial_data['contact_phone']),
            "instructions": form.data.get('special_instructions', ''),
        }
    }

    return render(request, "orders/checkout.html", context)


@login_required
@require_GET
def history(request: HttpRequest) -> HttpResponse:
    """
    Display user's order history with real data.

    Purpose: Show user's past orders (Phase 2 Implementation)

    Flow:
    1. Query user's orders from database
    2. Include related OrderItems (optimized)
    3. Order by newest first
    4. Pass to template for display

    Template Context:
    - orders: QuerySet of Order objects with OrderItems

    Query Optimization:
    - Uses prefetch_related('items') to load OrderItems
    - Avoids N+1 queries when displaying order details

    URL: /orders/history/

    Example:
        User visits: http://127.0.0.1:8000/orders/history/
        Sees: Their actual order history with real data
        Can: View order details, status, and totals
    """
    # Query user's orders with related items (optimized)
    orders = Order.objects.filter(
        user=request.user
    ).prefetch_related('items').order_by('-created_at')

    # Prepare context
    context = {
        "orders": orders,
    }

    # Render history template
    return render(request, "orders/history.html", context)


# ============================================================================
# PAYMENT CALLBACK VIEWS (Phase 4 - PayMongo Integration)
# ============================================================================

@login_required
@require_GET
def payment_success(request: HttpRequest) -> HttpResponse:
    """
    Handle successful payment redirect from PayMongo.

    Purpose: Display success page after user completes payment on PayMongo.

    Flow:
    1. Get order_id from query string
    2. Verify order belongs to logged-in user (security)
    3. Check PayMongo API for payment status
    4. Update order status if payment is confirmed
    5. Display success page with order details

    Query Parameters:
    - order_id: The Order ID (required)

    Security:
    - Requires authentication
    - Verifies order belongs to current user
    - Returns 404 if order not found or doesn't belong to user

    URL: /orders/payment/success/?order_id=123

    Template Context:
    - order: The Order object
    - payment_confirmed: Boolean indicating if payment was verified
    """
    from orders.payments import get_checkout_session, PayMongoError

    # Get order ID from query string
    order_id = request.GET.get('order_id')

    if not order_id:
        messages.error(request, "Invalid payment callback - no order specified")
        return redirect('orders:history')

    # Get order and verify it belongs to user
    order = get_object_or_404(
        Order.objects.prefetch_related('items'),
        pk=order_id,
        user=request.user
    )

    # Check if order has a checkout session (indicates PayMongo was used)
    if not order.checkout_session_id:
        messages.error(request, "Invalid payment callback - order has no payment session")
        return redirect('orders:history')

    # Check PayMongo API for payment status (if order is still pending)
    payment_confirmed = False
    if order.status == Order.Status.PENDING:
        try:
            session_data = get_checkout_session(order.checkout_session_id)
            session_attrs = session_data.get("attributes", {})
            payment_status = session_attrs.get("payment_intent", {}).get("attributes", {}).get("status", "")

            # Check if payments array has successful payment
            payments = session_attrs.get("payments", [])
            if payments:
                payment = payments[0]
                payment_attrs = payment.get("attributes", {})
                payment_status = payment_attrs.get("status", "")

                if payment_status == "paid":
                    # Get payment method
                    source = payment_attrs.get("source", {})
                    payment_method = source.get("type", "unknown")

                    # Mark order as paid
                    order.mark_paid(
                        payment_intent_id=payment.get("id", ""),
                        payment_method=payment_method,
                    )
                    payment_confirmed = True

            # Also check checkout session status
            if not payment_confirmed and session_attrs.get("status") == "paid":
                order.mark_paid()
                payment_confirmed = True

        except PayMongoError:
            # If API call fails, just show the page without updating status
            pass

    # If order was already paid, consider it confirmed
    if order.status == Order.Status.PAID:
        payment_confirmed = True

    # Show appropriate message
    if payment_confirmed:
        messages.success(
            request,
            f"Payment successful for order {order.reference_number}! Your order is being prepared."
        )
    else:
        messages.info(
            request,
            f"Order {order.reference_number} received. Payment status: {order.get_status_display()}"
        )

    context = {
        "order": order,
        "page_title": "Payment Successful",
        "payment_confirmed": payment_confirmed,
    }

    return render(request, "orders/payment_success.html", context)


@login_required
@require_GET
def payment_cancel(request: HttpRequest) -> HttpResponse:
    """
    Handle cancelled payment redirect from PayMongo.

    Purpose: Display cancellation page when user cancels payment on PayMongo.

    Flow:
    1. Get order_id from query string
    2. Verify order belongs to logged-in user (security)
    3. Display cancellation page with options:
       - Retry payment (go back to checkout)
       - Cancel order completely

    Note: Order remains in 'pending' status until:
    - User retries and completes payment, OR
    - User explicitly cancels, OR
    - Order expires (future feature)

    Query Parameters:
    - order_id: The Order ID (required)

    Security:
    - Requires authentication
    - Verifies order belongs to current user
    - Returns 404 if order not found or doesn't belong to user

    URL: /orders/payment/cancel/?order_id=123

    Template Context:
    - order: The Order object with items
    - can_retry: Boolean indicating if retry is possible
    """
    # Get order ID from query string
    order_id = request.GET.get('order_id')

    if not order_id:
        messages.error(request, "Invalid payment callback - no order specified")
        return redirect('orders:history')

    # Get order with items and verify it belongs to user
    order = get_object_or_404(
        Order.objects.prefetch_related('items'),
        pk=order_id,
        user=request.user
    )

    # Only allow cancellation for pending orders
    can_retry = order.status == Order.Status.PENDING

    if can_retry:
        messages.warning(
            request,
            f"Payment was cancelled for order {order.reference_number}. "
            "You can try again or cancel the order."
        )
    else:
        messages.info(
            request,
            f"Order {order.reference_number} status: {order.get_status_display()}"
        )

    context = {
        "order": order,
        "can_retry": can_retry,
        "page_title": "Payment Cancelled",
    }

    return render(request, "orders/payment_cancel.html", context)


@login_required
@require_POST
@transaction.atomic
def retry_payment(request: HttpRequest, order_id: int) -> HttpResponse:
    """
    Retry payment for a pending order.

    Purpose: Allow users to retry payment for orders that are still pending.

    Flow:
    1. Get order by ID and verify ownership
    2. Check order is still pending
    3. Create new PayMongo checkout session
    4. Redirect to PayMongo checkout

    Security:
    - Requires authentication
    - Requires POST method (CSRF protected)
    - Verifies order belongs to current user
    - Only allows retry for pending orders

    URL: /orders/payment/retry/<order_id>/
    """
    from orders.payments import create_checkout_session, PayMongoError

    # Get order and verify ownership
    order = get_object_or_404(
        Order.objects.prefetch_related('items'),
        pk=order_id,
        user=request.user
    )

    # Only allow retry for pending orders
    if order.status != Order.Status.PENDING:
        messages.error(request, "This order cannot be paid - it's no longer pending.")
        return redirect('orders:history')

    # Build callback URLs
    base_url = request.build_absolute_uri('/')[:-1]
    success_url = f"{base_url}/orders/payment/success/?order_id={order.pk}"
    cancel_url = f"{base_url}/orders/payment/cancel/?order_id={order.pk}"

    try:
        # Create new PayMongo checkout session
        checkout_session_id, checkout_url = create_checkout_session(
            order=order,
            success_url=success_url,
            cancel_url=cancel_url,
        )

        # Update checkout session ID
        order.checkout_session_id = checkout_session_id
        order.save(update_fields=['checkout_session_id'])

        # Redirect to PayMongo checkout
        return redirect(checkout_url)

    except PayMongoError as e:
        messages.error(request, f"Payment initialization failed: {e.message}")
        return redirect('orders:history')