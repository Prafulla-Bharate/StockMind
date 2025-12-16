from celery import shared_task
from celery.utils.log import get_task_logger
from apps.market.models import Stock
from services.market_data.fetcher import MarketDataFetcher
from services.market_data.indicators import TechnicalIndicatorCalculator
from services.streaming.kafka_producer import StockDataProducer
from django.core.cache import cache
from services.websocket.broadcaster import (
    broadcast_stock_update,
    broadcast_indicator_update
)

logger = get_task_logger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_market_data(self, symbols=None):
    """Fetch real-time market data"""
    try:
        if symbols is None:
            # Get top 100 stocks
            symbols = list(Stock.objects.filter(is_active=True)[:100].values_list('symbol', flat=True))
        
        fetcher = MarketDataFetcher()
        producer = StockDataProducer()
        
        for symbol in symbols:
            try:
                # Fetch quote
                quote = fetcher.fetch_real_time_quote(symbol)
                
                if quote:
                    # Save to database
                    fetcher.save_stock_price(symbol, quote)
                    
                    # Send to Kafka
                    producer.send_market_data(symbol, quote)
                    
                    # Cache for WebSocket
                    cache.set(f"latest_price_{symbol}", quote, 300)
                    
                    # Broadcast via WebSocket
                    broadcast_stock_update(symbol, quote)

                    logger.info(f"Fetched data for {symbol}")
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                continue
        
        producer.close()
        return f"Processed {len(symbols)} symbols"
        
    except Exception as exc:
        logger.error(f"Task failed: {exc}")
        raise self.retry(exc=exc)

@shared_task(bind=True)
def calculate_technical_indicators(self):
    """Calculate technical indicators for all active stocks"""
    try:
        symbols = Stock.objects.filter(is_active=True).values_list('symbol', flat=True)
        calculator = TechnicalIndicatorCalculator()
        
        success_count = 0
        for symbol in symbols:
            try:
                indicators = calculator.calculate_indicators(symbol)
                if indicators:
                    success_count += 1
                    cache.set(f"indicators_{symbol}", indicators, 600)
            except Exception as e:
                logger.error(f"Error calculating indicators for {symbol}: {e}")
                continue
        
        return f"Calculated indicators for {success_count}/{len(symbols)} stocks"
        
    except Exception as exc:
        logger.error(f"Task failed: {exc}")
        raise exc