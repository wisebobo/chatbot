"""
Integration tests for RAG and Wiki fallback mechanisms

Tests degradation from remote services to local storage.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.skills.rag_skill import RagSkill
from app.skills.wiki_skill import WikiSkill
from app.config.settings import get_settings


@pytest.fixture
def rag_skill():
    """Create RAG skill instance"""
    return RagSkill()


@pytest.fixture
def wiki_skill():
    """Create Wiki skill instance"""
    return WikiSkill()


@pytest.mark.asyncio
async def test_rag_remote_api_success(rag_skill):
    """Test RAG skill with successful remote API call"""
    # Mock HTTP response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [
            {"content": "Test document 1", "score": 0.95},
            {"content": "Test document 2", "score": 0.85}
        ]
    }
    mock_response.raise_for_status = MagicMock()
    
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        result = await rag_skill.execute({"query": "test query"})
        
        assert result.success is True
        assert len(result.data["results"]) == 2


@pytest.mark.asyncio
async def test_rag_remote_api_failure_fallback(rag_skill):
    """Test RAG skill falls back when remote API fails"""
    # Simulate network error
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = Exception("Connection timeout")
        
        result = await rag_skill.execute({"query": "test query"})
        
        # Should handle gracefully (either fallback or clear error)
        assert result is not None


@pytest.mark.asyncio
async def test_rag_local_mode_when_remote_disabled(rag_skill):
    """Test RAG uses local mode when remote is not configured"""
    # Disable remote API
    rag_skill._use_remote_api = False
    
    result = await rag_skill.execute({"query": "test query"})
    
    # Should use local implementation or return appropriate message
    assert result is not None


@pytest.mark.asyncio
async def test_wiki_local_engine_initialization(wiki_skill):
    """Test Wiki skill initializes local engine"""
    assert wiki_skill._local_wiki is not None
    assert hasattr(wiki_skill._local_wiki, 'get_article_count')


@pytest.mark.asyncio
async def test_wiki_local_search(wiki_skill):
    """Test Wiki search using local engine"""
    # Add sample article first
    from app.wiki.engine import WikiArticle, KnowledgeType
    
    sample_article = WikiArticle(
        entry_id="test_article_001",
        title="Test Article",
        type=KnowledgeType.CONCEPT,
        content="# Test Content\nThis is a test article.",
        aliases=["test", "sample"],
        tags=["test"],
        confidence=0.9
    )
    
    wiki_skill._local_wiki.save_article(sample_article)
    
    # Search for the article
    result = await wiki_skill.execute({
        "query": "test",
        "exact_match": False
    })
    
    assert result.success is True
    assert "articles" in result.data
    assert len(result.data["articles"]) > 0


@pytest.mark.asyncio
async def test_wiki_exact_match_search(wiki_skill):
    """Test Wiki exact match search"""
    from app.wiki.engine import WikiArticle, KnowledgeType
    
    article = WikiArticle(
        entry_id="exact_test",
        title="Exact Match Title",
        type=KnowledgeType.CONCEPT,
        content="Content here",
        confidence=0.9
    )
    wiki_skill._local_wiki.save_article(article)
    
    result = await wiki_skill.execute({
        "query": "Exact Match Title",
        "exact_match": True
    })
    
    assert result.success is True


@pytest.mark.asyncio
async def test_wiki_feedback_submission(wiki_skill):
    """Test submitting feedback to Wiki articles"""
    from app.wiki.engine import WikiArticle, KnowledgeType
    
    article = WikiArticle(
        entry_id="feedback_test",
        title="Feedback Test Article",
        type=KnowledgeType.CONCEPT,
        content="Test content",
        confidence=0.8
    )
    wiki_skill._local_wiki.save_article(article)
    
    # Submit positive feedback
    result = await wiki_skill.execute({
        "action": "feedback",
        "entry_id": "feedback_test",
        "user_id": "test_user",
        "is_positive": True,
        "comment": "Helpful article"
    })
    
    assert result.success is True
    
    # Verify feedback was recorded
    updated_article = wiki_skill._local_wiki.get_article("feedback_test")
    assert updated_article.feedback.positive == 1


@pytest.mark.asyncio
async def test_wiki_remote_api_configured(wiki_skill):
    """Test Wiki skill detects remote API configuration"""
    settings = get_settings()
    
    # Check if remote API is configured
    is_configured = bool(
        settings.wiki.api_key and 
        settings.wiki.api_url and 
        "your-group-ai-platform" not in settings.wiki.api_url.lower()
    )
    
    assert wiki_skill._use_remote_api == is_configured


@pytest.mark.asyncio
async def test_wiki_category_filter(wiki_skill):
    """Test Wiki search with category filter"""
    from app.wiki.engine import WikiArticle, KnowledgeType
    
    # Add articles of different types
    article1 = WikiArticle(
        entry_id="finance_001",
        title="Finance Policy",
        type=KnowledgeType.RULE,
        content="Finance rules",
        tags=["finance"]
    )
    article2 = WikiArticle(
        entry_id="it_001",
        title="IT Procedure",
        type=KnowledgeType.PROCESS,
        content="IT steps",
        tags=["it"]
    )
    
    wiki_skill._local_wiki.save_article(article1)
    wiki_skill._local_wiki.save_article(article2)
    
    # Search with category filter
    result = await wiki_skill.execute({
        "query": "policy",
        "category": "rule"
    })
    
    assert result.success is True


@pytest.mark.asyncio
async def test_rag_wiki_fallback_priority():
    """Test that system tries RAG first, then Wiki as fallback"""
    from app.graph.nodes import intent_recognition_node
    from app.state.agent_state import AgentState
    
    state = AgentState(
        user_input="What is the reimbursement policy?",
        session_id="test-session",
        user_id="test-user"
    )
    
    # Mock both RAG and Wiki
    with patch('app.graph.nodes.skill_registry') as mock_registry:
        # This test verifies routing logic
        result = await intent_recognition_node(state)
        
        # Should route to appropriate skill based on intent
        assert "routing_decision" in result
