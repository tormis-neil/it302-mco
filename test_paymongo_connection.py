#!/usr/bin/env python
"""
Quick test script to verify PayMongo API connectivity.
Run this after updating your .env file with real test keys.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, '/home/user/it302-mco')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'brewschews.settings')
django.setup()

from django.conf import settings
from orders.payments import _make_request, PayMongoError

print("=" * 60)
print("PayMongo Connection Test")
print("=" * 60)

# Check configuration
print("\n1. Checking Configuration...")
print(f"   Secret Key: {settings.PAYMONGO_SECRET_KEY[:15]}...")
print(f"   Public Key: {settings.PAYMONGO_PUBLIC_KEY[:15]}...")

if settings.PAYMONGO_SECRET_KEY == "sk_test_placeholder":
    print("   ❌ ERROR: Still using placeholder keys!")
    print("   → Update .env file with real test keys from PayMongo dashboard")
    sys.exit(1)

if not settings.PAYMONGO_SECRET_KEY.startswith("sk_test_"):
    print("   ⚠️  WARNING: Not using test keys!")
    print(f"   → Key starts with: {settings.PAYMONGO_SECRET_KEY[:8]}")
    if settings.PAYMONGO_SECRET_KEY.startswith("sk_live_"):
        print("   → You're using LIVE keys (real money)!")

print("   ✅ Configuration looks good")

# Test API connectivity
print("\n2. Testing PayMongo API Connection...")

try:
    # Try to list checkout sessions (doesn't create anything)
    response = _make_request("GET", "/checkout_sessions?limit=1")
    print("   ✅ SUCCESS! Connected to PayMongo API")
    print(f"   → API responded with data")

    # Check if we got valid response structure
    if "data" in response:
        print("   ✅ API response is valid")

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nYour PayMongo integration is configured correctly!")
    print("\nNext steps:")
    print("1. Start your server: python manage.py runserver")
    print("2. Make a test order on your website")
    print("3. Check PayMongo TEST dashboard for the transaction")
    print("\nTest Card: 4343 4343 4343 4345")
    print("Expiry: 12/28, CVV: 123")

except PayMongoError as e:
    print(f"   ❌ FAILED: {e.message}")
    print(f"   → Status Code: {e.status_code}")

    if e.status_code == 401:
        print("\n   → This means your API keys are INVALID")
        print("   → Double-check your keys in .env file")
        print("   → Make sure you copied them correctly from dashboard")

    print("\n" + "=" * 60)
    print("❌ TEST FAILED")
    print("=" * 60)
    sys.exit(1)

except Exception as e:
    print(f"   ❌ ERROR: {e}")
    print("\n" + "=" * 60)
    print("❌ TEST FAILED")
    print("=" * 60)
    sys.exit(1)
