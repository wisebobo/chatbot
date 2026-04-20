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
    wiki_entry_id: Optional[str] = None  # Wiki article ID for feedback (if skill returned wiki results)
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
                "user_input": request_data.message,  # Add user_input for intent recognition
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
            wiki_entry_id = None
            
            if messages:
                last_message = messages[-1]
                if isinstance(last_message, dict):
                    response_text = last_message.get("content", "")
                elif hasattr(last_message, 'content'):
                    response_text = last_message.content
                
                # Extract skill executed and wiki entry ID
                skill_executed = result.get("skill_executed") or result.get("current_skill")  # Try both field names
                wiki_entry_id = None
                
                if not skill_executed:
                    logger.info(f"[chat_endpoint] skill_executed=None")
                
                logger.info(f"[chat_endpoint] result keys: {list(result.keys())}")
                logger.info(f"[chat_endpoint] skill_executed type: {type(skill_executed)}, value: {skill_executed}")
                
                # If wiki_search was executed, extract wiki_entry_id from results
                if skill_executed == "wiki_search":
                    skill_result = result.get("skill_result")
                    logger.info(f"[chat_endpoint] skill_result type: {type(skill_result)}, value: {skill_result}")
                    
                    if skill_result and isinstance(skill_result, dict) and skill_result.get("success"):
                        results = skill_result.get("data", {}).get("results", [])
                        logger.info(f"[chat_endpoint] Found {len(results)} wiki results")
                        
                        if results and len(results) > 0:
                            # Use the first (most relevant) result's entry_id
                            wiki_entry_id = results[0].get("entry_id")
                            logger.info(f"[chat_endpoint] Extracted wiki_entry_id: {wiki_entry_id}")
            
            return ChatResponse(
                session_id=session_id,
                request_id=request_id,
                response=response_text,
                status="completed",
                skill_executed=skill_executed,
                wiki_entry_id=wiki_entry_id
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

    # Wiki articles list endpoint
    @app.get(f"{settings.api.api_prefix}/wiki/articles", tags=["Wiki"])
    async def list_wiki_articles():
        """
        Get list of all wiki articles
        
        Returns:
            List of wiki article summaries
        """
        try:
            from app.db.repositories import WikiRepository
            from app.db.database import get_db_manager
            
            db_manager = get_db_manager()
            wiki_repo = WikiRepository(db_manager.SessionLocal())
            
            # Get all articles using correct method name
            articles = wiki_repo.list_all(limit=100)
            
            result = []
            for article in articles:
                result.append({
                    "entry_id": article.entry_id,
                    "title": article.title or article.entry_id,
                    "type": article.type.value if hasattr(article.type, 'value') else str(article.type),
                    "version": article.version,
                    "summary": article.summary,
                    "confidence": article.confidence,
                    "status": article.status.value if hasattr(article.status, 'value') else str(article.status),
                    "created_at": article.created_at.isoformat() if article.created_at else None,
                    "updated_at": article.updated_at.isoformat() if article.updated_at else None,
                    "content": article.content,  # Include full content for view
                    "tags": article.tags or [],
                    "related_ids": article.related_ids or [],
                    # Feedback statistics
                    "positive_feedback": article.positive_feedback or 0,
                    "negative_feedback": article.negative_feedback or 0,
                    "total_feedback": (article.positive_feedback or 0) + (article.negative_feedback or 0)
                })
            
            return result
            
        except Exception as e:
            logger.error(f"List wiki articles error: {e}", exc_info=True)
            # Return empty list on error
            return []

    # LLM-powered Wiki compilation endpoint
    @app.post(f"{settings.api.api_prefix}/wiki/compile", tags=["Wiki"])
    async def compile_wiki_article(request: dict):
        """
        Compile raw document into structured wiki entry using LLM
        
        Request Body:
            raw_content: Raw document text
            source_url: Optional source URL
            source_type: Type of source (text, pdf, webpage, etc.)
            suggested_category: Optional category hint
            
        Returns:
            Compiled wiki article structure
        """
        try:
            from app.wiki.compiler import LLMPoweredWikiCompiler
            from app.wiki.engine import LocalWikiEngine
            
            raw_content = request.get("raw_content", "")
            source_url = request.get("source_url")
            source_type = request.get("source_type", "text")
            suggested_category = request.get("suggested_category")
            
            if not raw_content:
                raise HTTPException(status_code=400, detail="raw_content is required")
            
            # Initialize compiler
            wiki_engine = LocalWikiEngine()
            compiler = LLMPoweredWikiCompiler(wiki_engine)
            
            # Compile document
            article, operation = await compiler.compile_document(
                raw_content=raw_content,
                source_url=source_url,
                source_type=source_type,
                suggested_category=suggested_category
            )
            
            # Convert to dict for JSON response
            result = {
                "article": {
                    "entry_id": article.entry_id,
                    "title": article.title,
                    "type": article.type.value if hasattr(article.type, 'value') else str(article.type),
                    "version": article.version,
                    "summary": article.summary,
                    "content": article.content,
                    "tags": article.tags or [],
                    "sources": [
                        {
                            "source_id": src.source_id,
                            "url": src.url,
                            "file_name": src.file_name,
                            "page": src.page,
                            "content_snippet": src.content_snippet[:200] if src.content_snippet else ""
                        }
                        for src in article.sources
                    ] if article.sources else [],
                    "related_ids": [
                        {
                            "entry_id": rel.entry_id,
                            "relation": rel.relation.value if hasattr(rel.relation, 'value') else str(rel.relation)
                        }
                        for rel in article.related_ids
                    ] if article.related_ids else [],
                    "confidence": article.confidence,
                    "status": article.status.value if hasattr(article.status, 'value') else str(article.status),
                    "metadata": article.metadata or {}
                },
                "operation": operation,
                "message": f"Document successfully compiled ({operation})"
            }
            
            logger.info(f"Wiki compilation successful: {article.entry_id} ({operation})")
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Wiki compilation error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Compilation failed: {str(e)}")

    # Create wiki article endpoint
    @app.post(f"{settings.api.api_prefix}/wiki/articles", tags=["Wiki"])
    async def create_wiki_article(request: dict):
        """
        Save a compiled wiki article to database
        
        Request Body:
            Complete wiki article structure from compilation
        """
        try:
            from app.db.repositories import WikiRepository
            from app.db.database import get_db_manager
            from app.db.models import WikiEntry
            from datetime import datetime
            
            db_manager = get_db_manager()
            session = db_manager.SessionLocal()
            wiki_repo = WikiRepository(session)
            
            # Extract article data
            entry_id = request.get("entry_id")
            title = request.get("title")
            article_type = request.get("type", "concept")
            content = request.get("content", "")
            summary = request.get("summary", "")
            tags = request.get("tags", [])
            confidence = request.get("confidence", 0.8)
            version = request.get("version", 1)
            
            if not entry_id or not title:
                raise HTTPException(status_code=400, detail="entry_id and title are required")
            
            # Check if article already exists
            existing = wiki_repo.get_by_id(entry_id)
            
            if existing:
                # Update existing article
                existing.title = title
                existing.type = article_type
                existing.content = content
                existing.summary = summary
                existing.tags = tags
                existing.confidence = confidence
                existing.version = version + 1
                existing.updated_at = datetime.utcnow()
                
                session.commit()
                logger.info(f"Updated existing wiki article: {entry_id}")
                
                return {
                    "success": True,
                    "message": "Article updated successfully",
                    "operation": "updated",
                    "entry_id": entry_id,
                    "version": existing.version
                }
            else:
                # Create new article
                new_article = WikiEntry(
                    entry_id=entry_id,
                    title=title,
                    type=article_type,
                    content=content,
                    summary=summary,
                    tags=tags,
                    confidence=confidence,
                    version=version,
                    status="active",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                session.add(new_article)
                session.commit()
                logger.info(f"Created new wiki article: {entry_id}")
                
                return {
                    "success": True,
                    "message": "Article created successfully",
                    "operation": "created",
                    "entry_id": entry_id,
                    "version": version
                }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Create wiki article error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    # Database viewer endpoint
    @app.get(f"{settings.api.api_prefix}/database/{{table_name}}", tags=["Database"])
    async def get_database_table(table_name: str):
        """
        Get data from specified database table
        
        Args:
            table_name: Name of the table to query
            
        Returns:
            List of records from the table
        """
        try:
            from app.db.database import get_db_manager
            from sqlalchemy import text
            
            # Whitelist of allowed tables
            allowed_tables = ['wiki_entries', 'api_keys', 'chat_sessions']
            
            if table_name not in allowed_tables:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Table '{table_name}' is not accessible. Allowed tables: {', '.join(allowed_tables)}"
                )
            
            db_manager = get_db_manager()
            session = db_manager.SessionLocal()
            
            try:
                # Query all records from the table
                query = text(f"SELECT * FROM {table_name} LIMIT 100")
                result = session.execute(query)
                
                # Convert to list of dictionaries
                columns = result.keys()
                rows = []
                for row in result.fetchall():
                    row_dict = {}
                    for i, col in enumerate(columns):
                        value = row[i]
                        # Convert datetime to string
                        if hasattr(value, 'isoformat'):
                            value = value.isoformat()
                        row_dict[col] = value
                    rows.append(row_dict)
                
                return rows
                
            finally:
                session.close()
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Database query error: {e}", exc_info=True)
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