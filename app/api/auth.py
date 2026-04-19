"""
API Authentication and Authorization Module
Provides API Key-based authentication for production use
"""
import logging
import os
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# API Key header name
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


class APIUser(BaseModel):
    """Authenticated API user model"""
    user_id: str
    role: str
    rate_limit: int  # requests per minute
    description: str = ""


class APIKeyManager:
    """
    Manage API keys for authentication
    
    In production, this should be replaced with:
    - Database-backed key storage
    - Key rotation policies
    - Expiration handling
    """
    
    def __init__(self):
        # Load API keys from environment or config
        # Format: API_KEYS='{"key1": {"user_id": "user1", "role": "admin", "rate_limit": 100}}'
        self.api_keys: Dict[str, Dict[str, Any]] = self._load_api_keys()
        logger.info(f"Loaded {len(self.api_keys)} API keys")
    
    def _load_api_keys(self) -> Dict[str, Dict[str, Any]]:
        """Load API keys from environment variable"""
        import json
        
        # Default test keys (should be replaced in production)
        default_keys = {
            "sk-test-key-12345": {
                "user_id": "test_admin",
                "role": "admin",
                "rate_limit": 100,
                "description": "Test admin key"
            },
            "sk-user-key-67890": {
                "user_id": "test_user",
                "role": "user",
                "rate_limit": 30,
                "description": "Test user key"
            }
        }
        
        # Try to load from environment
        api_keys_env = os.getenv("API_KEYS")
        if api_keys_env:
            try:
                loaded_keys = json.loads(api_keys_env)
                logger.info("Loaded API keys from environment")
                return loaded_keys
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse API_KEYS environment variable: {e}")
                logger.warning("Using default test keys")
        
        return default_keys
    
    def validate_key(self, api_key: str) -> Optional[APIUser]:
        """
        Validate API key and return user info
        
        Args:
            api_key: The API key to validate
            
        Returns:
            APIUser object if valid, None otherwise
        """
        key_info = self.api_keys.get(api_key)
        if not key_info:
            return None
        
        return APIUser(
            user_id=key_info["user_id"],
            role=key_info["role"],
            rate_limit=key_info["rate_limit"],
            description=key_info.get("description", "")
        )
    
    def add_key(self, api_key: str, user_id: str, role: str = "user", 
                rate_limit: int = 30, description: str = ""):
        """
        Add a new API key (for runtime management)
        
        Note: In production, this should persist to database
        """
        self.api_keys[api_key] = {
            "user_id": user_id,
            "role": role,
            "rate_limit": rate_limit,
            "description": description
        }
        logger.info(f"Added API key for user: {user_id}")
    
    def revoke_key(self, api_key: str) -> bool:
        """
        Revoke an API key
        
        Returns:
            True if key was revoked, False if not found
        """
        if api_key in self.api_keys:
            del self.api_keys[api_key]
            logger.info(f"Revoked API key")
            return True
        return False


# Global API key manager instance
api_key_manager = APIKeyManager()


def get_api_key(api_key: Optional[str] = Security(API_KEY_HEADER)) -> APIUser:
    """
    Dependency to require API key authentication
    
    Usage:
        @app.get("/protected")
        async def protected_endpoint(current_user: APIUser = Depends(get_api_key)):
            ...
    
    Args:
        api_key: API key from request header
        
    Returns:
        APIUser object if authenticated
        
    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Please provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    user = api_key_manager.validate_key(api_key)
    if not user:
        logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    logger.debug(f"Authenticated user: {user.user_id} (role: {user.role})")
    return user


def get_optional_api_key(api_key: Optional[str] = Security(API_KEY_HEADER)) -> Optional[APIUser]:
    """
    Dependency for optional API key authentication (public endpoints)
    
    Usage:
        @app.get("/public")
        async def public_endpoint(current_user: Optional[APIUser] = Depends(get_optional_api_key)):
            if current_user:
                # Authenticated user
            else:
                # Anonymous user
        
    Returns:
        APIUser object if authenticated, None otherwise
    """
    if not api_key:
        return None
    
    user = api_key_manager.validate_key(api_key)
    if not user:
        logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
        return None
    
    return user


def require_role(required_role: str):
    """
    Dependency factory to require specific user role
    
    Usage:
        @app.delete("/admin/endpoint")
        async def admin_endpoint(current_user: APIUser = Depends(require_role("admin"))):
            ...
    
    Args:
        required_role: Required user role (e.g., "admin", "moderator")
        
    Returns:
        Dependency function
    """
    def role_checker(current_user: APIUser = Depends(get_api_key)) -> APIUser:
        if current_user.role != required_role and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
        return current_user
    
    return role_checker
