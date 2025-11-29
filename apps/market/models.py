from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

class Stock(models.Model):

    symbol = models.CharField(max_length=10, unique=True, primary_key=True)
    name = models.CharField(max_length=255)
    sector = models.CharField(max_length=100, blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    market_cap = models.BigIntegerField(null=True, blank=True)
    exchange = models.CharField(max_length=50, blank=True, null=True)
    currency = models.CharField(max_length=10, blank=True, default='USD', null=True)
    is_active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stocks'
        indexes = [
            models.Index(fields=['symbol']),
            models.Index(fields=['sector'])
        ]

    def __str__(self):
        return f"{self.symbol} - {self.name}"
    
class StockPrice(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='prices')
    timestamp = models.DateTimeField(db_index=True)
    open = models.DecimalField(max_digits=20, decimal_places=4, validators=[MinValueValidator(Decimal('0.0001'))])
    high = models.DecimalField(max_digits=20, decimal_places=4, validators=[MinValueValidator(Decimal('0.0001'))])
    low = models.DecimalField(max_digits=20, decimal_places=4, validators=[MinValueValidator(Decimal('0.0001'))])
    close = models.DecimalField(max_digits=20, decimal_places=4, validators=[MinValueValidator(Decimal('0.0001'))])
    volume = models.BigIntegerField(validators=[MinValueValidator(0)])
    adjusted_close = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)


    class Meta:
        db_table = 'stock_prices'
        unique_together = ('stock', 'timestamp')
        indexes = [
            models.Index(fields=['stock', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.stock.symbol} - {self.timestamp} "
    
    @property
    def change(self):
        """Calculate the price change from open to close"""
        return self.close - self.open
    
    @property
    def change_percent(self):
        """Calculate the percentage change from open to close"""
        if self.open > 0:
            return (self.change / self.open) * 100
        return Decimal('0.0')
    

class TechnicalIndicator(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='indicators')
    timestamp = models.DateTimeField(db_index=True)

    sma_20 = models.FloatField(null=True, blank=True, help_text="20-day Simple Moving Average")
    sma_50 = models.FloatField(null=True, blank=True, help_text="50-day Simple Moving Average")
    sma_200 = models.FloatField(null=True, blank=True, help_text="200-day Simple Moving Average")
    ema_12 = models.FloatField(null=True, blank=True, help_text="12-day Exponential Moving Average")
    ema_26 = models.FloatField(null=True, blank=True, help_text="26-day Exponential Moving Average")

    rsi_14 = models.FloatField(null=True, blank=True, help_text="14-day Relative Strength Index")
    macd = models.FloatField(null=True, blank=True, help_text="Moving Average Convergence Divergence")
    macd_signal = models.FloatField(null=True, blank=True, help_text="MACD Signal Line")
    macd_histogram = models.FloatField(null=True, blank=True, help_text="MACD Histogram")

    bollinger_upper = models.FloatField(null=True, blank=True, help_text="Bollinger Bands Upper Band")
    bollinger_middle = models.FloatField(null=True, blank=True, help_text="Bollinger Bands Middle Band")
    bollinger_lower = models.FloatField(null=True, blank=True, help_text="Bollinger Bands Lower Band")
    atr_14 = models.FloatField(null=True, blank=True, help_text="14-day Average True Range")

    obv = models.BigIntegerField(null=True, blank=True, help_text="On-Balance Volume")

    class Meta:
        db_table = 'technical_indicators'
        unique_together = ('stock', 'timestamp')
        indexes = [
            models.Index(fields=['stock', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.stock.symbol} - {self.timestamp} "
    

class MarketScanResult(models.Model):
    TIMEFRAME_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    ]

    TREND_CHOICES = [
        ('Bullish', 'Bullish'),
        ('Bearish', 'Bearish'),
        ('Neutral', 'Neutral')
    ]

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    timeframe = models.CharField(max_length=10, choices=TIMEFRAME_CHOICES)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='scan_results')

    price = models.DecimalField(max_digits=20, decimal_places=4)
    change = models.DecimalField(max_digits=10, decimal_places=4)
    change_percent = models.DecimalField(max_digits=10, decimal_places=4)


    volume = models.BigIntegerField()
    avg_volume = models.BigIntegerField()
    volume_ratio = models.FloatField()

    is_unusual_volume = models.BooleanField(default=False)
    is_breakout = models.BooleanField(default=False)
    is_gainer = models.BooleanField(default=False)
    is_loser = models.BooleanField(default=False)

    trend = models.CharField(max_length=10, choices=TREND_CHOICES)
    resistance = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    support = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)

    class Meta:
        db_table = 'market_scan_results'
        indexes = [
            models.Index(fields=['timeframe', 'timestamp']),
            models.Index(fields=['stock', 'timeframe']),
            models.Index(fields=['is_unusual_volume']),
            models.Index(fields=['is_breakout']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.stock.symbol} - {self.timeframe} - {self.timestamp} "
    

class NewsArticle(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='news')
    title = models.CharField(max_length=500)
    description = models.TextField()
    content = models.TextField(blank=True)
    url = models.URLField(unique=True, max_length=1000)
    url_to_image = models.URLField(blank=True, null=True, max_length=1000)
    source = models.CharField(max_length=100)
    author = models.CharField(max_length=255, blank=True)
    published_at = models.DateTimeField(db_index=True)
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'news_articles'
        indexes = [
            models.Index(fields=['stock', 'published_at']),
            models.Index(fields=['published_at']),
        ]
        ordering = ['-published_at']
    
    def __str__(self):
        return f"{self.stock.symbol} - {self.title[:50]}"
    

class Sentiment(models.Model):
    """Sentiment analysis results"""
    
    SENTIMENT_CHOICES = [
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative'),
    ]
    
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='sentiments')
    news_article = models.ForeignKey(NewsArticle, on_delete=models.CASCADE, null=True, blank=True, related_name='sentiment')
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # AI Sentiment (from Gemini)
    ai_sentiment = models.CharField(max_length=20, choices=SENTIMENT_CHOICES)
    ai_score = models.FloatField(help_text='Sentiment score from -1 (negative) to 1 (positive)')
    analysis = models.TextField(help_text='Detailed sentiment analysis')
    
    # Aggregated Sentiment
    overall_sentiment = models.CharField(max_length=20, choices=SENTIMENT_CHOICES)
    overall_score = models.FloatField()
    confidence = models.FloatField(default=0.0, help_text='Confidence score 0-1')
    
    # Article Counts
    bullish_count = models.IntegerField(default=0)
    neutral_count = models.IntegerField(default=0)
    bearish_count = models.IntegerField(default=0)
    total_articles = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'sentiments'
        indexes = [
            models.Index(fields=['stock', 'timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['overall_sentiment']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.stock.symbol} - {self.overall_sentiment} - {self.timestamp}"
    

class StockPrediction(models.Model):
    """ML-based stock predictions"""
    
    CONFIDENCE_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    TREND_CHOICES = [
        ('Uptrend', 'Uptrend'),
        ('Downtrend', 'Downtrend'),
        ('Sideways', 'Sideways'),
    ]
    
    RISK_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    SENTIMENT_CHOICES = [
        ('Bullish', 'Bullish'),
        ('Bearish', 'Bearish'),
        ('Neutral', 'Neutral'),
    ]
    
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='predictions')
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    current_price = models.DecimalField(max_digits=12, decimal_places=4)
    
    # Short-term prediction (1 week)
    short_term_target = models.DecimalField(max_digits=12, decimal_places=4)
    short_term_change = models.DecimalField(max_digits=8, decimal_places=4)
    short_term_confidence = models.CharField(max_length=20, choices=CONFIDENCE_CHOICES)
    short_term_trend = models.CharField(max_length=20, choices=TREND_CHOICES)
    
    # Medium-term prediction (1 month)
    medium_term_target = models.DecimalField(max_digits=12, decimal_places=4)
    medium_term_change = models.DecimalField(max_digits=8, decimal_places=4)
    medium_term_confidence = models.CharField(max_length=20, choices=CONFIDENCE_CHOICES)
    medium_term_trend = models.CharField(max_length=20, choices=TREND_CHOICES)
    
    # Long-term prediction (3 months)
    long_term_target = models.DecimalField(max_digits=12, decimal_places=4)
    long_term_change = models.DecimalField(max_digits=8, decimal_places=4)
    long_term_confidence = models.CharField(max_length=20, choices=CONFIDENCE_CHOICES)
    long_term_trend = models.CharField(max_length=20, choices=TREND_CHOICES)
    
    # Overall analysis
    bullish_score = models.FloatField(help_text='Bullish score 0-100')
    risk_level = models.CharField(max_length=20, choices=RISK_CHOICES)
    overall_sentiment = models.CharField(max_length=20, choices=SENTIMENT_CHOICES)
    
    # Model metadata
    model_version = models.CharField(max_length=50, default='1.0')
    accuracy_score = models.FloatField(null=True, blank=True)
    
    class Meta:
        db_table = 'stock_predictions'
        indexes = [
            models.Index(fields=['stock', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.stock.symbol} - Prediction - {self.timestamp}"