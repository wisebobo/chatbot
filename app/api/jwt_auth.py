"""
JWT Authentication Module
Provides token-based authentication with user management
"""
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
import hashlib
from pydantic import BaseModel, EmailStr, Field

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production-please-use-env-variable")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


class Token(BaseModel):
    """JWT token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Decoded token data"""
    user_id: str
    username: str
    role: str
    exp: datetime


class UserCreate(BaseModel):
    """User registration request model"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    """User login request model"""
    username: str
    password: str


class UserResponse(BaseModel):
    """User response model (excludes sensitive data)"""
    user_id: str
    username: str
    email: str
    role: str
    is_active: bool
    created_at: str


class UserInDB(BaseModel):
    """User model stored in database"""
    user_id: str
    username: str
    email: str
    hashed_password: str
    role: str = "user"
    is_active: bool = True
    created_at: datetime = None
    
    def __init__(self, **data):
        if 'created_at' not in data or data['created_at'] is None:
            data['created_at'] = datetime.now(timezone.utc)
        super().__init__(**data)


def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with salt"""
    # Generate a random salt
    import secrets
    salt = secrets.token_hex(16)
    # Hash password with salt
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    # Return salt:hash format
    return f"{salt}:{hashed}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        salt, hash_value = hashed_password.split(":")
        hashed = hashlib.sha256((plain_password + salt).encode()).hexdigest()
        return hashed == hash_value
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("user_id")
        username: str = payload.get("username")
        role: str = payload.get("role")
        exp: int = payload.get("exp")
        token_type: str = payload.get("type")
        
        if user_id is None or username is None:
            raise jwt.InvalidTokenError("Invalid token payload")
        
        return TokenData(
            user_id=user_id,
            username=username,
            role=role,
            exp=datetime.fromtimestamp(exp, tz=timezone.utc)
        )
    except jwt.ExpiredSignatureError:
        raise jwt.InvalidTokenError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise jwt.InvalidTokenError(f"Invalid token: {str(e)}")


class InMemoryUserStore:
    """
    In-memory user store for demonstration purposes
    
    WARNING: In production, replace this with a proper database backend
    such as PostgreSQL, MongoDB, or SQLAlchemy ORM
    """
    
    def __init__(self):
        self.users: dict[str, UserInDB] = {}
        self._initialize_default_users()
        logger.info(f"Initialized user store with {len(self.users)} users")
    
    def _initialize_default_users(self):
        """Initialize default admin user"""
        admin_user = UserInDB(
            user_id="admin_001",
            username="admin",
            email="admin@example.com",
            hashed_password=hash_password("admin123456"),
            role="admin",
            is_active=True
        )
        self.users[admin_user.username] = admin_user
        
        test_user = UserInDB(
            user_id="user_001",
            username="testuser",
            email="testuser@example.com",
            hashed_password=hash_password("test123456"),
            role="user",
            is_active=True
        )
        self.users[test_user.username] = test_user
    
    def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        """Get user by username"""
        return self.users.get(username)
    
    def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email"""
        for user in self.users.values():
            if user.email == email:
                return user
        return None
    
    def create_user(self, user_data: UserCreate) -> UserInDB:
        """Create a new user"""
        # Check if username already exists
        if user_data.username in self.users:
            raise ValueError(f"Username '{user_data.username}' already exists")
        
        # Check if email already exists
        if self.get_user_by_email(user_data.email):
            raise ValueError(f"Email '{user_data.email}' already registered")
        
        # Create new user
        import uuid
        new_user = UserInDB(
            user_id=f"user_{uuid.uuid4().hex[:8]}",
            username=user_data.username,
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            role="user",
            is_active=True
        )
        
        self.users[new_user.username] = new_user
        logger.info(f"Created new user: {new_user.username}")
        return new_user
    
    def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        """Authenticate user with username and password"""
        user = self.get_user_by_username(username)
        if not user:
            return None
        
        if not user.is_active:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    def list_users(self) -> list[UserResponse]:
        """List all users (for admin only)"""
        return [
            UserResponse(
                user_id=user.user_id,
                username=user.username,
                email=user.email,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at.isoformat()
            )
            for user in self.users.values()
        ]
    
    def deactivate_user(self, username: str) -> bool:
        """Deactivate a user account"""
        user = self.users.get(username)
        if user:
            user.is_active = False
            logger.info(f"Deactivated user: {username}")
            return True
        return False


# Global user store instance
user_store = InMemoryUserStore()
