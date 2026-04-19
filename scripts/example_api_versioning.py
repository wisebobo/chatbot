#!/usr/bin/env python3
"""
API Versioning Examples

Demonstrates how to use API versioning features including:
- URL path versioning
- Header-based version negotiation
- Checking version information
- Handling deprecation warnings
"""
import requests
import json


BASE_URL = "http://localhost:8000/api"


def example_1_url_path_versioning():
    """Example 1: Using URL path for version specification"""
    print("="*70)
    print("Example 1: URL Path Versioning")
    print("="*70)
    
    # v1 endpoint
    print("\n📌 Request to /api/v1/version/")
    try:
        response = requests.get(f"{BASE_URL}/v1/version/")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Unsupported version
    print("\n📌 Request to unsupported /api/v99/version/")
    try:
        response = requests.get(f"{BASE_URL}/v99/version/")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")


def example_2_header_versioning():
    """Example 2: Using headers for version specification"""
    print("\n" + "="*70)
    print("Example 2: Header-Based Version Negotiation")
    print("="*70)
    
    # Using Accept header
    print("\n📌 Using Accept: application/vnd.api.v1+json")
    try:
        response = requests.get(
            f"{BASE_URL}/v1/version/",
            headers={"Accept": "application/vnd.api.v1+json"}
        )
        print(f"Status: {response.status_code}")
        print(f"X-API-Version: {response.headers.get('X-API-Version')}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Using custom X-API-Version header
    print("\n📌 Using X-API-Version: v1")
    try:
        response = requests.get(
            f"{BASE_URL}/version/",  # No version in URL
            headers={"X-API-Version": "v1"}
        )
        print(f"Status: {response.status_code}")
        print(f"X-API-Version: {response.headers.get('X-API-Version')}")
    except Exception as e:
        print(f"Error: {e}")


def example_3_check_version_info():
    """Example 3: Checking API version information"""
    print("\n" + "="*70)
    print("Example 3: Checking Version Information")
    print("="*70)
    
    # Get current version info
    print("\n📌 Get current version information")
    try:
        response = requests.get(f"{BASE_URL}/v1/version/")
        data = response.json()
        print(f"Current Version: {data['current_version']['version']}")
        print(f"Latest Version: {data['latest_version']}")
        print(f"Upgrade Available: {data['upgrade_available']}")
        print(f"Deprecated: {data['deprecation_warning']}")
    except Exception as e:
        print(f"Error: {e}")
    
    # List all supported versions
    print("\n📌 List all supported versions")
    try:
        response = requests.get(f"{BASE_URL}/v1/version/supported")
        data = response.json()
        print(f"Default Version: {data['default_version']}")
        print(f"Latest Version: {data['latest_version']}")
        print(f"\nSupported Versions:")
        for ver, info in data['versions'].items():
            print(f"  - {ver}: Released {info['release_date']}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Get specific version details
    print("\n📌 Get details for v1")
    try:
        response = requests.get(f"{BASE_URL}/v1/version/v1")
        data = response.json()
        print(f"Version: {data['version']['version']}")
        print(f"Release Date: {data['version']['release_date']}")
        print(f"Changes:")
        for change in data['version']['changes']:
            print(f"  • {change}")
    except Exception as e:
        print(f"Error: {e}")


def example_4_deprecation_handling():
    """Example 4: Handling deprecation warnings"""
    print("\n" + "="*70)
    print("Example 4: Deprecation Warning Handling")
    print("="*70)
    
    print("\n📌 Check response headers for deprecation info")
    try:
        response = requests.get(f"{BASE_URL}/v1/version/")
        
        print(f"X-API-Version: {response.headers.get('X-API-Version')}")
        print(f"X-API-Latest-Version: {response.headers.get('X-API-Latest-Version')}")
        
        if 'Deprecation' in response.headers:
            print(f"⚠️  DEPRECATION WARNING: {response.headers['Deprecation']}")
            print(f"Sunset Date: {response.headers.get('Sunset', 'N/A')}")
            if 'Link' in response.headers:
                print(f"Migration Guide: {response.headers['Link']}")
        else:
            print("✅ No deprecation warnings")
    except Exception as e:
        print(f"Error: {e}")


def example_5_version_comparison():
    """Example 5: Comparing different version approaches"""
    print("\n" + "="*70)
    print("Example 5: Version Priority Demonstration")
    print("="*70)
    
    print("\nPriority Order (highest to lowest):")
    print("  1. URL Path: /api/v1/...")
    print("  2. Accept Header: application/vnd.api.v1+json")
    print("  3. Custom Header: X-API-Version: v1")
    print("  4. Default: v1")
    
    print("\n📌 Test: URL path overrides Accept header")
    try:
        # URL says v1, Accept says v2 - URL should win
        response = requests.get(
            f"{BASE_URL}/v1/version/",
            headers={"Accept": "application/vnd.api.v2+json"}
        )
        actual_version = response.headers.get('X-API-Version')
        print(f"URL: /api/v1/, Accept: v2 → Actual: {actual_version}")
        assert actual_version == "v1", "URL path should take priority"
        print("✅ URL path correctly took priority")
    except Exception as e:
        print(f"Error: {e}")


def example_6_changelog():
    """Example 6: Viewing API changelog"""
    print("\n" + "="*70)
    print("Example 6: API Changelog")
    print("="*70)
    
    try:
        response = requests.get(f"{BASE_URL}/v1/version/changelog")
        data = response.json()
        
        print(f"Total Versions: {data['total_versions']}")
        print(f"Latest Version: {data['latest_version']}\n")
        
        for entry in data['changelog']:
            print(f"Version {entry['version']} ({entry['release_date']})")
            print(f"  Status: {entry['status']}")
            print(f"  Changes:")
            for change in entry['changes']:
                print(f"    • {change}")
            print()
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Run all examples"""
    print("\n🚀 API Versioning Examples")
    print("Make sure the server is running on http://localhost:8000\n")
    
    try:
        example_1_url_path_versioning()
        example_2_header_versioning()
        example_3_check_version_info()
        example_4_deprecation_handling()
        example_5_version_comparison()
        example_6_changelog()
        
        print("\n" + "="*70)
        print("✅ All examples completed!")
        print("="*70)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to server")
        print("Please start the server first: python main.py")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
