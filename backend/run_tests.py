#!/usr/bin/env python3
"""
Test runner script for hyper-tuner backend tests.
This script automatically handles the proper path setup for imports.
"""

import unittest
import sys
import os
import importlib.util

# Ensure we can import modules from the parent directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Check for required dependencies
def check_dependency(module_name):
    """Check if a dependency is installed"""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

# List of dependencies for different test modules
dependencies = {
    'test_market_calendar': ['pytz'],
    'test_backtest_timestamps': ['pytz', 'pandas', 'numpy', 'backtrader'],
    'test_simplified': []  # No external dependencies
}

# Load all tests from the tests directory, filtering based on available dependencies
def run_all_tests():
    print("Running all tests...")
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # Get all test files
    for file in os.listdir('tests'):
        if file.startswith('test_') and file.endswith('.py'):
            test_module = file[:-3]  # Remove .py extension
            
            # Check if all dependencies are available for this test
            missing_deps = []
            for dep in dependencies.get(test_module, []):
                if not check_dependency(dep):
                    missing_deps.append(dep)
            
            if missing_deps:
                print(f"Skipping {test_module} due to missing dependencies: {', '.join(missing_deps)}")
                print(f"  Install with: pip install {' '.join(missing_deps)}")
                continue
                
            # Add the test to the suite
            try:
                module_tests = test_loader.loadTestsFromName(f"tests.{test_module}")
                test_suite.addTest(module_tests)
                print(f"Added {test_module} tests")
            except Exception as e:
                print(f"Error loading tests from {test_module}: {str(e)}")
    
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    return result

if __name__ == '__main__':
    print("\n=======================================")
    print("Hyper-Tuner Backend Test Runner")
    print("=======================================\n")
    
    # Check for essential dependencies
    if not check_dependency('pytz'):
        print("WARNING: pytz module is missing. Some tests will be skipped.")
        print("Install with: pip install pytz\n")
    
    # Run tests and print results
    result = run_all_tests()
    print("\n=======================================")
    print(f"Tests ran: {result.testsRun}")
    print(f"Errors: {len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print("=======================================\n")
    
    # Exit with appropriate code
    if result.wasSuccessful():
        print("All tests passed!")
        sys.exit(0)
    else:
        print("Tests failed, see details above.")
        sys.exit(1)
