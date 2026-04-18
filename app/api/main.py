"""
FastAPI entry layer
Provides RESTful API endpoints and supports both standard and streaming responses
"""
import logging
import uuid
from typing import AsyncIterator, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.config.settings import get_settings
from app.graph.graph import get_graph
from app.monitoring.logger import setup_logging
from app.monitoring.metrics import get_metrics, request_counter, request_duration
from app.skills.base import skill_registry
from app.skills.controlm_skill import ControlMSkill
from app.skills.playwright_skill import PlaywrightSkill
from app.skills.rag_skill import RagSkill
from app.skills.wiki_skill import WikiSkill
from app.state.agent_state import AgentState, WorkflowStatus

logger = logging.getLogger(__name__)

# ===== request/response schema =====

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4096, description="User message")
    session_id: Optional[str] = Field(default=None, description="Session ID (create new if not provided)")
    user_id: Optional[str] = Field(default=None, description="User identifier")
    stream: bool = Field(default=False, description="Whether to return streaming response")


class ChatResponse(BaseModel):
    session_id: str
    request_id: str
    response: str
    status: str
    skill_executed: Optional[str] = None
    error: Optional[str] = None


class HumanApprovalRequest(BaseModel):
    session_id: str = Field(..., description="Session ID requiring approval")
    request_id: str = Field(..., description="Approval request ID")
    approved: bool = Field(..., description="Whether approved")
    reviewer_note: Optional[str] = Field(default=None, description="Reviewer notes")


class HealthResponse(BaseModel):
    status: str
    version: str
    registered_skills: list


# ===== application factory =====

def create_app() -> FastAPI:
    """Create the FastAPI application"""
    settings = get_settings()
    setup_logging(settings.monitoring.log_level, settings.monitoring.log_format)

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="Enterprise-level Agent Platform based on LangGraph",
        docs_url=f"{settings.api.api_prefix}/docs",
        redoc_url=f"{settings.api.api_prefix}/redoc",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # register skills
    skill_registry.register(ControlMSkill())
    skill_registry.register(PlaywrightSkill())
    skill_registry.register(RagSkill())
    skill_registry.register(WikiSkill())
    logger.info(f"Registered skills: {skill_registry.list_skill_names()}")

    prefix = settings.api.api_prefix

    @app.get(f"{prefix}/health", response_model=HealthResponse, tags=["System"])
    async def health_check():
        """Health check endpoint"""
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            registered_skills=skill_registry.list_skill_names(),
        )

    @app.post(f"{prefix}/chat", response_model=ChatResponse, tags=["Chat"])
    async def chat(req: ChatRequest):
        """
        Standard chat endpoint (non-streaming)
        """
        session_id = req.session_id or str(uuid.uuid4())
        request_id = str(uuid.uuid4())

        with request_duration.labels(endpoint="/chat").time():
            request_counter.labels(endpoint="/chat", status="started").inc()
            try:
                graph = get_graph()
                initial_state = AgentState(
                    session_id=session_id,
                    request_id=request_id,
                    user_id=req.user_id,
                    user_input=req.message,
                )
                config = {"configurable": {"thread_id": session_id}}
                result = await graph.ainvoke(initial_state, config=config)

                request_counter.labels(endpoint="/chat", status="success").inc()
                return ChatResponse(
                    session_id=session_id,
                    request_id=request_id,
                    response=result.get("final_response", ""),
                    status=result.get("workflow_status", WorkflowStatus.COMPLETED),
                    skill_executed=result.get("current_skill"),
                    error=result.get("error"),
                )
            except Exception as e:
                request_counter.labels(endpoint="/chat", status="error").inc()
                logger.error(f"Chat error: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

    @app.post(f"{prefix}/chat/stream", tags=["Chat"])
    async def chat_stream(req: ChatRequest):
        """
        Streaming chat endpoint (SSE)
        """
        session_id = req.session_id or str(uuid.uuid4())

        async def event_generator() -> AsyncIterator[str]:
            try:
                graph = get_graph()
                initial_state = AgentState(
                    session_id=session_id,
                    user_input=req.message,
                )
                config = {"configurable": {"thread_id": session_id}}
                async for event in graph.astream_events(initial_state, config=config, version="v2"):
                    if event["event"] == "on_chat_model_stream":
                        chunk = event["data"]["chunk"].content
                        if chunk:
                            yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: [ERROR] {e}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    @app.post(f"{prefix}/approval", tags=["Human Approval"])
    async def submit_approval(req: HumanApprovalRequest):
        """
        Submit a human approval decision (human-in-the-loop)
        After approval, the workflow will resume from the breakpoint
        """
        try:
            graph = get_graph()
            config = {"configurable": {"thread_id": req.session_id}}

            # restore from checkpoint and inject approval result
            result = await graph.ainvoke(
                {"human_approval_result": req.approved, "pending_approval": None},
                config=config,
            )
            return {
                "session_id": req.session_id,
                "approved": req.approved,
                "response": result.get("final_response", ""),
                "status": result.get("workflow_status"),
            }
        except Exception as e:
            logger.error(f"Approval error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @app.get(f"{prefix}/metrics", tags=["Monitoring"])
    async def metrics():
        """Prometheus metrics endpoint"""
        from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
        from fastapi.responses import Response
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()
