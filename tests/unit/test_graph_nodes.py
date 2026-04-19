"""
Unit tests for LangGraph workflow nodes

Tests intent recognition, skill execution, and response generation nodes.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.graph.nodes import (
    intent_recognition_node,
    skill_execution_node,
    response_generation_node,
)
from app.state.agent_state import AgentState, WorkflowStatus


@pytest.fixture
def sample_state():
    """Create a sample agent state for testing"""
    return AgentState(
        user_input="What is the loan approval process?",
        session_id="test-session-001",
        user_id="test-user",
        workflow_status=WorkflowStatus.RUNNING,
    )


@pytest.mark.asyncio
async def test_intent_recognition_cache_hit(sample_state):
    """Test intent recognition with cache hit"""
    # Pre-populate cache
    from app.graph.nodes import _cache_intent, _get_intent_cache_key
    
    cache_key = _get_intent_cache_key(sample_state.user_input)
    cached_data = {
        "detected_intent": "Query about loan process",
        "routing_decision": "wiki_search",
        "confidence_score": 0.95,
        "context": {"intent_params": {"query": "loan approval"}},
    }
    _cache_intent(cache_key, cached_data)
    
    # Call node - should use cache
    result = await intent_recognition_node(sample_state)
    
    assert result["routing_decision"] == "wiki_search"
    assert result["confidence_score"] == 0.95
    assert result["workflow_status"] == WorkflowStatus.RUNNING


@pytest.mark.asyncio
async def test_intent_recognition_llm_call(sample_state):
    """Test intent recognition with LLM call"""
    # Mock LLM adapter
    mock_response = MagicMock()
    mock_response.content = '''{
        "intent": "Query about loan process",
        "routing_decision": "wiki_search",
        "confidence": 0.95,
        "params": {"query": "loan approval"}
    }'''
    
    with patch('app.graph.nodes.get_llm_adapter') as mock_llm:
        mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
        
        result = await intent_recognition_node(sample_state)
        
        assert result["routing_decision"] == "wiki_search"
        assert result["confidence_score"] == 0.95
        assert "intent_params" in result["context"]


@pytest.mark.asyncio
async def test_intent_recognition_llm_error(sample_state):
    """Test intent recognition handles LLM errors gracefully"""
    # Clear cache first to ensure LLM is called
    from app.graph.nodes import INTENT_CACHE
    INTENT_CACHE.clear()
    
    with patch('app.graph.nodes.get_llm_adapter') as mock_llm:
        # Mock circuit breaker to allow the call through
        with patch('app.graph.nodes.CircuitBreakerRegistry.get_or_create') as mock_breaker_registry:
            # Create a mock breaker that just calls the function
            mock_breaker = MagicMock()
            async def passthrough(func):
                try:
                    return await func()
                except Exception:
                    raise
            mock_breaker.side_effect = passthrough
            mock_breaker_registry.return_value = mock_breaker
            
            # Make LLM raise an exception
            mock_llm.return_value.ainvoke = AsyncMock(side_effect=Exception("LLM timeout"))
            
            result = await intent_recognition_node(sample_state)
            
            # Should fallback to direct_reply
            assert result["routing_decision"] == "direct_reply"
            assert "error" in result
            assert result["workflow_status"] == WorkflowStatus.RUNNING


@pytest.mark.asyncio
async def test_skill_execution_not_found(sample_state):
    """Test skill execution with invalid skill name"""
    state = sample_state.copy(update={"routing_decision": "nonexistent_skill"})
    
    result = await skill_execution_node(state)
    
    assert result["workflow_status"] == WorkflowStatus.FAILED
    assert "error" in result
    assert "not registered" in result["error"]


@pytest.mark.asyncio
async def test_skill_execution_success(sample_state):
    """Test successful skill execution"""
    from app.skills.base import SkillOutput
    
    # Mock skill
    mock_skill = MagicMock()
    mock_skill.name = "wiki_search"
    mock_skill.description = "Search wiki"
    mock_skill.require_human_approval = False
    
    mock_output = SkillOutput(
        success=True,
        data={"results": ["Article 1", "Article 2"]},
        error_message=None
    )
    
    async def mock_safe_execute(params, max_retries=3):
        return mock_output
    
    mock_skill.safe_execute = mock_safe_execute
    
    state = sample_state.model_copy(update={
        "routing_decision": "wiki_search",
        "context": {"intent_params": {"query": "loan"}}
    })
    
    with patch('app.graph.nodes.skill_registry') as mock_registry:
        mock_registry.get.return_value = mock_skill
        
        # Mock circuit breaker
        with patch('app.graph.nodes.CircuitBreakerRegistry.get_or_create') as mock_breaker_registry:
            mock_breaker = MagicMock()
            async def passthrough(func):
                return await func()
            mock_breaker.side_effect = passthrough
            mock_breaker_registry.return_value = mock_breaker
            
            result = await skill_execution_node(state)
            
            assert result["workflow_status"] == WorkflowStatus.RUNNING
            assert result["skill_result"]["success"] is True
            assert "data" in result["skill_result"]


@pytest.mark.asyncio
async def test_skill_execution_failure(sample_state):
    """Test skill execution failure"""
    from app.skills.base import SkillOutput
    
    mock_skill = MagicMock()
    mock_skill.name = "wiki_search"
    mock_skill.require_human_approval = False
    
    mock_output = SkillOutput(
        success=False,
        data=None,
        error_message="Search failed"
    )
    mock_skill.safe_execute = AsyncMock(return_value=mock_output)
    
    state = sample_state.copy(update={
        "routing_decision": "wiki_search",
        "context": {"intent_params": {}}
    })
    
    with patch('app.graph.nodes.skill_registry') as mock_registry:
        mock_registry.get.return_value = mock_skill
        
        result = await skill_execution_node(state)
        
        assert result["workflow_status"] == WorkflowStatus.FAILED
        assert result["skill_result"]["success"] is False
        assert "error" in result


@pytest.mark.asyncio
async def test_skill_execution_human_approval_required(sample_state):
    """Test skill execution requires human approval"""
    mock_skill = MagicMock()
    mock_skill.name = "controlm_trigger"
    mock_skill.description = "Trigger Control-M job"
    mock_skill.require_human_approval = True
    
    state = sample_state.copy(update={
        "routing_decision": "controlm_trigger",
        "pending_approval": None
    })
    
    with patch('app.graph.nodes.skill_registry') as mock_registry:
        mock_registry.get.return_value = mock_skill
        
        result = await skill_execution_node(state)
        
        assert result["workflow_status"] == WorkflowStatus.WAITING_HUMAN
        assert result["pending_approval"] is not None
        assert result["pending_approval"].skill_name == "controlm_trigger"


@pytest.mark.asyncio
async def test_response_generation_basic(sample_state):
    """Test basic response generation"""
    state = sample_state.model_copy(update={
        "routing_decision": "direct_reply",
        "conversation_history": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
    })
    
    # Mock LLM
    mock_response = MagicMock()
    mock_response.content = "This is a test response"
    
    with patch('app.graph.nodes.get_llm_adapter') as mock_llm:
        mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
        
        result = await response_generation_node(state)
        
        # Check for actual response field name
        assert "final_response" in result or "response" in result
        assert result["workflow_status"] == WorkflowStatus.COMPLETED


@pytest.mark.asyncio
async def test_response_generation_with_skill_result(sample_state):
    """Test response generation with skill execution result"""
    state = sample_state.model_copy(update={
        "routing_decision": "wiki_search",
        "skill_result": {
            "success": True,
            "data": {"results": ["Result 1", "Result 2"]}
        },
        "current_skill": "wiki_search"
    })
    
    mock_response = MagicMock()
    mock_response.content = "Based on the search results..."
    
    with patch('app.graph.nodes.get_llm_adapter') as mock_llm:
        mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
        
        result = await response_generation_node(state)
        
        # Check for actual response field name
        assert "final_response" in result or "response" in result
        assert result["workflow_status"] == WorkflowStatus.COMPLETED
