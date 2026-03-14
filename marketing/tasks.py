"""
Celery tasks for the marketing broadcast system.

Moves the synchronous broadcast execution out of the HTTP request cycle
so that large broadcasts don't block the Gunicorn worker.
"""
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="marketing.send_broadcast",
    max_retries=3,
    default_retry_delay=60,  # 60 s between retries
    queue="broadcasts",
    acks_late=True,           # Only ack after the task completes (crash-safe)
)
def send_broadcast_task(self, post_id: int):
    """
    Execute a MarketingPost broadcast asynchronously.

    Picks up the MarketingPost by primary key, sends to all matching
    BotUser recipients, and updates the post statistics.
    Retries up to 3 times on transient failures.
    """
    from marketing.models import MarketingPost
    from marketing.broadcast_service import BroadcastService

    try:
        post = MarketingPost.objects.get(pk=post_id)
    except MarketingPost.DoesNotExist:
        logger.error("send_broadcast_task: MarketingPost %s not found", post_id)
        return {"error": "post_not_found"}

    if not post.is_sendable:
        logger.warning(
            "send_broadcast_task: post %s is not sendable (status=%s)",
            post_id, post.status,
        )
        return {"error": "not_sendable", "status": post.status}

    try:
        service = BroadcastService(post)
        recipient_count = service.prepare_recipients()

        if recipient_count == 0:
            logger.info("send_broadcast_task: no recipients for post %s", post_id)
            return {"recipients": 0, "sent": 0, "failed": 0}

        result = service.execute()
        logger.info(
            "send_broadcast_task: post %s — sent=%s failed=%s duration=%.1fs",
            post_id, result.sent_count, result.failed_count, result.duration_seconds,
        )
        return {
            "recipients": recipient_count,
            "sent": result.sent_count,
            "failed": result.failed_count,
            "duration_seconds": result.duration_seconds,
        }
    except Exception as exc:
        logger.error(
            "send_broadcast_task: error on post %s: %s", post_id, exc, exc_info=True
        )
        # Retry on transient failures (network errors etc.)
        raise self.retry(exc=exc)
