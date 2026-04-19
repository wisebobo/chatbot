# API Version Management Guide

## 📋 Overview

This guide explains the comprehensive API versioning system implemented in the chatbot project. The system supports multiple versioning strategies, deprecation management, and backward compatibility to ensure smooth API evolution.

## 🎯 Features

- ✅ **URL Path Versioning** - `/api/v1/chat`, `/api/v2/chat`
- ✅ **Header-Based Negotiation** - `Accept: application/vnd.api.v1+json`
- ✅ **Custom Header Support** - `X-API-Version: v1`
- ✅ **Deprecation Warnings** - Automatic headers for deprecated versions
- ✅ **Sunset Management** - Graceful retirement of old versions
- ✅ **Version Information API** - Query supported versions and migration guides
- ✅ **Backward Compatibility** - Seamless support for older clients

## 🚀 Quick Start

### Method 1: URL Path Versioning (Recommended)

```bash
# Use version in URL path
curl http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "test"}'
```

### Method 2: Accept Header

```bash
# Specify version in Accept header
curl http://localhost:8000/api/chat \
  -H "Accept: application/vnd.api.v1+json" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

### Method 3: Custom Header

```bash
# Use X-API-Version header
curl http://localhost:8000/api/chat \
  -H "X-API-Version: v1" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

### Default Behavior

If no version is specified, the API defaults to `v1`:

```bash
# This uses v1 by default
curl http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

## 📊 Version Priority

The API extracts version using this priority order:

1. **URL Path** (highest priority) - `/api/v1/...`
2. **Accept Header** - `application/vnd.api.v1+json`
3. **Custom Header** - `X-API-Version: v1`
4. **Default Version** - `v1` (lowest priority)

## 🔍 Checking Version Information

### Get Current Version Info

```bash
curl http://localhost:8000/api/v1/version/
```

**Response:**
```json
{
  "current_version": {
    "version": "v1",
    "release_date": "2026-01-01",
    "deprecation_date": null,
    "sunset_date": null,
    "is_deprecated": false,
    "is_sunset": false,
    "changes": [
      "Initial API release",
      "Core chat functionality",
      "Wiki knowledge base integration",
      "RAG skill support"
    ]
  },
  "latest_version": "v1",
  "upgrade_available": false,
  "deprecation_warning": false,
  "sunset_warning": false
}
```

### List All Supported Versions

```bash
curl http://localhost:8000/api/v1/version/supported
```

**Response:**
```json
{
  "versions": {
    "v1": {
      "version": "v1",
      "release_date": "2026-01-01",
      "is_deprecated": false,
      "is_sunset": false,
      "changes": [...]
    }
  },
  "default_version": "v1",
  "latest_version": "v1",
  "versioning_strategy": {
    "url_path": "/api/{version}/...",
    "header_accept": "application/vnd.api.{version}+json",
    "custom_header": "X-API-Version: {version}"
  }
}
```

### Get Specific Version Details

```bash
curl http://localhost:8000/api/v1/version/v1
```

### View Changelog

```bash
curl http://localhost:8000/api/v1/version/changelog
```

## ⚠️ Deprecation Handling

### Understanding Deprecation Headers

When a version is deprecated, responses include these headers:

```
X-API-Version: v1
X-API-Latest-Version: v2
Deprecation: date=2026-12-31
Sunset: date=2027-06-30
Link: <https://docs.example.com/migrate-to-v2>; rel="successor-version"
```

### Client-Side Handling

```python
import requests

response = requests.get("http://localhost:8000/api/v1/chat")

# Check for deprecation warning
if 'Deprecation' in response.headers:
    print("⚠️  This API version is deprecated!")
    print(f"Deprecation Date: {response.headers['Deprecation']}")
    print(f"Sunset Date: {response.headers.get('Sunset', 'N/A')}")
    
    # Check for migration guide
    if 'Link' in response.headers:
        print(f"Migration Guide: {response.headers['Link']}")
    
    # Plan migration to latest version
    latest = response.headers.get('X-API-Latest-Version')
    print(f"Please migrate to version: {latest}")
```

## 🔄 Version Lifecycle

### Stages

1. **Active** - Fully supported, receives updates
2. **Deprecated** - Still functional but no new features; migration recommended
3. **Sunset** - No longer available; returns HTTP 410 Gone

### Example: Adding a New Version

To add `v2` to the system:

```python
# In app/api/versioning.py

APIVersionManager.SUPPORTED_VERSIONS["v2"] = APIVersion(
    version="v2",
    release_date="2026-06-01",
    deprecation_date=None,
    sunset_date=None,
    is_deprecated=False,
    is_sunset=False,
    changes=[
        "Added analytics endpoint",
        "Improved error messages",
        "Breaking: Changed response format for /chat"
    ],
    migration_guide="https://docs.example.com/migrate-to-v2"
)

