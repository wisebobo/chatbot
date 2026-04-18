"""
LLM Wiki skill implementation
Provides structured wiki knowledge query capabilities using local wiki engine or company's Group AI Platform API
"""
import logging
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field

from app.config.settings import get_settings
from app.skills.base import BaseSkill, SkillExecutionError, SkillOutput
from app.wiki.engine import LocalWikiEngine
from app.wiki.sample_data import get_sample_articles

logger = logging.getLogger(__name__)


class WikiSearchParams(BaseModel):
    """Wiki search parameters"""
    query: str = Field(..., description="Search query or topic name")
    exact_match: bool = Field(default=False, description="Whether to use exact title matching")
    category: Optional[str] = Field(None, description="Filter by wiki category (optional)")
    include_sections: bool = Field(default=True, description="Whether to include all sections")
    max_length: Optional[int] = Field(None, description="Maximum content length to return", ge=100, le=10000)


class WikiSearchResult(BaseModel):
    """Single wiki search result"""
    title: str
    url: Optional[str] = None
    content: str
    category: Optional[str] = None
    last_updated: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class WikiSkill(BaseSkill):
    """
    LLM Wiki knowledge query skill
    Uses local wiki engine OR company's Group AI Platform API to retrieve structured wiki documentation
    
    When to use:
    - Query specific documented procedures or policies
    - Look up technical documentation with clear structure
    - Access well-organized knowledge articles
    - Retrieve information with known titles or categories
    
    Difference from RAG:
    - Wiki: Structured, curated content with clear organization
    - RAG: Unstructured documents with semantic similarity search
    
    Modes:
    - Local Mode: Uses built-in wiki engine (no external API needed)
    - Remote Mode: Uses Group AI Platform Wiki API (if configured)
    
    Example usage:
        # Basic wiki search
        {"query": "Annual Leave Policy"}
        
        # Exact title match
        {"query": "IT Equipment Request Process", "exact_match": true}
        
        # Filter by category
        {"query": "Reimbursement", "category": "Finance"}
        
        # Get concise version
        {"query": "Project Management Guidelines", "max_length": 500}
    """

    name = "wiki_search"
    description = "Query structured enterprise wiki knowledge base for documented procedures, policies, and technical documentation"
    require_human_approval = False

    def __init__(self):
        super().__init__()
        self._settings = get_settings().wiki
        
        # Initialize local wiki engine
        self._local_wiki = LocalWikiEngine()
        
        # Load sample data if wiki is empty
        if self._local_wiki.get_article_count() == 0:
            logger.info("Loading sample wiki articles...")
            sample_articles = get_sample_articles()
            self._local_wiki.import_articles(sample_articles)
            logger.info(f"Loaded {len(sample_articles)} sample articles")
        
        # Check if remote API is configured
        self._use_remote_api = bool(self._settings.api_key and 
                                     self._settings.api_url and 
                                     "your-group-ai-platform" not in self._settings.api_url.lower())
        
        if self._use_remote_api:
            logger.info("Wiki skill using remote API mode")
        else:
            logger.info("Wiki skill using local engine mode")

    async def execute(self, params: Dict[str, Any]) -> SkillOutput:
        """Execute wiki knowledge base search"""
        try:
            search_params = WikiSearchParams(**params)
        except Exception as e:
            return SkillOutput(success=False, error_message=f"Parameter validation failed: {e}")

        self.logger.info(f"Wiki search: query='{search_params.query[:50]}...', exact_match={search_params.exact_match}, mode={'remote' if self._use_remote_api else 'local'}")

        try:
            # Use remote API if configured, otherwise use local engine
            if self._use_remote_api:
                return await self._execute_remote(search_params)
            else:
                return await self._execute_local(search_params)

        except httpx.TimeoutException:
            raise SkillExecutionError(self.name, "Wiki API request timeout", retriable=True)
        except httpx.HTTPStatusError as e:
            raise SkillExecutionError(
                self.name, 
                f"Wiki API error: HTTP {e.response.status_code} - {e.response.text}", 
                retriable=False
            )
        except Exception as e:
            raise SkillExecutionError(self.name, f"Wiki search failed: {e}", retriable=True)

    async def _execute_remote(self, search_params: WikiSearchParams) -> SkillOutput:
        """Execute search using remote Group AI Platform API"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=self._settings.api_url,
                headers={
                    "Authorization": f"Bearer {self._settings.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "query": search_params.query,
                    "exact_match": search_params.exact_match,
                    "category": search_params.category,
                    "include_sections": search_params.include_sections,
                    "max_length": search_params.max_length,
                },
                timeout=self._settings.request_timeout,
            )
            response.raise_for_status()
            data = response.json()
            
            # Parse response (adjust according to your API format)
            results = []
            for item in data.get("articles", []):
                results.append(WikiSearchResult(
                    title=item.get("title", ""),
                    url=item.get("url"),
                    content=item.get("content", ""),
                    category=item.get("category"),
                    last_updated=item.get("last_updated"),
                    metadata=item.get("metadata"),
                ).dict())
            
            return SkillOutput(
                success=True,
                data={
                    "query": search_params.query,
                    "results": results,
                    "total_count": len(results),
                    "mode": "remote",
                }
            )

    async def _execute_local(self, search_params: WikiSearchParams) -> SkillOutput:
        """Execute search using local wiki engine"""
        # Search articles
        results = self._local_wiki.search_articles(
            query=search_params.query,
            exact_match=search_params.exact_match,
            category=search_params.category,
            max_results=10
        )
        
        # Format results
        formatted_results = []
        for article in results:
            content = article.get('content', '')
            
            # Truncate content if max_length specified
            if search_params.max_length and len(content) > search_params.max_length:
                content = content[:search_params.max_length] + "\n\n[Content truncated...]"
            
            formatted_results.append({
                "title": article.get('title', ''),
                "url": article.get('url'),
                "content": content,
                "category": article.get('category'),
                "last_updated": article.get('updated_at'),
                "relevance_score": article.get('relevance_score', 0),
                "metadata": article.get('metadata'),
            })
        
        return SkillOutput(
            success=True,
            data={
                "query": search_params.query,
                "results": formatted_results,
                "total_count": len(formatted_results),
                "mode": "local",
                "note": "Using local wiki engine. Add your own articles via admin interface.",
            }
        )

    def format_results_for_llm(self, results: Dict[str, Any]) -> str:
        """
        Format wiki search results for LLM context injection
        
        Args:
            results: Wiki search results from SkillOutput.data
            
        Returns:
            Formatted string suitable for LLM prompt context
        """
        if not results or "results" not in results or not results["results"]:
            return "No relevant wiki articles found"
        
        mode = results.get("mode", "unknown")
        formatted_parts = [f"**Search Mode:** {mode.upper()}"]
        
        for i, item in enumerate(results["results"], 1):
            parts = [f"\n[{i}] **Title:** {item.get('title', 'Unknown')}"]
            
            if item.get('category'):
                parts.append(f"    **Category:** {item['category']}")
            
            if item.get('relevance_score'):
                parts.append(f"    **Relevance:** {item['relevance_score']:.2f}")
            
            if item.get('last_updated'):
                parts.append(f"    **Last Updated:** {item['last_updated']}")
            
            if item.get('url'):
                parts.append(f"    **URL:** {item['url']}")
            
            parts.append(f"    **Content:**\n{item.get('content', '')}")
            
            formatted_parts.append("\n".join(parts))
        
        return "\n".join(formatted_parts)

    def get_tool_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The topic or question to search in the wiki knowledge base"
                        },
                        "exact_match": {
                            "type": "boolean",
                            "description": "Whether to use exact title matching (default: false)"
                        },
                        "category": {
                            "type": "string",
                            "description": "Filter by wiki category such as HR, IT, Finance, etc. (optional)"
                        },
                        "include_sections": {
                            "type": "boolean",
                            "description": "Whether to include all article sections (default: true)"
                        },
                        "max_length": {
                            "type": "integer",
                            "description": "Maximum content length to return, between 100-10000 characters (optional)"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
