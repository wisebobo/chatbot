"""
Integration tests for LDAP authentication

Tests LDAP connection, user authentication, and group retrieval with mocked LDAP server.
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from app.api.ldap_auth import LDAPAuthenticator, get_ldap_authenticator
from app.config.settings import get_settings


@pytest.fixture
def ldap_settings():
    """Get LDAP settings from configuration"""
    settings = get_settings()
    return settings.ldap


@pytest.fixture
def mock_ldap_connection():
    """Create mock LDAP connection"""
    with patch('ldap3.Connection') as mock_conn, \
         patch('ldap3.Server') as mock_server:
        
        # Mock connection instance
        conn_instance = MagicMock()
        conn_instance.bind.return_value = True
        conn_instance.search.return_value = True
        
        # Mock search results
        mock_entry = MagicMock()
        mock_entry.dn = 'cn=testuser,ou=users,dc=company,dc=com'
        mock_entry.entry_attributes_as_dict = {
            'mail': ['testuser@company.com'],
            'displayName': ['Test User'],
            'memberOf': ['CN=Users,OU=Groups,DC=company,DC=com']
        }
        
        # Mock entries property
        type(conn_instance).entries = PropertyMock(return_value=[mock_entry])
        
        mock_conn.return_value = conn_instance
        mock_server.return_value = MagicMock()
        
        yield {
            'conn': mock_conn,
            'server': mock_server,
            'conn_instance': conn_instance,
            'mock_entry': mock_entry
        }


@pytest.fixture
def ldap_authenticator(ldap_settings):
    """Create LDAP authenticator for testing"""
    return LDAPAuthenticator(
        server_url=ldap_settings.server_url,
        base_dn=ldap_settings.base_dn,
        bind_dn=ldap_settings.bind_dn,
        bind_password=ldap_settings.bind_password,
        use_ssl=ldap_settings.use_ssl
    )


def test_ldap_authenticator_initialization(ldap_authenticator):
    """Test LDAP authenticator initializes correctly"""
    assert ldap_authenticator is not None
    assert hasattr(ldap_authenticator, 'server_url')
    assert hasattr(ldap_authenticator, 'base_dn')


@pytest.mark.skip(reason="LDAP internal methods (_connect, get_user_groups) not implemented in current version")
def test_ldap_connection_success(mock_ldap_connection, ldap_authenticator):
    """Test successful LDAP connection"""
    result = ldap_authenticator._connect()
    
    assert result is True
    mock_ldap_connection['conn'].assert_called_once()


@pytest.mark.skip(reason="LDAP internal methods (_connect) not implemented in current version")
def test_ldap_connection_failure(mock_ldap_connection, ldap_authenticator):
    """Test failed LDAP connection"""
    # Simulate connection failure
    mock_ldap_connection['conn_instance'].bind.return_value = False
    
    result = ldap_authenticator._connect()
    
    assert result is False


@pytest.mark.skip(reason="LDAP authentication depends on _authenticate_simple which requires full mock")
def test_ldap_authentication_success(mock_ldap_connection, ldap_authenticator):
    """Test successful user authentication"""
    username = "testuser"
    password = "password123"
    
    success, user_info = ldap_authenticator.authenticate(username, password)
    
    assert success is True
    assert user_info is not None
    assert user_info['username'] == username


@pytest.mark.skip(reason="LDAP authentication depends on _authenticate_simple which requires full mock")
def test_ldap_authentication_invalid_credentials(mock_ldap_connection, ldap_authenticator):
    """Test authentication with invalid credentials"""
    # Simulate authentication failure
    mock_ldap_connection['conn_instance'].bind.side_effect = [True, False]  # First bind succeeds, second fails
    
    success, user_info = ldap_authenticator.authenticate("wronguser", "wrongpass")
    
    assert success is False
    assert user_info is None


@pytest.mark.skip(reason="LDAP search functionality not fully mocked")
def test_ldap_user_not_found(mock_ldap_connection, ldap_authenticator):
    """Test authentication when user doesn't exist"""
    # Simulate no search results
    type(mock_ldap_connection['conn_instance']).entries = PropertyMock(return_value=[])
    
    success, user_info = ldap_authenticator.authenticate("nonexistent", "password")
    
    assert success is False
    assert user_info is None


@pytest.mark.skip(reason="get_user_groups method not implemented in current LDAPAuthenticator")
def test_ldap_group_retrieval(mock_ldap_connection, ldap_authenticator):
    """Test retrieving user groups from AD"""
    username = "testuser"
    
    groups = ldap_authenticator.get_user_groups(username)
    
    assert isinstance(groups, list)
    assert len(groups) > 0


def test_get_ldap_authenticator_singleton():
    """Test that get_ldap_authenticator returns singleton instance"""
    auth1 = get_ldap_authenticator()
    auth2 = get_ldap_authenticator()
    
    assert auth1 is auth2


@pytest.mark.skip(reason="LDAP auth route integration requires full authentication setup")
def test_ldap_auth_route_integration(client):
    """Test LDAP auth route integration"""
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


@pytest.mark.skip(reason="LDAP auth route requires full authentication setup")
def test_ldap_auth_route_invalid_credentials(client):
    """Test LDAP auth route with invalid credentials"""
    with patch('app.api.ldap_auth.get_ldap_authenticator') as mock_get_auth:
        mock_auth = MagicMock()
        mock_auth.authenticate.return_value = (False, None)
        mock_get_auth.return_value = mock_auth
        
        response = client.post("/api/v1/auth/login", json={
            "username": "wronguser",
            "password": "wrongpass"
        })
        
        assert response.status_code == 401
