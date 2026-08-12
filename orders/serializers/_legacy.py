from rest_framework import serializers

from .models import Order, OrderItem


class OrderItemCreateSerializer(serializers.ModelSerializer):

    product_id = serializers.IntegerField(
        write_only=True,
        min_value=1
    )

    class Meta:
        model = OrderItem
        fields = [
            "product_id",
            "quantity_requested",
        ]

    def validate_quantity_requested(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Quantity must be greater than zero."
            )

        return value


class OrderCreateSerializer(serializers.ModelSerializer):

    store_id = serializers.IntegerField(
        write_only=True,
        min_value=1
    )

    items = OrderItemCreateSerializer(
        many=True,
        write_only=True
    )

    class Meta:
        model = Order
        fields = [
            "store_id",
            "items",
        ]

    def validate_items(self, items):

        if not items:
            raise serializers.ValidationError(
                "At least one item is required."
            )

        product_ids = [
            item["product_id"]
            for item in items
        ]

        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError(
                "Duplicate products are not allowed."
            )

        return items


class OrderItemSerializer(serializers.ModelSerializer):

    product_title = serializers.CharField(
        source="product.title",
        read_only=True
    )

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_title",
            "quantity_requested",
        ]


class OrderSerializer(serializers.ModelSerializer):

    items = OrderItemSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "store",
            "status",
            "created_at",
            "items",
        ]


class OrderListSerializer(serializers.ModelSerializer):

    total_items = serializers.IntegerField(
        read_only=True
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "created_at",
            "total_items",
        ]