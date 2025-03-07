# orders/tests/test_models.py
import pytest
from orders.models import Order


@pytest.mark.django_db
def test_create_order():
    """Тест создания заказа"""
    order = Order.objects.create(table_number=1, status="в ожидании")
    assert order.table_number == 1
    assert order.status == "в ожидании"
    assert (
        order.total_price == 0
    )  # Проверяем, что начальная цена 0 (если у вас есть логика расчета цены)
