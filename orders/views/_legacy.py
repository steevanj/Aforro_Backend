from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from stores.models import Store, Inventory

from .models import Order, OrderItem
from .serializers import (
    OrderCreateSerializer,
    OrderSerializer,
    OrderListSerializer
)
from django.db.models import Count
from .tasks import send_order_confirmation


class OrderCreateAPIView(APIView):

    def post(self, request):

        # --------------------------------
        # 1. Validate request
        # --------------------------------

        serializer = OrderCreateSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        store_id = serializer.validated_data[
            "store_id"
        ]

        items = serializer.validated_data[
            "items"
        ]

        product_ids = [
            item["product_id"]
            for item in items
        ]

        # --------------------------------
        # 2. Start transaction
        # --------------------------------

        with transaction.atomic():

            # Check store
            store = get_object_or_404(
                Store,
                id=store_id
            )

            # --------------------------------
            # 3. Lock inventory rows
            # --------------------------------

            inventory_rows = list(
                Inventory.objects
                .select_for_update()
                .select_related("product")
                .filter(
                    store_id=store_id,
                    product_id__in=product_ids
                )
            )

            inventory_map = {
                inventory.product_id: inventory
                for inventory in inventory_rows
            }

            # --------------------------------
            # 4. Check stock
            # --------------------------------

            insufficient_products = []

            for item in items:

                product_id = item["product_id"]

                requested_quantity = item[
                    "quantity_requested"
                ]

                inventory = inventory_map.get(
                    product_id
                )

                if (
                    inventory is None
                    or inventory.quantity < requested_quantity
                ):
                    insufficient_products.append(
                        product_id
                    )

            # --------------------------------
            # 5. Determine status
            # --------------------------------

            if insufficient_products:

                order_status = Order.Status.REJECTED

            else:

                order_status = Order.Status.CONFIRMED

            # --------------------------------
            # 6. Create order
            # --------------------------------

            order = Order.objects.create(
                store=store,
                status=order_status
            )

            # --------------------------------
            # 7. Create order items
            # --------------------------------

            order_items = [
                OrderItem(
                    order=order,
                    product_id=item["product_id"],
                    quantity_requested=item[
                        "quantity_requested"
                    ]
                )
                for item in items
            ]

            OrderItem.objects.bulk_create(
                order_items
            )

            # --------------------------------
            # 8. Deduct inventory
            # --------------------------------

            if order_status == Order.Status.CONFIRMED:

                for item in items:

                    inventory = inventory_map[
                        item["product_id"]
                    ]

                    inventory.quantity -= item[
                        "quantity_requested"
                    ]

                Inventory.objects.bulk_update(
                    inventory_rows,
                    ["quantity"]
                )

                # --------------------------------
                # 9. Invalidate Redis cache
                # --------------------------------

                transaction.on_commit(
                    lambda store_id=store_id:
                    invalidate_inventory_cache(
                        store_id
                    )
                )

                # --------------------------------
                # 10. Trigger Celery
                # --------------------------------

                transaction.on_commit(
                    lambda order_id=order.id:
                    send_order_confirmation.delay(
                        order_id
                    )
                )

        # --------------------------------
        # 11. Fetch optimized response
        # --------------------------------

        order = (
            Order.objects
            .select_related("store")
            .prefetch_related(
                "items__product"
            )
            .get(id=order.id)
        )

        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED
        )

class StoreOrderListAPIView(APIView):

    def get(self, request, store_id):

        orders = (
            Order.objects
            .filter(
                store_id=store_id
            )
            .annotate(
                total_items=Count("items")
            )
            .order_by(
                "-created_at"
            )
        )

        serializer = OrderListSerializer(
            orders,
            many=True
        )

        return Response(
            serializer.data
        )