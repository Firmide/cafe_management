from django import forms
from orders.models import Order, OrderItem, Item


class StaffOrderForm(forms.ModelForm):
    """Форма для создания/редактирования заказа сотрудниками"""
    
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
        table_number = self.cleaned_data.get("table_number")
        if table_number <= 0:
            raise forms.ValidationError("Номер стола должен быть больше 0!")
        
        busy_tables_str = self.data.get('busy_tables', '')
        if busy_tables_str:
            busy_tables = [int(x) for x in busy_tables_str.split(',') if x.strip()]
        else:
            busy_tables = []
        
        if not self.instance.pk:
            if table_number in busy_tables:
                raise forms.ValidationError(
                    f'Стол {table_number} уже занят! Выберите другой стол.'
                )
        else:
            current_order_busy = Order.objects.filter(
                status__in=['в ожидании', 'готово']
            ).exclude(id=self.instance.pk).values_list('table_number', flat=True)
            
            if table_number in current_order_busy:
                raise forms.ValidationError(
                    f'Стол {table_number} уже занят другим заказом!'
                )
        
        return table_number


class StaffOrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ["item", "quantity"]
        widgets = {
            "item": forms.Select(attrs={"class": "form-control item-select"}),
            "quantity": forms.NumberInput(attrs={
                "class": "form-control quantity-input",
                "min": 1,
                "value": 1
            }),
        }


# Formset для создания нового заказа (с 4 пустыми строками)
StaffOrderItemCreateFormSet = forms.inlineformset_factory(
    Order, OrderItem, form=StaffOrderItemForm,
    extra=3,  # Было 4, стало 3 - всего будет 4 строки (1 существующая + 3 пустых)
    can_delete=True, 
    min_num=1, 
    validate_min=True, 
    max_num=20
)

# Formset для редактирования заказа (без пустых строк)
StaffOrderItemEditFormSet = forms.inlineformset_factory(
    Order, OrderItem, form=StaffOrderItemForm,
    extra=0, can_delete=True, min_num=0, validate_min=False, max_num=20
)


class MenuItemForm(forms.ModelForm):
    """Форма для редактирования меню"""
    class Meta:
        model = Item
        fields = ['name', 'description', 'price', 'category', 'is_available']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }