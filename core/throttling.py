"""
Redis-based per-user rate limiter for internal JSON API endpoints.

Usage:
    from core.throttling import throttle

    @login_required
    @throttle(max_calls=10, period=60)   # max 10 calls per 60 s per user
    def my_api_view(request):
        ...

Falls back to allowing the request if Redis is unavailable (fail-open),
so a Redis outage never breaks the dashboard.
"""

import logging
import time
import functools

from django.http import JsonResponse

logger = logging.getLogger(__name__)


def throttle(max_calls: int, period: int, key_prefix: str = "throttle"):
    """
    Decorator factory: limit authenticated users to `max_calls` requests
    within `period` seconds.  Uses a sliding-window counter in Redis.

    Args:
        max_calls: Maximum number of allowed requests in the window.
        period:    Window duration in seconds.
        key_prefix: Optional prefix to differentiate limits across endpoints.

    Returns 429 JSON if the rate is exceeded.
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user_id = getattr(request.user, "pk", None)
            if not user_id:
                # Unauthenticated — let the view's own @login_required handle it
                return view_func(request, *args, **kwargs)

            cache_key = f"{key_prefix}:{view_func.__name__}:u:{user_id}"

            try:
                from django.core.cache import cache

                # Increment the counter; set TTL on first touch
                current = cache.get(cache_key, 0)
                if current >= max_calls:
                    logger.warning(
                        "Rate limit exceeded: user=%s endpoint=%s (%d/%d in %ds)",
                        user_id, view_func.__name__, current, max_calls, period,
                    )
                    return JsonResponse(
                        {
                            "error": "rate_limit_exceeded",
                            "detail": f"Too many requests. Limit: {max_calls} per {period}s.",
                            "retry_after": period,
                        },
                        status=429,
                    )

                # Atomic increment; set expiry only when creating the key
                pipe_result = cache.get_or_set(cache_key, 0, timeout=period)
                cache.incr(cache_key)

            except Exception as exc:
                # Redis unavailable — fail open: allow the request
                logger.debug("Throttle Redis error (fail-open): %s", exc)

            return view_func(request, *args, **kwargs)

        return _wrapped
    return decorator
