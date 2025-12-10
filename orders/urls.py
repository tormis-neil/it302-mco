"""URL configuration for the orders app."""
from django.urls import path

from . import views
from . import webhooks

app_name = "orders"

urlpatterns = [
    # Cart operations
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/", views.add_to_cart, name="add_to_cart"),
    path("cart/update/<int:cart_item_id>/", views.update_cart_item, name="update_cart_item"),
    path("cart/remove/<int:cart_item_id>/", views.remove_from_cart, name="remove_from_cart"),

    # Checkout and history
    path("checkout/", views.checkout, name="checkout"),
    path("history/", views.history, name="history"),

    # Payment (PayMongo Integration)
    path("payment/success/", views.payment_success, name="payment_success"),
    path("payment/cancel/", views.payment_cancel, name="payment_cancel"),
    path("payment/retry/<int:order_id>/", views.retry_payment, name="retry_payment"),

    # Webhooks (PayMongo callbacks)
    path("webhooks/paymongo/", webhooks.paymongo_webhook, name="paymongo_webhook"),
]