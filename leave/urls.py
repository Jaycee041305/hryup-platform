from django.urls import path
from . import views

app_name = 'leave'

urlpatterns = [
    path('', views.leave_dashboard, name='dashboard'),
    path('request/', views.request_leave, name='request'),
    path('queue/', views.manager_queue, name='manager_queue'),
    path('<int:pk>/approve/', views.approve_leave, name='approve'),
    path('<int:pk>/reject/', views.reject_leave, name='reject'),
]
