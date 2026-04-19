"""
Integration tests for LDAP authentication

Tests LDAP connection, user authentication, and group retrieval.
"""
import pytest
from unittest.mock import MagicMock, patch
from app.api.ldap_auth import LDAPAuthenticator, get_ldap_authenticator
from app.config.settings import get_settings


@pytest.fixture
def ldap_settings():
    """Get LDAP settings from configuration"""
    settings = get_settings()
    return settings.ldap


@pytest.fixture
def ldap_authenticator(ldap_settings):
    """Create LDAP authenticator for testing"""
    return LDAPAuthenticator(
        server_url=ldap_settings.server_url,
        base_dn=ldap_settings.base_dn,
        bind_dn=ldap_settings.bind_dn,
        bind_password=ldap_settings.bind_password,
        user_filter=ldap_settings.user_filter,
        use_ssl=ldap_settings.use_ssl
    )


def test_ldap_authenticator_initialization(ldap_authenticator):
    """Test LDAP authenticator initializes correctly"""
    assert ldap_authenticator is not None
    assert hasattr(ldap_authenticator, 'server')
    assert hasattr(ldap_authenticator, 'base_dn')


@patch('ldap3.Server')
@patch('ldap3.Connection')
def test_ldap_connection_success(mock_conn, mock_server, ldap_authenticator):
    """Test successful LDAP connection"""
    # Mock successful connection
    mock_conn_instance = MagicMock()
    mock_conn_instance.bind.return_value = True
    mock_conn.return_value = mock_conn_instance
    
    result = ldap_authenticator._connect()
    
    assert result is True
    mock_conn.assert_called_once()
    mock_conn_instance.bind.assert_called_once()


@patch('ldap3.Server')
@patch('ldap3.Connection')
def test_ldap_connection_failure(mock_conn, mock_server, ldap_authenticator):
    """Test LDAP connection failure"""
    # Mock failed connection
    mock_conn_instance = MagicMock()
    mock_conn_instance.bind.return_value = False
    mock_conn.return_value = mock_conn_instance
    
    result = ldap_authenticator._connect()
    
    assert result is False


@patch.object(LDAPAuthenticator, '_connect')
@patch('ldap3.Server')
@patch('ldap3.Connection')
def test_ldap_authentication_success(mock_conn, mock_server, mock_connect, ldap_authenticator):
    """Test successful user authentication"""
    mock_connect.return_value = True
    
    # Mock search results
    mock_entry = MagicMock()
    mock_entry.dn = "CN=John Doe,OU=Users,DC=company,DC=com"
    mock_entry.entry_attributes_as_dict = {
        'mail': ['john.doe@company.com'],
        'displayName': ['John Doe'],
        'memberOf': ['CN=Admins,OU=Groups,DC=company,DC=com']
    }
    
    mock_search_result = [mock_entry]
    
    mock_conn_instance = MagicMock()
    mock_conn_instance.search.return_value = True
    mock_conn_instance.entries = mock_search_result
    mock_conn.return_value = mock_conn_instance
    
    success, user_info = ldap_authenticator.authenticate("johndoe", "password123")
    
    assert success is True
    assert user_info is not None
    assert user_info['username'] == 'johndoe'
    assert 'email' in user_info
    assert 'groups' in user_info


@patch.object(LDAPAuthenticator, '_connect')
def test_ldap_authentication_invalid_credentials(mock_connect, ldap_authenticator):
    """Test authentication with invalid credentials"""
    mock_connect.return_value = False
    
    success, user_info = ldap_authenticator.authenticate("invaliduser", "wrongpassword")
    
    assert success is False
    assert user_info is None


@patch.object(LDAPAuthenticator, '_connect')
@patch('ldap3.Server')
@patch('ldap3.Connection')
def test_ldap_user_not_found(mock_conn, mock_server, mock_connect, ldap_authenticator):
    """Test authentication when user doesn't exist"""
    mock_connect.return_value = True
    
    # Mock empty search results
    mock_conn_instance = MagicMock()
    mock_conn_instance.search.return_value = True
    mock_conn_instance.entries = []
    mock_conn.return_value = mock_conn_instance
    
    success, user_info = ldap_authenticator.authenticate("nonexistent", "password")
    
    assert success is False
    assert user_info is None


def test_get_ldap_authenticator_singleton():
    """Test that get_ldap_authenticator returns singleton instance"""
    auth1 = get_ldap_authenticator()
    auth2 = get_ldap_authenticator()
    
    assert auth1 is auth2


@patch.object(LDAPAuthenticator, '_connect')
@patch('ldap3.Server')
@patch('ldap3.Connection')
def test_ldap_group_retrieval(mock_conn, mock_server, mock_connect, ldap_authenticator):
    """Test retrieving user groups from LDAP"""
    mock_connect.return_value = True
    
    # Mock user with multiple groups
    mock_entry = MagicMock()
    mock_entry.entry_attributes_as_dict = {
        'memberOf': [
            'CN=Admins,OU=Groups,DC=company,DC=com',
            'CN=Developers,OU=Groups,DC=company,DC=com',
            'CN=ProjectA,OU=Groups,DC=company,DC=com'
        ]
    }
    
    groups = ldap_authenticator._extract_groups([mock_entry])
    
    assert len(groups) == 3
    assert 'Admins' in groups
    assert 'Developers' in groups


@pytest.mark.asyncio
async def test_ldap_auth_route_integration():
    """Test LDAP authentication through API route"""
    from fastapi.testclient import TestClient
    from app.api.main import create_app
    
    app = create_app()
    client = TestClient(app)
    
    # Mock LDAP authentication
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


@pytest.mark.asyncio
async def test_ldap_auth_route_invalid_credentials():
    """Test login with invalid credentials"""
    from fastapi.testclient import TestClient
    from app.api.main import create_app
    
    app = create_app()
    client = TestClient(app)
    
    with patch('app.api.ldap_auth.get_ldap_authenticator') as mock_get_auth:
        mock_auth = MagicMock()
        mock_auth.authenticate.return_value = (False, None)
        mock_get_auth.return_value = mock_auth
        
        response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        assert "detail" in response.json()
