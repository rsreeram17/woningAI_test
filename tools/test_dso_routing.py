#!/usr/bin/env python3
"""Individual DSO Routing API testing tool."""

import os
import sys
import argparse
from datetime import datetime

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.config import load_config
from src.api_clients.dso_routing_api import DSORoutingAPI
from src.api_clients.dso_search_api import DSOSearchAPI
from src.api_clients.bag_client import BAGAPIClient
from src.utils.house_logger import HouseSpecificLogger

def test_dso_routing(address: str, renovation_type: str):
    """Test DSO Routing API with specific address and renovation type.

    Args:
        address: Dutch address (e.g., "1082GB 43-2")
        renovation_type: Type of renovation (e.g., "dakkapel", "uitbouw")
    """
    print("🗺️ DSO Routing API Individual Test")
    print("=" * 50)
    print(f"Address: {address}")
    print(f"Renovation type: {renovation_type}")

    try:
        # Load configuration
        config = load_config()
        dso_config = config.get_dso_config()
        bag_config = config.get_bag_config()

        print(f"\n🔧 Configuration:")
        print(f"   DSO API Key: {dso_config['api_key'][:10]}...")
        print(f"   BAG API Key: {bag_config['api_key'][:10]}...")
        print(f"   Base URL: {dso_config['production_url']}")

        # Initialize house logger for file output
        house_logger = HouseSpecificLogger(address, f"DSO_Routing_Test_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        print(f"📁 Created house-specific folder: {house_logger.house_folder}")

        # Initialize clients with house logger
        routing_client = DSORoutingAPI(dso_config, house_logger=house_logger)
        search_client = DSOSearchAPI(dso_config, house_logger=house_logger)
        bag_client = BAGAPIClient(bag_config, house_logger=house_logger)
        print("✅ DSO Routing Client initialized with logging")

        print(f"\n" + "=" * 50)
        print("🚀 RUNNING DSO ROUTING TESTS")
        print("=" * 50)

        # Initialize result variables
        coordinates_result = {}
        search_result = {}
        functional_refs = []
        authority_result = {}
        concept_request_result = {}
        processing_service_result = {}

        # Step 1: Get coordinates from address
        print(f"\n1️⃣ GET COORDINATES FROM ADDRESS")
        print("-" * 50)

        # Parse address for BAG API
        if isinstance(address, str):
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
                print(f"❌ Invalid address format")
                return

        coordinates_result = bag_client.get_address_extended(address_dict, renovation_type=renovation_type)

        if coordinates_result['success']:
            coordinates = bag_client.extract_coordinates(coordinates_result)
            if coordinates:
                print(f"✅ SUCCESS")
                print(f"📍 Coordinates: [{coordinates[0]}, {coordinates[1]}] (RD format)")
            else:
                print(f"❌ Could not extract coordinates")
                return
        else:
            print(f"❌ FAILED to get coordinates")
            print(f"   Error: {coordinates_result.get('error')}")
            return

        # Step 2: Get functional structure references
        print(f"\n2️⃣ GET FUNCTIONAL STRUCTURE REFERENCES")
        print("-" * 50)

        search_result = search_client.search_activities(renovation_type, renovation_type=renovation_type)

        if search_result['success']:
            functional_refs = search_client.extract_functional_structure_refs(search_result)
            print(f"✅ Found {len(functional_refs)} functional structure references")

            if functional_refs:
                print(f"📋 Sample references:")
                for i, ref in enumerate(functional_refs[:2], 1):
                    print(f"   {i}. {ref[:80]}...")
            else:
                print("❌ No functional references found")
                return
        else:
            print("❌ Search failed")
            print(f"   Error: {search_result.get('error')}")
            return

        # Step 3: Find Responsible Authority
        print(f"\n3️⃣ FIND RESPONSIBLE AUTHORITY")
        print("-" * 50)

        authority_result = routing_client.find_responsible_authority(
            functional_refs, coordinates, renovation_type=renovation_type
        )

        if authority_result['success']:
            print("✅ SUCCESS")
            data = authority_result['data']

            if data['authorities']:
                print(f"📊 Authority Results:")
                print(f"   Authorities found: {data['total_authorities']}")
                print(f"   Response time: {data['response_metadata']['duration']:.2f}s")

                print(f"\n🏛️ Responsible Authorities:")
                for i, auth in enumerate(data['authorities'][:3], 1):
                    print(f"   {i}. {auth.get('naam', 'Unknown')}")
                    print(f"      OIN: {auth.get('oin', 'Unknown')}")
                    print(f"      Level: {auth.get('bestuurslaag', 'Unknown')}")
                    print(f"      Contact: {auth.get('contactgegevens', 'No contact info')}")

                # Use first authority for subsequent tests
                primary_authority = data['authorities'][0]
                authority_oin = primary_authority.get('oin')
            else:
                print("❌ No authorities found")
                authority_oin = None
        else:
            print("❌ FAILED")
            print(f"   Error: {authority_result.get('error')}")
            authority_oin = None

        # Step 4: Check Concept Request Allowed (if we have authority)
        if authority_oin:
            print(f"\n4️⃣ CHECK CONCEPT REQUEST ALLOWED")
            print("-" * 50)

            concept_request_result = routing_client.check_concept_request_allowed(
                authority_oin, functional_refs, renovation_type=renovation_type
            )

            if concept_request_result['success']:
                print("✅ SUCCESS")
                data = concept_request_result['data']

                print(f"📊 Concept Request Results:")
                print(f"   Authority OIN: {data.get('authority_oin', 'Unknown')}")
                print(f"   Concept request allowed: {data.get('concept_allowed', 'Unknown')}")
                print(f"   Response time: {data['response_metadata']['duration']:.2f}s")

                if data.get('restrictions'):
                    print(f"\n📋 Restrictions:")
                    for restriction in data['restrictions']:
                        print(f"   • {restriction}")
            else:
                print("❌ FAILED")
                print(f"   Error: {concept_request_result.get('error')}")

            # Step 5: Find Processing Service
            print(f"\n5️⃣ FIND PROCESSING SERVICE")
            print("-" * 50)

            processing_service_result = routing_client.find_processing_service(
                authority_oin, functional_refs, coordinates, renovation_type=renovation_type
            )

            if processing_service_result['success']:
                print("✅ SUCCESS")
                data = processing_service_result['data']

                print(f"📊 Processing Service Results:")
                print(f"   Authority OIN: {data.get('authority_oin', 'Unknown')}")
                print(f"   Services found: {data.get('total_services', 0)}")
                print(f"   Response time: {data['response_metadata']['duration']:.2f}s")

                if data.get('services'):
                    print(f"\n🏢 Processing Services:")
                    for i, service in enumerate(data['services'][:3], 1):
                        print(f"   {i}. {service.get('naam', 'Unknown')}")
                        print(f"      Type: {service.get('type', 'Unknown')}")
                        print(f"      URL: {service.get('url', 'No URL')}")
            else:
                print("❌ FAILED")
                print(f"   Error: {processing_service_result.get('error')}")
        else:
            print(f"\n4️⃣ SKIP CONCEPT REQUEST CHECK (no authority OIN)")
            print("-" * 50)
            print("⚠️ Skipped - no authority OIN available")

            print(f"\n5️⃣ SKIP PROCESSING SERVICE CHECK (no authority OIN)")
            print("-" * 50)
            print("⚠️ Skipped - no authority OIN available")

        # Save test summary to files
        test_summary = {
            "address": address,
            "renovation_type": renovation_type,
            "test_timestamp": datetime.now().isoformat(),
            "results": {
                "coordinates_lookup": coordinates_result.get('success', False),
                "functional_refs_search": search_result.get('success', False),
                "authority_search": authority_result.get('success', False),
                "concept_request_check": concept_request_result.get('success', False),
                "processing_service_search": processing_service_result.get('success', False)
            },
            "coordinates": coordinates if coordinates_result.get('success') else [],
            "functional_references": functional_refs,
            "authorities_found": authority_result.get('data', {}).get('total_authorities', 0) if authority_result.get('success') else 0,
            "primary_authority": authority_result.get('data', {}).get('authorities', [{}])[0] if authority_result.get('success') and authority_result.get('data', {}).get('authorities') else {},
            "concept_request_allowed": concept_request_result.get('data', {}).get('concept_allowed') if concept_request_result.get('success') else None,
            "processing_services_found": processing_service_result.get('data', {}).get('total_services', 0) if processing_service_result.get('success') else 0
        }

        # Save to house-specific folder
        house_logger.save_renovation_test_results("dso_routing_test", test_summary)

        print(f"\n" + "=" * 50)
        print("🎉 DSO ROUTING API TEST COMPLETE")
        print("=" * 50)

        # Calculate success rate
        tests = [coordinates_result, search_result, authority_result, concept_request_result, processing_service_result]
        successful = sum(1 for test in tests if test.get('success'))
        success_rate = (successful / len(tests)) * 100

        print(f"📊 Overall Success Rate: {success_rate:.1f}% ({successful}/{len(tests)})")

        if success_rate >= 75:
            print("✅ DSO Routing API working excellently!")
            print("🚀 Ready to route permit applications to correct authorities")
        elif success_rate >= 50:
            print("⚠️ DSO Routing API partially working")
            print("💡 Some routing functions may be limited")
        else:
            print("❌ DSO Routing API having significant issues")
            print("💡 Check authority lookup and service routing")

        # Business summary
        if authority_result.get('success') and authority_result.get('data', {}).get('authorities'):
            primary_auth = authority_result['data']['authorities'][0]
            print(f"\n🎯 Business Summary for {address}:")
            print(f"   🏛️ Responsible Authority: {primary_auth.get('naam', 'Unknown')}")
            print(f"   📝 Authority Level: {primary_auth.get('bestuurslaag', 'Unknown')}")
            print(f"   📞 Contact Authority for {renovation_type} permits")

            if concept_request_result.get('success'):
                concept_allowed = concept_request_result.get('data', {}).get('concept_allowed')
                if concept_allowed:
                    print(f"   ✅ Concept requests allowed")
                else:
                    print(f"   ❌ Concept requests not allowed")

        print(f"\n📁 Results saved to:")
        print(f"   • House folder: {house_logger.house_folder}")
        print(f"   • Output folder: {house_logger.output_folder}")

        print(f"\n📁 Next steps:")
        print(f"   • Test DSO Catalog: python tools/test_dso_catalog.py '{address}' {renovation_type}")
        print(f"   • View saved results: ls {house_logger.house_folder}")
        print(f"   • Test full integration: python run_tests.py")

    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description='Test DSO Routing API with specific address and renovation')
    parser.add_argument('address', help='Dutch address (e.g., "1082GB 43-2")')
    parser.add_argument('renovation_type', help='Renovation type (e.g., "dakkapel", "uitbouw")')

    args = parser.parse_args()
    test_dso_routing(args.address, args.renovation_type)

if __name__ == "__main__":
    main()