from typing import Any, Dict, Optional


def success_response(data: Optional[Any] = None, message: str = '', meta: Optional[Dict] = None) -> Dict:
    """Standard success response

    Returns a JSON-serializable dict used across the project.
    """
    return {
        'success': True,
        'message': message,
        'data': data if data is not None else {},
        'meta': meta or {}
    }


def error_response(message: str = '', errors: Optional[Any] = None, code: Optional[int] = None) -> Dict:
    """Standard error response

    `errors` can be a dict or list describing validation or runtime errors.
    """
    payload = {
        'success': False,
        'message': message,
        'errors': errors if errors is not None else {}
    }
    if code is not None:
        payload['code'] = code
    return payload
