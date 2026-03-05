from rest_framework import serializers
from .models import Order, Item, OrderItem


class ItemSerializer(serializers.ModelSerializer):
    """Сериализатор для блюд"""
    class Meta:
        model = Item
        fields = ['id', 'name', 'description', 'price', 'category', 'is_available']
        read_only_fields = ['id']


class OrderItemSerializer(serializers.ModelSerializer):
    """Сериализатор для позиций заказа"""
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_price = serializers.DecimalField(source='item.price', read_only=True, max_digits=10, decimal_places=2)
    total = serializers.DecimalField(source='total_price', read_only=True, max_digits=10, decimal_places=2)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'item', 'item_name', 'item_price', 'quantity', 'total']
        read_only_fields = ['id']


class OrderListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка заказов (краткая версия)"""
    items_count = serializers.IntegerField(source='order_items.count', read_only=True)
    total = serializers.DecimalField(source='total_price', read_only=True, max_digits=10, decimal_places=2)
    
    class Meta:
        model = Order
        fields = ['id', 'table_number', 'status', 'total', 'items_count', 'created_at']
        read_only_fields = ['id', 'created_at']


class OrderDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детального просмотра заказа"""
    items_list = OrderItemSerializer(source='order_items', many=True, read_only=True)
    items_display = serializers.SerializerMethodField()
    total = serializers.DecimalField(source='total_price', read_only=True, max_digits=10, decimal_places=2)
    time_created = serializers.DateTimeField(source='created_at', read_only=True)
    time_paid = serializers.DateTimeField(source='paid_at', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'table_number', 'status', 'total', 
            'items_list', 'items_display', 
            'time_created', 'time_paid'
        ]
        read_only_fields = ['id', 'time_created']
    
    def get_items_display(self, obj):
        """Возвращает удобное представление блюд для отображения"""
        return obj.get_items_display()


class OrderCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления заказа"""
    items = OrderItemSerializer(source='order_items', many=True, required=False)
    
    class Meta:
        model = Order
        fields = ['id', 'table_number', 'status', 'items']
    
    def create(self, validated_data):
        """Создание заказа вместе с позициями"""
        items_data = validated_data.pop('order_items', [])
        order = Order.objects.create(**validated_data)
        
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        
        # Обновляем общую стоимость
        order.update_total_price()
        return order
    
    def update(self, instance, validated_data):
        """Обновление заказа и его позиций"""
        items_data = validated_data.pop('order_items', None)
        
        # Обновляем поля заказа
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Если есть новые позиции - обновляем
        if items_data is not None:
            # Удаляем старые позиции
            instance.order_items.all().delete()
            # Создаем новые
            for item_data in items_data:
                OrderItem.objects.create(order=instance, **item_data)
            
            # Обновляем общую стоимость
            instance.update_total_price()
        
        return instance