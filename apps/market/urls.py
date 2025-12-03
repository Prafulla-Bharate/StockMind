from django.urls import path, re_path
from .views import (
    StockDetailView,
    MarketScannerView,
    NewsView,
    SentimentView,
    AIPredictionView,
    StatisticalPredictionView
)

app_name = 'market'

urlpatterns = [
        # Simple index for the market API root
        path('', lambda request: __import__('django.http').http.HttpResponse(
                """
                <html>
                    <head><title>Market API</title></head>
                    <body>
                        <h1>Market API</h1>
                        <ul>
                            <li><a href='stock/'>Stock detail (append symbol)</a></li>
                            <li><a href='scanner/'>Market scanner</a></li>
                            <li><a href='news/'>News</a></li>
                            <li><a href='ai-prediction/'>AI prediction</a></li>
                        </ul>
                    </body>
                </html>
                """
        )),
    # Stock data
    path('stock/<str:symbol>/', StockDetailView.as_view(), name='stock-detail'),
    re_path(r'^stock/(?P<symbol>[^/]+)/?$', StockDetailView.as_view(), name='stock-detail-noslash'),
    
    # Market scanner
    path('scanner/', MarketScannerView.as_view(), name='market-scanner'),
    re_path(r'^scanner/?$', MarketScannerView.as_view(), name='market-scanner-noslash'),
    
    # News and sentiment
    path('news/', NewsView.as_view(), name='news'),
    re_path(r'^news/?$', NewsView.as_view(), name='news-noslash'),
    path('sentiment/<str:symbol>/', SentimentView.as_view(), name='sentiment'),
    re_path(r'^sentiment/(?P<symbol>[^/]+)/?$', SentimentView.as_view(), name='sentiment-noslash'),
    
    # Predictions
    path('ai-prediction/', AIPredictionView.as_view(), name='ai-prediction'),
    re_path(r'^ai-prediction/?$', AIPredictionView.as_view(), name='ai-prediction-noslash'),
    path('statistical-prediction/', StatisticalPredictionView.as_view(), name='statistical-prediction'),
    re_path(r'^statistical-prediction/?$', StatisticalPredictionView.as_view(), name='statistical-prediction-noslash'),
]
