"""
Database Repository Layer

Implements repository pattern for database operations.
Provides clean separation between business logic and data access.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from datetime import datetime
import logging

from app.db.models import WikiEntry, WikiFeedback, APIKey, AuditLog

logger = logging.getLogger(__name__)


class WikiRepository:
    """Repository for wiki entry operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, entry_data: Dict[str, Any]) -> WikiEntry:
        """Create a new wiki entry."""
        entry = WikiEntry(**entry_data)
        self.session.add(entry)
        self.session.flush()
        logger.info(f"Created wiki entry: {entry.entry_id}")
        return entry
    
    def get_by_id(self, entry_id: str) -> Optional[WikiEntry]:
        """Get wiki entry by entry_id."""
        return self.session.query(WikiEntry).filter(
            WikiEntry.entry_id == entry_id
        ).first()
    
    def get_by_db_id(self, db_id: int) -> Optional[WikiEntry]:
        """Get wiki entry by database ID."""
        return self.session.query(WikiEntry).filter(
            WikiEntry.id == db_id
        ).first()
    
    def update(self, entry_id: str, update_data: Dict[str, Any]) -> Optional[WikiEntry]:
        """Update an existing wiki entry."""
        entry = self.get_by_id(entry_id)
        if not entry:
            return None
        
        # Increment version
        update_data['version'] = entry.version + 1
        
        for key, value in update_data.items():
            if hasattr(entry, key):
                setattr(entry, key, value)
        
        entry.updated_at = datetime.utcnow()
        self.session.flush()
        logger.info(f"Updated wiki entry: {entry_id} (v{entry.version})")
        return entry
    
    def delete(self, entry_id: str) -> bool:
        """Delete a wiki entry."""
        entry = self.get_by_id(entry_id)
        if not entry:
            return False
        
        self.session.delete(entry)
        self.session.flush()  # Ensure deletion is executed
        logger.info(f"Deleted wiki entry: {entry_id}")
        return True
    
    def search(
        self,
        query: str,
        type_filter: Optional[str] = None,
        status_filter: str = "active",
        limit: int = 10,
        offset: int = 0
    ) -> List[WikiEntry]:
        """
        Search wiki entries by title, content, aliases, or tags.
        
        Args:
            query: Search query string
            type_filter: Filter by entry type (optional)
            status_filter: Filter by status (default: active)
            limit: Maximum results to return
            offset: Offset for pagination
        
        Returns:
            List of matching WikiEntry objects
        """
        db_query = self.session.query(WikiEntry).filter(
            WikiEntry.status == status_filter
        )
        
        # Full-text search across multiple fields
        search_filter = or_(
            WikiEntry.title.ilike(f"%{query}%"),
            WikiEntry.content.ilike(f"%{query}%"),
            WikiEntry.summary.ilike(f"%{query}%"),
        )
        
        db_query = db_query.filter(search_filter)
        
        # Apply type filter if specified
        if type_filter:
            db_query = db_query.filter(WikiEntry.type == type_filter)
        
        # Order by confidence and recency
        db_query = db_query.order_by(
            WikiEntry.confidence.desc(),
            WikiEntry.updated_at.desc()
        )
        
        # Apply pagination
        db_query = db_query.limit(limit).offset(offset)
        
        return db_query.all()
    
    def list_all(
        self,
        type_filter: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[WikiEntry]:
        """List all wiki entries with optional filters."""
        db_query = self.session.query(WikiEntry)
        
        if type_filter:
            db_query = db_query.filter(WikiEntry.type == type_filter)
        
        if status_filter:
            db_query = db_query.filter(WikiEntry.status == status_filter)
        
        db_query = db_query.order_by(WikiEntry.created_at.desc())
        db_query = db_query.limit(limit).offset(offset)
        
        return db_query.all()
    
    def count(self, status_filter: Optional[str] = None) -> int:
        """Count wiki entries."""
        db_query = self.session.query(func.count(WikiEntry.id))
        
        if status_filter:
            db_query = db_query.filter(WikiEntry.status == status_filter)
        
        return db_query.scalar()
    
    def add_feedback(self, entry_id: str, user_id: str, feedback_type: str, comment: Optional[str] = None) -> Optional[WikiFeedback]:
        """Add user feedback to a wiki entry."""
        entry = self.get_by_id(entry_id)
        if not entry:
            return None
        
        # Check if user already provided feedback
        existing_feedback = self.session.query(WikiFeedback).filter(
            WikiFeedback.entry_id == entry_id,
            WikiFeedback.user_id == user_id
        ).first()
        
        if existing_feedback:
            # Update existing feedback
            old_type = existing_feedback.feedback_type
            existing_feedback.feedback_type = feedback_type
            existing_feedback.comment = comment
            
            # Update counters
            self._update_feedback_counters(entry, old_type, feedback_type)
        else:
            # Create new feedback
            feedback = WikiFeedback(
                entry_id=entry_id,
                user_id=user_id,
                feedback_type=feedback_type,
                comment=comment
            )
            self.session.add(feedback)
            
            # Update counters
            self._update_feedback_counters(entry, None, feedback_type)
        
        self.session.flush()
        return existing_feedback or feedback
    
    def _update_feedback_counters(self, entry: WikiEntry, old_type: Optional[str], new_type: str):
        """Update feedback counters on wiki entry and recalculate confidence."""
        if old_type:
            if old_type == "positive":
                entry.positive_feedback -= 1
            elif old_type == "negative":
                entry.negative_feedback -= 1
        
        if new_type == "positive":
            entry.positive_feedback += 1
        elif new_type == "negative":
            entry.negative_feedback += 1
        
        entry.feedback_count = entry.positive_feedback + entry.negative_feedback
        
        # Automatically recalculate confidence based on feedback ratio
        self._recalculate_confidence(entry)
    
    def _recalculate_confidence(self, entry: WikiEntry):
        """
        Recalculate confidence score based on user feedback.
        
        Formula: confidence = positive / (positive + negative)
        - Starts at 1.0 (default)
        - Adjusts based on feedback ratio
        - Minimum feedback threshold to avoid over-adjustment with few votes
        """
        total_feedback = entry.positive_feedback + entry.negative_feedback
        
        if total_feedback == 0:
            # No feedback yet, keep original confidence
            return
        
        # Calculate feedback ratio
        feedback_ratio = entry.positive_feedback / total_feedback
        
        # Apply smoothing to avoid extreme values with few votes
        # Use Bayesian average: (positive + 1) / (total + 2)
        # This pulls towards 0.5 when we have little data
        smoothed_confidence = (entry.positive_feedback + 1) / (total_feedback + 2)
        
        # Blend with original confidence (gradual adjustment)
        # Weight decreases as we get more feedback
        original_weight = max(0.3, 1.0 - (total_feedback * 0.05))  # Min 30% weight
        feedback_weight = 1.0 - original_weight
        
        # Calculate new confidence
        new_confidence = (entry.confidence * original_weight) + (smoothed_confidence * feedback_weight)
        
        # Clamp to valid range [0.1, 1.0]
        entry.confidence = max(0.1, min(1.0, new_confidence))
        
        logger.info(
            f"Recalculated confidence for {entry.entry_id}: "
            f"{entry.confidence:.2f} (positive={entry.positive_feedback}, "
            f"negative={entry.negative_feedback}, total={total_feedback})"
        )
    
    def get_low_confidence_entries(self, threshold: float = 0.6, limit: int = 20) -> List[WikiEntry]:
        """Get entries with low confidence scores for review."""
        return self.session.query(WikiEntry).filter(
            WikiEntry.confidence < threshold,
            WikiEntry.status == "active"
        ).order_by(
            WikiEntry.confidence.asc()
        ).limit(limit).all()
    
    def get_feedback_summary(self, entry_id: str) -> Dict[str, Any]:
        """
        Get feedback summary for a wiki entry.
        
        Args:
            entry_id: The entry ID
            
        Returns:
            Dictionary with feedback statistics
        """
        entry = self.get_by_id(entry_id)
        if not entry:
            return None
        
        # Count feedback by type
        positive_count = self.session.query(func.count(WikiFeedback.id)).filter(
            WikiFeedback.entry_id == entry_id,
            WikiFeedback.feedback_type == "positive"
        ).scalar() or 0
        
        negative_count = self.session.query(func.count(WikiFeedback.id)).filter(
            WikiFeedback.entry_id == entry_id,
            WikiFeedback.feedback_type == "negative"
        ).scalar() or 0
        
        total_count = positive_count + negative_count
        
        return {
            "entry_id": entry_id,
            "positive": positive_count,
            "negative": negative_count,
            "total": total_count,
            "ratio": positive_count / total_count if total_count > 0 else 0,
            "confidence": entry.confidence
        }


class APIKeyRepository:
    """Repository for API key operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, key_hash: str, name: str, owner: Optional[str] = None, rate_limit: int = 100) -> APIKey:
        """Create a new API key record."""
        api_key = APIKey(
            key_hash=key_hash,
            name=name,
            owner=owner,
            rate_limit=rate_limit
        )
        self.session.add(api_key)
        self.session.flush()
        return api_key
    
    def get_by_hash(self, key_hash: str) -> Optional[APIKey]:
        """Get API key by hash."""
        return self.session.query(APIKey).filter(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True
        ).first()
    
    def deactivate(self, key_hash: str) -> bool:
        """Deactivate an API key."""
        api_key = self.get_by_hash(key_hash)
        if not api_key:
            return False
        
        api_key.is_active = False
        self.session.flush()
        return True
    
    def increment_usage(self, key_hash: str):
        """Increment API key usage counter."""
        api_key = self.get_by_hash(key_hash)
        if api_key:
            api_key.total_requests += 1
            api_key.last_used_at = datetime.utcnow()
            self.session.flush()
    
    def list_all(self, active_only: bool = True) -> List[APIKey]:
        """List all API keys."""
        query = self.session.query(APIKey)
        if active_only:
            query = query.filter(APIKey.is_active == True)
        return query.order_by(APIKey.created_at.desc()).all()


class AuditLogRepository:
    """Repository for audit log operations."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_log(
        self,
        action: str,
        user_id: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        method: Optional[str] = None,
        endpoint: Optional[str] = None,
        status_code: Optional[int] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> AuditLog:
        """Create a new audit log entry."""
        log = AuditLog(
            action=action,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            error_message=error_message,
            metadata=metadata or {}
        )
        self.session.add(log)
        self.session.flush()
        return log
    
    def get_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """Query audit logs with filters."""
        query = self.session.query(AuditLog)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        if action:
            query = query.filter(AuditLog.action == action)
        
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)
        
        query = query.order_by(AuditLog.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        return query.all()
