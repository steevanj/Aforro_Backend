from django.db.models import Count
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Order
from ..serializers import OrderListSerializer


class StoreOrderListAPIView(APIView):
    def get(self, request, store_id):
        orders = (
            Order.objects.filter(store_id=store_id)
            .annotate(total_items=Count("items"))
            .order_by("-created_at")
        )

        serializer = OrderListSerializer(orders, many=True)
        return Response(serializer.data)
