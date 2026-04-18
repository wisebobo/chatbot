"""
Monitoring and logging module
Provides structured logging and Prometheus metrics
"""
import logging
import sys
from typing import Literal

try:
    import structlog
    HAS_STRUCTLOG = True
except ImportError:
    HAS_STRUCTLOG = False


def setup_logging(
    log_level: str = "INFO",
    log_format: Literal["json", "text"] = "json",
) -> None:
    """
    Initialize logging configuration
    
    Args:
        log_level: log level DEBUG/INFO/WARNING/ERROR
        log_format: output format json (structured) or text (readable)
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    if HAS_STRUCTLOG and log_format == "json":
        structlog.configure(
            processors=[
                structlog.stdlib.add_log_level,
                structlog.stdlib.add_logger_name,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    else:
        logging.basicConfig(
            level=level,
            format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            stream=sys.stdout,
        )

    # reduce third-party library noise
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
