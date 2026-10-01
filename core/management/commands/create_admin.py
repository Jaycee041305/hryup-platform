from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates the default HRyUp Admin account if it does not exist.'

    def handle(self, *args, **options):
        email = 'admin@hryup.ph'
        if not User.objects.filter(email=email).exists():
            User.objects.create_superuser(
                email=email,
                first_name='System',
                last_name='Admin',
                role='HRYUP_ADMIN',
                password='password123!'
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully created admin account: {email}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Admin account {email} already exists.'))
