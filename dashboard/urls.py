from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardIndexView.as_view(), name='index'),
    path('client/<int:company_id>/', views.ClientDashboardView.as_view(), name='client_dashboard'),
]
