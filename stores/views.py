from django.core.cache import cache

from rest_framework.response import Response
from rest_framework.views import APIView

from .cache import inventory_cache_key
from .models import Inventory
from .serializers import InventorySerializer


class StoreInventoryAPIView(APIView):

    def get(self, request, store_id):

        # -----------------------------
        # 1. Check Redis
        # -----------------------------

        cache_key = inventory_cache_key(
            store_id
        )

        cached_data = cache.get(
            cache_key
        )

        if cached_data is not None:

            return Response(
                cached_data
            )

        # -----------------------------
        # 2. Query database
        # -----------------------------

        inventory = (
            Inventory.objects
            .filter(
                store_id=store_id
            )
            .select_related(
                "product",
                "product__category"
            )
            .order_by(
                "product__title"
            )
        )

        # -----------------------------
        # 3. Serialize
        # -----------------------------

        serializer = InventorySerializer(
            inventory,
            many=True
        )

        data = serializer.data

        # -----------------------------
        # 4. Store in Redis
        # -----------------------------

        cache.set(
            cache_key,
            data,
            timeout=300
        )

        return Response(data)