"""
Django management command to backup the database.

This command creates a backup of the database (PostgreSQL or SQLite)
with automatic compression and rotation of old backups.

Usage:
    python manage.py backup_db
    python manage.py backup_db --keep 7  # Keep last 7 backups
"""

import os
import gzip
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Creates a backup of the database with automatic rotation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep',
            type=int,
            default=30,
            help='Number of backups to keep (default: 30)'
        )
        parser.add_argument(
            '--backup-dir',
            type=str,
            default=None,
            help='Custom backup directory path'
        )

    def handle(self, *args, **options):
        keep_backups = options['keep']
        custom_backup_dir = options['backup_dir']
        
        # Get database settings
        db_settings = settings.DATABASES['default']
        db_engine = db_settings['ENGINE']
        
        # Determine backup directory
        if custom_backup_dir:
            backup_dir = Path(custom_backup_dir)
        else:
            backup_dir = settings.BASE_DIR / 'backups' / 'database'
        
        # Create backup directory if it doesn't exist
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        self.stdout.write(self.style.SUCCESS(f'Starting database backup...'))
        
        try:
            if 'postgresql' in db_engine:
                self._backup_postgresql(db_settings, backup_dir, timestamp)
            elif 'sqlite3' in db_engine:
                self._backup_sqlite(db_settings, backup_dir, timestamp)
            else:
                self.stdout.write(
                    self.style.ERROR(f'Unsupported database engine: {db_engine}')
                )
                return
            
            # Rotate old backups
            self._rotate_backups(backup_dir, keep_backups)
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Backup completed successfully!')
            )
            self.stdout.write(f'  Backup location: {backup_dir}')
            self.stdout.write(f'  Keeping last {keep_backups} backups')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Backup failed: {str(e)}')
            )
            raise

    def _backup_postgresql(self, db_settings, backup_dir, timestamp):
        """Backup PostgreSQL database using pg_dump"""
        db_name = db_settings['NAME']
        db_user = db_settings['USER']
        db_password = db_settings['PASSWORD']
        db_host = db_settings['HOST']
        db_port = db_settings['PORT']
        
        backup_file = backup_dir / f'backup_postgres_{timestamp}.sql'
        compressed_file = backup_dir / f'backup_postgres_{timestamp}.sql.gz'
        
        self.stdout.write(f'Backing up PostgreSQL database: {db_name}')
        
        # Set environment variable for password
        env = os.environ.copy()
        env['PGPASSWORD'] = db_password
        
        # Run pg_dump
        cmd = [
            'pg_dump',
            '-h', db_host,
            '-p', str(db_port),
            '-U', db_user,
            '-F', 'p',  # Plain text format
            '-f', str(backup_file),
            db_name
        ]
        
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f'pg_dump failed: {result.stderr}')
        
        # Compress the backup
        self.stdout.write('Compressing backup...')
        with open(backup_file, 'rb') as f_in:
            with gzip.open(compressed_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove uncompressed file
        backup_file.unlink()
        
        file_size = compressed_file.stat().st_size / (1024 * 1024)
        self.stdout.write(f'Backup size: {file_size:.2f} MB')

    def _backup_sqlite(self, db_settings, backup_dir, timestamp):
        """Backup SQLite database"""
        db_path = Path(db_settings['NAME'])
        
        if not db_path.exists():
            raise Exception(f'Database file not found: {db_path}')
        
        backup_file = backup_dir / f'backup_sqlite_{timestamp}.db'
        compressed_file = backup_dir / f'backup_sqlite_{timestamp}.db.gz'
        
        self.stdout.write(f'Backing up SQLite database: {db_path.name}')
        
        # Copy the database file
        shutil.copy2(db_path, backup_file)
        
        # Compress the backup
        self.stdout.write('Compressing backup...')
        with open(backup_file, 'rb') as f_in:
            with gzip.open(compressed_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove uncompressed file
        backup_file.unlink()
        
        file_size = compressed_file.stat().st_size / (1024 * 1024)
        self.stdout.write(f'Backup size: {file_size:.2f} MB')

    def _rotate_backups(self, backup_dir, keep_backups):
        """Remove old backups, keeping only the most recent ones"""
        # Get all backup files
        backup_files = sorted(
            backup_dir.glob('backup_*.gz'),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        # Remove old backups
        if len(backup_files) > keep_backups:
            self.stdout.write(f'Removing old backups...')
            for old_backup in backup_files[keep_backups:]:
                old_backup.unlink()
                self.stdout.write(f'  Removed: {old_backup.name}')
