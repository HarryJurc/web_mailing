from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from accounts.models import CustomUser


class Client(models.Model):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    comment = models.TextField(blank=True)
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.full_name} <{self.email}>"


class Message(models.Model):
    subject = models.CharField(max_length=255, verbose_name='Тема письма')
    body = models.TextField(verbose_name='Тело письма')
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='messages')

    def __str__(self):
        return self.subject

class Mailing(models.Model):
    STATUS_CHOICES = [
        ('Создана', 'Создана'),
        ('Запущена', 'Запущена'),
        ('Завершена', 'Завершена'),
    ]
    owner = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='owned_mailings'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='received_mailings'
    )
    start_datetime = models.DateTimeField('Дата и время первой отправки')
    end_datetime = models.DateTimeField('Дата и время окончания отправки')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Создана')
    message = models.ForeignKey('Message', on_delete=models.CASCADE)
    recipients = models.ManyToManyField('Client', related_name='mailings')

    def __str__(self):
        return f"Рассылка #{self.id} - {self.status}"

    def save(self, *args, **kwargs):
        if self.end_datetime < timezone.now():
            self.status = 'Завершена'
        super().save(*args, **kwargs)

class Attempt(models.Model):
    STATUS_CHOICES = [
        ('Успешно', 'Успешно'),
        ('Не успешно', 'Не успешно'),
    ]

    timestamp = models.DateTimeField('Дата и время попытки', default=timezone.now)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES)
    server_response = models.TextField('Ответ почтового сервера')
    mailing = models.ForeignKey('Mailing', on_delete=models.CASCADE, related_name='attempts')
    client = models.ForeignKey('Client', on_delete=models.CASCADE, related_name='attempts')

    def __str__(self):
        return f"Попытка #{self.id} — {self.status} ({self.timestamp:%d.%m.%Y %H:%M})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        cache_key = f'mailing_stats_{self.mailing.owner.id}'
        cache.delete(cache_key)

    def delete(self, *args, **kwargs):
        cache_key = f'mailing_stats_{self.mailing.owner.id}'
        cache.delete(cache_key)
        super().delete(*args, **kwargs)
