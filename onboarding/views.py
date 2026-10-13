from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from core.mixins import CompanyAccessMixin, TenantQuerySetMixin, ClientManagerRequiredMixin
from employees.models import Employee
from .models import EmployeeOnboarding, PolicyDocument, PolicyAcknowledgment

class TrackerListView(CompanyAccessMixin, TenantQuerySetMixin, ListView):
    model = EmployeeOnboarding
    template_name = 'onboarding/tracker_list.html'
    context_object_name = 'trackers'

    def get_queryset(self):
        qs = super().get_queryset()
        company_id = self.request.GET.get('company')
        if company_id and self.request.user.role in ('HRYUP_ADMIN', 'HRYUP_STAFF'):
            qs = qs.filter(company_id=company_id)
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.get_company()
        if company:
            from .models import OnboardingTemplate, OnboardingTask
            if not OnboardingTemplate.objects.filter(company=company).exists():
                template = OnboardingTemplate.objects.create(title='Standard New Hire Checklist', company=company)
                tasks = [
                    'Submit Government IDs (SSS, PhilHealth, Pag-IBIG, TIN)',
                    'Sign Non-Disclosure Agreement (NDA)',
                    'Read and Acknowledge Employee Handbook',
                    'Setup Company Email and IT Accounts',
                    'Attend HR Orientation'
                ]
                for desc in tasks:
                    OnboardingTask.objects.create(template=template, description=desc, company=company)

        all_trackers = list(context.get('trackers', []))
        context['pending_trackers'] = [t for t in all_trackers if t.status == 'pending' or not t.employee.user.is_active]
        context['active_trackers'] = [t for t in all_trackers if t.status != 'pending' and t.employee.user.is_active]
        context['pending_count'] = len(context['pending_trackers'])
        context['active_count'] = len(context['active_trackers'])
        return context

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

from django.views.generic import View
from django.utils import timezone
from .forms import AssignOnboardingForm
from .models import EmployeeOnboardingTask
from django.contrib import messages

class AssignOnboardingView(CompanyAccessMixin, CreateView):
    model = EmployeeOnboarding
    form_class = AssignOnboardingForm
    template_name = 'onboarding/assign_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.get_company()
        return kwargs
        
    def form_valid(self, form):
        form.instance.company = self.get_company()
        self.object = form.save()
        
        # Auto-create the tasks based on the template
        tasks_to_create = []
        for template_task in self.object.template.tasks.all():
            tasks_to_create.append(
                EmployeeOnboardingTask(
                    onboarding=self.object,
                    task=template_task,
                    company=self.get_company()
                )
            )
        EmployeeOnboardingTask.objects.bulk_create(tasks_to_create)
        
        messages.success(self.request, "Onboarding assigned successfully.")
        
        url = reverse_lazy('onboarding:tracker_list')
        company = self.request.GET.get('company') or self.request.POST.get('company')
        if company:
            return redirect(f"{url}?company={company}")
        return redirect(url)

class TrackerDetailView(CompanyAccessMixin, TenantQuerySetMixin, DetailView):
    model = EmployeeOnboarding
    template_name = 'onboarding/tracker_detail.html'
    context_object_name = 'tracker'
    
    def get_object(self, queryset=None):
        tracker = super().get_object(queryset)
        # Self-healing logic: if tasks weren't created (e.g. due to a crash), create them now
        if not tracker.employee_tasks.exists() and tracker.template.tasks.exists():
            from .models import EmployeeOnboardingTask
            tasks_to_create = []
            for template_task in tracker.template.tasks.all():
                tasks_to_create.append(
                    EmployeeOnboardingTask(
                        onboarding=tracker,
                        task=template_task,
                        company=tracker.company
                    )
                )
            EmployeeOnboardingTask.objects.bulk_create(tasks_to_create)
        return tracker

class ToggleTaskView(CompanyAccessMixin, View):
    def post(self, request, pk, task_id, *args, **kwargs):
        tracker = get_object_or_404(EmployeeOnboarding.objects.for_user(request.user), pk=pk)
        task = get_object_or_404(EmployeeOnboardingTask, pk=task_id, onboarding=tracker)
        
        task.is_completed = not task.is_completed
        task.completed_at = timezone.now() if task.is_completed else None
        task.save()
        
        # Check overall progress
        total_tasks = tracker.employee_tasks.count()
        completed_tasks = tracker.employee_tasks.filter(is_completed=True).count()
        
        if completed_tasks == 0:
            tracker.status = 'pending'
        elif completed_tasks == total_tasks:
            tracker.status = 'completed'
        else:
            tracker.status = 'in_progress'
        tracker.save()
        
        url = reverse_lazy('onboarding:tracker_detail', kwargs={'pk': tracker.pk})
        company = self.request.GET.get('company') or self.request.POST.get('company')
        if company:
            return redirect(f"{url}?company={company}")
        return redirect(url)


class ApproveOnboardingView(ClientManagerRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        tracker = get_object_or_404(EmployeeOnboarding.objects.for_user(request.user), pk=pk)
        employee = tracker.employee
        user = employee.user
        
        # Activate the employee's user account so they can log in
        user.is_active = True
        user.save(update_fields=['is_active'])
        
        # Update employee status
        employee.status = Employee.StatusChoices.ACTIVE
        employee.save(update_fields=['status'])
        
        # Update onboarding tracker status
        tracker.status = 'in_progress'
        tracker.save(update_fields=['status'])
        
        from audit.services import log_action
        log_action(
            user=request.user,
            action='APPROVE',
            description=f"Approved employee onboarding application for {user.get_full_name()} ({user.email})",
            obj=employee,
            request=request
        )
        
        messages.success(
            request, 
            f"Application for {user.get_full_name()} ({user.email}) has been approved! Their account is now active and they can log in."
        )
        
        url = reverse_lazy('onboarding:tracker_list')
        company = request.GET.get('company') or request.POST.get('company')
        if company:
            return redirect(f"{url}?company={company}")
        return redirect(url)


class RejectOnboardingView(ClientManagerRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        tracker = get_object_or_404(EmployeeOnboarding.objects.for_user(request.user), pk=pk)
        employee = tracker.employee
        user = employee.user
        
        user.is_active = False
        user.save(update_fields=['is_active'])
        
        employee.status = Employee.StatusChoices.TERMINATED
        employee.save(update_fields=['status'])
        
        tracker.status = 'rejected'
        tracker.save(update_fields=['status'])
        
        from audit.services import log_action
        log_action(
            user=request.user,
            action='REJECT',
            description=f"Rejected employee onboarding application for {user.get_full_name()} ({user.email})",
            obj=employee,
            request=request
        )
        
        messages.warning(
            request,
            f"Application for {user.get_full_name()} has been rejected."
        )
        
        url = reverse_lazy('onboarding:tracker_list')
        company = request.GET.get('company') or request.POST.get('company')
        if company:
            return redirect(f"{url}?company={company}")
        return redirect(url)
