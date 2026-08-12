from celery import shared_task


@shared_task
def send_order_confirmation(order_id):

    from .models import Order

    order = (
        Order.objects
        .select_related("store")
        .get(id=order_id)
    )

    print(
        f"Order {order.id} confirmed "
        f"for store {order.store.name}"
    )

    return {
        "order_id": order.id,
        "status": order.status,
    }