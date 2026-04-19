# Enhanced Exception Handling Guide

## 📋 Overview

The Enterprise Agent Platform now includes a comprehensive exception handling system with:

- ✅ **Custom Exception Hierarchy** - Structured error types with metadata
- ✅ **Global Exception Handler** - Unified error responses and logging
- ✅ **Exponential Backoff Retry** - Intelligent retry with jitter
- ✅ **Circuit Breaker Pattern** - Prevent cascading failures
- ✅ **Correlation ID Tracking** - End-to-end request tracing
- ✅ **Structured Error Logging** - Detailed context for debugging

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│      Client Request                 │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  CorrelationID Middleware           │ ← Generates unique ID per request
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│    Business Logic                   │
│  ┌──────────────────────────────┐   │
│  │ Circuit Breaker              │   │ ← Monitors failure rates
│  └──────────┬───────────────────┘   │
│             │                        │
│  ┌──────────▼───────────────────┐   │
│  │ Exponential Backoff Retry    │   │ ← Retries transient failures
│  └──────────┬───────────────────┘   │
│             │                        │
│  ┌──────────▼───────────────────┐   │
│  │ Custom Exceptions            │   │ ← Structured error types
│  └──────────┬───────────────────┘   │
└─────────────┼───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  Global Exception Handler           │ ← Catches all exceptions
│  - Logs with correlation_id         │
│  - Returns standardized response    │
│  - Updates metrics                  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│      Error Response (JSON)          │
│  {                                  │
│    "error": {                       │
│      "code": "...",                 │
│      "message": "...",              │
│      "correlation_id": "..."        │
│    }                                │
│  }                                  │
└─────────────────────────────────────┘
```

## 🎯 Custom Exception Types

All custom exceptions inherit from `AppError` and provide consistent structure.

### Exception Hierarchy

| Exception | Status Code | Use Case |
|-----------|-------------|----------|
| `ValidationError` | 400 | Invalid input parameters |
| `NotFoundError` | 404 | Resource not found |
| `AuthenticationError` | 401 | Authentication failed |
| `AuthorizationError` | 403 | Insufficient permissions |
| `RateLimitError` | 429 | Rate limit exceeded |
| `SkillExecutionError` | 500 | Skill execution failed |
| `LLMError` | 502 | LLM API call failed |
| `ExternalServiceError` | 502 | External service (RAG, Wiki) failed |
| `DatabaseError` | 500 | Database operation failed |
| `ConfigurationError` | 500 | Configuration error |

### Usage Examples

```python
from app.exceptions import ValidationError, NotFoundError, LLMError

# Validation error
raise ValidationError(
    message="Invalid email format",
    field="email",
    details={"provided": "invalid-email"}
)

# Not found error
raise NotFoundError(
    resource_type="User",
    resource_id="12345"
)

# LLM error with retry hint
raise LLMError(
    model="gpt-4",
    error_message="Rate limit exceeded",
    retriable=True
)
```

### Error Response Format

All exceptions return a standardized JSON response:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "correlation_id": "abc-123-def-456",
    "details": {
      "field": "email",
      "provided": "invalid-email"
    }
  }
}
```

## 🔄 Exponential Backoff Retry

Automatically retries failed operations with increasing delays.

### Features

- ✅ Exponential backoff with configurable base delay
- ✅ Random jitter to prevent thundering herd
- ✅ Maximum delay cap
- ✅ Configurable retry conditions
- ✅ Works with both sync and async functions

### Usage as Decorator

```python
from app.utils.retry import exponential_backoff

@exponential_backoff(
    max_retries=3,
    base_delay=1.0,
    max_delay=30.0,
    retryable_exceptions=(ConnectionError, TimeoutError)
)
async def call_external_api(url: str) -> dict:
    """This function will automatically retry on transient failures"""
    import httpx
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
        response.raise_for_status()
        return response.json()
```

### Usage with Configuration

```python
from app.utils.retry import retry_with_config, RetryConfig

async def fetch_data(query: str) -> dict:
    # Your logic here
    pass

# Use predefined configuration
result = await retry_with_config(
    fetch_data,
    "search query",
    config=RetryConfig.aggressive(),  # More retries, longer waits
    retryable_exceptions=(TimeoutError,)
)
```

### Retry Configurations

```python
# Quick retry (fast, fewer attempts)
RetryConfig.quick()
# max_retries=2, base_delay=0.5s, max_delay=5.0s

# Standard retry (balanced)
RetryConfig.standard()
# max_retries=3, base_delay=1.0s, max_delay=30.0s

# Aggressive retry (more attempts, longer waits)
RetryConfig.aggressive()
# max_retries=5, base_delay=2.0s, max_delay=120.0s
```

