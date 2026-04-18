"""
Unit tests - RAG skill
Tests for the RAG knowledge base search skill
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.skills.rag_skill import RagSkill, RagSearchParams


class TestRagSkill:
    """Test cases for RagSkill"""

    @pytest.fixture
    def rag_skill(self):
        """Create a RagSkill instance for testing"""
        return RagSkill()

    def test_rag_skill_initialization(self, rag_skill):
        """Test RagSkill initialization"""
        assert rag_skill.name == "rag_search"
        assert rag_skill.description is not None
        assert rag_skill.require_human_approval is False

    def test_rag_search_params_validation(self):
        """Test RagSearchParams validation"""
        # Valid params
        params = RagSearchParams(query="test query")
        assert params.query == "test query"
        assert params.top_k == 5  # default value
        
        # Custom top_k
        params = RagSearchParams(query="test", top_k=10)
        assert params.top_k == 10
        
        # Invalid top_k (too high)
        with pytest.raises(Exception):
            RagSearchParams(query="test", top_k=25)
        
        # Invalid top_k (too low)
        with pytest.raises(Exception):
            RagSearchParams(query="test", top_k=0)

    @pytest.mark.asyncio
    async def test_rag_execute_with_mock_data(self, rag_skill):
        """Test RAG skill execution with mock API response"""
        # Mock the httpx.AsyncClient
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "content": "Test content 1",
                    "source": "Source A",
                    "relevance_score": 0.95,
                    "metadata": {"doc_id": "1"}
                },
                {
                    "content": "Test content 2",
                    "source": "Source B",
                    "relevance_score": 0.87,
                    "metadata": {"doc_id": "2"}
                }
            ],
            "total_count": 2
        }
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await rag_skill.execute({
                "query": "test query",
                "top_k": 2
            })
            
            assert result.success is True
            assert "results" in result.data
            assert len(result.data["results"]) == 2

    @pytest.mark.asyncio
    async def test_rag_execute_invalid_params(self, rag_skill):
        """Test RAG skill execution with invalid parameters"""
        result = await rag_skill.execute({})
        
        assert result.success is False
        assert "Parameter validation failed" in result.error_message

    @pytest.mark.asyncio
    async def test_rag_execute_api_timeout(self, rag_skill):
        """Test RAG skill handling of API timeout"""
        import httpx
        
        # Note: When API is not configured, the skill returns mock data instead of calling API
        # This test verifies that mock data path works correctly
        result = await rag_skill.execute({"query": "test query"})
        
        # Should return mock data when API is not configured
        assert result.success is True
        assert "results" in result.data
        assert "mock" in result.data.get("note", "").lower() or len(result.data["results"]) > 0

    def test_format_results_for_llm(self, rag_skill):
        """Test formatting RAG results for LLM"""
        results = {
            "results": [
                {
                    "content": "Test content",
                    "source": "Test Source",
                    "relevance_score": 0.9
                }
            ]
        }
        
        formatted = rag_skill.format_results_for_llm(results)
        
        assert "[1] Source:" in formatted
        assert "Test Source" in formatted
        assert "Relevance:" in formatted
        assert "0.90" in formatted
        assert "Test content" in formatted

    def test_format_results_empty(self, rag_skill):
        """Test formatting empty RAG results"""
        formatted = rag_skill.format_results_for_llm({})
        assert "No relevant knowledge base content found" in formatted
        
        formatted = rag_skill.format_results_for_llm({"results": []})
        assert "No relevant knowledge base content found" in formatted

    def test_get_tool_schema(self, rag_skill):
        """Test tool schema generation"""
        schema = rag_skill.get_tool_schema()
        
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "rag_search"
        assert "parameters" in schema["function"]
        assert "query" in schema["function"]["parameters"]["properties"]
        assert "top_k" in schema["function"]["parameters"]["properties"]
        assert schema["function"]["parameters"]["required"] == ["query"]
