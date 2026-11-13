from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import LeaveRequest, LeaveBalance
from .forms import LeaveRequestForm
from employees.models import Employee

LEAVE_TYPE_CONFIG = [
    {
        'name': 'Vacation Leave',
        'default_days': 15.0,
        'allowance_display': '5-15 days',
        'category': 'Company',
    },
    {
        'name': 'Sick Leave',
        'default_days': 15.0,
        'allowance_display': '5-15 days',
        'category': 'Company',
    },
    {
        'name': 'Birthday Leave',
        'default_days': 1.0,
        'allowance_display': '1 day',
        'category': 'Company',
    },
    {
        'name': 'Paternity Leave',
        'default_days': 7.0,
        'allowance_display': '7 days',
        'category': 'Statutory',
    },
    {
        'name': 'Maternity Leave',
        'default_days': 105.0,
        'allowance_display': '105 days',
        'category': 'Statutory',
    },
    {
        'name': 'Rehabilitation Leave',
        'default_days': 180.0,
        'allowance_display': '6 months',
        'category': 'Statutory',
    },
    {
        'name': 'Bereavement Leave',
        'default_days': 5.0,
        'allowance_display': '3-5 days',
        'category': 'Company',
    },
    {
        'name': 'Solo Parent Leave',
        'default_days': 7.0,
        'allowance_display': '7 days',
        'category': 'Statutory',
    },
    {
        'name': 'Service Incentive Leave',
        'default_days': 5.0,
        'allowance_display': '5 days',
        'category': 'Statutory',
    },
    {
        'name': 'Special Leave for Women (RA 9710)',
        'default_days': 60.0,
        'allowance_display': '2 months',
        'category': 'Statutory',
    },
    {
        'name': 'VAWC Leave (RA 9262)',
        'default_days': 10.0,
        'allowance_display': '10 days',
        'category': 'Statutory',
    },
]

def _auto_provision_leave_for_employee(employee):
    """Ensures all standard leave types exist for the company and the employee has balances."""
    from .models import LeaveType, LeaveBalance
    company = employee.company
    
    for cfg in LEAVE_TYPE_CONFIG:
        leave_type, _ = LeaveType.objects.get_or_create(
            company=company,
            name=cfg['name'],
            defaults={'default_days': cfg['default_days']}
        )
        LeaveBalance.objects.get_or_create(
            employee=employee,
            leave_type=leave_type,
            company=company,
            defaults={'remaining_days': leave_type.default_days}
        )

GROUP_1_NAMES = [
    'Vacation Leave',
    'Sick Leave',
    'Birthday Leave',
    'Paternity Leave',
    'Maternity Leave',
    'Rehabilitation Leave',
]

def format_days_display(days, name=None):
    if name == 'Rehabilitation Leave' and days >= 180:
        return '6 mos'
    if name == 'Special Leave for Women (RA 9710)' and days >= 60:
        return '2 mos'
    int_days = int(days) if days == int(days) else days
    if int_days == 1:
        return '1 day'
    return f"{int_days} days"

