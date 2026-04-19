"""
RAG (Retrieval-Augmented Generation) skill implementation
Provides knowledge base search capabilities using company's Group AI Platform API
"""
import logging
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field

from app.config.settings import get_settings
from app.skills.base import BaseSkill, SkillExecutionError, SkillOutput

logger = logging.getLogger(__name__)


class RagSearchParams(BaseModel):
    """RAG search parameters"""
    query: str = Field(..., description="Search query text")
    top_k: int = Field(default=5, description="Number of results to return", ge=1, le=20)
    knowledge_base: Optional[str] = Field(None, description="Specify knowledge base name (optional)")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filter conditions (optional)")
    min_relevance_score: float = Field(default=0.0, description="Minimum relevance score threshold", ge=0.0, le=1.0)


class RagSearchResult(BaseModel):
    """Single RAG search result"""
    content: str
    source: str
    relevance_score: float
    metadata: Optional[Dict[str, Any]] = None


class RagSkill(BaseSkill):
    """
    RAG knowledge base search skill
    Uses company's Group AI Platform API to retrieve relevant information from knowledge base
    
    Example usage:
        # Basic search
        {"query": "How to apply for annual leave?"}
        
        # Specify knowledge base and count
        {"query": "Reimbursement process", "top_k": 3, "knowledge_base": "HR Policies"}
        
        # With filter conditions
        {"query": "IT equipment request", "filters": {"category": "IT", "year": 2024}}
    """

    name = "rag_search"
    description = "Retrieve relevant information from enterprise knowledge base, supporting natural language queries and intelligent semantic search"
    require_human_approval = False

    def __init__(self):
        super().__init__()
        self._settings = get_settings().rag

    async def execute(self, params: Dict[str, Any]) -> SkillOutput:
        """Execute RAG knowledge base search"""
        try:
            search_params = RagSearchParams(**params)
        except Exception as e:
            return SkillOutput(success=False, error_message=f"Parameter validation failed: {e}")

        self.logger.info(f"RAG search: query='{search_params.query[:50]}...', top_k={search_params.top_k}")

        try:
            # ============================================================
            # TODO: Implement RAG API call logic for company Group AI Platform
            # ============================================================
            # 
            # Example code structure (modify according to actual requirements):
            #
            # async with httpx.AsyncClient() as client:
            #     response = await client.post(
            #         url=self._settings.api_url,
            #         headers={
            #             "Authorization": f"Bearer {self._settings.api_key}",
            #             "Content-Type": "application/json",
            #         },
            #         json={
            #             "query": search_params.query,
            #             "top_k": search_params.top_k,
            #             "knowledge_base": search_params.knowledge_base,
            #             "filters": search_params.filters,
            #             "min_relevance_score": search_params.min_relevance_score,
            #         },
            #         timeout=self._settings.request_timeout,
            #     )
            #     response.raise_for_status()
            #     data = response.json()
            #     
            #     # Parse response results
            #     results = []
            #     for item in data.get("results", []):
            #         results.append(RagSearchResult(
            #             content=item.get("content", ""),
            #             source=item.get("source", ""),
            #             relevance_score=item.get("relevance_score", 0.0),
            #             metadata=item.get("metadata"),
            #         ).dict())
            #     
            #     return SkillOutput(
            #         success=True,
            #         data={
            #             "query": search_params.query,
            #             "results": results,
            #             "total_count": len(results),
            #         }
            #     )
            #
            # ============================================================
            
            # Temporary placeholder implementation - please replace with actual API call
            self.logger.warning("RAG API not configured, returning mock data")
            
            # Mock results (for testing only, please remove in production)
            mock_results = [
                {
                    "content": f"This is sample knowledge base content about '{search_params.query}' - Example 1",
                    "source": "Knowledge Base Document A",
                    "relevance_score": 0.95,
                    "metadata": {"doc_id": "doc_001", "category": "technical"}
                },
                {
                    "content": f"This is sample knowledge base content about '{search_params.query}' - Example 2",
                    "source": "Knowledge Base Document B",
                    "relevance_score": 0.87,
                    "metadata": {"doc_id": "doc_002", "category": "business"}
                }
            ]
            
            return SkillOutput(
                success=True,
                data={
                    "query": search_params.query,
                    "results": mock_results,
                    "total_count": len(mock_results),
                    "note": "⚠️ This is mock data. Please configure the real RAG API endpoint.",
                }
            )

        except httpx.TimeoutException:
            raise SkillExecutionError(self.name, "RAG API request timeout", retriable=True)
        except httpx.HTTPStatusError as e:
            raise SkillExecutionError(
                self.name, 
                f"RAG API error: HTTP {e.response.status_code} - {e.response.text}", 
                retriable=False
            )
        except Exception as e:
            raise SkillExecutionError(self.name, f"RAG search failed: {e}", retriable=True)

    def format_results_for_llm(self, results: Dict[str, Any]) -> str:
        """
        Format RAG search results for LLM context injection
        
        Args:
            results: RAG search results from SkillOutput.data
            
        Returns:
            Formatted string suitable for LLM prompt context
        """
        if not results or "results" not in results or not results["results"]:
            return "No relevant knowledge base content found"
        
        formatted_parts = []
        for i, item in enumerate(results["results"], 1):
            formatted_parts.append(
                f"[{i}] Source: {item.get('source', 'Unknown')}\n"
                f"    Relevance: {item.get('relevance_score', 0):.2f}\n"
                f"    Content: {item.get('content', '')}\n"
            )
        
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
                            "description": "Search query text, use natural language to describe the information you want to find",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of results to return, default 5, range 1-20",
                            "minimum": 1,
                            "maximum": 20,
                        },
                        "knowledge_base": {
                            "type": "string",
                            "description": "Specify knowledge base name (optional, search all knowledge bases if not specified)",
                        },
                        "filters": {
                            "type": "object",
                            "description": "Filter conditions, such as date range, category, etc. (optional)",
                        },
                        "min_relevance_score": {
                            "type": "number",
                            "description": "Minimum relevance score threshold, 0.0-1.0, default 0.0",
                            "minimum": 0.0,
                            "maximum": 1.0,
                        },
                    },
                    "required": ["query"],
                },
            },
        }
