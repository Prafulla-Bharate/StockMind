# ============================================================================
# FILE: apps/market/admin.py
# ============================================================================
from django.contrib import admin
from .models import (
    Stock, StockPrice, TechnicalIndicator, 
    MarketScanResult, NewsArticle, Sentiment, StockPrediction
)

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'name', 'sector', 'industry', 'market_cap', 'is_active', 'last_updated']
    list_filter = ['sector', 'industry', 'is_active', 'exchange']
    search_fields = ['symbol', 'name', 'sector', 'industry']
    readonly_fields = ['last_updated']
    ordering = ['symbol']

@admin.register(StockPrice)
class StockPriceAdmin(admin.ModelAdmin):
    list_display = ['stock', 'timestamp', 'open', 'high', 'low', 'close', 'volume']
    list_filter = ['timestamp', 'stock']
    search_fields = ['stock__symbol', 'stock__name']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']

@admin.register(TechnicalIndicator)
class TechnicalIndicatorAdmin(admin.ModelAdmin):
    list_display = ['stock', 'timestamp', 'rsi_14', 'sma_20', 'sma_50', 'macd']
    list_filter = ['timestamp', 'stock']
    search_fields = ['stock__symbol']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']

@admin.register(MarketScanResult)
class MarketScanResultAdmin(admin.ModelAdmin):
    list_display = ['stock', 'timeframe', 'price', 'change_percent', 'volume_ratio', 'trend', 'timestamp']
    list_filter = ['timeframe', 'trend', 'is_unusual_volume', 'is_breakout', 'timestamp']
    search_fields = ['stock__symbol', 'stock__name']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']

@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ['stock', 'title', 'source', 'published_at', 'fetched_at']
    list_filter = ['source', 'published_at', 'fetched_at']
    search_fields = ['stock__symbol', 'title', 'description']
    date_hierarchy = 'published_at'
    ordering = ['-published_at']
    readonly_fields = ['fetched_at']

@admin.register(Sentiment)
class SentimentAdmin(admin.ModelAdmin):
    list_display = ['stock', 'overall_sentiment', 'overall_score', 'total_articles', 'timestamp']
    list_filter = ['overall_sentiment', 'ai_sentiment', 'timestamp']
    search_fields = ['stock__symbol', 'analysis']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']

@admin.register(StockPrediction)
class StockPredictionAdmin(admin.ModelAdmin):
    list_display = ['stock', 'current_price', 'short_term_target', 'bullish_score', 'overall_sentiment', 'timestamp']
    list_filter = ['overall_sentiment', 'risk_level', 'timestamp']
    search_fields = ['stock__symbol']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    readonly_fields = ['timestamp']