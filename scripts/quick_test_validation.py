#!/usr/bin/env python3
"""
Quick Test Validation Script

Runs a subset of tests to verify the test suite is working correctly.
"""
import subprocess
import sys


def run_quick_validation():
    """Run quick validation tests"""
    print("="*70)
    print("QUICK TEST VALIDATION")
    print("="*70)
    
    tests_to_run = [
        ("Unit: Skills", "tests/unit/test_skills.py"),
        ("Unit: State", "tests/unit/test_state.py"),
        ("Unit: RAG Skill", "tests/unit/test_rag_skill.py::test_rag_skill_initialization"),
        ("Unit: Wiki Skill", "tests/unit/test_wiki_skill.py::test_wiki_skill_local_mode"),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_path in tests_to_run:
        print(f"\n{name}...", end=" ")
        
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_path, "-v", "--tb=no", "-q"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ PASSED")
            passed += 1
        else:
            print("❌ FAILED")
            failed += 1
            print(f"  Output: {result.stdout[-200:]}")
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*70)
    
    if failed == 0:
        print("\n✅ All validation tests passed!")
        print("\nNext steps:")
        print("  1. Run full test suite: python scripts/run_tests.py all")
        print("  2. Check coverage: python scripts/run_tests.py coverage")
        print("  3. View HTML report: open htmlcov/index.html")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Check the output above.")
        return 1


if __name__ == "__main__":
    exit(run_quick_validation())
