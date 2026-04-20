"""
Prometheus monitoring metric definitions
Extended for production observability (Phase 3)
"""
try:
    from prometheus_client import Counter, Gauge, Histogram, Summary

    # ===== Basic Request Metrics =====
    request_counter = Counter(
        "agent_requests_total",
        "Total number of agent requests",
        ["endpoint", "status"],
    )

    request_duration = Histogram(
        "agent_request_duration_seconds",
        "Request duration in seconds",
        ["endpoint"],
        buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0],
    )

    # ===== Authentication & Security Metrics =====
    auth_failures = Counter(
        "authentication_failures_total",
        "Total authentication failures",
        ["endpoint", "reason"],
    )

    rate_limit_exceeded = Counter(
        "rate_limit_exceeded_total",
        "Total rate limit violations",
        ["endpoint", "client_ip"],
    )

    active_api_keys = Gauge(
        "active_api_keys_total",
        "Number of active API keys"
    )

    api_key_requests = Counter(
        "api_key_requests_total",
        "Total API key authenticated requests",
        ["key_name", "status"],
    )

    # ===== Audit Log Metrics =====
    audit_logs_created = Counter(
        "audit_logs_created_total",
        "Total audit log entries created",
        ["action_type"],
    )

    # ===== Skill Execution Metrics =====
    skill_execution_counter = Counter(
        "skill_executions_total",
        "Total skill executions",
        ["skill_name", "status"],
    )

    skill_execution_duration = Histogram(
        "skill_execution_duration_seconds",
        "Skill execution duration in seconds",
        ["skill_name"],
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    )

    # ===== Session Management Metrics =====
    active_sessions = Gauge(
        "agent_active_sessions",
        "Number of active agent sessions",
    )

    session_duration = Histogram(
        "session_duration_seconds",
        "Session duration in seconds",
        buckets=[60, 300, 600, 1800, 3600, 7200],
    )

    # ===== LLM Performance Metrics =====
    llm_latency = Histogram(
        "llm_call_duration_seconds",
        "LLM call duration in seconds",
        ["model", "operation"],
        buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    )

    llm_calls_total = Counter(
        "llm_calls_total",
        "Total LLM API calls",
        ["model", "status"],
    )

    llm_token_usage = Counter(
        "llm_tokens_total",
        "Total tokens used",
        ["model", "type"],  # type: prompt or completion
    )

    llm_errors = Counter(
        "llm_errors_total",
        "Total LLM API errors",
        ["model", "error_type"],
    )

    # ===== Wiki Knowledge Base Metrics =====
    wiki_articles_total = Gauge(
        "wiki_articles_total",
        "Total number of wiki articles"
    )

    wiki_feedback_submitted = Counter(
        "wiki_feedback_total",
        "Total wiki feedback submissions",
        ["entry_id", "is_positive"],
    )

    wiki_low_confidence_alerts = Counter(
        "wiki_low_confidence_alerts_total",
        "Alerts for low-confidence wiki articles",
        ["entry_id", "confidence"],
    )

    wiki_compilation_duration = Histogram(
        "wiki_compilation_duration_seconds",
        "Wiki compilation duration in seconds",
        buckets=[1.0, 5.0, 10.0, 30.0, 60.0],
    )

    # ===== Error Tracking Metrics =====
    api_error_rate = Counter(
        "api_error_total",
        "Total API errors",
        ["endpoint", "error_type", "status_code"],
    )

    exception_count = Counter(
        "exceptions_total",
        "Total exceptions raised",
        ["exception_type", "module"],
    )

    # ===== Business Metrics =====
    user_logins = Counter(
        "user_logins_total",
        "Total user logins via LDAP",
        ["status"],  # success or failure
    )

    jwt_tokens_issued = Counter(
        "jwt_tokens_issued_total",
        "Total JWT tokens issued",
        ["token_type"],  # access or refresh
    )

    ldap_auth_duration = Histogram(
        "ldap_authentication_duration_seconds",
        "LDAP authentication duration in seconds",
        ["status"],
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
    )

    # ===== System Resource Metrics =====
    memory_usage_bytes = Gauge(
        "process_memory_bytes",
        "Process memory usage in bytes"
    )

    cpu_usage_percent = Gauge(
        "process_cpu_percent",
        "Process CPU usage percentage"
    )

except ImportError:
    # Prometheus not installed, create dummy metrics
    class DummyMetric:
        def __init__(self, *args, **kwargs):
            pass
        def inc(self, *args, **kwargs):
            pass
        def set(self, *args, **kwargs):
            pass
        def observe(self, *args, **kwargs):
            pass
    
    request_counter = DummyMetric()
    request_duration = DummyMetric()
    auth_failures = DummyMetric()
    rate_limit_exceeded = DummyMetric()
    active_api_keys = DummyMetric()
    api_key_requests = DummyMetric()
    audit_logs_created = DummyMetric()
    skill_execution_counter = DummyMetric()
    skill_execution_duration = DummyMetric()
    active_sessions = DummyMetric()
    session_duration = DummyMetric()
    llm_latency = DummyMetric()
    llm_calls_total = DummyMetric()
    llm_token_usage = DummyMetric()
    llm_errors = DummyMetric()
    wiki_articles_total = DummyMetric()
    wiki_feedback_submitted = DummyMetric()
    wiki_low_confidence_alerts = DummyMetric()
    wiki_compilation_duration = DummyMetric()
    api_error_rate = DummyMetric()
    exception_count = DummyMetric()
    user_logins = DummyMetric()
    jwt_tokens_issued = DummyMetric()
    ldap_auth_duration = DummyMetric()
    memory_usage_bytes = DummyMetric()
    cpu_usage_percent = DummyMetric()


def get_metrics():
    """Get all metrics as a dictionary"""
    import sys
    if 'prometheus_client' in sys.modules:
        return {
            'request_counter': request_counter,
            'request_duration': request_duration,
            'auth_failures': auth_failures,
            'rate_limit_exceeded': rate_limit_exceeded,
            'active_api_keys': active_api_keys,
            'api_key_requests': api_key_requests,
            'audit_logs_created': audit_logs_created,
            'skill_execution_counter': skill_execution_counter,
            'skill_execution_duration': skill_execution_duration,
            'active_sessions': active_sessions,
            'session_duration': session_duration,
            'llm_latency': llm_latency,
            'llm_calls_total': llm_calls_total,
            'llm_token_usage': llm_token_usage,
            'llm_errors': llm_errors,
            'wiki_articles_total': wiki_articles_total,
            'wiki_feedback_submitted': wiki_feedback_submitted,
            'wiki_low_confidence_alerts': wiki_low_confidence_alerts,
            'wiki_compilation_duration': wiki_compilation_duration,
            'api_error_rate': api_error_rate,
            'exception_count': exception_count,
            'user_logins': user_logins,
            'jwt_tokens_issued': jwt_tokens_issued,
            'ldap_auth_duration': ldap_auth_duration,
            'memory_usage_bytes': memory_usage_bytes,
            'cpu_usage_percent': cpu_usage_percent,
        }
    return {}
