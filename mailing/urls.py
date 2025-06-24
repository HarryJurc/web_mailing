from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('clients/', views.client_list, name='client_list'),
    path('clients/create/', views.client_create, name='client_create'),
    path('clients/<int:pk>/detail/', views.client_detail, name='client_detail'),
    path('clients/<int:pk>/edit/', views.client_update, name='client_update'),
    path('clients/<int:pk>/delete/', views.client_delete, name='client_delete'),
    path('messages/', views.message_list, name='message_list'),
    path('messages/create/', views.message_create, name='message_create'),
    path('messages/<int:pk>/detail/', views.message_detail, name='message_detail'),
    path('messages/<int:pk>/edit/', views.message_update, name='message_update'),
    path('messages/<int:pk>/delete/', views.message_delete, name='message_delete'),
    path('mailings/', views.mailing_list, name='mailing_list'),
    path('mailings/create/', views.mailing_create, name='mailing_create'),
    path('mailings/<int:pk>/edit/', views.mailing_update, name='mailing_update'),
    path('mailings/<int:pk>/delete/', views.mailing_delete, name='mailing_delete'),
    path('mailings/<int:pk>/send/', views.send_mailing, name='send_mailing'),
    path('stats/', views.mailing_stats_view, name='stats'),
]
