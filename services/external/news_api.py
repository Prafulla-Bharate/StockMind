
import requests
import logging
from datetime import datetime, timedelta
from django.conf import settings
from apps.market.models import NewsArticle, Stock

logger = logging.getLogger(__name__)

class NewsAPIService:
    """Fetch news from NewsAPI"""
    
    def __init__(self):
        self.api_key = settings.NEWSAPI_KEY
        self.base_url = "https://newsapi.org/v2/everything"
    
    def fetch_news(self, symbol, company_name=None, days_back=7):
        """Fetch news articles for a stock"""
        try:
            # Prepare query
            query = f"{symbol} OR {company_name}" if company_name else symbol
            
            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            params = {
                'q': query,
                'from': from_date,
                'sortBy': 'publishedAt',
                'language': 'en',
                'apiKey': self.api_key,
                'pageSize': 20
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'ok':
                articles = []
                stock = Stock.objects.get(symbol=symbol)
                
                for article in data['articles']:
                    try:
                        # Check if article already exists
                        if NewsArticle.objects.filter(url=article['url']).exists():
                            continue
                        
                        news_article = NewsArticle.objects.create(
                            stock=stock,
                            title=article['title'],
                            description=article.get('description', ''),
                            content=article.get('content', ''),
                            url=article['url'],
                            url_to_image=article.get('urlToImage'),
                            source=article['source']['name'],
                            author=article.get('author', ''),
                            published_at=datetime.fromisoformat(
                                article['publishedAt'].replace('Z', '+00:00')
                            )
                        )
                        articles.append(news_article)
                        
                    except Exception as e:
                        logger.error(f"Error saving article: {e}")
                        continue
                
                return articles
            
            return []
            
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
            return []
