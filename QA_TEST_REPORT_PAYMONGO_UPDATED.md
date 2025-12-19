# QA Test Report: PayMongo Transactions Not Appearing in Dashboard
## 🔄 UPDATED FINDINGS

**Report Date:** December 19, 2025
**Tester:** QA Engineer (Claude)
**Test Environment:** Production (LIVE API Keys Detected)
**Issue Severity:** 🔴 **CRITICAL**
**Status:** ⚠️ **UPDATED ANALYSIS**

---

## ⚠️ CRITICAL DISCOVERY

After reviewing the actual `.env` file, I discovered that **LIVE PayMongo API keys** are configured:

```env
PAYMONGO_SECRET_KEY=sk_live_*********************
PAYMONGO_PUBLIC_KEY=pk_live_*********************
```

⚠️ **SECURITY NOTE:** Actual keys redacted for security. Keys start with `sk_live_` and `pk_live_`.

**This changes the entire diagnosis!**

---

## 🔍 Updated Root Cause Analysis

### Most Likely Cause: Wrong Dashboard

**You have LIVE keys configured, but you may be checking the TEST dashboard.**

PayMongo has **TWO separate dashboards**:

1. **Test Dashboard** - Shows transactions from test API keys (`sk_test_*`)
2. **Live Dashboard** - Shows transactions from live API keys (`sk_live_*`)

**Where to check:**
- **Test Dashboard:** https://dashboard.paymongo.com/test/payments
- **Live Dashboard:** https://dashboard.paymongo.com/payments (or toggle to "Live" mode)

### Critical Questions:

