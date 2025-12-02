from apps.market.models import Stock, StockPrice
from django.db.models import Avg, F
from datetime import datetime, timedelta
from utils.constants import (
    GAINER_THRESHOLD, LOSER_THRESHOLD,
    UNUSUAL_VOLUME_RATIO, BREAKOUT_THRESHOLD
)
import logging

logger = logging.getLogger(__name__)

class MarketScanner:
    """Market scanner for finding interesting stocks"""
    
    def scan(self, timeframe='daily'):
        """Scan market for gainers, losers, unusual volume, breakouts"""
        try:
            # Get all active stocks
            stocks = Stock.objects.filter(is_active=True)
            results = []
            
            for stock in stocks:
                try:
                    result = self._analyze_stock(stock, timeframe)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.error(f"Error analyzing {stock.symbol}: {e}")
                    continue
            
            return results
        
        except Exception as e:
            logger.error(f"Scanner error: {e}")
            return []
    
    def _analyze_stock(self, stock, timeframe):
        """Analyze individual stock"""
        # Get latest two prices
        prices = StockPrice.objects.filter(stock=stock).order_by('-timestamp')[:2]
        
        if len(prices) < 2:
            return None
        
        latest = prices[0]
        previous = prices[1]
        
        # Calculate change
        change = latest.close - previous.close
        change_percent = ((latest.close - previous.close) / previous.close) * 100
        
        # Calculate average volume (20 days)
        twenty_days_ago = datetime.now() - timedelta(days=20)
        avg_volume = StockPrice.objects.filter(
            stock=stock,
            timestamp__gte=twenty_days_ago
        ).aggregate(Avg('volume'))['volume__avg'] or 1
        
        volume_ratio = latest.volume / avg_volume if avg_volume > 0 else 1
        
        # Determine flags
        is_gainer = change_percent >= GAINER_THRESHOLD
        is_loser = change_percent <= LOSER_THRESHOLD
        is_unusual_volume = volume_ratio >= UNUSUAL_VOLUME_RATIO
        is_breakout = abs(change_percent) >= BREAKOUT_THRESHOLD
        
        # Determine trend
        if change_percent > 0:
            trend = 'Bullish'
        elif change_percent < 0:
            trend = 'Bearish'
        else:
            trend = 'Neutral'
        
        return {
            'stock': stock,
            'price': latest.close,
            'change': change,
            'change_percent': change_percent,
            'volume': latest.volume,
            'avg_volume': int(avg_volume),
            'volume_ratio': volume_ratio,
            'is_gainer': is_gainer,
            'is_loser': is_loser,
            'is_unusual_volume': is_unusual_volume,
            'is_breakout': is_breakout,
            'trend': trend,
            'resistance': None,  # Calculate if needed
            'support': None      # Calculate if needed
        }