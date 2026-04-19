"""
Test Wiki Feedback API endpoints
Tests the complete feedback loop: submit feedback → confidence recalculation → statistics
"""
import requests
import json
from typing import Optional

# API Configuration
BASE_URL = "http://localhost:8000/api/v1"


def test_submit_feedback(entry_id: str, is_positive: bool, comment: Optional[str] = None):
    """
    Test submitting feedback to a wiki article
    
    Args:
        entry_id: Article entry_id
        is_positive: True for thumbs up, False for thumbs down
        comment: Optional user comment
        
    Returns:
        Response JSON or error message
    """
    url = f"{BASE_URL}/wiki/feedback"
    
    payload = {
        "entry_id": entry_id,
        "is_positive": is_positive,
        "comment": comment
    }
    
    print(f"\n📤 Submitting {'positive' if is_positive else 'negative'} feedback...")
    print(f"   Entry ID: {entry_id}")
    print(f"   Comment: {comment or '(none)'}")
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ Success!")
        print(f"   Updated Confidence: {result['feedback_summary']['updated_confidence']}")
        print(f"   Total Feedback: {result['feedback_summary']['total']}")
        print(f"   Positive/Negative: {result['feedback_summary']['positive']}/{result['feedback_summary']['negative']}")
        
        return result
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        print(f"   Response: {e.response.text}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_get_feedback_stats(entry_id: str):
    """
    Test getting feedback statistics for a wiki article
    
    Args:
        entry_id: Article entry_id
        
    Returns:
        Statistics JSON or error message
    """
    url = f"{BASE_URL}/wiki/{entry_id}/feedback"
    
    print(f"\n📊 Fetching feedback statistics...")
    print(f"   Entry ID: {entry_id}")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        stats = response.json()
        print(f"✅ Success!")
        print(f"   Title: {stats['title']}")
        print(f"   Version: {stats['version']}")
        print(f"   Current Confidence: {stats['confidence']['current']}")
        print(f"   Feedback Ratio: {stats['confidence']['feedback_ratio']}")
        print(f"   Total Feedback: {stats['feedback']['total']}")
        print(f"   Positive: {stats['feedback']['positive']}")
        print(f"   Negative: {stats['feedback']['negative']}")
        if stats['feedback']['comments']:
            print(f"   Recent Comments:")
            for comment in stats['feedback']['comments']:
                print(f"      - {comment}")
        
        return stats
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        print(f"   Response: {e.response.text}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_feedback_loop_scenario():
    """
    Test complete feedback loop scenario
    
    Simulates multiple users providing feedback and observes confidence changes
    """
    print("=" * 80)
    print("Wiki Feedback API - Complete Test Scenario")
    print("=" * 80)
    
    # Use a known article entry_id (from example script)
    entry_id = "conc_loan_prime_rate"
    
    print(f"\n🎯 Testing with article: {entry_id}")
    print("-" * 80)
    
    # Step 1: Get initial stats
    print("\n[Step 1] Getting initial feedback statistics...")
    initial_stats = test_get_feedback_stats(entry_id)
    
    if not initial_stats:
        print("\n⚠️  Article not found. Please run example_enhanced_wiki_compiler.py first.")
        return
    
    initial_confidence = initial_stats['confidence']['current']
    print(f"\n📈 Initial Confidence: {initial_confidence}")
    
    # Step 2: Submit positive feedback
    print("\n" + "=" * 80)
    print("[Step 2] User 1 submits POSITIVE feedback")
    print("=" * 80)
    test_submit_feedback(
        entry_id=entry_id,
        is_positive=True,
        comment="Very helpful explanation!"
    )
    
    # Step 3: Submit another positive feedback
    print("\n" + "=" * 80)
    print("[Step 3] User 2 submits POSITIVE feedback")
    print("=" * 80)
    test_submit_feedback(
        entry_id=entry_id,
        is_positive=True,
        comment="Clear and concise"
    )
    
    # Step 4: Submit negative feedback
    print("\n" + "=" * 80)
    print("[Step 4] User 3 submits NEGATIVE feedback")
    print("=" * 80)
    test_submit_feedback(
        entry_id=entry_id,
        is_positive=False,
        comment="Needs more recent data"
    )
    
    # Step 5: Get final stats
    print("\n" + "=" * 80)
    print("[Step 5] Getting final feedback statistics")
    print("=" * 80)
    final_stats = test_get_feedback_stats(entry_id)
    
    if final_stats:
        final_confidence = final_stats['confidence']['current']
        confidence_change = final_confidence - initial_confidence
        
        print("\n" + "=" * 80)
        print("📊 FEEDBACK LOOP SUMMARY")
        print("=" * 80)
        print(f"Initial Confidence:  {initial_confidence:.3f}")
        print(f"Final Confidence:    {final_confidence:.3f}")
        print(f"Change:              {confidence_change:+.3f} ({'↑' if confidence_change > 0 else '↓'})")
        print(f"Total Feedback:      {final_stats['feedback']['total']}")
        print(f"Positive/Negative:   {final_stats['feedback']['positive']}/{final_stats['feedback']['negative']}")
        
        # Verify confidence formula
        total = final_stats['feedback']['total']
        if total > 0:
            feedback_ratio = final_stats['feedback']['positive'] / total
            expected_confidence = 0.7 * initial_confidence + 0.3 * feedback_ratio
            print(f"\n🔍 Formula Verification:")
            print(f"   Feedback Ratio: {feedback_ratio:.3f}")
            print(f"   Expected: 0.7 × {initial_confidence:.3f} + 0.3 × {feedback_ratio:.3f} = {expected_confidence:.3f}")
            print(f"   Actual:   {final_confidence:.3f}")
            print(f"   Match:    {'✅ Yes' if abs(expected_confidence - final_confidence) < 0.01 else '❌ No'}")
    
    print("\n" + "=" * 80)
    print("✅ Test completed successfully!")
    print("=" * 80)


def test_error_cases():
    """Test error handling"""
    print("\n" + "=" * 80)
    print("Testing Error Cases")
    print("=" * 80)
    
    # Test 1: Non-existent article
    print("\n[Test 1] Submitting feedback to non-existent article...")
    result = test_submit_feedback(
        entry_id="non_existent_article",
        is_positive=True,
        comment="Test"
    )
    if result is None:
        print("✅ Correctly returned error for non-existent article")
    
    # Test 2: Get stats for non-existent article
    print("\n[Test 2] Getting stats for non-existent article...")
    result = test_get_feedback_stats("non_existent_article")
    if result is None:
        print("✅ Correctly returned error for non-existent article")


if __name__ == "__main__":
    import sys
    
    print("\n🧪 Wiki Feedback API Test Suite")
    print("=" * 80)
    print("Make sure the FastAPI server is running:")
    print("  cd e:\\Python\\chatbot")
    print("  uvicorn app.api.main:app --reload --port 8000")
    print("=" * 80)
    
    input("\nPress Enter to start tests (or Ctrl+C to cancel)...")
    
    try:
        # Run main scenario
        test_feedback_loop_scenario()
        
        # Run error cases
        test_error_cases()
        
        print("\n🎉 All tests completed!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
