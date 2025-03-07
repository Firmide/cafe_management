from django.urls import path
from . import views

urlpatterns = [
    path("", views.order_list, name="order_list"),  # Список заказов
    path("create/", views.order_create, name="order_create"),  # Создание заказа
    path("<int:order_id>/", views.order_detail, name="order_detail"),  # Детали заказа
    path(
        "<int:order_id>/edit/", views.order_edit, name="order_edit"
    ),  # Редактирование заказа
    path(
        "<int:order_id>/delete/", views.order_delete, name="order_delete"
    ),  # Удаление заказа
    path(
        "<int:order_id>/update_status/", views.update_status, name="update_status"
    ),  # Обновление статуса
    path("revenue/", views.revenue_report, name="revenue_report"),  # Выручка за смену
]
