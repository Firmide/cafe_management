from django.urls import path
from . import views

app_name = 'customer'

urlpatterns = [
    path('', views.menu_view, name='menu'),
    path('cart/', views.cart_page, name='cart_page'),
    path('order/new/', views.order_create, name='order_create'),
    path('order/<int:order_id>/', views.order_status, name='order_status'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('api/add-to-cart/', views.api_add_to_cart, name='api_add_to_cart'),
    path('api/order/<int:order_id>/', views.get_order_details, name='get_order_details'),
]