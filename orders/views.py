from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncDate
from django.contrib import messages
from rest_framework import generics, filters, viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend

from .models import Order, Item, OrderItem, OrderHistory
from .serializers import (
    ItemSerializer, OrderListSerializer, OrderDetailSerializer,
    OrderCreateUpdateSerializer, OrderItemSerializer
)
from .forms import OrderForm, OrderItemCreateFormSet, OrderItemEditFormSet, LegacyOrderForm  # ВАЖНО: добавили оба formset


# ==================== ВЕБ-ИНТЕРФЕЙС (шаблоны) ====================

def dashboard(request):
    """Дашборд со статистикой"""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Статистика за сегодня
    today_orders = Order.objects.filter(created_at__date=today)
    today_stats = {
        'total': today_orders.count(),
        'pending': today_orders.filter(status='в ожидании').count(),
        'ready': today_orders.filter(status='готово').count(),
        'paid': today_orders.filter(status='оплачено').count(),
        'revenue': float(today_orders.filter(status='оплачено').aggregate(Sum('total_price'))['total_price__sum'] or 0),
    }
    
    # Статистика за неделю
    week_orders = Order.objects.filter(created_at__date__gte=week_ago)
    week_revenue = week_orders.filter(status='оплачено').aggregate(Sum('total_price'))['total_price__sum'] or 0
    week_orders_count = week_orders.count()
    
    # Статистика за месяц
    month_orders = Order.objects.filter(created_at__date__gte=month_ago)
    month_revenue = month_orders.filter(status='оплачено').aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    # Популярные блюда за неделю
    popular_items = Item.objects.filter(
        orderitem__order__created_at__date__gte=week_ago,
        orderitem__order__status='оплачено'
    ).annotate(
        total_ordered=Sum('orderitem__quantity')
    ).filter(total_ordered__gt=0).order_by('-total_ordered')[:10]
    
    # Заказы по дням (для графика)
    last_7_days = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_orders = Order.objects.filter(created_at__date=day)
        day_paid = day_orders.filter(status='оплачено')
        last_7_days.append({
            'date': day.strftime('%d.%m'),
            'orders': day_orders.count(),
            'revenue': float(day_paid.aggregate(Sum('total_price'))['total_price__sum'] or 0)
        })
    
    # Статусы заказов
    status_stats = {
        'В ожидании': Order.objects.filter(status='в ожидании').count(),
        'Готово': Order.objects.filter(status='готово').count(),
        'Оплачено': Order.objects.filter(status='оплачено').count(),
    }
    
    # Средний чек
    paid_orders = Order.objects.filter(status='оплачено')
    if paid_orders.exists():
        total_sum = paid_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
        avg_check = total_sum / paid_orders.count()
    else:
        avg_check = 0
    
    # Общая статистика
    total_orders = Order.objects.count()
    total_revenue = Order.objects.filter(status='оплачено').aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_items = Item.objects.count()
    
    # Последние заказы (для отображения в дашборде)
    recent_orders = Order.objects.order_by('-created_at')[:10]
    
    # Средние показатели
    first_order = Order.objects.order_by('created_at').first()
    if first_order:
        days_since_first = (today - first_order.created_at.date()).days or 1
        avg_orders_per_day = round(total_orders / days_since_first, 1)
        avg_revenue_per_day = round(total_revenue / days_since_first, 2)
    else:
        avg_orders_per_day = 0
        avg_revenue_per_day = 0
    
    # Самый популярный стол (по количеству заказов)
    popular_table_data = Order.objects.values('table_number').annotate(
        cnt=Count('id')
    ).order_by('-cnt').first()
    popular_table = popular_table_data['table_number'] if popular_table_data else '—'
    
    context = {
        'today_stats': today_stats,
        'week_revenue': week_revenue,
        'week_orders_count': week_orders_count,
        'month_revenue': month_revenue,
        'popular_items': popular_items,
        'last_7_days': last_7_days,
        'status_stats': status_stats,
        'avg_check': round(avg_check, 2),
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_items': total_items,
        'orders': recent_orders,
        'avg_orders_per_day': avg_orders_per_day,
        'avg_revenue_per_day': avg_revenue_per_day,
        'popular_table': popular_table,
    }
    
    return render(request, 'orders/dashboard.html', context)


def order_list(request):
    """Вывод списка заказов с поиском и фильтрацией"""
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    
    orders = Order.objects.all()
    
    if query:
        if query.isdigit():
            orders = orders.filter(table_number=int(query))
        else:
            orders = orders.filter(
                Q(status__icontains=query) |
                Q(order_items__item__name__icontains=query)
            ).distinct()
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Добавляем отформатированные данные для отображения
    for order in orders:
        order.display_items = order.get_items_display()
    
    context = {
        'orders': orders,
        'query': query,
        'status_filter': status_filter,
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'orders/order_list.html', context)


