"""
Models to support cart management and order history.

Models:
- Cart: Active shopping cart for a user (one per user)
- CartItem: Individual items in a cart
- Order: Completed checkout captured for history
- OrderItem: Line items in a completed order

Current Status:
- Models exist but NOT connected to views yet
- UI shows placeholder data only
- Full implementation planned for Phase 2

Relationships:
- User (1) ←→ (1) Cart
- Cart (1) ←→ (Many) CartItem
- User (1) ←→ (Many) Order
- Order (1) ←→ (Many) OrderItem

Used by:
- orders/views.py: Currently shows sample data (not real cart/orders)
- Future: Will be used for actual order processing

Related Files:
- orders/views.py: Placeholder views with sample data
- orders/forms.py: Cart and checkout forms (ready for Phase 2)
- menu/models.py: MenuItem referenced by CartItem and OrderItem
"""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from menu.models import MenuItem


class Cart(models.Model):
    """
    Active shopping cart for a user.
    
    Purpose: Stores in-progress item selections before checkout
    
    Relationship:
    - OneToOne with User (each user has exactly one cart)
    - OneToMany with CartItem (cart can have multiple items)
    
    Lifecycle:
    - Created: When user first adds item to cart
    - Updated: When user adds/removes/updates items
    - Cleared: After successful checkout (items become OrderItems)
    
    Current Status: Model exists but not used yet (Phase 2)
    
    Example Usage (Future):
        user = request.user
        cart = user.cart  # Access user's cart
        total_items = cart.total_items()  # Get item count
        cart.items.all()  # Get all items in cart
    """

    # Link to user (OneToOne: each user has exactly one cart)
    # CASCADE: If user deleted, cart deleted too
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="cart"
    )
    
    # Timestamp when cart was first created
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Timestamp when cart was last modified (add/remove/update item)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        """Human-readable representation for Django admin."""
        return f"Cart({self.user.username})"

    def total_items(self) -> int:
        """
        Calculate total number of items in cart (including quantities).
        
        Example:
            Cart contains:
            - 2x Cappuccino
            - 3x Croissant
            - 1x Cold Brew
            
            total_items() returns: 6 (2 + 3 + 1)
        
        Returns:
            Total quantity of all items in cart
        """
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    """
    Individual item stored in a user's cart.
    
    Purpose: Represents one menu item + quantity in the cart
    
    Relationships:
    - Belongs to one Cart (ForeignKey)
    - References one MenuItem (ForeignKey)
    
    Unique Together:
    - (cart, menu_item): Can't have same item twice in cart
    - If user adds same item again, update quantity instead
    
    Current Status: Model exists but not used yet (Phase 2)
    
    Example Usage (Future):
        cart_item = CartItem.objects.create(
            cart=user.cart,
            menu_item=cappuccino,
            quantity=2
        )
        print(cart_item.line_total)  # Calculates price × quantity
    """

    # Link to parent cart
    # CASCADE: If cart deleted, cart items deleted too
    cart = models.ForeignKey(
        Cart, 
        on_delete=models.CASCADE, 
        related_name="items"
    )
    
    # Link to menu item being ordered
    # CASCADE: If menu item deleted, cart item deleted too
    # (Consider PROTECT in production to prevent menu changes breaking carts)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    
    # How many of this item user wants (1-10)
    quantity = models.PositiveIntegerField(default=1)
    
    # When item was added to cart
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Prevent duplicate items in same cart
        # User can't add Cappuccino twice; must update quantity
        unique_together = ["cart", "menu_item"]
        
        # Show newest items first in cart
        ordering = ["-added_at"]

    def __str__(self) -> str:
        """Human-readable representation for Django admin."""
        return f"{self.menu_item.name} x{self.quantity}"

    @property
    def line_total(self) -> Decimal:
        """
        Calculate total price for this cart item (price × quantity).
        
        Example:
            menu_item.base_price = 145.00 (Cappuccino)
            quantity = 2
            line_total = 145.00 × 2 = 290.00
        
        Returns:
            Total cost for this line item as Decimal
        """
        return self.menu_item.base_price * self.quantity


