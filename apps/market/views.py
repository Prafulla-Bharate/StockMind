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
from textblob import TextBlob
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

            # Calculate indicators on-demand if missing or stale
            try:
                needs_calc = False
                if not latest_indicator:
                    needs_calc = True
                elif latest_price and latest_indicator.timestamp < latest_price.timestamp:
                    needs_calc = True

                if needs_calc:
                    tic = TechnicalIndicatorCalculator()
                    tic.calculate_indicators(stock.symbol)
                    latest_indicator = TechnicalIndicator.objects.filter(
                        stock=stock
                    ).order_by('-timestamp').first()
            except Exception:
                pass
            
            indicators = {}
            if latest_indicator:
                indicators = {
                    'rsi': latest_indicator.rsi_14,
                    'macd': latest_indicator.macd,
                    'sma20': latest_indicator.sma_20,
                    'sma50': latest_indicator.sma_50,
                }
            
            # Calculate 52-week high/low
            from django.utils import timezone
            year_ago = timezone.now() - timedelta(days=365)
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
            
            quick_analyzed = 0
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
                else:
                    # Fast local sentiment for first few articles to keep endpoint snappy
                    try:
                        if quick_analyzed < 5:  # cap per request
                            text = f"{article.title} {article.description}"
                            polarity = TextBlob(text).sentiment.polarity
                            if polarity > 0.1:
                                lbl = 'positive'
                            elif polarity < -0.1:
                                lbl = 'negative'
                            else:
                                lbl = 'neutral'

                            Sentiment.objects.create(
                                stock=stock,
                                news_article=article,
                                ai_sentiment=lbl,
                                ai_score=float(polarity),
                                analysis='Quick local sentiment (TextBlob).',
                                overall_sentiment=lbl,
                                overall_score=float(polarity),
                                total_articles=1
                            )
                            article_data['sentiment'] = {
                                'score': float(polarity),
                                'label': lbl,
                                'explanation': 'Quick local sentiment (TextBlob).'
                            }
                            total_score += float(polarity)
                            if lbl == 'positive':
                                bullish += 1
                            elif lbl == 'negative':
                                bearish += 1
                            else:
                                neutral += 1
                            quick_analyzed += 1
                        else:
                            article_data['sentiment'] = {
                                'score': 0,
                                'label': 'neutral',
                                'explanation': 'Sentiment not available yet.'
                            }
                    except Exception:
                        article_data['sentiment'] = {
                            'score': 0,
                            'label': 'neutral',
                            'explanation': 'Sentiment not available yet.'
                        }
                
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
                # Return neutral fallback instead of 404 to avoid frontend crashes
                data = {
                    'sentiment': 'Neutral',
                    'sentimentScore': 0,
                    'analysis': 'Sentiment data not available yet; defaulting to neutral.',
                    'timestamp': datetime.now().isoformat()
                }
                return Response(success_response(data=data))
            
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
    
    def get(self, request):
        """GET /api/market/ai-prediction - Returns API documentation"""
        return Response({
            'endpoint': '/api/market/ai-prediction/',
            'method': 'POST',
            'description': 'Generate AI-based stock price predictions using LSTM model',
            'authentication': 'JWT Bearer Token required',
            'request_body': {
                'symbol': {
                    'type': 'string',
                    'required': True,
                    'description': 'Stock symbol (e.g., AAPL, MSFT, GOOGL)',
                    'example': 'AAPL'
                },
                'historicalData': {
                    'type': 'array',
                    'required': False,
                    'description': 'Optional historical price data. If not provided, data will be fetched from database',
                    'example': []
                }
            },
            'example_request': {
                'symbol': 'AAPL',
                'historicalData': []
            },
            'response': {
                'success': True,
                'data': {
                    'prediction': 'Based on AI analysis, the stock is predicted to reach $150.25 in 30 days.'
                }
            }
        })
    
    def post(self, request):
        """POST /api/market/ai-prediction"""
        import logging
        logger = logging.getLogger(__name__)
        
        # Log incoming request data for debugging
        logger.info(f"AI Prediction Request - Data: {request.data}")
        logger.info(f"AI Prediction Request - Content Type: {request.content_type}")
        
        symbol = request.data.get('symbol')
        historical_data = request.data.get('historicalData', [])
        
        logger.info(f"Extracted symbol: {symbol}, historical_data length: {len(historical_data) if historical_data else 0}")
        
        if not symbol:
            logger.warning(f"Missing symbol in request. Full request data: {request.data}")
            return Response(
                error_response(
                    message='Symbol is required. Please provide a stock symbol in the request body.',
                    errors={'symbol': ['This field is required']}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Convert historical data to DataFrame
            if historical_data:
                logger.info(f"Using provided historical data: {len(historical_data)} records")
                df = pd.DataFrame(historical_data)
            else:
                # Fetch from database first
                logger.info(f"Fetching historical data from database for symbol: {symbol.upper()}")
                stock, created = Stock.objects.get_or_create(
                    symbol=symbol.upper(),
                    defaults={'name': symbol.upper()}
                )
                prices = StockPrice.objects.filter(stock=stock).order_by('timestamp')[:500]
                price_list = list(prices.values('timestamp', 'open', 'high', 'low', 'close', 'volume'))
                logger.info(f"Fetched {len(price_list)} price records from database")
                
                # If not enough data in DB, fetch from yfinance
                if len(price_list) < 100:
                    logger.info(f"Not enough data in DB, fetching from yfinance...")
                    from services.market_data.fetcher import MarketDataFetcher
                    fetcher = MarketDataFetcher()
                    historical = fetcher.fetch_historical_data(symbol, period='1y', interval='1d')
                    
                    if historical:
                        logger.info(f"Fetched {len(historical)} records from yfinance")
                        # Convert to DataFrame format
                        df = pd.DataFrame([{
                            'timestamp': item['date'],
                            'open': float(item['open']),
                            'high': float(item['high']),
                            'low': float(item['low']),
                            'close': float(item['close']),
                            'volume': item['volume']
                        } for item in historical])
                    else:
                        df = pd.DataFrame(price_list)
                else:
                    df = pd.DataFrame(price_list)
            
            logger.info(f"DataFrame length: {len(df)}, Required: 100")
            
            if len(df) < 100:
                logger.warning(f"Insufficient data: {len(df)} records found, 100 required")
                return Response(
                    error_response(
                        message=f'Not enough historical data. Found {len(df)} records, need at least 100 for AI prediction. The stock may be newly listed or have insufficient trading history.',
                        errors={'data': [f'Only {len(df)} historical price points available']}
                    ),
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
    
    def get(self, request):
        """GET /api/market/statistical-prediction - Returns API documentation"""
        return Response({
            'endpoint': '/api/market/statistical-prediction/',
            'method': 'POST',
            'description': 'Get statistical ML predictions for a stock based on historical data',
            'authentication': 'JWT Bearer Token required',
            'request_body': {
                'symbol': {
                    'type': 'string',
                    'required': True,
                    'description': 'Stock symbol (e.g., AAPL, MSFT)',
                    'example': 'AAPL'
                },
                'historicalData': {
                    'type': 'array',
                    'required': False,
                    'description': 'Optional historical price data'
                }
            },
            'response': {
                'success': True,
                'data': {
                    'symbol': 'AAPL',
                    'timestamp': '2025-12-23T10:00:00Z',
                    'currentPrice': 250.50,
                    'technicalIndicators': {
                        'sma20': 245.30,
                        'sma50': 240.10,
                        'rsi': 65.5,
                        'macd': 2.15
                    },
                    'predictions': {
                        'shortTerm': {...},
                        'mediumTerm': {...},
                        'longTerm': {...}
                    }
                }
            }
        })
    
    def post(self, request):
        """POST /api/market/statistical-prediction"""
        import logging
        logger = logging.getLogger(__name__)
        
        symbol = request.data.get('symbol')
        historical_data = request.data.get('historicalData', [])
        
        logger.info(f"Statistical Prediction Request - Symbol: {symbol}")
        
        if not symbol:
            logger.warning(f"Missing symbol in statistical prediction request")
            return Response(
                error_response(
                    message='Symbol is required',
                    errors={'symbol': ['This field is required']}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            stock, created = Stock.objects.get_or_create(
                symbol=symbol.upper(),
                defaults={'name': symbol.upper()}
            )
            
            # Get latest prediction from database
            prediction = StockPrediction.objects.filter(
                stock=stock
            ).order_by('-timestamp').first()
            
            if not prediction:
                # No prediction exists yet - return 200 with null data instead of 404
                logger.warning(f"No prediction available for {symbol} - run update_predictions task first")
                return Response(
                    success_response(
                        data=None,
                        message=f'No prediction available for {symbol}. Predictions are generated periodically via Celery tasks. Please try again later or run: python manage.py shell -c "from tasks.prediction_tasks import update_predictions; update_predictions.delay()"'
                    ),
                    status=status.HTTP_200_OK
                )
            
            # Get latest indicators
            indicator = TechnicalIndicator.objects.filter(
                stock=stock
            ).order_by('-timestamp').first()
            
            logger.info(f"Successfully retrieved prediction for {symbol}")
            
            data = {
                'symbol': stock.symbol,
                'timestamp': prediction.timestamp.isoformat(),
                'currentPrice': float(prediction.current_price),
                'technicalIndicators': {
                    'sma20': float(indicator.sma_20) if indicator and indicator.sma_20 else None,
                    'sma50': float(indicator.sma_50) if indicator and indicator.sma_50 else None,
                    'rsi': float(indicator.rsi_14) if indicator and indicator.rsi_14 else None,
                    'macd': float(indicator.macd) if indicator and indicator.macd else None,
                    'bollingerUpper': float(indicator.bollinger_upper) if indicator and indicator.bollinger_upper else None,
                    'bollingerLower': float(indicator.bollinger_lower) if indicator and indicator.bollinger_lower else None,
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