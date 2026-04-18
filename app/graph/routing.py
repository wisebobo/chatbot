"""
LangGraph orchestration layer - routing logic
Defines routing functions for conditional edges that decide the next workflow step
"""
import logging
from typing import Literal

from app.state.agent_state import AgentState, WorkflowStatus

logger = logging.getLogger(__name__)


def route_after_intent(
    state: AgentState,
) -> Literal["skill_execution", "response_generation"]:
    """
    Routing decision after intent recognition
    
    Returns:
        - "skill_execution": skill invocation is required
        - "response_generation": generate a direct response
    """
    if state.routing_decision and state.routing_decision != "direct_reply":
        logger.debug(f"Routing to skill: {state.routing_decision}")
        return "skill_execution"
    logger.debug("Routing to direct reply")
    return "response_generation"


def route_after_skill(
    state: AgentState,
) -> Literal["response_generation", "error_handler", "__end__"]:
    """
    Routing decision after skill execution
    
    Returns:
        - "response_generation": skill succeeded, generate response
        - "error_handler": skill execution failed
        - "__end__": waiting for human intervention (workflow paused)
    """
    if state.workflow_status == WorkflowStatus.WAITING_HUMAN:
        logger.info("Workflow paused, waiting for human approval")
        return "__end__"   # LangGraph interrupt mechanism will pause here

    if state.workflow_status == WorkflowStatus.FAILED:
        logger.warning("Skill execution failed, routing to error handler")
        return "error_handler"

    return "response_generation"


def route_after_intent_with_error(
    state: AgentState,
) -> Literal["skill_execution", "response_generation", "error_handler"]:
    """
    Intent routing with error handling (enhanced)
    """
    if state.workflow_status == WorkflowStatus.FAILED:
        return "error_handler"
    return route_after_intent(state)
