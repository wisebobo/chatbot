"""
LangGraph orchestration layer - graph construction and initialization
Combines nodes and routing into a complete StateGraph and configures the checkpointer
"""
import logging
from typing import Optional

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    error_handler_node,
    intent_recognition_node,
    response_generation_node,
    skill_execution_node,
)
from app.graph.routing import route_after_intent_with_error, route_after_skill
from app.state.agent_state import AgentState

logger = logging.getLogger(__name__)

# global graph instance
_graph = None


def build_graph(checkpointer=None):
    """
    Build the LangGraph StateGraph
    
    Args:
        checkpointer: state persistence layer, defaults to MemorySaver (replace with PostgresSaver in production)
        
    Returns:
        compiled CompiledGraph
    """
    logger.info("Building LangGraph StateGraph...")

    # Use in-memory checkpointer (development only)
    if checkpointer is None:
        checkpointer = MemorySaver()
        logger.warning("Using MemorySaver checkpointer (dev only). Use PostgresSaver in production.")

    builder = StateGraph(AgentState)

    # ---- register nodes ----
    builder.add_node("intent_recognition", intent_recognition_node)
    builder.add_node("skill_execution", skill_execution_node)
    builder.add_node("response_generation", response_generation_node)
    builder.add_node("error_handler", error_handler_node)

    # ---- define edges ----
    # entry -> intent recognition
    builder.add_edge(START, "intent_recognition")

    # intent recognition -> skill execution or direct response (conditional routing)
    builder.add_conditional_edges(
        "intent_recognition",
        route_after_intent_with_error,
        {
            "skill_execution": "skill_execution",
            "response_generation": "response_generation",
            "error_handler": "error_handler",
        },
    )

    # skill execution -> response generation or error handler or pause (conditional routing)
    builder.add_conditional_edges(
        "skill_execution",
        route_after_skill,
        {
            "response_generation": "response_generation",
            "error_handler": "error_handler",
            "__end__": END,
        },
    )

    # response generation / error handler -> end
    builder.add_edge("response_generation", END)
    builder.add_edge("error_handler", END)

    # ---- compile ----
    compiled = builder.compile(checkpointer=checkpointer)
    logger.info("LangGraph StateGraph built successfully")
    return compiled


async def get_postgres_checkpointer():
    """
    Get the PostgreSQL checkpointer (for production)
    Requires installation: pip install langgraph-checkpoint-postgres
    """
    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        from app.config.settings import get_settings
        settings = get_settings()
        checkpointer = AsyncPostgresSaver.from_conn_string(settings.database.postgres_dsn)
        await checkpointer.setup()
        logger.info("PostgreSQL checkpointer initialized")
        return checkpointer
    except ImportError:
        logger.warning("langgraph-checkpoint-postgres not installed, falling back to MemorySaver")
        return MemorySaver()


def get_graph(checkpointer=None):
    """Get the global Graph instance (singleton)"""
    global _graph
    if _graph is None:
        _graph = build_graph(checkpointer)
    return _graph
