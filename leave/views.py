from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import LeaveRequest, LeaveBalance
from .forms import LeaveRequestForm
from employees.models import Employee

def _auto_provision_leave_for_employee(employee):
    """Ensures basic leave types exist for the company and the employee has balances."""
    from .models import LeaveType, LeaveBalance
    company = employee.company
    if not LeaveType.objects.filter(company=company, is_deleted=False).exists():
        LeaveType.objects.create(name="Vacation Leave", default_days=15.0, company=company)
        LeaveType.objects.create(name="Sick Leave", default_days=15.0, company=company)
    
    for leave_type in LeaveType.objects.filter(company=company, is_deleted=False):
        LeaveBalance.objects.get_or_create(
            employee=employee,
            leave_type=leave_type,
            company=company,
            defaults={'remaining_days': leave_type.default_days}
        )

@login_required
def leave_dashboard(request):
    try:
        employee = request.user.employee_profile
    except Employee.DoesNotExist:
        messages.error(request, "Employee profile not found.")
        return redirect('core:landing')

    _auto_provision_leave_for_employee(employee)

    balances = LeaveBalance.objects.filter(employee=employee, is_deleted=False)
    requests = LeaveRequest.objects.filter(employee=employee, is_deleted=False).order_by('-start_date')
    
    return render(request, 'leave/dashboard.html', {'balances': balances, 'requests': requests})

@login_required
def request_leave(request):
    try:
        employee = request.user.employee_profile
    except Employee.DoesNotExist:
        messages.error(request, "Employee profile not found.")
        return redirect('core:landing')

    _auto_provision_leave_for_employee(employee)
    company = employee.company

    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave_request = form.save(commit=False)
            leave_request.employee = employee
            leave_request.company = company
            try:
                leave_request.clean()
                leave_request.save()
                messages.success(request, "Leave request submitted successfully.")
                return redirect('leave:dashboard')
            except ValidationError as e:
                for error in e.messages:
                    messages.error(request, error)
    else:
        form = LeaveRequestForm()

    # Filter leave types for the company (must happen for both GET and POST)
    form.fields['leave_type'].queryset = form.fields['leave_type'].queryset.filter(company=company, is_deleted=False)

    return render(request, 'leave/request_form.html', {'form': form})

@login_required
def manager_queue(request):
    if request.user.role not in ['CLIENT_MANAGER', 'HRYUP_STAFF']:
        messages.error(request, "You do not have permission to view this page.")
        return redirect('core:landing')
    
    if request.user.role == 'CLIENT_MANAGER':
        try:
            company = request.user.employee_profile.company
            requests = LeaveRequest.objects.filter(company=company, status=LeaveRequest.StatusChoices.PENDING, is_deleted=False)
        except Employee.DoesNotExist:
            requests = LeaveRequest.objects.none()
    else:
        requests = LeaveRequest.objects.filter(status=LeaveRequest.StatusChoices.PENDING, is_deleted=False)
        
    return render(request, 'leave/manager_queue.html', {'requests': requests})

@login_required
def approve_leave(request, pk):
    if request.user.role not in ['CLIENT_MANAGER', 'HRYUP_STAFF']:
        messages.error(request, "Permission denied.")
        return redirect('core:landing')

    leave_request = get_object_or_404(LeaveRequest, pk=pk, is_deleted=False)
    if request.method == 'POST':
        leave_request.status = LeaveRequest.StatusChoices.APPROVED
        leave_request.save()
        messages.success(request, f"Leave request for {leave_request.employee} approved.")
    return redirect('leave:manager_queue')

@login_required
def reject_leave(request, pk):
    if request.user.role not in ['CLIENT_MANAGER', 'HRYUP_STAFF']:
        messages.error(request, "Permission denied.")
        return redirect('core:landing')

    leave_request = get_object_or_404(LeaveRequest, pk=pk, is_deleted=False)
    if request.method == 'POST':
        leave_request.status = LeaveRequest.StatusChoices.REJECTED
        leave_request.save()
        messages.success(request, f"Leave request for {leave_request.employee} rejected.")
    return redirect('leave:manager_queue')
