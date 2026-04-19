#!/usr/bin/env python3
"""
Test Runner Script

Runs different test suites with appropriate configurations.
Usage:
    python run_tests.py unit          # Run unit tests only
    python run_tests.py integration   # Run integration tests only
    python run_tests.py e2e           # Run end-to-end tests only
    python run_tests.py all           # Run all tests
    python run_tests.py coverage      # Run tests with coverage report
"""
import sys
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Run a command and report results"""
    print(f"\n{'='*70}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*70)
    
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode == 0:
        print(f"✅ {description} PASSED")
    else:
        print(f"❌ {description} FAILED")
    
    return result.returncode


def run_unit_tests():
    """Run unit tests"""
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/unit/",
        "-v",
        "--tb=short",
        "-x"
    ]
    return run_command(cmd, "Unit Tests")


def run_integration_tests():
    """Run integration tests"""
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/integration/",
        "-v",
        "--tb=short",
        "-x",
        "-m", "not load"  # Exclude load tests by default
    ]
    return run_command(cmd, "Integration Tests")


def run_e2e_tests():
    """Run end-to-end tests"""
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/integration/test_end_to_end.py",
        "-v",
        "--tb=short"
    ]
    return run_command(cmd, "End-to-End Tests")


def run_load_tests():
    """Run load/performance tests"""
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/integration/test_rate_limit_and_load.py",
        "-v",
        "--tb=short",
        "-m", "load"
    ]
    return run_command(cmd, "Load Tests")


def run_with_coverage():
    """Run all tests with coverage report"""
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--cov=app",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml",
        "--cov-fail-under=80",  # Require 80% coverage
        "-x"
    ]
    return run_command(cmd, "Tests with Coverage Report")


def run_all_tests():
    """Run all tests"""
    results = []
    
    print("\n" + "="*70)
    print("RUNNING COMPLETE TEST SUITE")
    print("="*70)
    
    results.append(("Unit Tests", run_unit_tests()))
    results.append(("Integration Tests", run_integration_tests()))
    results.append(("E2E Tests", run_e2e_tests()))
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for name, code in results:
        status = "✅ PASSED" if code == 0 else "❌ FAILED"
        print(f"{name:30s} {status}")
    
    all_passed = all(code == 0 for _, code in results)
    
    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
    
    return 0 if all_passed else 1


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "unit":
        exit_code = run_unit_tests()
    elif command == "integration":
        exit_code = run_integration_tests()
    elif command == "e2e":
        exit_code = run_e2e_tests()
    elif command == "load":
        exit_code = run_load_tests()
    elif command == "coverage":
        exit_code = run_with_coverage()
    elif command == "all":
        exit_code = run_all_tests()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        exit_code = 1
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
