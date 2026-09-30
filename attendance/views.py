from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from .models import Attendance
from employees.models import Employee

@login_required
def attendance_dashboard(request):
    try:
        employee = request.user.employee_profile
    except Employee.DoesNotExist:
        messages.error(request, "You do not have an employee profile.")
        return redirect('core:landing')

    today = timezone.localdate()
    attendance = Attendance.objects.filter(employee=employee, date=today, is_deleted=False).first()

    context = {
        'employee': employee,
        'today': today,
        'attendance': attendance,
    }
    return render(request, 'attendance/dashboard.html', context)

@login_required
def toggle_attendance(request):
    if request.method == 'POST':
        try:
            employee = request.user.employee_profile
        except Employee.DoesNotExist:
            messages.error(request, "Employee profile not found.")
            return redirect('attendance:dashboard')

        today = timezone.localdate()
        now = timezone.localtime().time()

        attendance, created = Attendance.objects.get_or_create(
            employee=employee,
            date=today,
            is_deleted=False,
            defaults={'company': employee.company, 'time_in': now}
        )

        if not created:
            if not attendance.time_in:
                attendance.time_in = now
                messages.success(request, f"Time in recorded at {now.strftime('%I:%M %p')}.")
            elif not attendance.time_out:
                attendance.time_out = now
                messages.success(request, f"Time out recorded at {now.strftime('%I:%M %p')}.")
            else:
                messages.warning(request, "You have already timed in and out for today.")
            attendance.save()
        else:
            messages.success(request, f"Time in recorded at {now.strftime('%I:%M %p')}.")

    return redirect('attendance:dashboard')

@login_required
def attendance_list(request):
    try:
        employee = request.user.employee_profile
    except Employee.DoesNotExist:
        messages.error(request, "Employee profile not found.")
        return redirect('core:landing')

    attendances = Attendance.objects.filter(employee=employee, is_deleted=False).order_by('-date')
    return render(request, 'attendance/list.html', {'attendances': attendances})

@login_required
def monthly_summary(request):
    try:
        employee = request.user.employee_profile
    except Employee.DoesNotExist:
        messages.error(request, "Employee profile not found.")
        return redirect('core:landing')

    import calendar
    from datetime import datetime

    month = int(request.GET.get('month', timezone.localdate().month))
    year = int(request.GET.get('year', timezone.localdate().year))

    attendances = Attendance.objects.filter(
        employee=employee,
        date__year=year,
        date__month=month,
        is_deleted=False
    )
    
    total_days = attendances.count()

    context = {
        'attendances': attendances,
        'month': month,
        'year': year,
        'total_days': total_days,
    }
    return render(request, 'attendance/monthly_summary.html', context)
