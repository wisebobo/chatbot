"""
Enhanced Wiki knowledge base implementation with advanced features
Supports versioning, relationships, feedback loop, and knowledge graph
"""
import json
import logging
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class KnowledgeType(str, Enum):
    """Knowledge entry types following ITIL and knowledge management standards"""
    CONCEPT = "concept"      # Concepts and definitions
    RULE = "rule"            # Business rules and policies
    PROCESS = "process"      # Workflows and procedures
    CASE = "case"            # Case studies and examples
    FORMULA = "formula"      # Formulas and calculations
    QA = "qa"                # Q&A pairs
    EVENT = "event"          # Events and incidents


class RelationType(str, Enum):
    """Types of relationships between knowledge entries"""
    RELATED_TO = "related_to"           # General relationship
    DEPENDS_ON = "depends_on"           # Dependency relationship
    CONFLICT_WITH = "conflict_with"     # Conflicting information
    EXAMPLE_OF = "example_of"           # Example/instance relationship
    SUB_CONCEPT = "sub_concept"         # Hierarchical relationship


class EntryStatus(str, Enum):
    """Lifecycle status of knowledge entries"""
    ACTIVE = "active"               # Currently valid and active
    DRAFT = "draft"                 # Under review or creation
    DEPRECATED = "deprecated"       # Outdated or replaced
    CONFLICTED = "conflicted"       # Has conflicting information


class SourceReference(BaseModel):
    """Source reference for knowledge traceability"""
    source_id: str = Field(..., description="Unique identifier of the source document")
    file_name: Optional[str] = Field(None, description="Original file name")
    page: Optional[int] = Field(None, description="Page number in the source document")
    content_snippet: str = Field(..., description="Excerpt from original content for verification")
    url: Optional[str] = Field(None, description="URL to the source document if available")


class RelatedEntry(BaseModel):
    """Relationship to another knowledge entry"""
    entry_id: str = Field(..., description="ID of the related knowledge entry")
    relation: RelationType = Field(..., description="Type of relationship")


class UserFeedback(BaseModel):
    """User feedback for continuous improvement"""
    positive: int = Field(default=0, description="Number of positive feedback")
    negative: int = Field(default=0, description="Number of negative feedback")
    comments: List[str] = Field(default_factory=list, description="User comments and suggestions")


class WikiArticle(BaseModel):
    """
    Enhanced wiki article model with knowledge graph capabilities
    
    Features:
    - Version control for incremental updates
    - Relationship mapping for knowledge network
    - Confidence scoring and user feedback loop
    - Source traceability to reduce hallucinations
    - Status management for conflict detection
    """
    
    # Core identification
    entry_id: str = Field(..., description="Global unique ID for deduplication and linking (e.g., concept_loan_rate)")
    title: str = Field(..., description="Article title, typically a noun/term/question")
    aliases: List[str] = Field(default_factory=list, description="Aliases, synonyms, alternative names for semantic matching")
    
    # Content and classification
    type: KnowledgeType = Field(..., description="Knowledge type: concept/rule/process/case/formula/qa/event")
    content: str = Field(..., description="Structured body text in Markdown format for answer generation")
    summary: Optional[str] = Field(None, description="Concise summary for quick retrieval and display")
    
    # Hierarchy and relationships
    parent_ids: List[str] = Field(default_factory=list, description="Parent entry IDs for hierarchical structure")
    related_ids: List[RelatedEntry] = Field(default_factory=list, description="Related entries and relationship types")
    tags: List[str] = Field(default_factory=list, description="Classification tags for filtering and search")
    
    # Traceability and quality
    sources: List[SourceReference] = Field(default_factory=list, description="Knowledge sources for traceability")
    confidence: float = Field(
        default=1.0, 
        ge=0.0, 
        le=1.0, 
        description="Confidence score (0-1) for automatic validation priority"
    )
    
    # Lifecycle management
    status: EntryStatus = Field(default=EntryStatus.ACTIVE, description="Status: active/draft/deprecated/conflicted")
    version: int = Field(default=1, description="Version number, incremented on each update")
    create_time: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Creation timestamp"
    )
    update_time: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Last update timestamp"
    )
    
    # Feedback loop
    feedback: UserFeedback = Field(default_factory=UserFeedback, description="User feedback for automatic optimization")
    
    # Extended metadata
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional custom metadata")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @field_validator('sources', mode='before')
    @classmethod
    def validate_sources(cls, v):
        """Ensure sources are converted to SourceReference objects"""
        if isinstance(v, list):
            return [
                SourceReference(**item) if isinstance(item, dict) else item
                for item in v
            ]
        return v
    
    @field_validator('related_ids', mode='before')
    @classmethod
    def validate_related_ids(cls, v):
        """Ensure related_ids are converted to RelatedEntry objects"""
        if isinstance(v, list):
            return [
                RelatedEntry(**item) if isinstance(item, dict) else item
                for item in v
            ]
        return v
    
    @field_validator('feedback', mode='before')
    @classmethod
    def validate_feedback(cls, v):
        """Ensure feedback is converted to UserFeedback object"""
        if isinstance(v, dict):
            return UserFeedback(**v)
        return v


