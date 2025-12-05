"""
PayMongo webhook handlers for payment events.

Webhooks are HTTP callbacks that PayMongo sends to your server
when payment events occur (e.g., payment successful).

Security:
- All webhooks are verified using HMAC-SHA256 signatures
- Invalid signatures are rejected with 403 status
- Events are idempotent (safe to receive multiple times)

Events Handled:
- checkout_session.payment.paid: Payment successful
- payment.failed: Payment failed

URL: /orders/webhooks/paymongo/
"""

from __future__ import annotations

import json
import logging

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from orders.models import Order
from orders.payments import verify_webhook_signature, extract_payment_info

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def paymongo_webhook(request: HttpRequest) -> HttpResponse:
    """
    Handle incoming PayMongo webhook events.

    This endpoint receives webhook notifications from PayMongo
    when payment events occur.

    Security:
    - CSRF exempt (webhooks come from external source)
    - Signature verification via HMAC-SHA256
    - POST only

    Supported Events:
    - checkout_session.payment.paid: Mark order as paid
    - payment.failed: Mark order as failed

    Returns:
        200: Webhook processed successfully
        400: Invalid JSON payload
        403: Invalid signature
        404: Order not found

    URL: /orders/webhooks/paymongo/
    """
    # Get signature from header
    signature_header = request.headers.get("Paymongo-Signature", "")

    # Verify signature
    if not verify_webhook_signature(request.body, signature_header):
        logger.warning("Invalid webhook signature")
        return HttpResponse(status=403)

    # Parse JSON payload
    try:
        webhook_data = json.loads(request.body)
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook payload")
        return HttpResponse(status=400)

    # Extract payment info
    payment_info = extract_payment_info(webhook_data)
    event_type = payment_info["event_type"]

    logger.info(
        f"Received webhook: {event_type}",
        extra={"payment_info": payment_info}
    )

    # Handle different event types
    if event_type == "checkout_session.payment.paid":
        return _handle_payment_paid(payment_info)
    elif event_type == "payment.failed":
        return _handle_payment_failed(payment_info)
    else:
        # Acknowledge unknown events (don't fail)
        logger.info(f"Ignoring unhandled event type: {event_type}")
        return JsonResponse({"status": "ignored", "event": event_type})


def _handle_payment_paid(payment_info: dict) -> HttpResponse:
    """
    Handle successful payment event.

    Updates the order status to 'paid' and stores payment details.

    Args:
        payment_info: Extracted payment information

    Returns:
        JsonResponse with processing result
    """
    order_id = payment_info.get("order_id")
    checkout_session_id = payment_info.get("checkout_session_id")

    # Find order by ID or checkout session
    order = None

    if order_id:
        try:
            order = Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            pass

    if not order and checkout_session_id:
        try:
            order = Order.objects.get(checkout_session_id=checkout_session_id)
        except Order.DoesNotExist:
            pass

    if not order:
        logger.error(
            f"Order not found for payment",
            extra={"payment_info": payment_info}
        )
        return HttpResponse(status=404)

    # Check if already processed (idempotency)
    if order.status == Order.Status.PAID:
        logger.info(f"Order {order.reference_number} already marked as paid")
        return JsonResponse({
            "status": "already_processed",
            "order_reference": order.reference_number
        })

    # Mark order as paid
    order.mark_paid(
        payment_intent_id=payment_info.get("payment_intent_id", ""),
        payment_method=payment_info.get("payment_method", ""),
    )

    logger.info(
        f"Order {order.reference_number} marked as paid",
        extra={
            "payment_intent_id": payment_info.get("payment_intent_id"),
            "payment_method": payment_info.get("payment_method"),
        }
    )

    return JsonResponse({
        "status": "success",
        "order_reference": order.reference_number,
        "payment_status": "paid",
    })


def _handle_payment_failed(payment_info: dict) -> HttpResponse:
    """
    Handle failed payment event.

    Updates the order status to 'failed'.

    Args:
        payment_info: Extracted payment information

    Returns:
        JsonResponse with processing result
    """
    order_id = payment_info.get("order_id")
    checkout_session_id = payment_info.get("checkout_session_id")

    # Find order
    order = None

    if order_id:
        try:
            order = Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            pass

    if not order and checkout_session_id:
        try:
            order = Order.objects.get(checkout_session_id=checkout_session_id)
        except Order.DoesNotExist:
            pass

    if not order:
        logger.error(
            f"Order not found for failed payment",
            extra={"payment_info": payment_info}
        )
        return HttpResponse(status=404)

    # Mark order as failed
    order.mark_failed()

    logger.warning(
        f"Order {order.reference_number} payment failed",
        extra={"payment_info": payment_info}
    )

    return JsonResponse({
        "status": "success",
        "order_reference": order.reference_number,
        "payment_status": "failed",
    })
