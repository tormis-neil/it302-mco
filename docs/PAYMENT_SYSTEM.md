# Payment System (PayMongo Integration)

## What It Is

The payment system allows customers to pay for their orders online using **PayMongo**, a Philippine payment gateway. Customers can pay using:

- **Credit/Debit Card** (Visa, Mastercard)
- **GCash** (e-wallet)
- **PayMaya** (e-wallet)

When a customer clicks "Place Order", they are redirected to PayMongo's secure checkout page where they complete payment. After payment, they return to the website and see their order confirmation.

---

## How It Works

Think of it like ordering food through a delivery app:

1. **You add items to your cart** → Cart page shows your items
2. **You click checkout** → Enter your contact info
3. **You click "Place Order"** → Redirected to PayMongo (like being sent to a cashier)
4. **You pay** → Choose payment method and complete payment
5. **You come back** → See order confirmation page
6. **Café gets notified** → PayMongo tells the website "payment received!"

### Visual Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   1. Cart   │────▶│ 2. Checkout │────▶│  3. PayMongo │────▶│  4. Success │
│  (Website)  │     │  (Website)  │     │   (Payment)  │     │  (Website)  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
     │                    │                    │                    │
     │ Add items          │ Enter contact      │ Pay with           │ Order
     │ to cart            │ information        │ Card/GCash/Maya    │ confirmed!
     └────────────────────┴────────────────────┴────────────────────┘
```

---

## Step-by-Step Payment Process

### Step 1: User Clicks "Place Order"

**What happens behind the scenes:**

1. User fills checkout form (name, phone, instructions)
2. Form is validated (`orders/views.py:617-620`)
3. Order is created in database with status "pending" (`orders/views.py:625-635`)
4. Order items are saved with current prices (`orders/views.py:638-645`)

**Code Reference:**
```python
# orders/views.py:625-635
order = Order.objects.create(
    user=rquest.user,
    status=Order.Status.PENDING,
    reference_number=order_reference,
    contact_name=form.cleaned_data['contact_name'],
    contact_phone=form.cleaned_data['contact_phone'],
    special_instructions=form.cleaned_data.get('special_instructions', ''),
    subtotal=subtotal,
    tax=tax,
    total=total,
)
```

### Step 2: Create PayMongo Checkout Session

**What happens behind the scenes:**

1. Website calls PayMongo API to create a "checkout session"
2. Sends: order total, item names, quantities, prices
3. PayMongo returns: checkout URL where user will pay
4. Order stores the checkout session ID for later verification

**Code Reference:**
```python
# orders/payments.py:126-202
def create_checkout_session(order, success_url, cancel_url):
    # Convert total to centavos (PayMongo uses smallest currency unit)
    amount_centavos = int(order.total * 100)

    # Build line items from order items
    line_items = []
    for item in order.items.all():
        line_items.append({
            "currency": "PHP",
            "amount": int(item.unit_price * 100),
            "name": item.menu_item_name,
            "quantity": item.quantity,
        })

    # Create checkout session
    payload = {
        "data": {
            "attributes": {
                "payment_method_types": ["card", "gcash", "paymaya"],
                "line_items": line_items,
                "success_url": success_url,
                "cancel_url": cancel_url,
            }
        }
    }

    # Call PayMongo API
    response = _make_request("POST", "/checkout_sessions", payload)
    return session_id, checkout_url
```

### Step 3: User Pays on PayMongo

**What the user sees:**

1. Redirected to PayMongo's hosted checkout page
2. Sees order summary (items, quantities, total)
3. Chooses payment method (Card, GCash, or PayMaya)
4. Completes payment:
   - **Card**: Enter card details
   - **GCash**: Opens GCash app/website
   - **PayMaya**: Opens PayMaya app/website

**Important:** The website does NOT handle card numbers. PayMongo handles all sensitive payment data securely.

### Step 4: Payment Completed - User Returns

**If payment successful:**

1. PayMongo redirects to success URL: `/orders/payment/success/?order_id=123`
2. Website checks PayMongo API to verify payment (`orders/views.py:802-833`)
3. Order status updated to "paid" (`orders/views.py:820-824`)
4. User sees success page with order details

**Code Reference:**
```python
# orders/views.py:820-824
if payment_status == "paid":
    order.mark_paid(
        payment_intent_id=payment.get("id", ""),
        payment_method=payment_method,
    )
    payment_confirmed = True