def order_detail(request, order_id):
    """Детали заказа с историей изменений"""
    order = get_object_or_404(Order, id=order_id)
    order.display_items = order.get_items_display()
    
    # Получаем историю изменений
    history = order.history.all()
    
    return render(request, 'orders/order_detail.html', {
        'order': order,
        'history': history
    })


def order_create(request):
    """Создание нового заказа с выбором блюд из меню и проверкой на занятый стол"""
    # Получаем список занятых столов (с незавершенными заказами)
    busy_tables = Order.objects.filter(
        status__in=['в ожидании', 'готово']
    ).values_list('table_number', flat=True).distinct()
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        # Используем CREATE formset с 4 пустыми строками
        formset = OrderItemCreateFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            # Проверяем, не занят ли стол
            table_number = form.cleaned_data['table_number']
            if table_number in busy_tables:
                form.add_error('table_number', f'Стол {table_number} уже занят! Выберите другой стол или завершите текущий заказ.')
            else:
                order = form.save(commit=False)
                order.save()
                
                # Сохраняем все позиции
                instances = formset.save(commit=False)
                for instance in instances:
                    instance.order = order
                    instance.save()
                
                # Удаляем отмеченные на удаление
                for obj in formset.deleted_objects:
                    obj.delete()
                
                # Обновляем общую стоимость
                order.update_total_price(save=True)
                
                return redirect('order_list')
    else:
        form = OrderForm()
        # Для GET запроса используем CREATE formset с 4 пустыми строками
        formset = OrderItemCreateFormSet(queryset=OrderItem.objects.none())
    
    # Передаем список доступных блюд и занятых столов
    items = Item.objects.filter(is_available=True).order_by('category', 'name')
    
    return render(request, 'orders/order_form.html', {
        'form': form,
        'formset': formset,
        'items': items,
        'title': 'Новый заказ',
        'busy_tables': list(busy_tables),
    })

def order_edit(request, order_id):
    """Редактирование заказа (добавка блюд)"""
    order = get_object_or_404(Order, id=order_id)
    
    # Если заказ оплачен, нельзя редактировать
    if order.status == 'оплачено':
        messages.error(request, 'Нельзя редактировать оплаченный заказ')
        return redirect('order_detail', order_id=order.id)
    
    # Если это старый заказ (с текстовым полем items) и нет позиций в новой структуре
    if order.items and not order.order_items.exists() and request.GET.get('legacy') != '1':
        return render(request, 'orders/order_form.html', {
            'order': order,
            'legacy_order': True
        })
    
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        # Для редактирования используем EDIT formset без пустых строк
        formset = OrderItemEditFormSet(request.POST, instance=order)
        
        if form.is_valid() and formset.is_valid():
            order = form.save()
            formset.save()
            
            # Обновляем общую стоимость
            order.update_total_price(save=True)
            
            return redirect('order_list')
    else:
        form = OrderForm(instance=order)
        # Для GET запроса используем EDIT formset без пустых строк
        formset = OrderItemEditFormSet(instance=order)
    
    # Передаем список доступных блюд для выбора
    items = Item.objects.filter(is_available=True).order_by('category', 'name')
    
    # Список занятых столов (исключая текущий заказ)
    busy_tables = Order.objects.filter(
        status__in=['в ожидании', 'готово']
    ).exclude(id=order.id).values_list('table_number', flat=True).distinct()
    
    return render(request, 'orders/order_form.html', {
        'form': form,
        'formset': formset,
        'items': items,
        'order': order,
        'title': f'Редактирование заказа #{order.id}',
        'busy_tables': list(busy_tables),
    })


def order_delete(request, order_id):
    """Удаление заказа"""
    order = get_object_or_404(Order, id=order_id)
    order.delete()
    return redirect('order_list')


def update_status(request, order_id):
    """Быстрое обновление статуса"""
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
    
    return redirect('order_detail', order_id=order.id)


def menu_view(request):
    """Просмотр меню"""
    categories = []
    for category_code, category_name in Item.CATEGORY_CHOICES:
        items = Item.objects.filter(category=category_code, is_available=True)
        if items.exists():
            categories.append({
                'code': category_code,
                'name': category_name,
                'items': items
            })
    
    return render(request, 'orders/menu.html', {'categories': categories})


# ==================== REST API ====================

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
        """Выбор сериализатора в зависимости от действия"""
        if self.action == 'list':
            return OrderListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return OrderCreateUpdateSerializer
        return OrderDetailSerializer
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Смена статуса заказа"""
        order = self.get_object()
        new_status = request.data.get('status')
        
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            return Response({'status': 'ok', 'new_status': order.status})
        return Response(
            {'error': 'Invalid status'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['get'])
    def today_stats(self, request):
        """Статистика за сегодня"""
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
    """Общая статистика для дашборда (API)"""
    today = timezone.now().date()
    
    # Заказы сегодня
    today_orders = Order.objects.filter(created_at__date=today)
    
    # Популярные блюда сегодня
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