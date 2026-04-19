"""
Exception Handling Examples and Best Practices

This module demonstrates how to use the enhanced exception handling system.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
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
from app.utils.retry import exponential_backoff, RetryConfig, retry_with_config
from app.utils.circuit_breaker import CircuitBreaker, CircuitBreakerRegistry


# ===== Example 1: Using Custom Exceptions =====

async def example_custom_exceptions():
    """Demonstrate custom exception usage"""
    
    # Validation error
    try:
        raise ValidationError(
            message="Invalid email format",
            field="email",
            details={"provided": "invalid-email"}
        )
    except AppError as e:
        print(f"Error: {e.to_dict()}")
        # Output: {"error": {"code": "VALIDATION_ERROR", "message": "...", ...}}
    
    # Not found error
    try:
        raise NotFoundError(resource_type="User", resource_id="12345")
    except AppError as e:
        print(f"Status: {e.status_code}, Code: {e.error_code}")
        # Output: Status: 404, Code: NOT_FOUND
    
    # LLM error with retry hint
    try:
        raise LLMError(
            model="gpt-4",
            error_message="Rate limit exceeded",
            retriable=True
        )
    except AppError as e:
        if e.details.get("retriable"):
            print("This error can be retried")


# ===== Example 2: Exponential Backoff Retry =====

@exponential_backoff(
    max_retries=3,
    base_delay=1.0,
    max_delay=30.0,
    retryable_exceptions=(ConnectionError, TimeoutError)
)
async def call_external_api(url: str) -> dict:
    """Example function with automatic retry"""
    import httpx
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
        response.raise_for_status()
        return response.json()


async def example_retry_decorator():
    """Demonstrate retry decorator usage"""
    try:
        result = await call_external_api("https://api.example.com/data")
        print(f"Success: {result}")
    except Exception as e:
        print(f"All retries exhausted: {e}")


async def example_retry_with_config():
    """Demonstrate retry with configuration object"""
    
    async def fetch_data(query: str) -> dict:
        # Simulate API call
        pass
    
    try:
        result = await retry_with_config(
            fetch_data,
            "search query",
            config=RetryConfig.aggressive(),  # More retries, longer waits
            retryable_exceptions=(TimeoutError,)
        )
        print(f"Result: {result}")
    except Exception as e:
        print(f"Failed after all retries: {e}")


# ===== Example 3: Circuit Breaker =====

async def example_circuit_breaker_decorator():
    """Demonstrate circuit breaker as decorator"""
    
    # Get or create circuit breaker
    breaker = CircuitBreakerRegistry.get_or_create(
        name="external_api",
        failure_threshold=5,
        recovery_timeout=60.0
    )
    
    @breaker
    async def unstable_service_call(data: str) -> str:
        # This might fail
        pass
    
    try:
        result = await unstable_service_call("test data")
        print(f"Success: {result}")
    except Exception as e:
        print(f"Circuit breaker rejected or service failed: {e}")


async def example_circuit_breaker_with_fallback():
    """Demonstrate circuit breaker with fallback function"""
    
    async def primary_service() -> dict:
        # Primary service that might fail
        raise ConnectionError("Service unavailable")
    
    async def fallback_service() -> dict:
        # Fallback implementation
        return {"status": "using_cached_data", "data": []}
    
    breaker = CircuitBreaker(
        name="primary_api",
        failure_threshold=3,
        recovery_timeout=30.0,
        fallback_function=fallback_service
    )
    
    # Wrap primary service
    protected_call = breaker(primary_service)
    
    try:
        result = await protected_call()
        print(f"Result (may be from fallback): {result}")
    except Exception as e:
        print(f"Both primary and fallback failed: {e}")


# ===== Example 4: Combining Retry + Circuit Breaker =====

@exponential_backoff(max_retries=3, base_delay=1.0)
async def resilient_api_call(url: str) -> dict:
    """Combine retry with circuit breaker for maximum resilience"""
    
    breaker = CircuitBreakerRegistry.get_or_create(
        name=f"api_{url}",
        failure_threshold=5,
        recovery_timeout=60.0
    )
    
    @breaker
    async def make_request():
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            return response.json()
    
    return await make_request()


# ===== Example 5: Monitoring Circuit Breaker States =====

def example_monitor_circuit_breakers():
    """Demonstrate monitoring all circuit breakers"""
    
    registry = CircuitBreakerRegistry
    
    # Get states of all circuit breakers
    all_states = registry.get_all_states()
    
    for name, state in all_states.items():
        print(f"\nCircuit Breaker: {name}")
        print(f"  State: {state['state']}")
        print(f"  Failures: {state['failure_count']}/{state['failure_threshold']}")
        print(f"  Time in current state: {state['time_in_current_state']:.1f}s")
        
        # Alert if circuit is open
        if state['state'] == 'open':
            print(f"  ⚠️  WARNING: Circuit is OPEN! Service may be down.")


# ===== Example 6: Error Response Format =====

def example_error_responses():
    """Show standardized error response format"""
    
    # All AppError instances have consistent format
    error = ValidationError(
        message="Invalid input",
        field="username",
        correlation_id="abc-123-def"
    )
    
    response = error.to_dict()
    print(response)
    # Output:
    # {
    #   "error": {
    #     "code": "VALIDATION_ERROR",
    #     "message": "Invalid input",
    #     "correlation_id": "abc-123-def",
    #     "details": {
    #       "field": "username"
    #     }
    #   }
    # }


# ===== Best Practices =====

"""
Best Practices for Exception Handling:

1. **Use Specific Exceptions**
   - Use ValidationError for input validation
   - Use NotFoundError for missing resources
   - Use AuthenticationError for auth failures
   - Don't use generic Exception unless necessary

2. **Provide Context**
   - Always include meaningful error messages
   - Add relevant details in the details dict
   - Include correlation_id for tracing

3. **Retry Wisely**
   - Only retry transient errors (network, timeout)
   - Don't retry business logic errors (validation, auth)
   - Use appropriate retry counts and delays

4. **Circuit Breaker Strategy**
   - Set reasonable failure thresholds (3-5)
   - Use appropriate recovery timeouts (30-60s)
   - Implement fallback functions when possible

5. **Logging**
   - Log errors with full stack traces for 5xx
   - Log warnings for 4xx client errors
   - Include correlation_id in all logs

6. **API Responses**
   - Never expose internal error details to clients
   - Always include correlation_id for support
   - Use consistent error format

7. **Testing**
   - Test retry logic with mock failures
   - Test circuit breaker state transitions
   - Verify error responses match expected format
"""


if __name__ == "__main__":
    print("Running exception handling examples...\n")
    
    # Run examples
    asyncio.run(example_custom_exceptions())
    print("\n" + "="*70 + "\n")
    
    example_error_responses()
    print("\n" + "="*70 + "\n")
    
    example_monitor_circuit_breakers()
    
    print("\n✅ All examples completed!")
