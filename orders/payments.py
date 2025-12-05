"""
PayMongo API integration for payment processing.

This module provides functions to interact with the PayMongo API:
- create_checkout_session(): Create a checkout session for an order
- verify_webhook_signature(): Verify webhook authenticity
- get_checkout_session(): Retrieve checkout session details

PayMongo Flow:
1. User clicks "Pay Now" → create_checkout_session()
2. User redirected to PayMongo hosted checkout
3. User pays via Card/GCash/Maya
4. PayMongo sends webhook → verify_webhook_signature()
5. Order marked as paid

API Documentation: https://developers.paymongo.com/reference
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
from decimal import Decimal
from typing import Optional, Tuple

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class PayMongoError(Exception):
    """Custom exception for PayMongo API errors."""

    def __init__(self, message: str, status_code: int = None, response: dict = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


def _get_auth_header() -> str:
    """
    Generate Basic Auth header for PayMongo API.

    PayMongo uses HTTP Basic Auth with secret key as username
    and empty password.

    Returns:
        Base64 encoded auth string
    """
    secret_key = settings.PAYMONGO_SECRET_KEY
    # Format: base64(secret_key:)
    credentials = f"{secret_key}:"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


def _make_request(
    method: str,
    endpoint: str,
    data: dict = None,
) -> dict:
    """
    Make authenticated request to PayMongo API.

    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint (e.g., /checkout_sessions)
        data: Request payload for POST requests

    Returns:
        API response as dictionary

    Raises:
        PayMongoError: If API request fails
    """
    url = f"{settings.PAYMONGO_API_URL}{endpoint}"
    headers = {
        "Authorization": _get_auth_header(),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data,
            timeout=30,
        )

        response_data = response.json()

        if not response.ok:
            error_message = "PayMongo API error"
            if "errors" in response_data:
                errors = response_data["errors"]
                if errors:
                    error_message = errors[0].get("detail", error_message)

            logger.error(
                f"PayMongo API error: {error_message}",
                extra={
                    "status_code": response.status_code,
                    "response": response_data,
                }
            )
            raise PayMongoError(
                message=error_message,
                status_code=response.status_code,
                response=response_data,
            )

        return response_data

    except requests.RequestException as e:
        logger.error(f"PayMongo request failed: {e}")
        raise PayMongoError(f"Failed to connect to PayMongo: {e}")


def create_checkout_session(
    order,
    success_url: str,
    cancel_url: str,
) -> Tuple[str, str]:
    """
    Create a PayMongo checkout session for an order.

    This creates a hosted checkout page where the user can pay
    via Card, GCash, or PayMaya.

    Args:
        order: Order model instance
        success_url: URL to redirect after successful payment
        cancel_url: URL to redirect if user cancels

    Returns:
        Tuple of (checkout_session_id, checkout_url)

    Raises:
        PayMongoError: If session creation fails

    Example:
        session_id, checkout_url = create_checkout_session(
            order=order,
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
        )
        # Redirect user to checkout_url
    """
    # Convert total to centavos (PayMongo uses smallest currency unit)
    amount_centavos = int(order.total * 100)

    # Build line items from order items
    line_items = []
    for item in order.items.all():
        line_items.append({
            "currency": settings.PAYMENT_CURRENCY,
            "amount": int(item.unit_price * 100),  # Convert to centavos
            "name": item.menu_item_name,
            "quantity": item.quantity,
        })

    # Create checkout session payload
    payload = {
        "data": {
            "attributes": {
                "send_email_receipt": False,
                "show_description": True,
                "show_line_items": True,
                "description": f"{settings.PAYMENT_DESCRIPTION_PREFIX} #{order.reference_number}",
                "line_items": line_items,
                "payment_method_types": ["card", "gcash", "paymaya"],
                "success_url": success_url,
                "cancel_url": cancel_url,
                "reference_number": order.reference_number,
                "metadata": {
                    "order_id": str(order.pk),
                    "reference_number": order.reference_number,
                },
            }
        }
    }

    logger.info(f"Creating checkout session for order {order.reference_number}")

    response = _make_request("POST", "/checkout_sessions", payload)

    checkout_session = response["data"]
    session_id = checkout_session["id"]
    checkout_url = checkout_session["attributes"]["checkout_url"]

    logger.info(
        f"Checkout session created: {session_id} for order {order.reference_number}"
    )

    return session_id, checkout_url


def get_checkout_session(session_id: str) -> dict:
    """
    Retrieve checkout session details from PayMongo.

    Useful for checking payment status without webhooks.

    Args:
        session_id: PayMongo checkout session ID

    Returns:
        Checkout session data

    Raises:
        PayMongoError: If retrieval fails
    """
    response = _make_request("GET", f"/checkout_sessions/{session_id}")
    return response["data"]


def verify_webhook_signature(
    payload: bytes,
    signature_header: str,
) -> bool:
    """
    Verify PayMongo webhook signature.

    PayMongo signs webhooks using HMAC-SHA256 with your webhook secret.
    This prevents attackers from sending fake webhook events.

    Args:
        payload: Raw request body bytes
        signature_header: Value of 'Paymongo-Signature' header

    Returns:
        True if signature is valid, False otherwise

    Signature Header Format:
        t=timestamp,te=test_signature,li=live_signature

    Example:
        is_valid = verify_webhook_signature(
            payload=request.body,
            signature_header=request.headers.get('Paymongo-Signature'),
        )
        if not is_valid:
            return HttpResponse(status=403)
    """
    webhook_secret = settings.PAYMONGO_WEBHOOK_SECRET

    if not webhook_secret:
        # If no webhook secret configured, skip verification (dev mode)
        logger.warning("Webhook secret not configured, skipping verification")
        return True

    if not signature_header:
        logger.warning("No signature header provided")
        return False

    try:
        # Parse signature header
        # Format: t=timestamp,te=test_signature,li=live_signature
        parts = {}
        for part in signature_header.split(","):
            key, value = part.split("=", 1)
            parts[key] = value

        timestamp = parts.get("t", "")
        test_signature = parts.get("te", "")
        live_signature = parts.get("li", "")

        # Use test or live signature based on environment
        expected_signature = test_signature or live_signature

        if not timestamp or not expected_signature:
            logger.warning("Invalid signature header format")
            return False

        # Compute expected signature
        # signed_payload = timestamp + "." + payload
        signed_payload = f"{timestamp}.{payload.decode('utf-8')}"

        computed_signature = hmac.new(
            webhook_secret.encode(),
            signed_payload.encode(),
            hashlib.sha256
        ).hexdigest()

        # Compare signatures (timing-safe)
        is_valid = hmac.compare_digest(computed_signature, expected_signature)

        if not is_valid:
            logger.warning("Webhook signature verification failed")

        return is_valid

    except Exception as e:
        logger.error(f"Webhook signature verification error: {e}")
        return False


def extract_payment_info(webhook_data: dict) -> dict:
    """
    Extract payment information from webhook payload.

    Args:
        webhook_data: Parsed webhook JSON data

    Returns:
        Dictionary with payment info:
        - event_type: Type of event (e.g., 'checkout_session.payment.paid')
        - checkout_session_id: Checkout session ID
        - payment_intent_id: Payment intent ID (if available)
        - payment_method: Payment method used
        - order_reference: Order reference number from metadata
        - order_id: Order ID from metadata
    """
    data = webhook_data.get("data", {})
    attributes = data.get("attributes", {})

    event_type = attributes.get("type", "")

    # Extract from checkout session data
    checkout_data = attributes.get("data", {})
    checkout_attributes = checkout_data.get("attributes", {})

    # Get payment intent if available
    payments = checkout_attributes.get("payments", [])
    payment_intent_id = ""
    payment_method = ""

    if payments:
        payment = payments[0]
        payment_attributes = payment.get("attributes", {})
        payment_intent_id = payment.get("id", "")

        # Get payment method type
        source = payment_attributes.get("source", {})
        payment_method = source.get("type", "unknown")

    # Get metadata
    metadata = checkout_attributes.get("metadata", {})

    return {
        "event_type": event_type,
        "checkout_session_id": checkout_data.get("id", ""),
        "payment_intent_id": payment_intent_id,
        "payment_method": payment_method,
        "order_reference": metadata.get("reference_number", ""),
        "order_id": metadata.get("order_id", ""),
    }
