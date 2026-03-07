"""
Management command: cancel_expired_payme_orders

Cancels orders whose Payme payment deadline has passed and they are still in
'payment_pending' state with card payment type. Sends a Telegram notification
to each affected user.

Run every 15–30 minutes via crontab, e.g.:
  */15 * * * * /home/Wow-dash/venv/bin/python /home/Wow-dash/manage.py cancel_expired_payme_orders

The order status is set to 'cancelled'. Admin staff can still manually
change the status afterwards if needed.
"""

import logging
from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Auto-cancel Payme-pending orders whose 12-hour payment deadline has expired "
        "and send a notification to the bot user."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print which orders would be cancelled without making changes.",
        )

    def handle(self, *args, **options):
        from orders.models import Order

        dry_run = options["dry_run"]
        now = timezone.now()

        # Find all orders that are still awaiting Payme payment and whose
        # deadline (updated_at + PAYME_PAYMENT_DEADLINE_HOURS) has passed.
        from django.conf import settings
        import datetime
        deadline_hours = getattr(settings, "PAYME_PAYMENT_DEADLINE_HOURS", 12)
        cutoff = now - datetime.timedelta(hours=deadline_hours)
        expired_orders = (
            Order.objects.filter(
                status="payment_pending",
                payment_type="card",
                updated_at__lt=cutoff,
            )
            .select_related("bot_user", "branch__center")
        )

        cancelled_count = 0
        skipped_count = 0

        for order in expired_orders:
            # Extra guard: only auto-cancel for Payme-enabled centers
            center = None
            try:
                if order.branch and order.branch.center:
                    center = order.branch.center
            except Exception:
                pass

            if not (center and center.payme_enabled):
                skipped_count += 1
                continue

            if dry_run:
                self.stdout.write(
                    f"  [DRY RUN] Would cancel order #{order.get_order_number()} "
                    f"(updated_at: {order.updated_at}, center: {center.name})"
                )
                cancelled_count += 1
                continue

            try:
                old_status = order.status
                order.status = "cancelled"
                order.save(update_fields=["status", "updated_at"])
                cancelled_count += 1
                logger.info(
                    f"Auto-cancelled Payme order #{order.get_order_number()} "
                    f"(id={order.id}, updated_at={order.updated_at})"
                )

                # Notify the user via Telegram
                try:
                    from bot.main import send_payme_deadline_expired_notification
                    send_payme_deadline_expired_notification(order)
                except Exception as notify_err:
                    logger.warning(
                        f"Failed to notify user for order {order.id}: {notify_err}"
                    )

            except Exception as e:
                logger.error(f"Failed to cancel order {order.id}: {e}", exc_info=True)

        action = "Would cancel" if dry_run else "Cancelled"
        self.stdout.write(
            self.style.SUCCESS(
                f"{action} {cancelled_count} expired Payme order(s). "
                f"Skipped {skipped_count} (Payme not enabled for center)."
            )
        )
