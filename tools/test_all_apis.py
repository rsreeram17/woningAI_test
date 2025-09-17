#!/usr/bin/env python3
"""Test all APIs individually with a single command."""

import os
import sys
import argparse
import subprocess

def run_test(script_name, args, description):
    """Run a test script and capture results."""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")

    cmd = [sys.executable, script_name] + args

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        # Print stdout
        if result.stdout:
            print(result.stdout)

        # Print stderr if there are errors
        if result.stderr:
            print(f"⚠️ Errors/Warnings:")
            print(result.stderr)

        success = result.returncode == 0
        return success, result.stdout

    except subprocess.TimeoutExpired:
        print("❌ Test timed out (120s)")
        return False, ""
    except Exception as e:
        print(f"❌ Failed to run test: {e}")
        return False, ""

def test_all_apis(address: str, renovation_type: str):
    """Test all APIs in sequence.

    Args:
        address: Dutch address (e.g., "1082GB 43-2")
        renovation_type: Type of renovation (e.g., "dakkapel")
    """
    print("🚀 Complete API Testing Suite")
    print("=" * 60)
    print(f"Address: {address}")
    print(f"Renovation type: {renovation_type}")

    # Change to tools directory
    tools_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(tools_dir)

    results = []

    # Test 1: BAG API
    success, output = run_test("test_bag_api.py", [address], "BAG API Test")
    results.append(("BAG API", success, "Address lookup and building data"))

    # Test 2: DSO Search API
    success, output = run_test("test_dso_search.py", [address, renovation_type], "DSO Search API Test")
    results.append(("DSO Search API", success, "Find applicable rules and activities"))

    # Test 3: DSO Interactive API
    success, output = run_test("test_dso_interactive.py", [address, renovation_type], "DSO Interactive API Test")
    results.append(("DSO Interactive API", success, "Permit checks and requirements"))

    # TODO: Add other API tests when ready
    # success, output = run_test("test_dso_routing.py", [address, renovation_type], "DSO Routing API Test")
    # results.append(("DSO Routing API", success, "Authority routing"))

    # success, output = run_test("test_dso_catalog.py", [address, renovation_type], "DSO Catalog API Test")
    # results.append(("DSO Catalog API", success, "Regulation catalog"))

    # Final summary
    print(f"\n{'='*60}")
    print("🎉 COMPLETE API TEST SUMMARY")
    print(f"{'='*60}")

    total_tests = len(results)
    successful_tests = sum(1 for _, success, _ in results if success)
    success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0

    print(f"📊 Overall Results: {successful_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
    print()

    for api_name, success, description in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {api_name:<20} - {description}")

    print()

    if success_rate >= 80:
        print("🚀 Excellent! APIs are ready for integration")
    elif success_rate >= 60:
        print("✅ Good! Most APIs working, minor issues to resolve")
    elif success_rate >= 40:
        print("⚠️ Moderate. Some APIs working, need troubleshooting")
    else:
        print("❌ Poor. Significant issues need to be resolved")

    print(f"\n📁 Next steps:")
    if successful_tests >= 2:
        print(f"   • Run full integration: python ../run_tests.py")
    print(f"   • View detailed logs: ls ../logs/by_house/")
    print(f"   • Test different renovation: python test_all_apis.py '{address}' uitbouw")

def main():
    parser = argparse.ArgumentParser(description='Test all APIs with a single command')
    parser.add_argument('address', help='Dutch address (e.g., "1082GB 43-2")')
    parser.add_argument('renovation_type', help='Renovation type (e.g., "dakkapel", "uitbouw")')

    args = parser.parse_args()
    test_all_apis(args.address, args.renovation_type)

if __name__ == "__main__":
    main()