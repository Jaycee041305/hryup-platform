from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from core.mixins import HRyUpAdminRequiredMixin as AdminRequiredMixin, HRyUpStaffRequiredMixin as StaffRequiredMixin
from .models import Company, SubscriptionPackage, Subscription
from .forms import CompanyForm, SubscriptionPackageForm, SubscriptionForm
from django.contrib.auth import get_user_model

User = get_user_model()

class CompanyListView(StaffRequiredMixin, ListView):
    """
    Admin/Staff only.
    Template: companies/company_list.html
    Context: companies (paginated by 20)
    """
    model = Company
    template_name = 'companies/company_list.html'
    context_object_name = 'companies'
    paginate_by = 20
    
    def get_queryset(self):
        return Company.objects.filter(is_deleted=False)

class CompanyDetailView(StaffRequiredMixin, DetailView):
    """
    Admin/Staff only.
    Template: companies/company_detail.html
    Context: company, subscription, employees_count
    """
    model = Company
    template_name = 'companies/company_detail.html'
    context_object_name = 'company'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subscription'] = self.object.active_subscription
        context['employees_count'] = self.object.employee_count
        return context

class CompanyCreateView(AdminRequiredMixin, CreateView):
    """
    Admin only.
    Template: companies/company_form.html
    Context: form
    """
    model = Company
    form_class = CompanyForm
    template_name = 'companies/company_form.html'
    success_url = reverse_lazy('companies:list')

class CompanyUpdateView(AdminRequiredMixin, UpdateView):
    """
    Admin only.
    Template: companies/company_form.html
    Context: form, company
    """
    model = Company
    form_class = CompanyForm
    template_name = 'companies/company_form.html'
    context_object_name = 'company'
    
    def get_success_url(self):
        return reverse_lazy('companies:detail', kwargs={'pk': self.object.pk})

class PackageListView(AdminRequiredMixin, ListView):
    """
    Admin only.
    Template: companies/package_list.html
    Context: packages
    """
    model = SubscriptionPackage
    template_name = 'companies/package_list.html'
    context_object_name = 'packages'

class PackageCreateView(AdminRequiredMixin, CreateView):
    """
    Admin only.
    Template: companies/package_form.html
    Context: form
    """
    model = SubscriptionPackage
    form_class = SubscriptionPackageForm
    template_name = 'companies/package_form.html'
    success_url = reverse_lazy('companies:package_list')

class PackageUpdateView(AdminRequiredMixin, UpdateView):
    """
    Admin only.
    Template: companies/package_form.html
    Context: form, package
    """
    model = SubscriptionPackage
    form_class = SubscriptionPackageForm
    template_name = 'companies/package_form.html'
    context_object_name = 'package'
    success_url = reverse_lazy('companies:package_list')

class SubscriptionCreateView(AdminRequiredMixin, CreateView):
    """
    Admin only.
    Template: companies/subscription_form.html
    Context: form, company
    """
    model = Subscription
    form_class = SubscriptionForm
    template_name = 'companies/subscription_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['company'] = get_object_or_404(Company, pk=self.kwargs['company_id'])
        return context
        
    def form_valid(self, form):
        form.instance.company = get_object_or_404(Company, pk=self.kwargs['company_id'])
        return super().form_valid(form)
        
    def get_success_url(self):
        return reverse_lazy('companies:detail', kwargs={'pk': self.kwargs['company_id']})

class StaffAssignmentView(AdminRequiredMixin, TemplateView):
    """
    Admin only.
    Template: companies/staff_assignment.html
    Context: company, assignments, available_staff
    """
    template_name = 'companies/staff_assignment.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = get_object_or_404(Company, pk=self.kwargs['company_id'])
        context['company'] = company
        context['assignments'] = []
        context['available_staff'] = User.objects.filter(is_staff=True)
        return context
