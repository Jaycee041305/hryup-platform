from django.urls import path
from . import views

app_name = 'payroll'

urlpatterns = [
    path('', views.PayrollPeriodListView.as_view(), name='period_list'),
    path('create/', views.PayrollPeriodCreateView.as_view(), name='period_create'),
    path('<int:pk>/', views.PayrollPeriodDetailView.as_view(), name='period_detail'),
    path('<int:pk>/run/', views.RunAggregationView.as_view(), name='run_aggregation'),
    path('<int:pk>/lock/', views.LockPeriodView.as_view(), name='lock_period'),
    path('<int:pk>/export/', views.ExportCSVView.as_view(), name='export_csv'),
]
