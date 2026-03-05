from django.urls import path
from . import views

urlpatterns = [
    # Главная и список заказов
    path('', views.order_list, name='order_list'),
    
    # Заказы
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('order/new/', views.order_create, name='order_create'),
    path('order/<int:order_id>/edit/', views.order_edit, name='order_edit'),
    path('order/<int:order_id>/delete/', views.order_delete, name='order_delete'),
    path('order/<int:order_id>/status/', views.update_status, name='update_status'),
    
    # Отчеты и меню
    path('dashboard/', views.dashboard, name='dashboard'),  # Дашборд
    path('menu/', views.menu_view, name='menu_view'),       # Меню
]