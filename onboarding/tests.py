from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from companies.models import Company
from employees.models import Employee
from onboarding.models import PolicyDocument, OnboardingTemplate, EmployeeOnboarding

User = get_user_model()

class OnboardingTenantIsolationTests(TestCase):
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

        # Create policies
        self.policy_a = PolicyDocument.objects.create(company=self.company_a, title='Policy A')
        self.policy_b = PolicyDocument.objects.create(company=self.company_b, title='Policy B')

        # Employee users
        self.user_emp_a = User.objects.create_user(password='password', role='CLIENT_EMPLOYEE', email='ea@test.com', first_name='EA', last_name='EA')
        self.emp_a = Employee.objects.create(company=self.company_a, user=self.user_emp_a, department='IT', position='Dev', hire_date='2020-01-01')
        
        self.user_emp_b = User.objects.create_user(password='password', role='CLIENT_EMPLOYEE', email='eb@test.com', first_name='EB', last_name='EB')
        self.emp_b = Employee.objects.create(company=self.company_b, user=self.user_emp_b, department='HR', position='Recruiter', hire_date='2020-02-01')

        # Templates
        self.template_a = OnboardingTemplate.objects.create(company=self.company_a, title='Template A')
        self.template_b = OnboardingTemplate.objects.create(company=self.company_b, title='Template B')

        self.tracker_a = EmployeeOnboarding.objects.create(company=self.company_a, employee=self.emp_a, template=self.template_a, status='pending')
        self.tracker_b = EmployeeOnboarding.objects.create(company=self.company_b, employee=self.emp_b, template=self.template_b, status='pending')

    def test_tenant_isolation_tracker(self):
        self.client.force_login(self.admin_a)
        session = self.client.session
        session['active_company_id'] = self.company_a.id
        session.save()
        
        response = self.client.get(reverse('onboarding:tracker_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Template A')
        self.assertNotContains(response, 'Template B')
        
        self.client.force_login(self.admin_b)
        session = self.client.session
        session['active_company_id'] = self.company_b.id
        session.save()
        
        response = self.client.get(reverse('onboarding:tracker_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Template B')
        self.assertNotContains(response, 'Template A')

    def test_tenant_isolation_policies(self):
        self.client.force_login(self.admin_a)
        session = self.client.session
        session['active_company_id'] = self.company_a.id
        session.save()
        
        response = self.client.get(reverse('onboarding:policy_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Policy A')
        self.assertNotContains(response, 'Policy B')

    def test_policy_acknowledgment_isolation(self):
        self.client.force_login(self.user_emp_a)
        session = self.client.session
        session['active_company_id'] = self.company_a.id
        session.save()
        
        # Trying to acknowledge Policy B should fail or return 404
        response = self.client.get(reverse('onboarding:policy_acknowledge', args=[self.policy_b.id]))
        self.assertEqual(response.status_code, 404)
        
        # Policy A should work
        response = self.client.get(reverse('onboarding:policy_acknowledge', args=[self.policy_a.id]))
        self.assertEqual(response.status_code, 200)
