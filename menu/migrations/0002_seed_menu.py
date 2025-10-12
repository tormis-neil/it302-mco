from decimal import Decimal

from django.db import migrations

from pages.menu_data import MENU_CATEGORIES

PRICES = {
    "Maple Cocoa Nibs Oatmilk Shaken Espresso": Decimal("195.00"),
    "Frappuccino": Decimal("185.00"),
    "Drip Coffee": Decimal("120.00"),
    "Cold Brew": Decimal("150.00"),
    "Espresso Shot": Decimal("110.00"),
    "Cappuccino": Decimal("145.00"),
    "Chai Tea Cream Frappuccino": Decimal("175.00"),
    "Caramel Cream Frappuccino": Decimal("180.00"),
    "Full Leaf Brewed Tea": Decimal("105.00"),
    "Iced Black Tea Latte": Decimal("160.00"),
    "Lemonade": Decimal("95.00"),
    "Iced Cucumber": Decimal("115.00"),
    "Glazed Chicken": Decimal("210.00"),
    "Buttered Chicken": Decimal("225.00"),
    "Chocolate Dipped Doughnut": Decimal("85.00"),
    "Bacon Belgian Waffle": Decimal("165.00"),
    "Cheesy Tuna Sandwich": Decimal("155.00"),
    "Egg Sandwich": Decimal("140.00"),
}


def seed_menu(apps, schema_editor):
    Category = apps.get_model("menu", "Category")
    MenuItem = apps.get_model("menu", "MenuItem")

    if Category.objects.exists():
        return

    for order, category_data in enumerate(MENU_CATEGORIES, start=1):
        category = Category.objects.create(
            name=category_data.title,
            slug=category_data.slug,
            description=category_data.blurb,
            kind="drink" if category_data.kind == "drinks" else "food",
            display_order=order,
            is_featured=category_data.kind == "drinks" and order == 1,
        )
        for item_order, item in enumerate(category_data.items, start=1):
            MenuItem.objects.create(
                category=category,
                name=item.name,
                slug="{}-{}".format(category.slug, item_order),
                description=item.description,
                base_price=PRICES.get(item.name, Decimal("150.00")),
                image=item.image,
                display_order=item_order,
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