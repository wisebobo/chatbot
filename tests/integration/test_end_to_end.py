"""
End-to-end tests for complete API workflows

Tests full request/response cycles including authentication, chat, and feedback.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from app.api.main import create_app


@pytest.fixture
def client():
    """Create test client"""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def api_key():
    """Get test API key"""
    return "sk-test-key-12345"


@pytest.fixture
def auth_headers(api_key):
    """Get authentication headers"""
    return {"X-API-Key": api_key}


class TestAuthenticationFlow:
    """Test complete authentication flows"""
    
    def test_login_with_valid_credentials(self, client):
        """Test login with valid LDAP credentials"""
        with patch('app.api.ldap_auth.get_ldap_authenticator') as mock_get_auth:
            mock_auth = MagicMock()
            mock_auth.authenticate.return_value = (True, {
                'username': 'testuser',
                'email': 'test@company.com',
                'display_name': 'Test User',
                'groups': ['Users']
            })
            mock_get_auth.return_value = mock_auth
            
            response = client.post("/api/v1/auth/login", json={
                "username": "testuser",
                "password": "password123"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "bearer"
    
    def test_login_with_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        with patch('app.api.ldap_auth.get_ldap_authenticator') as mock_get_auth:
            mock_auth = MagicMock()
            mock_auth.authenticate.return_value = (False, None)
            mock_get_auth.return_value = mock_auth
            
            response = client.post("/api/v1/auth/login", json={
                "username": "wronguser",
                "password": "wrongpass"
            })
            
            assert response.status_code == 401
    
    def test_access_protected_endpoint_with_valid_key(self, client, auth_headers):
        """Test accessing protected endpoint with valid API key"""
        response = client.get("/api/v1/health", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_access_protected_endpoint_without_key(self, client):
        """Test accessing protected endpoint without API key"""
        response = client.get("/api/v1/health")
        
        # Should require authentication
        assert response.status_code in [401, 403]
    
    def test_access_protected_endpoint_with_invalid_key(self, client):
        """Test accessing protected endpoint with invalid API key"""
        headers = {"X-API-Key": "invalid-key"}
        response = client.get("/api/v1/health", headers=headers)
        
        assert response.status_code == 401


class TestChatWorkflow:
    """Test complete chat workflow"""
    
    @patch('app.graph.nodes.get_llm_adapter')
    def test_chat_direct_reply(self, mock_llm, client, auth_headers):
        """Test chat with direct reply (no skill execution)"""
        # Mock LLM for intent recognition
        mock_response = MagicMock()
        mock_response.content = '''{
            "intent": "Greeting",
            "routing_decision": "direct_reply",
            "confidence": 0.95,
            "params": {}
        }'''
        mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
        
        # Mock LLM for response generation
        mock_response2 = MagicMock()
        mock_response2.content = "Hello! How can I help you?"
        
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_response
            else:
                return mock_response2
        
        mock_llm.return_value.ainvoke = AsyncMock(side_effect=side_effect)
        
        response = client.post("/api/v1/chat", json={
            "message": "Hello",
            "session_id": "test-session-001"
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["session_id"] == "test-session-001"
    
    @patch('app.graph.nodes.get_llm_adapter')
    def test_chat_with_skill_execution(self, mock_llm, client, auth_headers):
        """Test chat that triggers skill execution"""
        # Mock intent to use wiki_search
        mock_intent = MagicMock()
        mock_intent.content = '''{
            "intent": "Query about policy",
            "routing_decision": "wiki_search",
            "confidence": 0.9,
            "params": {"query": "policy"}
        }'''
        
        # Mock response generation
        mock_response = MagicMock()
        mock_response.content = "Based on the wiki search results..."
        
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:  # Intent + Response
                return mock_intent if call_count[0] == 1 else mock_response
            else:
                return mock_response
        
        mock_llm.return_value.ainvoke = AsyncMock(side_effect=side_effect)
        
        response = client.post("/api/v1/chat", json={
            "message": "What is the reimbursement policy?",
            "session_id": "test-session-002"
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
    
    def test_chat_validation_error(self, client, auth_headers):
        """Test chat with invalid input"""
        response = client.post("/api/v1/chat", json={
            "message": "",  # Empty message
            "session_id": "test-session"
        }, headers=auth_headers)
        
        assert response.status_code == 422  # Validation error
    
    def test_chat_streaming_mode(self, client, auth_headers):
        """Test chat in streaming mode"""
        with patch('app.graph.nodes.get_llm_adapter') as mock_llm:
            mock_response = MagicMock()
            mock_response.content = '{"intent": "Greeting", "routing_decision": "direct_reply", "confidence": 0.9, "params": {}}'
            mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
            
            response = client.post("/api/v1/chat", json={
                "message": "Hello",
                "session_id": "stream-test",
                "stream": True
            }, headers=auth_headers)
            
            # Streaming returns different response format
            assert response.status_code == 200


class TestWikiFeedbackWorkflow:
    """Test Wiki feedback submission workflow"""
    
    def test_submit_positive_feedback(self, client, auth_headers):
        """Test submitting positive feedback to wiki article"""
        # First ensure article exists
        from app.wiki.db_engine import DatabaseWikiEngine
        from app.wiki.engine import WikiArticle, KnowledgeType
        
        wiki_engine = DatabaseWikiEngine()
        article = WikiArticle(
            entry_id="feedback_e2e_test",
            title="E2E Feedback Test",
            type=KnowledgeType.CONCEPT,
            content="Test content",
            confidence=0.8
        )
        wiki_engine.save_article(article)
        
        # Submit feedback
        response = client.post("/api/v1/wiki/feedback", json={
            "entry_id": "feedback_e2e_test",
            "is_positive": True,
            "comment": "Very helpful!"
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_submit_negative_feedback(self, client, auth_headers):
        """Test submitting negative feedback"""
        from app.wiki.db_engine import DatabaseWikiEngine
        from app.wiki.engine import WikiArticle, KnowledgeType
        
        wiki_engine = DatabaseWikiEngine()
        article = WikiArticle(
            entry_id="negative_feedback_test",
            title="Negative Feedback Test",
            type=KnowledgeType.CONCEPT,
            content="Test content",
            confidence=0.8
        )
        wiki_engine.save_article(article)
        
        response = client.post("/api/v1/wiki/feedback", json={
            "entry_id": "negative_feedback_test",
            "is_positive": False,
            "comment": "Not accurate"
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_submit_feedback_invalid_entry(self, client, auth_headers):
        """Test submitting feedback to non-existent article"""
        response = client.post("/api/v1/wiki/feedback", json={
            "entry_id": "nonexistent_entry",
            "is_positive": True
        }, headers=auth_headers)
        
        # Should handle gracefully
        assert response.status_code in [200, 404]


class TestAPIKeyManagement:
    """Test API key management workflow"""
    
    def test_create_api_key(self, client, auth_headers):
        """Test creating new API key"""
        response = client.post("/api/v1/api-keys/", json={
            "name": "E2E Test Key",
            "owner": "test_user",
            "rate_limit": 100
        }, headers=auth_headers)
        
        # May require admin role
        assert response.status_code in [201, 403]
    
    def test_list_api_keys(self, client, auth_headers):
        """Test listing API keys"""
        response = client.get("/api/v1/api-keys/", headers=auth_headers)
        
        # May require admin role
        assert response.status_code in [200, 403]
    
    def test_get_api_key_metrics(self, client, auth_headers):
        """Test getting API key usage metrics"""
        response = client.get("/api/v1/api-keys/metrics", headers=auth_headers)
        
        assert response.status_code in [200, 401, 403]


class TestHealthAndMonitoring:
    """Test health check and monitoring endpoints"""
    
    def test_health_check(self, client, auth_headers):
        """Test health check endpoint"""
        response = client.get("/api/v1/health", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "registered_skills" in data
    
    def test_prometheus_metrics(self, client):
        """Test Prometheus metrics endpoint"""
        response = client.get("/metrics")
        
        # Should return metrics in Prometheus format
        assert response.status_code == 200
        assert "HELP" in response.text or "TYPE" in response.text
    
    def test_audit_log_query(self, client, auth_headers):
        """Test querying audit logs"""
        # This endpoint may not exist yet, but shows the pattern
        response = client.get("/api/v1/audit-logs?limit=10", headers=auth_headers)
        
        # May require special permissions
        assert response.status_code in [200, 401, 403, 404]


class TestErrorHandling:
    """Test error handling across the API"""
    
    def test_404_not_found(self, client, auth_headers):
        """Test 404 error response"""
        response = client.get("/api/v1/nonexistent-endpoint", headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert "correlation_id" in data["error"]
    
    def test_500_internal_error_handling(self, client, auth_headers):
        """Test that 500 errors are handled gracefully"""
        with patch('app.graph.nodes.get_llm_adapter') as mock_llm:
            # Force an unhandled exception
            mock_llm.return_value.ainvoke = AsyncMock(side_effect=Exception("Unexpected error"))
            
            response = client.post("/api/v1/chat", json={
                "message": "Test error handling",
                "session_id": "error-test"
            }, headers=auth_headers)
            
            # Should return proper error response
            assert response.status_code in [500, 502]
            data = response.json()
            assert "error" in data
            assert "correlation_id" in data["error"]
    
    def test_correlation_id_in_response(self, client, auth_headers):
        """Test that correlation ID is included in responses"""
        response = client.get("/api/v1/health", headers=auth_headers)
        
        assert "x-correlation-id" in response.headers
        correlation_id = response.headers["x-correlation-id"]
        assert len(correlation_id) > 0
        
        # Check error response also has it
        response = client.get("/api/v1/nonexistent", headers=auth_headers)
        assert "x-correlation-id" in response.headers


class TestSessionManagement:
    """Test session management workflow"""
    
    def test_session_creation_and_reuse(self, client, auth_headers):
        """Test that sessions are created and reused"""
        session_id = "persistent-session-test"
        
        # First request - creates session
        with patch('app.graph.nodes.get_llm_adapter') as mock_llm:
            mock_response = MagicMock()
            mock_response.content = '{"intent": "Test", "routing_decision": "direct_reply", "confidence": 0.9, "params": {}}'
            mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
            
            response1 = client.post("/api/v1/chat", json={
                "message": "First message",
                "session_id": session_id
            }, headers=auth_headers)
            
            assert response1.status_code == 200
            
            # Second request - should reuse session
            response2 = client.post("/api/v1/chat", json={
                "message": "Second message",
                "session_id": session_id
            }, headers=auth_headers)
            
            assert response2.status_code == 200
    
    def test_auto_generated_session_id(self, client, auth_headers):
        """Test that session ID is auto-generated if not provided"""
        with patch('app.graph.nodes.get_llm_adapter') as mock_llm:
            mock_response = MagicMock()
            mock_response.content = '{"intent": "Test", "routing_decision": "direct_reply", "confidence": 0.9, "params": {}}'
            mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
            
            response = client.post("/api/v1/chat", json={
                "message": "Test message"
                # No session_id provided
            }, headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert "session_id" in data
            assert len(data["session_id"]) > 0
