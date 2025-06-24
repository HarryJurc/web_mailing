from django.shortcuts import render, redirect, get_object_or_404

from django.conf import settings
from .models import Client, Message, Mailing, Attempt
from .forms import ClientForm, MessageForm, MailingForm
from django.core.mail import send_mail
from django.contrib import messages
from django.utils import timezone
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST


@never_cache
def home(request):
    cache.delete('home')
    total_mailings = Mailing.objects.count()
    active_mailings = Mailing.objects.filter(status='Запущена').count()
    unique_recipients = Client.objects.values('email').distinct().count()

    context = {
        'total_mailings': total_mailings,
        'active_mailings': active_mailings,
        'unique_recipients': unique_recipients,
    }
    return render(request, 'home.html', context)

def check_edit_permission(request, obj, list_view_name: str, object_type: str = 'объект'):
    user = request.user

    if user != obj.owner and user.role != 'manager':
        messages.error(request, f"Вы не можете редактировать чужой объект: {object_type}.")
        return redirect(list_view_name)

    if user.role == 'manager':
        messages.warning(request, f"Менеджеры не могут редактировать чужие объекты: {object_type}.")
        return redirect(list_view_name)

    return None

@login_required(login_url='accounts:login')
def client_list(request):
    cache_key = f'client_list_{request.user.id}'
    cache.delete(cache_key)
    clients = cache.get(cache_key)
    if clients is None:
        if request.user.role == 'manager':
            clients = list(Client.objects.all())
        else:
            clients = list(Client.objects.filter(owner=request.user))
        cache.set(cache_key, clients, 300)
    return render(request, 'mailing/client_list.html', {'clients': clients})

@login_required(login_url='accounts:login')
def client_create(request):
    form = ClientForm(request.POST or None)
    if form.is_valid():
        client = form.save(commit=False)
        client.owner = request.user
        client.save()
        cache.delete(f'client_list_{request.user.id}')
        return redirect('client_list')
    return render(request, 'mailing/client_form.html', {'form': form})

@login_required(login_url='accounts:login')
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    return render(request, 'mailing/client_detail.html', {'client': client})

@login_required(login_url='accounts:login')
def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk)
    permission_redirect = check_edit_permission(request, client, 'client_list', 'клиент')
    if permission_redirect:
        return permission_redirect

    form = ClientForm(request.POST or None, instance=client)
    if form.is_valid():
        form.save()
        cache.delete(f'client_list_{request.user.id}')
        return redirect('client_list')
    return render(request, 'mailing/client_form.html', {'form': form})

@login_required(login_url='accounts:login')
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    permission_redirect = check_edit_permission(request, client, 'client_list', 'клиент')
    if permission_redirect:
        return permission_redirect

    if request.method == 'POST':
        client.delete()
        cache.delete(f'client_list_{request.user.id}')
        return redirect('client_list')
    return render(request, 'mailing/client_confirm_delete.html', {'client': client})

@never_cache
@vary_on_cookie
@login_required(login_url='accounts:login')
def message_list(request):
    cache.delete(f'message_list_{request.user.id}')
    all_messages = Message.objects.all()
    return render(request, 'mailing/message_list.html', {'messages': all_messages})

@login_required(login_url='accounts:login')
def message_create(request):
    form = MessageForm(request.POST or None)
    if form.is_valid():
        message = form.save(commit=False)
        message.owner = request.user
        message.save()
        cache.delete(f'message_list_{request.user.id}')
        return redirect('message_list')
    return render(request, 'mailing/message_form.html', {'form': form})

@login_required(login_url='accounts:login')
def message_update(request, pk):
    message = get_object_or_404(Message, pk=pk)
    permission_redirect = check_edit_permission(request, message, 'message_list', 'сообщение')
    if permission_redirect:
        return permission_redirect

    form = MessageForm(request.POST or None, instance=message)
    if form.is_valid():
        form.save()
        cache.delete(f'message_list_{request.user.id}')
        return redirect('message_list')
    return render(request, 'mailing/message_form.html', {'form': form})

@login_required(login_url='accounts:login')
def message_delete(request, pk):
    message = get_object_or_404(Message, pk=pk)
    permission_redirect = check_edit_permission(request, message, 'message_list', 'сообщение')
    if permission_redirect:
        return permission_redirect

    if request.method == 'POST':
        message.delete()
        cache.delete(f'message_list_{request.user.id}')
        return redirect('message_list')
    return render(request, 'mailing/message_confirm_delete.html', {'message': message})

