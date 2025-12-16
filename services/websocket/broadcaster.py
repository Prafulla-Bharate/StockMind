"""
Broadcast helper functions for sending WebSocket updates
Use these in your Celery tasks to broadcast real-time data
"""
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)

def broadcast_stock_update(symbol, data):
    """
    Broadcast stock price update to all subscribers
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL')
        data: Dict with price data
    """
    channel_layer = get_channel_layer()
    
    try:
        async_to_sync(channel_layer.group_send)(
            f"stock_{symbol}",
            {
                'type': 'stock_update',
                'data': {
                    'symbol': symbol,
                    'price': float(data.get('price', 0)),
                    'change': float(data.get('change', 0)),
                    'changePercent': float(data.get('changePercent', 0)),
                    'volume': data.get('volume', 0),
                    'timestamp': data.get('timestamp').isoformat() if data.get('timestamp') else None
                }
            }
        )
        logger.debug(f"Broadcast stock update for {symbol}")
    except Exception as e:
        logger.error(f"Error broadcasting stock update: {e}")

def broadcast_indicator_update(symbol, indicators):
    """
    Broadcast technical indicators update
    
    Args:
        symbol: Stock symbol
        indicators: Dict with indicator values
    """
    channel_layer = get_channel_layer()
    
    try:
        async_to_sync(channel_layer.group_send)(
            f"stock_{symbol}",
            {
                'type': 'indicator_update',
                'data': {
                    'symbol': symbol,
                    'rsi': indicators.get('rsi_14'),
                    'sma20': indicators.get('sma_20'),
                    'sma50': indicators.get('sma_50'),
                    'macd': indicators.get('macd'),
                    'timestamp': indicators.get('timestamp').isoformat() if indicators.get('timestamp') else None
                }
            }
        )
        logger.debug(f"Broadcast indicator update for {symbol}")
    except Exception as e:
        logger.error(f"Error broadcasting indicator update: {e}")

def broadcast_sentiment_update(symbol, sentiment_data):
    """
    Broadcast sentiment analysis update
    
    Args:
        symbol: Stock symbol
        sentiment_data: Dict with sentiment info
    """
    channel_layer = get_channel_layer()
    
    try:
        async_to_sync(channel_layer.group_send)(
            f"stock_{symbol}",
            {
                'type': 'sentiment_update',
                'data': {
                    'symbol': symbol,
                    'sentiment': sentiment_data.get('sentiment'),
                    'score': float(sentiment_data.get('score', 0)),
                    'timestamp': sentiment_data.get('timestamp').isoformat() if sentiment_data.get('timestamp') else None
                }
            }
        )
        logger.debug(f"Broadcast sentiment update for {symbol}")
    except Exception as e:
        logger.error(f"Error broadcasting sentiment update: {e}")

def broadcast_prediction_update(symbol, prediction_data):
    """
    Broadcast ML prediction update
    
    Args:
        symbol: Stock symbol
        prediction_data: Dict with prediction info
    """
    channel_layer = get_channel_layer()
    
    try:
        async_to_sync(channel_layer.group_send)(
            f"stock_{symbol}",
            {
                'type': 'prediction_update',
                'data': {
                    'symbol': symbol,
                    'predictions': prediction_data.get('predictions'),
                    'timestamp': prediction_data.get('timestamp').isoformat() if prediction_data.get('timestamp') else None
                }
            }
        )
        logger.debug(f"Broadcast prediction update for {symbol}")
    except Exception as e:
        logger.error(f"Error broadcasting prediction update: {e}")