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

        # Step 2: Validate and Extract Activity Details
        print(f"\n2️⃣ VALIDATE FUNCTIONAL REFERENCES & EXTRACT ACTIVITY IDS")
        print("-" * 50)

        validation_result = detailed_query_client.validate_and_get_activity_details(
            functional_refs, renovation_type=renovation_type
        )

        if validation_result['success']:
            print("✅ SUCCESS")
            data = validation_result['data']

            print(f"📊 Validation Results:")
            print(f"   Activity IDs extracted: {len(data['activity_ids'])}")
            print(f"   Successful lookups: {data['successful_lookups']}")
            print(f"   Total attempted: {data['total_attempted']}")

            print(f"\n📋 Activity IDs found:")
            for i, activity_id in enumerate(data['activity_ids'], 1):
                print(f"   {i}. {activity_id}")

            activity_details = data['activity_details']
        else:
            print("❌ FAILED")
            print(f"   Error: {validation_result.get('error')}")
            return

        # Step 3: Test Individual API Methods
        if activity_details:
            sample_activity_id = list(activity_details.keys())[0]

            print(f"\n3️⃣ INDIVIDUAL API METHOD TESTS")
            print("-" * 50)
            print(f"Testing with activity ID: {sample_activity_id}")

            # Test A: Get Activity Lifecycle
            print(f"\n🔍 A) ACTIVITY LIFECYCLE TEST")
            print("-" * 30)

            lifecycle_result = detailed_query_client.get_activity_lifecycle(
                sample_activity_id, renovation_type=renovation_type
            )

            if lifecycle_result['success']:
                print("✅ SUCCESS")
                data = lifecycle_result['data']
                print(f"📊 Lifecycle Results:")
                print(f"   Activities found: {data['total_found']}")
                print(f"   Response time: {data['response_metadata']['duration']:.2f}s")

                if data['activities']:
                    activity = data['activities'][0]
                    print(f"\n📋 Sample Activity Details:")
                    print(f"   Name: {activity.get('naam', 'Unknown')}")
                    print(f"   Status: {activity.get('procedurestatus', 'Unknown')}")
                    if 'bevoegdGezag' in activity:
                        authority = activity['bevoegdGezag']
                        print(f"   Authority: {authority.get('naam', 'Unknown')} ({authority.get('bestuurslaag', 'Unknown')})")
                    if 'geregistreerdMet' in activity:
                        reg = activity['geregistreerdMet']
                        print(f"   Version: {reg.get('versie', 'Unknown')}")
                        print(f"   Effective from: {reg.get('beginInwerking', 'Unknown')}")
            else:
                print("❌ FAILED")
                print(f"   Error: {lifecycle_result.get('error')}")

            # Test B: Get Legal Source
            print(f"\n🔍 B) LEGAL SOURCE TEST")
            print("-" * 30)

            legal_source_result = detailed_query_client.get_legal_source(
                sample_activity_id, renovation_type=renovation_type
            )

            if legal_source_result['success']:
                print("✅ SUCCESS")
                data = legal_source_result['data']
                print(f"📊 Legal Source Results:")
                print(f"   Document ID: {data.get('document_identification', 'Unknown')}")
                print(f"   Rule texts found: {data['total_rule_texts']}")
                print(f"   Response time: {data['response_metadata']['duration']:.2f}s")

                if data['rule_texts']:
                    rule = data['rule_texts'][0]
                    print(f"\n📋 Sample Rule Text:")
                    print(f"   ID: {rule.get('identificatie', 'Unknown')}")
                    print(f"   Description: {rule.get('omschrijving', 'No description')[:100]}...")
                    print(f"   Article: {rule.get('labelXml', '')} {rule.get('nummerXml', '')}")
                    print(f"   Status: {rule.get('procedurestatus', 'Unknown')}")
            else:
                print("❌ FAILED")
                print(f"   Error: {legal_source_result.get('error')}")

            # Test C: Get Rule Texts
            print(f"\n🔍 C) RULE TEXTS TEST")
            print("-" * 30)

            rule_texts_result = detailed_query_client.get_rule_texts(
                sample_activity_id, renovation_type=renovation_type
            )

            if rule_texts_result['success']:
                print("✅ SUCCESS")
                data = rule_texts_result['data']
                print(f"📊 Rule Texts Results:")
                print(f"   Rule texts found: {data['total_found']}")
                print(f"   Response time: {data['response_metadata']['duration']:.2f}s")

                if data['rule_texts']:
                    print(f"\n📋 Rule Texts Sample (first 3):")
                    for i, rule in enumerate(data['rule_texts'][:3], 1):
                        print(f"   {i}. {rule.get('identificatie', 'Unknown')}")
                        print(f"      Text: {rule.get('omschrijving', 'No description')[:80]}...")
                        print(f"      Document: {rule.get('documentIdentificatie', 'Unknown')}")
            else:
                print("❌ FAILED")
                print(f"   Error: {rule_texts_result.get('error')}")

        # Step 4: Test Location Search (if we had coordinates)
        print(f"\n4️⃣ LOCATION SEARCH TEST")
        print("-" * 50)

        # Use example coordinates (Amsterdam center) for testing
        test_coordinates = [121000, 487000]
        print(f"Testing with coordinates: {test_coordinates} (Amsterdam center)")

        location_result = detailed_query_client.search_locations(
            test_coordinates, renovation_type=renovation_type
        )

        if location_result['success']:
            print("✅ SUCCESS")
            data = location_result['data']
            print(f"📊 Location Search Results:")
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
            print(f"   Error: {location_result.get('error')}")

        # Save test summary to files
        test_summary = {
            "address": address,
            "renovation_type": renovation_type,
            "test_timestamp": datetime.now().isoformat(),
            "results": {
                "search_prerequisite": search_result.get('success', False),
                "functional_refs_extraction": len(functional_refs) > 0,
                "activity_validation": validation_result.get('success', False),
                "lifecycle_test": lifecycle_result.get('success', False) if 'lifecycle_result' in locals() else False,
                "legal_source_test": legal_source_result.get('success', False) if 'legal_source_result' in locals() else False,
                "rule_texts_test": rule_texts_result.get('success', False) if 'rule_texts_result' in locals() else False,
                "location_search_test": location_result.get('success', False)
            },
            "functional_references": functional_refs,
            "activity_ids": validation_result.get('data', {}).get('activity_ids', []) if validation_result.get('success') else [],
            "activity_details_summary": {
                "total_activities": len(activity_details),
                "successful_lookups": validation_result.get('data', {}).get('successful_lookups', 0) if validation_result.get('success') else 0
            },
            "location_search_results": location_result.get('data', {}).get('total_found', 0) if location_result.get('success') else 0
        }

        # Save to house-specific folder
        house_logger.save_renovation_test_results("dso_detailed_query_test", test_summary)

        print(f"\n" + "=" * 50)
        print("🎉 DSO DETAILED QUERY API TEST COMPLETE")
        print("=" * 50)

        # Summary
        success_count = sum([
            test_summary['results']['functional_refs_extraction'],
            test_summary['results']['activity_validation'],
            test_summary['results']['lifecycle_test'],
            test_summary['results']['legal_source_test'],
            test_summary['results']['rule_texts_test'],
            test_summary['results']['location_search_test']
        ])

        if success_count >= 4:
            print("✅ DSO Detailed Query API working excellently!")
            print(f"✅ Successfully tested {success_count}/6 core functions")
            print("🚀 Ready to test DSO Interactive API with detailed legal data")
        elif success_count >= 2:
            print("⚠️ DSO Detailed Query API partially working")
            print(f"⚠️ {success_count}/6 core functions succeeded")
            print("💡 Some legal details may be missing")
        else:
            print("❌ DSO Detailed Query API having issues")
            print("💡 Check activity IDs and API endpoints")

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