from __future__ import annotations
from typing import Any
from rest_framework.renderers import JSONRenderer


def _snake_to_camel(s: str) -> str:
    parts = s.split('_')
    return parts[0] + ''.join(p.title() for p in parts[1:]) if parts else s


def _transform(obj: Any) -> Any:
    """Recursively convert dict keys from snake_case to camelCase."""
    if isinstance(obj, dict):
        new = {}
        for k, v in obj.items():
            new_key = _snake_to_camel(k) if isinstance(k, str) else k
            new[new_key] = _transform(v)
        return new
    if isinstance(obj, list):
        return [_transform(v) for v in obj]
    return obj


class CamelCaseJSONRenderer(JSONRenderer):
    """Render JSON with camelCase keys and wrap into ApiResponse shape.

    Behavior:
    - If the view already returns an ApiResponse-shaped payload (has 'status' and 'data'), leave it as-is.
    - Otherwise, convert keys to camelCase and wrap into { data, message, status }.
    - Preserve legacy 'success' boolean for backward compatibility.
    """

    charset = 'utf-8'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        # If no data (e.g., HTTP 204 No Content), let DRF handle it
        if data is None:
            return super().render(data, accepted_media_type, renderer_context)

        # If already shaped for frontend, don't re-wrap
        if isinstance(data, dict) and 'status' in data and 'data' in data:
            # still convert any nested keys to camelCase for consistency
            data['data'] = _transform(data.get('data'))
            return super().render(data, accepted_media_type, renderer_context)

        # Determine response status code
        status_code = None
        if renderer_context and renderer_context.get('response') is not None:
            try:
                status_code = int(getattr(renderer_context['response'], 'status_code', 200))
            except Exception:
                status_code = None

        is_error = status_code is not None and status_code >= 400

        if is_error:
            payload = {
                'data': None,
                'message': '',
                'status': 'error',
                'errors': _transform(data),
                'success': False,
            }
        else:
            payload = {
                'data': _transform(data),
                'message': '',
                'status': 'success',
                'success': True,
            }

        return super().render(payload, accepted_media_type, renderer_context)
