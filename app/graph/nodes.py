"""
LangGraph orchestration layer - core workflow node definitions
Each node represents an Agent workflow step and is orchestrated by the StateGraph
"""
import logging
import hashlib
import json
from typing import Any, Dict
from datetime import datetime, timedelta

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.llm.adapter import get_llm_adapter
from app.skills.base import skill_registry
from app.state.agent_state import AgentState, HumanApprovalRequest, WorkflowStatus

logger = logging.getLogger(__name__)

# ===== Intent Cache Configuration =====
INTENT_CACHE = {}  # Simple in-memory cache: {hash: {"routing": ..., "timestamp": ...}}
INTENT_CACHE_TTL = 3600  # Cache TTL in seconds (1 hour)
INTENT_CACHE_MAX_SIZE = 1000  # Maximum cache entries


def _get_intent_cache_key(user_input: str) -> str:
    """Generate cache key from user input"""
    # Normalize input: lowercase, strip whitespace
    normalized = user_input.strip().lower()
    return hashlib.md5(normalized.encode('utf-8')).hexdigest()


def _get_cached_intent(cache_key: str) -> Dict[str, Any] | None:
    """Get cached intent if exists and not expired"""
    if cache_key in INTENT_CACHE:
        entry = INTENT_CACHE[cache_key]
        # Check TTL
        if datetime.now().timestamp() - entry['timestamp'] < INTENT_CACHE_TTL:
            logger.debug(f"Intent cache hit for key: {cache_key[:8]}...")
            return entry['data']
        else:
            # Expired, remove from cache
            del INTENT_CACHE[cache_key]
    return None


def _cache_intent(cache_key: str, intent_data: Dict[str, Any]):
    """Cache intent recognition result"""
    # Evict oldest entries if cache is full
    if len(INTENT_CACHE) >= INTENT_CACHE_MAX_SIZE:
        oldest_key = min(INTENT_CACHE.keys(), key=lambda k: INTENT_CACHE[k]['timestamp'])
        del INTENT_CACHE[oldest_key]
        logger.debug(f"Evicted oldest cache entry: {oldest_key[:8]}...")
    
    INTENT_CACHE[cache_key] = {
        'data': intent_data,
        'timestamp': datetime.now().timestamp()
    }
    logger.debug(f"Cached intent for key: {cache_key[:8]}...")


# ===== system prompts =====
INTENT_SYSTEM_PROMPT = """You are an enterprise-level intelligent assistant responsible for understanding user intent and routing to the correct processing workflow.

Available skills:
{skill_list}

Please analyze the user input and return the following JSON format:
{{
  "intent": "intent description",
  "routing_decision": "skill name or direct_reply",
  "confidence": 0.0-1.0,
  "params": {{}}
}}

If no skill invocation is needed, return "direct_reply" for routing_decision.
Return only JSON, no additional explanation."""

RESPONSE_SYSTEM_PROMPT = """You are a professional enterprise-level intelligent assistant.
Based on the conversation history and skill execution results, generate clear and professional responses.
Responses should be concise and highlight key information."""


async def intent_recognition_node(state: AgentState) -> Dict[str, Any]:
    """
    Intent recognition node
    Calls the LLM to analyze user intent and decide routing
    
    Optimization: Uses caching to avoid redundant LLM calls for similar queries
    """
    logger.info(f"[intent_recognition] session={state.session_id}, input={state.user_input[:50]}")

    # Check cache first
    cache_key = _get_intent_cache_key(state.user_input)
    cached_result = _get_cached_intent(cache_key)
    
    if cached_result:
        logger.info(f"[intent_recognition] Using cached intent: {cached_result.get('routing_decision')}")
        return {
            **cached_result,
            "workflow_status": WorkflowStatus.RUNNING,
        }

    llm = get_llm_adapter()
    skill_names = skill_registry.list_skill_names()
    skill_descriptions = "\n".join(
        f"- {s.name}: {s.description}"
        for s in skill_registry.get_all_skills().values()
    )

    messages = [
        SystemMessage(content=INTENT_SYSTEM_PROMPT.format(skill_list=skill_descriptions)),
        HumanMessage(content=state.user_input),
    ]

    try:
        response = await llm.ainvoke(messages)
        content = response.content.strip()
        # Remove possible markdown code block
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        parsed = json.loads(content)
        routing = parsed.get("routing_decision", "direct_reply")
        # Validate that the routing target exists
        if routing not in skill_names and routing != "direct_reply":
            logger.warning(f"Unknown routing target: {routing}, fallback to direct_reply")
            routing = "direct_reply"

        intent_result = {
            "detected_intent": parsed.get("intent", ""),
            "routing_decision": routing,
            "confidence_score": float(parsed.get("confidence", 0.0)),
            "context": {**state.context, "intent_params": parsed.get("params", {})},
        }
        
        # Cache the result
        _cache_intent(cache_key, intent_result)
        
        return {
            **intent_result,
            "workflow_status": WorkflowStatus.RUNNING,
        }
    except Exception as e:
        logger.error(f"[intent_recognition] failed: {e}", exc_info=True)
        return {
            "routing_decision": "direct_reply",
            "error": str(e),
            "workflow_status": WorkflowStatus.RUNNING,
        }


