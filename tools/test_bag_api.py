#!/usr/bin/env python3
"""Individual BAG API testing tool."""

import os
import sys
import argparse
from datetime import datetime

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.config import load_config
from src.api_clients.bag_client import BAGAPIClient
from src.utils.house_logger import HouseSpecificLogger

def test_bag_api(address: str):
    """Test BAG API with a specific address.

    Args:
        address: Dutch address (postcode + number, e.g., "1082GB 43-2")
    """
    print("🏠 BAG API Individual Test")
    print("=" * 50)
    print(f"Testing address: {address}")

    try:
        # Load configuration
        config = load_config()
        bag_config = config.get_bag_config()

        print(f"\n🔧 Configuration:")
        print(f"   API Key: {bag_config['api_key'][:10]}...")
        print(f"   Base URL: {bag_config['base_url']}")

        # Initialize house logger for file output
        house_logger = HouseSpecificLogger(address, f"BAG_API_Test_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        print(f"📁 Created house-specific folder: {house_logger.house_folder}")

        # Initialize BAG client with house logger
        bag_client = BAGAPIClient(bag_config, house_logger=house_logger)
        print("✅ BAG Client initialized with logging")

        # Parse address into components if it's a string
        if isinstance(address, str):
            # Try to parse as "postcode number-addition" format
            parts = address.split()
            if len(parts) >= 2:
                postcode = parts[0]
                number_part = parts[1]

                # Handle number with addition (e.g., "43-2")
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
                print("❌ Invalid address format. Use: 'postcode number' or 'postcode number-addition'")
                return
        else:
            address_dict = address

        print(f"\n📋 Address components:")
        for key, value in address_dict.items():
            print(f"   {key}: {value}")

        print(f"\n" + "=" * 50)
        print("🚀 RUNNING BAG API TESTS")
        print("=" * 50)

        # Test 1: Basic Address Search
        print(f"\n1️⃣ BASIC ADDRESS SEARCH")
        print("-" * 30)

        basic_result = bag_client.search_address(address_dict)

        if basic_result['success']:
            print("✅ SUCCESS")
            data = basic_result['data']
            address_found = data['address_found']

            print(f"📍 Address found:")
            print(f"   Street: {address_found.get('openbareRuimteNaam', 'Unknown')}")
            print(f"   Number: {address_found.get('huisnummer')}{'-' + address_found.get('huisnummertoevoeging', '') if address_found.get('huisnummertoevoeging') else ''}")
            print(f"   Postcode: {address_found.get('postcode')}")
            print(f"   City: {address_found.get('woonplaatsNaam')}")
            print(f"   Response time: {data['response_metadata']['duration']:.2f}s")
        else:
            print("❌ FAILED")
            print(f"   Error: {basic_result.get('error')}")
            return

        # Test 2: Extended Address Search
        print(f"\n2️⃣ EXTENDED ADDRESS SEARCH")
        print("-" * 30)

        extended_result = bag_client.get_address_extended(address_dict)

        if extended_result['success']:
            print("✅ SUCCESS")
            data = extended_result['data']

            print(f"🏗️ Building Information:")
            building = data['building']
            print(f"   Construction year: {building.get('bouwjaar', 'Unknown')}")
            print(f"   Surface area: {building.get('oppervlakte', 'Unknown')} m²")
            print(f"   Usage: {building.get('gebruiksdoel', 'Unknown')}")
            print(f"   Object type: {building.get('object_type', 'Unknown')}")

            print(f"🗺️ Coordinates:")
            coordinates = data['coordinates']
            if coordinates:
                print(f"   X: {coordinates[0]} (RD format)")
                print(f"   Y: {coordinates[1]} (RD format)")
                print("   ✅ Ready for DSO API integration")
            else:
                print("   ❌ No coordinates found")

            print(f"   Response time: {data['response_metadata']['duration']:.2f}s")
        else:
            print("❌ FAILED")
            print(f"   Error: {extended_result.get('error')}")

        # Test 3: Complete Validation
        print(f"\n3️⃣ COMPLETE VALIDATION")
        print("-" * 30)

        validation_result = bag_client.validate_address_for_testing(address_dict)

        if validation_result['success']:
            print("✅ SUCCESS")

            print(f"🎯 Validation Summary:")
            summary = validation_result.get('validation_summary', {})
            for step, status in summary.items():
                print(f"   • {step}: {status}")

            coordinates = validation_result.get('coordinates')
            if coordinates:
                print(f"\n📊 Final Results:")
                print(f"   ✅ Address validated successfully")
                print(f"   ✅ Building data retrieved")
                print(f"   ✅ Coordinates extracted: [{coordinates[0]}, {coordinates[1]}]")
                print(f"   ✅ Ready for DSO integration")
            else:
                print(f"   ❌ Coordinates missing")
        else:
            print("❌ FAILED")
            print(f"   Error: {validation_result.get('error')}")
            print(f"   Failed at: {validation_result.get('validation_step')}")

        # Save test summary to files
        test_summary = {
            "address": address,
            "address_components": address_dict,
            "test_timestamp": datetime.now().isoformat(),
            "results": {
                "basic_search": basic_result.get('success', False),
                "extended_search": extended_result.get('success', False),
                "validation": validation_result.get('success', False)
            },
            "building_data": extended_result.get('data', {}).get('building', {}) if extended_result.get('success') else {},
            "coordinates": validation_result.get('coordinates') if validation_result.get('success') else None
        }

        # Save to house-specific folder
        house_logger.save_renovation_test_results("bag_api_test", test_summary)

        print(f"\n" + "=" * 50)
        print("🎉 BAG API TEST COMPLETE")
        print("=" * 50)

        if validation_result.get('success'):
            print("✅ Your address works with the BAG API!")
            print("🚀 Ready to test DSO APIs")
        else:
            print("❌ Address validation failed")
            print("💡 Check address format or try a different address")

        print(f"\n📁 Results saved to:")
        print(f"   • House folder: {house_logger.house_folder}")
        print(f"   • Output folder: {house_logger.output_folder}")

        print(f"\n📁 Next steps:")
        print(f"   • Test DSO Search: python tools/test_dso_search.py '{address}' dakkapel")
        print(f"   • View saved results: ls {house_logger.house_folder}")
        print(f"   • Test full integration: python run_tests.py")

    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description='Test BAG API with a specific address')
    parser.add_argument('address', help='Dutch address (e.g., "1082GB 43-2")')

    args = parser.parse_args()
    test_bag_api(args.address)

if __name__ == "__main__":
    main()