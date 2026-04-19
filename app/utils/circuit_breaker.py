"""
Circuit Breaker Pattern Implementation

Prevents cascading failures by:
- Monitoring failure rates
- Automatically opening circuit when threshold exceeded
- Allowing periodic test requests in half-open state
- Providing fallback mechanisms
"""
import logging
import time
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing, reject requests
    HALF_OPEN = "half_open" # Testing if service recovered


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""
    
    def __init__(self, service_name: str, message: str = "Circuit breaker is open"):
        super().__init__(f"{service_name}: {message}")
        self.service_name = service_name


class CircuitBreaker:
    """
    Circuit Breaker implementation
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service failing, requests immediately rejected
    - HALF_OPEN: Testing if service recovered, limited requests allowed
    
    Transitions:
    - CLOSED -> OPEN: When failure count exceeds threshold
    - OPEN -> HALF_OPEN: After timeout period
    - HALF_OPEN -> CLOSED: When test request succeeds
    - HALF_OPEN -> OPEN: When test request fails
    
    Example:
        breaker = CircuitBreaker(
            name="llm_api",
            failure_threshold=5,
            recovery_timeout=60
        )
        
        @breaker
        async def call_llm(prompt: str) -> str:
            # LLM API call
            pass
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Optional[type] = Exception,
        fallback_function: Optional[Callable] = None
    ):
        """
        Initialize circuit breaker
        
        Args:
            name: Unique name for this circuit breaker
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying again (half-open)
            expected_exception: Exception type that counts as failure
            fallback_function: Function to call when circuit is open
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception or Exception
        self.fallback_function = fallback_function
        
        # State tracking
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.last_state_change_time = time.time()
        
        logger.info(
            f"Circuit breaker '{name}' initialized "
            f"(threshold={failure_threshold}, timeout={recovery_timeout}s)"
        )
    
    def __call__(self, func: Callable):
        """Decorator to wrap function with circuit breaker"""
        
        async def async_wrapper(*args, **kwargs):
            return await self._execute(func, *args, **kwargs)
        
        def sync_wrapper(*args, **kwargs):
            return self._execute_sync(func, *args, **kwargs)
        
        # Return appropriate wrapper
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    async def _execute(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker logic (async)"""
        
        # Check if we should transition from OPEN to HALF_OPEN
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info(
                    f"Circuit breaker '{self.name}' transitioning to HALF_OPEN"
                )
                self.state = CircuitState.HALF_OPEN
                self.last_state_change_time = time.time()
            else:
                # Circuit still open, use fallback or raise error
                logger.warning(
                    f"Circuit breaker '{self.name}' is OPEN, rejecting request"
                )
                
                if self.fallback_function:
                    logger.info(f"Using fallback for '{self.name}'")
                    if callable(self.fallback_function):
                        import inspect
                        if inspect.iscoroutinefunction(self.fallback_function):
                            return await self.fallback_function(*args, **kwargs)
                        else:
                            return self.fallback_function(*args, **kwargs)
                
                raise CircuitBreakerError(self.name)
        
        try:
            # Execute the function
            result = await func(*args, **kwargs)
            
            # Success - update counters
            self._on_success()
            
            return result
        
        except self.expected_exception as e:
            # Failure - update counters
            self._on_failure(e)
            
            # Re-raise or use fallback
            if self.state == CircuitState.OPEN and self.fallback_function:
                logger.info(f"Using fallback after failure for '{self.name}'")
                if callable(self.fallback_function):
                    import inspect
                    if inspect.iscoroutinefunction(self.fallback_function):
                        return await self.fallback_function(*args, **kwargs)
                    else:
                        return self.fallback_function(*args, **kwargs)
            
            raise
    
    def _execute_sync(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker logic (sync)"""
        
        # Check if we should transition from OPEN to HALF_OPEN
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info(
                    f"Circuit breaker '{self.name}' transitioning to HALF_OPEN"
                )
                self.state = CircuitState.HALF_OPEN
                self.last_state_change_time = time.time()
            else:
                # Circuit still open, use fallback or raise error
                logger.warning(
                    f"Circuit breaker '{self.name}' is OPEN, rejecting request"
                )
                
                if self.fallback_function:
                    logger.info(f"Using fallback for '{self.name}'")
                    if callable(self.fallback_function):
                        return self.fallback_function(*args, **kwargs)
                
                raise CircuitBreakerError(self.name)
        
        try:
            # Execute the function
            result = func(*args, **kwargs)
            
            # Success - update counters
            self._on_success()
            
            return result
        
        except self.expected_exception as e:
            # Failure - update counters
            self._on_failure(e)
            
            # Re-raise or use fallback
            if self.state == CircuitState.OPEN and self.fallback_function:
                logger.info(f"Using fallback after failure for '{self.name}'")
                if callable(self.fallback_function):
                    return self.fallback_function(*args, **kwargs)
            
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        
        time_since_failure = time.time() - self.last_failure_time
        return time_since_failure >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful execution"""
        if self.state == CircuitState.HALF_OPEN:
            # Test succeeded, close circuit
            logger.info(
                f"Circuit breaker '{self.name}' closing (test succeeded)"
            )
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_state_change_time = time.time()
        else:
            # Reset failure count on success
            self.failure_count = 0
            self.success_count += 1
    
    def _on_failure(self, exception: Exception):
        """Handle failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        logger.warning(
            f"Circuit breaker '{self.name}' failure {self.failure_count}/"
            f"{self.failure_threshold}: {type(exception).__name__}"
        )
        
        if self.state == CircuitState.HALF_OPEN:
            # Test failed, reopen circuit
            logger.error(
                f"Circuit breaker '{self.name}' reopening (test failed)"
            )
            self.state = CircuitState.OPEN
            self.last_state_change_time = time.time()
        
        elif self.failure_count >= self.failure_threshold:
            # Threshold exceeded, open circuit
            logger.error(
                f"Circuit breaker '{self.name}' OPENED after "
                f"{self.failure_count} failures"
            )
            self.state = CircuitState.OPEN
            self.last_state_change_time = time.time()
    
    def get_state(self) -> dict:
        """Get current circuit breaker state for monitoring"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "last_failure_time": self.last_failure_time,
            "time_in_current_state": time.time() - self.last_state_change_time
        }
    
    def reset(self):
        """Manually reset circuit breaker to closed state"""
        logger.info(f"Circuit breaker '{self.name}' manually reset")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_state_change_time = time.time()


class CircuitBreakerRegistry:
    """
    Registry for managing multiple circuit breakers
    
    Provides centralized management and monitoring of all circuit breakers
    in the application.
    """
    
    _instance = None
    _breakers = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_or_create(
        cls,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        fallback_function: Optional[Callable] = None
    ) -> CircuitBreaker:
        """Get existing circuit breaker or create new one"""
        if name not in cls._breakers:
            cls._breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                fallback_function=fallback_function
            )
        
        return cls._breakers[name]
    
    @classmethod
    def get(cls, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name"""
        return cls._breakers.get(name)
    
    @classmethod
    def get_all_states(cls) -> dict:
        """Get states of all circuit breakers"""
        return {
            name: breaker.get_state()
            for name, breaker in cls._breakers.items()
        }
    
    @classmethod
    def reset_all(cls):
        """Reset all circuit breakers"""
        for breaker in cls._breakers.values():
            breaker.reset()
    
    @classmethod
    def clear(cls):
        """Clear all circuit breakers (for testing)"""
        cls._breakers.clear()
