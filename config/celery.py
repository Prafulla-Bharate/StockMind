import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('stockmind')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    'fetch-market-data-every-minute': {
        'task': 'tasks.market_tasks.fetch_market_data',
        'schedule': crontab(minute='*'),  # Every minute
        'args': (),
    },
    'calculate-technical-indicators': {
        'task': 'tasks.market_tasks.calculate_technical_indicators',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'run-market-scanner-daily': {
        'task': 'tasks.scanner_tasks.run_market_scanner',
        'schedule': crontab(hour=16, minute=0),  # 4 PM ET daily
        'args': ('daily',),
    },
    'run-market-scanner-weekly': {
        'task': 'tasks.scanner_tasks.run_market_scanner',
        'schedule': crontab(day_of_week=5, hour=16, minute=0),  # Friday 4 PM
        'args': ('weekly',),
    },
    'update-predictions-hourly': {
        'task': 'tasks.prediction_tasks.update_predictions',
        'schedule': crontab(minute=0),  # Every hour
    },
    'fetch-news-every-30min': {
        'task': 'tasks.sentiment_tasks.fetch_and_analyze_news',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
    'cleanup-old-data-daily': {
        'task': 'tasks.cleanup_tasks.cleanup_old_data',
        'schedule': crontab(hour=0, minute=0),  # Midnight
    },
}

# Task routing
app.conf.task_routes = {
    'tasks.market_tasks.*': {'queue': 'market_data'},
    'tasks.prediction_tasks.*': {'queue': 'predictions'},
    'tasks.sentiment_tasks.*': {'queue': 'sentiment'},
    'tasks.scanner_tasks.*': {'queue': 'default'},
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')