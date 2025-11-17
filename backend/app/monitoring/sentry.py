"""Sentry integration for error tracking and performance monitoring.

Initializes Sentry SDK with release tagging for deployment tracking.
"""

import logging
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from app.config.settings import Settings

logger = logging.getLogger(__name__)


def init_sentry(settings: Settings) -> None:
    """Initialize Sentry error tracking.
    
    Args:
        settings: Application settings containing SENTRY_DSN
        
    Features:
        - Error tracking with stack traces
        - Performance monitoring (transactions)
        - Release tagging for deployment tracking
        - Redis integration for operation monitoring
        - FastAPI integration for HTTP request tracking
    """
    if not settings.SENTRY_DSN:
        logger.warning(
            "Sentry DSN not configured - error tracking disabled",
            extra={"component": "monitoring"}
        )
        return
    
    # Determine environment from settings
    environment = getattr(settings, "APP_ENV", "development")
    
    # Configure Sentry with integrations
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=environment,
        
        # Release tracking for deployment correlation
        release=settings.GIT_COMMIT_SHA if hasattr(settings, "GIT_COMMIT_SHA") else None,
        
        # Integrations
        integrations=[
            FastApiIntegration(
                transaction_style="endpoint",  # Track by endpoint, not URL params
                failed_request_status_codes=[500, 599],  # Only track 5xx as errors
            ),
            RedisIntegration(),
            LoggingIntegration(
                level=logging.INFO,  # Capture info and above
                event_level=logging.ERROR  # Only create Sentry events for errors
            ),
        ],
        
        # Performance monitoring
        traces_sample_rate=1.0 if environment != "production" else 0.1,  # 100% dev, 10% prod
        
        # Error sampling
        sample_rate=1.0,  # Capture all errors
        
        # Additional options
        attach_stacktrace=True,
        send_default_pii=False,  # Don't send PII (user IDs, IPs) automatically
        
        # Custom event processors
        before_send=_before_send_filter,
    )
    
    logger.info(
        "Sentry initialized",
        extra={
            "environment": environment,
            "release": settings.GIT_COMMIT_SHA if hasattr(settings, "GIT_COMMIT_SHA") else "unknown",
            "traces_sample_rate": 1.0 if environment != "production" else 0.1,
        }
    )


def _before_send_filter(event: dict, hint: dict) -> dict | None:
    """Filter events before sending to Sentry.
    
    Args:
        event: Sentry event data
        hint: Additional context about the event
        
    Returns:
        Modified event or None to drop the event
        
    Filters:
        - Removes sensitive data from request bodies
        - Drops noisy exceptions (e.g., Redis connection timeouts in dev)
    """
    # Drop Redis connection errors in development
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]
        if exc_type.__name__ == "ConnectionError" and "redis" in str(exc_value).lower():
            # Don't send Redis connection errors (too noisy in dev)
            return None
    
    # Sanitize request data
    if "request" in event:
        request = event["request"]
        
        # Remove sensitive headers
        if "headers" in request:
            sensitive_headers = ["authorization", "cookie", "x-api-key"]
            for header in sensitive_headers:
                if header in request["headers"]:
                    request["headers"][header] = "[Filtered]"
        
        # Remove message body (may contain user PII)
        if "data" in request:
            request["data"] = "[Filtered]"
    
    return event


def capture_exception_with_context(
    exception: Exception,
    context: dict | None = None
) -> str:
    """Capture exception with additional context.
    
    Args:
        exception: Exception to capture
        context: Additional context tags/data
        
    Returns:
        Sentry event ID
        
    Example:
        >>> event_id = capture_exception_with_context(
        ...     exception=ValueError("Invalid IATA code"),
        ...     context={
        ...         "session_id": "abc123",
        ...         "user_input": "NYC to LAX",
        ...         "extracted_origin": "NYC"
        ...     }
        ... )
    """
    with sentry_sdk.push_scope() as scope:
        # Add context tags
        if context:
            for key, value in context.items():
                scope.set_tag(key, value)
        
        # Capture exception
        event_id = sentry_sdk.capture_exception(exception)
    
    return event_id


def set_user_context(session_id: str, user_agent: str | None = None) -> None:
    """Set user context for Sentry tracking.
    
    Args:
        session_id: Anonymous session identifier
        user_agent: Optional user agent string
        
    Note: We don't send real user IDs to respect privacy
    """
    sentry_sdk.set_user({
        "id": session_id,  # Anonymous session ID
        "user_agent": user_agent
    })


def start_transaction(name: str, op: str) -> sentry_sdk.tracing.Transaction:
    """Start a Sentry performance transaction.
    
    Args:
        name: Transaction name (e.g., "flight_search")
        op: Operation type (e.g., "agent.tool.execution")
        
    Returns:
        Transaction object (use as context manager)
        
    Example:
        >>> with start_transaction("flight_search", "agent.tool"):
        ...     results = await search_flights(params)
    """
    return sentry_sdk.start_transaction(name=name, op=op)
