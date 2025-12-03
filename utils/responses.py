from typing import Any, Dict, Optional


def success_response(data: Optional[Any] = None, message: str = '', meta: Optional[Dict] = None) -> Dict:
    """Standard success response

    Returns a JSON-serializable dict used across the project.
    """
    # New frontend-friendly ApiResponse shape:
    # { data: <T>, message?: string, status: 'success' }
    payload = {
        'data': data if data is not None else None,
        'message': message,
        'status': 'success',
    }

    # Preserve legacy key for backward compatibility with internal callers
    payload['success'] = True

    if meta:
        payload['meta'] = meta

    return payload


def error_response(message: str = '', errors: Optional[Any] = None, code: Optional[int] = None) -> Dict:
    """Standard error response

    `errors` can be a dict or list describing validation or runtime errors.
    """
    # New frontend-friendly ApiResponse shape for errors:
    # { data: null, message: string, status: 'error', errors: {...} }
    payload = {
        'data': None,
        'message': message,
        'status': 'error',
        'errors': errors if errors is not None else {}
    }

    # Preserve legacy key for backward compatibility with internal callers
    payload['success'] = False

    if code is not None:
        payload['code'] = code

    return payload
