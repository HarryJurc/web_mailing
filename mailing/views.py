from django.shortcuts import render, redirect, get_object_or_404
from .models import Client
from .forms import ClientForm

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
