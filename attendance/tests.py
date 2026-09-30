from django.test import TestCase
from django.utils import timezone
from core.models import TenantModel
from companies.models import Company
from accounts.models import User
from employees.models import Employee
from .models import WorkSchedule, Attendance
import datetime

class AttendanceTestCase(TestCase):
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
        self.client.force_login(self.user)

    def test_toggle_attendance(self):
        response = self.client.post('/attendance/toggle/')
        self.assertEqual(response.status_code, 302)
        
        att = Attendance.objects.get(employee=self.employee, date=timezone.localdate())
        self.assertIsNotNone(att.time_in)
        self.assertIsNone(att.time_out)

        # Toggle out
        response = self.client.post('/attendance/toggle/')
        self.assertEqual(response.status_code, 302)
        att.refresh_from_db()
        self.assertIsNotNone(att.time_out)

    def test_attendance_list(self):
        Attendance.objects.create(
            employee=self.employee,
            company=self.company,
            date=timezone.localdate(),
            time_in=datetime.time(9, 0),
            time_out=datetime.time(17, 0)
        )
        response = self.client.get('/attendance/list/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "05:00 PM")
