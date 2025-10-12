from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class CatalogViewTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = User.objects.create_user(
            username="menuuser",
            email="menu@example.com",
            password="ComplexPass1!",
        )

    def test_catalog_requires_authentication(self) -> None:
        response = self.client.get(reverse("menu:catalog"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_catalog_renders_menu_preview(self) -> None:
        self.client.login(username="menuuser", password="ComplexPass1!")
        response = self.client.get(reverse("menu:catalog"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Our ordering engine is almost ready")
        self.assertContains(response, "Coming Soon")