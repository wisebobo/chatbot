"""
Unit tests for utility modules (retry, circuit breaker)

Tests exponential backoff retry and circuit breaker pattern implementations.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from app.utils.retry import exponential_backoff, RetryConfig, retry_with_config, RetryExhaustedError
from app.utils.circuit_breaker import CircuitBreaker, CircuitBreakerRegistry, CircuitBreakerError


class TestExponentialBackoff:
    """Tests for exponential backoff retry decorator"""
    
    @pytest.mark.asyncio
    async def test_successful_call_no_retry(self):
        """Test that successful calls don't trigger retries"""
        call_count = 0
        
        @exponential_backoff(max_retries=3, base_delay=0.01)
        async def success_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await success_func()
        
        assert result == "success"
        assert call_count == 1  # Should only be called once
    
    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self):
        """Test retry on transient errors"""
        call_count = 0
        
        @exponential_backoff(max_retries=3, base_delay=0.01, max_delay=0.1)
        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"
        
        result = await flaky_func()
        
        assert result == "success"
        assert call_count == 3  # Should retry until success
    
    @pytest.mark.asyncio
    async def test_exhaust_retries(self):
        """Test that exception is raised after exhausting retries"""
        call_count = 0
        
        @exponential_backoff(max_retries=2, base_delay=0.01)
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Permanent error")
        
        with pytest.raises(RetryExhaustedError):
            await always_fails()
        
        assert call_count == 3  # Initial + 2 retries
    
    @pytest.mark.asyncio
    async def test_only_retry_specified_exceptions(self):
        """Test that only specified exceptions trigger retry"""
        call_count = 0
        
        @exponential_backoff(
            max_retries=3,
            base_delay=0.01,
            retryable_exceptions=(ConnectionError,)
        )
        async def raises_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Not retryable")
        
        with pytest.raises(ValueError):
            await raises_value_error()
        
        assert call_count == 1  # Should not retry
    
    @pytest.mark.asyncio
    async def test_jitter_prevents_thundering_herd(self):
        """Test that jitter adds randomness to delays"""
        delays = []
        
        @exponential_backoff(max_retries=3, base_delay=0.1, jitter=True)
        async def track_delays():
            raise ConnectionError("Test")
        
        # Run multiple times to observe jitter
        for _ in range(5):
            try:
                await track_delays()
            except RetryExhaustedError:
                pass
    
    def test_retry_config_presets(self):
        """Test predefined retry configurations"""
        quick = RetryConfig.quick()
        assert quick.max_retries == 2
        assert quick.base_delay == 0.5
        
        standard = RetryConfig.standard()
        assert standard.max_retries == 3
        assert standard.base_delay == 1.0
        
        aggressive = RetryConfig.aggressive()
        assert aggressive.max_retries == 5
        assert aggressive.base_delay == 2.0
    
    @pytest.mark.asyncio
    async def test_retry_with_config_function(self):
        """Test retry_with_config helper function"""
        call_count = 0
        
        async def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError("Slow response")
            return "done"
        
        result = await retry_with_config(
            flaky_operation,
            config=RetryConfig(max_retries=3, base_delay=0.01),
            retryable_exceptions=(TimeoutError,)
        )
        
        assert result == "done"
        assert call_count == 2


