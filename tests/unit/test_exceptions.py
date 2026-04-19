"""
Unit tests for custom exception hierarchy

Tests all custom exception types and their behavior.
"""
import pytest
from app.exceptions import (
    AppError,
    ValidationError,
    NotFoundError,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    SkillExecutionError,
    LLMError,
    ExternalServiceError,
    DatabaseError,
    ConfigurationError,
)


class TestAppError:
    """Tests for base AppError class"""
    
    def test_basic_app_error(self):
        """Test basic AppError creation"""
        error = AppError(
            message="Something went wrong",
            error_code="TEST_ERROR",
            status_code=500
        )
        
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.error_code == "TEST_ERROR"
        assert error.status_code == 500
        assert error.correlation_id is not None
    
    def test_app_error_with_details(self):
        """Test AppError with additional details"""
        error = AppError(
            message="Validation failed",
            error_code="VALIDATION_ERROR",
            status_code=400,
            details={"field": "email", "value": "invalid"}
        )
        
        assert error.details["field"] == "email"
        assert error.details["value"] == "invalid"
    
    def test_app_error_to_dict(self):
        """Test converting AppError to dictionary"""
        error = AppError(
            message="Test error",
            error_code="TEST_CODE",
            correlation_id="test-123"
        )
        
        error_dict = error.to_dict()
        
        assert "error" in error_dict
        assert error_dict["error"]["code"] == "TEST_CODE"
        assert error_dict["error"]["message"] == "Test error"
        assert error_dict["error"]["correlation_id"] == "test-123"
    
    def test_app_error_auto_generates_correlation_id(self):
        """Test that correlation ID is auto-generated if not provided"""
        error1 = AppError(message="Error 1")
        error2 = AppError(message="Error 2")
        
        assert error1.correlation_id is not None
        assert error2.correlation_id is not None
        assert error1.correlation_id != error2.correlation_id


class TestValidationError:
    """Tests for ValidationError"""
    
    def test_validation_error_basic(self):
        """Test basic validation error"""
        error = ValidationError(
            message="Invalid input",
            field="username"
        )
        
        assert error.status_code == 400
        assert error.error_code == "VALIDATION_ERROR"
        assert error.details["field"] == "username"
    
    def test_validation_error_with_details(self):
        """Test validation error with additional context"""
        error = ValidationError(
            message="Email format invalid",
            field="email",
            details={"provided": "not-an-email", "expected": "user@domain.com"}
        )
        
        assert error.details["field"] == "email"
        assert error.details["provided"] == "not-an-email"


class TestNotFoundError:
    """Tests for NotFoundError"""
    
    def test_not_found_error_basic(self):
        """Test basic not found error"""
        error = NotFoundError(
            resource_type="User",
            resource_id="12345"
        )
        
        assert error.status_code == 404
        assert error.error_code == "NOT_FOUND"
        assert "User" in error.message
        assert "12345" in error.message
        assert error.details["resource_type"] == "User"
        assert error.details["resource_id"] == "12345"


class TestAuthenticationError:
    """Tests for AuthenticationError"""
    
    def test_authentication_error_default_message(self):
        """Test authentication error with default message"""
        error = AuthenticationError()
        
        assert error.status_code == 401
        assert error.error_code == "AUTHENTICATION_FAILED"
        assert error.message == "Authentication failed"
    
    def test_authentication_error_custom_message(self):
        """Test authentication error with custom message"""
        error = AuthenticationError(message="Token expired")
        
        assert error.message == "Token expired"


class TestAuthorizationError:
    """Tests for AuthorizationError"""
    
    def test_authorization_error_default_message(self):
        """Test authorization error with default message"""
        error = AuthorizationError()
        
        assert error.status_code == 403
        assert error.error_code == "AUTHORIZATION_DENIED"
        assert error.message == "Insufficient permissions"
    
    def test_authorization_error_custom_message(self):
        """Test authorization error with custom message"""
        error = AuthorizationError(message="Admin access required")
        
        assert error.message == "Admin access required"


class TestRateLimitError:
    """Tests for RateLimitError"""
    
    def test_rate_limit_error_default_retry(self):
        """Test rate limit error with default retry time"""
        error = RateLimitError()
        
        assert error.status_code == 429
        assert error.error_code == "RATE_LIMIT_EXCEEDED"
        assert error.details["retry_after_seconds"] == 60
    
    def test_rate_limit_error_custom_retry(self):
        """Test rate limit error with custom retry time"""
        error = RateLimitError(retry_after=120)
        
        assert error.details["retry_after_seconds"] == 120


