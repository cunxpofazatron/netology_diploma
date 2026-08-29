from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

@shared_task
def send_email_task(subject, message, to_email):
    """
    Фоновая задача для отправки email.
    В режиме разработки письма будут выводиться в консоль.
    """
    msg = EmailMultiAlternatives(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email]
    )
    msg.send()
    return f"Письмо успешно отправлено на {to_email}"
