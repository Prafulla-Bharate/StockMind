from django.apps import AppConfig


class MarketConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.market'
    verbose_name = 'Market'

    def ready(self):
        # import app-specific signals if present
        try:
            import apps.market.signals  # noqa
        except Exception:
            pass