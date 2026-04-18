"""
Unit tests - state module
"""
import pytest
from app.state.agent_state import AgentState, WorkflowStatus


def test_agent_state_defaults():
    state = AgentState(user_input="hello")
    assert state.workflow_status == WorkflowStatus.PENDING
    assert state.session_id is not None
    assert state.messages == []
    assert state.skill_executions == []


def test_add_skill_execution():
    state = AgentState(user_input="run job")
    execution = state.add_skill_execution("controlm_job", {"action": "run", "job_name": "MyJob"})
    assert execution.skill_name == "controlm_job"
    assert len(state.skill_executions) == 1


def test_get_last_skill_execution_empty():
    state = AgentState(user_input="test")
    assert state.get_last_skill_execution() is None
