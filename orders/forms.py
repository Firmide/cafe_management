from django import forms
from .models import Order, OrderItem, Item
import re


class OrderForm(forms.ModelForm):
    """Форма для создания/редактирования заказа"""
    
    # Добавляем скрытое поле для передачи списка занятых столов
    busy_tables = forms.CharField(widget=forms.HiddenInput(), required=False)
    
    class Meta:
        model = Order
        fields = ["table_number", "status"]
        widgets = {
            "table_number": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Номер стола",
                "min": 1
            }),
            "status": forms.Select(attrs={
                "class": "form-control"
            }),
        }
        labels = {
            "table_number": "Номер стола",
            "status": "Статус заказа"
        }

    def clean_table_number(self):
        """Проверяем, чтобы номер стола был больше 0 и не был занят"""
        table_number = self.cleaned_data.get("table_number")
        
        if table_number <= 0:
            raise forms.ValidationError("Номер стола должен быть больше 0!")
        
        # Получаем список занятых столов из скрытого поля
        busy_tables_str = self.data.get('busy_tables', '')
        if busy_tables_str:
            busy_tables = [int(x) for x in busy_tables_str.split(',') if x.strip()]
        else:
            busy_tables = []
        
        # Проверяем для нового заказа
        if not self.instance.pk:  # Если это создание нового заказа
            if table_number in busy_tables:
                raise forms.ValidationError(
                    f'Стол {table_number} уже занят! Выберите другой стол или дождитесь освобождения.'
                )
        else:  # Если это редактирование существующего заказа
            # Исключаем текущий заказ из списка занятых
            current_order_busy = Order.objects.filter(
                status__in=['в ожидании', 'готово']
            ).exclude(id=self.instance.pk).values_list('table_number', flat=True)
            
            if table_number in current_order_busy:
                raise forms.ValidationError(
                    f'Стол {table_number} уже занят другим заказом!'
                )
        
        return table_number


class OrderItemForm(forms.ModelForm):
    """Форма для позиции заказа (отдельное блюдо)"""
    
    class Meta:
        model = OrderItem
        fields = ["item", "quantity"]
        widgets = {
            "item": forms.Select(attrs={
                "class": "form-control item-select"
            }),
            "quantity": forms.NumberInput(attrs={
                "class": "form-control quantity-input",
                "min": 1,
                "value": 1
            }),
        }
    
    def clean_quantity(self):
        """Проверяем, чтобы количество было больше 0"""
        quantity = self.cleaned_data.get("quantity")
        if quantity < 1:
            raise forms.ValidationError("Количество должно быть не меньше 1")
        return quantity


# Formset для создания нового заказа (с 4 пустыми строками)
OrderItemCreateFormSet = forms.inlineformset_factory(
    Order, 
    OrderItem, 
    form=OrderItemForm,
    extra=3,  # 4 пустые строки для нового заказа
    can_delete=True,
    min_num=1,
    validate_min=True,
    max_num=20
)

# Formset для редактирования заказа (без пустых строк)
OrderItemEditFormSet = forms.inlineformset_factory(
    Order, 
    OrderItem, 
    form=OrderItemForm,
    extra=0,  # 0 пустых строк при редактировании
    can_delete=True,
    min_num=0,
    validate_min=False,
    max_num=20
)


class LegacyOrderForm(forms.ModelForm):
    """Старая форма для обратной совместимости (если нужно редактировать старые заказы)"""
    
    class Meta:
        model = Order
        fields = ["table_number", "items", "status"]
        widgets = {
            "table_number": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Номер стола"
            }),
            "items": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Введите блюда в формате: хлеб-100, борщ-200 (только для старых заказов)",
            }),
            "status": forms.Select(attrs={
                "class": "form-control"
            }),
        }
        labels = {
            "table_number": "Номер стола",
            "items": "Список блюд (старый формат)",
            "status": "Статус заказа"
        }

    def clean_table_number(self):
        """Проверяем, чтобы номер стола был больше 0."""
        table_number = self.cleaned_data.get("table_number")
        if table_number <= 0:
            raise forms.ValidationError("Номер стола должен быть больше 0!")
        
        # Проверка на занятость стола для старых заказов
        if not self.instance.pk:  # Новый заказ
            busy_tables = Order.objects.filter(
                status__in=['в ожидании', 'готово']
            ).values_list('table_number', flat=True)
            
            if table_number in busy_tables:
                raise forms.ValidationError(
                    f'Стол {table_number} уже занят! Выберите другой стол.'
                )
        else:  # Редактирование
            busy_tables = Order.objects.filter(
                status__in=['в ожидании', 'готово']
            ).exclude(id=self.instance.pk).values_list('table_number', flat=True)
            
            if table_number in busy_tables:
                raise forms.ValidationError(
                    f'Стол {table_number} уже занят другим заказом!'
                )
        
        return table_number

    def clean_items(self):
        """Проверяем, что каждый элемент списка блюд соответствует формату 'название - цена'."""
        items = self.cleaned_data.get("items")
        if not items:
            return items
            
        item_list = items.split(",")
        for item in item_list:
            item = item.strip()
            if item and not re.match(r"^.+\s*-\s*\d+$", item):
                raise forms.ValidationError(
                    f"Неверный формат блюда: {item}. Используйте формат 'Название - Цена'."
                )
        return items