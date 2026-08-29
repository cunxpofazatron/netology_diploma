import os
from celery import Celery

# Задаем настройки Django по умолчанию для Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orders.settings')

app = Celery('orders')

# Читаем настройки Celery из файла settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически находим задачи (tasks.py) в наших приложениях
app.autodiscover_tasks()
