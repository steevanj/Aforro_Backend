from django.db import transaction
from django.shortcuts import get_object_or_404
from django.db.models import Count
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from stores.models import Inventory, Store

from ..models import Order, OrderItem
from ..serializers import OrderCreateSerializer, OrderSerializer
from ..tasks import send_order_confirmation


class OrderCreateAPIView(APIView):
    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        store_id = serializer.validated_data["store_id"]
        items = serializer.validated_data["items"]
        product_ids = [item["product_id"] for item in items]

        with transaction.atomic():
            store = get_object_or_404(Store, id=store_id)
            inventory_rows = list(
                Inventory.objects.select_for_update()
                .select_related("product")
                .filter(store_id=store_id, product_id__in=product_ids)
            )
            inventory_map = {inventory.product_id: inventory for inventory in inventory_rows}

            insufficient_products = []
            for item in items:
                product_id = item["product_id"]
                requested_quantity = item["quantity_requested"]
                inventory = inventory_map.get(product_id)

                if inventory is None or inventory.quantity < requested_quantity:
                    insufficient_products.append(product_id)

            order_status = Order.Status.REJECTED if insufficient_products else Order.Status.CONFIRMED
            order = Order.objects.create(store=store, status=order_status)

            order_items = [
                OrderItem(
                    order=order,
                    product_id=item["product_id"],
                    quantity_requested=item["quantity_requested"],
                )
                for item in items
            ]
            OrderItem.objects.bulk_create(order_items)

            if order_status == Order.Status.CONFIRMED:
                for item in items:
                    inventory = inventory_map[item["product_id"]]
                    inventory.quantity -= item["quantity_requested"]

                Inventory.objects.bulk_update(inventory_rows, ["quantity"])
                transaction.on_commit(lambda store_id=store_id: invalidate_inventory_cache(store_id))
                transaction.on_commit(lambda order_id=order.id: send_order_confirmation.delay(order_id))

        order = (
            Order.objects.select_related("store")
            .prefetch_related("items__product")
            .get(id=order.id)
        )

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
