from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse


class SubscriptionEnforcementMiddleware:
    """Block non-superusers from the app when their center subscription is missing or expired.

    Superusers are exempt. Regular users can only access a small set of safe URLs
    (login/logout, renewal request, the expired page itself, admin, static/media) when
    their subscription is inactive.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        media_url = getattr(settings, "MEDIA_URL", "/media/") or "/media/"
        self.exempt_prefixes = (
            settings.STATIC_URL,
            media_url,
            "/admin",
        )
        self.exempt_names = {
            "admin_login",
            "login",
            "logout",
            "password_reset",
            "password_reset_done",
            "password_reset_confirm",
            "password_reset_complete",
            "billing:subscription_expired",
            "billing:request_renewal",
        }

    def __call__(self, request):
        if self._is_exempt(request):
            return self.get_response(request)

        user = request.user
        if not user.is_authenticated or user.is_superuser:
            return self.get_response(request)

        profile = getattr(user, "admin_profile", None)
        if not profile or not profile.center:
            return self.get_response(request)

        center = profile.center
        subscription = getattr(center, "subscription", None)

        if subscription and subscription.is_active():
            return self.get_response(request)

        # Inactive or missing subscription: keep user in the expired flow only.
        expired_url = reverse("billing:subscription_expired")
        if request.path != expired_url:
            return redirect(expired_url)

        return self.get_response(request)

    def _is_exempt(self, request):
        path = request.path

        for prefix in self.exempt_prefixes:
            if prefix and path.startswith(prefix):
                return True

        match = getattr(request, "resolver_match", None)
        if match:
            url_name = match.view_name or match.url_name
            if url_name in self.exempt_names:
                return True

        return False
