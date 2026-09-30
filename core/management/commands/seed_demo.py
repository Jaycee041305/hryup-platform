import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from companies.models import Company, SubscriptionPackage, Subscription
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with demo companies, users, and packages.'

    def handle(self, *args, **options):
        self.stdout.write('Seeding demo data...')
        
        # 1. Packages
        packages = [
            {'name': 'Basic HR', 'tier': 'BASIC', 'price_monthly': 2999, 'module_employee_records': True, 'module_attendance': True},
            {'name': 'Standard HR', 'tier': 'STANDARD', 'price_monthly': 5999, 'module_employee_records': True, 'module_attendance': True, 'module_leave': True, 'module_payroll': True},
            {'name': 'Premium HR', 'tier': 'PREMIUM', 'price_monthly': 9999, 'module_employee_records': True, 'module_attendance': True, 'module_leave': True, 'module_payroll': True, 'module_recruitment': True, 'module_onboarding': True, 'module_helpdesk': True},
        ]
        
        for pkg_data in packages:
            pkg, created = SubscriptionPackage.objects.get_or_create(
                tier=pkg_data['tier'],
                defaults=pkg_data
            )
            if created:
                self.stdout.write(f"Created package: {pkg.name}")

        premium_pkg = SubscriptionPackage.objects.get(tier='PREMIUM')
        basic_pkg = SubscriptionPackage.objects.get(tier='BASIC')

        # 2. Companies
        company1, created = Company.objects.get_or_create(
            name="Alpha Tech MSME",
            defaults={
                'email': 'contact@alphatech.example.com',
                'company_size': 'SMALL',
            }
        )
        if created:
            self.stdout.write(f"Created company: {company1.name}")
            Subscription.objects.create(
                company=company1,
                package=premium_pkg,
                start_date=timezone.now().date(),
                expiry_date=(timezone.now() + timedelta(days=365)).date()
            )

        company2, created = Company.objects.get_or_create(
            name="Beta Retail MSME",
            defaults={
                'email': 'contact@betaretail.example.com',
                'company_size': 'MICRO',
            }
        )
        if created:
            self.stdout.write(f"Created company: {company2.name}")
            Subscription.objects.create(
                company=company2,
                package=basic_pkg,
                start_date=timezone.now().date(),
                expiry_date=(timezone.now() + timedelta(days=365)).date()
            )

        # 3. Users (One per role)
        users = [
            {'email': 'admin@hryup.ph', 'first_name': 'System', 'last_name': 'Admin', 'role': 'HRYUP_ADMIN', 'is_staff': True, 'is_superuser': True},
            {'email': 'staff@hryup.ph', 'first_name': 'HR', 'last_name': 'Specialist', 'role': 'HRYUP_STAFF'},
            {'email': 'manager@alphatech.example.com', 'first_name': 'Client', 'last_name': 'Manager', 'role': 'CLIENT_MANAGER'},
            {'email': 'employee@alphatech.example.com', 'first_name': 'Client', 'last_name': 'Employee', 'role': 'CLIENT_EMPLOYEE'},
        ]

        for u_data in users:
            is_super = u_data.pop('is_superuser', False)
            is_staff = u_data.pop('is_staff', False)
            
            if not User.objects.filter(email=u_data['email']).exists():
                if is_super:
                    user = User.objects.create_superuser(**u_data, password='password123!')
                else:
                    user = User.objects.create_user(**u_data, password='password123!')
                self.stdout.write(f"Created user: {user.email}")
            
        self.stdout.write(self.style.SUCCESS('Successfully seeded demo data!'))
