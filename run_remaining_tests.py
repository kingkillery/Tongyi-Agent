#!/usr/bin/env python3
"""
Run remaining Tongyi Agent tests and summarize failures.
Excludes tests that are already passing from our previous runs.
"""
import subprocess
import sys
from pathlib import Path

# Tests that were already passing in previous runs
PASSING_TESTS = [
    "tests/test_model_router.py",
    "tests/test_integration.py::TestIntegration::test_logging_integration",
    "tests/test_integration.py::TestIntegration::test_local_first_behavior_in_system_prompt", 
    "tests/test_integration.py::TestIntegration::test_end_to_end_simple_question",
    "tests/test_integration.py::TestIntegration::test_budget_enforcement_integration",
    "tests/test_integration.py::TestIntegration::test_verification_integration",
]

def run_pytest(test_specs):
    """Run pytest with given test specifications and return results."""
    cmd = [sys.executable, "-m", "pytest", "-v", "--tb=short"] + test_specs
    print(f"Running: {' '.join(cmd)}")
    print("=" * 60)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1, "", str(e)

def get_all_test_files():
    """Get all test files in the tests directory."""
    tests_dir = Path(__file__).parent / "tests"
    return list(tests_dir.glob("test_*.py"))

def main():
    """Main script to run remaining tests."""
    print("Tongyi Agent - Running Remaining Tests")
    print("=" * 60)
    
    # Get all test files
    all_test_files = get_all_test_files()
    all_test_paths = [str(f) for f in all_test_files]
    
    # Filter out already passing test files
    remaining_tests = []
    for test_path in all_test_paths:
        if not any(passing in test_path for passing in PASSING_TESTS):
            remaining_tests.append(test_path)
    
    print(f"Found {len(all_test_paths)} total test files")
    print(f"Skipping {len(PASSING_TESTS)} already passing test specs")
    print(f"Running {len(remaining_tests)} remaining test files")
    print()
    
    if not remaining_tests:
        print("All tests are already passing! ✅")
        return 0
    
    # Run the remaining tests
    returncode, stdout, stderr = run_pytest(remaining_tests)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if returncode == 0:
        print("✅ All remaining tests passed!")
        return 0
    else:
        print("❌ Some tests failed. See output above for details.")
        
        # Extract failed test names for easier debugging
        failed_tests = []
        lines = stdout.split('\n')
        for line in lines:
            if "FAILED" in line and "::" in line:
                failed_tests.append(line.strip())
        
        if failed_tests:
            print("\nFailed tests:")
            for test in failed_tests:
                print(f"  - {test}")
        
        return returncode

if __name__ == "__main__":
    sys.exit(main())
