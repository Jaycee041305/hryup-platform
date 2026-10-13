from django.views.generic import ListView, DetailView, CreateView, View
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone

from core.mixins import CompanyAccessMixin, TenantQuerySetMixin, ClientManagerRequiredMixin
from employees.models import Employee
from .models import EmployeeOnboarding, PolicyDocument, PolicyAcknowledgment, EmployeeOnboardingTask
from .forms import AssignOnboardingForm

class TrackerListView(CompanyAccessMixin, TenantQuerySetMixin, ListView):
    model = EmployeeOnboarding
    template_name = 'onboarding/tracker_list.html'
    context_object_name = 'trackers'

    def get_queryset(self):
        user = self.request.user
        if user.role == 'HRYUP_ADMIN':
            qs = EmployeeOnboarding.objects.all().select_related('employee__user', 'company', 'template')
        elif user.role == 'HRYUP_STAFF':
            assigned = user.staff_assignments.values_list('company_id', flat=True)
            if assigned.exists():
                qs = EmployeeOnboarding.objects.filter(company_id__in=assigned).select_related('employee__user', 'company', 'template')
            else:
                qs = EmployeeOnboarding.objects.all().select_related('employee__user', 'company', 'template')
        else:
            # Client manager
            company = self.get_company()
            if not company and hasattr(user, 'employee_profile') and user.employee_profile:
                company = user.employee_profile.company
            if company:
                qs = EmployeeOnboarding.objects.filter(company=company).select_related('employee__user', 'company', 'template')
            else:
                qs = EmployeeOnboarding.objects.none()

        company_id = self.request.GET.get('company')
        if company_id:
            qs = qs.filter(company_id=company_id)
        return qs.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_trackers = list(self.get_queryset())

        # Auto-heal: Ensure any pending Employee has an onboarding tracker
        company = self.get_company()
        if company:
            from .models import OnboardingTemplate
            template = OnboardingTemplate.objects.filter(company=company).first()
            if not template:
                template = OnboardingTemplate.objects.create(title='Employee Application', company=company)
            pending_emps = Employee.objects.filter(company=company, status=Employee.StatusChoices.PENDING_APPROVAL)
            for emp in pending_emps:
                if not EmployeeOnboarding.objects.filter(employee=emp).exists():
                    t = EmployeeOnboarding.objects.create(
                        employee=emp,
                        company=company,
                        template=template,
                        status='pending'
                    )
                    all_trackers.insert(0, t)

        context['pending_applications'] = [
            t for t in all_trackers 
            if t.status == 'pending' or not t.employee.user.is_active or t.employee.status == Employee.StatusChoices.PENDING_APPROVAL
        ]
        context['approved_applications'] = [
            t for t in all_trackers 
            if t.employee.user.is_active and t.status != 'rejected' and t.employee.status == Employee.StatusChoices.ACTIVE
        ]
        context['rejected_applications'] = [
            t for t in all_trackers 
            if t.status == 'rejected' or (t not in context['pending_applications'] and not t.employee.user.is_active)
        ]

        # For template compatibility
        context['pending_trackers'] = context['pending_applications']
        context['active_trackers'] = context['approved_applications']
        context['pending_count'] = len(context['pending_applications'])
        context['approved_count'] = len(context['approved_applications'])
        context['rejected_count'] = len(context['rejected_applications'])
        context['active_count'] = context['approved_count']
        return context

class TrackerDetailView(CompanyAccessMixin, TenantQuerySetMixin, DetailView):
    model = EmployeeOnboarding
    template_name = 'onboarding/tracker_detail.html'
    context_object_name = 'tracker'

class ApproveOnboardingView(ClientManagerRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        user = request.user
        if user.role == 'HRYUP_ADMIN':
            qs = EmployeeOnboarding.objects.all()
        elif user.role == 'HRYUP_STAFF':
            assigned = user.staff_assignments.values_list('company_id', flat=True)
            if assigned.exists():
                qs = EmployeeOnboarding.objects.filter(company_id__in=assigned)
            else:
                qs = EmployeeOnboarding.objects.all()
        else:
            company = user.get_company()
            if not company and hasattr(user, 'employee_profile') and user.employee_profile:
                company = user.employee_profile.company
            qs = EmployeeOnboarding.objects.filter(company=company) if company else EmployeeOnboarding.objects.none()

        tracker = get_object_or_404(qs, pk=pk)
        employee = tracker.employee
        target_user = employee.user
        
        # Activate employee's account so they can log in
        target_user.is_active = True
        target_user.save(update_fields=['is_active'])
        
        # Set employee status to ACTIVE
        employee.status = Employee.StatusChoices.ACTIVE
        employee.save(update_fields=['status'])
        
        # Update tracker status
        tracker.status = 'in_progress'
        tracker.save(update_fields=['status'])
        
        from audit.services import log_action
        log_action(
            user=request.user,
            action='APPROVE',
            description=f"Approved employee application for {target_user.get_full_name()} ({target_user.email})",
            obj=employee,
            request=request
        )
        
        messages.success(
            request, 
            f"Application for {target_user.get_full_name()} ({target_user.email}) has been approved! Their account is now active and they can log into the website."
        )
        
        url = reverse_lazy('onboarding:tracker_list')
        company_param = request.GET.get('company') or request.POST.get('company')
        if company_param:
            return redirect(f"{url}?company={company_param}")
        return redirect(url)

class RejectOnboardingView(ClientManagerRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        user = request.user
        if user.role == 'HRYUP_ADMIN':
            qs = EmployeeOnboarding.objects.all()
        elif user.role == 'HRYUP_STAFF':
            assigned = user.staff_assignments.values_list('company_id', flat=True)
            if assigned.exists():
                qs = EmployeeOnboarding.objects.filter(company_id__in=assigned)
            else:
                qs = EmployeeOnboarding.objects.all()
        else:
            company = user.get_company()
            if not company and hasattr(user, 'employee_profile') and user.employee_profile:
                company = user.employee_profile.company
            qs = EmployeeOnboarding.objects.filter(company=company) if company else EmployeeOnboarding.objects.none()

        tracker = get_object_or_404(qs, pk=pk)
        employee = tracker.employee
        target_user = employee.user
        
        # Deactivate user account
        target_user.is_active = False
        target_user.save(update_fields=['is_active'])
        
        # Set employee status to TERMINATED
        employee.status = Employee.StatusChoices.TERMINATED
        employee.save(update_fields=['status'])
        
        # Update tracker status to rejected
        tracker.status = 'rejected'
        tracker.save(update_fields=['status'])
        
        from audit.services import log_action
        log_action(
            user=request.user,
            action='REJECT',
            description=f"Rejected employee application for {target_user.get_full_name()} ({target_user.email})",
            obj=employee,
            request=request
        )
        
        messages.warning(
            request,
            f"Application for {target_user.get_full_name()} ({target_user.email}) has been rejected. Their account cannot access the website."
        )
        
        url = reverse_lazy('onboarding:tracker_list')
        company_param = request.GET.get('company') or request.POST.get('company')
        if company_param:
            return redirect(f"{url}?company={company_param}")
        return redirect(url)

class ToggleTaskView(CompanyAccessMixin, View):
    def post(self, request, pk, task_id, *args, **kwargs):
        tracker = get_object_or_404(EmployeeOnboarding.objects.for_user(request.user), pk=pk)
        task = get_object_or_404(EmployeeOnboardingTask, pk=task_id, onboarding=tracker)
        
        task.is_completed = not task.is_completed
        task.completed_at = timezone.now() if task.is_completed else None
        task.save()
        
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
