from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from companies.models import Company
from recruitment.models import JobVacancy, Application

User = get_user_model()

class RecruitmentTenantIsolationTests(TestCase):
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
        
        # Create vacancies
        self.vacancy_a = JobVacancy.objects.create(company=self.company_a, title='Vacancy A', description='Desc A', requirements='Req A', status='open')
        self.vacancy_b = JobVacancy.objects.create(company=self.company_b, title='Vacancy B', description='Desc B', requirements='Req B', status='open')

        # Create applications
        self.app_a = Application.objects.create(company=self.company_a, vacancy=self.vacancy_a, applicant_name='App A', email='appa@test.com', phone='123', status='new')
        self.app_b = Application.objects.create(company=self.company_b, vacancy=self.vacancy_b, applicant_name='App B', email='appb@test.com', phone='456', status='new')

    def test_tenant_isolation_list(self):
        self.client.force_login(self.admin_a)
        session = self.client.session
        session['active_company_id'] = self.company_a.id
        session.save()
        
        response = self.client.get(reverse('recruitment:vacancy_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vacancy A')
        self.assertNotContains(response, 'Vacancy B')
        
        self.client.force_login(self.admin_b)
        session = self.client.session
        session['active_company_id'] = self.company_b.id
        session.save()
        
        response = self.client.get(reverse('recruitment:vacancy_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vacancy B')
        self.assertNotContains(response, 'Vacancy A')

    def test_tenant_isolation_pipeline(self):
        self.client.force_login(self.admin_a)
        session = self.client.session
        session['active_company_id'] = self.company_a.id
        session.save()
        
        response = self.client.get(reverse('recruitment:pipeline'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'App A')
        self.assertNotContains(response, 'App B')

    def test_public_vacancy_list(self):
        response = self.client.get(reverse('recruitment:public_vacancy_list', args=[self.company_a.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vacancy A')
        self.assertNotContains(response, 'Vacancy B')
