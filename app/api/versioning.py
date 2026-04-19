"""
API Version Management Module

Provides comprehensive API versioning support including:
- URL path versioning (/api/v1, /api/v2)
- Header-based version negotiation
- Deprecation headers and warnings
- Backward compatibility layer
- Version migration utilities
"""
from typing import Optional, Dict, Any
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import re
from datetime import datetime


class APIVersion:
    """Represents an API version with metadata"""
    
    def __init__(
        self,
        version: str,
        release_date: str,
        deprecation_date: Optional[str] = None,
        sunset_date: Optional[str] = None,
        is_deprecated: bool = False,
        is_sunset: bool = False,
        changes: Optional[list] = None,
        migration_guide: Optional[str] = None
    ):
        self.version = version
        self.release_date = release_date
        self.deprecation_date = deprecation_date
        self.sunset_date = sunset_date
        self.is_deprecated = is_deprecated
        self.is_sunset = is_sunset
        self.changes = changes or []
        self.migration_guide = migration_guide
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert version info to dictionary"""
        return {
            "version": self.version,
            "release_date": self.release_date,
            "deprecation_date": self.deprecation_date,
            "sunset_date": self.sunset_date,
            "is_deprecated": self.is_deprecated,
            "is_sunset": self.is_sunset,
            "changes": self.changes,
            "migration_guide": self.migration_guide
        }


class APIVersionManager:
    """Manages API versions and their lifecycle"""
    
    # Supported versions registry
    SUPPORTED_VERSIONS: Dict[str, APIVersion] = {
        "v1": APIVersion(
            version="v1",
            release_date="2026-01-01",
            deprecation_date=None,
            sunset_date=None,
            is_deprecated=False,
            is_sunset=False,
            changes=[
                "Initial API release",
                "Core chat functionality",
                "Wiki knowledge base integration",
                "RAG skill support"
            ],
            migration_guide=None
        ),
        # Future versions can be added here
        # "v2": APIVersion(...)
    }
    
    # Default version when not specified
    DEFAULT_VERSION = "v1"
    
    # Latest stable version
    LATEST_VERSION = "v1"
    
    @classmethod
    def get_version(cls, version: str) -> Optional[APIVersion]:
        """Get version information by version string"""
        return cls.SUPPORTED_VERSIONS.get(version)
    
    @classmethod
    def is_supported(cls, version: str) -> bool:
        """Check if version is supported"""
        return version in cls.SUPPORTED_VERSIONS
    
    @classmethod
    def is_deprecated(cls, version: str) -> bool:
        """Check if version is deprecated"""
        ver = cls.get_version(version)
        return ver.is_deprecated if ver else False
    
    @classmethod
    def is_sunset(cls, version: str) -> bool:
        """Check if version has been sunset (no longer available)"""
        ver = cls.get_version(version)
        return ver.is_sunset if ver else False
    
    @classmethod
    def get_all_versions(cls) -> Dict[str, Dict[str, Any]]:
        """Get all supported versions with metadata"""
        return {
            ver: info.to_dict()
            for ver, info in cls.SUPPORTED_VERSIONS.items()
        }
    
    @classmethod
    def get_latest_version(cls) -> str:
        """Get the latest stable version"""
        return cls.LATEST_VERSION


class APIVersionMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API version handling
    
    Supports:
    1. URL path versioning: /api/v1/chat, /api/v2/chat
    2. Header-based versioning: Accept: application/vnd.api.v1+json
    3. Adds deprecation headers to responses
    4. Validates version support
    """
    
    # Pattern to extract version from URL path
    VERSION_PATTERN = re.compile(r'^/api/(v\d+)/')
    
    # Custom media type pattern
    VENDOR_MEDIA_TYPE_PATTERN = re.compile(
        r'application/vnd\.api\.(v\d+)\+json'
    )
    
    async def dispatch(self, request: Request, call_next):
        """Process request and add version handling"""
        
        # Extract version from request
        api_version = self._extract_version(request)
        
        # Validate version
        if not APIVersionManager.is_supported(api_version):
            return self._create_unsupported_version_response(api_version)
        
        # Check if version is sunset
        if APIVersionManager.is_sunset(api_version):
            return self._create_sunset_response(api_version)
        
        # Add version info to request state
        request.state.api_version = api_version
        
        # Process request
        response = await call_next(request)
        
        # Add version headers to response
        self._add_version_headers(response, api_version)
        
        return response
    
    def _extract_version(self, request: Request) -> str:
        """
        Extract API version from request using priority:
        1. URL path (/api/v1/...)
        2. Accept header (application/vnd.api.v1+json)
        3. Custom header (X-API-Version: v1)
        4. Default version
        """
        
        # 1. Try URL path
        path = request.url.path
        match = self.VERSION_PATTERN.match(path)
        if match:
            return match.group(1)
        
        # 2. Try Accept header
        accept_header = request.headers.get("accept", "")
        match = self.VENDOR_MEDIA_TYPE_PATTERN.search(accept_header)
        if match:
            return match.group(1)
        
        # 3. Try custom header
        custom_version = request.headers.get("x-api-version")
        if custom_version:
            return custom_version
        
        # 4. Use default version
        return APIVersionManager.DEFAULT_VERSION
    
    def _add_version_headers(self, response: Response, version: str):
        """Add version-related headers to response"""
        
        # Current API version
        response.headers["X-API-Version"] = version
        
        # Latest available version
        response.headers["X-API-Latest-Version"] = APIVersionManager.LATEST_VERSION
        
        # Deprecation warning if applicable
        if APIVersionManager.is_deprecated(version):
            ver_info = APIVersionManager.get_version(version)
            if ver_info and ver_info.deprecation_date:
                response.headers["Deprecation"] = f"date={ver_info.deprecation_date}"
                response.headers["Sunset"] = f"date={ver_info.sunset_date}" if ver_info.sunset_date else ""
                
                # Add link to migration guide
                if ver_info.migration_guide:
                    response.headers["Link"] = f'<{ver_info.migration_guide}>; rel="successor-version"'
    
    def _create_unsupported_version_response(self, version: str) -> Response:
        """Create error response for unsupported version"""
        from starlette.responses import JSONResponse
        
        supported_versions = list(APIVersionManager.SUPPORTED_VERSIONS.keys())
        
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "UNSUPPORTED_API_VERSION",
                    "message": f"API version '{version}' is not supported",
                    "supported_versions": supported_versions,
                    "latest_version": APIVersionManager.LATEST_VERSION,
                    "documentation": "/api/docs"
                }
            },
            headers={
                "X-API-Latest-Version": APIVersionManager.LATEST_VERSION,
                "X-Supported-Versions": ", ".join(supported_versions)
            }
        )
    
    def _create_sunset_response(self, version: str) -> Response:
        """Create error response for sunset version"""
        from starlette.responses import JSONResponse
        
        ver_info = APIVersionManager.get_version(version)
        
        return JSONResponse(
            status_code=410,  # Gone
            content={
                "error": {
                    "code": "API_VERSION_SUNSET",
                    "message": f"API version '{version}' has been retired",
                    "sunset_date": ver_info.sunset_date if ver_info else None,
                    "migration_guide": ver_info.migration_guide if ver_info else None,
                    "latest_version": APIVersionManager.LATEST_VERSION
                }
            },
            headers={
                "X-API-Latest-Version": APIVersionManager.LATEST_VERSION,
                "Sunset": f"date={ver_info.sunset_date}" if ver_info and ver_info.sunset_date else ""
            }
        )


