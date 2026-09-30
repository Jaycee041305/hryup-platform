import os
import shutil
import subprocess
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
import dj_database_url

class Command(BaseCommand):
    help = """Backup the database.
    
    RESTORE PROCEDURES:
    
    SQLite:
        1. Stop the application
        2. Copy the backup file to replace the db.sqlite3 file:
           cp backups/backup_YYYYMMDD_HHMMSS.sqlite3 db.sqlite3
        3. Restart the application
    
    PostgreSQL:
        1. Stop the application
        2. Drop and recreate the database:
           dropdb hryup_db
           createdb hryup_db
        3. Restore from backup:
           pg_restore -d hryup_db backups/backup_YYYYMMDD_HHMMSS.dump
           OR for SQL format:
           psql hryup_db < backups/backup_YYYYMMDD_HHMMSS.sql
        4. Restart the application
    """
    
    def add_arguments(self, parser):
        parser.add_argument('--keep', type=int, default=10, help='Number of backups to keep')
        parser.add_argument('--output-dir', type=str, default='backups', help='Backup output directory')
    
    def handle(self, *args, **options):
        backup_dir = os.path.join(settings.BASE_DIR, options['output_dir'])
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        db_config = settings.DATABASES['default']
        engine = db_config.get('ENGINE', '')
        
        if 'sqlite3' in engine:
            db_path = db_config.get('NAME', '')
            if not os.path.exists(db_path):
                self.stdout.write(self.style.ERROR(f'Database file not found: {db_path}'))
                return
            backup_filename = f'backup_{timestamp}.sqlite3'
            backup_path = os.path.join(backup_dir, backup_filename)
            shutil.copy2(db_path, backup_path)
            
        elif 'postgresql' in engine or 'postgres' in engine:
            backup_filename = f'backup_{timestamp}.dump'
            backup_path = os.path.join(backup_dir, backup_filename)
            
            env = os.environ.copy()
            if db_config.get('PASSWORD'):
                env['PGPASSWORD'] = db_config['PASSWORD']
            
            cmd = [
                'pg_dump',
                '-h', db_config.get('HOST', 'localhost'),
                '-p', str(db_config.get('PORT', '5432')),
                '-U', db_config.get('USER', 'postgres'),
                '-Fc',  # Custom format for pg_restore
                '-f', backup_path,
                db_config.get('NAME', 'hryup_db')
            ]
            
            try:
                subprocess.run(cmd, env=env, check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                self.stdout.write(self.style.ERROR(f'Backup failed: {e.stderr.decode()}'))
                return
            except FileNotFoundError:
                self.stdout.write(self.style.ERROR('pg_dump not found. Is PostgreSQL client installed?'))
                return
        else:
            self.stdout.write(self.style.ERROR(f'Unsupported database engine: {engine}'))
            return
        
        # Report success
        size = os.path.getsize(backup_path)
        size_mb = size / (1024 * 1024)
        self.stdout.write(self.style.SUCCESS(
            f'Backup created: {backup_path} ({size_mb:.2f} MB)'
        ))
        
        # Cleanup old backups
        self._cleanup_old_backups(backup_dir, options['keep'])
    
    def _cleanup_old_backups(self, backup_dir, keep):
        backups = sorted([
            f for f in os.listdir(backup_dir)
            if f.startswith('backup_')
        ])
        
        if len(backups) > keep:
            for old_backup in backups[:-keep]:
                old_path = os.path.join(backup_dir, old_backup)
                os.remove(old_path)
                self.stdout.write(f'Removed old backup: {old_backup}')
