from celery import shared_task
from celery.utils.log import get_task_logger
from datetime import timedelta
from django.utils import timezone
from apps.market.models import StockPrice, MarketScanResult, Sentiment
from apps.authentication.models import RefreshToken

logger = get_task_logger(__name__)

@shared_task
def cleanup_old_data():
    """Clean up old data from database"""
    try:
        # Delete stock prices older than 5 years
        five_years_ago = timezone.now() - timedelta(days=5*365)
        old_prices = StockPrice.objects.filter(timestamp__lt=five_years_ago)
        prices_count = old_prices.count()
        old_prices.delete()
        logger.info(f"Deleted {prices_count} old price records")
        
        # Delete scan results older than 90 days
        ninety_days_ago = timezone.now() - timedelta(days=90)
        old_scans = MarketScanResult.objects.filter(timestamp__lt=ninety_days_ago)
        scans_count = old_scans.count()
        old_scans.delete()
        logger.info(f"Deleted {scans_count} old scan results")
        
        # Delete sentiments older than 90 days
        old_sentiments = Sentiment.objects.filter(timestamp__lt=ninety_days_ago)
        sentiments_count = old_sentiments.count()
        old_sentiments.delete()
        logger.info(f"Deleted {sentiments_count} old sentiment records")
        
        # Delete revoked tokens older than 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        old_tokens = RefreshToken.objects.filter(
            is_revoked=True,
            created_at__lt=thirty_days_ago
        )
        tokens_count = old_tokens.count()
        old_tokens.delete()
        logger.info(f"Deleted {tokens_count} old tokens")
        
        return f"Cleanup completed: {prices_count} prices, {scans_count} scans, {sentiments_count} sentiments, {tokens_count} tokens"
    
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        raise e

@shared_task
def reset_daily_request_counters():
    """Reset daily API request counters"""
    try:
        from apps.authentication.models import UserProfile
        
        profiles = UserProfile.objects.filter(daily_request_count__gt=0)
        count = profiles.count()
        profiles.update(daily_request_count=0)
        
        logger.info(f"Reset request counters for {count} users")
        return f"Reset {count} user counters"
    
    except Exception as e:
        logger.error(f"Reset counters task failed: {e}")
        raise e