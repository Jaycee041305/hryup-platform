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
        if period.status == PayrollPeriod.StatusChoices.LOCKED:
            messages.error(request, "Cannot run aggregation for a locked period.")
            return redirect('payroll:period_detail', pk=pk)
        
        try:
            run_payroll_aggregation(period)
            messages.success(request, "Payroll data successfully aggregated.")
        except Exception as e:
            messages.error(request, f"Error running aggregation: {str(e)}")
            
        return redirect('payroll:period_detail', pk=pk)

class LockPeriodView(ClientManagerRequiredMixin, TenantQuerySetMixin, View):
    def post(self, request, pk, *args, **kwargs):
        period = get_object_or_404(PayrollPeriod.objects.for_user(request.user), pk=pk)
        if period.status == PayrollPeriod.StatusChoices.OPEN:
            period.status = PayrollPeriod.StatusChoices.LOCKED
            period.save(update_fields=['status'])
            messages.success(request, "Period locked successfully.")
        else:
            messages.info(request, "Period is already locked.")
            
        return redirect('payroll:period_detail', pk=pk)

class ExportCSVView(ClientManagerRequiredMixin, TenantQuerySetMixin, View):
    def get(self, request, pk, *args, **kwargs):
        period = get_object_or_404(PayrollPeriod.objects.for_user(request.user), pk=pk)
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="payroll_{period.start_date}_{period.end_date}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Employee', 'Department', 'Position', 
            'Total Hours', 'Late Hours', 'Absent Days', 'Approved Leave Days',
            'Basic Rate', 'Allowances', 'Deductions', 'Net Pay'
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
                entry.approved_leave_days,
                entry.basic_rate,
                entry.allowances,
                entry.deductions,
                entry.net_compiled_pay
            ])
            
        return response
