"""
Management command to clean up stale bot user states.
Run this periodically (e.g., daily via cron) to prevent database bloat.
"""
from django.core.management.base import BaseCommand
from accounts.models import BotUserState


class Command(BaseCommand):
    help = 'Clean up stale bot user states older than specified hours'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Clean up states not updated in this many hours (default: 24)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned without actually doing it'
        )

    def handle(self, *args, **options):
        hours = options['hours']
        dry_run = options['dry_run']
        
        if dry_run:
            from django.utils import timezone
            from datetime import timedelta
            
            cutoff = timezone.now() - timedelta(hours=hours)
            count = BotUserState.objects.filter(updated_at__lt=cutoff).count()
            self.stdout.write(
                self.style.WARNING(f'Would clean up {count} stale states (dry run)')
            )
        else:
            cleaned = BotUserState.cleanup_old_states(hours=hours)
            self.stdout.write(
                self.style.SUCCESS(f'Cleaned up {cleaned} stale bot user states')
            )
