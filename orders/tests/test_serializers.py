# orders/tests/test_serializers.py
import pytest
from orders.models import Order
from orders.serializers import OrderSerializer


@pytest.mark.django_db
def test_order_serializer():
    """Тест сериализатора для заказа"""
    order = Order.objects.create(table_number=1, status="в ожидании")
    serializer = OrderSerializer(order)

    assert serializer.data["table_number"] == 1
    assert serializer.data["status"] == "в ожидании"