@login_required(login_url='accounts:login')
def message_detail(request, pk):
    message = get_object_or_404(Message, pk=pk)
    return render(request, 'mailing/message_detail.html', {'message': message})

@never_cache
@vary_on_cookie
@login_required(login_url='accounts:login')
def mailing_list(request):
    user = request.user
    if user.role == 'manager':
        mailings = Mailing.objects.all()
    else:
        mailings = Mailing.objects.filter(owner=user)
    return render(request, 'mailing/mailing_list.html', {'mailings': mailings})

@login_required(login_url='accounts:login')
def mailing_create(request):
    form = MailingForm(request.POST or None)
    if form.is_valid():
        mailing = form.save(commit=False)
        mailing.owner = request.user
        mailing.save()
        cache.delete(f'mailing_list_{request.user.id}')
        cache.delete('home')
        return redirect('mailing_list')
    return render(request, 'mailing/mailing_form.html', {'form': form})

@login_required(login_url='accounts:login')
def mailing_update(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk)
    permission_redirect = check_edit_permission(request, mailing, 'mailing_list', 'рассылка')
    if permission_redirect:
        return permission_redirect

    form = MailingForm(request.POST or None, instance=mailing)
    if form.is_valid():
        form.save()
        cache.delete(f'mailing_list_{request.user.id}')
        cache.delete('home')
        return redirect('mailing_list')
    return render(request, 'mailing/mailing_form.html', {'form': form})

@login_required(login_url='accounts:login')
def mailing_delete(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk)
    permission_redirect = check_edit_permission(request, mailing, 'mailing_list', 'рассылка')
    if permission_redirect:
        return permission_redirect

    if request.method == 'POST':
        mailing.delete()
        cache.delete(f'mailing_list_{request.user.id}')
        cache.delete('home')
        return redirect('mailing_list')
    return render(request, 'mailing/mailing_confirm_delete.html', {'mailing': mailing})

@login_required(login_url='accounts:login')
def send_mailing(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk)

    if mailing.owner != request.user and request.user.role != 'manager':
        raise PermissionDenied("Вы не можете отправить чужую рассылку.")

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

    cache.delete(f'mailing_list_{request.user.id}')
    cache.delete('home')
    cache.delete(f'mailing_stats_{request.user.id}')

    messages.success(request, "Попытки отправки рассылки завершены.")
    return redirect('mailing_list')

@login_required(login_url='accounts:login')
def mailing_stats_view(request):
    user = request.user
    if user.role == 'manager':
        raise PermissionDenied("Менеджеры не могут просматривать статистику.")

    cache_key = f'mailing_stats_{request.user.id}'
    stats = cache.get(cache_key)

    if stats is None:
        mailings = Mailing.objects.filter(owner=user)
        stats_list = []
        total_success = 0
        total_fail = 0

        for mailing in mailings:
            success_count = Attempt.objects.filter(mailing=mailing, status='Успешно').count()
            fail_count = Attempt.objects.filter(mailing=mailing, status='Не успешно').count()

            stats_list.append({
                'id': mailing.id,
                'status': mailing.status,
                'start_datetime': mailing.start_datetime,
                'end_datetime': mailing.end_datetime,
                'success_count': success_count,
                'fail_count': fail_count,
            })

            total_success += success_count
            total_fail += fail_count

        stats = {
            'stats': stats_list,
            'total_messages_sent': total_success,
            'total_fail': total_fail,
        }
        cache.set(cache_key, stats, 300)

    return render(request, 'mailing/stats.html', stats)

@user_passes_test(lambda u: u.role == 'manager')
def stop_mailing(request, pk):
    mailing = get_object_or_404(Mailing, pk=pk)
    mailing.status = 'Отключена'
    mailing.save()
    cache.delete('home')
    cache.delete(f'mailing_list_{request.user.id}')
    messages.success(request, "Рассылка отключена.")
    return redirect('mailing_list')

User = get_user_model()

@user_passes_test(lambda u: u.role == 'manager')
def user_list(request):
    users = User.objects.all()
    return render(request, 'accounts/user_list.html', {'users': users})

@user_passes_test(lambda u: u.role == 'manager')
def block_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = False
    user.save()
    messages.success(request, f"Пользователь {user.email} заблокирован.")
    return redirect('user_list')
