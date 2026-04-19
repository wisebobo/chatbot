"""
JWT Authentication Dependencies
Provides FastAPI dependencies for JWT token validation
"""
import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import InvalidTokenError

from app.api.jwt_auth import decode_token, TokenData, user_store

logger = logging.getLogger(__name__)

# HTTP Bearer security scheme
security = HTTPBearer(auto_error=False)


def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> TokenData:
    """
    Dependency to get current authenticated user from JWT token
    
    Usage:
        @app.get("/protected")
        async def protected_endpoint(current_user: TokenData = Depends(get_current_user)):
            ...
    
    Args:
        credentials: HTTP authorization credentials from header
        
    Returns:
        TokenData with user information
        
    Raises:
        HTTPException: If token is missing or invalid
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        token_data = decode_token(credentials.credentials)
        return token_data
    except InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_active_user(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """
    Dependency to get current active user (checks if user is active)
    
    Usage:
        @app.get("/active-only")
        async def active_only_endpoint(current_user: TokenData = Depends(get_current_active_user)):
            ...
    
    Args:
        current_user: Current user token data
        
    Returns:
        TokenData if user is active
        
    Raises:
        HTTPException: If user is not found or inactive
    """
    user = user_store.get_user_by_username(current_user.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    return current_user


def require_role(required_role: str):
    """
    Dependency factory to require specific user role
    
    Usage:
        @app.delete("/admin/endpoint")
        async def admin_endpoint(current_user: TokenData = Depends(require_role("admin"))):
            ...
    
    Args:
        required_role: Required user role (e.g., "admin", "user")
        
    Returns:
        Dependency function that checks user role
    """
    def role_checker(current_user: TokenData = Depends(get_current_active_user)) -> TokenData:
        if current_user.role != required_role and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
        return current_user
    
    return role_checker


def get_optional_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[TokenData]:
    """
    Dependency for optional JWT authentication (public endpoints)
    
    Usage:
        @app.get("/public")
        async def public_endpoint(current_user: Optional[TokenData] = Depends(get_optional_current_user)):
            if current_user:
                # Authenticated user
            else:
                # Anonymous user
        
    Returns:
        TokenData if authenticated, None otherwise
    """
    if credentials is None:
        return None
    
    try:
        token_data = decode_token(credentials.credentials)
        return token_data
    except InvalidTokenError:
        return None
