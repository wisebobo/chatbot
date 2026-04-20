"""
Database-backed Wiki engine using PostgreSQL/SQLite
Replaces file-based storage with database persistence
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.db.database import get_db_manager
from app.db.models import WikiEntry as DBWikiEntry
from app.db.repositories import WikiRepository
from app.wiki.engine import (
    EntryStatus,
    KnowledgeType,
    RelatedEntry,
    RelationType,
    SourceReference,
    UserFeedback,
    WikiArticle,
)

logger = logging.getLogger(__name__)


class DatabaseWikiEngine:
    """
    Database-backed Wiki engine with PostgreSQL/SQLite support
    
    Features:
    - Persistent storage with SQLAlchemy ORM
    - Automatic environment detection (SQLite for dev, PostgreSQL for prod)
    - Full-text search capabilities
    - Version control and audit trail
    - Feedback tracking and confidence scoring
    """

    def __init__(self):
        """Initialize database wiki engine"""
        self.db_manager = get_db_manager()
        logger.info("DatabaseWikiEngine initialized")

    def _convert_to_wiki_article(self, db_entry: DBWikiEntry) -> WikiArticle:
        """Convert database model to WikiArticle"""
        # Convert sources
        sources = []
        if db_entry.sources:
            for src_data in db_entry.sources:
                if isinstance(src_data, dict):
                    try:
                        sources.append(SourceReference(**src_data))
                    except Exception as e:
                        logger.warning(f"Failed to convert source: {e}")
        
        # Convert related_ids
        related = []
        if db_entry.related_ids:
            for rel_data in db_entry.related_ids:
                if isinstance(rel_data, dict):
                    try:
                        # Handle both old and new relation type formats
                        relation_value = rel_data.get("relation", "related_to")
                        if isinstance(relation_value, str):
                            # Map old relation types to new enum values
                            relation_mapping = {
                                "implements": "related_to",
                                "references": "related_to",
                                "example": "example_of",
                                "parent": "sub_concept",
                            }
                            mapped_relation = relation_mapping.get(relation_value, relation_value)
                            
                            # Ensure it's a valid enum value
                            try:
                                RelationType(mapped_relation)
                            except ValueError:
                                mapped_relation = "related_to"
                            
                            rel_data["relation"] = mapped_relation
                        
                        related.append(RelatedEntry(**rel_data))
                    except Exception as e:
                        logger.warning(f"Failed to convert related entry: {e}, data: {rel_data}")
        
        # Convert feedback
        feedback = UserFeedback(
            positive=db_entry.positive_feedback or 0,
            negative=db_entry.negative_feedback or 0
        )
        
        return WikiArticle(
            entry_id=db_entry.entry_id,
            title=db_entry.title,
            aliases=db_entry.aliases or [],
            type=KnowledgeType(db_entry.type),
            content=db_entry.content,
            summary=db_entry.summary,
            parent_ids=[],  # Not stored in DB yet
            related_ids=related,
            tags=db_entry.tags or [],
            sources=sources,
            confidence=db_entry.confidence or 1.0,
            status=EntryStatus(db_entry.status),
            version=db_entry.version,
            create_time=db_entry.created_at.isoformat() if db_entry.created_at else datetime.now().isoformat(),
            update_time=db_entry.updated_at.isoformat() if db_entry.updated_at else datetime.now().isoformat(),
            feedback=feedback,
            metadata={}
        )

    def _convert_to_db_entry(self, article: WikiArticle) -> Dict[str, Any]:
        """Convert WikiArticle to database entry dict"""
        # Convert sources to dict
        sources = []
        if article.sources:
            for src in article.sources:
                sources.append(src.model_dump() if hasattr(src, 'model_dump') else src.dict())
        
        # Convert related_ids to dict
        related = []
        if article.related_ids:
            for rel in article.related_ids:
                related.append(rel.model_dump() if hasattr(rel, 'model_dump') else rel.dict())
        
        return {
            "entry_id": article.entry_id,
            "version": article.version,
            "type": article.type.value if hasattr(article.type, 'value') else str(article.type),
            "title": article.title,
            "summary": article.summary,
            "content": article.content,
            "aliases": article.aliases,
            "tags": article.tags,
            "related_ids": related,
            "sources": sources,
            "confidence": article.confidence,
            "status": article.status.value if hasattr(article.status, 'value') else str(article.status),
            "positive_feedback": article.feedback.positive,
            "negative_feedback": article.feedback.negative,
            "feedback_count": article.feedback.positive + article.feedback.negative,
        }

    def get_article(self, entry_id: str) -> Optional[WikiArticle]:
        """Get wiki article by entry_id"""
        with self.db_manager.get_session() as session:
            repo = WikiRepository(session)
            db_entry = repo.get_by_id(entry_id)
            
            if not db_entry:
                return None
            
            return self._convert_to_wiki_article(db_entry)

    def save_article(self, article: WikiArticle) -> WikiArticle:
        """Save or update wiki article"""
        with self.db_manager.get_session() as session:
            repo = WikiRepository(session)
            
            # Check if exists
            existing = repo.get_by_id(article.entry_id)
            
            if existing:
                # Update existing
                update_data = self._convert_to_db_entry(article)
                updated = repo.update(article.entry_id, update_data)
                logger.info(f"Updated wiki article: {article.entry_id} (v{article.version})")
            else:
                # Create new
                db_data = self._convert_to_db_entry(article)
                created = repo.create(db_data)
                logger.info(f"Created wiki article: {article.entry_id}")
            
            session.commit()
            return article

    def delete_article(self, entry_id: str) -> bool:
        """Delete wiki article"""
        with self.db_manager.get_session() as session:
            repo = WikiRepository(session)
            deleted = repo.delete(entry_id)
            session.commit()
            
            if deleted:
                logger.info(f"Deleted wiki article: {entry_id}")
            
            return deleted

    def search_articles(
        self,
        query: str,
        category: Optional[str] = None,
        exact_match: bool = False,
        limit: int = 10
    ) -> List[WikiArticle]:
        """Search wiki articles"""
        with self.db_manager.get_session() as session:
            repo = WikiRepository(session)
            
            if exact_match:
                # Exact title match
                db_entries = repo.session.query(DBWikiEntry).filter(
                    DBWikiEntry.title == query,
                    DBWikiEntry.status == "active"
                ).limit(limit).all()
            else:
                # Full-text search
                type_filter = category if category else None
                db_entries = repo.search(
                    query=query,
                    type_filter=type_filter,
                    status_filter="active",
                    limit=limit
                )
            
            return [self._convert_to_wiki_article(entry) for entry in db_entries]

    def list_articles(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[WikiArticle]:
        """List all wiki articles with optional filters"""
        with self.db_manager.get_session() as session:
            repo = WikiRepository(session)
            
            type_filter = category if category else None
            status_filter = status if status else None
            
            db_entries = repo.list_all(
                type_filter=type_filter,
                status_filter=status_filter,
                limit=limit
            )
            
            return [self._convert_to_wiki_article(entry) for entry in db_entries]

    def add_feedback(self, entry_id: str, user_id: str, is_positive: bool, comment: Optional[str] = None) -> bool:
        """Add user feedback to wiki article"""
        with self.db_manager.get_session() as session:
            repo = WikiRepository(session)
            
            feedback_type = "positive" if is_positive else "negative"
            feedback = repo.add_feedback(
                entry_id=entry_id,
                user_id=user_id,
                feedback_type=feedback_type,
                comment=comment
            )
            
            if feedback:
                session.commit()
                logger.info(f"Added {feedback_type} feedback for {entry_id} by {user_id}")
                return True
            
            return False

    def get_article_count(self) -> int:
        """Get total number of active articles"""
        with self.db_manager.get_session() as session:
            repo = WikiRepository(session)
            return repo.count(status_filter="active")

    def import_articles(self, articles: List) -> int:
        """Import multiple articles (accepts WikiArticle objects or dicts)"""
        count = 0
        for article in articles:
            try:
                # Convert dict to WikiArticle if needed
                if isinstance(article, dict):
                    from app.wiki.engine import WikiArticle
                    article = WikiArticle(**article)
                
                self.save_article(article)
                count += 1
            except Exception as e:
                entry_id = article.entry_id if hasattr(article, 'entry_id') else article.get('entry_id', 'unknown')
                logger.error(f"Failed to import article {entry_id}: {e}")
        
        logger.info(f"Imported {count}/{len(articles)} articles")
        return count
