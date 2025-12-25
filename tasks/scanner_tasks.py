from celery import shared_task
from celery.utils.log import get_task_logger
from apps.market.models import Stock, StockPrice, MarketScanResult
from services.market_data.scanner import MarketScanner
from datetime import datetime

logger = get_task_logger(__name__)

@shared_task(bind=True)
def run_market_scanner(self, timeframe='daily'):
    """Run market scanner"""
    try:
        scanner = MarketScanner()
        results = scanner.scan(timeframe=timeframe)
        
        if not results:
            logger.warning(f"No scanner results for {timeframe}")
            return f"No results for {timeframe}"
        
        # Save results
        from django.utils import timezone
        timestamp = timezone.now()
        created_count = 0
        
        for result in results:
            try:
                MarketScanResult.objects.create(
                    timestamp=timestamp,
                    timeframe=timeframe,
                    stock=result['stock'],
                    price=result['price'],
                    change=result['change'],
                    change_percent=result['change_percent'],
                    volume=result['volume'],
                    avg_volume=result['avg_volume'],
                    volume_ratio=result['volume_ratio'],
                    is_unusual_volume=result['is_unusual_volume'],
                    is_breakout=result['is_breakout'],
                    is_gainer=result['is_gainer'],
                    is_loser=result['is_loser'],
                    trend=result['trend'],
                    resistance=result.get('resistance'),
                    support=result.get('support')
                )
                created_count += 1
            
            except Exception as e:
                logger.error(f"Error saving scan result: {e}")
                continue
        
        return f"Scanner completed: {created_count} results for {timeframe}"
    
    except Exception as exc:
        logger.error(f"Scanner task failed: {exc}")
        raise self.retry(exc=exc, countdown=300)