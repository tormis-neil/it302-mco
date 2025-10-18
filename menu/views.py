"""
Authenticated menu views.

Views:
- catalog(): Display menu items to logged-in users

Purpose: Shows available menu items organized by category
Access: Requires authentication (@login_required)
Status: Fully functional read-only display

Related Files:
- menu/models.py: Category and MenuItem models
- templates/menu/catalog.html: Template for display
- menu/urls.py: Routes /menu/ to catalog view
"""

from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from .models import Category, MenuItem


def _available_categories():
    """
    Return categories with available items for display.
    
    Process:
    1. Filter items: Only show is_available=True
    2. Filter categories: Only show categories that have available items
    3. Prefetch items: Optimize database queries (avoid N+1 problem)
    4. Order by: display_order, then name
    
    Returns:
        QuerySet of Category objects with prefetched available items
    
    Example:
        categories = _available_categories()
        for category in categories:
            print(f"{category.name}:")
            for item in category.items.all():
                print(f"  - {item.name} (₱{item.base_price})")
    
    Database Queries:
        Without prefetch: N+1 queries (1 for categories + N for each category's items)
        With prefetch: 2 queries total (1 for categories + 1 for all items)
    """
    # Create queryset for available items only
    item_queryset = MenuItem.objects.filter(is_available=True)
    
    # Get categories that have at least one available item
    # Prefetch their items to avoid multiple database hits
    return (
        Category.objects.filter(items__is_available=True)
        .prefetch_related(Prefetch("items", queryset=item_queryset))
        .order_by("display_order", "name")
    )


@login_required  # Requires user to be logged in
@require_GET     # Only allows GET requests (no POST)
def catalog(request: HttpRequest) -> HttpResponse:
    """
    Render the authenticated menu as a read-only preview UI.
    
    Purpose: Display available menu items organized by category
    
    Flow:
    1. Check user is authenticated (@login_required decorator)
    2. Query available categories and items
    3. Pass data to template
    4. Render menu/catalog.html
    
    Access Control:
    - Requires login: @login_required redirects to /accounts/login/ if not logged in
    - Read-only: No cart functionality yet (coming in Phase 2)
    
    Template Context:
    - categories: QuerySet of Category objects with items
    
    URL:
    - /menu/ → This view
    
    Example Usage:
        # User visits http://127.0.0.1:8000/menu/
        # If not logged in → Redirected to /accounts/login/
        # If logged in → See menu organized by categories
    
    Current Limitations:
    - "Add to Cart" buttons are disabled (UI placeholder)
    - Cannot actually order items yet
    - Menu is read-only display
    
    Future Enhancements:
    - Enable "Add to Cart" functionality
    - Show item availability status
    - Filter by category
    - Search menu items
    """
    # Get all categories with their available items
    categories = _available_categories()
    
    # Prepare data for template
    context = {
        "categories": categories,
    }
    
    # Render template with context data
    return render(request, "menu/catalog.html", context)