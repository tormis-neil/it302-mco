"""Views for the pages app."""
from django.shortcuts import render
from django.views.decorators.http import require_GET

from .menu_data import MENU_CATEGORIES, get_menu_categories


@require_GET
def home(request):
    """Render the marketing landing page."""
    return render(request, "pages/index.html")


@require_GET
def menu_preview(request):
    """Render the menu preview page."""
    drinks = get_menu_categories("drinks")
    food = get_menu_categories("food")

    default_category = ""
    if drinks:
        default_category = drinks[0].slug
    elif MENU_CATEGORIES:
        default_category = MENU_CATEGORIES[0].slug

    return render(
        request,
        "pages/menu.html",
        {
            "drinks_categories": drinks,
            "food_categories": food,
            "all_categories": MENU_CATEGORIES,
            "default_category": default_category,
        },
    )