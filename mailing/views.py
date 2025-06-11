from django.shortcuts import render, redirect, get_object_or_404

from django.conf import settings
from .models import Client, Message, Mailing, Attempt
from .forms import ClientForm, MessageForm, MailingForm
from django.core.mail import send_mail
from django.contrib import messages
from django.utils import timezone
from django.utils.timezone import now



def home(request):
    total_mailings = Mailing.objects.count()
    active_mailings = Mailing.objects.filter(status='Запущена').count()
    unique_recipients = Client.objects.distinct().count()

    context = {
        'total_mailings': total_mailings,
        'active_mailings': active_mailings,
        'unique_recipients': unique_recipients,
    }
    return render(request, 'home.html', context)


def client_list(request):
    clients = Client.objects.all()
    return render(request, 'mailing/client_list.html', {'clients': clients})

def client_create(request):
    form = ClientForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('client_list')
    return render(request, 'mailing/client_form.html', {'form': form})

def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    return render(request, 'mailing/client_detail.html', {'client': client})

def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk)
    form = ClientForm(request.POST or None, instance=client)
    if form.is_valid():
        form.save()
        return redirect('client_list')
    return render(request, 'mailing/client_form.html', {'form': form})

def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        client.delete()
        return redirect('client_list')
    return render(request, 'mailing/client_confirm_delete.html', {'client': client})

def message_list(request):
    messages = Message.objects.all()
    return render(request, 'mailing/message_list.html', {'messages': messages})

def message_create(request):
    form = MessageForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('message_list')
    return render(request, 'mailing/message_form.html', {'form': form})

def message_update(request, pk):
    message = get_object_or_404(Message, pk=pk)
    form = MessageForm(request.POST or None, instance=message)
    if form.is_valid():
        form.save()
        return redirect('message_list')
    return render(request, 'mailing/message_form.html', {'form': form})

def message_delete(request, pk):
    message = get_object_or_404(Message, pk=pk)
    if request.method == 'POST':
        message.delete()
        return redirect('message_list')
    return render(request, 'mailing/message_confirm_delete.html', {'message': message})

def message_detail(request, pk):
    message = get_object_or_404(Message, pk=pk)
    return render(request, 'mailing/message_detail.html', {'message': message})

def mailing_list(request):
    mailings = Mailing.objects.all()
    return render(request, 'mailing/mailing_list.html', {'mailings': mailings})

def mailing_create(request):
    form = MailingForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('mailing_list')
    return render(request, 'mailing/mailing_form.html', {'form': form})

def mailing_update(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk)
    form = MailingForm(request.POST or None, instance=mailing)
    if form.is_valid():
        form.save()
        return redirect('mailing_list')
    return render(request, 'mailing/mailing_form.html', {'form': form})

def mailing_delete(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk)
    if request.method == 'POST':
        mailing.delete()
        return redirect('mailing_list')
    return render(request, 'mailing/mailing_confirm_delete.html', {'mailing': mailing})

def send_mailing(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk)

    if mailing.status == 'Завершена':
        messages.error(request, "Эта рассылка уже завершена.")
        return redirect('mailing_list')

    if mailing.start_datetime > now():
        messages.warning(request, "Рассылка ещё не началась.")
        return redirect('mailing_list')

    for client in mailing.recipients.all():
        try:
            send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[client.email],
                fail_silently=False,
            )
            Attempt.objects.create(
                mailing=mailing,
                status='Успешно',
                server_response=f"Письмо успешно отправлено на {client.email}"
            )
        except Exception as e:
            Attempt.objects.create(
                mailing=mailing,
                status='Не успешно',
                server_response=str(e)
            )

    if mailing.end_datetime <= now():
        mailing.status = 'Завершена'
    else:
        mailing.status = 'Запущена'
    mailing.save()

    messages.success(request, "Попытки отправки рассылки завершены.")
    return redirect('mailing_list')
