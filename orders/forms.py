from django import forms
from .models import Order
import re


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["table_number", "items", "status"]
        widgets = {
            "items": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Введите блюда в формате: хлеб-100, борщ-200",
                }
            ),
        }

    def clean_table_number(self):
        """Проверяем, чтобы номер стола был больше 0."""
        table_number = self.cleaned_data.get("table_number")
        if table_number <= 0:
            raise forms.ValidationError("Номер стола должен быть больше 0!")
        return table_number

    def clean_items(self):
        """Проверяем, что каждый элемент списка блюд соответствует формату 'название - цена'."""
        items = self.cleaned_data.get("items")
        item_list = items.split(",")

        for item in item_list:
            item = item.strip()
            if not re.match(
                r"^.+\s*-\s*\d+$", item
            ):  # Проверка формата "Название - Цена"
                raise forms.ValidationError(
                    f"Неверный формат блюда: {item}. Используйте формат 'Название - Цена'."
                )

        return items
