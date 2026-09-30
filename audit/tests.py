from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from .models import AuditLog
from .services import log_action, get_client_ip
from django.utils import timezone
from unittest.mock import Mock

User = get_user_model()

class DummyObj:
    def __init__(self, pk):
        self.pk = pk
    def __str__(self):
        return f"Dummy {self.pk}"

class AuditTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email='admin@test.com', first_name='Admin', last_name='User',
            role='HRYUP_ADMIN', password='password123'
        )
        self.user = User.objects.create_user(
            email='user@test.com', first_name='Regular', last_name='User',
            role='CLIENT_EMPLOYEE', password='password123'
        )
        self.client = Client()
        self.factory = RequestFactory()

    def test_audit_log_creation(self):
        log = AuditLog.objects.create(
            user=self.user,
            action='CREATE',
            description='Test creation'
        )
        self.assertEqual(AuditLog.objects.count(), 1)
        self.assertIn('CREATE', str(log))

    def test_log_action_service(self):
        dummy = DummyObj(1)
        request = self.factory.get('/')
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        
        log = log_action(
            user=self.user,
            action='UPDATE',
            description='Updated dummy',
            obj=dummy,
            request=request
        )
        self.assertEqual(log.object_type, 'DummyObj')
        self.assertEqual(log.object_id, '1')
        self.assertEqual(log.ip_address, '127.0.0.1')

    def test_get_client_ip_without_proxy(self):
        request = self.factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        ip = get_client_ip(request)
        self.assertEqual(ip, '192.168.1.1')

    def test_get_client_ip_with_proxy(self):
        request = self.factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '10.0.0.1, 192.168.1.1'
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        ip = get_client_ip(request)
        self.assertEqual(ip, '10.0.0.1')

    def test_audit_log_list_view_access(self):
        # Admin can access
        self.client.force_login(self.admin)
        response = self.client.get(reverse('audit:audit_log_list'))
        self.assertEqual(response.status_code, 200)
        
        # Non-admin cannot
        self.client.force_login(self.user)
        response = self.client.get(reverse('audit:audit_log_list'))
        self.assertEqual(response.status_code, 403)

    def test_log_entry_on_login(self):
        # Use POST to the login URL to trigger the full auth flow including signals
        from django.test import RequestFactory
        from django.contrib.auth import authenticate
        from django.contrib.auth.signals import user_logged_in

        # Manually trigger the signal since axes makes client.login() difficult in tests
        factory = RequestFactory()
        request = factory.post('/accounts/login/')
        request.META['REMOTE_ADDR'] = '127.0.0.1'

        # The accounts.signals module already connects to user_logged_in
        # Just dispatch the signal manually
        user_logged_in.send(sender=self.user.__class__, request=request, user=self.user)

        self.assertTrue(AuditLog.objects.filter(user=self.user, action='LOGIN').exists())