### Delay Calculation

```
Attempt 1: delay = 1.0s  (+/- jitter)
Attempt 2: delay = 2.0s  (+/- jitter)
Attempt 3: delay = 4.0s  (+/- jitter)
Attempt 4: delay = 8.0s  (+/- jitter)
...capped at max_delay
```

## ⚡ Circuit Breaker Pattern

Prevents cascading failures by monitoring failure rates and temporarily blocking requests to failing services.

### States

```
CLOSED ──failures exceed threshold──> OPEN
  ▲                                    │
  │                                    │ after recovery_timeout
  │                                    ▼
  └────test succeeds────────── HALF_OPEN
                                    │
                                    │ test fails
                                    ▼
                                  OPEN
```

### Usage as Decorator

```python
from app.utils.circuit_breaker import CircuitBreakerRegistry

# Get or create circuit breaker
breaker = CircuitBreakerRegistry.get_or_create(
    name="llm_api",
    failure_threshold=5,      # Open after 5 failures
    recovery_timeout=60.0     # Try again after 60 seconds
)

@breaker
async def call_llm(prompt: str) -> str:
    """Protected by circuit breaker"""
    # Your LLM call here
    pass
```

### With Fallback Function

```python
async def primary_service() -> dict:
    """Primary implementation that might fail"""
    raise ConnectionError("Service unavailable")

async def fallback_service() -> dict:
    """Fallback when primary is down"""
    return {"status": "using_cached_data", "data": []}

breaker = CircuitBreaker(
    name="primary_api",
    failure_threshold=3,
    recovery_timeout=30.0,
    fallback_function=fallback_service  # Called when circuit is open
)

protected_call = breaker(primary_service)
result = await protected_call()  # May use fallback
```

### Monitoring Circuit Breakers

```python
from app.utils.circuit_breaker import CircuitBreakerRegistry

# Get states of all circuit breakers
all_states = CircuitBreakerRegistry.get_all_states()

for name, state in all_states.items():
    print(f"{name}: {state['state']}")
    print(f"  Failures: {state['failure_count']}/{state['failure_threshold']}")
    print(f"  Time in state: {state['time_in_current_state']:.1f}s")
```

### Combining Retry + Circuit Breaker

```python
from app.utils.retry import exponential_backoff
from app.utils.circuit_breaker import CircuitBreakerRegistry

@exponential_backoff(max_retries=3, base_delay=1.0)
async def resilient_api_call(url: str) -> dict:
    """Maximum resilience: retry + circuit breaker"""
    
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
```

## 🔍 Correlation ID Tracking

Every request gets a unique correlation ID for end-to-end tracing.

### Automatic Generation

The `CorrelationIDMiddleware` automatically:
1. Generates a UUID for each request (or extracts from header)
2. Stores it in request state
3. Adds it to response headers
4. Includes it in all log entries

### Usage

```python
# Client sends request with correlation ID
curl -H "X-Correlation-ID: my-custom-id" http://localhost:8000/api/v1/chat

# Response includes the same correlation ID
# X-Correlation-ID: my-custom-id

# All logs include correlation_id
logger.info("Processing request")
# Output: INFO - Processing request [correlation_id=my-custom-id]
```

### Tracing Errors

When an error occurs:
1. Error response includes `correlation_id`
2. Full stack trace logged with same `correlation_id`
3. Support team can search logs by `correlation_id` to see complete request flow

## 📊 Integration with Existing Code

### Intent Recognition Node

Already updated with:
- ✅ Exponential backoff retry on LLM failures
- ✅ Circuit breaker for LLM calls
- ✅ Structured error handling
- ✅ Detailed logging

```python
# In app/graph/nodes.py
@exponential_backoff(
    max_retries=3,
    base_delay=1.0,
    retryable_exceptions=(TimeoutError, ConnectionError)
)
async def call_llm_with_retry():
    response = await llm.ainvoke(messages)
    return response

llm_breaker = CircuitBreakerRegistry.get_or_create(
    name="llm_intent_recognition",
    failure_threshold=5,
    recovery_timeout=60.0
)

response = await llm_breaker(call_llm_with_retry)
```

### Skill Execution Node

Already updated with:
- ✅ Per-skill circuit breakers
- ✅ Configurable retry counts
- ✅ Distinguishes retriable vs non-retriable errors
- ✅ Comprehensive error logging

## 🧪 Testing

Run the example script to see all features in action:

```bash
python scripts/example_exception_handling.py
```

## 📈 Monitoring & Metrics

### Prometheus Metrics

The following metrics are automatically tracked:

