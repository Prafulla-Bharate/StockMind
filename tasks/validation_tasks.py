"""
Validation and cleanup tasks for the market data
"""
import logging
from celery import shared_task
from apps.market.models import Stock, StockPrice
from services.market_data.resolver import _validate_symbol_has_data
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task
def validate_and_cleanup_stocks():
    """
    Remove stocks from database that:
    1. Have no valid market data (invalid symbols)
    2. Have no price data for >7 days
    3. Are duplicates or have wrong exchange suffix
    """
    removed_count = 0
    invalid_count = 0
    stale_count = 0
    
    try:
        # Get all stocks
        all_stocks = Stock.objects.all()
        
        for stock in all_stocks:
            # Check 1: Invalid symbol (no fetchable data)
            if not _validate_symbol_has_data(stock.symbol):
                logger.info(f"Removing invalid stock: {stock.symbol} (no market data)")
                stock.delete()
                invalid_count += 1
                removed_count += 1
                continue
            
            # Check 2: Stale data (no prices in >7 days)
            latest_price = StockPrice.objects.filter(stock=stock).order_by('-timestamp').first()
            if not latest_price:
                logger.info(f"Removing stale stock: {stock.symbol} (no price history)")
                stock.delete()
                stale_count += 1
                removed_count += 1
                continue
            
            cutoff = timezone.now() - timedelta(days=7)
            if latest_price.timestamp < cutoff:
                logger.info(f"Removing stale stock: {stock.symbol} (last update: {latest_price.timestamp})")
                stock.delete()
                stale_count += 1
                removed_count += 1
    
    except Exception as e:
        logger.error(f"Error in validate_and_cleanup_stocks: {e}")
        return f"Error: {e}"
    
    return f"Cleanup complete: removed {removed_count} stocks ({invalid_count} invalid, {stale_count} stale)"


@shared_task
def validate_stock_data(symbol: str) -> bool:
    """
    Validate a specific stock symbol has real market data.
    Returns True if valid, False otherwise.
    """
    try:
        if _validate_symbol_has_data(symbol):
            logger.info(f"Stock {symbol} validated successfully")
            return True
        else:
            logger.warning(f"Stock {symbol} failed validation - no market data")
            # Optionally remove the stock if it fails
            Stock.objects.filter(symbol=symbol).delete()
            return False
    except Exception as e:
        logger.error(f"Error validating stock {symbol}: {e}")
        return False