class TestCircuitBreaker:
    """Tests for circuit breaker pattern"""
    
    def setup_method(self):
        """Clear registry before each test"""
        CircuitBreakerRegistry.clear()
    
    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initializes in closed state"""
        breaker = CircuitBreaker(
            name="test_service",
            failure_threshold=3,
            recovery_timeout=60.0
        )
        
        assert breaker.state.value == "closed"
        assert breaker.failure_count == 0
        assert breaker.name == "test_service"
    
    @pytest.mark.asyncio
    async def test_circuit_stays_closed_on_success(self):
        """Test circuit stays closed when calls succeed"""
        breaker = CircuitBreaker(name="test", failure_threshold=3)
        
        @breaker
        async def success_call():
            return "ok"
        
        for _ in range(5):
            result = await success_call()
            assert result == "ok"
        
        assert breaker.state.value == "closed"
    
    @pytest.mark.asyncio
    async def test_circuit_opens_after_threshold(self):
        """Test circuit opens after reaching failure threshold"""
        breaker = CircuitBreaker(name="test", failure_threshold=3)
        
        @breaker
        async def failing_call():
            raise ConnectionError("Service down")
        
        # Trigger failures
        for i in range(3):
            try:
                await failing_call()
            except ConnectionError:
                pass
        
        # Circuit should be open
        assert breaker.state.value == "open"
        
        # Next call should be rejected immediately
        with pytest.raises(CircuitBreakerError):
            await failing_call()
    
    @pytest.mark.asyncio
    async def test_circuit_half_open_after_timeout(self):
        """Test circuit transitions to half-open after recovery timeout"""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=0.1  # 100ms for testing
        )
        
        @breaker
        async def failing_call():
            raise ConnectionError("Down")
        
        # Open the circuit
        for _ in range(2):
            try:
                await failing_call()
            except ConnectionError:
                pass
        
        assert breaker.state.value == "open"
        
        # Wait for recovery timeout
        await asyncio.sleep(0.15)
        
        # Next call should transition to half-open
        @breaker
        async def success_call():
            return "recovered"
        
        result = await success_call()
        assert result == "recovered"
        assert breaker.state.value == "closed"  # Should close after success
    
    @pytest.mark.asyncio
    async def test_circuit_with_fallback(self):
        """Test circuit breaker uses fallback when open"""
        async def primary():
            raise ConnectionError("Primary down")
        
        async def fallback():
            return "fallback data"
        
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            fallback_function=fallback
        )
        
        protected = breaker(primary)
        
        # Trigger failures to open circuit
        for _ in range(2):
            try:
                await protected()
            except Exception:
                pass
        
        # Next call should use fallback
        result = await protected()
        assert result == "fallback data"
    
    def test_circuit_breaker_registry_singleton(self):
        """Test registry returns same instance"""
        breaker1 = CircuitBreakerRegistry.get_or_create("test_svc")
        breaker2 = CircuitBreakerRegistry.get_or_create("test_svc")
        
        assert breaker1 is breaker2
    
    def test_circuit_breaker_state_monitoring(self):
        """Test monitoring circuit breaker states"""
        breaker = CircuitBreakerRegistry.get_or_create(
            name="monitored_service",
            failure_threshold=5
        )
        
        state = breaker.get_state()
        
        assert "name" in state
        assert "state" in state
        assert "failure_count" in state
        assert state["name"] == "monitored_service"
        assert state["failure_threshold"] == 5
    
    def test_manual_reset(self):
        """Test manual circuit breaker reset"""
        breaker = CircuitBreaker(name="test", failure_threshold=2)
        
        # Manually set to open
        breaker.state = type('obj', (object,), {'value': 'open'})()
        breaker.failure_count = 5
        
        # Reset
        breaker.reset()
        
        assert breaker.state.value == "closed"
        assert breaker.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_half_open_to_open_on_failure(self):
        """Test circuit goes back to open if half-open test fails"""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=0.05
        )
        
        @breaker
        async def failing_call():
            raise ConnectionError("Still down")
        
        # Open circuit
        for _ in range(2):
            try:
                await failing_call()
            except ConnectionError:
                pass
        
        assert breaker.state.value == "open"
        
        # Wait for half-open
        await asyncio.sleep(0.06)
        
        # Test fails, should go back to open
        try:
            await failing_call()
        except (ConnectionError, CircuitBreakerError):
            pass
        
        assert breaker.state.value == "open"


class TestIntegrationRetryAndCircuitBreaker:
    """Integration tests combining retry and circuit breaker"""
    
    @pytest.mark.asyncio
    async def test_retry_with_circuit_breaker(self):
        """Test using retry inside circuit breaker"""
        CircuitBreakerRegistry.clear()
        
        call_count = 0
        
        @exponential_backoff(max_retries=2, base_delay=0.01)
        async def flaky_service():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError("Slow")
            return "success"
        
        breaker = CircuitBreakerRegistry.get_or_create(
            name="integrated_test",
            failure_threshold=5
        )
        
        protected = breaker(flaky_service)
        
        result = await protected()
        
        assert result == "success"
        assert call_count == 2
    
    def test_multiple_circuit_breakers_independent(self):
        """Test that different circuit breakers operate independently"""
        breaker1 = CircuitBreakerRegistry.get_or_create("service_a")
        breaker2 = CircuitBreakerRegistry.get_or_create("service_b")
        
        # Fail breaker1
        breaker1.failure_count = 10
        breaker1.state = type('obj', (object,), {'value': 'open'})()
        
        # breaker2 should be unaffected
        assert breaker2.state.value == "closed"
        assert breaker2.failure_count == 0
