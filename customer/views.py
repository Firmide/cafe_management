from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import json
from orders.models import Item, Order, OrderItem


def menu_view(request):
    """Просмотр меню для клиентов"""
    categories = []
    for category_code, category_name in Item.CATEGORY_CHOICES:
        items = Item.objects.filter(category=category_code, is_available=True)
        if items.exists():
            categories.append({
                'code': category_code,
                'name': category_name,
                'items': items
            })
    
    return render(request, 'customer/menu.html', {'categories': categories})


def order_create(request):
    """Создание заказа клиентом с проверкой на занятый стол"""
    
    # Получаем список занятых столов
    busy_tables = Order.objects.filter(
        status__in=['в ожидании', 'готово']
    ).values_list('table_number', flat=True).distinct()
    
    if request.method == 'POST':
        table_number = request.POST.get('table_number')
        cart_data = request.POST.get('cart_data')
        
        # Проверяем, что номер стола указан
        if not table_number:
            return render(request, 'customer/order_form.html', {
                'error': 'Укажите номер стола',
                'busy_tables': list(busy_tables)
            })
        
        try:
            table_number = int(table_number)
        except ValueError:
            return render(request, 'customer/order_form.html', {
                'error': 'Номер стола должен быть числом',
                'busy_tables': list(busy_tables)
            })
        
        # Проверяем, не занят ли стол
        if table_number in busy_tables:
            return render(request, 'customer/order_form.html', {
                'error': f'Стол {table_number} уже занят. Пожалуйста, выберите другой стол.',
                'busy_tables': list(busy_tables)
            })
        
        # Получаем данные корзины
        try:
            cart_items = json.loads(cart_data)
        except:
            cart_items = []
        
        if not cart_items:
            return redirect('customer:menu')
        
        # Создаем заказ
        order = Order.objects.create(
            table_number=table_number,
            status='в ожидании'
        )
        
        # Добавляем позиции
        for item_data in cart_items:
            try:
                item = Item.objects.get(id=item_data['id'], is_available=True)
                OrderItem.objects.create(
                    order=order,
                    item=item,
                    quantity=item_data.get('quantity', 1)
                )
            except Item.DoesNotExist:
                continue
        
        # Обновляем сумму
        order.update_total_price(save=True)
        
        # Сохраняем номер стола в сессии для истории заказов
        request.session['last_table'] = table_number
        
        # Очищаем корзину
        # Мы очистим на клиенте через JavaScript
        
        return redirect('customer:order_status', order_id=order.id)
    
    # GET запрос - показываем форму со списком занятых столов
    return render(request, 'customer/order_form.html', {
        'busy_tables': list(busy_tables)
    })


def order_status(request, order_id):
    """Просмотр статуса заказа клиентом"""
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'customer/order_status.html', {'order': order})


def my_orders(request):
    """Просмотр истории заказов - теперь через localStorage"""
    return render(request, 'customer/my_orders.html')


def get_order_details(request, order_id):
    """API для получения деталей заказа (для AJAX)"""
    try:
        order = Order.objects.get(id=order_id)
        items = []
        for item in order.order_items.all():
            items.append({
                'name': item.item.name,
                'quantity': item.quantity,
                'price': float(item.item.price),
                'total': float(item.total_price)
            })
        
        return JsonResponse({
            'success': True,
            'order': {
                'id': order.id,
                'table_number': order.table_number,
                'status': order.status,
                'status_display': order.get_status_display(),
                'total_price': float(order.total_price),
                'created_at': order.created_at.strftime('%d.%m.%Y %H:%M'),
                'items': items
            }
        })
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Заказ не найден'}, status=404)


@csrf_exempt
def api_add_to_cart(request):
    """API для добавления в корзину (AJAX)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            quantity = data.get('quantity', 1)
            
            item = Item.objects.get(id=item_id, is_available=True)
            
            return JsonResponse({
                'success': True,
                'item': {
                    'id': item.id,
                    'name': item.name,
                    'price': float(item.price),
                    'quantity': quantity
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)