async def skill_execution_node(state: AgentState) -> Dict[str, Any]:
    """
    Skill execution node
    Invokes the chosen skill based on routing, handling exceptions and retries
    """
    skill_name = state.routing_decision
    logger.info(f"[skill_execution] skill={skill_name}, session={state.session_id}")

    skill = skill_registry.get(skill_name)
    if not skill:
        logger.error(f"Skill '{skill_name}' not found in registry")
        return {
            "error": f"Skill '{skill_name}' is not registered",
            "workflow_status": WorkflowStatus.FAILED,
        }

    params = state.context.get("intent_params", {})

    # Dynamic approval check: 
    # 1. Check if the skill has a method to dynamically determine approval need
    # 2. Fallback to the static class attribute if method doesn't exist
    needs_approval = False
    if hasattr(skill, 'requires_approval_for'):
        try:
            needs_approval = await skill.requires_approval_for(params)
        except Exception as e:
            logger.warning(f"Dynamic approval check failed for {skill_name}, falling back to static check: {e}")
            needs_approval = getattr(skill, 'require_human_approval', False)
    else:
        needs_approval = getattr(skill, 'require_human_approval', False)

    # Check if human approval is required
    if needs_approval and state.pending_approval is None:
        approval_request = HumanApprovalRequest(
            skill_name=skill_name,
            action_description=f"Preparing to execute skill: {skill.description}",
            params_to_confirm=params,
        )
        logger.info(f"[skill_execution] requesting human approval for skill={skill_name}")
        return {
            "pending_approval": approval_request,
            "workflow_status": WorkflowStatus.WAITING_HUMAN,
        }

    # If approval was already granted or not required, proceed with execution
    if state.pending_approval and state.human_approval_result is False:
        return {
            "skill_result": {"rejected": True, "message": "Operation has been cancelled by user"},
            "workflow_status": WorkflowStatus.COMPLETED,
        }

    execution = state.add_skill_execution(skill_name, params)

    output = await skill.safe_execute(params, max_retries=state.max_retries)
    execution.status = "success" if output.success else "failed"
    execution.output = output.data
    execution.error_message = output.error_message

    if not output.success:
        return {
            "skill_result": {"success": False, "error": output.error_message},
            "workflow_status": WorkflowStatus.FAILED,
            "error": output.error_message,
        }

    return {
        "skill_result": {"success": True, "data": output.data},
        "current_skill": skill_name,
        "workflow_status": WorkflowStatus.RUNNING,
    }


async def response_generation_node(state: AgentState) -> Dict[str, Any]:
    """
    Response generation node
    Generates the final natural language reply based on execution results
    """
    logger.info(f"[response_generation] session={state.session_id}")

    llm = get_llm_adapter()

    # Build the context summary
    context_summary = ""
    if state.skill_result:
        context_summary = f"\nSkill execution result: {state.skill_result}"
    if state.error:
        context_summary += f"\nError encountered during execution: {state.error}"

    messages = list(state.messages) + [
        SystemMessage(
            content=RESPONSE_SYSTEM_PROMPT
            + (f"\n\nContext information: {context_summary}" if context_summary else "")
        ),
        HumanMessage(content=f"Please respond to the user's request based on the above information: {state.user_input}"),
    ]

    chunks = []
    try:
        async for chunk in llm.astream(messages):
            chunks.append(chunk)
    except Exception as e:
        logger.error(f"[response_generation] stream failed: {e}", exc_info=True)
        return {
            "final_response": f"Processing completed, but an error occurred while generating response: {e}",
            "workflow_status": WorkflowStatus.COMPLETED,
        }

    final_response = "".join(chunks)
    return {
        "final_response": final_response,
        "streaming_chunks": chunks,
        "messages": [AIMessage(content=final_response)],
        "workflow_status": WorkflowStatus.COMPLETED,
    }


async def error_handler_node(state: AgentState) -> Dict[str, Any]:
    """
    Error handling node
    Handles exceptions in the workflow in a unified manner
    """
    logger.error(f"[error_handler] session={state.session_id}, error={state.error}")
    error_response = f"Sorry, we encountered an issue while processing your request: {state.error or 'Unknown error'}. Please try again later or contact the administrator."
    return {
        "final_response": error_response,
        "messages": [AIMessage(content=error_response)],
        "workflow_status": WorkflowStatus.FAILED,
    }
