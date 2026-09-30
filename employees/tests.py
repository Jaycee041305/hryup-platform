from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from companies.models import Company
from employees.models import Employee

User = get_user_model()

class EmployeeTenantIsolationTests(TestCase):
    def setUp(self):
        # Create companies
        self.company_a = Company.objects.create(name='Company A')
        self.company_b = Company.objects.create(name='Company B')
        
        # Create admin user for company A
        self.admin_a = User.objects.create_user(password='password', role='HRYUP_STAFF', email='a@test.com', first_name='A', last_name='A')
        self.admin_a.staff_assignments.create(company=self.company_a)
        
        # Create admin user for company B
        self.admin_b = User.objects.create_user(password='password', role='HRYUP_STAFF', email='b@test.com', first_name='B', last_name='B')
        self.admin_b.staff_assignments.create(company=self.company_b)
        
        # Create employee user in Company A
        self.user_emp_a = User.objects.create_user(password='password', role='CLIENT_EMPLOYEE', email='ea@test.com', first_name='EA', last_name='EA')
        self.emp_a = Employee.objects.create(
            company=self.company_a, user=self.user_emp_a, department='IT', position='Dev', hire_date='2020-01-01'
        )
        
        # Create employee user in Company B
        self.user_emp_b = User.objects.create_user(password='password', role='CLIENT_EMPLOYEE', email='eb@test.com', first_name='EB', last_name='EB')
        self.emp_b = Employee.objects.create(
            company=self.company_b, user=self.user_emp_b, department='HR', position='Recruiter', hire_date='2020-02-01'
        )
        
    def test_tenant_isolation_list(self):
        self.client.force_login(self.admin_a)
        session = self.client.session
        session['active_company_id'] = self.company_a.id
        session.save()
        
        response = self.client.get(reverse('employees:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'EA EA')
        self.assertNotContains(response, 'EB EB')
        
        self.client.force_login(self.admin_b)
        session = self.client.session
        session['active_company_id'] = self.company_b.id
        session.save()
        
        response = self.client.get(reverse('employees:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'EB EB')
        self.assertNotContains(response, 'EA EA')

    def test_tenant_isolation_detail(self):
        self.client.force_login(self.admin_a)
        session = self.client.session
        session['active_company_id'] = self.company_a.id
        session.save()
        
        response = self.client.get(reverse('employees:detail', args=[self.emp_a.id]))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(reverse('employees:detail', args=[self.emp_b.id]))
        self.assertEqual(response.status_code, 404)

    def test_employee_role_access(self):
        self.client.force_login(self.user_emp_a)
        # employee can see their own profile
        response = self.client.get(reverse('employees:detail', args=[self.emp_a.id]))
        self.assertEqual(response.status_code, 200)
        
        # employee cannot see another employee in same company (because EmployeeSelfOnlyMixin)
        user_emp_a2 = User.objects.create_user(password='password', role='CLIENT_EMPLOYEE', email='ea2@test.com', first_name='EA2', last_name='EA2')
        emp_a2 = Employee.objects.create(
            company=self.company_a, user=user_emp_a2, department='IT', position='QA', hire_date='2021-01-01'
        )
        response = self.client.get(reverse('employees:detail', args=[emp_a2.id]))
        self.assertEqual(response.status_code, 404)
