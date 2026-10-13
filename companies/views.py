from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, TemplateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from core.mixins import HRyUpAdminRequiredMixin as AdminRequiredMixin, HRyUpStaffRequiredMixin as StaffRequiredMixin
from .models import Company, SubscriptionPackage, Subscription
from .forms import CompanyForm, SubscriptionPackageForm, SubscriptionForm
from django.contrib.auth import get_user_model
from django.contrib import messages

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
    Context: company, subscription, employees_count, managers
    """
    model = Company
    template_name = 'companies/company_detail.html'
    context_object_name = 'company'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subscription'] = self.object.active_subscription
        context['employees_count'] = self.object.employee_count
        context['managers'] = User.objects.filter(
            role='CLIENT_MANAGER',
            employee_profile__company=self.object,
            employee_profile__is_deleted=False
        )
        return context

class CompanyCreateView(StaffRequiredMixin, CreateView):
    """
    Admin and Staff.
    Template: companies/company_form.html
    Context: form
    """
    model = Company
    form_class = CompanyForm
    template_name = 'companies/company_form.html'
    
    def get_success_url(self):
        return reverse_lazy('companies:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.is_active = True
        response = super().form_valid(form)
        company = self.object
        
        # If created by staff, automatically assign them to this company
        if self.request.user.role == 'HRYUP_STAFF':
            from accounts.models import StaffAssignment
            StaffAssignment.objects.get_or_create(
                staff=self.request.user,
                company=company,
                defaults={'is_primary': True}
            )

        manager_email = form.cleaned_data.get('manager_email')
        if manager_email:
            first_name = form.cleaned_data.get('manager_first_name')
            last_name = form.cleaned_data.get('manager_last_name')
            phone = form.cleaned_data.get('manager_phone') or ''
            password = form.cleaned_data.get('manager_password') or 'password123!'
            
            user = User.objects.create_user(
                email=manager_email,
                first_name=first_name,
                last_name=last_name,
                role='CLIENT_MANAGER',
                phone=phone,
                password=password
            )
            
            from employees.models import Employee
            import datetime
            Employee.objects.create(
                user=user,
                company=company,
                department='Management',
                position='Manager',
                hire_date=datetime.date.today(),
                status=Employee.StatusChoices.ACTIVE
            )
            messages.success(self.request, f"Company '{company.name}' and Client Manager account for {user.get_full_name()} ({user.email}) created successfully!")
        else:
            messages.success(self.request, f"Company '{company.name}' created successfully! You can create a Client Manager account below at any time.")
            
        return response

class CompanyUpdateView(StaffRequiredMixin, UpdateView):
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

class CompanyDeleteView(AdminRequiredMixin, DeleteView):
    """
    Admin only.
    Template: companies/company_confirm_delete.html
    """
    model = Company
    template_name = 'companies/company_confirm_delete.html'
    success_url = reverse_lazy('companies:company_list')
    
    def form_valid(self, form):
        from django.contrib import messages
        from django.http import HttpResponseRedirect
        company = self.get_object()
        
        company.delete()
        
        messages.success(self.request, f"Company '{company.name}' was successfully deleted.")
        return HttpResponseRedirect(self.success_url)

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

from accounts.models import StaffAssignment
from .forms import StaffAssignmentForm
from django.shortcuts import redirect

class StaffAssignmentView(AdminRequiredMixin, TemplateView):
    """
    Admin only.
    Template: companies/staff_assignment.html
    Context: company, assignments, form
    """
    template_name = 'companies/staff_assignment.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = get_object_or_404(Company, pk=self.kwargs['company_id'])
        context['company'] = company
        context['assignments'] = company.staff_assignments.select_related('staff').all()
        if 'form' not in context:
            context['form'] = StaffAssignmentForm()
        return context

    def post(self, request, *args, **kwargs):
        company = get_object_or_404(Company, pk=self.kwargs['company_id'])
        
        # Handle remove assignment
        if 'remove_assignment' in request.POST:
            assignment_id = request.POST.get('remove_assignment')
            StaffAssignment.objects.filter(id=assignment_id, company=company).delete()
            messages.success(request, "Staff assignment removed.")
            return redirect('companies:staff_assignment', company_id=company.pk)
            
        # Handle add assignment
        form = StaffAssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.company = company
            
            # Check if already assigned
            if StaffAssignment.objects.filter(staff=assignment.staff, company=company).exists():
                messages.error(request, f"{assignment.staff.get_full_name()} is already assigned to this company.")
            else:
                assignment.save()
                messages.success(request, f"{assignment.staff.get_full_name()} assigned successfully.")
                
            return redirect('companies:staff_assignment', company_id=company.pk)
            
        return self.render_to_response(self.get_context_data(form=form))


class CompanyToggleStatusView(AdminRequiredMixin, View):
    def post(self, request, pk):
        company = get_object_or_404(Company, pk=pk)
        company.is_active = not company.is_active
        company.save(update_fields=['is_active'])
        status_str = "activated" if company.is_active else "deactivated"
        messages.success(request, f"Company '{company.name}' was successfully {status_str}.")
        return redirect('companies:company_detail', pk=company.pk)
