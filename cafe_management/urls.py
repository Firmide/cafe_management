from django.contrib import admin
from django.urls import path, include
from orders import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("orders/", include("orders.urls")),  # Подключаем маршруты приложения orders
    path("api/", include("orders.api_urls")),  # Подключаем API
    path(
        "", views.order_list, name="home"
    ),  # Главная страница будет отображать список заказов
]
