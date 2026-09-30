from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from core.mixins import CompanyAccessMixin, TenantQuerySetMixin
from employees.models import Employee
from .models import EmployeeOnboarding, PolicyDocument, PolicyAcknowledgment

class TrackerListView(CompanyAccessMixin, TenantQuerySetMixin, ListView):
    model = EmployeeOnboarding
    template_name = 'onboarding/tracker_list.html'
    context_object_name = 'trackers'

class PolicyListView(CompanyAccessMixin, TenantQuerySetMixin, ListView):
    model = PolicyDocument
    template_name = 'onboarding/policy_list.html'
    context_object_name = 'policies'

class PolicyAcknowledgeView(CompanyAccessMixin, CreateView):
    model = PolicyAcknowledgment
    template_name = 'onboarding/policy_acknowledge.html'
    fields = []
    
    def get_document(self):
        return get_object_or_404(PolicyDocument, id=self.kwargs.get('pk'), company=self.get_company())

    def form_valid(self, form):
        document = self.get_document()
        employee = get_object_or_404(Employee, user=self.request.user, company=self.get_company())
        
        # Check if already acknowledged
        if PolicyAcknowledgment.objects.filter(employee=employee, document=document).exists():
            return redirect('onboarding:policy_list')

        form.instance.document = document
        form.instance.employee = employee
        form.instance.company = self.get_company()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['document'] = self.get_document()
        return context

    def get_success_url(self):
        return reverse_lazy('onboarding:policy_list')
