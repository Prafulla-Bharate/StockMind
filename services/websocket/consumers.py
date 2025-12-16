import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class MarketConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time market data"""
    
    async def connect(self):
        """Handle WebSocket connection"""
        # Accept the connection
        await self.accept()
        
        # Initialize subscribed symbols set
        self.subscribed_symbols = set()
        
        logger.info(f"WebSocket connected: {self.channel_name}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave all subscribed groups
        for symbol in self.subscribed_symbols:
            await self.channel_layer.group_discard(
                f"stock_{symbol}",
                self.channel_name
            )
        
        logger.info(f"WebSocket disconnected: {self.channel_name} (code: {close_code})")
    
    async def receive(self, text_data):
        """
        Receive message from WebSocket
        Expected format: {"type": "subscribe", "symbol": "AAPL"}
                        {"type": "unsubscribe", "symbol": "AAPL"}
        """
        try:
            data = json.loads(text_data)
            action = data.get('type')
            symbol = data.get('symbol', '').upper()
            
            if not symbol:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Symbol is required'
                }))
                return
            
            if action == 'subscribe':
                await self.subscribe_to_stock(symbol)
            elif action == 'unsubscribe':
                await self.unsubscribe_from_stock(symbol)
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Invalid action type'
                }))
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Error in receive: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error'
            }))
    
    async def subscribe_to_stock(self, symbol):
        """Subscribe to stock updates"""
        # Add to group
        await self.channel_layer.group_add(
            f"stock_{symbol}",
            self.channel_name
        )
        
        # Add to subscribed set
        self.subscribed_symbols.add(symbol)
        
        # Send confirmation
        await self.send(text_data=json.dumps({
            'type': 'subscribed',
            'symbol': symbol,
            'message': f'Subscribed to {symbol}'
        }))
        
        # Send current price if available in cache
        price_data = cache.get(f"latest_price_{symbol}")
        if price_data:
            await self.send(text_data=json.dumps({
                'type': 'stock_update',
                'data': {
                    'symbol': symbol,
                    'price': float(price_data.get('price', 0)),
                    'change': float(price_data.get('change', 0)),
                    'changePercent': float(price_data.get('changePercent', 0)),
                    'volume': price_data.get('volume', 0),
                    'timestamp': price_data.get('timestamp').isoformat() if price_data.get('timestamp') else None
                }
            }))
        
        logger.info(f"Client {self.channel_name} subscribed to {symbol}")
    
    async def unsubscribe_from_stock(self, symbol):
        """Unsubscribe from stock updates"""
        # Remove from group
        await self.channel_layer.group_discard(
            f"stock_{symbol}",
            self.channel_name
        )
        
        # Remove from subscribed set
        self.subscribed_symbols.discard(symbol)
        
        # Send confirmation
        await self.send(text_data=json.dumps({
            'type': 'unsubscribed',
            'symbol': symbol,
            'message': f'Unsubscribed from {symbol}'
        }))
        
        logger.info(f"Client {self.channel_name} unsubscribed from {symbol}")
    
    # Event handlers (called when messages are sent to group)
    
    async def stock_update(self, event):
        """Send stock price update to WebSocket"""
        data = event['data']
        
        await self.send(text_data=json.dumps({
            'type': 'stock_update',
            'data': data
        }))
    
    async def indicator_update(self, event):
        """Send technical indicator update to WebSocket"""
        data = event['data']
        
        await self.send(text_data=json.dumps({
            'type': 'indicator_update',
            'data': data
        }))
    
    async def sentiment_update(self, event):
        """Send sentiment update to WebSocket"""
        data = event['data']
        
        await self.send(text_data=json.dumps({
            'type': 'sentiment_update',
            'data': data
        }))
    
    async def prediction_update(self, event):
        """Send prediction update to WebSocket"""
        data = event['data']
        
        await self.send(text_data=json.dumps({
            'type': 'prediction_update',
            'data': data
        }))
    
    async def news_update(self, event):
        """Send news update to WebSocket"""
        data = event['data']
        
        await self.send(text_data=json.dumps({
            'type': 'news_update',
            'data': data
        }))

