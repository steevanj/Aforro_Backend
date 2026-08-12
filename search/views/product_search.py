from django.db.models import Case, IntegerField, OuterRef, Q, Subquery, Value, When
from rest_framework.views import APIView

from products.models import Product
from stores.models import Inventory

from ..pagination import ProductSearchPagination
from ..serializers import ProductSearchSerializer


class ProductSearchAPIView(APIView):
    def get(self, request):
        queryset = Product.objects.select_related("category")

        q = request.query_params.get("q", "").strip()
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q)
                | Q(description__icontains=q)
                | Q(category__name__icontains=q)
            )

        category = request.query_params.get("category")
        if category:
            queryset = queryset.filter(category_id=category)

        min_price = request.query_params.get("min_price")
        if min_price:
            queryset = queryset.filter(price__gte=min_price)

        max_price = request.query_params.get("max_price")
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        store_id = request.query_params.get("store_id")
        if store_id:
            inventory_subquery = (
                Inventory.objects.filter(store_id=store_id, product_id=OuterRef("pk"))
                .values("quantity")[:1]
            )
            queryset = queryset.annotate(inventory_quantity=Subquery(inventory_subquery))

            in_stock = request.query_params.get("in_stock")
            if in_stock == "true":
                queryset = queryset.filter(inventory_quantity__gt=0)
            elif in_stock == "false":
                queryset = queryset.filter(Q(inventory_quantity=0) | Q(inventory_quantity__isnull=True))

        sort = request.query_params.get("sort", "relevance")
        if sort == "price":
            queryset = queryset.order_by("price", "id")
        elif sort == "newest":
            queryset = queryset.order_by("-created_at", "-id")
        elif sort == "relevance" and q:
            queryset = queryset.annotate(
                relevance=Case(
                    When(title__istartswith=q, then=Value(3)),
                    When(title__icontains=q, then=Value(2)),
                    When(description__icontains=q, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ).order_by("-relevance", "-created_at")
        else:
            queryset = queryset.order_by("-created_at")

        paginator = ProductSearchPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = ProductSearchSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