class Order(models.Model):
    """
    Completed checkout captured for history purposes.
    
    Purpose: Immutable record of a completed order
    
    Lifecycle:
    1. User completes checkout → Order created with status='pending'
    2. Staff confirms order → status='confirmed'
    3. Order prepared → status='ready' (future)
    4. Customer picks up → status='completed' (future)
    5. Or cancelled → status='cancelled'
    
    Relationships:
    - Belongs to one User (ForeignKey)
    - Has many OrderItems (line items snapshot at checkout)
    
    Data Snapshot:
    - OrderItems store name and price at time of order
    - Prevents issues if menu item price/name changes later
    - Order history always shows what customer actually paid
    
    Current Status: Model exists but not used yet (Phase 2)
    
    Example Usage (Future):
        order = Order.objects.create(
            user=request.user,
            contact_name="John Doe",
            subtotal=Decimal("435.00"),
            tax=Decimal("34.80"),
            total=Decimal("469.80")
        )
        order.mark_confirmed()  # Update status
    """

    class Status(models.TextChoices):
        """
        Order lifecycle states.

        PENDING: Order placed, awaiting payment
        PAID: Payment confirmed via PayMongo webhook
        CONFIRMED: Staff confirmed, preparing order
        CANCELLED: Order cancelled (by user or staff)
        FAILED: Payment failed

        Future statuses (Phase 3):
        - PREPARING: Being prepared by kitchen
        - READY: Ready for pickup
        - COMPLETED: Picked up by customer
        """
        PENDING = "pending", "Pending Payment"
        PAID = "paid", "Paid"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"
        FAILED = "failed", "Payment Failed"

    class PaymentMethod(models.TextChoices):
        """
        Payment methods supported by PayMongo.
        """
        CARD = "card", "Credit/Debit Card"
        GCASH = "gcash", "GCash"
        PAYMAYA = "paymaya", "PayMaya"
        GRAB_PAY = "grab_pay", "GrabPay"
        UNKNOWN = "unknown", "Unknown"

    # Link to user who placed the order
    # CASCADE: If user deleted, keep orders for audit (consider PROTECT)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="orders"
    )
    
    # Current order status (pending → confirmed → ready → completed)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    # Order reference number (e.g., BC-251116-001)
    reference_number = models.CharField(max_length=20, unique=True, blank=True)

    # Customer contact information (snapshot at checkout)
    contact_name = models.CharField(max_length=120)
    contact_phone = models.CharField(max_length=20, blank=True)
    
    # Special instructions from customer (e.g., "Extra hot", "No sugar")
    special_instructions = models.TextField(blank=True)
    
    # Financial totals (snapshot at checkout)
    # Max 999999.99 (6 digits, 2 decimals)
    subtotal = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=Decimal("0.00")
    )
    
    # Sales tax (8% in views.py)
    tax = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=Decimal("0.00")
    )
    
    # Grand total (subtotal + tax)
    total = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=Decimal("0.00")
    )
    
    # When order was placed
    created_at = models.DateTimeField(auto_now_add=True)

    # When order was last modified (status change, etc.)
    updated_at = models.DateTimeField(auto_now=True)

    # ═══════════════════════════════════════════════════════════════
    # PAYMENT FIELDS (PayMongo Integration)
    # ═══════════════════════════════════════════════════════════════

    # PayMongo Checkout Session ID
    # Created when user clicks "Pay Now", used to track the checkout
    checkout_session_id = models.CharField(max_length=100, blank=True)

    # PayMongo Payment Intent ID
    # Created after successful payment, contains payment details
    payment_intent_id = models.CharField(max_length=100, blank=True)

    # Payment method used (card, gcash, paymaya, etc.)
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        blank=True,
    )

    # When payment was confirmed (from PayMongo webhook)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        # Show newest orders first
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Human-readable representation for Django admin."""
        return f"Order #{self.pk} ({self.user.username})"

    def mark_paid(self, payment_intent_id: str = "", payment_method: str = "") -> None:
        """
        Mark order as paid after successful payment.

        Called by: PayMongo webhook handler

        Updates:
        - status: pending → paid
        - payment_intent_id: From PayMongo
        - payment_method: card/gcash/paymaya/etc.
        - paid_at: Current timestamp
        - updated_at: Current timestamp

        Args:
            payment_intent_id: PayMongo payment intent ID
            payment_method: Payment method used (card, gcash, etc.)
        """
        self.status = self.Status.PAID
        self.payment_intent_id = payment_intent_id
        self.payment_method = payment_method or self.PaymentMethod.UNKNOWN
        self.paid_at = timezone.now()
        self.updated_at = timezone.now()
        self.save(update_fields=[
            "status", "payment_intent_id", "payment_method", "paid_at", "updated_at"
        ])

    def mark_confirmed(self) -> None:
        """
        Mark order as confirmed by staff.

        Called by: Staff dashboard (future implementation)

        Updates:
        - status: paid → confirmed
        - updated_at: Current timestamp

        Example:
            order = Order.objects.get(pk=123)
            order.mark_confirmed()
            # Status now 'confirmed', updated_at refreshed
        """
        self.status = self.Status.CONFIRMED
        self.updated_at = timezone.now()
        self.save(update_fields=["status", "updated_at"])

    def mark_failed(self) -> None:
        """
        Mark order as failed due to payment failure.

        Called by: PayMongo webhook handler or timeout

        Updates:
        - status: pending → failed
        - updated_at: Current timestamp
        """
        self.status = self.Status.FAILED
        self.updated_at = timezone.now()
        self.save(update_fields=["status", "updated_at"])


class OrderItem(models.Model):
    """
    Line item captured at the time of checkout (price snapshot).
    
    Purpose: Immutable record of what was ordered and at what price
    
    Why Snapshot Data?
    - menu_item_name: Stores name at time of order
    - unit_price: Stores price at time of order
    - Even if menu item name/price changes later, order history stays accurate
    
    Example Scenario:
        2024-01-15: User orders "Cappuccino" at ₱145.00
        2024-02-01: Café increases price to ₱155.00
        User's order history still shows ₱145.00 (what they paid)
    
    Relationships:
    - Belongs to one Order (ForeignKey)
    - References one MenuItem (ForeignKey with PROTECT)
    
    PROTECT vs CASCADE:
    - PROTECT: Can't delete MenuItem if used in any order
    - Prevents: Accidentally breaking order history
    
    Current Status: Model exists but not used yet (Phase 2)
    
    Example Usage (Future):
        order_item = OrderItem.objects.create(
            order=order,
            menu_item=cappuccino,
            menu_item_name=cappuccino.name,      # Snapshot name
            unit_price=cappuccino.base_price,    # Snapshot price
            quantity=2
        )
        print(order_item.line_total)  # 145.00 × 2 = 290.00
    """

    # Link to parent order
    # CASCADE: If order deleted, order items deleted too
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, 
        related_name="items"
    )
    
    # Link to menu item (for reference only)
    # PROTECT: Can't delete menu item if it's in any order
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    
    # Snapshot of menu item name at time of order
    # Prevents issues if menu item renamed later
    menu_item_name = models.CharField(max_length=120)
    
    # Snapshot of price at time of order
    # Preserves what customer actually paid
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    
    # Quantity ordered
    quantity = models.PositiveIntegerField()

    class Meta:
        # Sort by item name alphabetically
        ordering = ["menu_item_name"]

    def __str__(self) -> str:
        """Human-readable representation for Django admin."""
        return f"{self.menu_item_name} x{self.quantity}"

    @property
    def line_total(self) -> Decimal:
        """
        Calculate total price for this order item (price × quantity).
        
        Uses snapshot price, not current menu price.
        
        Example:
            unit_price = 145.00 (snapshot from checkout)
            quantity = 2
            line_total = 145.00 × 2 = 290.00
            
            Even if current menu price is now ₱155.00,
            this still returns ₱290.00 (what was paid)
        
        Returns:
            Total cost for this line item as Decimal
        """
        return self.unit_price * self.quantity