def get_employee_leave_summary(employee):
    """
    Returns structured leave credits, leaves taken, and remaining balances for an employee.
    """
    from .models import LeaveType, LeaveBalance, LeaveRequest
    _auto_provision_leave_for_employee(employee)
    
    summary = []
    for cfg in LEAVE_TYPE_CONFIG:
        lt = LeaveType.objects.filter(company=employee.company, name=cfg['name'], is_deleted=False).first()
        if not lt:
            continue
        
        balance = LeaveBalance.objects.filter(employee=employee, leave_type=lt, is_deleted=False).first()
        
        # Calculate leaves taken (sum of duration_days of APPROVED leave requests)
        approved_requests = LeaveRequest.objects.filter(
            employee=employee,
            leave_type=lt,
            status=LeaveRequest.StatusChoices.APPROVED,
            is_deleted=False
        )
        taken_days = sum(req.duration_days for req in approved_requests)
        
        total_days = float(lt.default_days)
        remaining = float(balance.remaining_days) if balance else max(0.0, total_days - taken_days)
        
        group = 1 if cfg['name'] in GROUP_1_NAMES else 2
        
        summary.append({
            'name': cfg['name'],
            'allowance_display': cfg['allowance_display'],
            'category': cfg['category'],
            'group': group,
            'total_days': total_days,
            'taken_days': taken_days,
            'taken_display': format_days_display(taken_days, cfg['name']),
            'remaining_days': remaining,
            'remaining_display': format_days_display(remaining, cfg['name']),
            'leave_type': lt,
        })
    return summary

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
    
    from django.db.models import Case, When, IntegerField, Count
    import json
    
    # Order so PENDING is at the top, then sort by most recently created
    ordering = [
        Case(
            When(status=LeaveRequest.StatusChoices.PENDING, then=0),
            default=1,
            output_field=IntegerField(),
        ),
        '-created_at'
    ]
    
    if request.user.role == 'CLIENT_MANAGER':
        try:
            company = request.user.employee_profile.company
            requests = LeaveRequest.objects.filter(company=company, is_deleted=False).order_by(*ordering)
        except Employee.DoesNotExist:
            requests = LeaveRequest.objects.none()
    else:
        requests = LeaveRequest.objects.filter(is_deleted=False).order_by(*ordering)
        
    # Generate Chart Data: Leave Requests by Employee
    type_counts = requests.values(
        'employee__user__first_name',
        'employee__user__last_name'
    ).annotate(count=Count('id')).order_by('-count')
    
    labels = []
    data_counts = []
    colors = ['#4e73df', '#1cc88a', '#f6c23e', '#e74a3b', '#36b9cc', '#858796', '#5a5c69', '#2e59d9', '#17a673', '#2c9faf']
    bg_colors = []
    
    for idx, item in enumerate(type_counts):
        emp_name = f"{item['employee__user__first_name']} {item['employee__user__last_name']}".strip()
        labels.append(f"{emp_name} ({item['count']})")
        data_counts.append(item['count'])
        bg_colors.append(colors[idx % len(colors)])
        
    chart_data = None
    if data_counts:
        chart_data = json.dumps({
            'labels': labels,
            'data': data_counts,
            'colors': bg_colors
        })
        
    return render(request, 'leave/manager_queue.html', {
        'requests': requests,
        'chart_data': chart_data
    })

@login_required
def approve_leave(request, pk):
    if request.user.role not in ['CLIENT_MANAGER', 'HRYUP_STAFF']:
        messages.error(request, "Permission denied.")
        return redirect('core:landing')

    leave_request = get_object_or_404(LeaveRequest, pk=pk, is_deleted=False)
    if request.method == 'POST':
        if leave_request.status != LeaveRequest.StatusChoices.APPROVED:
            leave_request.status = LeaveRequest.StatusChoices.APPROVED
            leave_request.save()
            balance = LeaveBalance.objects.filter(
                employee=leave_request.employee,
                leave_type=leave_request.leave_type
            ).first()
            if balance:
                balance.remaining_days = max(0, float(balance.remaining_days) - float(leave_request.duration_days))
                balance.save()
        messages.success(request, f"Leave request for {leave_request.employee} approved.")
    return redirect('leave:manager_queue')

@login_required
def reject_leave(request, pk):
    if request.user.role not in ['CLIENT_MANAGER', 'HRYUP_STAFF']:
        messages.error(request, "Permission denied.")
        return redirect('core:landing')

    leave_request = get_object_or_404(LeaveRequest, pk=pk, is_deleted=False)
    if request.method == 'POST':
        if leave_request.status == LeaveRequest.StatusChoices.APPROVED:
            balance = LeaveBalance.objects.filter(
                employee=leave_request.employee,
                leave_type=leave_request.leave_type
            ).first()
            if balance:
                balance.remaining_days = float(balance.remaining_days) + float(leave_request.duration_days)
                balance.save()
        leave_request.status = LeaveRequest.StatusChoices.REJECTED
        leave_request.save()
        messages.success(request, f"Leave request for {leave_request.employee} rejected.")
    return redirect('leave:manager_queue')
