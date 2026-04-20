"""
FastAPI entry layer
Provides RESTful API endpoints and supports both standard and streaming responses
"""
import logging
import uuid
from typing import Any, AsyncIterator, Dict, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

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
from app.wiki.engine import LocalWikiEngine
from app.api.auth import get_api_key, get_optional_api_key, APIUser
from app.api.auth_routes import router as auth_router
from app.api.api_key_routes import router as api_key_router
from app.api.versioning import APIVersionMiddleware
from app.api.version_routes import router as version_router

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


class WikiFeedbackRequest(BaseModel):
    entry_id: str = Field(..., description="Wiki article entry_id")
    is_positive: bool = Field(..., description="True for thumbs up, False for thumbs down")
    comment: Optional[str] = Field(default=None, max_length=500, description="Optional user comment")


class WikiFeedbackResponse(BaseModel):
    success: bool
    entry_id: str
    feedback_summary: Dict[str, Any]


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

    # ===== Exception Handler Setup =====
    from app.middleware.exception_handler import (
        register_exception_handlers,
        CorrelationIDMiddleware
    )
    
    # Add correlation ID middleware
    app.add_middleware(CorrelationIDMiddleware)
    logger.info("Correlation ID middleware registered")

    # ===== API Versioning Middleware =====
    app.add_middleware(APIVersionMiddleware)
    logger.info("API versioning middleware registered")

    # Register global exception handlers
    register_exception_handlers(app)
    logger.info("Global exception handlers registered")

    # ===== Rate Limiter Setup =====
    import os
    # Use in-memory storage for testing, Redis for production
    storage_uri = os.getenv("RATE_LIMIT_STORAGE", "memory://")
    
    # Disable env file reading to avoid Unicode issues on Windows
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["200/minute"],
        storage_uri=storage_uri,
        enabled=True,
        config_filename=None
    )
    
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    logger.info(f"Rate limiter initialized with storage: {storage_uri}, default limit: 200/minute")

    # ===== Monitoring & Observability Setup =====
    try:
        from prometheus_client import make_asgi_app
        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)
        logger.info("Prometheus metrics endpoint mounted at /metrics")
    except ImportError:
        logger.warning("prometheus_client not installed, metrics endpoint disabled")

    # ===== CORS Setup =====
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info(f"CORS middleware registered with origins: {settings.api.allowed_origins}")

    # ===== Register Routers =====
    # Health check endpoint (with API prefix)
    @app.get(f"{settings.api.api_prefix}/health", response_model=HealthResponse, tags=["Health"])
    async def health_check():
        """Health check endpoint"""
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            registered_skills=skill_registry.list_skill_names()
        )

    # Auth routes
    app.include_router(auth_router, prefix=settings.api.api_prefix)
    logger.info("Auth routes registered")

    # API Key management routes
    app.include_router(api_key_router, prefix=settings.api.api_prefix)
    logger.info("API key management routes registered")

    # Version routes
    app.include_router(version_router, prefix=settings.api.api_prefix)
    logger.info("API version routes registered")

    # Chat endpoint
    @app.post(f"{settings.api.api_prefix}/chat", response_model=ChatResponse, tags=["Chat"])
    async def chat_endpoint(
        request_data: ChatRequest,
        background_tasks: BackgroundTasks,
        current_user: Optional[APIUser] = Depends(get_optional_api_key)
    ):
        """
        Main chat endpoint - processes user messages through the agent
        
        Args:
            request_data: Chat request containing message and optional session_id
            background_tasks: FastAPI background tasks
            current_user: Optional authenticated user
            
        Returns:
            ChatResponse with agent's reply
        """
        session_id = request_data.session_id or str(uuid.uuid4())
        request_id = str(uuid.uuid4())
        
        try:
            # Get LangGraph instance
            graph = get_graph()
            
            # Prepare input state
            initial_state = {
                "messages": [{"role": "user", "content": request_data.message}],
                "session_id": session_id,
                "request_id": request_id,
                "user_id": request_data.user_id,
                "workflow_status": WorkflowStatus.RUNNING,
            }
            
            # Prepare config for checkpointer
            config = {
                "configurable": {
                    "thread_id": session_id,
                }
            }
            
            # Execute graph
            result = await graph.ainvoke(initial_state, config=config)
            
            # Extract response
            messages = result.get("messages", [])
            response_text = ""
            skill_executed = None
            
            if messages:
                last_message = messages[-1]
                if isinstance(last_message, dict):
                    response_text = last_message.get("content", "")
                elif hasattr(last_message, 'content'):
                    response_text = last_message.content
                
                # Check for skill execution metadata
                skill_executed = result.get("skill_executed")
            
            return ChatResponse(
                session_id=session_id,
                request_id=request_id,
                response=response_text,
                status="completed",
                skill_executed=skill_executed
            )
            
        except Exception as e:
            logger.error(f"Chat endpoint error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    # Human approval endpoint
    @app.post(f"{settings.api.api_prefix}/human-approval", tags=["Human Approval"])
    async def human_approval_endpoint(
        approval_data: HumanApprovalRequest,
        current_user: APIUser = Depends(get_api_key)
    ):
        """
        Submit human approval decision for pending actions
        
        Args:
            approval_data: Approval decision data
            current_user: Authenticated user (required)
            
        Returns:
            Success confirmation
        """
        try:
            # Store approval decision in state
            from app.state.agent_state import get_state_store
            state_store = get_state_store()
            
            approval_key = f"approval:{approval_data.session_id}:{approval_data.request_id}"
            await state_store.set(approval_key, {
                "approved": approval_data.approved,
                "reviewer": current_user.name,
                "note": approval_data.reviewer_note,
                "timestamp": str(uuid.uuid4())
            })
            
            return {"status": "approved" if approval_data.approved else "rejected"}
            
        except Exception as e:
            logger.error(f"Human approval error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    # Wiki feedback endpoint
    @app.post(f"{settings.api.api_prefix}/wiki/feedback", response_model=WikiFeedbackResponse, tags=["Wiki"])
    async def wiki_feedback_endpoint(
        feedback_data: WikiFeedbackRequest,
        current_user: Optional[APIUser] = Depends(get_optional_api_key)
    ):
        """
        Submit feedback for wiki articles
        
        Args:
            feedback_data: Feedback data (positive/negative + optional comment)
            current_user: Optional authenticated user
            
        Returns:
            WikiFeedbackResponse with success status
        """
        try:
            from app.wiki.db_engine import DatabaseWikiEngine
            wiki_engine = DatabaseWikiEngine()
            
            # Add feedback to wiki entry
            success = wiki_engine.add_feedback(
                entry_id=feedback_data.entry_id,
                is_positive=feedback_data.is_positive,
                comment=feedback_data.comment,
                user_id=current_user.name if current_user else "anonymous"
            )
            
            if not success:
                raise HTTPException(status_code=404, detail=f"Wiki entry {feedback_data.entry_id} not found")
            
            # Get updated feedback summary
            from app.db.repositories import WikiRepository
            from app.db.database import get_db_manager
            db_manager = get_db_manager()
            wiki_repo = WikiRepository(db_manager.SessionLocal())
            
            feedback_summary = wiki_repo.get_feedback_summary(feedback_data.entry_id)
            
            return WikiFeedbackResponse(
                success=True,
                entry_id=feedback_data.entry_id,
                feedback_summary=feedback_summary
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Wiki feedback error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    # Initialize skills
    logger.info("Initializing skills...")
    skill_registry.register(ControlMSkill())
    skill_registry.register(PlaywrightSkill())
    skill_registry.register(RagSkill())
    skill_registry.register(WikiSkill())
    logger.info(f"Registered {len(skill_registry.list_skill_names())} skills")

    logger.info(f"FastAPI application created successfully")
    return app


# Create global app instance
app = create_app()