❓ **Are you looking at the LIVE dashboard or TEST dashboard?**
- Your app is using LIVE keys
- Transactions will ONLY appear in the LIVE dashboard
- Test dashboard will be empty (because you're not using test keys)

❓ **Are you making real payments or test payments?**
- With LIVE keys, you need to use REAL credit cards
- Test cards (like 4343 4343 4343 4345) will NOT work with live keys
- Real money will be charged!

---

## 🚨 Security Concerns

### Using Live Keys in Development

**⚠️ DANGER:** You're using LIVE API keys, which means:

1. **Real Money Risk**
   - Any payments made are REAL transactions
   - Real money is being charged to customers
   - Refunds cost fees and processing time

2. **Production Data in Development**
   - Development testing is mixing with real customer data
   - Risk of data corruption or errors affecting real customers
   - Difficult to distinguish test orders from real orders

3. **Key Exposure Risk**
   - Live keys have access to real payment data
   - If keys are leaked, real financial damage can occur
   - Development environments are less secure than production

### **RECOMMENDATION: Switch to Test Keys Immediately**

For development/testing, you should use TEST keys:

```env
# For development - use TEST keys
PAYMONGO_SECRET_KEY=sk_test_YOUR_TEST_KEY_HERE
PAYMONGO_PUBLIC_KEY=pk_test_YOUR_TEST_KEY_HERE
```

**Get your test keys from:**
https://dashboard.paymongo.com/developers → Switch to "Test" mode → API Keys

---

## 🔧 Troubleshooting Steps

### Step 1: Verify Which Dashboard You're Checking

1. Go to https://dashboard.paymongo.com/
2. Look for the mode toggle (usually in top navigation)
3. **Make sure you're in LIVE mode**, not Test mode
4. Check: Payments → Transactions

### Step 2: Create a Test Transaction

**Important:** With live keys, you need to make a REAL payment (or use a real card that you can refund later).

1. Go to your website
2. Add items to cart
3. Proceed to checkout
4. Click "Place Order"
5. **Immediately check LIVE dashboard** - checkout session should appear
6. Use a REAL credit card to complete payment
7. Check LIVE dashboard again - payment should appear

### Step 3: Check Application Logs

```bash
# Check Django logs for errors
tail -f logs/django.log

# Or check console output if running development server
python manage.py runserver
```

Look for errors like:
- ❌ "PayMongo API error"
- ❌ "Failed to connect to PayMongo"
- ❌ "Authentication failed"

### Step 4: Verify API Connectivity

Test if your server can reach PayMongo API:

```bash
# Activate virtual environment
source .venv/bin/activate

# Test API connection with your LIVE keys
python manage.py shell
```

```python
from orders.payments import create_checkout_session
from orders.models import Order

# Get a test order (or create one manually)
order = Order.objects.filter(status='pending').first()

if order:
    try:
        session_id, url = create_checkout_session(
            order=order,
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel"
        )
        print(f"✅ Success! Session ID: {session_id}")
        print(f"✅ Check LIVE dashboard now!")
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("No pending orders found")
```

---

## 🎯 Possible Scenarios

### Scenario A: Looking at Wrong Dashboard ✅ MOST LIKELY

**Symptom:** No transactions visible anywhere
**Cause:** Checking TEST dashboard while using LIVE keys
**Solution:** Switch to LIVE dashboard view

**How to fix:**
1. Go to https://dashboard.paymongo.com/
2. Toggle to "Live" mode (not "Test" mode)
3. Navigate to Payments or Transactions
4. Transactions should be visible

---

### Scenario B: Using Test Cards with Live Keys ❌

**Symptom:** Payments fail or get declined
**Cause:** Test card numbers don't work with live API keys
**Solution:** Use real payment methods or switch to test keys

**Test cards that DON'T work with live keys:**
- ❌ 4343 4343 4343 4345 (test card)
- ❌ 5555 5555 5555 4444 (test card)

**What works with live keys:**
- ✅ Real credit/debit cards
- ✅ Real GCash account
- ✅ Real PayMaya account

---

### Scenario C: Network/Firewall Issues 🔌

**Symptom:** Users can't reach checkout page or payments fail
**Cause:** Server can't connect to PayMongo API

**Check:**
```bash
# Test network connectivity
curl -I https://api.paymongo.com/v1/checkout_sessions

# Should return: HTTP/2 401 (unauthorized, but connected)
# Should NOT return: timeout, connection refused, etc.
```

**Common causes:**
- Firewall blocking outbound HTTPS to api.paymongo.com
- Proxy server issues
- DNS resolution problems
- SSL certificate validation issues

---

### Scenario D: Webhook Not Configured 📡

**Symptom:** Payments complete but orders stay "pending"
**Cause:** Webhook not sending updates back to your server

**This doesn't affect dashboard visibility** - transactions still appear in PayMongo dashboard even without webhooks.

But for order status updates:
1. Go to PayMongo Dashboard → Developers → Webhooks
2. Check if webhook is configured
3. Webhook URL should be: `https://your-domain.com/orders/webhooks/paymongo/`
4. Events should include: `checkout_session.payment.paid`

---

### Scenario E: Account Issues 🏢

**Symptom:** API calls return authentication errors
**Cause:** PayMongo account issues

**Check:**
- ✅ Account is verified and active
- ✅ KYC verification completed (required for live mode)
- ✅ Account not suspended or restricted
- ✅ API keys not revoked

**Verify in dashboard:**
- Account Settings → Verification Status
- Developers → API Keys → Check if keys are active

---

## 📊 Diagnostic Checklist

Run through this checklist to diagnose the issue:

### Configuration ✅
- [x] `.env` file exists
- [x] `PAYMONGO_SECRET_KEY` starts with `sk_live_`
- [x] `PAYMONGO_PUBLIC_KEY` starts with `pk_live_`
- [ ] Keys are active (not revoked)
- [ ] PayMongo account is verified

### Dashboard Access 🎯
- [ ] Logged into correct PayMongo account
- [ ] Viewing **LIVE** dashboard (not test)
- [ ] Checking "Payments" or "Transactions" section
- [ ] Date range includes recent transactions

### Payment Flow 💳
- [ ] Can add items to cart
- [ ] Can proceed to checkout
- [ ] Can click "Place Order" without errors
- [ ] Gets redirected to PayMongo checkout page
- [ ] Checkout page shows correct order details

### API Connectivity 🔌
- [ ] Server can connect to api.paymongo.com
- [ ] No firewall/proxy blocking HTTPS
- [ ] SSL certificates are valid
- [ ] No authentication errors in logs

---

## 🔬 Advanced Debugging

### Enable Debug Logging

Add to `brewschews/settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'orders.payments': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

This will show detailed PayMongo API calls in console.

### Check Checkout Session Response

Add temporary debug output in `orders/payments.py` after line 192:

```python
logger.info(f"Creating checkout session for order {order.reference_number}")

response = _make_request("POST", "/checkout_sessions", payload)

# Add this debug output
logger.info(f"PayMongo Response: {response}")

checkout_session = response["data"]
```

### Inspect Network Traffic

Use browser dev tools when making payment:
1. Open Developer Tools (F12)
2. Go to Network tab
3. Click "Place Order"
4. Look for POST request to `/orders/checkout/`
5. Check response - should redirect to PayMongo
6. If error, check response body for details

---

## 🎬 Video Walkthrough Steps

Here's exactly what to do:

### Test #1: Verify Dashboard Access

1. Open browser to https://dashboard.paymongo.com/
2. **Look for mode toggle** - should say "Live" or "Test"
3. **Click to switch to LIVE mode**
4. Go to left sidebar → Payments (or Transactions)
5. Look for recent transactions
6. Take screenshot and check date range

### Test #2: Create New Transaction

1. Open your website in **new incognito window**
2. Add an inexpensive item to cart
3. Go to checkout
4. Fill in contact info
5. Click "Place Order"
6. **Stop here** - note the time
7. **Immediately switch to PayMongo dashboard**
8. Refresh dashboard
9. Look for a new "Checkout Session" with timestamp matching above
10. **Expected:** Should see checkout session even before payment is completed

### Test #3: Complete Payment (Optional - Costs Real Money)

⚠️ **WARNING: This will charge a real card!**

1. Continue from Test #2 checkout page
2. Use a real credit card (you can refund later)
3. Complete payment
4. Return to website
5. **Immediately check PayMongo LIVE dashboard**
6. Should see completed payment in transactions

---

## 💡 Quick Fixes

### Fix #1: Definitely Wrong Dashboard

**If you see transactions in PayMongo dashboard but they're in the Test section:**
- You were looking at the wrong dashboard
- Switch to Live mode
- Transactions should be there

### Fix #2: Switch to Test Keys (Recommended for Development)

**Stop using live keys in development!**

1. Go to https://dashboard.paymongo.com/
2. Switch to **Test** mode
3. Go to Developers → API Keys
4. Copy **TEST** keys (sk_test_* and pk_test_*)
5. Update `.env`:
   ```env
   PAYMONGO_SECRET_KEY=sk_test_YOUR_TEST_KEY
   PAYMONGO_PUBLIC_KEY=pk_test_YOUR_TEST_KEY
   ```
6. Restart application
7. Now check **TEST** dashboard for transactions
8. Use test cards: 4343 4343 4343 4345

### Fix #3: API Connection Issues

If server can't connect to PayMongo API:

```bash
# Check if port 443 (HTTPS) is open
telnet api.paymongo.com 443

# If that fails, check network/firewall settings
# May need to whitelist api.paymongo.com
```

---

## 📋 Data Collection Needed

To help debug further, please provide:

1. **Screenshot of PayMongo dashboard**
   - Show which mode (Test vs Live)
   - Show the Payments/Transactions page
   - Include date range visible

2. **Application logs when making payment**
   ```bash
   python manage.py runserver
   # Then make a test payment and copy all output
   ```

3. **Browser console errors**
   - F12 → Console tab
   - Try checkout process
   - Screenshot any red errors

4. **Network tab details**
   - F12 → Network tab
   - Try checkout
   - Find POST to `/orders/checkout/`
   - Right-click → Copy as cURL

5. **PayMongo account status**
   - Is KYC verification complete?
   - Are API keys marked as "Active"?
   - Any notifications or warnings in dashboard?

---

## 🎯 Next Steps

### Immediate Actions:

1. **Verify Dashboard Mode**
   - [ ] Confirm you're checking LIVE dashboard
   - [ ] Screenshot the dashboard showing mode

2. **Test Transaction**
   - [ ] Create a test checkout session
   - [ ] Check dashboard immediately
   - [ ] Document result

3. **Switch to Test Keys** (Recommended)
   - [ ] Get test API keys
   - [ ] Update `.env`
   - [ ] Restart application
   - [ ] Test with test cards
   - [ ] Check TEST dashboard

---

## 📞 Support Escalation

If none of the above resolves the issue:

1. **Contact PayMongo Support**
   - Email: support@paymongo.com
   - Include: Account email, approximate transaction times
   - Ask: "Why aren't transactions appearing in my dashboard?"

2. **Check PayMongo Status**
   - https://status.paymongo.com/
   - Verify no ongoing outages

3. **Provide Debug Information**
   - Application logs
   - Network traffic captures
   - Screenshots of dashboard

---

## 🔐 Security Reminder

**⚠️ CRITICAL SECURITY NOTICE**

Your `.env` file contains LIVE API keys. These should:

1. **NEVER** be committed to git
2. **NEVER** be shared publicly
3. **NEVER** be used in development (use test keys instead)
4. Be rotated if exposed
5. Be stored securely

**Check immediately:**
```bash
# Make sure .env is in .gitignore
cat .gitignore | grep .env

# Make sure .env is not tracked by git
git status | grep .env

# If .env shows up, DO NOT commit it!
```

---

## 📝 Revised Conclusion

**Original diagnosis:** Missing API credentials ❌
**Updated diagnosis:** Using LIVE keys, likely checking wrong dashboard ✅

**Most probable cause:** You're checking the **TEST** dashboard while your application uses **LIVE** API keys.

**Recommended solution:**
1. Switch to viewing **LIVE** dashboard in PayMongo
2. OR switch application to use **TEST** keys for development
3. Verify transactions appear in correct dashboard

**Next step:** Please confirm which dashboard mode you were checking (Test vs Live) and whether transactions appear when viewing the correct one.

---

**End of Updated Report**

*This report supersedes the previous analysis with corrected findings based on actual .env configuration.*
