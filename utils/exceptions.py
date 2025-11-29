from typing import Any, Optional

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

from .responses import error_response


def custom_exception_handler(exc: Exception, context: dict) -> Optional[Response]:
    """Custom DRF exception handler that returns a standardized error payload.

    This wraps DRF's default `exception_handler` and converts the returned
    response.data into the project's `error_response` shape.
    """
    # Let DRF build the initial Response (may be None for unhandled exceptions)
    response = exception_handler(exc, context)

    if response is None:
        # Unhandled exception — return a 500 with a generic payload
        payload = error_response(message=str(exc) or "Server error")
        return Response(payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # For handled exceptions, normalize the body
    data = response.data
    message = ""
    errors: Any = None

    try:
        if isinstance(data, dict):
            # DRF often places a single message under 'detail'
            if 'detail' in data:
                message = data.get('detail')
                # Preserve other keys as errors
                errors = {k: v for k, v in data.items() if k != 'detail'}
            else:
                errors = data
        else:
            errors = data
    except Exception:
        # Fall back if response.data is unexpected
        message = str(data)
        errors = None

    payload = error_response(message=message or "", errors=errors, code=response.status_code)
    return Response(payload, status=response.status_code)
