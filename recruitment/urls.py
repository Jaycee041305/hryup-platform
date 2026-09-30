from django.urls import path
from . import views

app_name = 'recruitment'

urlpatterns = [
    path('vacancies/', views.VacancyListView.as_view(), name='vacancy_list'),
    path('vacancies/create/', views.VacancyCreateView.as_view(), name='vacancy_create'),
    path('vacancies/<int:pk>/edit/', views.VacancyUpdateView.as_view(), name='vacancy_edit'),
    path('pipeline/', views.PipelineBoardView.as_view(), name='pipeline'),
    path('shortlist/', views.ShortlistView.as_view(), name='shortlist'),
    path('public/<int:company_id>/vacancies/', views.PublicVacancyListView.as_view(), name='public_vacancy_list'),
    path('public/<int:company_id>/vacancies/<int:vacancy_id>/apply/', views.PublicApplicationView.as_view(), name='public_apply'),
]
