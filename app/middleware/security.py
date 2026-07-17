"""
EduCore AI Platform — Security Headers Middleware

Injects security-related HTTP response headers into every response.
These headers harden the application against common web vulnerabilities
such as XSS, clickjacking, MIME sniffing, and information disclosure.
"""

from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to every HTTP response.

    Headers applied:
        - X-Content-Type-Options: Prevents MIME-type sniffing.
        - X-Frame-Options: Prevents clickjacking.
        - X-XSS-Protection: Enables XSS filter in older browsers.
        - Strict-Transport-Security: Enforces HTTPS.
        - Referrer-Policy: Controls referrer information.
        - Permissions-Policy: Restricts browser features.
        - Cache-Control: Prevents caching of API responses.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Inject security headers into the response."""
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        response.headers["Cache-Control"] = "no-store"
        response.headers["Server"] = "EduCore"

        return response
