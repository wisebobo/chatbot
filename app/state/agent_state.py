"""
Agent state definition module
Uses TypedDict + Pydantic to define workflow state for LangGraph StateGraph usage
"""
from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Dict, List, Optional, Sequence
from uuid import uuid4

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    """Workflow execution status enum"""
    PENDING = "pending"
    RUNNING = "running"
    WAITING_HUMAN = "waiting_human"   # human-in-the-loop waiting for approval
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SkillExecution(BaseModel):
    """Skill execution record"""
    skill_name: str
    input_params: Dict[str, Any] = Field(default_factory=dict)
    output: Optional[Any] = None
    status: str = "pending"           # pending | running | success | failed
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    retry_count: int = 0

    class Config:
        arbitrary_types_allowed = True


class HumanApprovalRequest(BaseModel):
    """Human approval request (human-in-the-loop)"""
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    skill_name: str
    action_description: str
    params_to_confirm: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved: Optional[bool] = None
    reviewer_note: Optional[str] = None


class AgentState(BaseModel):
    """
    LangGraph Agent main state
    Shared by all nodes and passed through the StateGraph
    """
    # ---- session identifiers ----
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: Optional[str] = None
    request_id: str = Field(default_factory=lambda: str(uuid4()))

    # ---- message history (automatically appended using add_messages reducer) ----
    messages: Annotated[Sequence[BaseMessage], add_messages] = Field(default_factory=list)

    # ---- intent and routing ----
    user_input: str = ""
    detected_intent: Optional[str] = None        # detected intent
    routing_decision: Optional[str] = None       # routing decision: skill_name | direct_reply
    confidence_score: float = 0.0

    # ---- skill execution context ----
    current_skill: Optional[str] = None
    skill_executions: List[SkillExecution] = Field(default_factory=list)
    skill_result: Optional[Any] = None

    # ---- Human-in-the-loop ----
    pending_approval: Optional[HumanApprovalRequest] = None
    human_approval_result: Optional[bool] = None

    # ---- workflow metadata ----
    workflow_status: WorkflowStatus = WorkflowStatus.PENDING
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    # ---- output ----
    final_response: Optional[str] = None
    streaming_chunks: List[str] = Field(default_factory=list)

    # ---- timestamps ----
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # ---- extension metadata (for skills to store temporary data) ----
    context: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    def add_skill_execution(self, skill_name: str, params: Dict[str, Any]) -> SkillExecution:
        """Add a skill execution record"""
        execution = SkillExecution(
            skill_name=skill_name,
            input_params=params,
            started_at=datetime.utcnow(),
        )
        self.skill_executions.append(execution)
        return execution

    def get_last_skill_execution(self) -> Optional[SkillExecution]:
        """Get the most recent skill execution record"""
        return self.skill_executions[-1] if self.skill_executions else None
