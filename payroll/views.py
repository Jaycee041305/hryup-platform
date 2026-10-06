from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, View
from django.http import HttpResponse
from .models import PayrollPeriod, PayrollEntry
from .forms import PayrollPeriodForm
from .services import run_payroll_aggregation
from core.mixins import ClientManagerRequiredMixin, TenantQuerySetMixin, CompanyAccessMixin
import csv

class PayrollPeriodListView(ClientManagerRequiredMixin, TenantQuerySetMixin, ListView):
    model = PayrollPeriod
    template_name = 'payroll/payrollperiod_list.html'
    context_object_name = 'periods'

class PayrollPeriodCreateView(ClientManagerRequiredMixin, CompanyAccessMixin, CreateView):
    model = PayrollPeriod
    form_class = PayrollPeriodForm
    template_name = 'payroll/payrollperiod_form.html'
    success_url = reverse_lazy('payroll:period_list')

    def form_valid(self, form):
        company = self.get_company()
        if not company:
            messages.error(self.request, "Company context not found.")
            return self.form_invalid(form)
        form.instance.company = company
        return super().form_valid(form)

    def get_success_url(self):
        company = self.request.GET.get('company') or self.request.POST.get('company')
        url = reverse('payroll:period_list')
        if company:
            return f"{url}?company={company}"
        return url

class PayrollPeriodDetailView(ClientManagerRequiredMixin, TenantQuerySetMixin, DetailView):
    model = PayrollPeriod
    template_name = 'payroll/payrollperiod_detail.html'
    context_object_name = 'period'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entries'] = self.object.entries.select_related('employee__user').all()
        return context

class RunAggregationView(ClientManagerRequiredMixin, TenantQuerySetMixin, View):
    def post(self, request, pk, *args, **kwargs):
        period = get_object_or_404(PayrollPeriod.objects.for_user(request.user), pk=pk)
        
        if request.user.role not in ['HRYUP_STAFF', 'HRYUP_ADMIN']:
            messages.error(request, "Only HRyUp Staff can run payroll aggregation.")
            return redirect('payroll:period_detail', pk=pk)

        if period.status != PayrollPeriod.StatusChoices.DRAFT:
            messages.error(request, "Cannot run aggregation unless the period is in Draft status.")
            return redirect('payroll:period_detail', pk=pk)
        
        try:
            run_payroll_aggregation(period)
            messages.success(request, "Payroll data successfully aggregated.")
        except Exception as e:
            messages.error(request, f"Error running aggregation: {str(e)}")
            
        return redirect('payroll:period_detail', pk=pk)

class SubmitForApprovalView(ClientManagerRequiredMixin, TenantQuerySetMixin, View):
    def post(self, request, pk, *args, **kwargs):
        period = get_object_or_404(PayrollPeriod.objects.for_user(request.user), pk=pk)
        
        if request.user.role not in ['HRYUP_STAFF', 'HRYUP_ADMIN']:
            messages.error(request, "Only HRyUp Staff can submit payroll for approval.")
            return redirect('payroll:period_detail', pk=pk)

        if period.status == PayrollPeriod.StatusChoices.DRAFT:
            period.status = PayrollPeriod.StatusChoices.PENDING_APPROVAL
            period.save(update_fields=['status'])
            messages.success(request, "Payroll submitted to Client Manager for approval.")
        else:
            messages.info(request, "Period is not in Draft status.")
            
        return redirect('payroll:period_detail', pk=pk)

class ApprovePayrollView(ClientManagerRequiredMixin, TenantQuerySetMixin, View):
    def post(self, request, pk, *args, **kwargs):
        period = get_object_or_404(PayrollPeriod.objects.for_user(request.user), pk=pk)
        
        if request.user.role != 'CLIENT_MANAGER':
            messages.error(request, "Only the Client Manager can approve the payroll.")
            return redirect('payroll:period_detail', pk=pk)

        if period.status == PayrollPeriod.StatusChoices.PENDING_APPROVAL:
            period.status = PayrollPeriod.StatusChoices.APPROVED
            period.save(update_fields=['status'])
            messages.success(request, "Payroll approved successfully. You can now disburse funds.")
        else:
            messages.info(request, "Period is not pending approval.")
            
        return redirect('payroll:period_detail', pk=pk)

class MarkAsPaidView(ClientManagerRequiredMixin, TenantQuerySetMixin, View):
    def post(self, request, pk, *args, **kwargs):
        period = get_object_or_404(PayrollPeriod.objects.for_user(request.user), pk=pk)
        
        if request.user.role != 'CLIENT_MANAGER':
            messages.error(request, "Only the Client Manager can mark the payroll as paid.")
            return redirect('payroll:period_detail', pk=pk)

        if period.status == PayrollPeriod.StatusChoices.APPROVED:
            period.status = PayrollPeriod.StatusChoices.PAID
            period.save(update_fields=['status'])
            messages.success(request, "Payroll marked as Paid! Payslips are now available to employees.")
        else:
            messages.info(request, "Period must be Approved before it can be marked as Paid.")
            
        return redirect('payroll:period_detail', pk=pk)

class ExportCSVView(ClientManagerRequiredMixin, TenantQuerySetMixin, View):
    def get(self, request, pk, *args, **kwargs):
        period = get_object_or_404(PayrollPeriod.objects.for_user(request.user), pk=pk)
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="payroll_{period.start_date}_{period.end_date}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Employee', 'Department', 'Position', 
            'Total Hours', 'Late Hours', 'Absent Days', 'Approved Leave Days'
        ])
        
        entries = period.entries.select_related('employee__user').all()
        for entry in entries:
            writer.writerow([
                entry.employee.user.get_full_name(),
                entry.employee.department,
                entry.employee.position,
                entry.total_hours,
                entry.late_hours,
                entry.absent_days,
                entry.approved_leave_days
            ])
            
        return response

class MyPayslipsView(TenantQuerySetMixin, ListView):
    model = PayrollEntry
    template_name = 'payroll/my_payslips.html'
    context_object_name = 'payslips'

    def get_queryset(self):
        # Only show payslips for PAID periods for the logged-in employee
        if not hasattr(self.request.user, 'employee_profile'):
            return PayrollEntry.objects.none()
            
        emp = self.request.user.employee_profile
        return PayrollEntry.objects.filter(
            employee=emp, 
            period__status=PayrollPeriod.StatusChoices.PAID,
            is_deleted=False
        ).order_by('-period__start_date')
