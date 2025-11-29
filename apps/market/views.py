from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from django.db.models import Avg
from datetime import datetime, timedelta
import pandas as pd
from decimal import Decimal

from .models import (
    Stock, StockPrice, TechnicalIndicator, 
    MarketScanResult, NewsArticle, Sentiment, StockPrediction
)
from .serializers import (
    StockSerializer, StockPriceSerializer, TechnicalIndicatorSerializer,
    MarketScanResultSerializer, NewsArticleSerializer, 
    SentimentSerializer, StockPredictionSerializer
)
from services.market_data.fetcher import MarketDataFetcher
from services.market_data.indicators import TechnicalIndicatorCalculator
from services.external.news_api import NewsAPIService
from services.external.gemini_api import GeminiSentimentAnalyzer
from services.ml.lstm_predictor import LSTMPredictor
from utils.responses import success_response, error_response

class StockDetailView(APIView):
    """Get detailed stock information"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, symbol):
        """GET /api/market/stock/{symbol}"""
        # Check cache first
        cache_key = f"stock_detail_{symbol}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(success_response(data=cached_data))
        
        try:
            # Get or create stock
            stock, created = Stock.objects.get_or_create(
                symbol=symbol.upper(),
                defaults={'name': symbol.upper()}
            )
            
            # If newly created, fetch data
            if created:
                fetcher = MarketDataFetcher()
                overview = fetcher.fetch_company_overview(symbol)
                if overview:
                    stock.name = overview['name']
                    stock.sector = overview['sector']
                    stock.industry = overview['industry']
                    stock.market_cap = overview['marketCap']
                    stock.save()
            
            # Get latest price
            latest_price = StockPrice.objects.filter(stock=stock).order_by('-timestamp').first()
            
            if not latest_price:
                # Fetch real-time data
                fetcher = MarketDataFetcher()
                quote = fetcher.fetch_real_time_quote(symbol)
                if quote:
                    fetcher.save_stock_price(symbol, quote)
                    latest_price = StockPrice.objects.filter(stock=stock).order_by('-timestamp').first()
            
            # Get historical data (last 200 candles)
            historical = StockPrice.objects.filter(
                stock=stock
            ).order_by('-timestamp')[:200]
            historical_data = [
                {
                    'date': price.timestamp.isoformat(),
                    'open': float(price.open),
                    'high': float(price.high),
                    'low': float(price.low),
                    'close': float(price.close),
                    'volume': price.volume
                }
                for price in reversed(list(historical))
            ]
            
            # Get latest indicators
            latest_indicator = TechnicalIndicator.objects.filter(
                stock=stock
            ).order_by('-timestamp').first()
            
            indicators = {}
            if latest_indicator:
                indicators = {
                    'rsi': latest_indicator.rsi_14,
                    'macd': latest_indicator.macd,
                    'sma20': latest_indicator.sma_20,
                    'sma50': latest_indicator.sma_50,
                }
            
            # Calculate 52-week high/low
            year_ago = datetime.now() - timedelta(days=365)
            year_prices = StockPrice.objects.filter(
                stock=stock,
                timestamp__gte=year_ago
            )
            
            high_52w = 0
            low_52w = 0
            if year_prices.exists():
                high_52w = float(year_prices.order_by('-high').first().high)
                low_52w = float(year_prices.order_by('low').first().low)
            
            # Prepare response
            data = {
                'symbol': stock.symbol,
                'name': stock.name,
                'price': float(latest_price.close) if latest_price else 0,
                'change': float(latest_price.change) if latest_price else 0,
                'changePercent': float(latest_price.change_percent) if latest_price else 0,
                'volume': latest_price.volume if latest_price else 0,
                'marketCap': stock.market_cap,
                'high52w': high_52w,
                'low52w': low_52w,
                'historicalData': historical_data,
                'indicators': indicators
            }
            
            # Cache for 5 minutes
            cache.set(cache_key, data, 300)
            
            return Response(success_response(data=data))
            
        except Exception as e:
            return Response(
                error_response(message=f"Error fetching stock data: {str(e)}"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class MarketScannerView(APIView):
    """Market scanner for gainers, losers, etc."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """GET /api/market/scanner?timeframe=daily"""
        timeframe = request.query_params.get('timeframe', 'daily')
        
        # Check cache
        cache_key = f"market_scanner_{timeframe}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(success_response(data=cached_data))
        
        try:
            # Get latest scan timestamp
            latest = MarketScanResult.objects.filter(
                timeframe=timeframe
            ).order_by('-timestamp').first()
            
            if not latest:
                return Response(
                    error_response(message='No scan results available'),
                    status=status.HTTP_404_NOT_FOUND
                )
            
            timestamp = latest.timestamp
            results = MarketScanResult.objects.filter(
                timeframe=timeframe,
                timestamp=timestamp
            ).select_related('stock')
            
            # Separate by categories
            gainers = results.filter(is_gainer=True).order_by('-change_percent')[:10]
            losers = results.filter(is_loser=True).order_by('change_percent')[:10]
            most_active = results.order_by('-volume')[:10]
            unusual_volume = results.filter(is_unusual_volume=True).order_by('-volume_ratio')[:10]
            breakouts = results.filter(is_breakout=True).order_by('-change_percent')[:10]
            
            # Calculate market overview
            total_scanned = results.count()
            bullish_count = results.filter(trend='Bullish').count()
            bearish_count = results.filter(trend='Bearish').count()
            avg_change = results.aggregate(Avg('change_percent'))['change_percent__avg'] or 0
            
            data = {
                'timeframe': timeframe,
                'timestamp': timestamp.isoformat(),
                'gainers': MarketScanResultSerializer(gainers, many=True).data,
                'losers': MarketScanResultSerializer(losers, many=True).data,
                'mostActive': MarketScanResultSerializer(most_active, many=True).data,
                'unusualVolume': MarketScanResultSerializer(unusual_volume, many=True).data,
                'breakouts': MarketScanResultSerializer(breakouts, many=True).data,
                'marketOverview': {
                    'totalScanned': total_scanned,
                    'bullish': bullish_count,
                    'bearish': bearish_count,
                    'avgChange': float(avg_change)
                }
            }
            
            # Cache for 10 minutes
            cache.set(cache_key, data, 600)
            
            return Response(success_response(data=data))
            
        except Exception as e:
            return Response(
                error_response(message=f"Error fetching scanner data: {str(e)}"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class NewsView(APIView):
    """Get news articles with sentiment"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """GET /api/market/news?symbol=AAPL&companyName=Apple"""
        symbol = request.query_params.get('symbol')
        company_name = request.query_params.get('companyName')
        
        if not symbol:
            return Response(
                error_response(message='Symbol parameter is required'),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            stock = Stock.objects.get(symbol=symbol.upper())
            
            # Get recent news (last 7 days)
            seven_days_ago = datetime.now() - timedelta(days=7)
            news_articles = NewsArticle.objects.filter(
                stock=stock,
                published_at__gte=seven_days_ago
            ).order_by('-published_at')[:20]
            
            # If no news in DB, fetch from API
            if not news_articles.exists():
                news_service = NewsAPIService()
                articles = news_service.fetch_news(symbol, company_name)
                news_articles = NewsArticle.objects.filter(
                    stock=stock,
                    published_at__gte=seven_days_ago
                ).order_by('-published_at')[:20]
            
            # Get sentiment for each article
            news_with_sentiment = []
            total_score = 0
            bullish = 0
            neutral = 0
            bearish = 0
            
            for article in news_articles:
                sentiment_obj = Sentiment.objects.filter(
                    news_article=article
                ).first()
                
                article_data = NewsArticleSerializer(article).data
                
                if sentiment_obj:
                    article_data['sentiment'] = {
                        'score': sentiment_obj.ai_score,
                        'label': sentiment_obj.ai_sentiment,
                        'explanation': sentiment_obj.analysis
                    }
                    
                    total_score += sentiment_obj.ai_score
                    if sentiment_obj.ai_sentiment == 'positive':
                        bullish += 1
                    elif sentiment_obj.ai_sentiment == 'negative':
                        bearish += 1
                    else:
                        neutral += 1
                
                news_with_sentiment.append(article_data)
            
            # Calculate overall sentiment
            total_articles = len(news_with_sentiment)
            avg_score = total_score / total_articles if total_articles > 0 else 0
            
            if avg_score > 0.2:
                overall_sentiment = 'Positive'
            elif avg_score < -0.2:
                overall_sentiment = 'Negative'
            else:
                overall_sentiment = 'Neutral'
            
            data = {
                'news': news_with_sentiment,
                'overallSentiment': {
                    'score': avg_score,
                    'label': overall_sentiment,
                    'totalArticles': total_articles,
                    'bullish': bullish,
                    'neutral': neutral,
                    'bearish': bearish
                }
            }
            
            return Response(success_response(data=data))
            
        except Stock.DoesNotExist:
            return Response(
                error_response(message='Stock not found'),
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                error_response(message=f"Error fetching news: {str(e)}"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SentimentView(APIView):
    """Get sentiment analysis for a stock"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, symbol):
        """GET /api/market/sentiment/{symbol}"""
        try:
            stock = Stock.objects.get(symbol=symbol.upper())
            
            # Get latest sentiment
            sentiment = Sentiment.objects.filter(
                stock=stock
            ).order_by('-timestamp').first()
            
            if not sentiment:
                return Response(
                    error_response(message='No sentiment data available'),
                    status=status.HTTP_404_NOT_FOUND
                )
            
            data = {
                'sentiment': sentiment.overall_sentiment,
                'sentimentScore': sentiment.overall_score,
                'analysis': sentiment.analysis,
                'timestamp': sentiment.timestamp.isoformat()
            }
            
            return Response(success_response(data=data))
            
        except Stock.DoesNotExist:
            return Response(
                error_response(message='Stock not found'),
                status=status.HTTP_404_NOT_FOUND
            )

