from rest_framework import serializers

from ..models import Product


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = ["id", "title", "description", "price", "category", "category_name", "created_at"]
