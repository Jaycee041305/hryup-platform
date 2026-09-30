from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from companies.models import Company
from employees.models import Employee
from documents.models import Document201

User = get_user_model()

class DocumentTenantIsolationTests(TestCase):
    def setUp(self):
        self.company_a = Company.objects.create(name='Company A')
        self.company_b = Company.objects.create(name='Company B')
        
        self.admin_a = User.objects.create_user(password='password', role='HRYUP_STAFF', email='a@test.com', first_name='A', last_name='A')
        self.admin_a.staff_assignments.create(company=self.company_a)
        
        self.user_emp_a = User.objects.create_user(password='password', role='CLIENT_EMPLOYEE', email='ea@test.com', first_name='EA', last_name='EA')
        self.emp_a = Employee.objects.create(company=self.company_a, user=self.user_emp_a, department='IT', position='Dev', hire_date='2020-01-01')
        
        self.user_emp_b = User.objects.create_user(password='password', role='CLIENT_EMPLOYEE', email='eb@test.com', first_name='EB', last_name='EB')
        self.emp_b = Employee.objects.create(company=self.company_b, user=self.user_emp_b, department='HR', position='Recruiter', hire_date='2020-02-01')
        
        fake_file = SimpleUploadedFile("test_doc.pdf", b"file_content", content_type="application/pdf")
        
        self.doc_a = Document201.objects.create(company=self.company_a, employee=self.emp_a, category='RESUME', file=fake_file, uploaded_by=self.admin_a)
        self.doc_b = Document201.objects.create(company=self.company_b, employee=self.emp_b, category='RESUME', file=fake_file, uploaded_by=self.admin_a)
        
    def test_tenant_isolation_list(self):
        self.client.force_login(self.admin_a)
        session = self.client.session
        session['active_company_id'] = self.company_a.id
        session.save()
        
        response = self.client.get(reverse('documents:list'))
        self.assertEqual(response.status_code, 200)
        documents = response.context['documents']
        self.assertIn(self.doc_a, documents)
        self.assertNotIn(self.doc_b, documents)
        
    def test_employee_role_access(self):
        self.client.force_login(self.user_emp_a)
        
        # Can list their own documents
        response = self.client.get(reverse('documents:list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.doc_a, response.context['documents'])
        
        # Can download their own document
        response = self.client.get(reverse('documents:download', args=[self.doc_a.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Disposition'], f'attachment; filename="{self.doc_a.file.name.split("/")[-1]}"')
        
        # Cannot download other employee's document in the same company
        user_emp_a2 = User.objects.create_user(password='password', role='CLIENT_EMPLOYEE', email='ea2@test.com', first_name='EA2', last_name='EA2')
        emp_a2 = Employee.objects.create(company=self.company_a, user=user_emp_a2, department='IT', position='QA', hire_date='2021-01-01')
        doc_a2 = Document201.objects.create(company=self.company_a, employee=emp_a2, category='CONTRACT', file=self.doc_a.file, uploaded_by=self.admin_a)
        
        response = self.client.get(reverse('documents:download', args=[doc_a2.id]))
        self.assertEqual(response.status_code, 404)
