from django.urls import path
from . import views

app_name = 'companies'

urlpatterns = [
    path('', views.CompanyListView.as_view(), name='company_list'),
    path('create/', views.CompanyCreateView.as_view(), name='company_create'),
    path('<int:pk>/', views.CompanyDetailView.as_view(), name='company_detail'),
    path('<int:pk>/edit/', views.CompanyUpdateView.as_view(), name='company_edit'),
    path('packages/', views.PackageListView.as_view(), name='package_list'),
    path('packages/create/', views.PackageCreateView.as_view(), name='package_create'),
    path('packages/<int:pk>/edit/', views.PackageUpdateView.as_view(), name='package_edit'),
    path('<int:company_id>/subscription/create/', views.SubscriptionCreateView.as_view(), name='subscription_create'),
    path('<int:company_id>/staff/', views.StaffAssignmentView.as_view(), name='staff_assignment'),
]
