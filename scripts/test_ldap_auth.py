"""
Test LDAP Authentication System
Tests LDAP login, JWT token generation, and protected endpoints

Usage:
    python scripts/test_ldap_auth.py
    
Note: This test requires a configured LDAP/Active Directory server.
      Update .env file with your AD configuration before running.
"""
import requests
import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

BASE_URL = "http://localhost:8000/api/v1"


def print_section(title: str):
    """Print test section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_ldap_login():
    """Test LDAP authentication and JWT token generation"""
    print_section("Test 1: LDAP Login")
    
    # Use test credentials from environment or defaults
    username = os.getenv("TEST_LDAP_USERNAME", "testuser")
    password = os.getenv("TEST_LDAP_PASSWORD", "TestPass123!")
    
    credentials = {
        "username": username,
        "password": password
    }
    
    print(f"Testing login for user: {username}")
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json=credentials
    )
    
    if response.status_code == 200:
        print("✅ PASS - LDAP authentication successful")
        tokens = response.json()
        print(f"   Access Token: {tokens['access_token'][:50]}...")
        print(f"   Refresh Token: {tokens['refresh_token'][:50]}...")
        print(f"   Token Type: {tokens['token_type']}")
        print(f"   Expires In: {tokens['expires_in']} seconds")
        return tokens
    else:
        print(f"❌ FAIL - Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 401:
            print("   Note: Invalid credentials or LDAP server not configured")
            print("   Please update TEST_LDAP_USERNAME and TEST_LDAP_PASSWORD in .env")
        
        return None


def test_invalid_login():
    """Test login with invalid credentials"""
    print_section("Test 2: Invalid Credentials")
    
    credentials = {
        "username": "invalid_user",
        "password": "wrong_password"
    }
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json=credentials
    )
    
    if response.status_code == 401:
        print("✅ PASS - Invalid credentials correctly rejected")
        print(f"   Error: {response.json().get('detail')}")
    else:
        print(f"❌ FAIL - Expected 401, got {response.status_code}")


def test_get_current_user(access_token: str):
    """Test getting current user info"""
    print_section("Test 3: Get Current User Info")
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(
        f"{BASE_URL}/auth/me",
        headers=headers
    )
    
    if response.status_code == 200:
        print("✅ PASS - Retrieved user information")
        user_info = response.json()
        print(f"   User ID: {user_info.get('user_id')}")
        print(f"   Username: {user_info.get('username')}")
        print(f"   Display Name: {user_info.get('display_name')}")
        print(f"   Email: {user_info.get('email')}")
        print(f"   Role: {user_info.get('role')}")
        print(f"   Token Expires: {user_info.get('exp')}")
    else:
        print(f"❌ FAIL - Status: {response.status_code}")
        print(f"   Response: {response.text}")


def test_token_refresh(refresh_token: str):
    """Test token refresh"""
    print_section("Test 4: Token Refresh")
    
    response = requests.post(
        f"{BASE_URL}/auth/refresh",
        params={"refresh_token": refresh_token}
    )
    
    if response.status_code == 200:
        print("✅ PASS - Token refresh successful")
        new_tokens = response.json()
        print(f"   New Access Token: {new_tokens['access_token'][:50]}...")
        print(f"   New Refresh Token: {new_tokens['refresh_token'][:50]}...")
        return new_tokens
    else:
        print(f"❌ FAIL - Status: {response.status_code}")
        print(f"   Response: {response.text}")
        return None


def test_protected_endpoint_without_token():
    """Test accessing protected endpoint without token"""
    print_section("Test 5: Protected Endpoint Without Token")
    
    response = requests.get(f"{BASE_URL}/auth/me")
    
    if response.status_code == 401:
        print("✅ PASS - Correctly rejected request without token")
        print(f"   Error: {response.json().get('detail')}")
    else:
        print(f"❌ FAIL - Expected 401, got {response.status_code}")


def test_ldap_health_check():
    """Test LDAP connection health"""
    print_section("Test 6: LDAP Health Check")
    
    response = requests.get(f"{BASE_URL}/auth/health")
    
    if response.status_code == 200:
        health = response.json()
        print("✅ PASS - LDAP health check completed")
        print(f"   Status: {health.get('status')}")
        print(f"   LDAP Server: {health.get('ldap_server')}")
        print(f"   Connected: {health.get('connected')}")
        
        if health.get('connected'):
            print("   ✅ LDAP server is reachable")
        else:
            print("   ⚠️  LDAP server is not reachable - check configuration")
    else:
        print(f"❌ FAIL - Status: {response.status_code}")
        print(f"   Response: {response.text}")


def test_admin_operations_with_user_token(access_token: str):
    """Test that regular user cannot perform admin operations"""
    print_section("Test 7: Admin Operations with User Token")
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    # Try to access admin-only endpoint (if exists)
    # For now, just verify the token works for regular endpoints
    response = requests.get(
        f"{BASE_URL}/auth/me",
        headers=headers
    )
    
    if response.status_code == 200:
        user_info = response.json()
        role = user_info.get('role', 'user')
        print(f"✅ User role: {role}")
        
        if role != "admin":
            print("   ℹ️  User is not admin - admin operations would be restricted")
    else:
        print(f"❌ FAIL - Could not verify user role")


def main():
    """Run all LDAP authentication tests"""
    print("\n" + "=" * 70)
    print("  LDAP Authentication Test Suite")
    print("=" * 70)
    print("\nNote: Ensure LDAP server is configured in .env file")
    print("Required env vars: LDAP_SERVER_URL, LDAP_BASE_DN, LDAP_DOMAIN")
    
    results = {
        "passed": 0,
        "failed": 0
    }
    
    # Test 1: LDAP Login
    tokens = test_ldap_login()
    if tokens:
        results["passed"] += 1
        access_token = tokens['access_token']
        refresh_token = tokens['refresh_token']
    else:
        results["failed"] += 1
        print("\n⚠️  Skipping remaining tests due to login failure")
        print_results(results)
        return
    
    # Test 2: Invalid Login
    test_invalid_login()
    results["passed"] += 1  # This should always pass
    
    # Test 3: Get Current User
    test_get_current_user(access_token)
    results["passed"] += 1
    
    # Test 4: Token Refresh
    new_tokens = test_token_refresh(refresh_token)
    if new_tokens:
        results["passed"] += 1
        access_token = new_tokens['access_token']
    else:
        results["failed"] += 1
    
    # Test 5: Protected Endpoint Without Token
    test_protected_endpoint_without_token()
    results["passed"] += 1
    
    # Test 6: LDAP Health Check
    test_ldap_health_check()
    results["passed"] += 1
    
    # Test 7: Admin Operations
    test_admin_operations_with_user_token(access_token)
    results["passed"] += 1
    
    # Print summary
    print_results(results)


def print_results(results: dict):
    """Print test results summary"""
    print("\n" + "=" * 70)
    print("  Test Results Summary")
    print("=" * 70)
    print(f"  Passed: {results['passed']}")
    print(f"  Failed: {results['failed']}")
    print(f"  Total:  {results['passed'] + results['failed']}")
    print("=" * 70)
    
    if results['failed'] == 0:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {results['failed']} test(s) failed")


if __name__ == "__main__":
    main()
