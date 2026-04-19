"""
Authentication API Routes
Provides user registration, login, and token management endpoints
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import Optional
from jwt import InvalidTokenError

from app.api.jwt_auth import (
    user_store,
    UserCreate,
    UserLogin,
    Token,
    UserResponse,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.monitoring.metrics import (
    auth_failures,
    user_registrations,
    user_logins,
    jwt_tokens_issued,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """
    Register a new user account
    
    Creates a new user with the provided credentials and returns JWT tokens.
    
    Args:
        user_data: User registration data (username, email, password)
        
    Returns:
        JWT access and refresh tokens
        
    Raises:
        HTTPException: 400 if username or email already exists
    """
    try:
        # Create user in store
        new_user = user_store.create_user(user_data)
        
        logger.info(f"New user registered: {new_user.username}")
        
        # Track registration metric
        user_registrations.inc()
        
        # Generate tokens
        token_data = {
            "user_id": new_user.user_id,
            "username": new_user.username,
            "role": new_user.role
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
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """
    Authenticate user and return JWT tokens
    
    Validates username and password, then issues JWT tokens for authenticated session.
    
    Args:
        credentials: Login credentials (username, password)
        
    Returns:
        JWT access and refresh tokens
        
    Raises:
        HTTPException: 401 if credentials are invalid
    """
    # Authenticate user
    user = user_store.authenticate_user(credentials.username, credentials.password)
    
    if not user:
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
    
    logger.info(f"User logged in: {user.username}")
    
    # Generate tokens
    token_data = {
        "user_id": user.user_id,
        "username": user.username,
        "role": user.role
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=1800
    )


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
        
        # Check if user still exists and is active
        user = user_store.get_user_by_username(token_data.username)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Generate new tokens
        new_token_data = {
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role
        }
        
        new_access_token = create_access_token(new_token_data)
        new_refresh_token = create_refresh_token(new_token_data)
        
        logger.info(f"Token refreshed for user: {user.username}")
        
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


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(authorization: Optional[str] = Header(None)):
    """
    Get current authenticated user information
    
    Extracts user info from JWT token in Authorization header.
    
    Args:
        authorization: Bearer token from Authorization header
        
    Returns:
        User information (excluding sensitive data)
        
    Raises:
        HTTPException: 401 if token is missing or invalid
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.split(" ")[1]
    
    try:
        token_data = decode_token(token)
        
        # Get user from store
        user = user_store.get_user_by_username(token_data.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at.isoformat()
        )
        
    except InvalidTokenError as e:
        logger.warning(f"Invalid token in /me endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/users", response_model=list[UserResponse])
async def list_all_users(authorization: Optional[str] = Header(None)):
    """
    List all users (admin only)
    
    Requires admin role to access this endpoint.
    
    Args:
        authorization: Bearer token from Authorization header
        
    Returns:
        List of all users
        
    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ")[1]

    try:
        token_data = decode_token(token)
        
        # Check admin role
        if token_data.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        
        # List all users
        users = user_store.list_users()
        return users
        
    except InvalidTokenError as e:
        logger.warning(f"Invalid token in /users endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/users/{username}/deactivate")
async def deactivate_user(username: str, authorization: Optional[str] = Header(None)):
    """
    Deactivate a user account (admin only)
    
    Admins can deactivate user accounts to prevent login.
    
    Args:
        username: Username to deactivate
        authorization: Bearer token from Authorization header
        
    Returns:
        Success message
        
    Raises:
        HTTPException: 401 if not authenticated, 403 if not admin, 404 if user not found
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ")[1]

    try:
        token_data = decode_token(token)
        
        # Check admin role
        if token_data.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        
        # Deactivate user
        success = user_store.deactivate_user(username)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{username}' not found"
            )
        
        logger.info(f"User deactivated by admin {token_data.username}: {username}")
        
        return {"message": f"User '{username}' has been deactivated"}
        
    except InvalidTokenError as e:
        logger.warning(f"Invalid token in deactivate endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
