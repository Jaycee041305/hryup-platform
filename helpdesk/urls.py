from django.urls import path
from . import views

app_name = 'helpdesk'

urlpatterns = [
    path('', views.ticket_list, name='ticket_list'),
    path('submit/', views.ticket_submit, name='ticket_submit'),
    path('<int:pk>/', views.ticket_detail, name='ticket_detail'),
    path('<int:pk>/escalate/', views.ticket_escalate, name='ticket_escalate'),
]
