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


class EmployeeRegistrationAndOnboardingApprovalTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name='Test Corp')
        self.manager_user = User.objects.create_user(
            email='manager@testcorp.com',
            first_name='Mngr',
            last_name='Corp',
            role='CLIENT_MANAGER',
            password='password123'
        )
        self.manager_emp = Employee.objects.create(
            user=self.manager_user,
            company=self.company,
            department='Management',
            position='Manager',
            hire_date='2020-01-01',
            status=Employee.StatusChoices.ACTIVE
        )

    def test_signup_creates_inactive_user_and_pending_tracker(self):
        from accounts.forms import UserRegistrationForm
        form_data = {
            'first_name': 'Juan',
            'last_name': 'Dela Cruz',
            'email': 'juan@testcorp.com',
            'phone': '09123456789',
            'company': self.company.pk,
            'position': 'Clerk',
            'password1': 'SafePass123!',
            'password2': 'SafePass123!',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()

        # User must be inactive awaiting onboarding approval
        self.assertFalse(user.is_active)
        self.assertEqual(user.role, 'CLIENT_EMPLOYEE')

        # Employee profile must be pending approval
        self.assertEqual(user.employee_profile.status, Employee.StatusChoices.PENDING_APPROVAL)

        # Onboarding tracker must be created with pending status
        tracker = EmployeeOnboarding.objects.get(employee=user.employee_profile)
        self.assertEqual(tracker.status, 'pending')
        self.assertTrue(tracker.employee_tasks.exists())

    def test_inactive_employee_login_form_message(self):
        from accounts.forms import EmailAuthenticationForm
        user = User.objects.create_user(
            email='pending@testcorp.com',
            first_name='Pending',
            last_name='User',
            role='CLIENT_EMPLOYEE',
            password='password123',
            is_active=False
        )
        form = EmailAuthenticationForm(data={'username': 'pending@testcorp.com', 'password': 'password123'})
        self.assertFalse(form.is_valid())
        self.assertIn('pending onboarding approval', str(form.errors))

    def test_manager_approves_application(self):
        # Create pending employee
        user = User.objects.create_user(
            email='applicant@testcorp.com',
            first_name='App',
            last_name='Licant',
            role='CLIENT_EMPLOYEE',
            password='password123',
            is_active=False
        )
        employee = Employee.objects.create(
            user=user,
            company=self.company,
            department='General',
            position='Staff',
            hire_date='2026-10-13',
            status=Employee.StatusChoices.PENDING_APPROVAL
        )
        template = OnboardingTemplate.objects.create(title='Standard', company=self.company)
        tracker = EmployeeOnboarding.objects.create(
            employee=employee,
            template=template,
            company=self.company,
            status='pending'
        )

        # Log in as manager and approve
        self.client.force_login(self.manager_user)
        response = self.client.post(reverse('onboarding:tracker_approve', kwargs={'pk': tracker.pk}))
        self.assertEqual(response.status_code, 302)

        # Reload records from DB
        user.refresh_from_db()
        employee.refresh_from_db()
        tracker.refresh_from_db()

        # User is active, employee is active, tracker is in progress
        self.assertTrue(user.is_active)
        self.assertEqual(employee.status, Employee.StatusChoices.ACTIVE)
        self.assertEqual(tracker.status, 'in_progress')
