from django.contrib import admin
from django.utils.html import format_html  # Добавь этот импорт
from .models import Order, Item, OrderItem, OrderHistory

class OrderHistoryInline(admin.TabularInline):
    """Инлайн для отображения истории в админке"""
    model = OrderHistory
    extra = 0
    readonly_fields = ['status', 'changed_at', 'comment']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

class OrderItemInline(admin.TabularInline):
    """Инлайн для отображения позиций заказа"""
    model = OrderItem
    extra = 1

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_available', 'image_preview')  # Добавили image_preview
    list_filter = ('category', 'is_available')
    search_fields = ('name', 'description')
    list_editable = ('price', 'is_available')
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'price', 'image')  # Добавили поле image
        }),
        ('Категория и доступность', {
            'fields': ('category', 'is_available')
        }),
    )
    
    def image_preview(self, obj):
        """Превью картинки в админке"""
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; width: auto; border-radius: 4px;" />', obj.image.url)
        return "—"
    image_preview.short_description = "Фото"

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'item', 'quantity', 'total_price')
    list_filter = ('order__status', 'item__category')
    search_fields = ('order__id', 'item__name')
    raw_id_fields = ('order', 'item')
    
    def total_price(self, obj):
        return f"{obj.total_price} ₽"
    total_price.short_description = "Стоимость"

@admin.register(OrderHistory)
class OrderHistoryAdmin(admin.ModelAdmin):
    list_display = ('order', 'get_status_display', 'changed_at', 'changed_by')
    list_filter = ('status', 'changed_at')
    search_fields = ('order__id', 'comment')
    readonly_fields = ['order', 'status', 'changed_at', 'comment', 'changed_by']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'table_number', 'display_total', 'status', 'created_at', 'paid_at')
    list_filter = ('status', 'created_at', 'paid_at')
    search_fields = ('table_number', 'order_items__item__name')
    readonly_fields = ('created_at', 'updated_at', 'paid_at', 'display_total')
    inlines = [OrderItemInline, OrderHistoryInline]
    list_editable = ('status',)
    list_per_page = 20
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('table_number', 'status')
        }),
        ('Финансы', {
            'fields': ('display_total',)
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at', 'paid_at'),
            'classes': ('collapse',)
        }),
        ('Старый формат (только для обратной совместимости)', {
            'fields': ('items',),
            'classes': ('collapse',)
        }),
    )
    
    def display_total(self, obj):
        """Отображение общей суммы"""
        return f"{obj.total_price} ₽"
    display_total.short_description = 'Общая сумма'
    display_total.admin_order_field = 'total_price'
    
    def save_model(self, request, obj, form, change):
        """Передаем информацию о том, кто изменил заказ"""
        if change:
            old = Order.objects.get(pk=obj.pk)
            if old.status != obj.status:
                OrderHistory.objects.create(
                    order=obj,
                    status=obj.status,
                    changed_by=request.user.username,
                    comment=f"Статус изменен в админке"
                )
        super().save_model(request, obj, form, change)