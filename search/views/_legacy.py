from django.db.models import (
    Q,
    Case,
    When,
    Value,
    IntegerField,
    Subquery,
    OuterRef,
)

from rest_framework.response import Response
from rest_framework.views import APIView

from products.models import Product
from stores.models import Inventory

from .pagination import ProductSearchPagination
from .serializers import ProductSearchSerializer
from django.core.cache import cache


class ProductSearchAPIView(APIView):

    def get(self, request):

        queryset = (
            Product.objects
            .select_related("category")
        )

        # --------------------------------
        # Keyword search
        # --------------------------------

        q = request.query_params.get(
            "q",
            ""
        ).strip()

        if q:

            queryset = queryset.filter(
                Q(title__icontains=q)
                |
                Q(description__icontains=q)
                |
                Q(category__name__icontains=q)
            )

        # --------------------------------
        # Category filter
        # --------------------------------

        category = request.query_params.get(
            "category"
        )

        if category:

            queryset = queryset.filter(
                category_id=category
            )

        # --------------------------------
        # Minimum price
        # --------------------------------

        min_price = request.query_params.get(
            "min_price"
        )

        if min_price:

            queryset = queryset.filter(
                price__gte=min_price
            )

        # --------------------------------
        # Maximum price
        # --------------------------------

        max_price = request.query_params.get(
            "max_price"
        )

        if max_price:

            queryset = queryset.filter(
                price__lte=max_price
            )

        # --------------------------------
        # Store inventory
        # --------------------------------

        store_id = request.query_params.get(
            "store_id"
        )

        if store_id:

            inventory_subquery = (
                Inventory.objects
                .filter(
                    store_id=store_id,
                    product_id=OuterRef("pk")
                )
                .values("quantity")[:1]
            )

            queryset = queryset.annotate(
                inventory_quantity=Subquery(
                    inventory_subquery
                )
            )

            # ----------------------------
            # In-stock filter
            # ----------------------------

            in_stock = request.query_params.get(
                "in_stock"
            )

            if in_stock == "true":

                queryset = queryset.filter(
                    inventory_quantity__gt=0
                )

            elif in_stock == "false":

                queryset = queryset.filter(
                    Q(inventory_quantity=0)
                    |
                    Q(
                        inventory_quantity__isnull=True
                    )
                )

        # --------------------------------
        # Sorting
        # --------------------------------

        sort = request.query_params.get(
            "sort",
            "relevance"
        )

        if sort == "price":

            queryset = queryset.order_by(
                "price",
                "id"
            )

        elif sort == "newest":

            queryset = queryset.order_by(
                "-created_at",
                "-id"
            )

        elif sort == "relevance" and q:

            queryset = queryset.annotate(

                relevance=Case(

                    When(
                        title__istartswith=q,
                        then=Value(3)
                    ),

                    When(
                        title__icontains=q,
                        then=Value(2)
                    ),

                    When(
                        description__icontains=q,
                        then=Value(1)
                    ),

                    default=Value(0),

                    output_field=IntegerField()
                )

            ).order_by(
                "-relevance",
                "-created_at"
            )

        else:

            queryset = queryset.order_by(
                "-created_at"
            )

        # --------------------------------
        # Pagination
        # --------------------------------

        paginator = ProductSearchPagination()

        page = paginator.paginate_queryset(
            queryset,
            request
        )

        serializer = ProductSearchSerializer(
            page,
            many=True
        )

        return paginator.get_paginated_response(
            serializer.data
        )

class ProductSuggestAPIView(APIView):

    def get(self, request):

        q = request.query_params.get(
            "q",
            ""
        ).strip().lower()

        # --------------------------------
        # Minimum 3 characters
        # --------------------------------

        if len(q) < 3:

            return Response({
                "results": []
            })

        # --------------------------------
        # Redis cache
        # --------------------------------

        cache_key = (
            f"product_suggest:{q}"
        )

        cached_results = cache.get(
            cache_key
        )

        if cached_results is not None:

            return Response({
                "results": cached_results
            })

        # --------------------------------
        # Database query
        # --------------------------------

        products = (
            Product.objects
            .filter(
                title__icontains=q
            )
            .annotate(

                match_priority=Case(

                    When(
                        title__istartswith=q,
                        then=Value(0)
                    ),

                    default=Value(1),

                    output_field=IntegerField()
                )

            )
            .order_by(
                "match_priority",
                "title"
            )
            .values_list(
                "title",
                flat=True
            )[:10]
        )

        results = list(products)

        # --------------------------------
        # Cache result
        # --------------------------------

        cache.set(
            cache_key,
            results,
            timeout=600
        )

        return Response({
            "results": results
        })