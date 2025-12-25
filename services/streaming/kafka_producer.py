from kafka import KafkaProducer
import logging
from django.conf import settings
from utils.json_serializer import safe_json_dumps

logger = logging.getLogger(__name__)

class StockDataProducer:
    """Kafka producer for streaming stock data"""
    
    def __init__(self):
        self.bootstrap_servers = settings.KAFKA_BOOTSTRAP_SERVERS
        self.producer = None
        self._connect()
    
    def _connect(self):
        """Connect to Kafka"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: safe_json_dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8'),
                acks='all',
                retries=3,
                max_in_flight_requests_per_connection=1
            )
            logger.info("Kafka producer connected")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            self.producer = None
    
    def send_market_data(self, symbol, data):
        """Send market data to Kafka"""
        if not self.producer:
            logger.warning("Kafka producer not connected")
            return False
        
        try:
            topic = settings.KAFKA_TOPICS['market_data']
            future = self.producer.send(
                topic,
                key=symbol,
                value=data
            )
            future.get(timeout=10)
            return True
        except Exception as e:
            logger.error(f"Error sending market data: {e}")
            return False
    
    def send_prediction(self, symbol, prediction):
        """Send prediction to Kafka"""
        if not self.producer:
            return False
        
        try:
            topic = settings.KAFKA_TOPICS['predictions']
            future = self.producer.send(
                topic,
                key=symbol,
                value=prediction
            )
            future.get(timeout=10)
            return True
        except Exception as e:
            logger.error(f"Error sending prediction: {e}")
            return False
    
    def send_sentiment(self, symbol, sentiment):
        """Send sentiment to Kafka"""
        if not self.producer:
            return False
        
        try:
            topic = settings.KAFKA_TOPICS['sentiment']
            future = self.producer.send(
                topic,
                key=symbol,
                value=sentiment
            )
            future.get(timeout=10)
            return True
        except Exception as e:
            logger.error(f"Error sending sentiment: {e}")
            return False
    
    def close(self):
        """Close producer connection"""
        if self.producer:
            self.producer.flush()
            self.producer.close()
