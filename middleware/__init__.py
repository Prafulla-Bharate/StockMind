"""Lightweight middleware package for local development.

This package provides no-op or minimal stubs for middleware referenced
in settings so the development server can run without external deps.
"""

__all__ = ["rate_limit", "metrics"]
