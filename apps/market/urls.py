from django.urls import path
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
    # Stock data
    path('stock/<str:symbol>/', StockDetailView.as_view(), name='stock-detail'),
    
    # Market scanner
    path('scanner/', MarketScannerView.as_view(), name='market-scanner'),
    
    # News and sentiment
    path('news/', NewsView.as_view(), name='news'),
    path('sentiment/<str:symbol>/', SentimentView.as_view(), name='sentiment'),
    
    # Predictions
    path('ai-prediction/', AIPredictionView.as_view(), name='ai-prediction'),
    path('statistical-prediction/', StatisticalPredictionView.as_view(), name='statistical-prediction'),
]
