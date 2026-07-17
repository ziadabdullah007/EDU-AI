"""
EduCore AI Platform — Request Logging Middleware

Logs every incoming HTTP request and its response with timing information.
Attaches a correlation ID to each request for distributed tracing readiness.

Log fields per request:
    - correlation_id: Unique request identifier
    - method: HTTP method
    - path: Request path
    - status_code: Response status
    - duration_ms: Processing time in milliseconds
    - client_ip: Client IP address
"""

import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger(__name__)

_CORRELATION_ID_HEADER = "X-Correlation-ID"
_SKIP_PATHS = frozenset({"/health", "/docs", "/openapi.json", "/redoc"})


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs every HTTP request/response pair.

    Attaches a unique correlation ID to each request and logs:
    - Incoming request metadata
    - Response status and duration

    The correlation ID is available to downstream handlers via
    request.state.correlation_id.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process the request, log it, and return the response."""
        correlation_id = request.headers.get(
            _CORRELATION_ID_HEADER, str(uuid.uuid4())
        )
        request.state.correlation_id = correlation_id

        start_time = time.perf_counter()

        if request.url.path not in _SKIP_PATHS:
            logger.info(
                "request_received",
                correlation_id=correlation_id,
                method=request.method,
                path=request.url.path,
                client_ip=self._get_client_ip(request),
                query_string=str(request.url.query) or None,
            )

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers[_CORRELATION_ID_HEADER] = correlation_id

        if request.url.path not in _SKIP_PATHS:
            log_fn = logger.warning if response.status_code >= 400 else logger.info
            log_fn(
                "request_completed",
                correlation_id=correlation_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
            )

        return response

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Extract the real client IP, respecting proxy forwarding headers."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"
