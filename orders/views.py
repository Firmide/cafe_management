# Этот файл больше не используется. Вся логика перенесена в staff/views.py и customer/views.py
# Оставлен только для обратной совместимости API

from django.shortcuts import render
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Sum

from .models import Order, Item
from .serializers import (
    ItemSerializer, OrderListSerializer, OrderDetailSerializer,
    OrderCreateUpdateSerializer
)


class ItemViewSet(viewsets.ModelViewSet):
    """API для управления меню"""
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_available']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'category']


class OrderViewSet(viewsets.ModelViewSet):
    """API для управления заказами"""
    queryset = Order.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'table_number']
    search_fields = ['table_number', 'order_items__item__name']
    ordering_fields = ['created_at', 'total_price', 'table_number']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return OrderListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return OrderCreateUpdateSerializer
        return OrderDetailSerializer
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            return Response({'status': 'ok', 'new_status': order.status})
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def today_stats(self, request):
        today = timezone.now().date()
        orders_today = Order.objects.filter(created_at__date=today)
        
        stats = {
            'total_orders': orders_today.count(),
            'pending': orders_today.filter(status='в ожидании').count(),
            'ready': orders_today.filter(status='готово').count(),
            'paid': orders_today.filter(status='оплачено').count(),
            'revenue': float(orders_today.filter(status='оплачено')
                           .aggregate(Sum('total_price'))['total_price__sum'] or 0)
        }
        return Response(stats)


@api_view(['GET'])
def dashboard_stats(request):
    today = timezone.now().date()
    today_orders = Order.objects.filter(created_at__date=today)
    
    popular_today = Item.objects.filter(
        orderitem__order__created_at__date=today
    ).annotate(
        ordered_count=Sum('orderitem__quantity')
    ).filter(ordered_count__gt=0).order_by('-ordered_count')[:5]
    
    stats = {
        'today': {
            'orders': today_orders.count(),
            'revenue': float(today_orders.filter(status='оплачено')
                           .aggregate(Sum('total_price'))['total_price__sum'] or 0),
            'pending': today_orders.filter(status='в ожидании').count(),
        },
        'total': {
            'orders': Order.objects.count(),
            'items': Item.objects.count(),
            'revenue': float(Order.objects.filter(status='оплачено')
                           .aggregate(Sum('total_price'))['total_price__sum'] or 0)
        },
        'popular_items': [
            {'name': item.name, 'count': item.ordered_count}
            for item in popular_today
        ]
    }
    return Response(stats)