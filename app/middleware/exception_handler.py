"""
Global Exception Handler Middleware

Provides centralized exception handling for the FastAPI application with:
- Unified error response format
- Structured logging with correlation IDs
- Stack trace capture for debugging
- Prometheus metrics integration
"""
import logging
import traceback
from typing import Callable

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.exceptions import AppError
from app.monitoring.metrics import (
    request_counter,
    auth_failures,
)

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI):
    """
    Register global exception handlers
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        """Handle custom application errors"""
        # Log with full stack trace for server errors
        if exc.status_code >= 500:
            logger.error(
                f"Application error [{exc.error_code}]: {exc.message}",
                extra={
                    "correlation_id": exc.correlation_id,
                    "error_code": exc.error_code,
                    "status_code": exc.status_code,
                    "path": str(request.url.path),
                    "method": request.method,
                    "stack_trace": traceback.format_exc()
                }
            )
        else:
            logger.warning(
                f"Client error [{exc.error_code}]: {exc.message}",
                extra={
                    "correlation_id": exc.correlation_id,
                    "error_code": exc.error_code,
                    "status_code": exc.status_code,
                    "path": str(request.url.path),
                    "method": request.method
                }
            )
        
        # Track authentication failures
        if exc.status_code == 401:
            auth_failures.labels(
                endpoint=str(request.url.path),
                reason=exc.error_code
            ).inc()
        
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
            headers={
                "X-Correlation-ID": exc.correlation_id,
                "X-Error-Code": exc.error_code
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic validation errors"""
        correlation_id = str(id(request))
        
        logger.warning(
            f"Validation error: {exc.errors()}",
            extra={
                "correlation_id": correlation_id,
                "path": str(request.url.path),
                "method": request.method
            }
        )
        
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "correlation_id": correlation_id,
                    "details": {
                        "errors": exc.errors()
                    }
                }
            },
            headers={"X-Correlation-ID": correlation_id}
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle standard HTTP exceptions"""
        correlation_id = str(id(request))
        
        # Log unexpected HTTP errors
        if exc.status_code >= 500:
            logger.error(
                f"HTTP error {exc.status_code}: {exc.detail}",
                extra={
                    "correlation_id": correlation_id,
                    "path": str(request.url.path),
                    "method": request.method,
                    "stack_trace": traceback.format_exc()
                }
            )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                    "correlation_id": correlation_id
                }
            },
            headers={"X-Correlation-ID": correlation_id}
        )
    
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        """Handle all other unhandled exceptions"""
        correlation_id = str(id(request))
        
        # Log critical error with full stack trace
        logger.critical(
            f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
            extra={
                "correlation_id": correlation_id,
                "path": str(request.url.path),
                "method": request.method,
                "exception_type": type(exc).__name__,
                "stack_trace": traceback.format_exc()
            }
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred. Please contact support.",
                    "correlation_id": correlation_id
                }
            },
            headers={"X-Correlation-ID": correlation_id}
        )


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add correlation ID to all requests
    
    Generates a unique correlation ID for each request and adds it to:
    - Request state (for use in handlers)
    - Response headers (for client tracking)
    - Log context (for tracing)
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Generate or extract correlation ID
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            from uuid import uuid4
            correlation_id = str(uuid4())
        
        # Store in request state
        request.state.correlation_id = correlation_id
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response
