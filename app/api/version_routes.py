"""
API Version Information Routes

Provides endpoints to query API version information, supported versions,
and migration guides.
"""
from fastapi import APIRouter, Depends, Request
from typing import Dict, Any
from app.api.versioning import APIVersionManager, get_api_version

router = APIRouter(
    prefix="/version",
    tags=["API Versioning"],
    responses={
        400: {"description": "Unsupported API version"},
        410: {"description": "API version has been sunset"}
    }
)


@router.get("/")
async def get_version_info(request: Request) -> Dict[str, Any]:
    """
    Get current API version information
    
    Returns details about the current API version being used,
    including deprecation status and available upgrades.
    """
    current_version = get_api_version(request)
    version_info = APIVersionManager.get_version(current_version)
    
    if not version_info:
        return {
            "current_version": current_version,
            "supported": False,
            "latest_version": APIVersionManager.LATEST_VERSION
        }
    
    return {
        "current_version": version_info.to_dict(),
        "latest_version": APIVersionManager.LATEST_VERSION,
        "upgrade_available": current_version != APIVersionManager.LATEST_VERSION,
        "deprecation_warning": version_info.is_deprecated,
        "sunset_warning": version_info.is_sunset
    }


@router.get("/supported")
async def list_supported_versions() -> Dict[str, Any]:
    """
    List all supported API versions
    
    Returns metadata for all currently supported API versions,
    including release dates, deprecation status, and changes.
    """
    return {
        "versions": APIVersionManager.get_all_versions(),
        "default_version": APIVersionManager.DEFAULT_VERSION,
        "latest_version": APIVersionManager.LATEST_VERSION,
        "versioning_strategy": {
            "url_path": "/api/{version}/...",
            "header_accept": "application/vnd.api.{version}+json",
            "custom_header": "X-API-Version: {version}"
        }
    }


@router.get("/{version}")
async def get_specific_version(version: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific API version
    
    Args:
        version: Version string (e.g., "v1", "v2")
    
    Returns:
        Detailed version information including changes and migration guide
    """
    version_info = APIVersionManager.get_version(version)
    
    if not version_info:
        return {
            "error": {
                "code": "VERSION_NOT_FOUND",
                "message": f"Version '{version}' is not recognized",
                "supported_versions": list(APIVersionManager.SUPPORTED_VERSIONS.keys())
            }
        }
    
    return {
        "version": version_info.to_dict(),
        "is_current_default": version == APIVersionManager.DEFAULT_VERSION,
        "is_latest": version == APIVersionManager.LATEST_VERSION
    }


@router.get("/{version}/migration")
async def get_migration_guide(version: str) -> Dict[str, Any]:
    """
    Get migration guide for upgrading from a specific version
    
    Args:
        version: The version to migrate from
    
    Returns:
        Migration guide with breaking changes and upgrade instructions
    """
    version_info = APIVersionManager.get_version(version)
    
    if not version_info:
        return {
            "error": {
                "code": "VERSION_NOT_FOUND",
                "message": f"Version '{version}' is not recognized"
            }
        }
    
    if not version_info.migration_guide:
        return {
            "version": version,
            "migration_guide": None,
            "message": "No migration guide available for this version",
            "changes": version_info.changes
        }
    
    return {
        "version": version,
        "target_version": APIVersionManager.LATEST_VERSION,
        "migration_guide_url": version_info.migration_guide,
        "breaking_changes": [
            change for change in version_info.changes 
            if "breaking" in change.lower() or "removed" in change.lower()
        ],
        "all_changes": version_info.changes
    }


@router.get("/changelog")
async def get_changelog() -> Dict[str, Any]:
    """
    Get changelog for all API versions
    
    Returns a chronological list of changes across all versions.
    """
    changelog = []
    
    for ver_str, ver_info in sorted(
        APIVersionManager.SUPPORTED_VERSIONS.items(),
        key=lambda x: x[1].release_date,
        reverse=True
    ):
        changelog.append({
            "version": ver_str,
            "release_date": ver_info.release_date,
            "deprecation_date": ver_info.deprecation_date,
            "changes": ver_info.changes,
            "status": "sunset" if ver_info.is_sunset else "deprecated" if ver_info.is_deprecated else "stable"
        })
    
    return {
        "changelog": changelog,
        "total_versions": len(changelog),
        "latest_version": APIVersionManager.LATEST_VERSION
    }
