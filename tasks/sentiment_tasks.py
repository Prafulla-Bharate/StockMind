from celery import shared_task
from celery.utils.log import get_task_logger
from apps.market.models import Stock, NewsArticle, Sentiment
from services.external.news_api import NewsAPIService
from services.external.gemini_api import GeminiSentimentAnalyzer

logger = get_task_logger(__name__)

@shared_task(bind=True, max_retries=3)
def fetch_and_analyze_news(self, symbols=None):
    """Fetch news and analyze sentiment"""
    try:
        if symbols is None:
            # Get active stocks
            symbols = list(Stock.objects.filter(is_active=True)[:50].values_list('symbol', flat=True))
        
        news_service = NewsAPIService()
        sentiment_analyzer = GeminiSentimentAnalyzer()
        
        for symbol in symbols:
            try:
                # Fetch news
                articles = news_service.fetch_news(symbol)
                
                # Analyze sentiment for each article
                for article in articles:
                    try:
                        sentiment_result = sentiment_analyzer.analyze_article(
                            article.title,
                            article.description
                        )
                        
                        if sentiment_result:
                            # Save sentiment
                            Sentiment.objects.create(
                                stock=article.stock,
                                news_article=article,
                                ai_sentiment=sentiment_result['sentiment'],
                                ai_score=sentiment_result['score'],
                                analysis=sentiment_result['analysis'],
                                overall_sentiment=sentiment_result['sentiment'],
                                overall_score=sentiment_result['score'],
                                total_articles=1
                            )
                    
                    except Exception as e:
                        logger.error(f"Error analyzing article sentiment: {e}")
                        continue
                
                logger.info(f"Processed news for {symbol}")
            
            except Exception as e:
                logger.error(f"Error processing news for {symbol}: {e}")
                continue
        
        return f"Processed news for {len(symbols)} stocks"
    
    except Exception as exc:
        logger.error(f"Task failed: {exc}")
        raise self.retry(exc=exc, countdown=60)

@shared_task(bind=True)
def aggregate_sentiment(self, symbol):
    """Aggregate sentiment from multiple articles"""
    try:
        stock = Stock.objects.get(symbol=symbol)
        
        # Get recent sentiments (last 7 days)
        from datetime import datetime, timedelta
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        sentiments = Sentiment.objects.filter(
            stock=stock,
            timestamp__gte=seven_days_ago
        )
        
        if not sentiments.exists():
            return f"No sentiments found for {symbol}"
        
        # Calculate aggregate
        total_score = sum(s.ai_score for s in sentiments)
        avg_score = total_score / sentiments.count()
        
        bullish = sentiments.filter(ai_sentiment='positive').count()
        neutral = sentiments.filter(ai_sentiment='neutral').count()
        bearish = sentiments.filter(ai_sentiment='negative').count()
        
        # Determine overall sentiment
        if avg_score > 0.2:
            overall = 'positive'
        elif avg_score < -0.2:
            overall = 'negative'
        else:
            overall = 'neutral'
        
        # Create aggregate sentiment
        Sentiment.objects.create(
            stock=stock,
            ai_sentiment=overall,
            ai_score=avg_score,
            analysis=f"Aggregate sentiment from {sentiments.count()} articles over the past week.",
            overall_sentiment=overall,
            overall_score=avg_score,
            bullish_count=bullish,
            neutral_count=neutral,
            bearish_count=bearish,
            total_articles=sentiments.count()
        )
        
        return f"Aggregated sentiment for {symbol}"
    
    except Exception as exc:
        logger.error(f"Task failed: {exc}")
        raise exc
