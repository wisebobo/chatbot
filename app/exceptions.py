"""
Custom Exception Hierarchy for Enterprise Agent Platform

Provides structured exception handling with:
- Custom exception classes for different error types
- Error codes and metadata
- Correlation ID tracking
- Structured error responses
"""
from typing import Any, Dict, Optional
from uuid import uuid4


class AppError(Exception):
    """
    Base application exception
    
    All custom exceptions should inherit from this class.
    Provides consistent error structure and metadata.
    """
    
    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.correlation_id = correlation_id or str(uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response"""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "correlation_id": self.correlation_id,
                "details": self.details if self.details else None
            }
        }


class ValidationError(AppError):
    """Input validation error (400)"""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        details = kwargs.get("details", {})
        if field:
            details["field"] = field
        
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )


class NotFoundError(AppError):
    """Resource not found error (404)"""
    
    def __init__(self, resource_type: str, resource_id: str, **kwargs):
        super().__init__(
            message=f"{resource_type} with ID '{resource_id}' not found",
            error_code="NOT_FOUND",
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id},
            **kwargs
        )


class AuthenticationError(AppError):
    """Authentication failure (401)"""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_FAILED",
            status_code=401,
            **kwargs
        )


class AuthorizationError(AppError):
    """Authorization/permission denied (403)"""
    
    def __init__(self, message: str = "Insufficient permissions", **kwargs):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_DENIED",
            status_code=403,
            **kwargs
        )


class RateLimitError(AppError):
    """Rate limit exceeded (429)"""
    
    def __init__(self, retry_after: int = 60, **kwargs):
        super().__init__(
            message="Rate limit exceeded. Please try again later.",
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={"retry_after_seconds": retry_after},
            **kwargs
        )


class SkillExecutionError(AppError):
    """Skill execution failure (500)"""
    
    def __init__(self, skill_name: str, error_message: str, retriable: bool = False, **kwargs):
        super().__init__(
            message=f"Skill '{skill_name}' execution failed: {error_message}",
            error_code="SKILL_EXECUTION_FAILED",
            status_code=500,
            details={
                "skill_name": skill_name,
                "retriable": retriable
            },
            **kwargs
        )


class LLMError(AppError):
    """LLM API call failure (502)"""
    
    def __init__(self, model: str, error_message: str, retriable: bool = True, **kwargs):
        super().__init__(
            message=f"LLM API call failed for model '{model}': {error_message}",
            error_code="LLM_API_ERROR",
            status_code=502,
            details={
                "model": model,
                "retriable": retriable
            },
            **kwargs
        )


class ExternalServiceError(AppError):
    """External service (RAG, Wiki, etc.) failure (502)"""
    
    def __init__(self, service_name: str, error_message: str, retriable: bool = True, **kwargs):
        super().__init__(
            message=f"External service '{service_name}' failed: {error_message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details={
                "service_name": service_name,
                "retriable": retriable
            },
            **kwargs
        )


class DatabaseError(AppError):
    """Database operation failure (500)"""
    
    def __init__(self, operation: str, error_message: str, **kwargs):
        super().__init__(
            message=f"Database operation '{operation}' failed: {error_message}",
            error_code="DATABASE_ERROR",
            status_code=500,
            details={"operation": operation},
            **kwargs
        )


class ConfigurationError(AppError):
    """Configuration error (500)"""
    
    def __init__(self, config_key: str, error_message: str, **kwargs):
        super().__init__(
            message=f"Configuration error for '{config_key}': {error_message}",
            error_code="CONFIGURATION_ERROR",
            status_code=500,
            details={"config_key": config_key},
            **kwargs
        )
