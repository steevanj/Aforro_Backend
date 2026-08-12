import random

from faker import Faker

from django.core.management.base import BaseCommand
from django.db import transaction

from products.models import Category, Product
from stores.models import Store, Inventory


fake = Faker()


class Command(BaseCommand):

    help = "Generate sample data"

    @transaction.atomic
    def handle(self, *args, **kwargs):

        self.stdout.write(
            "Generating seed data..."
        )

        # ------------------------------
        # Categories
        # ------------------------------

        categories = []

        for i in range(15):

            categories.append(
                Category(
                    name=f"Category {i + 1}"
                )
            )

        Category.objects.bulk_create(
            categories,
            ignore_conflicts=True
        )

        categories = list(
            Category.objects.all()
        )

        # ------------------------------
        # Products
        # ------------------------------

        products = []

        for i in range(1200):

            products.append(
                Product(
                    title=f"{fake.word().title()} Product {i + 1}",
                    description=fake.text(
                        max_nb_chars=200
                    ),
                    price=random.randint(
                        100,
                        100000
                    ),
                    category=random.choice(
                        categories
                    )
                )
            )

        Product.objects.bulk_create(
            products,
            batch_size=500
        )

        # ------------------------------
        # Stores
        # ------------------------------

        stores = []

        for i in range(25):

            stores.append(
                Store(
                    name=f"Store {i + 1}",
                    location=fake.city()
                )
            )

        Store.objects.bulk_create(
            stores
        )

        # ------------------------------
        # Inventory
        # ------------------------------

        products = list(
            Product.objects.all()
        )

        stores = list(
            Store.objects.all()
        )

        inventory = []

        for store in stores:

            selected_products = random.sample(
                products,
                300
            )

            for product in selected_products:

                inventory.append(
                    Inventory(
                        store=store,
                        product=product,
                        quantity=random.randint(
                            0,
                            100
                        )
                    )
                )

        Inventory.objects.bulk_create(
            inventory,
            batch_size=1000
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Seed data generated successfully."
            )
        )