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

        # Test F: Legal Source and Rule Texts
        print(f"\n🔍 F) LEGAL SOURCE AND RULE TEXTS")
        print("-" * 30)

        # Initialize result variables
        legal_source_result = {}
        rule_texts_result = {}

        # Find a specific activity to test with
        test_activity_id = None
        if activity_ids_result.get('success') and activity_ids_result.get('data', {}).get('activity_identifications'):
            # Look for Amsterdam dakkapel activity specifically
            activity_ids = activity_ids_result['data']['activity_identifications']
            for aid in activity_ids:
                if 'gm0363' in aid and 'Dakkapel' in aid:
                    test_activity_id = aid
                    break

            # If no dakkapel found, use first activity
            if not test_activity_id:
                test_activity_id = activity_ids[0]

        if test_activity_id:
            print(f"📋 Testing with activity: {test_activity_id}")

            # Test F1: Legal Source
            print(f"\n📖 F1) Legal Source")
            print("-" * 20)

            legal_source_result = detailed_query_client.get_activity_legal_source(
                test_activity_id, renovation_type=renovation_type
            )

            if legal_source_result['success']:
                print("✅ SUCCESS")
                data = legal_source_result['data']
                print(f"📊 Legal Source Results:")
                print(f"   Response time: {data['response_metadata']['duration']:.2f}s")

                legal_source = data['legal_source']
                if isinstance(legal_source, dict):
                    if 'documentIdentificatie' in legal_source:
                        print(f"   Document: {legal_source['documentIdentificatie']}")

                    if 'regelteksten' in legal_source:
                        regelteksten = legal_source['regelteksten']
                        print(f"   Rule texts in source: {len(regelteksten)}")

                        if regelteksten:
                            first_rule = regelteksten[0]
                            print(f"   Sample rule ID: {first_rule.get('identificatie', 'Unknown')}")
                else:
                    print(f"   Raw response received")
            else:
                print("❌ FAILED")
                print(f"   Error: {legal_source_result.get('error')}")

            # Test F2: Rule Texts
            print(f"\n📖 F2) Rule Texts")
            print("-" * 20)

            rule_texts_result = detailed_query_client.get_activity_rule_texts(
                test_activity_id, size=5, renovation_type=renovation_type
            )

            if rule_texts_result['success']:
                print("✅ SUCCESS")
                data = rule_texts_result['data']
                print(f"📊 Rule Texts Results:")
                print(f"   Rule texts found: {data['total_found']}")
                print(f"   Response time: {data['response_metadata']['duration']:.2f}s")

                rule_texts = data['rule_texts']
                if rule_texts and len(rule_texts) > 0:
                    print(f"\n📋 Sample Rule Texts (first 2):")
                    for i, rule in enumerate(rule_texts[:2], 1):
                        print(f"   {i}. {rule.get('identificatie', 'Unknown')}")
                        print(f"      Article: {rule.get('labelXml', 'Unknown')} {rule.get('nummerXml', '')}")
                        print(f"      Title: {rule.get('opschrift', 'No title')}")

                        # Show description preview (clean XML)
                        description = rule.get('omschrijving', 'No description')
                        if description and len(description) > 100:
                            # Remove XML tags for preview
                            import re
                            clean_desc = re.sub(r'<[^>]+>', '', description)
                            if len(clean_desc) > 80:
                                clean_desc = clean_desc[:80] + "..."
                            print(f"      Content: {clean_desc}")
                else:
                    print("   No rule texts found")

                # Show pagination info
                pagination = data.get('pagination', {})
                if pagination and pagination.get('totalElements'):
                    print(f"\n📄 Pagination:")
                    print(f"   Total elements: {pagination.get('totalElements', 'Unknown')}")
                    print(f"   Pages: {pagination.get('totalPages', 'Unknown')}")
            else:
                print("❌ FAILED")
                print(f"   Error: {rule_texts_result.get('error')}")
        else:
            print("⚠️ No activity IDs available for legal source and rule texts testing")
            legal_source_result = {"success": False, "error": "No activity IDs available"}
            rule_texts_result = {"success": False, "error": "No activity IDs available"}

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
                "comprehensive_validation": validation_result.get('success', False),
                "legal_source_lookup": legal_source_result.get('success', False),
                "rule_texts_lookup": rule_texts_result.get('success', False)
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
            test_summary['results']['comprehensive_validation'],
            test_summary['results']['legal_source_lookup'],
            test_summary['results']['rule_texts_lookup']
        ])

        total_tests = 9
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