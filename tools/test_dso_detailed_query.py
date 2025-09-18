#!/usr/bin/env python3
"""Individual DSO Detailed Query API testing tool."""

import os
import sys
import argparse
from datetime import datetime

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.config import load_config
from src.api_clients.dso_detailed_query_api import DSODetailedQueryAPI
from src.api_clients.dso_search_api import DSOSearchAPI
from src.utils.house_logger import HouseSpecificLogger

def test_dso_detailed_query(address: str, renovation_type: str):
    """Test DSO Detailed Query API with specific renovation type.

    Args:
        address: Dutch address (for display and functional ref lookup)
        renovation_type: Type of renovation (e.g., "dakkapel", "uitbouw")
    """
    print("📋 DSO Detailed Query API Individual Test")
    print("=" * 50)
    print(f"Address: {address}")
    print(f"Renovation type: {renovation_type}")

    try:
        # Load configuration
        config = load_config()
        dso_config = config.get_dso_config()

        print(f"\n🔧 Configuration:")
        print(f"   API Key: {dso_config['api_key'][:10]}...")
        print(f"   Base URL: {dso_config['production_url']}")

        # Initialize house logger for file output
        house_logger = HouseSpecificLogger(address, f"DSO_DetailedQuery_Test_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        print(f"📁 Created house-specific folder: {house_logger.house_folder}")

        # Initialize APIs with house logger
        detailed_query_client = DSODetailedQueryAPI(dso_config, house_logger=house_logger)
        search_client = DSOSearchAPI(dso_config, house_logger=house_logger)
        print("✅ DSO Detailed Query Client initialized with logging")

        print(f"\n" + "=" * 50)
        print("🚀 RUNNING DSO DETAILED QUERY TESTS")
        print("=" * 50)

        # Initialize result variables
        search_result = {}
        functional_refs = []
        validation_result = {}
        activity_details = {}
        location_result = {}

        # Step 1: Get functional references from search (prerequisite)
        print(f"\n1️⃣ PREREQUISITE: GET FUNCTIONAL REFERENCES")
        print("-" * 50)

        print(f"First, we need to search for '{renovation_type}' to get functional structure references...")

        search_result = search_client.search_activities(renovation_type, renovation_type=renovation_type)

        if search_result['success']:
            functional_refs = search_client.extract_functional_structure_refs(search_result)
            print(f"✅ Found {len(functional_refs)} functional structure references")

            if functional_refs:
                print(f"📋 Sample references:")
                for i, ref in enumerate(functional_refs[:3], 1):
                    print(f"   {i}. {ref[:80]}...")
            else:
                print("❌ No functional references found - cannot proceed with detailed query tests")
                return
        else:
            print("❌ Search failed - cannot get functional references")
            print(f"   Error: {search_result.get('error')}")
            return

        # Step 2: Get Coordinates for Detailed Query
        print(f"\n2️⃣ GET COORDINATES FOR DETAILED QUERY")
        print("-" * 50)

        # Parse address for BAG API
        parts = address.split()
        if len(parts) >= 2:
            postcode = parts[0]
            number_part = parts[1]
            if '-' in number_part:
                number, addition = number_part.split('-', 1)
                address_dict = {
                    'postcode': postcode,
                    'huisnummer': int(number),
                    'huisnummertoevoeging': addition
                }
            else:
                address_dict = {
                    'postcode': postcode,
                    'huisnummer': int(number_part)
                }
        else:
            print("❌ Invalid address format")
            return

        # Import BAG client
        from src.api_clients.bag_client import BAGAPIClient
        bag_config = config.get_bag_config()
        bag_client = BAGAPIClient(bag_config, house_logger=house_logger)

        coordinates_result = bag_client.get_address_extended(address_dict, renovation_type=renovation_type)

        if coordinates_result['success']:
            coordinates = bag_client.extract_coordinates(coordinates_result)
            if coordinates:
                print("✅ SUCCESS")
                print(f"   Coordinates: [{coordinates[0]}, {coordinates[1]}] (RD format)")
            else:
                print("❌ Could not extract coordinates")
                return
        else:
            print("❌ FAILED to get coordinates")
            print(f"   Error: {coordinates_result.get('error')}")
            return

        # Step 3: Test Detailed Query API Methods with Coordinates
        print(f"\n3️⃣ DETAILED QUERY API TESTS")
        print("-" * 50)

        # Test A: Search Activity Identifications
        print(f"\n🔍 A) ACTIVITY IDENTIFICATIONS SEARCH")
        print("-" * 30)

        activity_ids_result = detailed_query_client.search_activity_identifications(
            coordinates, renovation_type=renovation_type
        )

        if activity_ids_result['success']:
            print("✅ SUCCESS")
            data = activity_ids_result['data']
            print(f"📊 Activity IDs Results:")
            print(f"   Activity identifications found: {data['total_found']}")
            print(f"   Search buffer: {data['search_criteria']['buffer_meters']} meters")
            print(f"   Response time: {data['response_metadata']['duration']:.2f}s")

            if data['activity_identifications']:
                print(f"\n📋 Sample Activity IDs (first 3):")
                for i, activity_id in enumerate(data['activity_identifications'][:3], 1):
                    print(f"   {i}. {activity_id}")
        else:
            print("❌ FAILED")
            print(f"   Error: {activity_ids_result.get('error')}")

        # Test B: Search Location Identifications
        print(f"\n🔍 B) LOCATION IDENTIFICATIONS SEARCH")
        print("-" * 30)

        location_ids_result = detailed_query_client.search_location_identifications(
            coordinates, renovation_type=renovation_type
        )

        if location_ids_result['success']:
            print("✅ SUCCESS")
            data = location_ids_result['data']
            print(f"📊 Location IDs Results:")
            print(f"   Location identifications found: {data['total_found']}")
            print(f"   Search buffer: {data['search_criteria']['buffer_meters']} meters")
            print(f"   Response time: {data['response_metadata']['duration']:.2f}s")

            if data['location_identifications']:
                print(f"\n📋 Sample Location IDs (first 3):")
                for i, location_id in enumerate(data['location_identifications'][:3], 1):
                    print(f"   {i}. {location_id}")
        else:
            print("❌ FAILED")
            print(f"   Error: {location_ids_result.get('error')}")

        # Test C: Search Locations
        print(f"\n🔍 C) LOCATIONS SEARCH")
        print("-" * 30)

        locations_result = detailed_query_client.search_locations(
            coordinates, renovation_type=renovation_type
        )

        if locations_result['success']:
            print("✅ SUCCESS")
            data = locations_result['data']
            print(f"📊 Locations Results:")
            print(f"   Locations found: {data['total_found']}")
            print(f"   Search operator: {data['search_criteria']['spatial_operator']}")
            print(f"   Response time: {data['response_metadata']['duration']:.2f}s")

            if data['locations']:
                print(f"\n📋 Sample Locations (first 3):")
                for i, location in enumerate(data['locations'][:3], 1):
                    print(f"   {i}. {location.get('identificatie', 'Unknown')}")
                    print(f"      Name: {location.get('noemer', 'Unknown')}")
                    print(f"      Spatial relation: {location.get('spatialOperator', 'Unknown')}")
        else:
            print("❌ FAILED")
            print(f"   Error: {locations_result.get('error')}")

        # Test D: Get Aggregated Activities
        print(f"\n🔍 D) AGGREGATED ACTIVITIES")
        print("-" * 30)

        activities_result = detailed_query_client.get_aggregated_activities(
            size=5, renovation_type=renovation_type
        )

        if activities_result['success']:
            print("✅ SUCCESS")
            data = activities_result['data']
            print(f"📊 Aggregated Activities Results:")
            print(f"   Activities found: {data['total_found']}")
            print(f"   Response time: {data['response_metadata']['duration']:.2f}s")

            if data['activities']:
                print(f"\n📋 Sample Activities (first 3):")
                for i, activity in enumerate(data['activities'][:3], 1):
                    print(f"   {i}. {activity.get('identificatie', 'Unknown')}")
                    print(f"      Name: {activity.get('naam', 'Unknown')}")
                    print(f"      Status: {activity.get('procedurestatus', 'Unknown')}")
        else:
            print("❌ FAILED")
            print(f"   Error: {activities_result.get('error')}")

        # Test E: Comprehensive Validation
        print(f"\n🔍 E) COMPREHENSIVE VALIDATION")
        print("-" * 30)

        validation_result = detailed_query_client.validate_coordinates_and_get_context(
            coordinates, renovation_type=renovation_type
        )

        if validation_result['success']:
            print("✅ SUCCESS")
            data = validation_result['data']
            test_summary = data['test_summary']
            print(f"📊 Comprehensive Validation Results:")
            print(f"   Successful tests: {test_summary['successful_tests']}/{test_summary['total_tests']}")
            print(f"   Success rate: {test_summary['success_rate']:.1f}%")
        else:
            print("❌ FAILED")
            print(f"   Error: {validation_result.get('error')}")

        # Save test summary to files
        test_summary = {
            "address": address,
            "renovation_type": renovation_type,
            "test_timestamp": datetime.now().isoformat(),
            "results": {
                "search_prerequisite": search_result.get('success', False),
                "coordinates_extraction": coordinates_result.get('success', False),
                "activity_identifications_search": activity_ids_result.get('success', False),
                "location_identifications_search": location_ids_result.get('success', False),
                "locations_search": locations_result.get('success', False),
                "aggregated_activities": activities_result.get('success', False),
                "comprehensive_validation": validation_result.get('success', False)
            },
            "coordinates": coordinates if coordinates_result.get('success') else [],
            "functional_references": functional_refs,
            "detailed_query_results": {
                "activity_identifications_found": activity_ids_result.get('data', {}).get('total_found', 0) if activity_ids_result.get('success') else 0,
                "location_identifications_found": location_ids_result.get('data', {}).get('total_found', 0) if location_ids_result.get('success') else 0,
                "locations_found": locations_result.get('data', {}).get('total_found', 0) if locations_result.get('success') else 0,
                "aggregated_activities_found": activities_result.get('data', {}).get('total_found', 0) if activities_result.get('success') else 0
            }
        }

        # Save to house-specific folder
        house_logger.save_renovation_test_results("dso_detailed_query_test", test_summary)

        print(f"\n" + "=" * 50)
        print("🎉 DSO DETAILED QUERY API TEST COMPLETE")
        print("=" * 50)

        # Summary
        success_count = sum([
            test_summary['results']['search_prerequisite'],
            test_summary['results']['coordinates_extraction'],
            test_summary['results']['activity_identifications_search'],
            test_summary['results']['location_identifications_search'],
            test_summary['results']['locations_search'],
            test_summary['results']['aggregated_activities'],
            test_summary['results']['comprehensive_validation']
        ])

        total_tests = 7
        if success_count >= 5:
            print("✅ DSO Detailed Query API working excellently!")
            print(f"✅ Successfully tested {success_count}/{total_tests} core functions")
            print("🚀 Ready to test DSO Interactive API with detailed legal data")
        elif success_count >= 3:
            print("⚠️ DSO Detailed Query API partially working")
            print(f"⚠️ {success_count}/{total_tests} core functions succeeded")
            print("💡 Some API methods may be limited")
        else:
            print("❌ DSO Detailed Query API having issues")
            print("💡 Check API endpoints and coordinate handling")

        print(f"\n📁 Results saved to:")
        print(f"   • House folder: {house_logger.house_folder}")
        print(f"   • Output folder: {house_logger.output_folder}")

        print(f"\n📁 Next steps:")
        print(f"   • Test DSO Interactive: python tools/test_dso_interactive.py '{address}' {renovation_type}")
        print(f"   • View saved results: ls {house_logger.house_folder}")
        print(f"   • Test full integration: python run_tests.py")

    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description='Test DSO Detailed Query API with specific renovation type')
    parser.add_argument('address', help='Dutch address (e.g., "1082GB 43-2")')
    parser.add_argument('renovation_type', help='Renovation type (e.g., "dakkapel", "uitbouw")')

    args = parser.parse_args()
    test_dso_detailed_query(args.address, args.renovation_type)

if __name__ == "__main__":
    main()