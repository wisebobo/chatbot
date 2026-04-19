"""
JWT Authentication Dependencies
Provides FastAPI dependencies for JWT token validation
"""
import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import InvalidTokenError

from app.api.jwt_auth import decode_token, TokenData

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


def get_optional_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[TokenData]:
    """
    Optional authentication - returns None if no valid token
    
    Usage:
        @app.get("/optional-auth")
        async def optional_auth_endpoint(current_user: Optional[TokenData] = Depends(get_optional_current_user)):
            if current_user:
                # User is authenticated
                pass
            else:
                # Anonymous user
                pass
    
    Args:
        credentials: HTTP authorization credentials from header
        
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


def require_role(required_role: str):
    """
    Dependency factory to require specific user role
    
    Usage:
        @app.get("/admin-only")
        async def admin_endpoint(current_user: TokenData = Depends(require_role("admin"))):
            ...
    
    Args:
        required_role: Required role (e.g., 'admin', 'user')
        
    Returns:
        Dependency function that checks user role
    """
    def role_checker(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
        return current_user
    
    return role_checker
