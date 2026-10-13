from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import StaffAssignment

User = get_user_model()


class AccountsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            password='password123'
        )
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            first_name='Staff',
            last_name='User',
            role='HRYUP_STAFF',
            password='password123'
        )
        self.client_user = User.objects.create_user(
            email='client@example.com',
            first_name='Client',
            last_name='Manager',
            role='CLIENT_MANAGER',
            password='password123'
        )

    def test_create_user(self):
        user = User.objects.create_user(
            email='newuser@example.com',
            first_name='New',
            last_name='User',
            role='CLIENT_EMPLOYEE',
            password='password123'
        )
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            email='newadmin@example.com',
            first_name='New',
            last_name='Admin',
            password='password123'
        )
        self.assertEqual(user.email, 'newadmin@example.com')
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_email_login(self):
        # Use force_login to bypass axes backend requirement for request object
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)

    def test_role_properties(self):
        self.assertTrue(self.admin_user.is_hryup_admin)
        self.assertTrue(self.staff_user.is_hryup_staff)
        self.assertTrue(self.client_user.is_client_manager)
        self.assertFalse(self.client_user.is_client_employee)

    def test_admin_access_user_list(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(response.status_code, 200)

    def test_non_admin_cannot_access_user_list(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(response.status_code, 403)

    def test_profile_requires_login(self):
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_profile_access_when_logged_in(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)

    def test_staff_assignment_creation(self):
        from companies.models import Company
        self.assertEqual(StaffAssignment._meta.get_field('staff').remote_field.model, User)
        self.assertEqual(StaffAssignment._meta.get_field('company').remote_field.model, Company)

    def test_user_company_property(self):
        from companies.models import Company
        from employees.models import Employee
        import datetime
        company = Company.objects.create(name='Test Company')
        emp_user = User.objects.create_user(
            email='emp@testcompany.com',
            first_name='Emp',
            last_name='Loyee',
            role='CLIENT_EMPLOYEE',
            password='password123'
        )
        Employee.objects.create(
            user=emp_user,
            company=company,
            department='General',
            position='Employee',
            hire_date=datetime.date.today()
        )
        self.assertEqual(emp_user.company, company)

    def test_employee_public_signup(self):
        from companies.models import Company
        company = Company.objects.create(name='Acme Corp')
        response = self.client.post(reverse('accounts:signup'), {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane.doe@acme.com',
            'phone': '09123456789',
            'company': company.pk,
            'position': 'Cashier',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })
        self.assertEqual(response.status_code, 302)
        created_user = User.objects.filter(email='jane.doe@acme.com').first()
        self.assertIsNotNone(created_user)
        self.assertEqual(created_user.role, 'CLIENT_EMPLOYEE')
        self.assertTrue(hasattr(created_user, 'employee_profile'))
        self.assertEqual(created_user.employee_profile.company, company)
        self.assertEqual(created_user.employee_profile.position, 'Cashier')

    def test_admin_can_create_client_manager(self):
        from companies.models import Company
        company = Company.objects.create(name='Beta Tech')
        self.client.force_login(self.admin_user)
        response = self.client.post(reverse('accounts:user_create'), {
            'first_name': 'Manager',
            'last_name': 'Boss',
            'email': 'boss@betatech.com',
            'phone': '09987654321',
            'role': 'CLIENT_MANAGER',
            'company': company.pk,
            'custom_password': 'CustomPass123!',
        })
        self.assertEqual(response.status_code, 302)
        mgr = User.objects.filter(email='boss@betatech.com').first()
        self.assertIsNotNone(mgr)
        self.assertEqual(mgr.role, 'CLIENT_MANAGER')
        self.assertTrue(hasattr(mgr, 'employee_profile'))
        self.assertEqual(mgr.employee_profile.company, company)
        self.assertEqual(mgr.employee_profile.position, 'Manager')
        self.assertTrue(mgr.check_password('CustomPass123!'))

    def test_non_admin_cannot_access_user_create(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('accounts:user_create'))
        self.assertEqual(response.status_code, 403)
