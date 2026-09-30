from decimal import Decimal
from datetime import date, time, timedelta
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from companies.models import Company
from employees.models import Employee
from attendance.models import Attendance, WorkSchedule
from leave.models import LeaveType, LeaveRequest
from .models import PayrollPeriod, PayrollEntry
from .services import run_payroll_aggregation

User = get_user_model()

class PayrollServiceTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Test Co")
        
        self.user = User.objects.create_user(email='emp1@example.com', first_name='emp1', last_name='User', role='CLIENT_EMPLOYEE', password='pw')
        self.employee = Employee.objects.create(
            company=self.company, 
            user=self.user,
            department="IT",
            position="Dev",
            hire_date=date.today(),
            status=Employee.StatusChoices.ACTIVE
        )
        
        WorkSchedule.objects.create(
            company=self.company,
            employee=self.employee,
            days_of_week="Mon,Tue,Wed,Thu,Fri",
            start_time=time(9, 0),
            end_time=time(17, 0)
        )
        
        self.period = PayrollPeriod.objects.create(
            company=self.company,
            start_date=date(2023, 1, 2), # Monday
            end_date=date(2023, 1, 8)    # Sunday
        )
        
    def test_aggregation_with_attendance_and_late(self):
        # Mon: 2023-01-02
        # In at 9:30 (late), Out at 17:00 => 7.5 hours duration, 0.5 hours late
        Attendance.objects.create(
            company=self.company,
            employee=self.employee,
            date=date(2023, 1, 2),
            time_in=time(9, 30),
            time_out=time(17, 0),
            review_status=Attendance.ReviewStatus.APPROVED
        )
        
        run_payroll_aggregation(self.period)
        
        entry = PayrollEntry.objects.get(period=self.period, employee=self.employee)
        self.assertEqual(entry.total_hours, Decimal('7.50'))
        self.assertEqual(entry.late_hours, Decimal('0.50'))
        # Mon attendance, Tue-Fri absent => 4 absent days
        self.assertEqual(entry.absent_days, Decimal('4.00'))

    def test_aggregation_with_leave(self):
        lv_type = LeaveType.objects.create(company=self.company, name="Sick")
        LeaveRequest.objects.create(
            company=self.company,
            employee=self.employee,
            leave_type=lv_type,
            start_date=date(2023, 1, 3),
            end_date=date(2023, 1, 4),
            status=LeaveRequest.StatusChoices.APPROVED
        )
        
        run_payroll_aggregation(self.period)
        entry = PayrollEntry.objects.get(period=self.period, employee=self.employee)
        # 2 days leave
        self.assertEqual(entry.approved_leave_days, Decimal('2.00'))
        # 5 work days - 2 leave = 3 absent
        self.assertEqual(entry.absent_days, Decimal('3.00'))

    def test_locked_period_cannot_aggregate(self):
        self.period.status = PayrollPeriod.StatusChoices.LOCKED
        self.period.save()
        with self.assertRaises(ValueError):
            run_payroll_aggregation(self.period)

class PayrollViewsTests(TestCase):
    def setUp(self):
        self.company1 = Company.objects.create(name="Company 1")
        self.company2 = Company.objects.create(name="Company 2")
        
        self.hr_user1 = User.objects.create_user(email='hr1@example.com', first_name='hr1', last_name='User', role='CLIENT_MANAGER', password='pw')
        self.hr_emp1 = Employee.objects.create(
            company=self.company1, user=self.hr_user1, position="HR", hire_date=date.today()
        )
        
        self.hr_user2 = User.objects.create_user(email='hr2@example.com', first_name='hr2', last_name='User', role='CLIENT_MANAGER', password='pw')
        self.hr_emp2 = Employee.objects.create(
            company=self.company2, user=self.hr_user2, position="HR", hire_date=date.today()
        )
        
        self.emp_user = User.objects.create_user(email='emp@example.com', first_name='emp', last_name='User', role='CLIENT_EMPLOYEE', password='pw')
        self.emp = Employee.objects.create(
            company=self.company1, user=self.emp_user, position="Dev", hire_date=date.today()
        )
        
        self.period1 = PayrollPeriod.objects.create(
            company=self.company1, start_date=date(2023, 1, 1), end_date=date(2023, 1, 15)
        )
        self.period2 = PayrollPeriod.objects.create(
            company=self.company2, start_date=date(2023, 1, 1), end_date=date(2023, 1, 15)
        )
        
    def test_tenant_isolation_list(self):
        self.client.force_login(self.hr_user1)
        response = self.client.get(reverse('payroll:period_list'))
        self.assertEqual(response.status_code, 200)
        periods = response.context['periods']
        self.assertIn(self.period1, periods)
        self.assertNotIn(self.period2, periods)

    def test_role_permission(self):
        self.client.force_login(self.emp_user)
        response = self.client.get(reverse('payroll:period_list'))
        self.assertEqual(response.status_code, 403) # PermissionDenied

    def test_create_period_assigns_tenant(self):
        self.client.force_login(self.hr_user1)
        response = self.client.post(reverse('payroll:period_create'), {
            'start_date': '2023-02-01',
            'end_date': '2023-02-15'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(PayrollPeriod.objects.filter(company=self.company1, start_date='2023-02-01').exists())
