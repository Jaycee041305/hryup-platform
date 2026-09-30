from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from core.mixins import CompanyAccessMixin, TenantQuerySetMixin, EmployeeSelfOnlyMixin
from .models import Employee
from django.db.models import Q

class EmployeeListView(CompanyAccessMixin, TenantQuerySetMixin, ListView):
    model = Employee
    template_name = 'employees/employee_list.html'
    context_object_name = 'employees'
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        query = self.request.GET.get('q')
        status = self.request.GET.get('status')
        if query:
            qs = qs.filter(
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(position__icontains=query) |
                Q(department__icontains=query)
            )
        if status:
            qs = qs.filter(status=status)
        return qs

class EmployeeDetailView(CompanyAccessMixin, EmployeeSelfOnlyMixin, TenantQuerySetMixin, DetailView):
    model = Employee
    template_name = 'employees/employee_detail.html'
    context_object_name = 'employee'

class EmployeeCreateView(CompanyAccessMixin, TenantQuerySetMixin, CreateView):
    model = Employee
    template_name = 'employees/employee_form.html'
    fields = ['user', 'department', 'position', 'hire_date', 'status', 'privacy_consent']
    success_url = reverse_lazy('employees:list')

    def form_valid(self, form):
        form.instance.company = self.get_company()
        return super().form_valid(form)

class EmployeeUpdateView(CompanyAccessMixin, TenantQuerySetMixin, UpdateView):
    model = Employee
    template_name = 'employees/employee_form.html'
    fields = ['user', 'department', 'position', 'hire_date', 'status', 'privacy_consent']
    success_url = reverse_lazy('employees:list')
