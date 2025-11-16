"""URL configuration for the orders app."""
from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    # Cart operations (Phase 1)
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/", views.add_to_cart, name="add_to_cart"),
    path("cart/update/<int:cart_item_id>/", views.update_cart_item, name="update_cart_item"),
    path("cart/remove/<int:cart_item_id>/", views.remove_from_cart, name="remove_from_cart"),

    # Checkout and history (Phase 2)
    path("checkout/", views.checkout, name="checkout"),
    path("history/", views.history, name="history"),
]