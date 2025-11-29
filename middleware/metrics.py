"""Development stub for Prometheus-like metrics middleware.

This stub will not export real metrics but will attempt to integrate with
`prometheus_client` if available. Otherwise it acts as a no-op while
exposing a small header so the middleware presence is observable.
"""
from django.utils.deprecation import MiddlewareMixin
from importlib import import_module


class PrometheusMiddleware(MiddlewareMixin):
    """A tiny middleware that records basic request timing when possible.

    For development this either records a timing metric using the
    `prometheus_client` package (if installed) or sets a header
    `X-Prometheus-Stub` so the app doesn't break when the middleware
    is referenced.
    """

    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.client = None
        try:
            prometheus = import_module("prometheus_client")
            self.client = prometheus
        except Exception:
            self.client = None

    def process_request(self, request):
        request._prometheus_start_time = None
        if self.client:
            try:
                import time
                request._prometheus_start_time = time.time()
            except Exception:
                request._prometheus_start_time = None

    def process_response(self, request, response):
        if getattr(request, "_prometheus_start_time", None) and self.client:
            try:
                import time
                duration = time.time() - request._prometheus_start_time
                # Best-effort: don't crash if registry isn't available
                # Real instrumentation would use counters/histograms.
                # Here we only attach a header with duration for visibility.
                response["X-Prometheus-Duration"] = str(round(duration, 6))
            except Exception:
                pass
        else:
            response["X-Prometheus-Stub"] = "1"
        return response
