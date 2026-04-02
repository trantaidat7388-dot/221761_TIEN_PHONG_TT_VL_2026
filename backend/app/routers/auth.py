"""Auth router facade.

Provides standardized module name app.routers.auth while preserving
existing route implementation in auth_routes.
"""

from .auth_routes import router

__all__ = ["router"]
