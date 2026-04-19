"""
LDAP Authentication Module
Provides Active Directory authentication via LDAP protocol
"""
import logging
import os
from typing import Optional, Tuple
from ldap3 import Server, Connection, ALL, NTLM, SIMPLE
from ldap3.core.exceptions import LDAPException, LDAPBindError

logger = logging.getLogger(__name__)


class LDAPAuthenticator:
    """
    LDAP Authenticator for Active Directory integration
    
    Supports both simple bind and NTLM authentication methods.
    """
    
    def __init__(
        self,
        server_url: str,
        base_dn: str,
        domain: Optional[str] = None,
        use_ssl: bool = True,
        auth_method: str = "simple",
        bind_dn: Optional[str] = None,
        bind_password: Optional[str] = None,
    ):
        """
        Initialize LDAP authenticator
        
        Args:
            server_url: LDAP server URL (e.g., ldap://ad.company.com or ldaps://ad.company.com)
            base_dn: Base DN for user search (e.g., DC=company,DC=com)
            domain: AD domain name (e.g., COMPANY)
            use_ssl: Use SSL/TLS connection
            auth_method: Authentication method ('simple' or 'ntlm')
            bind_dn: Service account DN for searching users (optional)
            bind_password: Service account password (optional)
        """
        self.server_url = server_url
        self.base_dn = base_dn
        self.domain = domain
        self.use_ssl = use_ssl
        self.auth_method = auth_method
        self.bind_dn = bind_dn
        self.bind_password = bind_password
        
        # Initialize LDAP server
        try:
            self.server = Server(
                self.server_url,
                use_ssl=self.use_ssl,
                get_info=ALL
            )
            logger.info(f"LDAP server initialized: {self.server_url}")
        except Exception as e:
            logger.error(f"Failed to initialize LDAP server: {e}")
            raise
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[dict]]:
        """
        Authenticate user against Active Directory
        
        Args:
            username: User's username or sAMAccountName
            password: User's password
            
        Returns:
            Tuple of (success: bool, user_info: dict or None)
        """
        try:
            if self.auth_method == "ntlm":
                return self._authenticate_ntlm(username, password)
            else:
                return self._authenticate_simple(username, password)
                
        except LDAPBindError as e:
            logger.warning(f"LDAP bind failed for user '{username}': {str(e)}")
            return False, None
        except LDAPException as e:
            logger.error(f"LDAP error during authentication: {str(e)}")
            return False, None
        except Exception as e:
            logger.error(f"Unexpected error during LDAP authentication: {str(e)}", exc_info=True)
            return False, None
    
    def _authenticate_simple(self, username: str, password: str) -> Tuple[bool, Optional[dict]]:
        """
        Authenticate using simple bind method
        
        This method constructs the user's DN and attempts to bind directly.
        """
        # Construct user DN
        # Common patterns: CN=username,OU=Users,DC=company,DC=com
        # or: uid=username,OU=Users,DC=company,DC=com
        user_dn = self._build_user_dn(username)
        
        logger.debug(f"Attempting simple bind with DN: {user_dn}")
        
        try:
            # Attempt to bind with user credentials
            conn = Connection(
                self.server,
                user=user_dn,
                password=password,
                auto_bind=True
            )
            
            # If bind succeeds, retrieve user information
            user_info = self._get_user_info(conn, username)
            conn.unbind()
            
            logger.info(f"User '{username}' authenticated successfully via simple bind")
            return True, user_info
            
        except LDAPBindError:
            logger.warning(f"Authentication failed for user '{username}'")
            return False, None
    
    def _authenticate_ntlm(self, username: str, password: str) -> Tuple[bool, Optional[dict]]:
        """
        Authenticate using NTLM method (Windows AD standard)
        
        This method uses domain\\username format for authentication.
        """
        if not self.domain:
            logger.error("Domain is required for NTLM authentication")
            return False, None
        
        # Format username as DOMAIN\username
        ntlm_username = f"{self.domain}\\{username}"
        
        logger.debug(f"Attempting NTLM authentication for: {ntlm_username}")
        
        try:
            # For NTLM, we may need a service account to search first
            if self.bind_dn and self.bind_password:
                # Bind with service account first
                search_conn = Connection(
                    self.server,
                    user=self.bind_dn,
                    password=self.bind_password,
                    authentication=NTLM,
                    auto_bind=True
                )
                
                # Search for user
                user_info = self._search_user(search_conn, username)
                search_conn.unbind()
                
                if not user_info:
                    logger.warning(f"User '{username}' not found in AD")
                    return False, None
                
                # Now authenticate with user credentials
                user_conn = Connection(
                    self.server,
                    user=ntlm_username,
                    password=password,
                    authentication=NTLM,
                    auto_bind=True
                )
                user_conn.unbind()
                
                logger.info(f"User '{username}' authenticated successfully via NTLM")
                return True, user_info
            else:
                # Direct NTLM bind without service account
                conn = Connection(
                    self.server,
                    user=ntlm_username,
                    password=password,
                    authentication=NTLM,
                    auto_bind=True
                )
                
                # Get user info (limited without search)
                user_info = {
                    "username": username,
                    "domain": self.domain,
                    "dn": ntlm_username
                }
                conn.unbind()
                
                logger.info(f"User '{username}' authenticated successfully via NTLM")
                return True, user_info
                
        except LDAPBindError:
            logger.warning(f"NTLM authentication failed for user '{username}'")
            return False, None
    
    def _build_user_dn(self, username: str) -> str:
        """
        Build user DN from username
        
        Override this method to match your AD structure.
        Common patterns:
        - CN={username},OU=Users,{base_dn}
        - uid={username},OU=Users,{base_dn}
        - {username}@{domain}
        """
        # Default pattern - adjust based on your AD structure
        return f"CN={username},OU=Users,{self.base_dn}"
    
    def _search_user(self, conn: Connection, username: str) -> Optional[dict]:
        """
        Search for user in Active Directory
        
        Args:
            conn: LDAP connection (should be bound with service account)
            username: Username to search for
            
        Returns:
            User information dictionary or None
        """
        try:
            # Search filter for sAMAccountName
            search_filter = f"(sAMAccountName={username})"
            
            conn.search(
                search_base=self.base_dn,
                search_filter=search_filter,
                attributes=['cn', 'mail', 'displayName', 'memberOf', 'sAMAccountName']
            )
            
            if len(conn.entries) == 0:
                return None
            
            entry = conn.entries[0]
            user_info = {
                "username": str(entry.sAMAccountName.value) if hasattr(entry, 'sAMAccountName') else username,
                "common_name": str(entry.cn.value) if hasattr(entry, 'cn') else username,
                "email": str(entry.mail.value) if hasattr(entry, 'mail') else None,
                "display_name": str(entry.displayName.value) if hasattr(entry, 'displayName') else username,
                "dn": str(entry.entry_dn),
                "groups": [str(g) for g in entry.memberOf.values] if hasattr(entry, 'memberOf') else []
            }
            
            return user_info
            
        except Exception as e:
            logger.error(f"Error searching for user '{username}': {str(e)}")
            return None
    
    def _get_user_info(self, conn: Connection, username: str) -> dict:
        """
        Retrieve user information after successful authentication
        
        Args:
            conn: LDAP connection (already bound with user credentials)
            username: Username
            
        Returns:
            User information dictionary
        """
        try:
            # Search for current user's details
            search_filter = f"(sAMAccountName={username})"
            
            conn.search(
                search_base=self.base_dn,
                search_filter=search_filter,
                attributes=['cn', 'mail', 'displayName', 'memberOf', 'sAMAccountName']
            )
            
            if len(conn.entries) > 0:
                entry = conn.entries[0]
                return {
                    "username": str(entry.sAMAccountName.value) if hasattr(entry, 'sAMAccountName') else username,
                    "common_name": str(entry.cn.value) if hasattr(entry, 'cn') else username,
                    "email": str(entry.mail.value) if hasattr(entry, 'mail') else None,
                    "display_name": str(entry.displayName.value) if hasattr(entry, 'displayName') else username,
                    "dn": str(entry.entry_dn),
                    "groups": [str(g) for g in entry.memberOf.values] if hasattr(entry, 'memberOf') else []
                }
            
            # Fallback if search fails
            return {
                "username": username,
                "dn": self._build_user_dn(username)
            }
            
        except Exception as e:
            logger.warning(f"Could not retrieve user info for '{username}': {str(e)}")
            return {
                "username": username,
                "dn": self._build_user_dn(username)
            }
    
    def test_connection(self) -> bool:
        """
        Test LDAP server connectivity
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            test_conn = Connection(
                self.server,
                auto_bind=False
            )
            result = test_conn.bind()
            test_conn.unbind()
            return result
        except Exception as e:
            logger.error(f"LDAP connection test failed: {str(e)}")
            return False


def create_ldap_authenticator() -> LDAPAuthenticator:
    """
    Factory function to create LDAP authenticator from environment variables
    
    Expected environment variables:
    - LDAP_SERVER_URL: LDAP server URL
    - LDAP_BASE_DN: Base DN for searches
    - LDAP_DOMAIN: AD domain name (for NTLM)
    - LDAP_USE_SSL: Use SSL (true/false)
    - LDAP_AUTH_METHOD: Authentication method (simple/ntlm)
    - LDAP_BIND_DN: Service account DN (optional)
    - LDAP_BIND_PASSWORD: Service account password (optional)
    """
    server_url = os.getenv("LDAP_SERVER_URL", "ldap://ad.company.com")
    base_dn = os.getenv("LDAP_BASE_DN", "DC=company,DC=com")
    domain = os.getenv("LDAP_DOMAIN")
    use_ssl = os.getenv("LDAP_USE_SSL", "true").lower() == "true"
    auth_method = os.getenv("LDAP_AUTH_METHOD", "ntlm")
    bind_dn = os.getenv("LDAP_BIND_DN")
    bind_password = os.getenv("LDAP_BIND_PASSWORD")
    
    return LDAPAuthenticator(
        server_url=server_url,
        base_dn=base_dn,
        domain=domain,
        use_ssl=use_ssl,
        auth_method=auth_method,
        bind_dn=bind_dn,
        bind_password=bind_password,
    )


# Global LDAP authenticator instance (lazy initialization)
_ldap_authenticator: Optional[LDAPAuthenticator] = None


def get_ldap_authenticator() -> LDAPAuthenticator:
    """Get or create LDAP authenticator instance"""
    global _ldap_authenticator
    if _ldap_authenticator is None:
        _ldap_authenticator = create_ldap_authenticator()
    return _ldap_authenticator
