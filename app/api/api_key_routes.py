"""
API Key Management Routes
Provides endpoints for managing API keys with database persistence
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List
from pydantic import BaseModel

from app.api.auth import get_api_key, APIUser, create_api_key_in_db, revoke_api_key_in_db
from app.db.database import get_db
from app.db.repositories import APIKeyRepository, AuditLogRepository
from app.monitoring.metrics import active_api_keys

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api-keys", tags=["API Key Management"])


class CreateAPIKeyRequest(BaseModel):
    """Request to create a new API key"""
    name: str
    owner: str = None
    rate_limit: int = 100


class CreateAPIKeyResponse(BaseModel):
    """Response with newly created API key"""
    api_key: str
    key_info: dict
    warning: str = "Store this key securely. It will not be shown again."


class APIKeyInfo(BaseModel):
    """API key information (without the actual key)"""
    id: int
    name: str
    owner: str = None
    is_active: bool
    rate_limit: int
    total_requests: int
    created_at: str = None
    last_used_at: str = None


@router.post("/", response_model=CreateAPIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request_data: CreateAPIKeyRequest,
    request: Request,
    current_user: APIUser = Depends(get_api_key),
    db=Depends(get_db)
):
    """
    Create a new API key
    
    Requires admin role. The generated key will only be shown once.
    
    Args:
        request_data: Key creation parameters
        
    Returns:
        New API key and metadata
    """
    # Check admin role
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required to create API keys"
        )
    
    # Create key in database
    plain_key, key_info = create_api_key_in_db(
        name=request_data.name,
        owner=request_data.owner,
        rate_limit=request_data.rate_limit,
        db=db
    )
    
    # Log action
    audit_repo = AuditLogRepository(db)
    audit_repo.create_log(
        action="api_key_created",
        user_id=current_user.user_id,
        resource_type="api_key",
        resource_id=str(key_info["id"]),
        ip_address=request.client.host if request.client else "unknown",
        method="POST",
        endpoint="/api/v1/api-keys/",
        status_code=201,
        metadata={"key_name": request_data.name, "owner": request_data.owner}
    )
    db.commit()
    
    # Update metrics
    active_api_keys.inc()
    
    return CreateAPIKeyResponse(
        api_key=plain_key,
        key_info=key_info
    )


@router.get("/", response_model=List[APIKeyInfo])
async def list_api_keys(
    request: Request,
    current_user: APIUser = Depends(get_api_key),
    db=Depends(get_db)
):
    """
    List all API keys (metadata only, no actual keys)
    
    Requires admin role.
    
    Returns:
        List of API key metadata
    """
    # Check admin role
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required to list API keys"
        )
    
    repo = APIKeyRepository(db)
    db_keys = repo.list_all(active_only=False)
    
    return [
        APIKeyInfo(
            id=key.id,
            name=key.name,
            owner=key.owner,
            is_active=key.is_active,
            rate_limit=key.rate_limit,
            total_requests=key.total_requests,
            created_at=key.created_at.isoformat() if key.created_at else None,
            last_used_at=key.last_used_at.isoformat() if key.last_used_at else None,
        )
        for key in db_keys
    ]


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: int,
    request: Request,
    current_user: APIUser = Depends(get_api_key),
    db=Depends(get_db)
):
    """
    Revoke an API key by ID
    
    Requires admin role.
    
    Args:
        key_id: Database ID of the API key to revoke
    """
    # Check admin role
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required to revoke API keys"
        )
    
    repo = APIKeyRepository(db)
    
    # Get key info before revoking
    from app.db.models import APIKey as DBAPIKey
    db_key = db.query(DBAPIKey).filter(DBAPIKey.id == key_id).first()
    
    if not db_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key with ID {key_id} not found"
        )
    
    # Deactivate the key
    success = repo.deactivate(db_key.key_hash)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to revoke API key"
        )
    
    db.commit()
    
    # Log action
    audit_repo = AuditLogRepository(db)
    audit_repo.create_log(
        action="api_key_revoked",
        user_id=current_user.user_id,
        resource_type="api_key",
        resource_id=str(key_id),
        ip_address=request.client.host if request.client else "unknown",
        method="DELETE",
        endpoint=f"/api/v1/api-keys/{key_id}",
        status_code=200,
        metadata={"key_name": db_key.name, "owner": db_key.owner}
    )
    db.commit()
    
    # Update metrics
    active_api_keys.dec()
    
    logger.info(f"API key revoked: ID={key_id}, Name={db_key.name}")
    
    return {"message": f"API key '{db_key.name}' has been revoked"}


@router.get("/metrics")
async def get_api_key_metrics(
    current_user: APIUser = Depends(get_api_key),
    db=Depends(get_db)
):
    """
    Get API key usage metrics
    
    Returns:
        Summary statistics about API key usage
    """
    repo = APIKeyRepository(db)
    
    all_keys = repo.list_all(active_only=False)
    active_keys = [k for k in all_keys if k.is_active]
    
    total_requests = sum(k.total_requests for k in all_keys)
    
    return {
        "total_keys": len(all_keys),
        "active_keys": len(active_keys),
        "inactive_keys": len(all_keys) - len(active_keys),
        "total_requests_all_time": total_requests,
        "avg_requests_per_key": total_requests / len(all_keys) if all_keys else 0,
    }
