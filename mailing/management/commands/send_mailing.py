from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from mailing.models import Mailing
from django.utils import timezone

class Command(BaseCommand):
    help = 'Отправка рассылки по ID'

    def add_arguments(self, parser):
        parser.add_argument('mailing_id', type=int)

    def handle(self, *args, **kwargs):
        mailing_id = kwargs['mailing_id']
        try:
            mailing = Mailing.objects.get(pk=mailing_id)
        except Mailing.DoesNotExist:
            self.stdout.write(self.style.ERROR('Рассылка не найдена.'))
            return

        if mailing.status == 'Завершена':
            self.stdout.write(self.style.ERROR('Рассылка уже завершена.'))
            return

        for client in mailing.recipients.all():
            send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body,
                from_email='noreply@example.com',
                recipient_list=[client.email],
                fail_silently=False,
            )

        mailing.status = 'Запущена'
        mailing.save()

        self.stdout.write(self.style.SUCCESS('Рассылка отправлена успешно.'))