def get_api_version(request: Request) -> str:
    """Helper function to get API version from request"""
    return getattr(request.state, 'api_version', APIVersionManager.DEFAULT_VERSION)


def require_minimum_version(min_version: str = "v1"):
    """
    Decorator to enforce minimum API version for endpoints
    
    Usage:
        @router.post("/chat")
        @require_minimum_version("v1")
        async def chat_endpoint(request: Request):
            ...
    """
    def decorator(func):
        from functools import wraps
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find request in args or kwargs
            request = None
            
            # Check kwargs first
            if 'request' in kwargs:
                request = kwargs['request']
            else:
                # Check args (Request is usually the first arg in FastAPI)
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if request:
                current_version = get_api_version(request)
                
                # Simple version comparison (v1 < v2 < v3...)
                try:
                    current_num = int(current_version.replace('v', ''))
                    min_num = int(min_version.replace('v', ''))
                    
                    if current_num < min_num:
                        raise HTTPException(
                            status_code=400,
                            detail={
                                "error": {
                                    "code": "MINIMUM_VERSION_REQUIRED",
                                    "message": f"This endpoint requires API version {min_version} or higher",
                                    "current_version": current_version,
                                    "minimum_version": min_version,
                                    "latest_version": APIVersionManager.LATEST_VERSION
                                }
                            }
                        )
                except (ValueError, AttributeError):
                    # If version format is invalid, allow the request
                    pass
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Export main components
__all__ = [
    "APIVersion",
    "APIVersionManager",
    "APIVersionMiddleware",
    "get_api_version",
    "require_minimum_version"
]
