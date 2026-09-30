from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseForbidden
from core.mixins import CompanyAccessMixin, TenantQuerySetMixin
from companies.models import Company
from .models import JobVacancy, Application, ScreeningNote

class VacancyListView(CompanyAccessMixin, TenantQuerySetMixin, ListView):
    model = JobVacancy
    template_name = 'recruitment/vacancy_list.html'
    context_object_name = 'vacancies'

class VacancyCreateView(CompanyAccessMixin, TenantQuerySetMixin, CreateView):
    model = JobVacancy
    template_name = 'recruitment/vacancy_form.html'
    fields = ['title', 'description', 'requirements', 'status']
    success_url = reverse_lazy('recruitment:vacancy_list')

    def form_valid(self, form):
        form.instance.company = self.get_company()
        return super().form_valid(form)

class VacancyUpdateView(CompanyAccessMixin, TenantQuerySetMixin, UpdateView):
    model = JobVacancy
    template_name = 'recruitment/vacancy_form.html'
    fields = ['title', 'description', 'requirements', 'status']
    success_url = reverse_lazy('recruitment:vacancy_list')

class PipelineBoardView(CompanyAccessMixin, TenantQuerySetMixin, ListView):
    model = Application
    template_name = 'recruitment/pipeline_board.html'
    context_object_name = 'applications'

class ShortlistView(CompanyAccessMixin, TenantQuerySetMixin, ListView):
    model = Application
    template_name = 'recruitment/shortlist.html'
    context_object_name = 'applications'

    def get_queryset(self):
        return super().get_queryset().filter(status='shortlisted')

# Public Views
class PublicVacancyListView(ListView):
    model = JobVacancy
    template_name = 'recruitment/public_vacancy_list.html'
    context_object_name = 'vacancies'

    def get_queryset(self):
        company_id = self.kwargs.get('company_id')
        self.company = get_object_or_404(Company, id=company_id)
        return JobVacancy.objects.filter(company=self.company, status='open', is_deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['company'] = self.company
        return context

class PublicApplicationView(CreateView):
    model = Application
    template_name = 'recruitment/public_application_form.html'
    fields = ['applicant_name', 'email', 'phone', 'cv_file', 'privacy_consent']

    def get_vacancy(self):
        company_id = self.kwargs.get('company_id')
        vacancy_id = self.kwargs.get('vacancy_id')
        return get_object_or_404(JobVacancy, id=vacancy_id, company_id=company_id, status='open', is_deleted=False)

    def form_valid(self, form):
        vacancy = self.get_vacancy()
        form.instance.vacancy = vacancy
        form.instance.company = vacancy.company
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vacancy'] = self.get_vacancy()
        return context

    def get_success_url(self):
        return reverse_lazy('recruitment:public_vacancy_list', kwargs={'company_id': self.kwargs.get('company_id')})
