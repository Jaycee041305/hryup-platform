from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from companies.models import Company

User = get_user_model()

class Command(BaseCommand):
    help = 'Wipes all clients, staff, and companies to prepare for real production usage. Keeps the Admin intact.'

    def handle(self, *args, **options):
        # Delete all users EXCEPT the admin
        users_deleted, _ = User.objects.exclude(role='HRYUP_ADMIN').delete()
        
        # Delete all companies
        companies_deleted, _ = Company.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully deleted {users_deleted} non-admin users and {companies_deleted} companies.'
        ))
        self.stdout.write(self.style.SUCCESS('Your database is now clean and ready for real data!'))
