from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from companies.models import Company
from accounts.models import User
from employees.models import Employee
from .models import LeaveType, LeaveBalance, LeaveRequest
import datetime

class LeaveTestCase(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Test Company", is_active=True)
        self.user = User.objects.create_user(email="testuser@example.com", first_name="Test", last_name="User", role="CLIENT_EMPLOYEE", password="password")
        self.employee = Employee.objects.create(
            user=self.user,
            company=self.company,
            department="IT",
            position="Dev",
            hire_date=timezone.localdate()
        )
        
        self.manager_user = User.objects.create_user(email="manager@example.com", first_name="Manager", last_name="User", role="CLIENT_MANAGER", password="password")
        self.manager_employee = Employee.objects.create(
            user=self.manager_user,
            company=self.company,
            department="IT",
            position="Manager",
            hire_date=timezone.localdate()
        )

        self.leave_type = LeaveType.objects.create(company=self.company, name="Sick Leave", default_days=10)
        self.balance = LeaveBalance.objects.create(
            company=self.company,
            employee=self.employee,
            leave_type=self.leave_type,
            remaining_days=5
        )

    def test_overlap_validation(self):
        start = timezone.localdate()
        end = start + datetime.timedelta(days=2)
        req1 = LeaveRequest(
            company=self.company,
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=start,
            end_date=end,
            reason="Sick"
        )
        req1.clean()
        req1.save()

        req2 = LeaveRequest(
            company=self.company,
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=start + datetime.timedelta(days=1),
            end_date=end + datetime.timedelta(days=3),
            reason="Sick again"
        )
        with self.assertRaises(ValidationError):
            req2.clean()

    def test_balance_validation(self):
        start = timezone.localdate()
        end = start + datetime.timedelta(days=6)  # 7 days
        req = LeaveRequest(
            company=self.company,
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=start,
            end_date=end,
            reason="Too long"
        )
        with self.assertRaises(ValidationError):
            req.clean()

    def test_balance_deduction_on_approval(self):
        start = timezone.localdate()
        end = start + datetime.timedelta(days=1)  # 2 days
        req = LeaveRequest.objects.create(
            company=self.company,
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=start,
            end_date=end,
            reason="Sick"
        )
        
        self.assertEqual(self.balance.remaining_days, 5)
        
        # Approve
        self.client.force_login(self.manager_user)
        response = self.client.post(f'/leave/{req.pk}/approve/')
        self.assertEqual(response.status_code, 302)
        
        req.refresh_from_db()
        self.assertEqual(req.status, 'APPROVED')
        
        self.balance.refresh_from_db()
        self.assertEqual(self.balance.remaining_days, 3)

    def test_manager_queue_access(self):
        self.client.force_login(self.user)
        response = self.client.get('/leave/queue/')
        self.assertEqual(response.status_code, 302) # Redirect to landing because no permission

        self.client.force_login(self.manager_user)
        response = self.client.get('/leave/queue/')
        self.assertEqual(response.status_code, 200)
