# BREWS & CHEWS - DETAILED UPDATE PLAN
## MCO 2 IMPLEMENTATION GUIDE

**Project:** Online Café Ordering System  
**Phase:** MCO 2 - Full System Implementation  
**Document Version:** 1.0  
**Critical:** Follow this plan sequentially without alterations

---

## TABLE OF CONTENTS

1. [Phase 1: Cart Backend Implementation](#phase-1-cart-backend-implementation)
2. [Phase 2: Checkout Flow Completion](#phase-2-checkout-flow-completion)
3. [Phase 3: Payment Integration (PayMongo)](#phase-3-payment-integration-paymongo)
4. [Phase 4: Email Implementation](#phase-4-email-implementation)
5. [Additional Updates Needed](#additional-updates-needed)
6. [Summary by File](#summary-by-file)

---

## PHASE 1: CART BACKEND IMPLEMENTATION

### 1.1 Create Cart API Endpoints

**File:** `orders/views.py`

**What to add:**

- `add_to_cart_view()` - Handles adding items to cart
- `update_cart_item()` - Updates quantity of existing cart items
- `remove_from_cart()` - Removes items from cart
- `get_cart_summary()` - Returns cart data (count, total)

**How it works:**

- Each view receives menu item ID and quantity
- Gets or creates Cart for logged-in user
- Creates or updates CartItem records in database
- Returns JSON response for AJAX or redirects for regular forms
- Calculates line totals and cart totals

**Key logic:**

- If item already in cart → update quantity (add to existing)
- If quantity = 0 → delete CartItem
- Always recalculate totals after changes
- Use transactions to prevent race conditions

### 1.2 Update Cart View to Use Real Data

**File:** `orders/views.py` (modify existing `cart_view`)

**Current state:** Generates fake sample data

**What to change:**

- Remove hardcoded sample cart items
- Query actual Cart and CartItem objects for current user
- Pass real data to template
- Show empty cart message if no items

**Data to pass:**

- List of CartItem objects with menu item details
- Quantity per item
- Line total per item (price × quantity)
- Cart subtotal (sum of all line totals)
- Tax amount (8% of subtotal)
- Grand total (subtotal + tax)

### 1.3 Enable Add to Cart Buttons

**File:** `menu/templates/menu/catalog.html`

**What to change:**

- Remove `disabled` attribute from "Add to Cart" buttons
- Add form with CSRF token around each button
- Include hidden input with `menu_item_id`
- Set form action to `/orders/cart/add/`
- Set method to `POST`

**Two implementation options:**

1. **Simple:** Full page reload after adding (easier)
2. **Advanced:** AJAX request without reload (better UX)

**For simple approach:**

- Form submits to `add_to_cart` view
- View adds item and redirects back to menu
- Show success message using Django messages framework

**For AJAX approach:**

- Button triggers JavaScript function
- Fetch API calls `add_to_cart` endpoint
- Update cart badge count without reload
- Show toast notification "Item added!"

### 1.4 Update Cart Page Interface

**File:** `orders/templates/orders/cart.html`

**What to enable:**

- Make quantity buttons functional (+ and - buttons)
- Wire up "Remove" button to delete endpoint
- Make "Proceed to Checkout" button active
- Add forms for each action with CSRF tokens

**Quantity controls:**

- Plus button → POST to `update_cart` with quantity+1
- Minus button → POST to `update_cart` with quantity-1
- Remove button → POST to `remove_from_cart`

**Real-time total updates:**

- Each action should redirect back to cart page
- Page reload shows updated quantities and totals
- Alternative: Use AJAX to update without full reload

### 1.5 Add URL Routes

**File:** `orders/urls.py`

**New routes to add:**

- `/orders/cart/add/` → `add_to_cart_view`
- `/orders/cart/update/<int:cart_item_id>/` → `update_cart_item`
- `/orders/cart/remove/<int:cart_item_id>/` → `remove_from_cart`

**Requirements:**

- All routes require login (`@login_required` decorator)
- All are POST-only for security
- Include CSRF protection

---

## PHASE 2: CHECKOUT FLOW COMPLETION

### 2.1 Update Checkout View

**File:** `orders/views.py` (modify existing `checkout`)

**Current state:** Shows disabled form with sample data

**What to change:**

- Get actual Cart for logged-in user
- Calculate real totals from CartItem objects
- Pre-fill form with user's profile data (phone, name)
- Enable form submission

**GET request (show form):**

- Retrieve user's cart
- If cart empty → redirect to menu with message
- Calculate subtotal, tax, total
- Pre-populate contact info from `user.profile`
- Show list of cart items in order summary

**POST request (process order):**

- Validate form data
- Create Order object with calculated totals
- Create OrderItem objects from CartItem objects
- Store snapshot data (menu item name, price)
- Set order status to 'pending'
- Generate order reference number (e.g., BC-251107-001)
- DON'T clear cart yet (wait for payment)
- Redirect to payment page

### 2.2 Enable Checkout Form

**File:** `orders/templates/orders/checkout.html`

**What to change:**

- Remove `disabled` attributes from form fields
- Make form submittable
- Keep contact name, phone, special instructions fields
- Add form validation (HTML5 or JavaScript)

**Form fields:**

- Contact name (required, from profile)
- Contact phone (required, from profile)
- Special instructions (optional, textarea)
- All are editable even if pre-filled

**Validation:**

- Contact name: minimum 2 characters
- Phone: valid format (e.g., +639xxxxxxxxx or 09xxxxxxxxx)
- Don't allow empty cart checkout

### 2.3 Create Order Snapshot Logic

**File:** `orders/views.py` (in checkout POST handler)

**What it does:**

- Prevents issues if menu prices change later
- Preserves historical accuracy

**Process:**

For each CartItem, create OrderItem with:

- `menu_item` (foreign key reference)
- `menu_item_name` (snapshot - copy current name)
- `unit_price` (snapshot - copy current price)
- `quantity` (copy from cart)

**Why snapshot?**

- If Cappuccino price changes from ₱150 to ₱180 tomorrow
- Old orders still show ₱150 (what customer actually paid)
- `menu_item` FK still links to current menu item (for reference)

### 2.4 Order Reference Number Generation

**File:** `orders/models.py` or `orders/utils.py`

**What to create:**

- Function to generate unique order reference numbers
- Format: `BC-YYMMDD-NNN`
  - BC = Brews & Chews
  - YYMMDD = Year Month Day
  - NNN = Sequential number for that day

**How it works:**

- Count orders created today
- Increment counter
- Zero-pad to 3 digits (001, 002, etc.)
- Ensure uniqueness (check if exists, retry if collision)

**Example:**

- First order on Nov 7, 2025 → BC-251107-001
- Second order same day → BC-251107-002
- First order next day → BC-251108-001

### 2.5 Transaction Handling

**File:** `orders/views.py` (checkout POST handler)

**What to implement:**

- Wrap order creation in database transaction
- If anything fails, rollback everything
- Prevents partial orders (order exists but no items)

**Transaction steps:**

1. Start transaction
2. Create Order object
3. Loop through CartItems
4. Create all OrderItem objects
5. If all succeed → commit transaction
6. If any fail → rollback and show error

**Why important:**

- Ensures data consistency
- All-or-nothing operation
- Prevents orphaned records

---

## PHASE 3: PAYMENT INTEGRATION (PAYMONGO)

### 3.1 PayMongo Account Setup

**What to do:**

1. Go to paymongo.com
2. Sign up for free test account
3. Verify email
4. Navigate to Developers section
5. Copy your test API keys:
   - Secret Key (sk_test_...)
   - Public Key (pk_test_...)
6. Add to .env file (never commit keys to git)

**Environment variables:**

```
PAYMONGO_SECRET_KEY=sk_test_xxxxx
PAYMONGO_PUBLIC_KEY=pk_test_xxxxx
```

### 3.2 Install Required Package

**What to install:**

- PayMongo has no official Python SDK
- Use `requests` library (already in Django)
- Or install `paymongo-python` (community package)

**Add to requirements.txt:**

```
requests>=2.31.0
```

(if not already there)

No additional packages required - can use Django's built-in HTTP client or requests library.

### 3.3 Create Payment Service

**New file:** `orders/payment_service.py`

**What to create:**

`PayMongoService` class with methods:

- `create_payment_intent()` - Creates payment intent
- `retrieve_payment_intent()` - Gets payment status
- `verify_webhook_signature()` - Validates webhook calls

**Payment intent creation:**

- Takes order ID and amount
- Calls PayMongo API with authentication
- Specifies allowed payment methods (card, gcash, paymaya)
- Receives payment intent object with checkout_url
- Returns checkout URL to redirect user

**Configuration:**

- Base URL: `api.paymongo.com/v1`
- Authentication: Basic auth with secret key (base64 encoded)
- Currency: PHP (Philippine Peso)
- Amount: Convert to centavos (multiply by 100)

### 3.4 Update Checkout to Create Payment

**File:** `orders/views.py` (modify checkout POST)

**What to add after order creation:**

- Create PayMongo payment intent
- Store `payment_intent_id` in Order model
- Redirect user to PayMongo checkout URL

**Flow:**

1. User submits checkout form
2. Order created with status='pending'
3. Payment intent created via API
4. `Order.payment_intent_id` = intent.id (save)
5. Redirect to `payment_intent.checkout_url`
6. User completes payment on PayMongo page
7. PayMongo redirects back to success/failure URL

### 3.5 Add Payment Intent ID to Order Model

**File:** `orders/models.py`

**What to add:**

- New field: `payment_intent_id` (CharField, nullable, blank)
- Max length: 100 characters
- Used to track PayMongo payment

**Create migration:**

- Run: `python manage.py makemigrations`
- Run: `python manage.py migrate`

### 3.6 Create Webhook Endpoint

**New file or add to:** `orders/webhooks.py`

**What to create:**

- View function: `paymongo_webhook(request)`
- Exempt from CSRF (`@csrf_exempt` decorator)
- Accepts POST requests only

**What it does:**

1. Receive webhook POST from PayMongo
2. Verify webhook signature (important for security)
3. Parse event data
4. Check event type (payment.paid, payment.failed)
5. Find Order by `payment_intent_id`
6. Update order status accordingly
7. Return 200 OK response

**Events to handle:**

- `payment.paid` → Set order status to 'paid'
- `payment.failed` → Set order status to 'cancelled'

### 3.7 Add Webhook URL Route

**File:** `orders/urls.py`

**New route:**

- `/webhooks/paymongo/` → `paymongo_webhook` view
- Must be publicly accessible (no `@login_required`)
- POST only

**Important:**

- This URL must be registered in PayMongo dashboard
- PayMongo will call this URL when payment events occur
- Must return 200 OK quickly (process in background if needed)

### 3.8 Create Success/Failure Pages

**New files:**

- `orders/templates/orders/payment_success.html`
- `orders/templates/orders/payment_failed.html`

**New views:**

- `payment_success(request)` - Shows order confirmed
- `payment_failed(request)` - Shows payment failed

**What they show:**

- **Success:** Order reference, "Payment successful", link to order history
- **Failed:** "Payment failed", option to retry, link to cart

**URL routes:**

- `/orders/payment/success/`
- `/orders/payment/failed/`

These are redirect URLs given to PayMongo:

- PayMongo redirects user here after payment attempt
- Success page: can show order details
- Failed page: can allow retry or return to cart

### 3.9 Webhook Signature Verification

**File:** `orders/webhooks.py` (in webhook view)

**What to implement:**

- PayMongo sends signature in HTTP header
- Compute HMAC signature of request body
- Compare with received signature
- Reject if mismatch (prevents fake webhooks)

**Security:**

- Use webhook secret (get from PayMongo dashboard)
- Add to .env: `PAYMONGO_WEBHOOK_SECRET`
- Use constant-time comparison (prevents timing attacks)
- Return 403 Forbidden if invalid

**Why critical:**

- Prevents attackers from faking payment confirmations
- Ensures webhooks actually come from PayMongo
- Required for production security

### 3.10 Handle Payment Timeouts

**File:** `orders/models.py` or background task

**What to implement:**

- Orders in 'pending' status for > 30 minutes
- Automatically cancel them
- Release cart items (or keep for user to retry)

**Options:**

- **Simple:** Manual admin action (good for demo)
- **Better:** Management command to run periodically
- **Advanced:** Celery scheduled task (overkill for demo)

**For demo purposes:**

- Simple approach is fine
- Can manually cancel pending orders
- Mention timeout logic in presentation

---

## PHASE 4: EMAIL IMPLEMENTATION

### 4.1 Gmail App Password Setup

**What to do:**

1. Go to Google Account settings
2. Navigate to Security
3. Enable 2-Factor Authentication (required for app passwords)
4. Go to "App Passwords" section
5. Generate new app password for "Mail"
6. Copy 16-character password
7. Add to .env file

**Environment variables:**

```
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=abcd efgh ijkl mnop
```

(16-char password)

**Important:**

- NOT your regular Gmail password
- App-specific password only
- Keep it secret, never commit to git

### 4.2 Configure Email Settings

**File:** `brewschews/settings.py`

**What to add:**

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = from environment variable
EMAIL_HOST_PASSWORD = from environment variable
DEFAULT_FROM_EMAIL = same as EMAIL_HOST_USER
```

**For development testing:**

- Can use console backend (prints to terminal)
- Switch to SMTP for actual demo

### 4.3 Create EmailOTP Model

**File:** `accounts/models.py`

**What to add:**

New model: `EmailOTP`

**Fields needed:**

- `email` (EmailField)
- `otp_code` (CharField, 6 digits)
- `created_at` (DateTimeField, auto)
- `verified` (BooleanField, default False)

**Methods to add:**

- `is_valid()` - Check if OTP is still valid (< 10 minutes old)
- `generate_otp()` - Class method to create new OTP

**Purpose:**

- Store OTP codes temporarily
- Track verification status
- Automatic expiration checking

### 4.4 Create Email Utility Functions

**New file:** `core/email_service.py` or `accounts/email_utils.py`

**Functions to create:**

**1. `generate_otp_code()`**

- Generates random 6-digit number
- Format: "123456"
- Use `random.randint` or `secrets` module

**2. `send_otp_email(email, otp_code)`**

- Composes email with OTP code
- Subject: "Verify your email - Brews & Chews"
- Body: "Your verification code is: {otp_code}"
- Valid for 10 minutes message
- Sends via Django's `send_mail()`

**3. `send_order_confirmation_email(order)`**

- Gets order details
- Lists all order items
- Shows totals
- Includes order reference number
- Subject: "Order Confirmation - #{reference}"
- Sends to order.user's email

**Email best practices:**

- HTML and plain text versions
- Clear subject lines
- Include company name
- Professional formatting

### 4.5 Update Signup Flow

**File:** `accounts/views.py` (modify existing `signup_view`)

**Current flow:**

1. User submits form
2. User created immediately
3. Redirect to menu

**New flow:**

1. User submits form
2. Validate form data
3. DON'T create user yet
4. Generate 6-digit OTP
5. Save OTP to EmailOTP model
6. Send OTP via email
7. Store form data in session
8. Redirect to OTP verification page

**Session data to store:**

- username
- email (encrypted)
- password (hashed)
- Any profile data

**Why use session:**

- User not created yet
- Need to preserve form data
- Temporary storage until verified

### 4.6 Create OTP Verification Page

**New file:** `accounts/templates/accounts/verify_otp.html`

**What to show:**

- "Enter verification code sent to {email}"
- Input field for 6-digit code
- Submit button
- Resend OTP link
- Code expires in 10 minutes message

**New view:** `verify_signup_otp(request)`

**What it does:**

**GET:** Show OTP input form

**POST:** Verify submitted OTP

- If valid → Create user account
- Clear session data
- Mark OTP as verified
- Redirect to login with success message
- If invalid → Show error, allow retry
- If expired → Show expired message, offer resend

### 4.7 Add Resend OTP Functionality

**New view:** `resend_otp(request)`

**What it does:**

1. Get email from session
2. Check if recent OTP exists (< 2 minutes)
3. If yes → Show "Please wait" message (rate limiting)
4. If no → Generate new OTP
5. Send new email
6. Redirect back to verification page

**Rate limiting:**

- Maximum 1 resend per 2 minutes
- Prevents email spam
- Shows countdown timer (optional)

**URL route:**

- `/accounts/verify/resend/` → `resend_otp`

### 4.8 Update Order Confirmation to Send Email

**File:** `orders/webhooks.py` (modify webhook handler)

**What to add:**

- After confirming payment (status → 'paid')
- Call `send_order_confirmation_email(order)`
- Email sent automatically
- Include try-except to handle email failures
- Log if email fails (don't crash webhook)

**Flow:**

1. PayMongo webhook received
2. Payment verified as successful
3. Order status updated to 'paid'
4. Send confirmation email
5. Return 200 OK to PayMongo

**Error handling:**

- If email fails, order still confirmed
- Log the error for debugging
- Don't block order processing
- Email is nice-to-have, not critical

### 4.9 Create Email Templates

**New files:**

- `templates/emails/otp_verification.html`
- `templates/emails/otp_verification.txt` (plain text version)
- `templates/emails/order_confirmation.html`
- `templates/emails/order_confirmation.txt`

**OTP email content:**

- Subject: "Verify your email - Brews & Chews"
- Greeting with email address
- "Your verification code is: {code}"
- Valid for 10 minutes
- Security note: "Didn't request this? Ignore this email"

**Order confirmation content:**

- Subject: "Order Confirmation #{reference}"
- Thank you message
- Order details table (items, quantities, prices)
- Totals (subtotal, tax, total)
- Order reference number
- "Your order will be ready in 15-20 minutes"
- Link to order history (optional)

### 4.10 Test Email Delivery

**What to test:**

**OTP emails:**

- Signup with valid email
- Check email received (check spam folder)
- Verify code works
- Test expired code (wait 10+ minutes)
- Test wrong code (error handling)
- Test resend functionality

**Order confirmation emails:**

- Complete full checkout flow
- Make test payment
- Webhook triggers email
- Check email received
- Verify all order details correct
- Test with different order sizes

**Common issues:**

- Gmail blocking: Less secure apps setting
- Spam folder: Check there first
- App password: Must use 16-char password, not regular
- Port 587: Make sure not blocked by firewall
- TLS: Must be enabled

---

## ADDITIONAL UPDATES NEEDED

### A. Update Order History View

**File:** `orders/views.py` (modify existing `history`)

**Current state:** Shows sample fake orders

**What to change:**

- Remove hardcoded sample data
- Query actual Order objects for logged-in user
- Order by `created_at` descending (newest first)
- Show real order details

**Data to display:**

- Order reference number
- Created date
- Status (pending, paid, preparing, ready, completed)
- Total amount
- List of items in each order

### B. Add Order Detail Page

**New file:** `orders/templates/orders/order_detail.html`

**New view:** `order_detail(request, order_id)`

**What it shows:**

- Full order information
- All order items with quantities and prices
- Order status timeline
- Payment status
- Customer contact info
- Special instructions (if any)

**Security:**

- Verify order belongs to logged-in user
- Return 404 if not found or unauthorized

**URL route:**

- `/orders/<int:order_id>/` → `order_detail`

### C. Update URLs Configuration

**File:** `orders/urls.py`

**All new routes to add:**

- `POST /cart/add/` → `add_to_cart`
- `POST /cart/update/<id>/` → `update_cart_item`
- `POST /cart/remove/<id>/` → `remove_from_cart`
- `GET/POST /checkout/` → `checkout` (already exists, just enable POST)
- `POST /webhooks/paymongo/` → `paymongo_webhook`
- `GET /payment/success/` → `payment_success`
- `GET /payment/failed/` → `payment_failed`
- `GET /orders/<id>/` → `order_detail`

**File:** `accounts/urls.py`

**New routes to add:**

- `POST /verify/` → `verify_signup_otp`
- `POST /verify/resend/` → `resend_otp`

### D. Add Success Messages

**Files:** All views that modify data

**What to add:**

- Use Django's messages framework
- Show success messages after actions

**Examples:**

- "Item added to cart"
- "Cart updated"
- "Order placed successfully"
- "Verification email sent"
- "Email verified successfully"

**How:**

- Import: `from django.contrib import messages`
- Add: `messages.success(request, "Your message")`
- Display in base template (already have Django messages)

### E. Add Form Validation

**Files to update:**

- `orders/forms.py` (create if doesn't exist)
- `accounts/forms.py` (modify existing)

**Checkout form validation:**

- Contact name: required, 2-100 characters
- Phone: required, valid phone format
- Special instructions: optional, max 500 characters

**OTP form validation:**

- OTP code: required, exactly 6 digits
- Only numbers allowed
- No spaces or special characters

### F. Error Handling

**What to add to all views:**

**Cart operations:**

- Item not found → show error, redirect to menu
- Out of stock → show error, don't add to cart
- Invalid quantity → show error, keep current
- Empty cart checkout → redirect to menu

**Payment:**

- API call fails → show error, keep order pending
- Webhook signature invalid → log and return 403
- Order not found → log error, return 200 (idempotency)

**Email:**

- Email send fails → log error, continue processing
- Invalid email format → show error in signup
- OTP expired → show clear message, offer resend
- OTP invalid → show error, allow retry (max 3 attempts)

### G. Update Database Migrations

**What to run:**

- After adding EmailOTP model: `python manage.py makemigrations accounts`
- After adding payment_intent_id: `python manage.py makemigrations orders`
- Apply migrations: `python manage.py migrate`

**Check migrations:**

- Review migration files before applying
- Test on development database first
- Backup database before running migrations

### H. Environment Variables Setup

**File:** `.env`

**All variables needed:**

```bash
# Email
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password

# PayMongo
PAYMONGO_SECRET_KEY=sk_test_xxxxx
PAYMONGO_PUBLIC_KEY=pk_test_xxxxx
PAYMONGO_WEBHOOK_SECRET=whsec_xxxxx

# Existing
DJANGO_SECRET_KEY=your-secret
ACCOUNT_EMAIL_ENCRYPTION_KEY=your-encryption-key
```

**Important:**

- Never commit .env to git
- .env should be in .gitignore (already is)
- Each developer needs their own .env
- Document required variables in .env.example

### I. Testing Checklist

**What to test:**

**Cart functionality:**

- ✓ Add item to empty cart
- ✓ Add same item twice (quantity increases)
- ✓ Add different items
- ✓ Increase quantity
- ✓ Decrease quantity
- ✓ Remove item
- ✓ Clear entire cart
- ✓ Totals calculate correctly

**Checkout:**

- ✓ Can't checkout with empty cart
- ✓ Form validation works
- ✓ Order created with correct details
- ✓ OrderItems match CartItems
- ✓ Totals correct (subtotal + tax)
- ✓ Reference number unique

**Payment:**

- ✓ Payment intent created
- ✓ Redirect to PayMongo works
- ✓ Test card payment succeeds
- ✓ Webhook receives confirmation
- ✓ Order status updates
- ✓ Failed payment handled

**Email:**

- ✓ OTP email sent on signup
- ✓ OTP code validates correctly
- ✓ Expired OTP rejected
- ✓ Resend OTP works
- ✓ User created after verification
- ✓ Order confirmation sent
- ✓ Email contains correct details

### J. Admin Interface Updates

**File:** `orders/admin.py`

**What to customize:**

- Register Order model if not already
- Add list display: reference, user, total, status, created
- Add filters: status, created date
- Add search: reference number, user email
- Make certain fields readonly: totals, reference
- Show OrderItems inline

**File:** `accounts/admin.py`

**What to add:**

- Register EmailOTP model
- List display: email, code, created, verified
- Filters: verified, created date
- Readonly: created_at

**Purpose:**

- Easy testing during development
- View orders and OTPs
- Debug payment issues
- Demo to instructor (admin panel tour)

---

## SUMMARY BY FILE

### Files to Create:

1. `orders/payment_service.py` - PayMongo integration
2. `orders/webhooks.py` - Webhook handler
3. `core/email_service.py` - Email utilities
4. `orders/forms.py` - Checkout form
5. `templates/emails/` folder with 4 templates
6. `templates/orders/payment_success.html`
7. `templates/orders/payment_failed.html`
8. `templates/accounts/verify_otp.html`
9. `templates/orders/order_detail.html`

### Files to Modify:

1. `orders/views.py` - Add 8+ new views, update 3 existing
2. `orders/models.py` - Add payment_intent_id field
3. `accounts/views.py` - Update signup flow, add OTP views
4. `accounts/models.py` - Add EmailOTP model
5. `orders/urls.py` - Add 8+ new routes
6. `accounts/urls.py` - Add 2 new routes
7. `menu/templates/menu/catalog.html` - Enable cart buttons
8. `orders/templates/orders/cart.html` - Enable interactions
9. `orders/templates/orders/checkout.html` - Enable form
10. `brewschews/settings.py` - Add email configuration
11. `.env` - Add email and payment credentials
12. `requirements.txt` - Add any new packages
13. `orders/admin.py` - Customize admin interface
14. `accounts/admin.py` - Add EmailOTP admin

### Migrations to Create:

1. Add EmailOTP model (accounts)
2. Add payment_intent_id to Order (orders)

---

## IMPLEMENTATION NOTES

**CRITICAL REMINDERS:**

1. **Follow the sequence** - Each phase builds on the previous one
2. **Test thoroughly** - Use the testing checklist after each phase
3. **Commit frequently** - Use Git after completing each major section
4. **Keep backups** - Backup database before running migrations
5. **Environment variables** - Never commit sensitive data to Git
6. **Security first** - Implement webhook signature verification
7. **Error handling** - Add proper try-except blocks throughout
8. **User feedback** - Show clear success/error messages
9. **Documentation** - Comment complex logic for future reference
10. **Demo readiness** - Ensure all features are presentable

**PHASE DEPENDENCIES:**

- Phase 2 depends on Phase 1 (need cart for checkout)
- Phase 3 depends on Phase 2 (need orders for payment)
- Phase 4 can be done in parallel but test after Phase 3
- Additional Updates depend on all phases

**TESTING STRATEGY:**

1. Test each view individually after creation
2. Test complete user flows (cart → checkout → payment → email)
3. Test error scenarios (failed payment, expired OTP)
4. Test edge cases (empty cart, duplicate items)
5. Test on different browsers if time permits

**END OF IMPLEMENTATION PLAN**

---

*This document must be followed exactly as written. Any deviations from the plan should be documented and justified. For questions or clarifications, consult with team members or instructor.*
