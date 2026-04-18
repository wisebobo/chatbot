"""
Prometheus monitoring metric definitions
"""
try:
    from prometheus_client import Counter, Gauge, Histogram, Summary

    # request counter
    request_counter = Counter(
        "agent_requests_total",
        "Total number of agent requests",
        ["endpoint", "status"],
    )

    # request latency histogram
    request_duration = Histogram(
        "agent_request_duration_seconds",
        "Request duration in seconds",
        ["endpoint"],
        buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0],
    )

    # skill execution counter
    skill_execution_counter = Counter(
        "skill_executions_total",
        "Total skill executions",
        ["skill_name", "status"],
    )

    # active session gauge
    active_sessions = Gauge(
        "agent_active_sessions",
        "Number of active agent sessions",
    )

    # LLM call latency
    llm_latency = Histogram(
        "llm_call_duration_seconds",
        "LLM call duration in seconds",
        buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    )

    PROMETHEUS_AVAILABLE = True

except ImportError:
    # Provide a no-op implementation when Prometheus is not installed
    PROMETHEUS_AVAILABLE = False

    class _NoopMetric:
        def labels(self, **kwargs): return self
        def inc(self, *a, **kw): pass
        def dec(self, *a, **kw): pass
        def set(self, *a, **kw): pass
        def observe(self, *a, **kw): pass
        def time(self): 
            from contextlib import contextmanager
            @contextmanager
            def noop():
                yield
            return noop()

    request_counter = _NoopMetric()
    request_duration = _NoopMetric()
    skill_execution_counter = _NoopMetric()
    active_sessions = _NoopMetric()
    llm_latency = _NoopMetric()


def get_metrics():
    """Return the current metrics status summary (for health checks)"""
    return {"prometheus_available": PROMETHEUS_AVAILABLE}
