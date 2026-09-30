from django.core.management.base import BaseCommand
from companies.models import SubscriptionPackage


class Command(BaseCommand):
    help = 'Seed the subscription packages (Basic, Standard, Premium)'

    def handle(self, *args, **options):
        packages = [
            {
                'name': 'Basic Plan',
                'tier': 'BASIC',
                'defaults': {
                    'description': 'Essential HR features for micro businesses getting started.',
                    'price_monthly': 2999.00,
                    'price_annually': 29990.00,
                    'max_employees': 10,
                    'module_employee_records': True,
                    'module_attendance': True,
                    'module_leave': False,
                    'module_payroll': False,
                    'module_helpdesk': False,
                    'module_recruitment': False,
                    'module_onboarding': False,
                    'is_active': True,
                },
            },
            {
                'name': 'Standard Plan',
                'tier': 'STANDARD',
                'defaults': {
                    'description': 'Complete HR suite for growing teams. Most popular choice.',
                    'price_monthly': 5999.00,
                    'price_annually': 59990.00,
                    'max_employees': 50,
                    'module_employee_records': True,
                    'module_attendance': True,
                    'module_leave': True,
                    'module_payroll': True,
                    'module_helpdesk': True,
                    'module_recruitment': False,
                    'module_onboarding': False,
                    'is_active': True,
                },
            },
            {
                'name': 'Premium Plan',
                'tier': 'PREMIUM',
                'defaults': {
                    'description': 'Full-featured HR platform with all modules for medium enterprises.',
                    'price_monthly': 9999.00,
                    'price_annually': 99990.00,
                    'max_employees': 200,
                    'module_employee_records': True,
                    'module_attendance': True,
                    'module_leave': True,
                    'module_payroll': True,
                    'module_helpdesk': True,
                    'module_recruitment': True,
                    'module_onboarding': True,
                    'is_active': True,
                },
            },
        ]

        for pkg_data in packages:
            defaults = pkg_data['defaults'].copy()
            defaults['name'] = pkg_data['name']
            package, created = SubscriptionPackage.objects.update_or_create(
                tier=pkg_data['tier'],
                defaults=defaults,
            )
            action = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(
                f'{action} package: {package.name} ({package.tier}) - PHP {package.price_monthly}/mo'
            ))

        self.stdout.write(self.style.SUCCESS('\nAll packages seeded successfully.'))
