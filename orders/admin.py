from django.contrib import admin
from .models import Order  # Импорт модели заказов


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "table_number", "total_price", "status")
    search_fields = ("table_number", "status")
    list_filter = ("status",)


# Если есть другие модели, можно их также зарегистрировать
# admin.site.register(AnotherModel)
