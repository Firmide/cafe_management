from django.db import models
from django.utils import timezone
from decimal import Decimal

class Item(models.Model):
    """Модель для хранения блюд (меню)"""
    CATEGORY_CHOICES = [
        ('закуски', 'Закуски'),
        ('салаты', 'Салаты'),
        ('супы', 'Супы'),
        ('горячее', 'Горячие блюда'),
        ('гарниры', 'Гарниры'),
        ('напитки', 'Напитки'),
        ('десерты', 'Десерты'),
        ('прочее', 'Прочее'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Название блюда", unique=True)
    description = models.TextField(verbose_name="Описание/состав", blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='прочее', verbose_name="Категория")
    is_available = models.BooleanField(default=True, verbose_name="Доступно")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")
    
    class Meta:
        verbose_name = "Блюдо"
        verbose_name_plural = "Меню"
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.price} ₽"


class Order(models.Model):
    """Заказ"""
    STATUS_CHOICES = [
        ("в ожидании", "В ожидании"),
        ("готово", "Готово"),
        ("оплачено", "Оплачено"),
    ]

    table_number = models.IntegerField(verbose_name="Номер стола")
    
    # ВРЕМЕННОЕ ПОЛЕ: для обратной совместимости со старыми заказами
    items = models.TextField(
        verbose_name="Список блюд (старый формат)", 
        blank=True,
        help_text="Только для старых заказов. Новые заказы используют OrderItem"
    )
    
    total_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0, 
        verbose_name="Общая стоимость"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="в ожидании",
        verbose_name="Статус"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлен")
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="Оплачен")

    def __str__(self):
        return f"Заказ #{self.id} (Стол {self.table_number})"

    def update_total_price(self, save=True):
        """Обновляет общую стоимость на основе связанных позиций"""
        if hasattr(self, 'order_items') and self.order_items.exists():
            total = sum(item.total_price for item in self.order_items.all())
        else:
            total = self._parse_old_items_total()
        
        self.total_price = total
        if save:
            self.save(update_fields=['total_price'])
        return total

    def _parse_old_items_total(self):
        """Парсит старый формат items и возвращает сумму"""
        total = Decimal('0')
        if self.items:
            for item in self.items.split(','):
                parts = item.strip().rsplit('-', 1)
                if len(parts) == 2:
                    try:
                        total += Decimal(parts[1].strip())
                    except:
                        pass
        return total

    def get_items_display(self):
        """Возвращает список блюд для отображения"""
        if hasattr(self, 'order_items') and self.order_items.exists():
            return [
                {
                    'name': oi.item.name,
                    'quantity': oi.quantity,
                    'price': oi.item.price,
                    'total': oi.total_price
                }
                for oi in self.order_items.all()
            ]
        else:
            items_list = []
            if self.items:
                for item in self.items.split(','):
                    parts = item.strip().rsplit('-', 1)
                    if len(parts) == 2:
                        items_list.append({
                            'name': parts[0].strip(),
                            'price': Decimal(parts[1].strip()),
                            'quantity': 1,
                            'total': Decimal(parts[1].strip())
                        })
            return items_list

    def save(self, *args, **kwargs):
        """Переопределенный save с логикой для статусов и истории"""
        old_status = None
        if self.pk:  # Существующий заказ
            old = Order.objects.get(pk=self.pk)
            old_status = old.status
            
            # Если статус меняется на оплачено, записываем время
            if old.status != 'оплачено' and self.status == 'оплачено':
                self.paid_at = timezone.now()
        else:  # Новый заказ
            if self.status == 'оплачено':
                self.paid_at = timezone.now()
        
        # Сохраняем заказ
        super().save(*args, **kwargs)
        
        # Если статус изменился, создаем запись в истории
        if old_status and old_status != self.status:
            OrderHistory.objects.create(
                order=self,
                status=self.status,
                comment=f"Статус изменен с '{old_status}' на '{self.status}'"
            )

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']


class OrderItem(models.Model):
    """Состав заказа (связь между заказом и блюдом)"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items', verbose_name="Заказ")
    item = models.ForeignKey(Item, on_delete=models.PROTECT, verbose_name="Блюдо")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    
    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"
    
    @property
    def total_price(self):
        """Стоимость позиции (цена * количество)"""
        return self.item.price * self.quantity
    
    def save(self, *args, **kwargs):
        """Переопределенный save для обновления суммы заказа"""
        super().save(*args, **kwargs)
        # Обновляем общую стоимость заказа
        self.order.update_total_price(save=True)
    
    def delete(self, *args, **kwargs):
        """Переопределенный delete для обновления суммы заказа"""
        order = self.order
        super().delete(*args, **kwargs)
        # Обновляем общую стоимость заказа после удаления
        order.update_total_price(save=True)
    
    def __str__(self):
        return f"{self.item.name} x{self.quantity} = {self.total_price} ₽"


class OrderHistory(models.Model):
    """Модель для истории изменений заказа"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='history', verbose_name="Заказ")
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES, verbose_name="Статус")
    changed_at = models.DateTimeField(auto_now_add=True, verbose_name="Время изменения")
    changed_by = models.CharField(max_length=100, verbose_name="Кто изменил", blank=True, null=True)
    comment = models.TextField(verbose_name="Комментарий", blank=True)
    
    class Meta:
        verbose_name = "История заказа"
        verbose_name_plural = "История заказов"
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"Заказ #{self.order.id} - {self.get_status_display()} ({self.changed_at.strftime('%d.%m.%Y %H:%M')})"