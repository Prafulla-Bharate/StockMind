"""Kafka consumer for processing market data"""
from kafka import KafkaConsumer
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class StockDataConsumer:
    """Kafka consumer for stock data"""
    
    def __init__(self):
        self.bootstrap_servers = settings.KAFKA_BOOTSTRAP_SERVERS
        self.consumer = None
        self._connect()
    
    def _connect(self):
        """Connect to Kafka"""
        try:
            self.consumer = KafkaConsumer(
                settings.KAFKA_TOPICS['market_data'],
                bootstrap_servers=self.bootstrap_servers,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id=settings.KAFKA_CONSUMER_GROUP if hasattr(settings, 'KAFKA_CONSUMER_GROUP') else 'stockmind-consumer'
            )
            logger.info("Kafka consumer connected")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            self.consumer = None
    
    def consume(self, callback):
        """Consume messages and call callback"""
        if not self.consumer:
            logger.warning("Kafka consumer not connected")
            return
        
        try:
            for message in self.consumer:
                try:
                    data = message.value
                    callback(data)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    continue
        except Exception as e:
            logger.error(f"Consumer error: {e}")
            self._connect()  # Reconnect
    
    def close(self):
        """Close consumer connection"""
        if self.consumer:
            self.consumer.close()