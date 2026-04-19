"""
Test API Authentication and Rate Limiting
Tests the Phase 1 security features

Usage:
    python scripts/test_auth_and_rate_limit.py
"""
import requests
import time
from typing import List, Tuple

BASE_URL = "http://localhost:8000/api/v1"

# Test API keys (should match those in auth.py or .env)
VALID_ADMIN_KEY = "sk-test-key-12345"
VALID_USER_KEY = "sk-user-key-67890"
INVALID_KEY = "sk-invalid-key-99999"


def test_health_endpoint_no_auth():
    """Test that health endpoint works without authentication"""
    print("\n[Test 1] Health endpoint (no auth required)")
    print("-" * 60)
    
    response = requests.get(f"{BASE_URL}/health")
    
    if response.status_code == 200:
        print("✅ PASS - Health endpoint accessible without auth")
        print(f"   Status: {response.json()['status']}")
    else:
        print(f"❌ FAIL - Status code: {response.status_code}")
        print(f"   Response: {response.text}")


def test_chat_without_api_key():
    """Test that chat endpoint requires API key"""
    print("\n[Test 2] Chat endpoint without API key")
    print("-" * 60)
    
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"message": "Hello"}
    )
    
    if response.status_code == 401:
        print("✅ PASS - Chat endpoint correctly requires API key")
        print(f"   Error: {response.json().get('detail')}")
    else:
        print(f"❌ FAIL - Expected 401, got {response.status_code}")
        print(f"   Response: {response.text}")


def test_chat_with_valid_api_key():
    """Test chat endpoint with valid API key"""
    print("\n[Test 3] Chat endpoint with valid API key")
    print("-" * 60)
    
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"message": "Hello"},
        headers={"X-API-Key": VALID_ADMIN_KEY}
    )
    
    # Should not get 401 (might get other errors due to LLM config)
    if response.status_code != 401:
        print("✅ PASS - Chat endpoint accepts valid API key")
        print(f"   Status: {response.status_code}")
    else:
        print(f"❌ FAIL - Valid API key rejected")
        print(f"   Error: {response.json().get('detail')}")


def test_chat_with_invalid_api_key():
    """Test chat endpoint with invalid API key"""
    print("\n[Test 4] Chat endpoint with invalid API key")
    print("-" * 60)
    
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"message": "Hello"},
        headers={"X-API-Key": INVALID_KEY}
    )
    
    if response.status_code == 401:
        print("✅ PASS - Invalid API key correctly rejected")
        print(f"   Error: {response.json().get('detail')}")
    else:
        print(f"❌ FAIL - Expected 401, got {response.status_code}")


def test_wiki_feedback_requires_auth():
    """Test that wiki feedback requires authentication"""
    print("\n[Test 5] Wiki feedback without API key")
    print("-" * 60)
    
    response = requests.post(
        f"{BASE_URL}/wiki/feedback",
        json={
            "entry_id": "test_article",
            "is_positive": True
        }
    )
    
    if response.status_code == 401:
        print("✅ PASS - Wiki feedback correctly requires API key")
        print(f"   Error: {response.json().get('detail')}")
    else:
        print(f"❌ FAIL - Expected 401, got {response.status_code}")


def test_wiki_feedback_with_auth():
    """Test wiki feedback with valid API key"""
    print("\n[Test 6] Wiki feedback with valid API key")
    print("-" * 60)
    
    response = requests.post(
        f"{BASE_URL}/wiki/feedback",
        json={
            "entry_id": "conc_loan_prime_rate",
            "is_positive": True,
            "comment": "Testing authentication"
        },
        headers={"X-API-Key": VALID_USER_KEY}
    )
    
    if response.status_code in [200, 404]:  # 404 is OK if article doesn't exist
        print("✅ PASS - Wiki feedback accepts valid API key")
        if response.status_code == 200:
            print(f"   Feedback recorded successfully")
        else:
            print(f"   Article not found (expected): {response.json().get('detail')}")
    else:
        print(f"❌ FAIL - Unexpected status: {response.status_code}")
        print(f"   Response: {response.text}")


def test_wiki_stats_optional_auth():
    """Test that wiki stats endpoint allows optional auth"""
    print("\n[Test 7] Wiki stats with optional auth")
    print("-" * 60)
    
    # Without auth
    response_anon = requests.get(
        f"{BASE_URL}/wiki/conc_loan_prime_rate/feedback"
    )
    
    # With auth
    response_auth = requests.get(
        f"{BASE_URL}/wiki/conc_loan_prime_rate/feedback",
        headers={"X-API-Key": VALID_USER_KEY}
    )
    
    if response_anon.status_code == 200 and response_auth.status_code == 200:
        print("✅ PASS - Wiki stats accessible with and without auth")
        print(f"   Anonymous: {response_anon.status_code}")
        print(f"   Authenticated: {response_auth.status_code}")
    else:
        print(f"❌ FAIL - One or both requests failed")
        print(f"   Anonymous: {response_anon.status_code}")
        print(f"   Authenticated: {response_auth.status_code}")


def test_rate_limiting():
    """Test rate limiting on chat endpoint"""
    print("\n[Test 8] Rate limiting test (this may take ~30 seconds)")
    print("-" * 60)
    print("Sending rapid requests to test rate limiting...")
    
    success_count = 0
    rate_limited_count = 0
    
    # Send 35 requests (limit is 30/minute)
    for i in range(35):
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"message": f"Test message {i}"},
            headers={"X-API-Key": VALID_ADMIN_KEY}
        )
        
        if response.status_code == 429:  # Too Many Requests
            rate_limited_count += 1
            if rate_limited_count == 1:
                print(f"   ✅ Rate limit triggered after {i+1} requests")
        elif response.status_code != 401:  # Ignore auth errors
            success_count += 1
        
        # Small delay to avoid overwhelming the server
        time.sleep(0.1)
    
    print(f"\nResults:")
    print(f"   Successful requests: {success_count}")
    print(f"   Rate limited: {rate_limited_count}")
    
    if rate_limited_count > 0:
        print("✅ PASS - Rate limiting is working")
    else:
        print("⚠️  WARNING - Rate limiting may not be working as expected")


def main():
    print("=" * 80)
    print("API Authentication & Rate Limiting Test Suite")
    print("=" * 80)
    print("\nMake sure the FastAPI server is running:")
    print("  cd e:\\Python\\chatbot")
    print("  uvicorn app.api.main:app --reload --port 8000")
    print("=" * 80)
    
    input("\nPress Enter to start tests (or Ctrl+C to cancel)...")
    
    try:
        # Run all tests
        test_health_endpoint_no_auth()
        test_chat_without_api_key()
        test_chat_with_valid_api_key()
        test_chat_with_invalid_api_key()
        test_wiki_feedback_requires_auth()
        test_wiki_feedback_with_auth()
        test_wiki_stats_optional_auth()
        test_rate_limiting()
        
        print("\n" + "=" * 80)
        print("✅ All tests completed!")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests cancelled by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