class TestSkillExecutionError:
    """Tests for SkillExecutionError"""
    
    def test_skill_execution_error_retriable(self):
        """Test skill execution error marked as retriable"""
        error = SkillExecutionError(
            skill_name="wiki_search",
            error_message="Timeout",
            retriable=True
        )
        
        assert error.status_code == 500
        assert error.error_code == "SKILL_EXECUTION_FAILED"
        assert error.details["skill_name"] == "wiki_search"
        assert error.details["retriable"] is True
    
    def test_skill_execution_error_not_retriable(self):
        """Test skill execution error marked as not retriable"""
        error = SkillExecutionError(
            skill_name="data_export",
            error_message="Invalid format",
            retriable=False
        )
        
        assert error.details["retriable"] is False


class TestLLMError:
    """Tests for LLMError"""
    
    def test_llm_error_retriable(self):
        """Test LLM error marked as retriable"""
        error = LLMError(
            model="gpt-4",
            error_message="Rate limit exceeded",
            retriable=True
        )
        
        assert error.status_code == 502
        assert error.error_code == "LLM_API_ERROR"
        assert error.details["model"] == "gpt-4"
        assert error.details["retriable"] is True
    
    def test_llm_error_not_retriable(self):
        """Test LLM error marked as not retriable"""
        error = LLMError(
            model="custom-model",
            error_message="Invalid API key",
            retriable=False
        )
        
        assert error.details["retriable"] is False


class TestExternalServiceError:
    """Tests for ExternalServiceError"""
    
    def test_external_service_error(self):
        """Test external service error"""
        error = ExternalServiceError(
            service_name="RAG API",
            error_message="Connection timeout",
            retriable=True
        )
        
        assert error.status_code == 502
        assert error.error_code == "EXTERNAL_SERVICE_ERROR"
        assert error.details["service_name"] == "RAG API"
        assert error.details["retriable"] is True


class TestDatabaseError:
    """Tests for DatabaseError"""
    
    def test_database_error(self):
        """Test database error"""
        error = DatabaseError(
            operation="INSERT",
            error_message="Constraint violation"
        )
        
        assert error.status_code == 500
        assert error.error_code == "DATABASE_ERROR"
        assert error.details["operation"] == "INSERT"


class TestConfigurationError:
    """Tests for ConfigurationError"""
    
    def test_configuration_error(self):
        """Test configuration error"""
        error = ConfigurationError(
            config_key="LLM_API_KEY",
            error_message="Missing required configuration"
        )
        
        assert error.status_code == 500
        assert error.error_code == "CONFIGURATION_ERROR"
        assert error.details["config_key"] == "LLM_API_KEY"


class TestExceptionInheritance:
    """Test that all exceptions properly inherit from AppError"""
    
    def test_all_exceptions_are_app_errors(self):
        """Verify all custom exceptions inherit from AppError"""
        exceptions = [
            ValidationError("test"),
            NotFoundError("User", "1"),
            AuthenticationError(),
            AuthorizationError(),
            RateLimitError(),
            SkillExecutionError("test", "error"),
            LLMError("model", "error"),
            ExternalServiceError("service", "error"),
            DatabaseError("op", "error"),
            ConfigurationError("key", "error"),
        ]
        
        for exc in exceptions:
            assert isinstance(exc, AppError)
            assert hasattr(exc, 'to_dict')
            assert hasattr(exc, 'status_code')
            assert hasattr(exc, 'error_code')
            assert hasattr(exc, 'correlation_id')


class TestExceptionResponseFormat:
    """Test standardized error response format"""
    
    def test_error_response_structure(self):
        """Test that all errors return consistent structure"""
        error = ValidationError(
            message="Test validation",
            field="test_field",
            correlation_id="test-id-123"
        )
        
        response = error.to_dict()
        
        # Verify structure
        assert "error" in response
        assert "code" in response["error"]
        assert "message" in response["error"]
        assert "correlation_id" in response["error"]
        assert "details" in response["error"]
        
        # Verify values
        assert response["error"]["code"] == "VALIDATION_ERROR"
        assert response["error"]["message"] == "Test validation"
        assert response["error"]["correlation_id"] == "test-id-123"
    
    def test_error_response_without_details(self):
        """Test error response when no details provided"""
        error = AuthenticationError(correlation_id="auth-123")
        response = error.to_dict()
        
        # Details should be None or empty
        assert response["error"]["details"] is None
