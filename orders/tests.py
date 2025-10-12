from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class OrdersDashboardUITests(TestCase):
    def setUp(self) -> None:
        self.anonymous_client = Client()
        self.authenticated_client = Client()
        self.user = User.objects.create_user(
            username="dashuser",
            email="dash@example.com",
            password="SecurePass1!",
        )
        self.authenticated_client.login(username="dashuser", password="SecurePass1!")

    def test_cart_view_requires_authentication(self) -> None:
        response = self.anonymous_client.get(reverse("orders:cart"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_cart_view_renders_placeholder_content(self) -> None:
        response = self.authenticated_client.get(reverse("orders:cart"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "preview mode")
        self.assertContains(response, "Checkout coming soon")

    def test_checkout_view_is_read_only(self) -> None:
        response = self.authenticated_client.get(reverse("orders:checkout"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Checkout is in staging mode")
        self.assertContains(response, "Fields are disabled")

    def test_history_view_lists_sample_orders(self) -> None:
        response = self.authenticated_client.get(reverse("orders:history"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recent orders")
        self.assertContains(response, "Order BC-")