from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    # Авторизация
    path('login/', views.staff_login, name='login'),
    path('logout/', views.staff_logout, name='logout'),
    
    # Главная сотрудников
    path('', views.order_list, name='dashboard'),
    
    # Заказы
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/new/', views.order_create, name='order_create'),
    path('orders/<int:order_id>/edit/', views.order_edit, name='order_edit'),
    path('orders/<int:order_id>/delete/', views.order_delete, name='order_delete'),
    path('orders/<int:order_id>/status/', views.update_status, name='update_status'),
    
    # Дашборд и меню
    path('dashboard/', views.dashboard, name='dashboard'),
    path('menu/', views.menu_view, name='menu_view'),
    path('menu/edit/', views.menu_edit, name='menu_edit'),
]