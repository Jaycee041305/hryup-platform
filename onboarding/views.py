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
        response = super().form_valid(form)
        
        # Auto-create the tasks based on the template
        tasks_to_create = []
        for template_task in form.instance.template.tasks.all():
            tasks_to_create.append(
                EmployeeOnboardingTask(
                    onboarding=form.instance,
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