```prometheus
# Request counter with status codes
request_counter_total{endpoint="/api/v1/chat", method="POST", status="200"}

# Authentication failures
auth_failures_total{endpoint="/auth/login", reason="AUTHENTICATION_FAILED"}

# Circuit breaker states (custom dashboard)
circuit_breaker_state{name="llm_api", state="open"} 1
```

### Log Examples

**Successful Request:**
```
INFO - [intent_recognition] session=abc123, input=What is the policy...
INFO - Intent cache hit for key: 7f3a2b1c...
DEBUG - Processing completed [correlation_id=xyz-789]
```

**Retry Attempt:**
```
WARNING - Retry 1/3 for call_llm_api after 1.23s due to TimeoutError: Request timed out
WARNING - Retry 2/3 for call_llm_api after 2.45s due to TimeoutError: Request timed out
INFO - Request succeeded on retry 2
```

**Circuit Breaker Open:**
```
WARNING - Circuit breaker 'llm_api' failure 5/5: ConnectionError
ERROR - Circuit breaker 'llm_api' OPENED after 5 failures
WARNING - Circuit breaker 'llm_api' is OPEN, rejecting request
INFO - Using fallback for 'llm_api'
```

**Error with Stack Trace:**
```
ERROR - Application error [LLM_API_ERROR]: LLM API call failed
  correlation_id=abc-123-def
  error_code=LLM_API_ERROR
  status_code=502
  path=/api/v1/chat
  method=POST
  stack_trace=Traceback (most recent call last):
    File "app/graph/nodes.py", line 123, in intent_recognition_node
      ...
```

## 🎯 Best Practices

### 1. Use Specific Exceptions

```python
# ✅ Good - Specific exception
raise ValidationError(message="Invalid email", field="email")

# ❌ Bad - Generic exception
raise Exception("Something went wrong")
```

### 2. Provide Context

```python
# ✅ Good - Rich context
raise NotFoundError(
    resource_type="WikiArticle",
    resource_id=entry_id,
    details={"searched_aliases": aliases}
)

# ❌ Bad - No context
raise NotFoundError("Not found")
```

### 3. Retry Wisely

```python
# ✅ Good - Only retry transient errors
@exponential_backoff(retryable_exceptions=(ConnectionError, TimeoutError))
async def call_api():
    pass

# ❌ Bad - Retry everything (including validation errors)
@exponential_backoff()
async def call_api():
    pass
```

### 4. Set Appropriate Thresholds

```python
# For critical services - conservative
CircuitBreakerRegistry.get_or_create(
    name="payment_api",
    failure_threshold=3,      # Fail fast
    recovery_timeout=120.0    # Wait longer before retry
)

# For non-critical services - lenient
CircuitBreakerRegistry.get_or_create(
    name="analytics_api",
    failure_threshold=10,     # Allow more failures
    recovery_timeout=30.0     # Retry sooner
)
```

### 5. Implement Fallbacks

```python
async def get_recommendations(user_id: str) -> list:
    """Primary implementation"""
    # Call ML service
    pass

async def get_default_recommendations() -> list:
    """Fallback - popular items"""
    return ["item1", "item2", "item3"]

breaker = CircuitBreaker(
    name="ml_recommendations",
    fallback_function=get_default_recommendations
)
```

### 6. Monitor Circuit Breakers

Set up alerts for circuit breaker state changes:

```python
# Check every minute
import asyncio

async def monitor_circuit_breakers():
    while True:
        states = CircuitBreakerRegistry.get_all_states()
        
        for name, state in states.items():
            if state['state'] == 'open':
                # Send alert
                send_alert(f"Circuit breaker {name} is OPEN!")
        
        await asyncio.sleep(60)
```

## 🚀 Migration Guide

If you have existing code with simple try-except blocks:

### Before

```python
async def old_code():
    try:
        result = await call_api()
        return result
    except Exception as e:
        logger.error(f"Failed: {e}")
        return None
```

### After

```python
from app.utils.retry import exponential_backoff
from app.utils.circuit_breaker import CircuitBreakerRegistry
from app.exceptions import ExternalServiceError

breaker = CircuitBreakerRegistry.get_or_create("external_api")

@exponential_backoff(max_retries=3, retryable_exceptions=(ConnectionError,))
@breaker
async def new_code():
    try:
        result = await call_api()
        return result
    except ConnectionError as e:
        raise ExternalServiceError(
            service_name="external_api",
            error_message=str(e),
            retriable=True
        ) from e
```

## 📚 Related Documentation

- [Exception Classes Reference](../app/exceptions.py)
- [Retry Utility Reference](../app/utils/retry.py)
- [Circuit Breaker Reference](../app/utils/circuit_breaker.py)
- [Global Exception Handler](../app/middleware/exception_handler.py)

---

**Last Updated:** 2026-04-19  
**Status:** ✅ Production Ready