APIVersionManager.LATEST_VERSION = "v2"
```

### Marking a Version as Deprecated

```python
# Update v1 to deprecated status
APIVersionManager.SUPPORTED_VERSIONS["v1"] = APIVersion(
    version="v1",
    release_date="2026-01-01",
    deprecation_date="2026-12-31",  # Set deprecation date
    sunset_date="2027-06-30",       # Set sunset date
    is_deprecated=True,              # Mark as deprecated
    is_sunset=False,
    changes=[...],
    migration_guide="https://docs.example.com/migrate-to-v2"
)
```

### Retiring a Version (Sunset)

```python
# Mark v1 as sunset (no longer available)
APIVersionManager.SUPPORTED_VERSIONS["v1"] = APIVersion(
    version="v1",
    release_date="2026-01-01",
    deprecation_date="2026-12-31",
    sunset_date="2027-06-30",
    is_deprecated=True,
    is_sunset=True,  # Mark as sunset
    changes=[...],
    migration_guide="https://docs.example.com/migrate-to-v2"
)
```

When clients try to use a sunset version, they receive:

```json
{
  "error": {
    "code": "API_VERSION_SUNSET",
    "message": "API version 'v1' has been retired",
    "sunset_date": "2027-06-30",
    "migration_guide": "https://docs.example.com/migrate-to-v2",
    "latest_version": "v2"
  }
}
```

## 🛡️ Enforcing Minimum Version

Use the `@require_minimum_version` decorator to enforce minimum API version for specific endpoints:

```python
from fastapi import APIRouter, Request
from app.api.versioning import require_minimum_version

router = APIRouter()

@router.post("/advanced-feature")
@require_minimum_version("v2")  # Requires v2 or higher
async def advanced_feature(request: Request, data: dict):
    # This endpoint only works with API v2+
    return {"result": "success"}
```

Clients using v1 will receive:

```json
{
  "error": {
    "code": "MINIMUM_VERSION_REQUIRED",
    "message": "This endpoint requires API version v2 or higher",
    "current_version": "v1",
    "minimum_version": "v2",
    "latest_version": "v2"
  }
}
```

## 📝 Best Practices

### For API Consumers

1. **Always Specify Version** - Don't rely on defaults; explicitly specify the version
2. **Monitor Deprecation Headers** - Check response headers for deprecation warnings
3. **Plan Migrations Early** - Start migrating when you see deprecation notices
4. **Test Against Latest** - Regularly test your client against the latest API version
5. **Subscribe to Changelog** - Monitor `/api/v1/version/changelog` for updates

### For API Developers

1. **Maintain Backward Compatibility** - Avoid breaking changes within major versions
2. **Provide Migration Guides** - Always include clear migration instructions
3. **Give Ample Warning** - Deprecate versions at least 6 months before sunset
4. **Document Changes** - Keep detailed changelogs for each version
5. **Monitor Usage** - Track which versions are still in use before sunsetting

## 🔧 Implementation Details

### Architecture

```
Request → APIVersionMiddleware → Extract Version → Validate → Process → Add Headers → Response
```

### Key Components

1. **APIVersion** - Represents a single API version with metadata
2. **APIVersionManager** - Manages version registry and lifecycle
3. **APIVersionMiddleware** - Intercepts requests/responses for version handling
4. **Version Routes** - `/api/v1/version/*` endpoints for querying version info

### Files

- [`app/api/versioning.py`](file://e:\Python\chatbot\app\api\versioning.py) - Core versioning logic
- [`app/api/version_routes.py`](file://e:\Python\chatbot\app\api\version_routes.py) - Version information endpoints
- [`app/api/main.py`](file://e:\Python\chatbot\app\api\main.py) - Middleware registration

## 🧪 Testing

### Run Unit Tests

```bash
pytest tests/unit/test_api_versioning.py -v
```

### Run Example Script

```bash
# Start server first
python main.py

# In another terminal
python scripts/example_api_versioning.py
```

### Manual Testing

```bash
# Test URL path versioning
curl http://localhost:8000/api/v1/version/

# Test unsupported version
curl http://localhost:8000/api/v99/version/

# Test header-based versioning
curl http://localhost:8000/api/version/ \
  -H "X-API-Version: v1"

# Check deprecation headers
curl -I http://localhost:8000/api/v1/version/
```

## 📚 Examples

See [`scripts/example_api_versioning.py`](file://e:\Python\chatbot\scripts\example_api_versioning.py) for complete working examples:

- URL path versioning
- Header-based negotiation
- Version information queries
- Deprecation handling
- Version priority demonstration
- Changelog viewing

## 🚨 Error Responses

### Unsupported Version (400)

```json
{
  "error": {
    "code": "UNSUPPORTED_API_VERSION",
    "message": "API version 'v99' is not supported",
    "supported_versions": ["v1"],
    "latest_version": "v1",
    "documentation": "/api/docs"
  }
}
```

### Sunset Version (410)

```json
{
  "error": {
    "code": "API_VERSION_SUNSET",
    "message": "API version 'v1' has been retired",
    "sunset_date": "2027-06-30",
    "migration_guide": "https://docs.example.com/migrate-to-v2",
    "latest_version": "v2"
  }
}
```

### Minimum Version Required (400)

```json
{
  "error": {
    "code": "MINIMUM_VERSION_REQUIRED",
    "message": "This endpoint requires API version v2 or higher",
    "current_version": "v1",
    "minimum_version": "v2",
    "latest_version": "v2"
  }
}
```

## 📖 Related Documentation

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [REST API Versioning Best Practices](https://restfulapi.net/versioning/)
- [HTTP Deprecation Header RFC](https://tools.ietf.org/html/draft-dalal-deprecation-header-00)

---

**Last Updated:** 2026-04-19  
**Current API Version:** v1  
**Latest Version:** v1
