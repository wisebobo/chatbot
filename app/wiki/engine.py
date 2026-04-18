"""
Local Wiki knowledge base implementation
Provides structured wiki article storage and search capabilities without external API dependency
"""
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class WikiArticle(BaseModel):
    """Wiki article model"""
    id: str
    title: str
    content: str
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    url: Optional[str] = None
    author: Optional[str] = None
    version: str = "1.0"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Optional[Dict[str, Any]] = None


class LocalWikiEngine:
    """
    Local Wiki engine with file-based storage
    Supports CRUD operations and full-text search
    """

    def __init__(self, storage_dir: str = "data/wiki"):
        """
        Initialize local wiki engine
        
        Args:
            storage_dir: Directory to store wiki articles (JSON files)
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.articles: Dict[str, WikiArticle] = {}
        self._load_articles()
        logger.info(f"LocalWikiEngine initialized with {len(self.articles)} articles")

    def _get_article_path(self, article_id: str) -> Path:
        """Get file path for an article"""
        return self.storage_dir / f"{article_id}.json"

    def _load_articles(self):
        """Load all articles from storage directory"""
        if not self.storage_dir.exists():
            return
        
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    article = WikiArticle(**data)
                    self.articles[article.id] = article
            except Exception as e:
                logger.warning(f"Failed to load article from {file_path}: {e}")

    def _save_article(self, article: WikiArticle):
        """Save single article to storage"""
        file_path = self._get_article_path(article.id)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(article.dict(), f, indent=2, ensure_ascii=False)

    def add_article(self, article_data: Dict[str, Any]) -> WikiArticle:
        """
        Add a new wiki article
        
        Args:
            article_data: Article data dictionary
            
        Returns:
            Created WikiArticle object
        """
        # Generate ID if not provided
        if 'id' not in article_data:
            article_data['id'] = f"wiki_{len(self.articles) + 1:04d}"
        
        # Set timestamps
        now = datetime.now().isoformat()
        article_data['created_at'] = now
        article_data['updated_at'] = now
        
        article = WikiArticle(**article_data)
        self.articles[article.id] = article
        self._save_article(article)
        
        logger.info(f"Added wiki article: {article.title} (ID: {article.id})")
        return article

    def update_article(self, article_id: str, updates: Dict[str, Any]) -> Optional[WikiArticle]:
        """
        Update an existing wiki article
        
        Args:
            article_id: Article ID to update
            updates: Fields to update
            
        Returns:
            Updated WikiArticle or None if not found
        """
        if article_id not in self.articles:
            logger.warning(f"Article not found: {article_id}")
            return None
        
        article = self.articles[article_id]
        
        # Update fields
        for key, value in updates.items():
            if hasattr(article, key) and key not in ['id', 'created_at']:
                setattr(article, key, value)
        
        # Update timestamp
        article.updated_at = datetime.now().isoformat()
        
        # Save to disk
        self._save_article(article)
        
        logger.info(f"Updated wiki article: {article.title} (ID: {article_id})")
        return article

    def delete_article(self, article_id: str) -> bool:
        """
        Delete a wiki article
        
        Args:
            article_id: Article ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        if article_id not in self.articles:
            logger.warning(f"Article not found for deletion: {article_id}")
            return False
        
        article = self.articles.pop(article_id)
        
        # Remove from disk
        file_path = self._get_article_path(article_id)
        if file_path.exists():
            file_path.unlink()
        
        logger.info(f"Deleted wiki article: {article.title} (ID: {article_id})")
        return True

    def get_article(self, article_id: str) -> Optional[WikiArticle]:
        """Get article by ID"""
        return self.articles.get(article_id)

    def search_articles(
        self,
        query: str,
        exact_match: bool = False,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        max_results: int = 10,
        max_length: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search wiki articles
        
        Args:
            query: Search query string
            exact_match: Whether to use exact title matching
            category: Filter by category
            tags: Filter by tags
            max_results: Maximum number of results to return
            
        Returns:
            List of matching articles (sorted by relevance)
        """
        results = []
        query_lower = query.lower()
        
        for article in self.articles.values():
            # Category filter
            if category and article.category != category:
                continue
            
            # Tags filter
            if tags and not any(tag in article.tags for tag in tags):
                continue
            
            # Calculate relevance score
            score = 0.0
            
            if exact_match:
                # Exact title match only
                if article.title.lower() == query_lower:
                    score = 1.0
                else:
                    continue
            else:
                # Title match (high weight)
                if query_lower in article.title.lower():
                    score += 0.7
                
                # Content match (medium weight)
                if query_lower in article.content.lower():
                    score += 0.2
                
                # Tags match (low weight)
                if any(query_lower in tag.lower() for tag in article.tags):
                    score += 0.1
            
            # Only include articles with some relevance
            if score > 0:
                result = article.model_dump()
                result['relevance_score'] = score
                results.append(result)
        
        # Sort by relevance score (descending)
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Limit results
        limited_results = results[:max_results]
        
        # Format results
        formatted_results = []
        for article in limited_results:
            content = article.get('content', '')
            
            # Truncate content if max_length specified
            if max_length and len(content) > max_length:
                content = content[:max_length] + "\n\n[Content truncated...]"
            
            formatted_results.append({
                "title": article.get('title', ''),
                "url": article.get('url'),
                "content": content,
                "category": article.get('category'),
                "last_updated": article.get('updated_at'),
                "relevance_score": article.get('relevance_score', 0),
                "metadata": article.get('metadata'),
            })
            
        return formatted_results

    def get_all_categories(self) -> List[str]:
        """Get list of all unique categories"""
        categories = set()
        for article in self.articles.values():
            if article.category:
                categories.add(article.category)
        return sorted(list(categories))

    def get_all_tags(self) -> List[str]:
        """Get list of all unique tags"""
        tags = set()
        for article in self.articles.values():
            tags.update(article.tags)
        return sorted(list(tags))

    def get_article_count(self) -> int:
        """Get total number of articles"""
        return len(self.articles)

    def export_articles(self) -> List[Dict[str, Any]]:
        """Export all articles as list of dictionaries"""
        return [article.model_dump() for article in self.articles.values()]

    def import_articles(self, articles_data: List[Dict[str, Any]]):
        """
        Import articles from list of dictionaries
        
        Args:
            articles_data: List of article data dictionaries
        """
        for data in articles_data:
            try:
                article = WikiArticle(**data)
                self.articles[article.id] = article
                self._save_article(article)
            except Exception as e:
                logger.warning(f"Failed to import article: {e}")
        
        logger.info(f"Imported {len(articles_data)} articles")
