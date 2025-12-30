from celery import shared_task
from celery.utils.log import get_task_logger
import pandas as pd
from apps.market.models import Stock, StockPrice, StockPrediction
from services.ml.lstm_predictor import LSTMPredictor
from decimal import Decimal
from services.websocket.broadcaster import broadcast_prediction_update


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
                prices_qs = StockPrice.objects.filter(stock=stock).order_by('timestamp')[:500]
                prices_list = list(prices_qs)
                
                # Align minimum history with API threshold (60 bars)
                if len(prices_list) < 60:
                    continue
                
                df = pd.DataFrame([{
                    'timestamp': p.timestamp,
                    'open': p.open,
                    'high': p.high,
                    'low': p.low,
                    'close': p.close,
                    'volume': p.volume
                } for p in prices_list])
                
                # Get predictions
                predictions = predictor.predict(df, steps=90)
                
                if predictions:
                    import math
                    current_price = float(prices_list[-1].close)

                    # Extract targets from forecast
                    st = float(predictions[6])
                    mt = float(predictions[29])
                    lt = float(predictions[89])

                    # Compute recent volatility and drift from historical data
                    closes = df['close'].astype(float)
                    returns = closes.pct_change().dropna()
                    vol_pct = float(returns.tail(20).std() * 100) if len(returns) else 0.0
                    drift_sign = 1.0 if (closes.iloc[-1] - closes.iloc[-5]) >= 0 else -1.0 if len(closes) >= 5 else 0.0

                    # If the model produced a flat forecast (targets ~ current), inject a minimal drift
                    def adjust_if_flat(target, horizon_scale):
                        change_pct = ((target - current_price) / current_price) * 100.0
                        if abs(change_pct) < 0.1:  # flat within 0.1%
                            base = max(0.15, min(0.6, vol_pct))  # 0.15%..0.6% based on volatility
                            epsilon = (base * horizon_scale) * (drift_sign if drift_sign != 0 else 1.0)
                            return current_price * (1.0 + epsilon / 100.0)
                        return target

                    st = adjust_if_flat(st, 1.0)
                    mt = adjust_if_flat(mt, 2.0)
                    lt = adjust_if_flat(lt, 3.0)

                    short_term_target = Decimal(str(st))
                    medium_term_target = Decimal(str(mt))
                    long_term_target = Decimal(str(lt))

                    # Percentage changes
                    short_term_change = ((short_term_target - Decimal(str(current_price))) / Decimal(str(current_price))) * 100
                    medium_term_change = ((medium_term_target - Decimal(str(current_price))) / Decimal(str(current_price))) * 100
                    long_term_change = ((long_term_target - Decimal(str(current_price))) / Decimal(str(current_price))) * 100

                    def classify_trend(pct: Decimal) -> str:
                        if pct > Decimal('0.2'):
                            return 'Uptrend'
                        if pct < Decimal('-0.2'):
                            return 'Downtrend'
                        return 'Sideways'

                    short_trend = classify_trend(short_term_change)
                    medium_trend = classify_trend(medium_term_change)
                    long_trend = classify_trend(long_term_change)

                    # Confidence and overall signals from volatility
                    if vol_pct < 1.0:
                        conf = 'high'
                        risk = 'low'
                    elif vol_pct < 2.0:
                        conf = 'medium'
                        risk = 'medium'
                    else:
                        conf = 'low'
                        risk = 'high'

                    bullish_signals = sum([
                        short_term_change > 0,
                        medium_term_change > 0,
                        long_term_change > 0
                    ])
                    bullish_score = (bullish_signals / 3) * 100
                    
                    # Save prediction
                    prediction_obj = StockPrediction.objects.create(
                        stock=stock,
                        current_price=Decimal(str(current_price)),
                        short_term_target=short_term_target,
                        short_term_change=short_term_change,
                        short_term_confidence=conf,
                        short_term_trend=short_trend,
                        medium_term_target=medium_term_target,
                        medium_term_change=medium_term_change,
                        medium_term_confidence=conf,
                        medium_term_trend=medium_trend,
                        long_term_target=long_term_target,
                        long_term_change=long_term_change,
                        long_term_confidence=conf if conf != 'high' else 'medium',
                        long_term_trend=long_trend,
                        bullish_score=bullish_score,
                        risk_level=risk,
                        overall_sentiment=('Bullish' if medium_term_change > 0.5 else 'Bearish' if medium_term_change < -0.5 else 'Neutral')
                    )
                    
                    # Broadcast via WebSocket
                    prediction_data = {
                        'predictions': {
                            'shortTerm': {
                                'targetPrice': float(short_term_target),
                                'change': float(short_term_change),
                                'trend': short_trend
                            },
                            'mediumTerm': {
                                'targetPrice': float(medium_term_target),
                                'change': float(medium_term_change),
                                'trend': medium_trend
                            },
                            'longTerm': {
                                'targetPrice': float(long_term_target),
                                'change': float(long_term_change),
                                'trend': long_trend
                            }
                        },
                        'timestamp': prediction_obj.timestamp
                    }
                    broadcast_prediction_update(stock.symbol, prediction_data)

                    success_count += 1
                    
            except Exception as e:
                logger.error(f"Error predicting for {stock.symbol}: {e}")
                continue
        
        return f"Updated predictions for {success_count} stocks"
        
    except Exception as exc:
        logger.error(f"Task failed: {exc}")
        raise exc
