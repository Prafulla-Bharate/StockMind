from celery import shared_task
from celery.utils.log import get_task_logger
from apps.market.models import Stock, StockPrice
from services.market_data.fetcher import MarketDataFetcher
from services.market_data.indicators import TechnicalIndicatorCalculator
from services.streaming.kafka_producer import StockDataProducer
from django.core.cache import cache
from services.websocket.broadcaster import (
    broadcast_stock_update,
    broadcast_indicator_update
)
from datetime import datetime
from django.utils import timezone

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


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def fetch_historical_data_for_stocks(self, symbols=None, period='1y', force_refresh=False):
    """
    Fetch and store historical data for stocks.
    
    Args:
        symbols: List of stock symbols. If None, fetches for all active stocks.
        period: Time period for historical data ('1y', '6mo', '2y', etc.)
        force_refresh: If True, refetch even if data exists
    
    Returns:
        Summary of operation
    """
    try:
        if symbols is None:
            # Get all active stocks
            stocks = Stock.objects.filter(is_active=True)
        else:
            stocks = Stock.objects.filter(symbol__in=symbols, is_active=True)
        
        fetcher = MarketDataFetcher()
        total_stocks = len(stocks)
        success_count = 0
        skipped_count = 0
        failed_stocks = []
        
        logger.info(f"Starting historical data fetch for {total_stocks} stocks (period: {period})")
        
        for stock in stocks:
            try:
                # Check if already has sufficient data (unless force refresh)
                if not force_refresh:
                    existing_count = StockPrice.objects.filter(stock=stock).count()
                    
                    if existing_count >= 100:
                        logger.info(f"Skipping {stock.symbol} - already has {existing_count} records")
                        skipped_count += 1
                        continue
                
                # Fetch historical data from yfinance
                logger.info(f"Fetching historical data for {stock.symbol}...")
                historical = fetcher.fetch_historical_data(
                    stock.symbol, 
                    period=period, 
                    interval='1d'
                )
                
                if not historical:
                    logger.warning(f"No historical data returned for {stock.symbol}")
                    failed_stocks.append(stock.symbol)
                    continue
                
                # Store data in database
                records_saved = 0
                for item in historical:
                    try:
                        # Convert date to datetime if needed
                        timestamp = item['date']
                        if not isinstance(timestamp, datetime):
                            timestamp = datetime.combine(timestamp, datetime.min.time())
                        if timezone.is_naive(timestamp):
                            timestamp = timezone.make_aware(timestamp)
                        
                        StockPrice.objects.update_or_create(
                            stock=stock,
                            timestamp=timestamp,
                            defaults={
                                'open': item['open'],
                                'high': item['high'],
                                'low': item['low'],
                                'close': item['close'],
                                'volume': item['volume']
                            }
                        )
                        records_saved += 1
                    except Exception as e:
                        logger.error(f"Error saving record for {stock.symbol}: {e}")
                        continue
                
                if records_saved > 0:
                    success_count += 1
                    logger.info(f"✅ Successfully saved {records_saved} records for {stock.symbol}")
                else:
                    failed_stocks.append(stock.symbol)
                    logger.warning(f"No records saved for {stock.symbol}")
                
            except Exception as e:
                logger.error(f"Error fetching historical data for {stock.symbol}: {e}")
                failed_stocks.append(stock.symbol)
                continue
        
        # Summary
        summary = {
            'total_stocks': total_stocks,
            'success': success_count,
            'skipped': skipped_count,
            'failed': len(failed_stocks),
            'failed_symbols': failed_stocks
        }
        
        logger.info(f"Historical data fetch completed: {summary}")
        return summary
        
    except Exception as exc:
        logger.error(f"Task failed: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True)
def populate_single_stock_history(self, symbol, period='1y'):
    """
    Populate historical data for a single stock.
    Useful for adding new stocks or refreshing specific symbols.
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL')
        period: Time period ('1y', '6mo', '2y', etc.)
    
    Returns:
        Number of records saved
    """
    try:
        # Get or create stock
        stock, created = Stock.objects.get_or_create(
            symbol=symbol.upper(),
            defaults={'name': symbol.upper(), 'is_active': True}
        )
        
        if created:
            logger.info(f"Created new stock entry for {symbol}")
        
        # Fetch historical data
        fetcher = MarketDataFetcher()
        historical = fetcher.fetch_historical_data(symbol, period=period, interval='1d')
        
        if not historical:
            logger.warning(f"No historical data returned for {symbol}")
            return 0
        
        # Store data
        records_saved = 0
        for item in historical:
            try:
                timestamp = item['date']
                if not isinstance(timestamp, datetime):
                    timestamp = datetime.combine(timestamp, datetime.min.time())
                if timezone.is_naive(timestamp):
                    timestamp = timezone.make_aware(timestamp)
                
                StockPrice.objects.update_or_create(
                    stock=stock,
                    timestamp=timestamp,
                    defaults={
                        'open': item['open'],
                        'high': item['high'],
                        'low': item['low'],
                        'close': item['close'],
                        'volume': item['volume']
                    }
                )
                records_saved += 1
            except Exception as e:
                logger.error(f"Error saving record: {e}")
                continue
        
        logger.info(f"✅ Saved {records_saved} historical records for {symbol}")
        return records_saved
        
    except Exception as exc:
        logger.error(f"Task failed for {symbol}: {exc}")
        raise exc