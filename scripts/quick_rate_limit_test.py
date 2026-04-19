"""
Quick test for rate limiting
"""
import requests
import time

BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "sk-test-key-12345"

print("Testing rate limiting on /wiki/feedback endpoint (limit: 10/min)...")
print("=" * 70)

success_count = 0
rate_limited_count = 0

for i in range(15):
    response = requests.post(
        f"{BASE_URL}/wiki/feedback",
        json={
            "entry_id": "conc_loan_prime_rate",
            "is_positive": True,
            "comment": f"Test {i+1}"
        },
        headers={"X-API-Key": API_KEY}
    )
    
    if response.status_code == 429:
        rate_limited_count += 1
        print(f"Request {i+1}: ❌ Rate limited (429)")
        if rate_limited_count == 1:
            retry_after = response.headers.get('Retry-After', 'unknown')
            print(f"   Retry-After: {retry_after} seconds")
    elif response.status_code == 200:
        success_count += 1
        print(f"Request {i+1}: ✅ Success (200)")
    else:
        print(f"Request {i+1}: ⚠️  Status {response.status_code}")
    
    time.sleep(0.2)  # Small delay

print("\n" + "=" * 70)
print(f"Results:")
print(f"  Successful: {success_count}")
print(f"  Rate Limited: {rate_limited_count}")

if rate_limited_count > 0:
    print("\n✅ Rate limiting is WORKING!")
else:
    print("\n⚠️  Rate limiting may not be working correctly")
