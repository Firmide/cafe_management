# orders/tests/test_views.py
import pytest
from django.urls import reverse
from orders.models import Order


@pytest.mark.django_db
def test_order_list_view(client):
    """Тест представления для списка заказов"""
    Order.objects.create(table_number=1, status="в ожидании")
    url = reverse("order_list")  # Убедитесь, что у вас есть URL с именем 'order_list'
    response = client.get(url)
    assert response.status_code == 200
    assert (
        "в ожидании" in response.content.decode()
    )  # Проверяем, что статус заказа отобразился на странице
