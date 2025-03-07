from django.db import models


class Order(models.Model):
    STATUS_CHOICES = [
        ("в ожидании", "В ожидании"),
        ("готово", "Готово"),
        ("оплачено", "Оплачено"),
    ]

    table_number = models.IntegerField(verbose_name="Номер стола")
    items = models.TextField(verbose_name="Список блюд (пример: хлеб-100, борщ-200)")
    total_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Общая стоимость"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="в ожидании",
        verbose_name="Статус заказа",
    )

    def parse_items(self):
        """
        Парсит строку items (блюдо-цена, блюдо-цена) и возвращает список словарей.
        """
        parsed = []
        if self.items:
            for item in self.items.split(","):
                parts = item.strip().rsplit("-", 1)
                if len(parts) == 2:
                    name, price = parts
                    parsed.append({"name": name.strip(), "price": price.strip()})
        return parsed

    @property
    def parsed_items(self):
        return self.parse_items()

    def save(self, *args, **kwargs):
        """Пересчитывает общую стоимость перед сохранением заказа."""
        self.total_price = sum(float(item["price"]) for item in self.parse_items())
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Заказ {self.id} (Стол {self.table_number})"
