from decimal import Decimal
from datetime import timedelta, datetime
from django.db import transaction
from .models import PayrollPeriod, PayrollEntry
from attendance.models import Attendance
from leave.models import LeaveRequest
from employees.models import Employee

@transaction.atomic
def run_payroll_aggregation(period: PayrollPeriod):
    if period.status == PayrollPeriod.StatusChoices.LOCKED:
        raise ValueError("Cannot run aggregation for a locked period.")

    company = period.company
    employees = Employee.objects.filter(company=company, status=Employee.StatusChoices.ACTIVE)
    
    # Remove old entries for this open period
    PayrollEntry.objects.filter(period=period).delete()
    
    entries_to_create = []
    
    for emp in employees:
        current_date = period.start_date
        total_hours = Decimal('0.00')
        late_hours = Decimal('0.00')
        absent_days = Decimal('0.00')
        
        schedules = list(emp.schedules.filter(is_deleted=False))
        attendances = Attendance.objects.filter(
            employee=emp, 
            date__range=[period.start_date, period.end_date],
            review_status=Attendance.ReviewStatus.APPROVED,
            is_deleted=False
        )
        att_dict = {a.date: a for a in attendances}
        
        leaves = LeaveRequest.objects.filter(
            employee=emp,
            status=LeaveRequest.StatusChoices.APPROVED,
            is_deleted=False,
            start_date__lte=period.end_date,
            end_date__gte=period.start_date
        )
        leave_dates = set()
        for lv in leaves:
            l_curr = max(lv.start_date, period.start_date)
            l_end = min(lv.end_date, period.end_date)
            while l_curr <= l_end:
                leave_dates.add(l_curr)
                l_curr += timedelta(days=1)
                
        approved_leave_days = Decimal(str(len(leave_dates)))

        while current_date <= period.end_date:
            day_abbr = current_date.strftime("%a")
            sch = next((s for s in schedules if day_abbr in s.days_of_week), None)
            att = att_dict.get(current_date)
            
            if att and att.time_in and att.time_out:
                dt_in = datetime.combine(current_date, att.time_in)
                dt_out = datetime.combine(current_date, att.time_out)
                if dt_out < dt_in:
                    dt_out += timedelta(days=1)
                
                duration = (dt_out - dt_in).total_seconds() / 3600
                total_hours += Decimal(str(round(duration, 2)))
                
                if sch:
                    sch_in = datetime.combine(current_date, sch.start_time)
                    if dt_in > sch_in:
                        late = (dt_in - sch_in).total_seconds() / 3600
                        late_hours += Decimal(str(round(late, 2)))
            else:
                if sch and current_date not in leave_dates:
                    absent_days += Decimal('1.00')
            
            current_date += timedelta(days=1)
            
        entry = PayrollEntry(
            company=company,
            period=period,
            employee=emp,
            total_hours=total_hours,
            late_hours=late_hours,
            absent_days=absent_days,
            approved_leave_days=approved_leave_days,
            basic_rate=Decimal('0.00'),
            allowances=Decimal('0.00'),
            deductions=Decimal('0.00'),
            net_compiled_pay=Decimal('0.00')
        )
        entries_to_create.append(entry)
        
    PayrollEntry.objects.bulk_create(entries_to_create)