class AIPredictionView(APIView):
    """AI-based stock prediction using LSTM"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """POST /api/market/ai-prediction"""
        symbol = request.data.get('symbol')
        historical_data = request.data.get('historicalData', [])
        
        if not symbol:
            return Response(
                error_response(message='Symbol is required'),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Convert historical data to DataFrame
            if historical_data:
                df = pd.DataFrame(historical_data)
            else:
                # Fetch from database
                stock = Stock.objects.get(symbol=symbol.upper())
                prices = StockPrice.objects.filter(stock=stock).order_by('timestamp')[:500]
                df = pd.DataFrame(list(prices.values(
                    'timestamp', 'open', 'high', 'low', 'close', 'volume'
                )))
            
            if len(df) < 100:
                return Response(
                    error_response(message='Not enough historical data'),
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Use LSTM predictor
            predictor = LSTMPredictor()
            predictions = predictor.predict(df, steps=30)
            
            if predictions:
                prediction_text = f"Based on AI analysis, the stock is predicted to reach ${predictions[-1]:.2f} in 30 days."
            else:
                prediction_text = "Unable to generate prediction with current data."
            
            data = {
                'prediction': prediction_text
            }
            
            return Response(success_response(data=data))
            
        except Exception as e:
            return Response(
                error_response(message=f"Prediction failed: {str(e)}"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class StatisticalPredictionView(APIView):
    """Statistical prediction with technical analysis"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """POST /api/market/statistical-prediction"""
        symbol = request.data.get('symbol')
        historical_data = request.data.get('historicalData', [])
        
        if not symbol:
            return Response(
                error_response(message='Symbol is required'),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            stock = Stock.objects.get(symbol=symbol.upper())
            
            # Get latest prediction from database
            prediction = StockPrediction.objects.filter(
                stock=stock
            ).order_by('-timestamp').first()
            
            if not prediction:
                return Response(
                    error_response(message='No prediction available'),
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get latest indicators
            indicator = TechnicalIndicator.objects.filter(
                stock=stock
            ).order_by('-timestamp').first()
            
            data = {
                'symbol': stock.symbol,
                'timestamp': prediction.timestamp.isoformat(),
                'currentPrice': float(prediction.current_price),
                'technicalIndicators': {
                    'sma20': indicator.sma_20 if indicator else None,
                    'sma50': indicator.sma_50 if indicator else None,
                    'rsi': indicator.rsi_14 if indicator else None,
                    'macd': indicator.macd if indicator else None,
                    'bollingerUpper': indicator.bollinger_upper if indicator else None,
                    'bollingerLower': indicator.bollinger_lower if indicator else None,
                },
                'predictions': {
                    'shortTerm': {
                        'period': '1 week',
                        'targetPrice': float(prediction.short_term_target),
                        'change': float(prediction.short_term_change),
                        'confidence': prediction.short_term_confidence,
                        'trend': prediction.short_term_trend
                    },
                    'mediumTerm': {
                        'period': '1 month',
                        'targetPrice': float(prediction.medium_term_target),
                        'change': float(prediction.medium_term_change),
                        'confidence': prediction.medium_term_confidence,
                        'trend': prediction.medium_term_trend
                    },
                    'longTerm': {
                        'period': '3 months',
                        'targetPrice': float(prediction.long_term_target),
                        'change': float(prediction.long_term_change),
                        'confidence': prediction.long_term_confidence,
                        'trend': prediction.long_term_trend
                    }
                },
                'overallOutlook': {
                    'bullishScore': prediction.bullish_score,
                    'sentiment': prediction.overall_sentiment,
                    'riskLevel': prediction.risk_level
                }
            }
            
            return Response(success_response(data=data))
            
        except Stock.DoesNotExist:
            return Response(
                error_response(message='Stock not found'),
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                error_response(message=f"Prediction failed: {str(e)}"),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )