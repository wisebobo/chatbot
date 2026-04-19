# Testing Guide

## 📋 Overview

The Enterprise Agent Platform includes a comprehensive test suite with **80%+ code coverage** across unit, integration, and end-to-end tests.

## 🏗️ Test Structure

```
tests/
├── conftest.py                    # Pytest configuration and fixtures
├── unit/                          # Unit tests (fast, isolated)
│   ├── test_graph_nodes.py        # LangGraph workflow nodes
│   ├── test_rag_skill.py          # RAG skill unit tests
│   ├── test_wiki_skill.py         # Wiki skill unit tests
│   ├── test_skills.py             # Base skill tests
│   └── test_state.py              # Agent state tests
└── integration/                   # Integration tests (slower, real dependencies)
    ├── test_ldap_auth.py          # LDAP authentication
    ├── test_rag_wiki_fallback.py  # RAG/Wiki fallback mechanisms
    ├── test_database_transactions.py  # Database operations
    ├── test_rate_limit_and_load.py    # Rate limiting & performance
    └── test_end_to_end.py         # Full API workflows
```

## 🎯 Test Categories

### 1. Unit Tests

**Purpose:** Test individual components in isolation  
**Location:** `tests/unit/`  
**Speed:** Fast (< 1 second per test)  
**Dependencies:** Mocked

**What's Tested:**
- ✅ LangGraph workflow nodes (intent recognition, skill execution, response generation)
- ✅ Skill implementations (RAG, Wiki, Control-M, Playwright)
- ✅ Agent state management
- ✅ Utility functions

**Run Command:**
```bash
python scripts/run_tests.py unit
```

### 2. Integration Tests

**Purpose:** Test component interactions with real dependencies  
**Location:** `tests/integration/`  
**Speed:** Moderate (1-5 seconds per test)  
**Dependencies:** Real databases, mocked external APIs

**What's Tested:**
- ✅ LDAP authentication flow
- ✅ RAG/Wiki fallback mechanisms
- ✅ Database transactions and repositories
- ✅ Rate limiting under load
- ✅ Circuit breaker behavior

**Run Command:**
```bash
python scripts/run_tests.py integration
```

### 3. End-to-End Tests

**Purpose:** Test complete user workflows through the API  
**Location:** `tests/integration/test_end_to_end.py`  
**Speed:** Slow (5-10 seconds per test)  
**Dependencies:** Full application stack

**What's Tested:**
- ✅ Authentication flows (login, token validation)
- ✅ Complete chat workflows
- ✅ Wiki feedback submission
- ✅ API key management
- ✅ Error handling and correlation IDs
- ✅ Session management

**Run Command:**
```bash
python scripts/run_tests.py e2e
```

### 4. Load Tests

**Purpose:** Test system behavior under high load  
**Location:** `tests/integration/test_rate_limit_and_load.py`  
**Speed:** Very slow (30+ seconds)  
**Dependencies:** Real application with monitoring

**What's Tested:**
- ✅ Rate limiting enforcement
- ✅ Concurrent session handling
- ✅ Memory usage under load
- ✅ Response time percentiles (P95, P99)
- ✅ Circuit breaker under failure storms

**Run Command:**
```bash
python scripts/run_tests.py load
```

## 🚀 Quick Start

### Run All Tests

```bash
# Run complete test suite
python scripts/run_tests.py all

# Or use pytest directly
pytest tests/ -v
```

### Run Specific Test Suite

```bash
# Unit tests only
python scripts/run_tests.py unit

# Integration tests only
python scripts/run_tests.py integration

# End-to-end tests only
python scripts/run_tests.py e2e
```

### Run with Coverage Report

```bash
python scripts/run_tests.py coverage
```

This generates:
- **Terminal report** - Shows missing lines
- **HTML report** - `htmlcov/index.html` (open in browser)
- **XML report** - `coverage.xml` (for CI/CD)

**Coverage Requirement:** 80% minimum

## 📊 Current Coverage

| Component | Coverage | Status |
|-----------|----------|--------|
| Graph Nodes | 85% | ✅ |
| Skills (RAG, Wiki) | 90% | ✅ |
| Database Repositories | 95% | ✅ |
| Authentication | 88% | ✅ |
| API Routes | 82% | ✅ |
| **Overall** | **87%** | ✅ |

## 🔧 Writing Tests

### Unit Test Example

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_intent_recognition():
    """Test intent recognition node"""
    from app.graph.nodes import intent_recognition_node
    from app.state.agent_state import AgentState
    
    state = AgentState(
        user_input="What is the policy?",
        session_id="test-session",
        user_id="test-user"
    )
    
    # Mock LLM
    with patch('app.graph.nodes.get_llm_adapter') as mock_llm:
        mock_response = MagicMock()
        mock_response.content = '{"routing_decision": "wiki_search"}'
        mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
        
        result = await intent_recognition_node(state)
        
        assert result["routing_decision"] == "wiki_search"
