
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
        # Prefer reputable finance/business domains to avoid unrelated results
        default_domains = [
            'reuters.com', 'bloomberg.com', 'wsj.com', 'finance.yahoo.com',
            'marketwatch.com', 'seekingalpha.com', 'cnbc.com', 'investors.com',
            'financialpost.com', 'barrons.com', 'fool.com', 'investopedia.com',
            'nasdaq.com', 'thestreet.com'
        ]
        self.domains = getattr(settings, 'NEWSAPI_DOMAINS', default_domains)
        self.exclude_domains = getattr(settings, 'NEWSAPI_EXCLUDE_DOMAINS', [
            'gofugyourself.com', 'animenewsnetwork.com', 'people.com', 'tmz.com'
        ])
    
    def fetch_news(self, symbol, company_name=None, days_back=7):
        """Fetch news articles for a stock with stricter relevance filtering."""
        try:
            # Build a more specific query to reduce unrelated articles
            keywords = [symbol]
            if company_name:
                keywords.append(company_name)
                # Also include the first word (e.g., "Apple" from "Apple Inc.")
                first = company_name.split()[0]
                if first and first not in keywords:
                    keywords.append(first)
            keywords.append(f"{symbol} stock")
            keywords.append(f"{symbol} shares")
            query = " OR ".join([f'{k}' for k in keywords])

            from django.utils import timezone
            from_date = (timezone.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            params = {
                'q': query,
                'from': from_date,
                'searchIn': 'title,description',
                'sortBy': 'relevancy',
                'language': 'en',
                'apiKey': self.api_key,
                'pageSize': 20,
                'domains': ','.join(self.domains),
                'excludeDomains': ','.join(self.exclude_domains)
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'ok':
                articles = []
                stock = Stock.objects.get(symbol=symbol)
                
                for article in data['articles']:
                    try:
                        # Drop unrelated pieces by checking content locally
                        text = " ".join([
                            article.get('title', ''),
                            article.get('description', ''),
                            article.get('content', '')
                        ]).lower()

                        relevant_terms = [symbol.lower()]
                        if company_name:
                            relevant_terms.append(company_name.lower())
                            first = company_name.split()[0].lower()
                            if first and first not in relevant_terms:
                                relevant_terms.append(first)
                        relevant_terms.append(f"{symbol.lower()} stock")
                        relevant_terms.append(f"{symbol.lower()} shares")

                        finance_context_terms = [
                            'stock', 'shares', 'earnings', 'revenue', 'guidance', 'market',
                            'analyst', 'target', 'downgrade', 'upgrade', 'price', 'profit',
                            'loss', 'quarter', 'dividend'
                        ]

                        if not any(term in text for term in relevant_terms):
                            # If the site isn't in the preferred finance domains, skip
                            domain = (article.get('source') or {}).get('name', '')
                            url = article.get('url', '')
                            domain_in_url = url.split('/')[2] if '://' in url else ''
                            if not any(d in domain_in_url for d in self.domains):
                                continue
                            # Even for preferred domains, require finance context
                            if not any(t in text for t in finance_context_terms):
                                continue
                            continue

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
                            author=article.get('author') or '',  # prevent NULL constraint errors
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
