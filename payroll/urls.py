from django.urls import path
from . import views

app_name = 'payroll'

urlpatterns = [
    path('', views.PayrollPeriodListView.as_view(), name='period_list'),
    path('create/', views.PayrollPeriodCreateView.as_view(), name='period_create'),
    path('<int:pk>/', views.PayrollPeriodDetailView.as_view(), name='period_detail'),
    path('<int:pk>/run/', views.RunAggregationView.as_view(), name='run_aggregation'),
    path('<int:pk>/submit-approval/', views.SubmitForApprovalView.as_view(), name='submit_approval'),
    path('<int:pk>/approve/', views.ApprovePayrollView.as_view(), name='approve'),
    path('<int:pk>/revert/', views.RevertToDraftView.as_view(), name='revert_draft'),
    path('<int:pk>/mark-paid/', views.MarkAsPaidView.as_view(), name='mark_paid'),
    path('<int:pk>/export/', views.ExportCSVView.as_view(), name='export_csv'),
    path('my-payslips/', views.MyPayslipsView.as_view(), name='my_payslips'),
]