```

### Integration Test Example

```python
import pytest
from fastapi.testclient import TestClient

def test_login_endpoint():
    """Test login through API"""
    from app.api.main import create_app
    
    app = create_app()
    client = TestClient(app)
    
    with patch('app.api.ldap_auth.get_ldap_authenticator') as mock_auth:
        mock_auth.return_value.authenticate.return_value = (True, {
            'username': 'testuser',
            'email': 'test@company.com'
        })
        
        response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "password123"
        })
        
        assert response.status_code == 200
        assert "access_token" in response.json()
```

### Test Markers

Use markers to categorize tests:

```python
@pytest.mark.slow      # Takes > 5 seconds
@pytest.mark.integration  # Requires external services
@pytest.mark.e2e       # End-to-end workflow
@pytest.mark.load      # Performance/load test
```

Run specific markers:
```bash
pytest -m "not slow"           # Skip slow tests
pytest -m "integration"        # Only integration tests
pytest -m "not load"           # Skip load tests
```

## 🐛 Debugging Tests

### Verbose Output

```bash
pytest tests/ -v --tb=long
```

### Show Print Statements

```bash
pytest tests/ -s
```

### Run Single Test

```bash
pytest tests/unit/test_graph_nodes.py::test_intent_recognition_cache_hit -v
```

### Stop on First Failure

```bash
pytest tests/ -x
```

### Parallel Execution

```bash
pip install pytest-xdist
pytest tests/ -n auto  # Use all CPU cores
```

## 📈 Continuous Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run tests with coverage
        run: python scripts/run_tests.py coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## 🎯 Test Best Practices

### 1. Naming Conventions

```python
# Good
def test_intent_recognition_with_cache_hit():
    pass

def test_login_with_invalid_credentials_returns_401():
    pass

# Bad
def test1():
    pass

def test_stuff():
    pass
```

### 2. Arrange-Act-Assert Pattern

```python
def test_wiki_search():
    # Arrange
    wiki_engine = DatabaseWikiEngine()
    article = WikiArticle(entry_id="test", title="Test", ...)
    wiki_engine.save_article(article)
    
    # Act
    results = wiki_engine.search_articles("test")
    
    # Assert
    assert len(results) == 1
    assert results[0].title == "Test"
```

### 3. Use Fixtures

```python
@pytest.fixture
def sample_article():
    return WikiArticle(
        entry_id="fixture_test",
        title="Fixture Test",
        type=KnowledgeType.CONCEPT,
        content="Test content"
    )

def test_save_article(sample_article):
    wiki_engine = DatabaseWikiEngine()
    wiki_engine.save_article(sample_article)
    
    retrieved = wiki_engine.get_article("fixture_test")
    assert retrieved is not None
```

### 4. Mock External Dependencies

```python
@patch('httpx.AsyncClient.post')
async def test_rag_api_call(mock_post):
    mock_post.return_value.json.return_value = {"results": []}
    
    skill = RagSkill()
    result = await skill.execute({"query": "test"})
    
    assert result.success is True
    mock_post.assert_called_once()
```

### 5. Test Edge Cases

```python
def test_empty_search_query():
    wiki_engine = DatabaseWikiEngine()
    results = wiki_engine.search_articles("")
    
    assert len(results) == 0

def test_search_with_special_characters():
    results = wiki_engine.search_articles("@#$%^&*")
    
    assert results is not None  # Should not crash
```

## 🔍 Common Issues

### Issue: Import Errors

**Solution:** Ensure project root is in Python path:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### Issue: Database Not Clean Between Tests

**Solution:** Use transaction rollback:
```python
@pytest.fixture
def session(db_manager):
    with db_manager.get_session() as session:
        yield session
        session.rollback()  # Cleanup
```

### Issue: Async Tests Not Running

**Solution:** Install pytest-asyncio:
```bash
pip install pytest-asyncio
```

Mark async tests:
```python
@pytest.mark.asyncio
async def test_async_function():
    pass
```

### Issue: Tests Too Slow

**Solution:** 
1. Use mocks instead of real services
2. Run tests in parallel: `pytest -n auto`
3. Skip slow tests: `pytest -m "not slow"`

## 📚 Related Documentation

- [Exception Handling Guide](EXCEPTION_HANDLING_GUIDE.md)
- [Database Configuration Guide](DATABASE_CONFIGURATION_GUIDE.md)
- [API Authentication Guide](API_AUTH_AND_RATE_LIMITING_GUIDE.md)

---

**Last Updated:** 2026-04-19  
**Test Count:** 50+ tests  
**Coverage:** 87%  
**Status:** ✅ Production Ready
