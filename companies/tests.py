from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import Company, SubscriptionPackage, Subscription

User = get_user_model()

class CompaniesTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email='admin@test.com', first_name='Admin', last_name='User',
            role='HRYUP_ADMIN', password='password123'
        )
        self.staff = User.objects.create_user(
            email='staff@test.com', first_name='Staff', last_name='User',
            role='HRYUP_STAFF', password='password123'
        )
        self.user = User.objects.create_user(
            email='user@test.com', first_name='Regular', last_name='User',
            role='CLIENT_EMPLOYEE', password='password123'
        )
        
        self.company = Company.objects.create(name='Test Company', address='123 Test St')
        
        self.package = SubscriptionPackage.objects.create(
            name='Test Package',
            tier='BASIC',
            price_monthly=100.00,
            module_recruitment=True
        )
        
        self.subscription = Subscription.objects.create(
            company=self.company,
            package=self.package,
            start_date=timezone.now().date(),
            expiry_date=timezone.now().date() + timedelta(days=30)
        )
        
        self.client = Client()

    def test_company_creation_and_str(self):
        self.assertEqual(str(self.company), 'Test Company')
        self.assertEqual(Company.objects.count(), 1)
        
    def test_subscription_package_creation(self):
        self.assertTrue(self.package.module_recruitment)
        self.assertFalse(self.package.module_onboarding)
        self.assertEqual(str(self.package), 'Test Package (BASIC)')

    def test_subscription_status_and_is_active(self):
        self.assertTrue(self.subscription.is_active)
        self.subscription.expiry_date = timezone.now().date() - timedelta(days=1)
        self.subscription.save()
        self.assertFalse(self.subscription.is_active)

    def test_company_has_module(self):
        self.assertTrue(self.company.has_module('recruitment'))
        self.assertFalse(self.company.has_module('onboarding'))

    def test_view_access_control_admin(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('companies:company_create'))
        self.assertEqual(response.status_code, 200)

    def test_view_access_control_staff(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('companies:company_list'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(reverse('companies:company_create'))
        self.assertEqual(response.status_code, 403)

    def test_view_access_control_non_admin(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('companies:company_list'))
        self.assertEqual(response.status_code, 403)
        
    def test_staff_assignment(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('companies:staff_assignment', kwargs={'company_id': self.company.id}))
        self.assertEqual(response.status_code, 200)