```

**If payment cancelled:**

1. PayMongo redirects to cancel URL: `/orders/payment/cancel/?order_id=123`
2. Order remains in "pending" status
3. User sees cancel page with options:
   - **Retry Payment**: Try paying again
   - **View Order History**: Go to order history

### Step 5: Webhook Notification (Background)

**What happens behind the scenes:**

PayMongo sends a "webhook" (notification) to our server when payment is complete. This is a backup in case the user closes their browser before returning.

1. PayMongo sends POST to `/orders/webhooks/paymongo/`
2. Website verifies the signature (security check)
3. If payment successful: marks order as "paid"
4. If payment failed: marks order as "failed"

**Code Reference:**
```python
# orders/webhooks.py:36-92
@csrf_exempt  # Webhooks come from external source
@require_POST
def paymongo_webhook(request):
    # Verify signature
    if not verify_webhook_signature(request.body, signature_header):
        return HttpResponse(status=403)

    # Parse and process event
    if event_type == "checkout_session.payment.paid":
        return _handle_payment_paid(payment_info)
    elif event_type == "payment.failed":
        return _handle_payment_failed(payment_info)
```

---

## Order Statuses

| Status | Meaning | When It Happens |
|--------|---------|-----------------|
| `pending` | Waiting for payment | Order created, user redirected to PayMongo |
| `paid` | Payment received | PayMongo confirms payment |
| `confirmed` | Order accepted | Café confirms and starts preparing |
| `ready` | Ready for pickup | Order is ready |
| `completed` | Order finished | Customer picked up order |
| `cancelled` | Order cancelled | User or café cancelled |
| `failed` | Payment failed | Payment was declined |

**Code Reference:** `orders/models.py:209-236`

---

## Payment Methods

### Card Payments

- Supports Visa and Mastercard
- 3D Secure (OTP verification) enabled for security
- Card details never touch our server (handled by PayMongo)

### GCash

- Philippine e-wallet
- User is redirected to GCash to authorize payment
- Money deducted from GCash balance

### PayMaya

- Philippine e-wallet
- User is redirected to PayMaya to authorize payment
- Money deducted from PayMaya balance

---

## Testing Payments

### Test Cards

Use these test card numbers in development mode:

| Card Number | Result |
|-------------|--------|
| `4343 4343 4343 4345` | Success (Visa) |
| `5555 5555 5555 4444` | Success (Mastercard) |
| `4000 0000 0000 0002` | Declined |

**For all test cards:**
- Expiry: Any future date (e.g., 12/25)
- CVV: Any 3 digits (e.g., 123)
- Name: Any name

### Test GCash/PayMaya

In test mode, GCash and PayMaya will show a simulator page where you can choose to:
- **Authorize** (complete payment)
- **Fail/Expire** (simulate declined payment)

---

## Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `PAYMONGO_SECRET_KEY` | API secret key (starts with `sk_test_`) | `sk_test_abc123...` |
| `PAYMONGO_PUBLIC_KEY` | API public key (starts with `pk_test_`) | `pk_test_xyz789...` |
| `PAYMONGO_WEBHOOK_SECRET` | Webhook signature secret | `whsk_...` |

**Get your keys:**
1. Sign up at https://paymongo.com
2. Go to **Developers > API Keys**
3. Copy the **Test** keys (not live!)

### Django Settings

```python
# brewschews/settings.py:488-495
PAYMONGO_SECRET_KEY = os.environ.get("PAYMONGO_SECRET_KEY", "")
PAYMONGO_PUBLIC_KEY = os.environ.get("PAYMONGO_PUBLIC_KEY", "")
PAYMONGO_WEBHOOK_SECRET = os.environ.get("PAYMONGO_WEBHOOK_SECRET", "")
PAYMONGO_API_URL = "https://api.paymongo.com/v1"
PAYMENT_CURRENCY = "PHP"
PAYMENT_DESCRIPTION_PREFIX = "Brews & Chews Order"
```

---

## Code References

### Files Overview

| File | Purpose |
|------|---------|
| `orders/payments.py` | PayMongo API integration |
| `orders/webhooks.py` | Webhook handlers |
| `orders/views.py` | Checkout and payment views |
| `orders/models.py` | Order model with payment fields |
| `orders/urls.py` | URL routing |

### Key Functions

| Function | File:Line | Purpose |
|----------|-----------|---------|
| `create_checkout_session()` | `orders/payments.py:126` | Create PayMongo checkout |
| `verify_webhook_signature()` | `orders/payments.py:224` | Verify webhook security |
| `get_checkout_session()` | `orders/payments.py:205` | Get payment status |
| `extract_payment_info()` | `orders/payments.py:305` | Parse webhook data |
| `checkout()` | `orders/views.py:547` | Handle checkout form |
| `payment_success()` | `orders/views.py:751` | Success page |
| `payment_cancel()` | `orders/views.py:860` | Cancel page |
| `retry_payment()` | `orders/views.py:932` | Retry failed payment |
| `paymongo_webhook()` | `orders/webhooks.py:36` | Handle webhooks |
| `_handle_payment_paid()` | `orders/webhooks.py:95` | Process successful payment |
| `_handle_payment_failed()` | `orders/webhooks.py:161` | Process failed payment |

### Order Model Payment Fields

| Field | Type | Purpose |
|-------|------|---------|
| `checkout_session_id` | CharField | PayMongo session ID |
| `payment_intent_id` | CharField | PayMongo payment ID |
| `payment_method` | CharField | card/gcash/paymaya |
| `paid_at` | DateTimeField | When payment was received |

**Code Reference:** `orders/models.py:296-319`

---

## Troubleshooting

### Issue: "Payment initialization failed"

**Cause:** PayMongo API keys not configured.

**Solution:**
1. Add keys to `.env` file:
   ```env
   PAYMONGO_SECRET_KEY=sk_test_your_key
   PAYMONGO_PUBLIC_KEY=pk_test_your_key
   ```
2. Restart the server

---

### Issue: Payment completed but order still "pending"

**Cause:** Webhook not received or not processed.

**Solution:**
1. Check webhook configuration in PayMongo dashboard
2. Check server logs for webhook errors
3. Manually verify payment status:
   ```python
   from orders.payments import get_checkout_session
   session = get_checkout_session("cs_xxx...")
   print(session)
   ```

---

### Issue: "Invalid webhook signature"

**Cause:** Webhook secret not configured or incorrect.

**Solution:**
1. Get webhook secret from PayMongo dashboard
2. Add to `.env`:
   ```env
   PAYMONGO_WEBHOOK_SECRET=whsk_...
   ```
3. Restart server

---

### Issue: Redirect URLs not working

**Cause:** Using localhost URLs which PayMongo can't access.

**Solution for development:**
1. Use ngrok to expose local server:
   ```bash
   ngrok http 8000
   ```
2. Use ngrok URL for testing
3. The website auto-detects and uses correct URLs

---

## Security Features

### Card Data Security

- Card numbers **never** touch our server
- PayMongo is PCI DSS compliant
- All payments processed on PayMongo's secure servers

### Webhook Security

- Webhooks verified using HMAC-SHA256 signatures (`orders/payments.py:224`)
- Invalid signatures rejected with 403 status
- Timing-safe comparison prevents timing attacks

### Order Verification

- Orders verified to belong to logged-in user (`orders/views.py:788-792`)
- Payment status double-checked with PayMongo API (`orders/views.py:802-833`)
- Idempotent webhook handling (safe to receive multiple times)

---

## Common Questions

### Q: Can I test payments without a PayMongo account?

**A:** No, you need a PayMongo account to get API keys. However, you can create a free account and use test mode indefinitely.

### Q: What happens if the user closes the browser during payment?

**A:** The webhook system handles this. When payment completes, PayMongo sends a webhook notification that updates the order status automatically.

### Q: Can users pay with cash?

**A:** Currently, only online payments (Card, GCash, PayMaya) are supported. Cash on delivery could be added as a future feature.

### Q: What currency is used?

**A:** Philippine Peso (PHP). All amounts are in PHP.

### Q: How do refunds work?

**A:** Refunds are processed through the PayMongo dashboard by the café owner. The website doesn't currently have refund functionality built-in.

---

## Future Improvements

1. **Refund Integration** - Allow refunds from the website
2. **Payment History** - Show detailed payment receipts
3. **Multiple Payment Methods** - Add more e-wallets
4. **Subscription Payments** - For loyalty programs
5. **Split Payments** - Pay with multiple methods
