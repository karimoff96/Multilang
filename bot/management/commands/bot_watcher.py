"""
Bot Token Watcher - Automatically restarts bots when tokens change.

This command watches for changes in Translation Center bot tokens
and automatically restarts the bot process when changes are detected.

Usage:
    python manage.py bot_watcher
"""
import time
import subprocess
import hashlib
import logging
from django.core.management.base import BaseCommand
from organizations.models import TranslationCenter

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Watch for bot token changes and auto-restart bot process'

    def __init__(self):
        super().__init__()
        self.last_token_hash = None

    def get_token_hash(self):
        """Get a hash of all bot tokens to detect changes."""
        centers = TranslationCenter.objects.filter(
            is_active=True
        ).exclude(
            bot_token__isnull=True
        ).exclude(
            bot_token=''
        ).values_list('id', 'bot_token').order_by('id')
        
        token_string = '|'.join(f"{c[0]}:{c[1]}" for c in centers)
        return hashlib.md5(token_string.encode()).hexdigest()

    def restart_bots(self):
        """Restart the bot supervisor process."""
        try:
            result = subprocess.run(
                ['supervisorctl', 'restart', 'wowdash-bots'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.stdout.write(self.style.SUCCESS('✓ Bot process restarted successfully'))
                logger.info('Bot process restarted due to token change')
            else:
                self.stdout.write(self.style.ERROR(f'✗ Failed to restart: {result.stderr}'))
                logger.error(f'Failed to restart bots: {result.stderr}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error restarting bots: {e}'))
            logger.error(f'Error restarting bots: {e}')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🤖 Bot Token Watcher started'))
        self.stdout.write('Watching for bot token changes every 30 seconds...')
        
        self.last_token_hash = self.get_token_hash()
        self.stdout.write(f'Initial token hash: {self.last_token_hash}')

        while True:
            try:
                time.sleep(30)  # Check every 30 seconds
                
                current_hash = self.get_token_hash()
                
                if current_hash != self.last_token_hash:
                    self.stdout.write(self.style.WARNING(
                        f'⚡ Bot tokens changed! Old: {self.last_token_hash}, New: {current_hash}'
                    ))
                    self.restart_bots()
                    self.last_token_hash = current_hash
                    
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('\n👋 Bot watcher stopped'))
                break
            except Exception as e:
                logger.error(f'Bot watcher error: {e}')
                time.sleep(5)  # Wait before retrying