class LocalWikiEngine:
    """
    Enhanced Local Wiki engine with knowledge graph capabilities
    
    Features:
    - Version control for incremental updates (entry_id + version)
    - Relationship mapping for knowledge network (related_ids)
    - Confidence scoring and user feedback loop (confidence + feedback)
    - Source traceability to reduce hallucinations (sources)
    - Status management for conflict detection (status)
    - Semantic search with aliases support
    """

    def __init__(self, storage_dir: str = "data/wiki"):
        """
        Initialize enhanced local wiki engine
        
        Args:
            storage_dir: Directory to store wiki articles (JSON files)
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.articles: Dict[str, WikiArticle] = {}
        self._load_articles()
        logger.info(f"LocalWikiEngine initialized with {len(self.articles)} articles")

    def _get_article_path(self, entry_id: str) -> Path:
        """Get file path for an article"""
        return self.storage_dir / f"{entry_id}.json"

    def _load_articles(self):
        """Load all articles from storage directory"""
        if not self.storage_dir.exists():
            return
        
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    article = WikiArticle(**data)
                    self.articles[article.entry_id] = article
            except Exception as e:
                logger.warning(f"Failed to load article from {file_path}: {e}")

    def _save_article(self, article: WikiArticle):
        """Save single article to storage"""
        file_path = self._get_article_path(article.entry_id)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(article.model_dump(), f, indent=2, ensure_ascii=False)

    def add_article(self, article_data: Dict[str, Any]) -> WikiArticle:
        """
        Add a new wiki article with automatic ID generation
        
        Args:
            article_data: Article data dictionary
            
        Returns:
            Created WikiArticle object
        """
        # Generate entry_id if not provided
        if 'entry_id' not in article_data:
            # Create meaningful ID from title if available
            title = article_data.get('title', 'untitled')
            entry_id = f"{title.lower().replace(' ', '_')[:30]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            article_data['entry_id'] = entry_id
        
        # Set timestamps
        now = datetime.now().isoformat()
        article_data['create_time'] = now
        article_data['update_time'] = now
        
        # Initialize version
        if 'version' not in article_data:
            article_data['version'] = 1
        
        article = WikiArticle(**article_data)
        self.articles[article.entry_id] = article
        self._save_article(article)
        
        logger.info(f"Added wiki article: {article.title} (ID: {article.entry_id}, Type: {article.type})")
        return article

    def update_article(self, entry_id: str, updates: Dict[str, Any]) -> Optional[WikiArticle]:
        """
        Update an existing wiki article with version increment
        
        Args:
            entry_id: Article entry_id to update
            updates: Fields to update
            
        Returns:
            Updated WikiArticle or None if not found
        """
        if entry_id not in self.articles:
            logger.warning(f"Article not found: {entry_id}")
            return None
        
        article = self.articles[entry_id]
        
        # Get current article data as dict
        article_data = article.model_dump()
        
        # Apply updates (excluding immutable fields)
        immutable_fields = ['entry_id', 'create_time']
        for key, value in updates.items():
            if key not in immutable_fields:
                article_data[key] = value
        
        # Re-create the article object to trigger validators
        try:
            updated_article = WikiArticle(**article_data)
            
            # Increment version and update timestamp
            updated_article.version += 1
            updated_article.update_time = datetime.now().isoformat()
            
            # Save to disk
            self.articles[entry_id] = updated_article
            self._save_article(updated_article)
            
            logger.info(f"Updated wiki article: {updated_article.title} (ID: {entry_id}, Version: {updated_article.version})")
            return updated_article
        except Exception as e:
            logger.error(f"Failed to update article {entry_id}: {e}")
            return None

    def delete_article(self, entry_id: str) -> bool:
        """
        Soft delete a wiki article by marking as deprecated
        
        Args:
            entry_id: Article entry_id to delete
            
        Returns:
            True if marked as deprecated, False if not found
        """
        if entry_id not in self.articles:
            logger.warning(f"Article not found for deletion: {entry_id}")
            return False
        
        article = self.articles[entry_id]
        article.status = EntryStatus.DEPRECATED
        article.update_time = datetime.now().isoformat()
        article.version += 1
        
        self._save_article(article)
        
        logger.info(f"Deprecated wiki article: {article.title} (ID: {entry_id})")
        return True

    def hard_delete_article(self, entry_id: str) -> bool:
        """
        Permanently delete a wiki article (use with caution)
        
        Args:
            entry_id: Article entry_id to delete
            
        Returns:
            True if deleted, False if not found
        """
        if entry_id not in self.articles:
            logger.warning(f"Article not found for hard deletion: {entry_id}")
            return False
        
        article = self.articles.pop(entry_id)
        
        # Remove from disk
        file_path = self._get_article_path(entry_id)
        if file_path.exists():
            file_path.unlink()
        
        logger.info(f"Hard deleted wiki article: {article.title} (ID: {entry_id})")
        return True

    def get_article(self, entry_id: str) -> Optional[WikiArticle]:
        """Get article by entry_id"""
        return self.articles.get(entry_id)

    def search_articles(
        self,
        query: str,
        exact_match: bool = False,
        knowledge_type: Optional[KnowledgeType] = None,
        tags: Optional[List[str]] = None,
        status: Optional[EntryStatus] = None,
        min_confidence: float = 0.0,
        max_results: int = 10,
        max_length: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Enhanced search with semantic matching and filtering
        
        Args:
            query: Search query string
            exact_match: Whether to use exact title/alias matching
            knowledge_type: Filter by knowledge type
            tags: Filter by tags
            status: Filter by status (default: only ACTIVE)
            min_confidence: Minimum confidence score threshold
            max_results: Maximum number of results to return
            
        Returns:
            List of matching articles sorted by relevance
        """
        results = []
        query_lower = query.lower()
        
        # Default to active articles only
        if status is None:
            status = EntryStatus.ACTIVE
        
        for article in self.articles.values():
            # Status filter
            if article.status != status:
                continue
            
            # Knowledge type filter
            if knowledge_type and article.type != knowledge_type:
                continue
            
            # Tags filter
            if tags and not any(tag in article.tags for tag in tags):
                continue
            
            # Confidence filter
            if article.confidence < min_confidence:
                continue
            
            # Calculate relevance score
            score = 0.0
            
            if exact_match:
                # Exact title match
                if article.title.lower() == query_lower:
                    score = 1.0
                # Alias match
                elif any(alias.lower() == query_lower for alias in article.aliases):
                    score = 0.95
                else:
                    continue
            else:
                # Title match (high weight)
                if query_lower in article.title.lower():
                    score += 0.7
                
                # Alias match (high weight)
                if any(query_lower in alias.lower() for alias in article.aliases):
                    score += 0.65
                
                # Summary match (medium-high weight)
                if article.summary and query_lower in article.summary.lower():
                    score += 0.5
                
                # Content match (medium weight)
                if query_lower in article.content.lower():
                    score += 0.3
                
                # Tags match (low weight)
                if any(query_lower in tag.lower() for tag in article.tags):
                    score += 0.15
            
            # Only include articles with some relevance
            if score > 0:
                result = article.model_dump()
                result['relevance_score'] = score
                results.append(result)
        
        # Sort by relevance score (descending), then by confidence
        results.sort(key=lambda x: (x['relevance_score'], x.get('confidence', 0)), reverse=True)
        
        # Limit results
        limited_results = results[:max_results]
        
        # Format results
        formatted_results = []
        for article_data in limited_results:
            content = article_data.get('content', '')
            
            # Truncate content if max_length specified
            if max_length and len(content) > max_length:
                content = content[:max_length] + "\n\n[Content truncated...]"
            
            formatted_results.append({
                "entry_id": article_data.get('entry_id'),
                "title": article_data.get('title', ''),
                "type": article_data.get('type'),
                "summary": article_data.get('summary'),
                "content": content,
                "tags": article_data.get('tags', []),
                "confidence": article_data.get('confidence', 1.0),
                "version": article_data.get('version', 1),
                "update_time": article_data.get('update_time'),
                "related_ids": article_data.get('related_ids', []),
                "sources": article_data.get('sources', []),
                "relevance_score": article_data.get('relevance_score', 0),
            })
            
        return formatted_results

    def get_related_articles(self, entry_id: str, relation_type: Optional[RelationType] = None) -> List[Dict[str, Any]]:
        """
        Get related articles based on knowledge graph relationships
        
        Args:
            entry_id: Source article entry_id
            relation_type: Optional filter by relationship type
            
        Returns:
            List of related articles with relationship information
        """
        article = self.articles.get(entry_id)
        if not article:
            return []
        
        related = []
        for rel in article.related_ids:
            if relation_type and rel.relation != relation_type:
                continue
            
            related_article = self.articles.get(rel.entry_id)
            if related_article:
                related.append({
                    "entry_id": rel.entry_id,
                    "relation": rel.relation,
                    "title": related_article.title,
                    "summary": related_article.summary,
                    "type": related_article.type,
                })
        
        return related

    def submit_feedback(self, entry_id: str, is_positive: bool, comment: Optional[str] = None) -> bool:
        """
        Submit user feedback for continuous improvement
        
        Args:
            entry_id: Article entry_id
            is_positive: True for positive feedback, False for negative
            comment: Optional user comment
            
        Returns:
            True if feedback recorded successfully
        """
        article = self.articles.get(entry_id)
        if not article:
            logger.warning(f"Article not found for feedback: {entry_id}")
            return False
        
        if is_positive:
            article.feedback.positive += 1
        else:
            article.feedback.negative += 1
        
        if comment:
            article.feedback.comments.append(comment)
        
        # Recalculate confidence based on feedback ratio
        total_feedback = article.feedback.positive + article.feedback.negative
        if total_feedback > 0:
            feedback_ratio = article.feedback.positive / total_feedback
            # Blend original confidence with feedback ratio
            article.confidence = 0.7 * article.confidence + 0.3 * feedback_ratio
        
        article.update_time = datetime.now().isoformat()
        self._save_article(article)
        
        logger.info(f"Feedback recorded for article {entry_id}: {'positive' if is_positive else 'negative'}")
        return True

    def detect_conflicts(self) -> List[Dict[str, Any]]:
        """
        Detect potential conflicts between articles based on relationship mapping
        
        Returns:
            List of conflicting article pairs
        """
        conflicts = []
        
        for article in self.articles.values():
            for rel in article.related_ids:
                if rel.relation == RelationType.CONFLICT_WITH:
                    related_article = self.articles.get(rel.entry_id)
                    if related_article:
                        conflicts.append({
                            "article_1": {
                                "entry_id": article.entry_id,
                                "title": article.title,
                                "update_time": article.update_time,
                            },
                            "article_2": {
                                "entry_id": rel.entry_id,
                                "title": related_article.title,
                                "update_time": related_article.update_time,
                            },
                            "relation": rel.relation,
                        })
        
        return conflicts

    def get_all_types(self) -> List[str]:
        """Get list of all unique knowledge types"""
        types = set()
        for article in self.articles.values():
            types.add(article.type.value if isinstance(article.type, KnowledgeType) else article.type)
        return sorted(list(types))

    def get_all_tags(self) -> List[str]:
        """Get list of all unique tags"""
        tags = set()
        for article in self.articles.values():
            tags.update(article.tags)
        return sorted(list(tags))

    def get_article_count(self) -> int:
        """Get total number of articles"""
        return len(self.articles)

    def get_active_article_count(self) -> int:
        """Get count of active articles"""
        return sum(1 for a in self.articles.values() if a.status == EntryStatus.ACTIVE)

    def export_articles(self) -> List[Dict[str, Any]]:
        """Export all articles as list of dictionaries"""
        return [article.model_dump() for article in self.articles.values()]

    def import_articles(self, articles_data: List[Dict[str, Any]]) -> int:
        """
        Import articles from list of dictionaries
        
        Args:
            articles_data: List of article data dictionaries
            
        Returns:
            Number of successfully imported articles
        """
        imported_count = 0
        for data in articles_data:
            try:
                article = WikiArticle(**data)
                self.articles[article.entry_id] = article
                self._save_article(article)
                imported_count += 1
            except Exception as e:
                logger.warning(f"Failed to import article: {e}")
        
        logger.info(f"Imported {imported_count}/{len(articles_data)} articles")
        return imported_count
