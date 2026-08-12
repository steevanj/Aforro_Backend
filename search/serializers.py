from rest_framework import serializers

from products.models import Product


class ProductSearchSerializer(
    serializers.ModelSerializer
):

    category_name = serializers.CharField(
        source="category.name",
        read_only=True
    )

    inventory_quantity = serializers.IntegerField(
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "description",
            "price",
            "category",
            "category_name",
            "created_at",
            "inventory_quantity",
        ]