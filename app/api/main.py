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

    # ===== Rate Limiter Setup =====
    limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    logger.info("Rate limiter initialized with default limit: 200/minute")

    # ===== Monitoring & Observability Setup (Phase 3) =====
    try:
        from prometheus_client import make_asgi_app
        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)
        logger.info("Prometheus metrics endpoint mounted at /metrics")
    except ImportError:
        logger.warning("prometheus-client not installed, metrics endpoint disabled")
    
    # Start system resource monitor
    from app.monitoring.system_monitor import system_monitor
    system_monitor.start()
    logger.info("System resource monitor started")

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

    # Register authentication routes
    app.include_router(auth_router, prefix=settings.api.api_prefix)
    logger.info("Registered authentication routes: /auth/login, /auth/refresh, /auth/me")
    
    # Register API key management routes
    app.include_router(api_key_router, prefix=settings.api.api_prefix)
    logger.info("Registered API key management routes: /api-keys/")

    # Initialize database tables (auto-create if not exists)
    from app.db.database import get_db_manager
    db_manager = get_db_manager()
    db_manager.create_tables()
    logger.info(f"Database initialized: {db_manager._mask_url(db_manager.database_url)}")

    # Initialize wiki engine for feedback API (now uses database)
    from app.wiki.db_engine import DatabaseWikiEngine
    wiki_engine = DatabaseWikiEngine()
    article_count = wiki_engine.get_article_count()
    
    # Load sample data if empty
    if article_count == 0:
        logger.info("Loading sample wiki articles into database...")
        from app.wiki.sample_data import get_sample_articles
        sample_articles = get_sample_articles()
        wiki_engine.import_articles(sample_articles)
        article_count = len(sample_articles)
        logger.info(f"Loaded {article_count} sample articles to database")
    
    logger.info(f"Wiki engine initialized with {article_count} articles (database-backed)")

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
    @limiter.limit("30/minute")  # 30 requests per minute per IP
    async def chat(req: ChatRequest, request: Request):
        """
        Standard chat endpoint (non-streaming)
        
        Rate limit: 30 requests per minute per IP address
        """
        from app.monitoring.metrics import llm_calls_total, llm_latency, exception_count
        
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
    @limiter.limit("20/minute")  # 20 requests per minute for streaming (more resource intensive)
    async def chat_stream(req: ChatRequest, request: Request):
        """
        Streaming chat endpoint (SSE)
        
        Rate limit: 20 requests per minute per IP address
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
    @limiter.limit("20/minute")
    async def submit_approval(
        req: HumanApprovalRequest,
        request: Request,
        current_user: APIUser = Depends(get_api_key)  # Require authentication for approval
    ):
        """
        Submit a human approval decision (human-in-the-loop)
        
        Authentication: Required (X-API-Key header)
        Rate limit: 20 requests per minute
        
        After approval, the workflow will resume from the breakpoint
        
        Args:
            req: Approval request with session_id and decision
            current_user: Authenticated user (must have valid API key)
            
        Returns:
            Approval result and updated workflow status
        """
        try:
            logger.info(f"Approval submitted by user: {current_user.user_id} for session: {req.session_id}")
            
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

    @app.post(f"{prefix}/wiki/feedback", response_model=WikiFeedbackResponse, tags=["Wiki"])
    @limiter.limit("10/minute")  # Stricter limit for feedback to prevent spam
    async def submit_wiki_feedback(
        req: WikiFeedbackRequest,
        request: Request,
        current_user: APIUser = Depends(get_api_key)  # Require authentication
    ):
        """
        Submit user feedback for a wiki article (requires authentication)
        
        This implements the feedback loop for continuous knowledge improvement:
        - Positive/negative feedback is recorded
        - Confidence score is automatically recalculated
        - Low-confidence articles can be flagged for re-compilation
        
        Rate limit: 10 requests per minute per IP
        Authentication: Required (X-API-Key header)
        """
        from app.monitoring.metrics import wiki_feedback_submitted, wiki_low_confidence_alerts
        
        try:
            # Get article
            article = wiki_engine.get_article(req.entry_id)
            if not article:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Wiki article not found: {req.entry_id}"
                )
            
            # Submit feedback to wiki engine
            success = wiki_engine.submit_feedback(
                entry_id=req.entry_id,
                is_positive=req.is_positive,
                comment=req.comment
            )
            
            if not success:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Wiki article not found: {req.entry_id}"
                )
            
            # Get updated article for feedback summary
            article = wiki_engine.get_article(req.entry_id)
            if not article:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to retrieve updated article"
                )
            
            # Increment feedback submitted metric
            wiki_feedback_submitted.labels(is_positive=req.is_positive).inc()
            
            # Check if confidence is below threshold
            if article.confidence < 0.7:
                wiki_low_confidence_alerts.inc()
            
            return WikiFeedbackResponse(
                success=True,
                entry_id=req.entry_id,
                feedback_summary={
                    "positive": article.feedback.positive,
                    "negative": article.feedback.negative,
                    "total": article.feedback.positive + article.feedback.negative,
                    "comments_count": len(article.feedback.comments),
                    "updated_confidence": round(article.confidence, 3),
                    "confidence_change": "increased" if req.is_positive else "decreased"
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Wiki feedback error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @app.get(f"{prefix}/wiki/{{entry_id}}/feedback", tags=["Wiki"])
    @limiter.limit("60/minute")  # Higher limit for read operations
    async def get_wiki_feedback_stats(
        entry_id: str,
        request: Request,
        current_user: Optional[APIUser] = Depends(get_optional_api_key)  # Optional auth
    ):
        """
        Get feedback statistics for a wiki article
        
        Authentication: Optional (anonymous access allowed)
        Rate limit: 60 requests per minute per IP
        
        Args:
            entry_id: Wiki article entry_id
            current_user: Authenticated user if API key provided
            
        Returns:
            Feedback statistics and confidence information
        """
        try:
            user_info = f" by user: {current_user.user_id}" if current_user else " (anonymous)"
            logger.debug(f"Feedback stats requested for {entry_id}{user_info}")
            
            article = wiki_engine.get_article(entry_id)
            if not article:
                raise HTTPException(
                    status_code=404,
                    detail=f"Wiki article not found: {entry_id}"
                )
            
            total_feedback = article.feedback.positive + article.feedback.negative
            feedback_ratio = (
                article.feedback.positive / total_feedback 
                if total_feedback > 0 
                else 0
            )
            
            return {
                "entry_id": entry_id,
                "title": article.title,
                "version": article.version,
                "confidence": {
                    "current": round(article.confidence, 3),
                    "feedback_ratio": round(feedback_ratio, 3),
                    "threshold_for_recompile": 0.7
                },
                "feedback": {
                    "positive": article.feedback.positive,
                    "negative": article.feedback.negative,
                    "total": total_feedback,
                    "comments": article.feedback.comments[-5:]  # Last 5 comments
                },
                "status": article.status.value if hasattr(article.status, 'value') else article.status
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get wiki feedback stats: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @app.get(f"{prefix}/metrics", tags=["Monitoring"])
    async def metrics():
        """Prometheus metrics endpoint"""
        from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
        from fastapi.responses import Response
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()
