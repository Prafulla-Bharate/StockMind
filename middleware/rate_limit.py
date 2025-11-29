"""Development stub for RateLimitMiddleware.

This middleware is intentionally simple: it does not enforce strict rate
limits in development but exposes headers that mirror a rate-limiter so
frontends or tests can detect the presence of rate limiting.

If you want to enable real rate limiting, replace this with a production
implementation or install the original package used in production.
"""
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.conf import settings
import time


class RateLimitMiddleware(MiddlewareMixin):
    """A lightweight, non-blocking rate limit stub for development.

    - Adds headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.
    - Does not return 429 responses; only reports values for visibility.
    """

    DEFAULT_LIMIT = 1000
    DEFAULT_WINDOW = 60 * 60

    def _get_client_key(self, request):
        # Use IP address as key; falls back to session key
        ip = request.META.get("REMOTE_ADDR") or request.META.get("HTTP_X_FORWARDED_FOR")
        if not ip:
            return f"rl:anon:{getattr(request, 'session', None)}"
        return f"rl:ip:{ip}"

    def process_request(self, request):
        limit = getattr(settings, "DEV_RATE_LIMIT", self.DEFAULT_LIMIT)
        window = getattr(settings, "DEV_RATE_LIMIT_WINDOW", self.DEFAULT_WINDOW)

        key = self._get_client_key(request)
        now = int(time.time())
        period_key = f"{key}:{now // window}"

        try:
            count = cache.get(period_key) or 0
            cache.set(period_key, int(count) + 1, timeout=window)
        except Exception:
            # If cache backend isn't configured for dev, silently continue.
            count = 0

        remaining = max(0, limit - int(count))
        reset = ((now // window) + 1) * window

        # Attach simple attrs for views/tests to consume if needed
        request.rate_limit = {"limit": limit, "remaining": remaining, "reset": reset}

    def process_response(self, request, response):
        rl = getattr(request, "rate_limit", None)
        if rl is not None:
            response["X-RateLimit-Limit"] = str(rl.get("limit"))
            response["X-RateLimit-Remaining"] = str(rl.get("remaining"))
            response["X-RateLimit-Reset"] = str(rl.get("reset"))
        return response
