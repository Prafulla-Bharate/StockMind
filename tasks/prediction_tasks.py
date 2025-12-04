from celery import shared_task
from celery.utils.log import get_task_logger
import pandas as pd
from apps.market.models import Stock, StockPrice, StockPrediction
from services.ml.lstm_predictor import LSTMPredictor
from decimal import Decimal

logger = get_task_logger(__name__)

@shared_task(bind=True)
def update_predictions(self):
    """Update ML predictions for active stocks"""
    try:
        symbols = Stock.objects.filter(is_active=True)[:50]  # Limit to 50 for performance
        predictor = LSTMPredictor()
        
        success_count = 0
        for stock in symbols:
            try:
                # Get historical data
                prices = StockPrice.objects.filter(stock=stock).order_by('timestamp')[:500]
                
                if len(prices) < 100:
                    continue
                
                df = pd.DataFrame(list(prices.values('timestamp', 'open', 'high', 'low', 'close', 'volume')))
                
                # Get predictions
                predictions = predictor.predict(df, steps=90)
                
                if predictions:
                    current_price = float(prices.last().close)
                    
                    # Short term (7 days)
                    short_term_target = Decimal(str(predictions[6]))
                    short_term_change = ((short_term_target - Decimal(str(current_price))) / Decimal(str(current_price))) * 100
                    
                    # Medium term (30 days)
                    medium_term_target = Decimal(str(predictions[29]))
                    medium_term_change = ((medium_term_target - Decimal(str(current_price))) / Decimal(str(current_price))) * 100
                    
                    # Long term (90 days)
                    long_term_target = Decimal(str(predictions[89]))
                    long_term_change = ((long_term_target - Decimal(str(current_price))) / Decimal(str(current_price))) * 100
                    
                    # Determine trends and confidence
                    short_trend = 'Uptrend' if short_term_change > 0 else 'Downtrend'
                    medium_trend = 'Uptrend' if medium_term_change > 0 else 'Downtrend'
                    long_trend = 'Uptrend' if long_term_change > 0 else 'Downtrend'
                    
                    # Calculate bullish score
                    bullish_signals = sum([
                        short_term_change > 0,
                        medium_term_change > 0,
                        long_term_change > 0
                    ])
                    bullish_score = (bullish_signals / 3) * 100
                    
                    # Save prediction
                    StockPrediction.objects.create(
                        stock=stock,
                        current_price=Decimal(str(current_price)),
                        short_term_target=short_term_target,
                        short_term_change=short_term_change,
                        short_term_confidence='medium',
                        short_term_trend=short_trend,
                        medium_term_target=medium_term_target,
                        medium_term_change=medium_term_change,
                        medium_term_confidence='medium',
                        medium_term_trend=medium_trend,
                        long_term_target=long_term_target,
                        long_term_change=long_term_change,
                        long_term_confidence='low',
                        long_term_trend=long_trend,
                        bullish_score=bullish_score,
                        risk_level='medium',
                        overall_sentiment='Bullish' if bullish_score > 50 else 'Bearish'
                    )
                    
                    success_count += 1
                    
            except Exception as e:
                logger.error(f"Error predicting for {stock.symbol}: {e}")
                continue
        
        return f"Updated predictions for {success_count} stocks"
        
    except Exception as exc:
        logger.error(f"Task failed: {exc}")
        raise exc
