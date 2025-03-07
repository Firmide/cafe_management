# 📌 Cafe Management API

Этот проект представляет собой систему управления заказами кафе с **REST API**, которое позволяет создавать, редактировать и удалять заказы.

## 🚀 Установка

### 1️⃣ **Клонирование репозитория**
```sh
git clone https://github.com/your-repository/cafe-management.git
cd cafe-management
```

### 2️⃣ **Создание виртуального окружения**
```sh
python -m venv venv
source venv/bin/activate  # Для MacOS/Linux
venv\Scripts\activate  # Для Windows
```

### 3️⃣ **Установка зависимостей**
```sh
pip install -r requirements.txt
```

### 4️⃣ **Применение миграций**
```sh
python manage.py migrate
```

### 5️⃣ **Создание суперпользователя (опционально)**
```sh
python manage.py createsuperuser
```

### 6️⃣ **Запуск сервера**
```sh
python manage.py runserver
```

---

## 📡 API Эндпоинты

| Метод | URL               | Описание |
|-------|------------------|----------|
| GET   | `/api/orders/`   | Получить список заказов |
| POST  | `/api/orders/`   | Создать новый заказ |
| GET   | `/api/orders/1/` | Получить заказ с id=1 |
| PUT   | `/api/orders/1/` | Обновить заказ |
| DELETE | `/api/orders/1/` | Удалить заказ |

---

## 🔧 Технологии
- **Django** – Backend
- **Django REST Framework** – API
- **SQLite** – База данных

## 🛠 Разработчики
- Artur ([ваш GitHub](https://github.com/Firmide))


