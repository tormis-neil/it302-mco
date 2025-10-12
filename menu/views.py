"""Authenticated menu views."""
from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from .models import Category, MenuItem


def _available_categories():
    """Return the available categories and items for display."""

    item_queryset = MenuItem.objects.filter(is_available=True)
    return (
        Category.objects.filter(items__is_available=True)
        .prefetch_related(Prefetch("items", queryset=item_queryset))
        .order_by("display_order", "name")
    )


@login_required
@require_GET
def catalog(request: HttpRequest) -> HttpResponse:
    """Render the authenticated menu as a read-only preview UI."""

    categories = _available_categories()
    context = {
        "categories": categories,
    }
    return render(request, "menu/catalog.html", context)