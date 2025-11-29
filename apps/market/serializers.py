from rest_framework import serializers
from .models import (
    Stock, StockPrice, TechnicalIndicator, 
    MarketScanResult, NewsArticle, Sentiment, StockPrediction
)

class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = '__all__'

class StockPriceSerializer(serializers.ModelSerializer):
    change = serializers.DecimalField(max_digits=10, decimal_places=4, read_only=True)
    change_percent = serializers.DecimalField(max_digits=8, decimal_places=4, read_only=True)
    
    class Meta:
        model = StockPrice
        fields = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'change', 'change_percent']

class TechnicalIndicatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnicalIndicator
        exclude = ['id', 'stock']

class MarketScanResultSerializer(serializers.ModelSerializer):
    symbol = serializers.CharField(source='stock.symbol')
    name = serializers.CharField(source='stock.name')
    
    class Meta:
        model = MarketScanResult
        fields = [
            'symbol', 'name', 'price', 'change', 'change_percent',
            'volume', 'avg_volume', 'volume_ratio', 'trend',
            'is_unusual_volume', 'is_breakout', 'resistance', 'support'
        ]

class NewsArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsArticle
        fields = [
            'id', 'title', 'description', 'url', 'url_to_image',
            'source', 'author', 'published_at'
        ]

class SentimentSerializer(serializers.ModelSerializer):
    sentiment = serializers.CharField(source='overall_sentiment')
    sentiment_score = serializers.FloatField(source='overall_score')
    
    class Meta:
        model = Sentiment
        fields = [
            'sentiment', 'sentiment_score', 'analysis', 
            'timestamp', 'confidence', 'bullish_count', 
            'neutral_count', 'bearish_count', 'total_articles'
        ]

class StockPredictionSerializer(serializers.ModelSerializer):
    predictions = serializers.SerializerMethodField()
    
    class Meta:
        model = StockPrediction
        fields = [
            'symbol', 'timestamp', 'current_price', 'predictions',
            'bullish_score', 'risk_level', 'overall_sentiment'
        ]
    
    def get_predictions(self, obj):
        return {
            'shortTerm': {
                'period': '1 week',
                'targetPrice': float(obj.short_term_target),
                'change': float(obj.short_term_change),
                'confidence': obj.short_term_confidence,
                'trend': obj.short_term_trend,
            },
            'mediumTerm': {
                'period': '1 month',
                'targetPrice': float(obj.medium_term_target),
                'change': float(obj.medium_term_change),
                'confidence': obj.medium_term_confidence,
                'trend': obj.medium_term_trend,
            },
            'longTerm': {
                'period': '3 months',
                'targetPrice': float(obj.long_term_target),
                'change': float(obj.long_term_change),
                'confidence': obj.long_term_confidence,
                'trend': obj.long_term_trend,
            }
        }