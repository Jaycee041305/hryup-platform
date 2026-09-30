from django.urls import path
from . import views

app_name = 'templates_lib'

urlpatterns = [
    path('', views.template_list, name='template_list'),
    path('<int:pk>/download/', views.template_download, name='template_download'),
]
