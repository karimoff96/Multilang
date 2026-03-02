"""
Management command: notify_overdue_orders

Creates dashboard bell notifications for orders whose deadline has passed
and are still not completed or cancelled. Safe to run multiple times per day —
duplicate unread notifications for the same order are suppressed.

Add to crontab to run daily, e.g.:
  0 9 * * * /home/Wow-dash/venv/bin/python /home/Wow-dash/manage.py notify_overdue_orders
"""

import logging
from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Create bell notifications for overdue orders (deadline passed, not completed/cancelled)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print which orders would be notified without creating anything',
        )

    def handle(self, *args, **options):
        from orders.models import Order
        from core.models import AdminNotification

        dry_run = options['dry_run']
        today = timezone.now().date()

        overdue_orders = Order.objects.filter(
            deadline__lt=today,
        ).exclude(
            status__in=['completed', 'cancelled']
        ).select_related('bot_user', 'branch', 'branch__center')

        created_count = 0
        skipped_count = 0

        for order in overdue_orders:
            if dry_run:
                self.stdout.write(
                    f"  [DRY RUN] Order #{order.get_order_number()} — deadline {order.deadline} — status {order.status}"
                )
                created_count += 1
                continue

            try:
                result = AdminNotification.create_overdue_notification(order)
                if result is None:
                    skipped_count += 1  # already has unread overdue notification
                else:
                    created_count += 1
                    logger.info(f"Created overdue notification for order #{order.get_order_number()}")
            except Exception as e:
                logger.error(f"Failed to create overdue notification for order {order.id}: {e}")
                self.stderr.write(f"ERROR on order #{order.get_order_number()}: {e}")

        label = "[DRY RUN] Would create" if dry_run else "Created"
        self.stdout.write(
            self.style.SUCCESS(
                f"{label} {created_count} overdue notification(s). "
                f"{skipped_count} already had unread overdue notification(s)."
            )
        )
