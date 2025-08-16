#!/usr/bin/env python
"""
Comprehensive Test Runner
Runs all test suites and generates coverage reports
"""
import os
import sys
import subprocess
import time

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    
    start_time = time.time()
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    duration = time.time() - start_time
    
    if result.returncode == 0:
        print(f"✅ {description} - PASSED ({duration:.2f}s)")
        if result.stdout:
            print(result.stdout)
    else:
        print(f"❌ {description} - FAILED ({duration:.2f}s)")
        if result.stderr:
            print("STDERR:", result.stderr)
        if result.stdout:
            print("STDOUT:", result.stdout)
    
    return result.returncode == 0

def main():
    """Run comprehensive test suite"""
    print("🚀 Starting Comprehensive Test Suite")
    print("This will run all test categories and generate coverage reports")
    
    # Change to backend directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    test_suites = [
        {
            'cmd': 'python manage.py test core.test_models',
            'desc': 'Model Tests (FootImage, Shoe models)'
        },
        {
            'cmd': 'python manage.py test core.test_scoring',
            'desc': 'Scoring Algorithm Tests (recommendation logic)'
        },
        {
            'cmd': 'python manage.py test core.test_score_shoes',
            'desc': 'Score Shoes Module Tests (legacy scoring)'
        },
        {
            'cmd': 'python manage.py test core.test_management_commands',
            'desc': 'Management Commands Tests (ensure_admin, fix_guest_uploads)'
        },
        {
            'cmd': 'python manage.py test core.test_image_processing',
            'desc': 'Image Processing Tests (AI integration, dimension calculation)'
        },
        {
            'cmd': 'python manage.py test core.test_e2e',
            'desc': 'End-to-End Tests (complete user workflows)'
        }
    ]
    
    results = []
    total_start = time.time()
    
    # Run individual test suites
    for suite in test_suites:
        success = run_command(suite['cmd'], suite['desc'])
        results.append((suite['desc'], success))
    
    # Run comprehensive coverage analysis
    print(f"\n{'='*60}")
    print("📊 Generating Comprehensive Coverage Report")
    print(f"{'='*60}")
    
    coverage_cmd = (
        "coverage run --source='core' manage.py test "
        "core.test_models core.test_scoring core.test_score_shoes "
        "core.test_management_commands core.test_image_processing core.test_e2e"
    )
    
    coverage_success = run_command(coverage_cmd, "Coverage Data Collection")
    
    if coverage_success:
        run_command("coverage report", "Coverage Report Generation")
        run_command("coverage html", "HTML Coverage Report Generation")
    
    # Generate summary
    total_duration = time.time() - total_start
    
    print(f"\n{'='*60}")
    print("📋 TEST SUITE SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for desc, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {desc}")
    
    print(f"\n📈 Results: {passed}/{total} test suites passed")
    print(f"⏱️  Total execution time: {total_duration:.2f} seconds")
    
    if coverage_success:
        print(f"📊 Coverage report generated: htmlcov/index.html")
        print(f"🌐 View coverage: open htmlcov/index.html")
    
    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED! Great job!")
        return 0
    else:
        print(f"\n⚠️  Some tests failed. Check output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())