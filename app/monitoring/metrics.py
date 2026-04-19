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