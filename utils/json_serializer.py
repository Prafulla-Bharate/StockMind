"""
Centralized JSON serializer for safe serialization of Decimal, datetime, and date objects.
Used across Celery tasks, views, WebSocket broadcasters, and Kafka producers.
"""
import json
from decimal import Decimal
from datetime import datetime, date
from django.utils import timezone


def json_serializer(obj):
    """
    Custom JSON serializer for objects not serializable by default json code.
    Handles Decimal, datetime, and date objects.
    
    Usage:
        json.dumps(data, default=json_serializer)
    """
    if isinstance(obj, Decimal):
        # Convert Decimal to float; fallback to string for very large numbers
        try:
            return float(obj)
        except Exception:
            return str(obj)
    
    if isinstance(obj, datetime):
        # Ensure timezone-aware ISO8601
        if timezone.is_naive(obj):
            obj = timezone.make_aware(obj)
        return obj.isoformat()
    
    if isinstance(obj, date):
        # Represent dates as ISO8601 (YYYY-MM-DD)
        return obj.isoformat()
    
    # Fallback to string representation for other non-serializable types
    return str(obj)


def safe_json_dumps(obj, **kwargs):
    """
    Convenience wrapper for json.dumps with safe serialization.
    
    Usage:
        safe_json_dumps({'price': Decimal('123.45'), 'timestamp': datetime.now()})
    """
    return json.dumps(obj, default=json_serializer, **kwargs)
