"""Static menu data used to render the preview page before the database is ready."""

from dataclasses import dataclass
from typing import List, Sequence


@dataclass(frozen=True)
class MenuItem:
    """Simple representation of a menu item for the preview page."""

    name: str
    image: str
    description: str


@dataclass(frozen=True)
class MenuCategory:
    """Grouping of menu items for display in the preview UI."""

    slug: str
    title: str
    kind: str  # either "drinks" or "food"
    blurb: str
    items: Sequence[MenuItem]


MENU_CATEGORIES: List[MenuCategory] = [
    MenuCategory(
        slug="featured-drinks",
        title="Featured Drinks",
        kind="drinks",
        blurb="Seasonal favorites curated by our baristas.",
        items=(
            MenuItem(
                name="Maple Cocoa Nibs Oatmilk Shaken Espresso",
                image="img/Product 1.jpg",
                description="A cozy blend of maple, cocoa nibs, and velvety oatmilk shaken over ice.",
            ),
            MenuItem(
                name="Frappuccino",
                image="img/Product 2.jpg",
                description="Our signature blended beverage with whipped cream and caramel drizzle.",
            ),
        ),
    ),
    MenuCategory(
        slug="brewed-coffee",
        title="Brewed Coffee",
        kind="drinks",
        blurb="Slow brewed classics to jump-start your day.",
        items=(
            MenuItem(
                name="Drip Coffee",
                image="img/bg.jpg",
                description="Freshly brewed medium roast with a smooth finish.",
            ),
            MenuItem(
                name="Cold Brew",
                image="img/bg.jpg",
                description="Steeped for 20 hours for a naturally sweet, less acidic cup.",
            ),
        ),
    ),
    MenuCategory(
        slug="espresso",
        title="Espresso",
        kind="drinks",
        blurb="Pulled-to-order shots and milk-based espresso favorites.",
        items=(
            MenuItem(
                name="Espresso Shot",
                image="img/bg.jpg",
                description="A concentrated shot with rich crema and balanced sweetness.",
            ),
            MenuItem(
                name="Cappuccino",
                image="img/bg.jpg",
                description="Equal parts espresso, steamed milk, and foam dusted with cocoa.",
            ),
        ),
    ),
    MenuCategory(
        slug="blended-beverage",
        title="Blended Beverages",
        kind="drinks",
        blurb="Creamy and refreshing treats blended to perfection.",
        items=(
            MenuItem(
                name="Chai Tea Cream Frappuccino",
                image="img/bg.jpg",
                description="Spiced chai blended with milk and ice, finished with whipped cream.",
            ),
            MenuItem(
                name="Caramel Cream Frappuccino",
                image="img/bg.jpg",
                description="Buttery caramel blended with milk for a dessert-like sip.",
            ),
        ),
    ),
    MenuCategory(
        slug="teavana-tea",
        title="Teavana Tea",
        kind="drinks",
        blurb="Loose-leaf teas served hot or iced for any mood.",
        items=(
            MenuItem(
                name="Full Leaf Brewed Tea",
                image="img/bg.jpg",
                description="Choose from jasmine, earl grey, or chamomile, brewed to order.",
            ),
            MenuItem(
                name="Iced Black Tea Latte",
                image="img/bg.jpg",
                description="Bold black tea shaken with milk and a hint of sweetness over ice.",
            ),
        ),
    ),
    MenuCategory(
        slug="refreshers",
        title="Refreshers",
        kind="drinks",
        blurb="Light, fruit-forward refreshments with a caffeine boost.",
        items=(
            MenuItem(
                name="Lemonade",
                image="img/bg.jpg",
                description="House-made lemonade with freshly squeezed citrus.",
            ),
            MenuItem(
                name="Iced Cucumber",
                image="img/bg.jpg",
                description="Cucumber, mint, and lime shaken for a crisp cooler.",
            ),
        ),
    ),
    MenuCategory(
        slug="featured-food",
        title="Featured Food",
        kind="food",
        blurb="Limited-time pairings hand-picked for the season.",
        items=(
            MenuItem(
                name="Glazed Chicken",
                image="img/bg.jpg",
                description="Grilled chicken glazed with honey garlic and served warm.",
            ),
            MenuItem(
                name="Buttered Chicken",
                image="img/bg.jpg",
                description="Comforting butter chicken served with artisanal bread.",
            ),
        ),
    ),
    MenuCategory(
        slug="bakery",
        title="Bakery",
        kind="food",
        blurb="Freshly baked goods made in-house every morning.",
        items=(
            MenuItem(
                name="Chocolate Dipped Doughnut",
                image="img/bg.jpg",
                description="Yeast doughnut dipped in rich dark chocolate glaze.",
            ),
            MenuItem(
                name="Bacon Belgian Waffle",
                image="img/bg.jpg",
                description="Crisp waffle folded with smoky bacon bits and maple butter.",
            ),
        ),
    ),
    MenuCategory(
        slug="sandwiches",
        title="Sandwiches",
        kind="food",
        blurb="Savory sandwiches assembled with local ingredients.",
        items=(
            MenuItem(
                name="Cheesy Tuna Sandwich",
                image="img/bg.jpg",
                description="Toasted sourdough with creamy tuna salad and cheddar.",
            ),
            MenuItem(
                name="Egg Sandwich",
                image="img/bg.jpg",
                description="Soft brioche filled with scrambled eggs and cheddar cheese.",
            ),
        ),
    ),
]


def get_menu_categories(kind: str) -> List[MenuCategory]:
    """Return categories filtered by kind (drinks or food)."""

    kind = kind.lower()
    return [category for category in MENU_CATEGORIES if category.kind == kind]