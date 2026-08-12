from rest_framework import serializers

from ..models import OrderItem


class OrderItemCreateSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(write_only=True, min_value=1)

    class Meta:
        model = OrderItem
        fields = ["product_id", "quantity_requested"]

    def validate_quantity_requested(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value


class OrderItemSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source="product.title", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_title", "quantity_requested"]
