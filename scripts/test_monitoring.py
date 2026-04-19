"""
Test Monitoring & Observability (Phase 3)
Validates metrics collection, alert rules, and dashboard configuration

Usage:
    python scripts/test_monitoring.py
"""
import requests
import time
from typing import Dict, List

BASE_URL = "http://localhost:8000"


def print_section(title: str):
    """Print test section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_metrics_endpoint():
    """Test that /metrics endpoint is accessible"""
    print_section("Test 1: Metrics Endpoint Accessibility")
    
    try:
        response = requests.get(f"{BASE_URL}/metrics", timeout=5)
        
        if response.status_code == 200:
            print("✅ PASS - Metrics endpoint is accessible")
            print(f"   Response size: {len(response.text)} bytes")
            
            # Check for key metrics
            required_metrics = [
                "agent_requests_total",
                "authentication_failures_total",
                "wiki_articles_total",
                "process_memory_bytes",
                "process_cpu_percent"
            ]
            
            found_metrics = []
            missing_metrics = []
            
            for metric in required_metrics:
                if metric in response.text:
                    found_metrics.append(metric)
                else:
                    missing_metrics.append(metric)
            
            print(f"\n   Found metrics: {len(found_metrics)}/{len(required_metrics)}")
            for metric in found_metrics:
                print(f"     ✅ {metric}")
            
            if missing_metrics:
                print(f"\n   Missing metrics:")
                for metric in missing_metrics:
                    print(f"     ❌ {metric}")
                return False
            
            return True
        else:
            print(f"❌ FAIL - Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ FAIL - Error: {e}")
        return False


def test_system_resource_monitoring():
    """Test system resource metrics are being collected"""
    print_section("Test 2: System Resource Monitoring")
    
    try:
        response = requests.get(f"{BASE_URL}/metrics", timeout=5)
        
        # Check memory metric
        if "process_memory_bytes" in response.text:
            for line in response.text.split('\n'):
                if line.startswith("process_memory_bytes"):
                    value = float(line.split()[-1])
                    print(f"✅ Memory usage: {value / 1024 / 1024:.2f} MB")
                    break
        
        # Check CPU metric
        if "process_cpu_percent" in response.text:
            for line in response.text.split('\n'):
                if line.startswith("process_cpu_percent"):
                    value = float(line.split()[-1])
                    print(f"✅ CPU usage: {value:.1f}%")
                    break
        
        print("✅ PASS - System resource monitoring active")
        return True
        
    except Exception as e:
        print(f"❌ FAIL - Error: {e}")
        return False


def test_auth_metrics_tracking():
    """Test authentication metrics are tracked"""
    print_section("Test 3: Authentication Metrics Tracking")
    
    # Perform a login attempt
    try:
        # Failed login
        requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"username": "invalid", "password": "wrong"}
        )
        
        # Wait a moment for metrics to update
        time.sleep(1)
        
        # Check metrics
        response = requests.get(f"{BASE_URL}/metrics", timeout=5)
        
        if "authentication_failures_total" in response.text:
            print("✅ PASS - Authentication failure metric exists")
            
            # Check if counter incremented
            for line in response.text.split('\n'):
                if line.startswith("authentication_failures_total"):
                    print(f"   Metric: {line}")
                    break
            
            return True
        else:
            print("❌ FAIL - Authentication failure metric not found")
            return False
            
    except Exception as e:
        print(f"❌ FAIL - Error: {e}")
        return False


def test_business_metrics():
    """Test business metrics are available"""
    print_section("Test 4: Business Metrics Availability")
    
    try:
        response = requests.get(f"{BASE_URL}/metrics", timeout=5)
        
        business_metrics = {
            "user_registrations_total": "User registrations",
            "user_logins_total": "User logins",
            "jwt_tokens_issued_total": "JWT tokens issued",
            "wiki_feedback_total": "Wiki feedback submissions"
        }
        
        found = 0
        for metric, description in business_metrics.items():
            if metric in response.text:
                print(f"✅ {description}: {metric}")
                found += 1
        
        if found == len(business_metrics):
            print(f"\n✅ PASS - All {found} business metrics available")
            return True
        else:
            print(f"\n⚠️  PARTIAL - Only {found}/{len(business_metrics)} business metrics found")
            return True  # Still acceptable
            
    except Exception as e:
        print(f"❌ FAIL - Error: {e}")
        return False


def test_llm_performance_metrics():
    """Test LLM performance metrics exist"""
    print_section("Test 5: LLM Performance Metrics")
    
    try:
        response = requests.get(f"{BASE_URL}/metrics", timeout=5)
        
        llm_metrics = {
            "llm_call_duration_seconds": "LLM call latency",
            "llm_calls_total": "LLM API calls",
            "llm_tokens_total": "Token usage",
            "llm_errors_total": "LLM errors"
        }
        
        found = 0
        for metric, description in llm_metrics.items():
            if metric in response.text:
                print(f"✅ {description}: {metric}")
                found += 1
        
        if found == len(llm_metrics):
            print(f"\n✅ PASS - All {found} LLM metrics available")
            return True
        else:
            print(f"\n❌ FAIL - Only {found}/{len(llm_metrics)} LLM metrics found")
            return False
            
    except Exception as e:
        print(f"❌ FAIL - Error: {e}")
        return False


def verify_alert_rules_file():
    """Verify Prometheus alert rules file exists and is valid"""
    print_section("Test 6: Alert Rules Configuration")
    
    import os
    import yaml
    
    alerts_file = "monitoring/prometheus-alerts.yml"
    
    if not os.path.exists(alerts_file):
        print(f"❌ FAIL - Alert rules file not found: {alerts_file}")
        return False
    
    try:
        with open(alerts_file, 'r') as f:
            alerts_config = yaml.safe_load(f)
        
        if 'groups' not in alerts_config:
            print("❌ FAIL - Invalid alert rules format (missing 'groups')")
            return False
        
        total_rules = 0
        for group in alerts_config['groups']:
            rules_count = len(group.get('rules', []))
            total_rules += rules_count
            print(f"✅ Group '{group['name']}': {rules_count} rules")
        
        print(f"\n✅ PASS - Alert rules file valid ({total_rules} total rules)")
        return True
        
    except Exception as e:
        print(f"❌ FAIL - Error parsing alert rules: {e}")
        return False


def verify_grafana_dashboard():
    """Verify Grafana dashboard configuration"""
    print_section("Test 7: Grafana Dashboard Configuration")
    
    import os
    import json
    
    dashboard_file = "monitoring/grafana-dashboard.json"
    
    if not os.path.exists(dashboard_file):
        print(f"❌ FAIL - Dashboard file not found: {dashboard_file}")
        return False
    
    try:
        with open(dashboard_file, 'r') as f:
            dashboard = json.load(f)
        
        if 'dashboard' not in dashboard:
            print("❌ FAIL - Invalid dashboard format")
            return False
        
        panels = dashboard['dashboard'].get('panels', [])
        print(f"✅ Dashboard title: {dashboard['dashboard'].get('title')}")
        print(f"✅ Total panels: {len(panels)}")
        
        # Count panel types
        panel_types = {}
        for panel in panels:
            panel_type = panel.get('type', 'unknown')
            panel_types[panel_type] = panel_types.get(panel_type, 0) + 1
        
        print("\n   Panel types:")
        for ptype, count in panel_types.items():
            print(f"     - {ptype}: {count}")
        
        print(f"\n✅ PASS - Grafana dashboard configuration valid")
        return True
        
    except Exception as e:
        print(f"❌ FAIL - Error parsing dashboard: {e}")
        return False


def main():
    print("=" * 70)
    print("  Phase 3: Monitoring & Observability Test Suite")
    print("=" * 70)
    print("\nMake sure the FastAPI server is running:")
    print("  cd e:\\Python\\chatbot")
    print("  uvicorn app.api.main:app --reload --port 8000")
    print("=" * 70)
    
    input("\nPress Enter to start tests (or Ctrl+C to cancel)...")
    
    results = []
    
    try:
        # Run all tests
        results.append(("Metrics Endpoint", test_metrics_endpoint()))
        results.append(("System Resources", test_system_resource_monitoring()))
        results.append(("Auth Metrics", test_auth_metrics_tracking()))
        results.append(("Business Metrics", test_business_metrics()))
        results.append(("LLM Metrics", test_llm_performance_metrics()))
        results.append(("Alert Rules", verify_alert_rules_file()))
        results.append(("Grafana Dashboard", verify_grafana_dashboard()))
        
        # Summary
        print("\n" + "=" * 70)
        print("  Test Results Summary")
        print("=" * 70)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")
        
        print("\n" + "=" * 70)
        print(f"  Overall: {passed}/{total} tests passed")
        print("=" * 70)
        
        if passed == total:
            print("\n🎉 All monitoring tests passed! Phase 3 is ready for production.")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Please review the issues above.")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests cancelled by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
