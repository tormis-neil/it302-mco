from decimal import Decimal
from django.db import migrations


def seed_menu(apps, schema_editor):
    Category = apps.get_model("menu", "Category")
    MenuItem = apps.get_model("menu", "MenuItem")

    # Don't seed if data already exists
    if Category.objects.exists():
        return

    # Featured Drinks
    featured = Category.objects.create(
        name="Featured Drinks",
        slug="featured-drinks",
        description="Seasonal favorites curated by our baristas.",
        kind="drink",
        display_order=1,
        is_featured=True,
    )
    MenuItem.objects.create(
        category=featured,
        name="Maple Cocoa Nibs Oatmilk Shaken Espresso",
        slug="featured-drinks-1",
        description="A cozy blend of maple, cocoa nibs, and velvety oatmilk shaken over ice.",
        base_price=Decimal("195.00"),
        image="img/menu/maple-oatmilk.jpg",
        display_order=1,
    )
    MenuItem.objects.create(
        category=featured,
        name="Frappuccino",
        slug="featured-drinks-2",
        description="Our signature blended beverage with whipped cream and caramel drizzle.",
        base_price=Decimal("185.00"),
        image="img/menu/frappuccino.jpg",
        display_order=2,
    )

    # Brewed Coffee
    brewed = Category.objects.create(
        name="Brewed Coffee",
        slug="brewed-coffee",
        description="Slow brewed classics to jump-start your day.",
        kind="drink",
        display_order=2,
    )
    MenuItem.objects.create(
        category=brewed,
        name="Drip Coffee",
        slug="brewed-coffee-1",
        description="Freshly brewed medium roast with a smooth finish.",
        base_price=Decimal("120.00"),
        image="img/menu/drip-coffee.jpg",
        display_order=1,
    )
    MenuItem.objects.create(
        category=brewed,
        name="Cold Brew",
        slug="brewed-coffee-2",
        description="Steeped for 20 hours for a naturally sweet, less acidic cup.",
        base_price=Decimal("150.00"),
        image="img/menu/cold-brew.jpg",
        display_order=2,
    )

    # Espresso
    espresso = Category.objects.create(
        name="Espresso",
        slug="espresso",
        description="Pulled-to-order shots and milk-based espresso favorites.",
        kind="drink",
        display_order=3,
    )
    MenuItem.objects.create(
        category=espresso,
        name="Espresso Shot",
        slug="espresso-1",
        description="A concentrated shot with rich crema and balanced sweetness.",
        base_price=Decimal("110.00"),
        image="img/menu/espresso.jpg",
        display_order=1,
    )
    MenuItem.objects.create(
        category=espresso,
        name="Cappuccino",
        slug="espresso-2",
        description="Equal parts espresso, steamed milk, and foam dusted with cocoa.",
        base_price=Decimal("145.00"),
        image="img/menu/cappuccino.jpg",
        display_order=2,
    )

    # Bakery
    bakery = Category.objects.create(
        name="Bakery",
        slug="bakery",
        description="Freshly baked goods made in-house every morning.",
        kind="food",
        display_order=4,
    )
    MenuItem.objects.create(
        category=bakery,
        name="Chocolate Dipped Doughnut",
        slug="bakery-1",
        description="Yeast doughnut dipped in rich dark chocolate glaze.",
        base_price=Decimal("85.00"),
        image="img/menu/chocolate-donut.jpg",
        display_order=1,
    )
    MenuItem.objects.create(
        category=bakery,
        name="Egg Sandwich",
        slug="bakery-2",
        description="Soft brioche filled with scrambled eggs and cheddar cheese.",
        base_price=Decimal("140.00"),
        image="img/menu/egg-sandwich.jpg",
        display_order=2,
    )


def unseed_menu(apps, schema_editor):
    Category = apps.get_model("menu", "Category")
    Category.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("menu", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_menu, unseed_menu),
    ]