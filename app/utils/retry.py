"""
Exponential Backoff Retry Utility

Provides intelligent retry logic with:
- Exponential backoff with jitter
- Maximum retry attempts
- Configurable retry conditions
- Circuit breaker integration
"""
import asyncio
import logging
import random
import time
from functools import wraps
from typing import Callable, Optional, Tuple, Type, Union

logger = logging.getLogger(__name__)


class RetryExhaustedError(Exception):
    """Raised when all retry attempts are exhausted"""
    
    def __init__(self, message: str, last_exception: Optional[Exception] = None):
        super().__init__(message)
        self.last_exception = last_exception


def exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[int, Exception, float], None]] = None
):
    """
    Decorator for automatic retry with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay cap in seconds (default: 60.0)
        exponential_base: Base for exponential calculation (default: 2.0)
        jitter: Add random jitter to prevent thundering herd (default: True)
        retryable_exceptions: Tuple of exception types that should trigger retry
                             If None, retries on all exceptions
        on_retry: Callback function(retry_count, exception, delay) called before each retry
    
    Returns:
        Decorated function with retry logic
    
    Example:
        @exponential_backoff(max_retries=3, base_delay=1.0)
        async def call_llm_api(prompt: str) -> str:
            # LLM API call that might fail
            pass
        
        # Or with specific exceptions
        @exponential_backoff(
            max_retries=5,
            retryable_exceptions=(ConnectionError, TimeoutError)
        )
        async def fetch_data(url: str) -> dict:
            pass
    """
    
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                
                except Exception as e:
                    last_exception = e
                    
                    # Check if this exception is retryable
                    if retryable_exceptions and not isinstance(e, retryable_exceptions):
                        logger.error(f"Non-retryable exception: {type(e).__name__}: {e}")
                        raise
                    
                    # If we've exhausted retries, raise
                    if attempt >= max_retries:
                        logger.error(
                            f"All {max_retries} retry attempts exhausted for {func.__name__}",
                            exc_info=True
                        )
                        raise RetryExhaustedError(
                            f"Function '{func.__name__}' failed after {max_retries} retries",
                            last_exception=e
                        ) from e
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    # Add jitter to prevent synchronized retries
                    if jitter:
                        delay = delay * (0.5 + random.random() * 0.5)
                    
                    # Log retry attempt
                    logger.warning(
                        f"Retry {attempt + 1}/{max_retries} for {func.__name__} "
                        f"after {delay:.2f}s due to {type(e).__name__}: {e}"
                    )
                    
                    # Call retry callback if provided
                    if on_retry:
                        try:
                            on_retry(attempt + 1, e, delay)
                        except Exception as callback_error:
                            logger.error(f"Retry callback error: {callback_error}")
                    
                    # Wait before retry
                    await asyncio.sleep(delay)
            
            # Should never reach here, but just in case
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                
                except Exception as e:
                    last_exception = e
                    
                    # Check if this exception is retryable
                    if retryable_exceptions and not isinstance(e, retryable_exceptions):
                        logger.error(f"Non-retryable exception: {type(e).__name__}: {e}")
                        raise
                    
                    # If we've exhausted retries, raise
                    if attempt >= max_retries:
                        logger.error(
                            f"All {max_retries} retry attempts exhausted for {func.__name__}",
                            exc_info=True
                        )
                        raise RetryExhaustedError(
                            f"Function '{func.__name__}' failed after {max_retries} retries",
                            last_exception=e
                        ) from e
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    # Add jitter to prevent synchronized retries
                    if jitter:
                        delay = delay * (0.5 + random.random() * 0.5)
                    
                    # Log retry attempt
                    logger.warning(
                        f"Retry {attempt + 1}/{max_retries} for {func.__name__} "
                        f"after {delay:.2f}s due to {type(e).__name__}: {e}"
                    )
                    
                    # Call retry callback if provided
                    if on_retry:
                        try:
                            on_retry(attempt + 1, e, delay)
                        except Exception as callback_error:
                            logger.error(f"Retry callback error: {callback_error}")
                    
                    # Wait before retry
                    time.sleep(delay)
            
            # Should never reach here, but just in case
            raise last_exception
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class RetryConfig:
    """Configuration class for retry behavior"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    @classmethod
    def quick(cls) -> 'RetryConfig':
        """Quick retry configuration (fast, fewer attempts)"""
        return cls(max_retries=2, base_delay=0.5, max_delay=5.0)
    
    @classmethod
    def standard(cls) -> 'RetryConfig':
        """Standard retry configuration (balanced)"""
        return cls(max_retries=3, base_delay=1.0, max_delay=30.0)
    
    @classmethod
    def aggressive(cls) -> 'RetryConfig':
        """Aggressive retry configuration (more attempts, longer waits)"""
        return cls(max_retries=5, base_delay=2.0, max_delay=120.0)


async def retry_with_config(
    func: Callable,
    *args,
    config: Optional[RetryConfig] = None,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    **kwargs
):
    """
    Execute function with retry configuration
    
    Args:
        func: Async function to execute
        config: Retry configuration (uses standard if not provided)
        retryable_exceptions: Exceptions that should trigger retry
        *args, **kwargs: Arguments to pass to function
    
    Returns:
        Function result
    
    Example:
        result = await retry_with_config(
            call_llm_api,
            prompt="Hello",
            config=RetryConfig.aggressive(),
            retryable_exceptions=(TimeoutError, ConnectionError)
        )
    """
    if config is None:
        config = RetryConfig.standard()
    
    last_exception = None
    
    for attempt in range(config.max_retries + 1):
        try:
            return await func(*args, **kwargs)
        
        except Exception as e:
            last_exception = e
            
            # Check if retryable
            if retryable_exceptions and not isinstance(e, retryable_exceptions):
                raise
            
            # Exhausted retries
            if attempt >= config.max_retries:
                logger.error(
                    f"All {config.max_retries} retries exhausted",
                    exc_info=True
                )
                raise RetryExhaustedError(
                    f"Function failed after {config.max_retries} retries",
                    last_exception=e
                ) from e
            
            # Calculate delay
            delay = min(
                config.base_delay * (config.exponential_base ** attempt),
                config.max_delay
            )
            
            if config.jitter:
                delay = delay * (0.5 + random.random() * 0.5)
            
            logger.warning(
                f"Retry {attempt + 1}/{config.max_retries} after {delay:.2f}s"
            )
            
            await asyncio.sleep(delay)
    
    raise last_exception
