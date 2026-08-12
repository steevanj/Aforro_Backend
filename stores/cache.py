from django.core.cache import cache


def inventory_cache_key(store_id):
    return f"store_inventory:{store_id}"


def invalidate_inventory_cache(store_id):
    cache.delete(
        inventory_cache_key(store_id)
    )