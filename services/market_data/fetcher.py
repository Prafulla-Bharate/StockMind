import yfinance as yf
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from django.core.cache import cache
from apps.market.models import Stock, StockPrice
import pandas as pd

logger = logging.getLogger(__name__)



class MarketDataFetcher:
    """Fetch market data using yfinance (NO RATE LIMITS!)"""
    
    def __init__(self):
        # No API key needed!
        pass
    
    def fetch_real_time_quote(self, symbol):
        """Fetch real-time quote - NO RATE LIMITS"""
        cache_key = f"realtime_quote_{symbol}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info or 'currentPrice' not in info:
                # Fallback to fast_info
                fast_info = ticker.fast_info
                quote_data = {
                    'symbol': symbol,
                    'price': Decimal(str(fast_info.get('last_price', 0))),
                    'open': Decimal(str(fast_info.get('open', 0))),
                    'high': Decimal(str(fast_info.get('day_high', 0))),
                    'low': Decimal(str(fast_info.get('day_low', 0))),
                    'previousClose': Decimal(str(fast_info.get('previous_close', 0))),
                    'volume': int(fast_info.get('last_volume', 0)),
                    'timestamp': timezone.now()
                }
            else:
                current_price = Decimal(str(info.get('currentPrice', 0)))
                previous_close = Decimal(str(info.get('previousClose', 0)))
                change = current_price - previous_close
                change_percent = (change / previous_close * 100) if previous_close > 0 else 0
                
                quote_data = {
                    'symbol': symbol,
                    'price': current_price,
                    'change': change,
                    'changePercent': change_percent,
                    'volume': int(info.get('volume', 0)),
                    'open': Decimal(str(info.get('open', 0))),
                    'high': Decimal(str(info.get('dayHigh', 0))),
                    'low': Decimal(str(info.get('dayLow', 0))),
                    'previousClose': previous_close,
                    'timestamp': timezone.now()
                }
            
            # Cache for 1 minute
            cache.set(cache_key, quote_data, 60)
            return quote_data
            
        except Exception as e:
            logger.error(f"Error fetching real-time quote for {symbol}: {e}")
            return None
        

    def fetch_historical_data(self, symbol, period='1y', interval='1d'):
        """
        Fetch historical data - NO RATE LIMITS
        
        period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
        interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
        """
        cache_key = f"historical_{symbol}_{period}_{interval}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)
            
            if hist.empty:
                return None
            
            historical_data = []
            for index, row in hist.iterrows():
                historical_data.append({
                    'date': index.date() if interval in ['1d', '5d', '1wk', '1mo', '3mo'] else index,
                    'open': Decimal(str(row['Open'])),
                    'high': Decimal(str(row['High'])),
                    'low': Decimal(str(row['Low'])),
                    'close': Decimal(str(row['Close'])),
                    'volume': int(row['Volume'])
                })
            
            # Cache for 1 hour
            cache.set(cache_key, historical_data, 3600)
            return historical_data
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None
        

    def fetch_company_overview(self, symbol):
        """Fetch company overview - NO RATE LIMITS"""
        cache_key = f"company_overview_{symbol}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info:
                return None
            
            overview = {
                'symbol': symbol,
                'name': info.get('longName', info.get('shortName', symbol)),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'marketCap': info.get('marketCap'),
                'description': info.get('longBusinessSummary', ''),
                'exchange': info.get('exchange', 'NASDAQ'),
                'website': info.get('website', ''),
                'employees': info.get('fullTimeEmployees'),
                'city': info.get('city', ''),
                'state': info.get('state', ''),
                'country': info.get('country', ''),
                'peRatio': info.get('trailingPE'),
                'forwardPE': info.get('forwardPE'),
                'dividendYield': info.get('dividendYield'),
                'beta': info.get('beta'),
                'week52High': info.get('fiftyTwoWeekHigh'),
                'week52Low': info.get('fiftyTwoWeekLow'),
                'averageVolume': info.get('averageVolume'),
            }
            
            # Cache for 24 hours
            cache.set(cache_key, overview, 86400)
            return overview
            
        except Exception as e:
            logger.error(f"Error fetching company overview for {symbol}: {e}")
            return None
        
    
    def fetch_multiple_quotes(self, symbols):
        """Fetch multiple quotes at once - VERY FAST with yfinance"""
        try:
            # Join symbols with space
            tickers = yf.Tickers(' '.join(symbols))
            
            results = {}
            for symbol in symbols:
                try:
                    ticker = tickers.tickers[symbol]
                    info = ticker.info
                    
                    if info and 'currentPrice' in info:
                        current_price = Decimal(str(info.get('currentPrice', 0)))
                        previous_close = Decimal(str(info.get('previousClose', 0)))
                        change = current_price - previous_close
                        change_percent = (change / previous_close * 100) if previous_close > 0 else 0
                        
                        results[symbol] = {
                            'symbol': symbol,
                            'price': current_price,
                            'change': change,
                            'changePercent': change_percent,
                            'volume': int(info.get('volume', 0)),
                        }
                except Exception as e:
                    logger.error(f"Error fetching quote for {symbol}: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Error fetching multiple quotes: {e}")
            return {}
    
    def save_stock_price(self, symbol, price_data):
        """Save stock price to database"""
        try:
            stock, created = Stock.objects.get_or_create(
                symbol=symbol,
                defaults={'name': symbol}
            )
            
            StockPrice.objects.update_or_create(
                stock=stock,
                timestamp=price_data['timestamp'],
                defaults={
                    'open': price_data.get('open', price_data['price']),
                    'high': price_data.get('high', price_data['price']),
                    'low': price_data.get('low', price_data['price']),
                    'close': price_data['price'],
                    'volume': price_data.get('volume', 0)
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving stock price for {symbol}: {e}")
            return False
        

    def search_symbol(self, query):
        """Search for stock symbols by company name"""
        # Note: yfinance doesn't have built-in search
        # You can use a predefined list or integrate with another API
        # For now, return empty list
        logger.warning("Symbol search not implemented with yfinance")
        return []