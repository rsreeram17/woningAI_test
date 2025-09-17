#!/usr/bin/env python3
"""Test BAG API with the updated framework for your address."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import load_config
from src.api_clients.bag_client import BAGAPIClient

def test_bag_with_framework():
    """Test BAG API using the complete framework."""

    print("🏠 BAG API Test with Updated Framework")
    print("Your Address: 1082GB 43-2 (Overvoorde 43-2, Amsterdam)")
    print("="*80)

    try:
        # Load configuration
        config = load_config()
        bag_config = config.get_bag_config()

        print("🔧 Configuration Loaded:")
        print(f"   API Key: {bag_config['api_key'][:10]}...")
        print(f"   Base URL: {bag_config['base_url']}")
        print(f"   Timeout: {bag_config['timeout']}s")

        # Initialize BAG client
        bag_client = BAGAPIClient(bag_config)
        print("✅ BAG Client initialized")

        # Your address as it appears in config.yaml
        your_address = {
            'postcode': '1082GB',
            'huisnummer': 43,
            'huisnummertoevoeging': '2',
            'house_name': 'Amsterdam House 43-2',
            'description': 'House with toevoeging number',
            'priority': 'high'
        }

        print(f"\n📋 Testing Address Config:")
        print(f"   Postcode: {your_address['postcode']}")
        print(f"   Huisnummer: {your_address['huisnummer']}")
        print(f"   Huisnummertoevoeging: {your_address['huisnummertoevoeging']}")

        print(f"\n" + "="*80)
        print("🚀 RUNNING BAG API TESTS")
        print("="*80)

        # Test 1: Basic Address Search
        print(f"\n1️⃣ BASIC ADDRESS SEARCH")
        print("-" * 50)

        basic_result = bag_client.search_address(your_address)

        print(f"Result: {'✅ SUCCESS' if basic_result.get('success') else '❌ FAILED'}")

        if basic_result.get('success'):
            data = basic_result['data']
            address_found = data['address_found']
            search_params = data['search_params']

            print(f"📡 API Parameters used: {search_params}")
            print(f"📍 Address found:")
            print(f"   Street: {address_found.get('openbareRuimteNaam', 'Unknown')}")
            print(f"   Number: {address_found.get('huisnummer')}-{address_found.get('huisnummertoevoeging')}")
            print(f"   Postcode: {address_found.get('postcode')}")
            print(f"   City: {address_found.get('woonplaatsNaam')}")
            print(f"   Display: {address_found.get('adresregel5', 'Unknown')}")
        else:
            print(f"❌ Error: {basic_result.get('error')}")
            print(f"🔍 Debug info: {basic_result}")

        # Test 2: Extended Address Search
        print(f"\n2️⃣ EXTENDED ADDRESS SEARCH")
        print("-" * 50)

        extended_result = bag_client.get_address_extended(your_address)

        print(f"Result: {'✅ SUCCESS' if extended_result.get('success') else '❌ FAILED'}")

        if extended_result.get('success'):
            data = extended_result['data']
            address_info = data['address']
            building_info = data['building']
            coordinates = data['coordinates']

            print(f"📍 Complete Address Info:")
            print(f"   Formatted: {address_info.get('formatted_address', 'Unknown')}")
            print(f"   Street: {address_info.get('straatnaam', 'Unknown')}")
            print(f"   City: {address_info.get('plaatsnaam', 'Unknown')}")
            print(f"   Municipality: {address_info.get('gemeente', 'Unknown')}")

            print(f"🏗️ Building Information:")
            print(f"   Construction year: {building_info.get('bouwjaar', 'Unknown')}")
            print(f"   Surface area: {building_info.get('oppervlakte', 'Unknown')} m²")
            print(f"   Usage purpose: {building_info.get('gebruiksdoel', 'Unknown')}")
            print(f"   Object type: {building_info.get('object_type', 'Unknown')}")
            print(f"   Building status: {building_info.get('pand_status', 'Unknown')}")

            print(f"🗺️ Coordinates (RD format for DSO):")
            if coordinates:
                print(f"   X: {coordinates[0]}")
                print(f"   Y: {coordinates[1]}")
                print(f"   Ready for DSO integration: ✅")
            else:
                print(f"   ❌ No coordinates found")

        else:
            print(f"❌ Error: {extended_result.get('error')}")

        # Test 3: Complete Validation
        print(f"\n3️⃣ COMPLETE ADDRESS VALIDATION")
        print("-" * 50)

        validation_result = bag_client.validate_address_for_testing(your_address)

        print(f"Result: {'✅ SUCCESS' if validation_result.get('success') else '❌ FAILED'}")

        if validation_result.get('success'):
            print(f"🎯 Validation Summary:")
            summary = validation_result.get('validation_summary', {})
            for step, status in summary.items():
                print(f"   • {step}: {status}")

            print(f"🚀 Integration Status:")
            print(f"   Ready for DSO testing: {'✅' if summary.get('ready_for_dso_testing') else '❌'}")

            coordinates = validation_result.get('coordinates')
            if coordinates:
                print(f"   Coordinates available: ✅ [{coordinates[0]}, {coordinates[1]}]")
            else:
                print(f"   Coordinates available: ❌")

        else:
            print(f"❌ Validation failed: {validation_result.get('error')}")
            print(f"   Failed at step: {validation_result.get('validation_step')}")

        print(f"\n" + "="*80)
        print("🎉 SUMMARY")
        print("="*80)

        if validation_result.get('success'):
            print("✅ Your address 1082GB 43-2 works perfectly with the framework!")
            print("✅ BAG API returns complete building and location data")
            print("✅ Framework correctly handles huisnummertoevoeging")
            print("✅ Coordinates extracted for DSO API integration")
            print("🚀 Ready for full renovation testing!")
        else:
            print("❌ There are issues that need to be resolved before full testing")

        print(f"\n📁 Next steps:")
        print(f"   • Run full test: python run_tests.py")
        print(f"   • Quick test: python tools/quick_test.py '1082GB 43-2' dakkapel")
        print(f"   • View results: python tools/house_viewer.py '1082GB 43-2'")

    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_bag_with_framework()