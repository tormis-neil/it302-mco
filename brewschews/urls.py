"""Root URL configuration for the Brews & Chews project."""
from django.urls import include, path

urlpatterns = [
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("menu/", include(("menu.urls", "menu"), namespace="menu")),
    path("orders/", include(("orders.urls", "orders"), namespace="orders")),
    path("", include(("pages.urls", "pages"), namespace="pages")),
]