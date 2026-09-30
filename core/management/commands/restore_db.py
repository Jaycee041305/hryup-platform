import os
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Restores the database from a given JSON fixture backup.'

    def add_arguments(self, parser):
        parser.add_argument('filepath', type=str, help='Path to the backup JSON file')

    def handle(self, *args, **options):
        filepath = options['filepath']
        
        if not os.path.exists(filepath):
            raise CommandError(f'Backup file "{filepath}" does not exist.')
            
        self.stdout.write(self.style.WARNING(f'WARNING: This will overwrite existing data with {filepath}.'))
        
        try:
            self.stdout.write('Flushing current database...')
            # Flush removes all data but leaves tables
            call_command('flush', '--no-input')
            
            self.stdout.write(f'Loading data from {filepath}...')
            call_command('loaddata', filepath)
            
            self.stdout.write(self.style.SUCCESS(f'Successfully restored database from {filepath}'))
        except Exception as e:
            raise CommandError(f'Error restoring database: {str(e)}')
