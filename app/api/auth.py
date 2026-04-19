"""
API Authentication and Authorization Module
Provides API Key-based authentication with database persistence and audit logging
"""
import logging
import os
import secrets
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, Security, status, Request
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from app.db.database import get_db
from app.db.repositories import APIKeyRepository, AuditLogRepository

logger = logging.getLogger(__name__)

# API Key header name
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


class APIUser(BaseModel):
    """Authenticated API user model"""
    user_id: str
    role: str
    rate_limit: int  # requests per minute
    description: str = ""


def _get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_api_key(
    api_key: Optional[str] = Security(API_KEY_HEADER),
    request: Request = None,
    db=Depends(get_db)
) -> APIUser:
    """
    Dependency to require API key authentication with database validation
    
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
    
    # Initialize repository
    repo = APIKeyRepository(db)
    
    # Hash the API key for lookup (in production, use proper hashing like bcrypt)
    import hashlib
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    # Validate against database
    db_key = repo.get_by_hash(key_hash)
    
    if not db_key:
        # Log failed authentication attempt
        if request:
            audit_repo = AuditLogRepository(db)
            audit_repo.create_log(
                action="api_auth_failed",
                user_id="unknown",
                ip_address=_get_client_ip(request),
                method=request.method,
                endpoint=str(request.url.path),
                status_code=401,
                error_message="Invalid API key",
                metadata={"key_prefix": api_key[:8] + "..." if len(api_key) > 8 else api_key}
            )
            db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Increment usage counter
    repo.increment_usage(key_hash)
    db.commit()
    
    # Log successful authentication
    if request:
        audit_repo = AuditLogRepository(db)
        audit_repo.create_log(
            action="api_auth_success",
            user_id=db_key.owner or db_key.name,
            ip_address=_get_client_ip(request),
            method=request.method,
            endpoint=str(request.url.path),
            status_code=200,
            metadata={"api_key_name": db_key.name}
        )
        db.commit()
    
    return APIUser(
        user_id=db_key.owner or db_key.name,
        role="admin" if db_key.owner else "user",
        rate_limit=db_key.rate_limit,
        description=db_key.name
    )


def get_optional_api_key(
    api_key: Optional[str] = Security(API_KEY_HEADER),
    request: Request = None,
    db=Depends(get_db)
) -> Optional[APIUser]:
    """
    Dependency for optional API key authentication
    
    Usage:
        @app.get("/public")
        async def public_endpoint(current_user: Optional[APIUser] = Depends(get_optional_api_key)):
            ...
    
    Returns:
        APIUser object if valid key provided, None otherwise
    """
    if not api_key:
        return None
    
    try:
        return get_api_key(api_key, request, db)
    except HTTPException:
        return None


def generate_api_key() -> str:
    """Generate a new secure API key"""
    return f"sk-{secrets.token_urlsafe(32)}"


def create_api_key_in_db(
    name: str,
    owner: Optional[str] = None,
    rate_limit: int = 100,
    db=None
) -> tuple[str, dict]:
    """
    Create a new API key in database
    
    Returns:
        Tuple of (plain_text_key, key_info_dict)
    """
    import hashlib
    
    # Generate new key
    plain_key = generate_api_key()
    key_hash = hashlib.sha256(plain_key.encode()).hexdigest()
    
    # Save to database
    repo = APIKeyRepository(db)
    db_key = repo.create(
        key_hash=key_hash,
        name=name,
        owner=owner,
        rate_limit=rate_limit
    )
    db.commit()
    
    logger.info(f"Created API key: {name} for owner: {owner}")
    
    return plain_key, {
        "id": db_key.id,
        "name": db_key.name,
        "owner": db_key.owner,
        "rate_limit": db_key.rate_limit,
        "created_at": db_key.created_at.isoformat() if db_key.created_at else None,
    }


def revoke_api_key_in_db(api_key: str, db=None) -> bool:
    """
    Revoke an API key in database
    
    Returns:
        True if revoked, False if not found
    """
    import hashlib
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    repo = APIKeyRepository(db)
    result = repo.deactivate(key_hash)
    db.commit()
    
    if result:
        logger.info(f"Revoked API key hash: {key_hash[:16]}...")
    
    return result


def require_role(required_role: str):
    """
    Dependency factory to require specific user role
    
    Usage:
        @app.delete("/admin-only")
        async def admin_endpoint(current_user: APIUser = Depends(require_role("admin"))):
            ...
    """
    def role_checker(current_user: APIUser = Depends(get_api_key)) -> APIUser:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
        return current_user
    
    return role_checker
