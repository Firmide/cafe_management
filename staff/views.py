from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from orders.models import Order, Item, OrderItem, OrderHistory
from .forms import (
    StaffOrderForm, StaffOrderItemCreateFormSet, 
    StaffOrderItemEditFormSet, MenuItemForm
)

# Все view для сотрудников требуют авторизации
# @login_required

def staff_login(request):
    """Вход для сотрудников"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('staff:dashboard')
        else:
            return render(request, 'staff/login.html', {'error': 'Неверное имя пользователя или пароль'})
    
    return render(request, 'staff/login.html')


def staff_logout(request):
    """Выход из системы"""
    logout(request)
    return redirect('staff:login')

@login_required(login_url='staff:login')
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
    
    # Последние заказы
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
    
    # Самый популярный стол
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
    
    return render(request, 'staff/dashboard.html', context)


@login_required(login_url='staff:login')
def order_list(request):
    """Список заказов для сотрудников"""
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
    
    for order in orders:
        order.display_items = order.get_items_display()
    
    context = {
        'orders': orders,
        'query': query,
        'status_filter': status_filter,
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'staff/order_list.html', context)


@login_required(login_url='staff:login')
def order_detail(request, order_id):
    """Детали заказа"""
    order = get_object_or_404(Order, id=order_id)
    order.display_items = order.get_items_display()
    history = order.history.all()
    
    return render(request, 'staff/order_detail.html', {
        'order': order,
        'history': history
    })


@login_required(login_url='staff:login')
def order_create(request):
    """Создание нового заказа"""
    busy_tables = Order.objects.filter(
        status__in=['в ожидании', 'готово']
    ).values_list('table_number', flat=True).distinct()
    
    if request.method == 'POST':
        form = StaffOrderForm(request.POST)
        formset = StaffOrderItemCreateFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            table_number = form.cleaned_data['table_number']
            if table_number in busy_tables:
                form.add_error('table_number', f'Стол {table_number} уже занят!')
            else:
                order = form.save(commit=False)
                order.save()
                
                instances = formset.save(commit=False)
                for instance in instances:
                    instance.order = order
                    instance.save()
                
                for obj in formset.deleted_objects:
                    obj.delete()
                
                order.update_total_price(save=True)
                messages.success(request, f'Заказ #{order.id} создан')
                return redirect('staff:order_list')
    else:
        form = StaffOrderForm()
        formset = StaffOrderItemCreateFormSet(queryset=OrderItem.objects.none())
    
    items = Item.objects.filter(is_available=True).order_by('category', 'name')
    
    return render(request, 'staff/order_form.html', {
        'form': form,
        'formset': formset,
        'items': items,
        'title': 'Новый заказ',
        'busy_tables': list(busy_tables),
    })

@login_required(login_url='staff:login')
def order_edit(request, order_id):
    """Редактирование заказа"""
    order = get_object_or_404(Order, id=order_id)
    
    if order.status == 'оплачено':
        messages.error(request, 'Нельзя редактировать оплаченный заказ')
        return redirect('staff:order_detail', order_id=order.id)
    
    if request.method == 'POST':
        form = StaffOrderForm(request.POST, instance=order)
        formset = StaffOrderItemEditFormSet(request.POST, instance=order)
        
        if form.is_valid() and formset.is_valid():
            order = form.save()
            formset.save()
            order.update_total_price(save=True)
            messages.success(request, f'Заказ #{order.id} обновлен')
            return redirect('staff:order_list')
    else:
        form = StaffOrderForm(instance=order)
        formset = StaffOrderItemEditFormSet(instance=order)
    
    items = Item.objects.filter(is_available=True).order_by('category', 'name')
    busy_tables = Order.objects.filter(
        status__in=['в ожидании', 'готово']
    ).exclude(id=order.id).values_list('table_number', flat=True).distinct()
    
    return render(request, 'staff/order_form.html', {
        'form': form,
        'formset': formset,
        'items': items,
        'order': order,
        'title': f'Редактирование заказа #{order.id}',
        'busy_tables': list(busy_tables),
    })


@login_required(login_url='staff:login')
def order_delete(request, order_id):
    """Удаление заказа"""
    order = get_object_or_404(Order, id=order_id)
    order.delete()
    messages.success(request, f'Заказ #{order.id} удален')
    return redirect('staff:order_list')


@login_required(login_url='staff:login')
def update_status(request, order_id):
    """Быстрое обновление статуса"""
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f'Статус заказа #{order.id} изменен')
    
    return redirect('staff:order_detail', order_id=order.id)


@login_required(login_url='staff:login')
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
    
    return render(request, 'staff/menu.html', {'categories': categories})


@login_required(login_url='staff:login')
def menu_edit(request):
    """Редактирование меню"""
    items = Item.objects.all().order_by('category', 'name')
    
    if request.method == 'POST':
        # Обработка массового редактирования
        for item in items:
            form = MenuItemForm(request.POST, instance=item, prefix=f'item_{item.id}')
            if form.is_valid():
                form.save()
        messages.success(request, 'Меню обновлено')
        return redirect('staff:menu_view')
    
    # Создаем формы для каждого элемента
    forms = []
    for item in items:
        forms.append(MenuItemForm(instance=item, prefix=f'item_{item.id}'))
    
    return render(request, 'staff/menu_edit.html', {'forms': forms, 'items': items})