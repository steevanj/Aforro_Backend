from rest_framework import serializers

from ..models import Order
from .order_item import OrderItemCreateSerializer


class OrderCreateSerializer(serializers.ModelSerializer):
    store_id = serializers.IntegerField(write_only=True, min_value=1)
    items = OrderItemCreateSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = ["store_id", "items"]

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("At least one item is required.")

        product_ids = [item["product_id"] for item in items]

        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError("Duplicate products are not allowed.")

        return items
