"""
Database Models for LangGraph Enterprise Agent Platform

Defines SQLAlchemy ORM models for persistent storage.
"""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class WikiEntry(Base):
    """
    Wiki entry model for structured knowledge storage.
    
    Replaces the in-memory wiki store with persistent PostgreSQL/SQLite storage.
    """
    __tablename__ = "wiki_entries"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Unique identifier (format: type_abbreviation_keyword)
    entry_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Version control
    version = Column(Integer, default=1, nullable=False)
    
    # Entry metadata
    type = Column(String(50), nullable=False, index=True)  # concept, rule, process, etc.
    title = Column(String(200), nullable=False, index=True)
    summary = Column(Text, nullable=True)
    
    # Content
    content = Column(Text, nullable=False)
    
    # Aliases and tags for search
    aliases = Column(JSON, default=list)  # List of alternative names
    tags = Column(JSON, default=list)     # List of tags
    
    # Relationships
    related_ids = Column(JSON, default=list)  # List of {entry_id, relation_type}
    
    # Sources and confidence
    sources = Column(JSON, default=list)  # List of source references
    confidence = Column(Float, default=1.0)  # 0.0 to 1.0
    
    # Status
    status = Column(String(20), default="active", index=True)  # active, archived, draft
    
    # Feedback tracking
    feedback_count = Column(Integer, default=0)
    positive_feedback = Column(Integer, default=0)
    negative_feedback = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    compiled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_wiki_title_type', 'title', 'type'),
        Index('idx_wiki_status_confidence', 'status', 'confidence'),
        Index('idx_wiki_created', 'created_at'),
    )
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "entry_id": self.entry_id,
            "version": self.version,
            "type": self.type,
            "title": self.title,
            "summary": self.summary,
            "content": self.content,
            "aliases": self.aliases or [],
            "tags": self.tags or [],
            "related_ids": self.related_ids or [],
            "sources": self.sources or [],
            "confidence": self.confidence,
            "status": self.status,
            "feedback_count": self.feedback_count,
            "positive_feedback": self.positive_feedback,
            "negative_feedback": self.negative_feedback,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "compiled_at": self.compiled_at.isoformat() if self.compiled_at else None,
        }


class WikiFeedback(Base):
    """
    User feedback for wiki entries.
    
    Tracks individual user feedback to calculate confidence scores.
    """
    __tablename__ = "wiki_feedback"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Foreign key to wiki entry
    entry_id = Column(String(100), ForeignKey("wiki_entries.entry_id"), nullable=False, index=True)
    
    # User identification (from JWT or LDAP)
    user_id = Column(String(100), nullable=False, index=True)
    
    # Feedback type
    feedback_type = Column(String(20), nullable=False)  # positive, negative, neutral
    
    # Optional comment
    comment = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    entry = relationship("WikiEntry", back_populates="feedbacks")
    
    __table_args__ = (
        Index('idx_feedback_entry_user', 'entry_id', 'user_id', unique=True),
    )
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "entry_id": self.entry_id,
            "user_id": self.user_id,
            "feedback_type": self.feedback_type,
            "comment": self.comment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# Add relationship to WikiEntry
WikiEntry.feedbacks = relationship("WikiFeedback", back_populates="entry", cascade="all, delete-orphan")


class APIKey(Base):
    """
    API key model for authentication and rate limiting.
    """
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Key hash (never store plain text keys)
    key_hash = Column(String(64), unique=True, nullable=False, index=True)
    
    # Metadata
    name = Column(String(100), nullable=False)
    owner = Column(String(100), nullable=True)  # User or service name
    
    # Permissions
    is_active = Column(Boolean, default=True, index=True)
    rate_limit = Column(Integer, default=100)  # Requests per minute
    
    # Usage tracking
    total_requests = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    def to_dict(self) -> dict:
        """Convert model to dictionary (excludes sensitive data)."""
        return {
            "id": self.id,
            "name": self.name,
            "owner": self.owner,
            "is_active": self.is_active,
            "rate_limit": self.rate_limit,
            "total_requests": self.total_requests,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class AuditLog(Base):
    """
    Audit log for tracking important actions.
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Action details
    action = Column(String(50), nullable=False, index=True)  # login, create, update, delete
    resource_type = Column(String(50), nullable=True)  # wiki_entry, api_key, etc.
    resource_id = Column(String(100), nullable=True)
    
    # User information
    user_id = Column(String(100), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    
    # Request details
    method = Column(String(10), nullable=True)  # GET, POST, etc.
    endpoint = Column(String(200), nullable=True)
    
    # Result
    status_code = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Additional context
    extra_metadata = Column("metadata", JSON, default=dict)  # Use 'metadata' as column name
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "method": self.method,
            "endpoint": self.endpoint,
            "status_code": self.status_code,
            "error_message": self.error_message,
            "metadata": self.extra_metadata,  # Return as 'metadata' in API
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ChatSession(Base):
    """
    Chat session model for storing conversation history.
    
    Tracks user chat sessions and message history.
    """
    __tablename__ = "chat_sessions"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Session identifier (UUID format)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # User information
    user_id = Column(String(100), nullable=True, index=True)  # Can be anonymous
    
    # Session metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Session status
    is_active = Column(Boolean, default=True, index=True)
    
    # Message count
    message_count = Column(Integer, default=0)
    
    # Session metadata (JSON for flexibility)
    session_metadata = Column(JSON, default=dict)  # Store additional session info
    
    def __repr__(self):
        return f"<ChatSession(session_id='{self.session_id}', user_id='{self.user_id}', messages={self.message_count})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_activity_at": self.last_activity_at.isoformat() if self.last_activity_at else None,
            "is_active": self.is_active,
            "message_count": self.message_count,
            "metadata": self.session_metadata,  # Return as 'metadata' in API
        }
