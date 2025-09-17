#!/usr/bin/env python3
"""Quick test runner for debugging and single-scenario testing."""

import os
import sys
import time

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.config import load_config
from src.api_clients.bag_client import BAGAPIClient
from src.api_clients.dso_search_api import DSOSearchAPI
from src.api_clients.integration_client import IntegratedRenovationAnalysis
from src.utils.console_display import RealTimeDisplay

def quick_test(address: str, renovation_type: str):
    """Run a quick test for debugging purposes.

    Args:
        address: Dutch address string (e.g., "1012JS 1")
        renovation_type: Renovation type (e.g., "dakkapel")
    """
    console = RealTimeDisplay()

    console.print_header(f"Quick Test: {address} → {renovation_type}")

    try:
        # Load configuration
        config = load_config()

        # Initialize clients
        console.print_section("Initializing Clients")

        bag_config = config.get_bag_config()
        dso_config = config.get_dso_config()

        if not bag_config.get('api_key'):
            console.error("BAG API key not found. Please set BAG_API_KEY in your .env file.")
            return

        if not dso_config.get('api_key'):
            console.error("DSO API key not found. Please set DSO_API_KEY in your .env file.")
            return

        # Create clients
        bag_client = BAGAPIClient(bag_config)
        dso_search = DSOSearchAPI(dso_config)

        console.success("Clients initialized")

        # Step 1: Test BAG address resolution
        console.print_section("Step 1: BAG Address Resolution")

        print(f"🏠 Testing address: {address}")
        start_time = time.time()

        bag_result = bag_client.validate_address_for_testing(address)
        bag_duration = time.time() - start_time

        if bag_result['success']:
            address_info = bag_result['address_info']
            building_info = bag_result['building_info']
            coordinates = bag_result['coordinates']

            console.success(f"Address resolved in {bag_duration:.2f}s")
            print(f"   📍 Address: {address_info['formatted_address']}")
            print(f"   🏗️  Building year: {building_info.get('bouwjaar', 'Unknown')}")
            print(f"   📐 Area: {building_info.get('oppervlakte', 'Unknown')}m²")
            print(f"   🗺️  Coordinates: {coordinates}")

        else:
            console.error(f"Address resolution failed: {bag_result.get('error')}")
            return

        # Step 2: Test DSO rule search
        console.print_section("Step 2: DSO Rule Search")

        print(f"🔍 Searching for renovation type: {renovation_type}")
        start_time = time.time()

        # Get search terms for this renovation type
        default_terms = {
            'dakkapel': ['dakkapel', 'dakraam'],
            'uitbouw': ['uitbouw', 'aanbouw'],
            'badkamer_verbouwen': ['badkamer verbouwen', 'sanitair'],
            'extra_verdieping': ['extra verdieping', 'optopping'],
            'garage_bouwen': ['garage bouwen', 'bijgebouw'],
            'keuken_verbouwen': ['keuken verbouwen']
        }

        search_terms = default_terms.get(renovation_type, [renovation_type])

        dso_result = dso_search.search_with_multiple_terms(search_terms, renovation_type=renovation_type)
        dso_duration = time.time() - start_time

        if dso_result['success']:
            activities = dso_result['data']['combined_activities']
            console.success(f"Found {len(activities)} applicable rules in {dso_duration:.2f}s")

            if activities:
                print(f"   📋 First few rules:")
                for i, activity in enumerate(activities[:3], 1):
                    activity_name = activity.get('naam', 'Unknown')
                    print(f"      {i}. {activity_name}")

                if len(activities) > 3:
                    print(f"      ... and {len(activities) - 3} more")

            # Show search quality analysis
            search_analysis = dso_search.analyze_search_quality(dso_result, renovation_type)
            quality_score = search_analysis['quality_score']
            print(f"   📊 Search quality: {quality_score}/100")

        else:
            console.error(f"DSO search failed: {dso_result.get('error')}")

        # Step 3: Quick integration test
        console.print_section("Step 3: Quick Integration Test")

        if bag_result['success'] and dso_result['success']:
            print("✅ Both APIs successful - integration possible")

            total_duration = bag_duration + dso_duration
            print(f"⏱️ Total time: {total_duration:.2f}s")

            # Estimate business viability
            activities_found = len(dso_result['data']['combined_activities'])
            data_quality = 70 if building_info.get('bouwjaar') else 40
            regulatory_coverage = min(activities_found * 20, 80)

            estimated_viability = int((data_quality + regulatory_coverage) / 2)
            print(f"📈 Estimated viability: {estimated_viability}/100")

            if estimated_viability >= 70:
                console.success("High viability - good candidate for MVP")
            elif estimated_viability >= 50:
                console.info("Moderate viability - consider for MVP")
            else:
                console.warning("Low viability - may need additional work")

        else:
            console.error("Integration not possible due to API failures")

        # Summary
        console.print_section("Summary")

        print(f"🏠 Address: {address}")
        print(f"🔧 Renovation: {renovation_type}")
        print(f"📊 Results:")
        print(f"   • BAG API: {'✅' if bag_result['success'] else '❌'}")
        print(f"   • DSO API: {'✅' if dso_result['success'] else '❌'}")

        if bag_result['success'] and dso_result['success']:
            print(f"   • Integration: ✅ Possible")
            print(f"   • Rules found: {len(dso_result['data']['combined_activities'])}")
            print(f"   • Total duration: {bag_duration + dso_duration:.2f}s")
        else:
            print(f"   • Integration: ❌ Failed")

        console.info("For detailed analysis, run: python run_tests.py")
        console.info("For house-specific data, check: logs/by_house/")

    except Exception as e:
        console.error(f"Quick test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main function for quick test."""
    if len(sys.argv) >= 3:
        address = sys.argv[1]
        renovation_type = sys.argv[2]
        quick_test(address, renovation_type)
    else:
        console = RealTimeDisplay()
        console.print_header("Quick Test Tool")

        print("Usage: python tools/quick_test.py <address> <renovation_type>")
        print("\nExamples:")
        print("  python tools/quick_test.py \"1012JS 1\" dakkapel")
        print("  python tools/quick_test.py \"2631CR 15C\" uitbouw")

        print("\nAvailable renovation types:")
        print("  • dakkapel")
        print("  • uitbouw")
        print("  • badkamer_verbouwen")
        print("  • extra_verdieping")
        print("  • garage_bouwen")
        print("  • keuken_verbouwen")

        # Interactive mode
        try:
            address = input("\nEnter address (e.g., '1012JS 1'): ").strip()
            renovation_type = input("Enter renovation type (e.g., 'dakkapel'): ").strip()

            if address and renovation_type:
                quick_test(address, renovation_type)
            else:
                console.error("Both address and renovation type are required")

        except (KeyboardInterrupt, EOFError):
            console.info("Cancelled")

if __name__ == "__main__":
    main()