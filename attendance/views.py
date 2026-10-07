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
    
    # Check for past days where they timed in but never timed out
    missing_logs = Attendance.objects.filter(
        employee=employee,
        date__lt=today,
        time_out__isnull=True,
        is_deleted=False
    ).order_by('-date')

    context = {
        'employee': employee,
        'today': today,
        'attendance': attendance,
        'missing_logs': missing_logs,
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
    user = request.user
    
    # Base queryset
    qs = Attendance.objects.filter(is_deleted=False)
    
    if user.role == 'CLIENT_EMPLOYEE':
        if not hasattr(user, 'employee_profile'):
            messages.error(request, "Employee profile not found.")
            return redirect('core:landing')
        qs = qs.filter(employee=user.employee_profile)
        
    elif user.role == 'CLIENT_MANAGER':
        if not hasattr(user, 'employee_profile'):
            messages.error(request, "Manager profile not found.")
            return redirect('core:landing')
        qs = qs.filter(company=user.employee_profile.company)
        
    elif user.role == 'HRYUP_STAFF':
        company_id = request.GET.get('company')
        if company_id:
            qs = qs.filter(company_id=company_id, company__staff_assignments__staff=user)
        else:
            assigned_companies = user.staff_assignments.values_list('company_id', flat=True)
            qs = qs.filter(company_id__in=assigned_companies)
            
    elif user.role == 'HRYUP_ADMIN':
        company_id = request.GET.get('company')
        if company_id:
            qs = qs.filter(company_id=company_id)
            
    attendances = qs.order_by('-date', '-time_in')
    return render(request, 'attendance/list.html', {'attendances': attendances})

@login_required
def monthly_summary(request):
    user = request.user
    
    import calendar
    from datetime import datetime

    month = int(request.GET.get('month', timezone.localdate().month))
    year = int(request.GET.get('year', timezone.localdate().year))

    qs = Attendance.objects.filter(
        date__year=year,
        date__month=month,
        is_deleted=False
    )
    
    if user.role == 'CLIENT_EMPLOYEE':
        if not hasattr(user, 'employee_profile'):
            messages.error(request, "Employee profile not found.")
            return redirect('core:landing')
        qs = qs.filter(employee=user.employee_profile)
        
    elif user.role == 'CLIENT_MANAGER':
        if not hasattr(user, 'employee_profile'):
            messages.error(request, "Manager profile not found.")
            return redirect('core:landing')
        qs = qs.filter(company=user.employee_profile.company)
        
    elif user.role == 'HRYUP_STAFF':
        company_id = request.GET.get('company')
        if company_id:
            qs = qs.filter(company_id=company_id, company__staff_assignments__staff=user)
        else:
            assigned_companies = user.staff_assignments.values_list('company_id', flat=True)
            qs = qs.filter(company_id__in=assigned_companies)
            
    elif user.role == 'HRYUP_ADMIN':
        company_id = request.GET.get('company')
        if company_id:
            qs = qs.filter(company_id=company_id)
            
    attendances = qs.order_by('employee', 'date')
    
    total_days = attendances.count()

    context = {
        'attendances': attendances,
        'month': month,
        'year': year,
        'total_days': total_days,
    }
    return render(request, 'attendance/monthly_summary.html', context)

@login_required
def qr_scanner(request):
    """View to act as the Attendance Kiosk/Scanner."""
    if request.user.role not in ['CLIENT_MANAGER', 'HRYUP_ADMIN', 'HRYUP_STAFF', 'CLIENT_EMPLOYEE']:
        messages.error(request, "You don't have permission to access the scanner.")
        return redirect('dashboard:index')
    return render(request, 'attendance/qr_scanner.html')

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@login_required
@csrf_exempt
def qr_process_scan(request):
    """Processes AJAX requests from the QR scanner."""
    if request.method == 'POST':
        if request.user.role not in ['CLIENT_MANAGER', 'HRYUP_ADMIN', 'HRYUP_STAFF', 'CLIENT_EMPLOYEE']:
            return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
            
        try:
            data = json.loads(request.body)
            qr_token = data.get('qr_token')
            
            if not qr_token:
                return JsonResponse({'status': 'error', 'message': 'No QR token provided'})
                
            scanned_employee = Employee.objects.get(qr_token=qr_token)
            
            # Make sure the scanner user is scanning someone from their company
            if request.user.role in ['CLIENT_MANAGER', 'CLIENT_EMPLOYEE']:
                if scanned_employee.company != request.user.employee_profile.company:
                    return JsonResponse({'status': 'error', 'message': 'Employee belongs to a different company'})

            today = timezone.localdate()
            now = timezone.localtime().time()

            attendance, created = Attendance.objects.get_or_create(
                employee=scanned_employee,
                date=today,
                is_deleted=False,
                defaults={'company': scanned_employee.company, 'time_in': now, 'review_status': 'APPROVED'}
            )

            if not created:
                if not attendance.time_in:
                    attendance.time_in = now
                    action = f"Time In recorded for {scanned_employee.user.get_full_name()} at {now.strftime('%I:%M %p')}"
                elif not attendance.time_out:
                    attendance.time_out = now
                    action = f"Time Out recorded for {scanned_employee.user.get_full_name()} at {now.strftime('%I:%M %p')}"
                else:
                    return JsonResponse({'status': 'error', 'message': f"{scanned_employee.user.get_full_name()} has already timed in and out today."})
                attendance.save()
            else:
                action = f"Time In recorded for {scanned_employee.user.get_full_name()} at {now.strftime('%I:%M %p')}"

            return JsonResponse({'status': 'success', 'message': action, 'employee_name': scanned_employee.user.get_full_name()})
            
        except Employee.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid or unrecognized Employee QR code.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
