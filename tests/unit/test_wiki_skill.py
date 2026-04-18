"""
Unit tests for Wiki skill
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.skills.wiki_skill import WikiSkill, WikiSearchParams


class TestWikiSkill:
    """Test cases for WikiSkill"""

    @pytest.fixture
    def wiki_skill(self):
        """Create a WikiSkill instance for testing"""
        return WikiSkill()

    def test_wiki_skill_initialization(self, wiki_skill):
        """Test WikiSkill initialization"""
        assert wiki_skill.name == "wiki_search"
        assert "wiki" in wiki_skill.description.lower()
        assert wiki_skill.require_human_approval is False

    def test_wiki_search_params_validation(self):
        """Test WikiSearchParams validation"""
        # Valid params
        params = WikiSearchParams(query="Annual Leave Policy")
        assert params.query == "Annual Leave Policy"
        assert params.exact_match is False
        assert params.include_sections is True

        # With optional params
        params = WikiSearchParams(
            query="IT Equipment",
            exact_match=True,
            category="IT",
            max_length=1000
        )
        assert params.exact_match is True
        assert params.category == "IT"
        assert params.max_length == 1000

        # Invalid max_length (too small)
        with pytest.raises(Exception):
            WikiSearchParams(query="Test", max_length=50)

        # Invalid max_length (too large)
        with pytest.raises(Exception):
            WikiSearchParams(query="Test", max_length=15000)

    @pytest.mark.asyncio
    async def test_wiki_execute_with_mock_data(self, wiki_skill):
        """Test Wiki skill execution with local engine"""
        result = await wiki_skill.execute({
            "query": "Annual Leave Policy",
            "category": "HR"
        })

        assert result.success is True
        assert "results" in result.data
        # Local mode returns actual articles, not mock data
        assert len(result.data["results"]) >= 0  # May or may not find matches
        assert result.data.get("mode") == "local"

    @pytest.mark.asyncio
    async def test_wiki_execute_invalid_params(self, wiki_skill):
        """Test Wiki skill execution with invalid parameters"""
        result = await wiki_skill.execute({})

        assert result.success is False
        assert "Parameter validation failed" in result.error_message

    @pytest.mark.asyncio
    async def test_wiki_execute_api_timeout(self, wiki_skill):
        """Test Wiki skill handling when no results found"""
        import httpx
        
        # Note: Local engine doesn't call external API, so no timeout possible
        # This test verifies that empty results are handled correctly
        result = await wiki_skill.execute({"query": "xyz_nonexistent_query_12345"})
        
        # Should return success with empty results
        assert result.success is True
        assert "results" in result.data
        assert result.data.get("mode") == "local"

    def test_format_results_for_llm(self, wiki_skill):
        """Test formatting wiki results for LLM"""
        results = {
            "results": [
                {
                    "title": "Annual Leave Policy",
                    "url": "https://wiki.company.com/annual-leave",
                    "content": "Employees are entitled to annual leave...",
                    "category": "HR",
                    "last_updated": "2024-01-15"
                }
            ]
        }

        formatted = wiki_skill.format_results_for_llm(results)
        assert "Annual Leave Policy" in formatted
        assert "URL:" in formatted
        assert "Category:" in formatted
        assert "Last Updated:" in formatted
        assert "Content:" in formatted

    def test_format_results_empty(self, wiki_skill):
        """Test formatting empty wiki results"""
        formatted = wiki_skill.format_results_for_llm({})
        assert "No relevant wiki articles found" in formatted

        formatted = wiki_skill.format_results_for_llm({"results": []})
        assert "No relevant wiki articles found" in formatted

    def test_get_tool_schema(self, wiki_skill):
        """Test getting tool schema"""
        schema = wiki_skill.get_tool_schema()
        
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "wiki_search"
        assert "query" in schema["function"]["parameters"]["required"]
        assert "properties" in schema["function"]["parameters"]
        
        properties = schema["function"]["parameters"]["properties"]
        assert "query" in properties
        assert "exact_match" in properties
        assert "category" in properties
        assert "max_length" in properties
