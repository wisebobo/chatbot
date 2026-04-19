"""
Test JWT Authentication System
Tests user registration, login, token refresh, and protected endpoints

Usage:
    python scripts/test_jwt_auth.py
"""
import requests
import time
from typing import Optional

BASE_URL = "http://localhost:8000/api/v1"


def print_section(title: str):
    """Print test section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_user_registration():
    """Test user registration endpoint"""
    print_section("Test 1: User Registration")
    
    # Test data with unique username
    import time
    timestamp = int(time.time())
    user_data = {
        "username": f"testuser_{timestamp}",
        "email": f"testuser_{timestamp}@example.com",
        "password": "SecurePass123!"
    }
    
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json=user_data
    )
    
    if response.status_code == 201:
        print("✅ PASS - User registration successful")
        tokens = response.json()
        print(f"   Username: {user_data['username']}")
        print(f"   Access Token: {tokens['access_token'][:50]}...")
        print(f"   Refresh Token: {tokens['refresh_token'][:50]}...")
        print(f"   Expires In: {tokens['expires_in']} seconds")
        return tokens, user_data['username']
    else:
        print(f"❌ FAIL - Status: {response.status_code}")
        print(f"   Response: {response.text}")
        return None, None


def test_duplicate_registration(username: str):
    """Test duplicate user registration"""
    print_section("Test 2: Duplicate Registration Prevention")
    
    user_data = {
        "username": username,
        "email": "another@example.com",
        "password": "AnotherPass123!"
    }
    
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json=user_data
    )
    
    if response.status_code == 400:
        print("✅ PASS - Duplicate username correctly rejected")
        print(f"   Error: {response.json().get('detail')}")
    else:
        print(f"❌ FAIL - Expected 400, got {response.status_code}")


def test_user_login(username: str):
    """Test user login endpoint"""
    print_section("Test 3: User Login")
    
    credentials = {
        "username": username,
        "password": "SecurePass123!"
    }
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json=credentials
    )
    
    if response.status_code == 200:
        print("✅ PASS - Login successful")
        tokens = response.json()
        print(f"   Access Token: {tokens['access_token'][:50]}...")
        print(f"   Token Type: {tokens['token_type']}")
        return tokens
    else:
        print(f"❌ FAIL - Status: {response.status_code}")
        print(f"   Response: {response.text}")
        return None


def test_invalid_login():
    """Test login with invalid credentials"""
    print_section("Test 4: Invalid Login Credentials")
    
    credentials = {
        "username": "newuser_test",
        "password": "WrongPassword!"
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
    print_section("Test 5: Get Current User Info")
    
    response = requests.get(
        f"{BASE_URL}/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    if response.status_code == 200:
        print("✅ PASS - Retrieved current user info")
        user_info = response.json()
        print(f"   Username: {user_info['username']}")
        print(f"   Email: {user_info['email']}")
        print(f"   Role: {user_info['role']}")
        print(f"   Active: {user_info['is_active']}")
    else:
        print(f"❌ FAIL - Status: {response.status_code}")
        print(f"   Response: {response.text}")


def test_token_refresh(refresh_token: str):
    """Test token refresh endpoint"""
    print_section("Test 6: Token Refresh")
    
    # Send as query parameter, not JSON body
    response = requests.post(
        f"{BASE_URL}/auth/refresh?refresh_token={refresh_token}"
    )
    
    if response.status_code == 200:
        print("✅ PASS - Token refresh successful")
        tokens = response.json()
        print(f"   New Access Token: {tokens['access_token'][:50]}...")
        print(f"   New Refresh Token: {tokens['refresh_token'][:50]}...")
        return tokens
    else:
        print(f"❌ FAIL - Status: {response.status_code}")
        print(f"   Response: {response.text}")
        return None


def test_list_users(admin_token: str):
    """Test listing all users (admin only)"""
    print_section("Test 7: List All Users (Admin)")
    
    response = requests.get(
        f"{BASE_URL}/auth/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    if response.status_code == 200:
        print("✅ PASS - Retrieved user list")
        users = response.json()
        print(f"   Total Users: {len(users)}")
        for user in users:
            print(f"   - {user['username']} ({user['role']})")
    else:
        print(f"❌ FAIL - Status: {response.status_code}")
        print(f"   Response: {response.text}")


def test_access_protected_endpoint_without_token():
    """Test accessing protected endpoint without token"""
    print_section("Test 8: Protected Endpoint Without Token")
    
    response = requests.get(f"{BASE_URL}/auth/me")
    
    if response.status_code == 401:
        print("✅ PASS - Protected endpoint correctly requires authentication")
        print(f"   Error: {response.json().get('detail')}")
    else:
        print(f"❌ FAIL - Expected 401, got {response.status_code}")


def test_admin_operations_with_regular_user(user_token: str):
    """Test admin-only operations with regular user token"""
    print_section("Test 9: Admin Operations with Regular User")
    
    response = requests.get(
        f"{BASE_URL}/auth/users",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    if response.status_code == 403:
        print("✅ PASS - Admin operation correctly denied for regular user")
        print(f"   Error: {response.json().get('detail')}")
    else:
        print(f"❌ FAIL - Expected 403, got {response.status_code}")


def test_default_admin_login():
    """Test login with default admin credentials"""
    print_section("Test 10: Default Admin Login")
    
    credentials = {
        "username": "admin",
        "password": "admin123456"
    }
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json=credentials
    )
    
    if response.status_code == 200:
        print("✅ PASS - Default admin login successful")
        tokens = response.json()
        print(f"   Admin Token: {tokens['access_token'][:50]}...")
        return tokens
    else:
        print(f"❌ FAIL - Status: {response.status_code}")
        print(f"   Response: {response.text}")
        return None


def main():
    print("=" * 70)
    print("  JWT Authentication Test Suite")
    print("=" * 70)
    print("\nMake sure the FastAPI server is running:")
    print("  cd e:\\Python\\chatbot")
    print("  uvicorn app.api.main:app --reload --port 8000")
    print("=" * 70)
    
    input("\nPress Enter to start tests (or Ctrl+C to cancel)...")
    
    try:
        # Test registration
        reg_tokens, username = test_user_registration()
        if not reg_tokens:
            print("\n⚠️  Skipping remaining tests due to registration failure")
            return
        
        # Test duplicate registration
        test_duplicate_registration(username)
        
        # Test login
        login_tokens = test_user_login(username)
        if not login_tokens:
            print("\n⚠️  Skipping remaining tests due to login failure")
            return
        
        access_token = login_tokens['access_token']
        refresh_token = login_tokens['refresh_token']
        
        # Test invalid login
        test_invalid_login()
        
        # Test get current user
        test_get_current_user(access_token)
        
        # Test token refresh
        new_tokens = test_token_refresh(refresh_token)
        
        # Test protected endpoint without token
        test_access_protected_endpoint_without_token()
        
        # Test admin login
        admin_tokens = test_default_admin_login()
        if admin_tokens:
            admin_token = admin_tokens['access_token']
            
            # Test list users (admin)
            test_list_users(admin_token)
            
            # Test admin operations with regular user
            test_admin_operations_with_regular_user(access_token)
        
        print("\n" + "=" * 70)
        print("✅ All JWT authentication tests completed!")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests cancelled by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
