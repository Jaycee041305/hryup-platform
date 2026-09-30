from django.core.management.base import BaseCommand
from accounts.models import User

class Command(BaseCommand):
    help = 'Create the initial HRyUp admin user'
    
    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, default='admin@hryup.ph')
        parser.add_argument('--password', type=str, default='admin123!')
        parser.add_argument('--first-name', type=str, default='HRyUp')
        parser.add_argument('--last-name', type=str, default='Admin')
    
    def handle(self, *args, **options):
        email = options['email']
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f'User {email} already exists. Skipping.'))
            return
        
        user = User.objects.create_superuser(
            email=email,
            password=options['password'],
            first_name=options['first_name'],
            last_name=options['last_name'],
            role='HRYUP_ADMIN'
        )
        self.stdout.write(self.style.SUCCESS(f'Created admin user: {user.email}'))
