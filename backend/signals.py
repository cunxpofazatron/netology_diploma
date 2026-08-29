from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import ConfirmEmailToken, Order
from .tasks import send_email_task

@receiver(post_save, sender=ConfirmEmailToken)
def new_user_registered_signal(sender, instance, created, **kwargs):
    """Отправляем токен подтверждения асинхронно через Celery"""
    if created:
        # Метод .delay() отправляет задачу в фоновую очередь Redis
        send_email_task.delay(
            subject=f"Токен подтверждения для {instance.user.email}",
            message=f"Ваш токен для подтверждения регистрации: {instance.key}",
            to_email=instance.user.email
        )

@receiver(post_save, sender=Order)
def update_order_status_signal(sender, instance, created, **kwargs):
    """Отправляем уведомление при изменении статуса заказа"""
    if not created:
        send_email_task.delay(
            subject="Обновление статуса заказа",
            message=f"Статус вашего заказа №{instance.id} изменился на: {instance.state}",
            to_email=instance.user.email
        )
