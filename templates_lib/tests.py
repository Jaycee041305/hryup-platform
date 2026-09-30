from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import HRTemplate

User = get_user_model()

class TemplatesLibTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email='admin@hryup.com', password='pw', role='HRYUP_ADMIN', first_name='A', last_name='A')
        self.employee = User.objects.create_user(email='e1@comp1.com', password='pw', role='CLIENT_EMPLOYEE', first_name='E', last_name='1')

    def test_upload_permissions(self):
        self.client.force_login(User.objects.get(email='admin@hryup.com'))
        file_content = b"template content"
        f = SimpleUploadedFile("template.txt", file_content, content_type="text/plain")
        
        response = self.client.post(reverse('templates_lib:template_list'), {
            'title': 'Handbook',
            'description': 'Company Handbook',
            'file': f
        })
        self.assertEqual(HRTemplate.objects.count(), 1)
        
        # Client employee cannot upload
        self.client.force_login(User.objects.get(email='e1@comp1.com'))
        f2 = SimpleUploadedFile("template2.txt", file_content, content_type="text/plain")
        response = self.client.post(reverse('templates_lib:template_list'), {
            'title': 'Handbook2',
            'description': 'Company Handbook2',
            'file': f2
        })
        # form is not rendered/processed for employee
        self.assertEqual(HRTemplate.objects.count(), 1)

    def test_download(self):
        file_content = b"template content"
        f = SimpleUploadedFile("template.txt", file_content, content_type="text/plain")
        t = HRTemplate.objects.create(title='T1', file=f, uploaded_by=self.admin)
        
        self.client.force_login(User.objects.get(email='e1@comp1.com'))
        res = self.client.get(reverse('templates_lib:template_download', args=[t.pk]))
        self.assertEqual(res.status_code, 200)
