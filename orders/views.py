from typing import Optional, Dict, Any
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, QuerySet
from .models import Order
from .forms import OrderForm
from rest_framework import generics
from .serializers import OrderSerializer


def parse_items(items_str: str) -> list:
    """Парсинг строки с блюдами в список словарей."""
    try:
        return [
            {"name": item.split("-")[0].strip(), "price": item.split("-")[1].strip()}
            for item in items_str.split(",")
        ]
    except:
        return []


def order_list(request: HttpRequest) -> HttpResponse:
    """Вывод списка заказов с поиском, фильтрацией и парсингом блюд."""
    query: str = request.GET.get("q", "").strip()
    status_filter: str = request.GET.get("status", "").strip()

    orders: QuerySet[Order] = Order.objects.all()

    if query:
        if query.isdigit():
            orders = orders.filter(table_number=int(query))
        else:
            orders = orders.filter(status__icontains=query)

    if status_filter:
        orders = orders.filter(status=status_filter)

    # Парсинг блюд для корректного отображения
    for order in orders:
        order.items_parsed = parse_items(order.items)

    return render(
        request,
        "orders/order_list.html",
        {"orders": orders, "query": query, "status_filter": status_filter},
    )


def order_create(request: HttpRequest) -> HttpResponse:
    """Создание нового заказа с автоматическим расчетом стоимости."""
    if request.method == "POST":
        form: OrderForm = OrderForm(request.POST)
        if form.is_valid():
            order: Order = form.save(commit=False)
            order.save()
            return redirect("order_list")
    else:
        form = OrderForm()
    return render(request, "orders/order_form.html", {"form": form})


def order_detail(request: HttpRequest, order_id: int) -> HttpResponse:
    """Детали конкретного заказа."""
    order: Order = get_object_or_404(Order, id=order_id)
    order.items_parsed = parse_items(order.items)
    return render(request, "orders/order_detail.html", {"order": order})


def order_edit(request: HttpRequest, order_id: int) -> HttpResponse:
    """Редактирование заказа с пересчетом стоимости."""
    order: Order = get_object_or_404(Order, id=order_id)
    if request.method == "POST":
        form: OrderForm = OrderForm(request.POST, instance=order)
        if form.is_valid():
            order = form.save(commit=False)
            order.save()
            return redirect("order_list")
    else:
        form = OrderForm(instance=order)
    return render(request, "orders/order_form.html", {"form": form, "order": order})


def order_delete(request: HttpRequest, order_id: int) -> HttpResponse:
    """Удаление заказа."""
    order: Order = get_object_or_404(Order, id=order_id)
    order.delete()
    return redirect("order_list")


def update_status(request: HttpRequest, order_id: int) -> HttpResponse:
    """Обновление статуса заказа."""
    order: Order = get_object_or_404(Order, id=order_id)
    if request.method == "POST":
        new_status: Optional[str] = request.POST.get("status")
        if new_status in ["в ожидании", "готово", "оплачено"]:
            order.status = new_status
            order.save()
    return redirect("order_list")


def revenue_report(request: HttpRequest) -> HttpResponse:
    """Подсчет общей выручки за оплаченные заказы."""
    total_revenue: Optional[float] = (
        Order.objects.filter(status="оплачено").aggregate(Sum("total_price"))[
            "total_price__sum"
        ]
        or 0
    )
    return render(
        request, "orders/revenue_report.html", {"total_revenue": total_revenue}
    )


# REST API-контроллеры с аннотацией
class OrderListCreateAPIView(generics.ListCreateAPIView):
    """API для получения списка заказов и создания нового заказа."""

    queryset: QuerySet[Order] = Order.objects.all()
    serializer_class = OrderSerializer


class OrderDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """API для получения, обновления и удаления конкретного заказа."""

    queryset: QuerySet[Order] = Order.objects.all()
    serializer_class = OrderSerializer
