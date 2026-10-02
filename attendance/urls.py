from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('', views.attendance_dashboard, name='dashboard'),
    path('toggle/', views.toggle_attendance, name='toggle'),
    path('list/', views.attendance_list, name='list'),
    path('summary/', views.monthly_summary, name='summary'),
    path('qr-scanner/', views.qr_scanner, name='qr_scanner'),
    path('qr-process-scan/', views.qr_process_scan, name='qr_process_scan'),
]
