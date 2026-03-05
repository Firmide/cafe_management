from django import forms


class CustomerOrderForm(forms.Form):
    """Простая форма для клиентов - только номер стола"""
    table_number = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Номер вашего стола',
            'min': 1
        }),
        label='Номер стола'
    )