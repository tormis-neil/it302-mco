"""URL configuration for the orders app."""
from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("cart/", views.cart_view, name="cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("history/", views.history, name="history"),
]