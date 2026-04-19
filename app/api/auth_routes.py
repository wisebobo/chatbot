"""
Authentication API Routes
Provides LDAP-based authentication and JWT token management
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import Optional
from pydantic import BaseModel
from jwt import InvalidTokenError

from app.api.jwt_auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    Token,
)
from app.api.ldap_auth import get_ldap_authenticator, LDAPAuthenticator
from app.monitoring.metrics import (
    auth_failures,
    user_logins,
    jwt_tokens_issued,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


class UserLogin(BaseModel):
    """User login request model"""
    username: str
    password: str


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """
    Authenticate user against Active Directory via LDAP
    
    Validates username and password against AD, then issues JWT tokens for authenticated session.
    
    Args:
        credentials: Login credentials (username, password)
        
    Returns:
        JWT access and refresh tokens
        
    Raises:
        HTTPException: 401 if credentials are invalid
    """
    try:
        # Get LDAP authenticator
        ldap_auth = get_ldap_authenticator()
        
        # Authenticate against Active Directory
        success, user_info = ldap_auth.authenticate(credentials.username, credentials.password)
        
        if not success or not user_info:
            # Track failed login
            auth_failures.labels(endpoint="/auth/login", reason="invalid_credentials").inc()
            user_logins.labels(status="failure").inc()
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Track successful login
        user_logins.labels(status="success").inc()
        
        logger.info(f"User logged in via LDAP: {credentials.username}")
        
        # Determine user role based on AD groups
        # You can customize this logic based on your AD group structure
        role = _determine_role_from_groups(user_info.get("groups", []))
        
        # Generate JWT tokens with user information from AD
        token_data = {
            "user_id": user_info.get("username", credentials.username),
            "username": credentials.username,
            "email": user_info.get("email", ""),
            "display_name": user_info.get("display_name", credentials.username),
            "role": role,
            "dn": user_info.get("dn", "")
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        # Track token issuance
        jwt_tokens_issued.labels(token_type="access").inc()
        jwt_tokens_issued.labels(token_type="refresh").inc()
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=1800  # 30 minutes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service unavailable"
        )


def _determine_role_from_groups(groups: list[str]) -> str:
    """
    Determine user role based on Active Directory group membership
    
    Customize this function based on your AD group structure.
    
    Args:
        groups: List of AD group DNs the user belongs to
        
    Returns:
        Role string ('admin' or 'user')
    """
    # Example: Check if user is in admin groups
    admin_group_keywords = ["Admins", "Administrators", "IT-Admin"]
    
    for group in groups:
        if any(keyword.lower() in group.lower() for keyword in admin_group_keywords):
            return "admin"
    
    # Default role
    return "user"


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """
    Refresh access token using refresh token
    
    Validates the refresh token and issues a new access token.
    
    Args:
        refresh_token: Valid refresh token (query parameter or form data)
        
    Returns:
        New JWT access and refresh tokens
        
    Raises:
        HTTPException: 401 if refresh token is invalid or expired
    """
    try:
        # Decode and validate refresh token
        token_data = decode_token(refresh_token)
        
        # Verify it's a refresh token
        if token_data.exp.tzinfo is None:
            raise InvalidTokenError("Invalid token format")
        
        # Generate new tokens with same user data
        new_token_data = {
            "user_id": token_data.user_id,
            "username": token_data.username,
            "email": getattr(token_data, 'email', ''),
            "display_name": getattr(token_data, 'display_name', token_data.username),
            "role": token_data.role,
            "dn": getattr(token_data, 'dn', '')
        }
        
        new_access_token = create_access_token(new_token_data)
        new_refresh_token = create_refresh_token(new_token_data)
        
        logger.info(f"Token refreshed for user: {token_data.username}")
        
        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=1800
        )
        
    except InvalidTokenError as e:
        logger.warning(f"Invalid refresh token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=dict)
async def get_current_user_info(authorization: str = Header(...)):
    """
    Get current authenticated user information
    
    Decodes JWT token and returns user profile information.
    
    Args:
        authorization: Bearer token header
        
    Returns:
        User profile information
        
    Raises:
        HTTPException: 401 if token is invalid
    """
    try:
        # Extract token from Authorization header
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format"
            )
        
        token = authorization.split(" ")[1]
        
        # Decode token
        token_data = decode_token(token)
        
        return {
            "user_id": token_data.user_id,
            "username": token_data.username,
            "email": getattr(token_data, 'email', ''),
            "display_name": getattr(token_data, 'display_name', token_data.username),
            "role": token_data.role,
            "exp": token_data.exp.isoformat()
        }
        
    except InvalidTokenError as e:
        logger.warning(f"Invalid token in /me endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/health")
async def ldap_health_check():
    """
    Check LDAP connection health
    
    Returns:
        LDAP server connectivity status
    """
    try:
        ldap_auth = get_ldap_authenticator()
        is_connected = ldap_auth.test_connection()
        
        return {
            "status": "healthy" if is_connected else "unhealthy",
            "ldap_server": ldap_auth.server_url,
            "connected": is_connected
        }
    except Exception as e:
        logger.error(f"LDAP health check failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
