from django.db.models import Case, IntegerField, Value, When
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework.views import APIView

from products.models import Product


class ProductSuggestAPIView(APIView):
    def get(self, request):
        q = request.query_params.get("q", "").strip().lower()

        if len(q) < 3:
            return Response({"results": []})

        cache_key = f"product_suggest:{q}"
        cached_results = cache.get(cache_key)
        if cached_results is not None:
            return Response({"results": cached_results})

        products = (
            Product.objects.filter(title__icontains=q)
            .annotate(
                match_priority=Case(
                    When(title__istartswith=q, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField(),
                )
            )
            .order_by("match_priority", "title")
            .values_list("title", flat=True)[:10]
        )

        results = list(products)
        cache.set(cache_key, results, timeout=600)
        return Response({"results": results})
