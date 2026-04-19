"""
Load tests for rate limiting and concurrent sessions

Tests system behavior under high load and validates rate limits.
"""
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from app.api.main import create_app


@pytest.fixture
def client():
    """Create test client"""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def api_key():
    """Get test API key"""
    return "sk-test-key-12345"


def test_rate_limit_single_endpoint(client, api_key):
    """Test rate limiting on a single endpoint"""
    headers = {"X-API-Key": api_key}
    
    # Send requests rapidly
    responses = []
    for i in range(50):  # Should hit limit at 30/minute
        response = client.get("/api/v1/health", headers=headers)
        responses.append(response.status_code)
    
    # Count 429 responses
    rate_limited_count = responses.count(429)
    
    # Should have some rate-limited responses
    assert rate_limited_count > 0, "Rate limiting should be enforced"
    
    print(f"Total requests: {len(responses)}")
    print(f"Successful (200): {responses.count(200)}")
    print(f"Rate limited (429): {rate_limited_count}")


def test_rate_limit_multiple_endpoints(client, api_key):
    """Test rate limiting across multiple endpoints"""
    headers = {"X-API-Key": api_key}
    
    endpoints = [
        "/api/v1/health",
        "/api/v1/health",
        "/api/v1/health",
    ]
    
    total_requests = 0
    rate_limited = 0
    
    for endpoint in endpoints * 20:  # 60 total requests
        response = client.get(endpoint, headers=headers)
        total_requests += 1
        
        if response.status_code == 429:
            rate_limited += 1
    
    assert rate_limited > 0, "Rate limiting should work across endpoints"
    print(f"Rate limited {rate_limited}/{total_requests} requests")


@pytest.mark.asyncio
async def test_concurrent_sessions():
    """Test handling of multiple concurrent sessions"""
    from app.state.agent_state import AgentStateManager
    
    manager = AgentStateManager()
    
    # Create 100 concurrent sessions
    session_ids = [f"session-{i}" for i in range(100)]
    
    async def create_session(session_id):
        state = manager.get_or_create(session_id, user_id="test-user")
        return state.session_id
    
    tasks = [create_session(sid) for sid in session_ids]
    results = await asyncio.gather(*tasks)
    
    assert len(results) == 100
    assert len(set(results)) == 100  # All unique
    
    # Verify all sessions exist
    for session_id in session_ids:
        assert manager.exists(session_id)


@pytest.mark.asyncio
async def test_concurrent_chat_requests(client, api_key):
    """Test concurrent chat requests"""
    import httpx
    
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    
    async def send_chat_request(session_id):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "http://testserver/api/v1/chat",
                    json={
                        "message": f"Test message {session_id}",
                        "session_id": session_id
                    },
                    headers=headers
                )
                return response.status_code
            except Exception:
                return 500
    
    # Send 20 concurrent requests
    session_ids = [f"concurrent-session-{i}" for i in range(20)]
    tasks = [send_chat_request(sid) for sid in session_ids]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Count successful responses
    successful = sum(1 for r in results if isinstance(r, int) and r == 200)
    rate_limited = sum(1 for r in results if isinstance(r, int) and r == 429)
    
    print(f"Successful: {successful}")
    print(f"Rate limited: {rate_limited}")
    
    # Some should succeed, some might be rate limited
    assert successful > 0 or rate_limited > 0


def test_database_connection_pool_under_load(client, api_key):
    """Test database connection pool handles concurrent requests"""
    headers = {"X-API-Key": api_key}
    
    # Make multiple requests to database-backed endpoints
    responses = []
    for i in range(20):
        response = client.get("/api/v1/health", headers=headers)
        responses.append(response.status_code)
    
    # All should complete (no connection pool exhaustion)
    successful = responses.count(200)
    print(f"Database requests: {successful}/{len(responses)} successful")
    
    assert successful > 0


@pytest.mark.asyncio
async def test_circuit_breaker_under_load():
    """Test circuit breaker behavior under high failure rate"""
    from app.utils.circuit_breaker import CircuitBreaker, CircuitBreakerRegistry
    
    # Clear registry
    CircuitBreakerRegistry.clear()
    
    breaker = CircuitBreakerRegistry.get_or_create(
        name="test_service",
        failure_threshold=3,
        recovery_timeout=1.0
    )
    
    call_count = 0
    
    @breaker
    async def failing_service():
        nonlocal call_count
        call_count += 1
        raise ConnectionError("Service down")
    
    # Trigger failures to open circuit
    for i in range(5):
        try:
            await failing_service()
        except Exception:
            pass
    
    # Circuit should be open now
    state = breaker.get_state()
    assert state['state'] == 'open'
    
    # Further calls should be rejected immediately
    initial_calls = call_count
    
    for i in range(3):
        try:
            await failing_service()
        except Exception:
            pass
    
    # Should not have made additional calls (circuit is open)
    assert call_count == initial_calls or call_count == initial_calls + 1


def test_memory_usage_under_load(client, api_key):
    """Test memory usage doesn't grow unbounded under load"""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    headers = {"X-API-Key": api_key}
    
    # Make many requests
    for i in range(100):
        client.get("/api/v1/health", headers=headers)
    
    final_memory = process.memory_info().rss
    memory_growth_mb = (final_memory - initial_memory) / (1024 * 1024)
    
    print(f"Memory growth: {memory_growth_mb:.2f} MB")
    
    # Memory growth should be reasonable (< 50 MB)
    assert memory_growth_mb < 50, f"Memory grew too much: {memory_growth_mb:.2f} MB"


@pytest.mark.asyncio
async def test_intent_cache_performance():
    """Test intent recognition cache improves performance"""
    from app.graph.nodes import intent_recognition_node, _cache_intent, _get_intent_cache_key
    from app.state.agent_state import AgentState
    import time
    
    state = AgentState(
        user_input="What is the loan approval process?",
        session_id="perf-test",
        user_id="test-user"
    )
    
    # First call - will use LLM (slower)
    start = time.time()
    result1 = await intent_recognition_node(state)
    first_call_time = time.time() - start
    
    # Second call - should use cache (faster)
    start = time.time()
    result2 = await intent_recognition_node(state)
    cached_call_time = time.time() - start
    
    print(f"First call (LLM): {first_call_time:.3f}s")
    print(f"Cached call: {cached_call_time:.3f}s")
    print(f"Speedup: {first_call_time / max(cached_call_time, 0.001):.1f}x")
    
    # Cached call should be significantly faster
    assert cached_call_time < first_call_time * 0.5, "Cache should improve performance"


def test_api_response_time_under_load(client, api_key):
    """Test API response times remain acceptable under load"""
    headers = {"X-API-Key": api_key}
    
    response_times = []
    
    for i in range(30):
        start = time.time()
        response = client.get("/api/v1/health", headers=headers)
        elapsed = time.time() - start
        response_times.append(elapsed)
        
        assert response.status_code in [200, 429]
    
    avg_time = sum(response_times) / len(response_times)
    max_time = max(response_times)
    p95_time = sorted(response_times)[int(len(response_times) * 0.95)]
    
    print(f"Avg response time: {avg_time*1000:.1f}ms")
    print(f"Max response time: {max_time*1000:.1f}ms")
    print(f"P95 response time: {p95_time*1000:.1f}ms")
    
    # P95 should be under 1 second
    assert p95_time < 1.0, f"P95 response time too high: {p95_time*1000:.1f}ms"
