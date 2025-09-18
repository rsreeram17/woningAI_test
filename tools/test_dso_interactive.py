#!/usr/bin/env python3
"""Individual DSO Interactive API testing tool."""

import os
import sys
import argparse
from datetime import datetime

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.config import load_config
from src.api_clients.dso_search_api import DSOSearchAPI
from src.api_clients.dso_interactive_api import DSOInteractiveAPI
from src.api_clients.bag_client import BAGAPIClient
from src.utils.house_logger import HouseSpecificLogger

def test_dso_interactive(address: str, renovation_type: str):
    """Test DSO Interactive API with specific address and renovation type.

    Args:
        address: Dutch address (e.g., "1082GB 43-2")
        renovation_type: Type of renovation (e.g., "dakkapel", "uitbouw")
    """
    print("🎯 DSO Interactive API Individual Test")
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

        # Initialize house logger for file output
        house_logger = HouseSpecificLogger(address, f"DSO_Interactive_Test_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        print(f"📁 Created house-specific folder: {house_logger.house_folder}")

        # Initialize clients with house logger
        search_client = DSOSearchAPI(dso_config, house_logger=house_logger)
        interactive_client = DSOInteractiveAPI(dso_config, house_logger=house_logger)
        bag_client = BAGAPIClient(bag_config, house_logger=house_logger)
        print("✅ API Clients initialized with logging")

        print(f"\n" + "=" * 50)
        print("🚀 GETTING REQUIRED DATA")
        print("=" * 50)

        # Step 1: Get coordinates from BAG API
        print(f"\n1️⃣ GETTING COORDINATES FROM BAG API")
        print("-" * 30)

        # Parse address
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

        bag_result = bag_client.get_address_extended(address_dict)

        if not bag_result['success']:
            print("❌ FAILED - Cannot get coordinates")
            print(f"   Error: {bag_result.get('error')}")
            return

        coordinates = bag_client.extract_coordinates(bag_result)
        if not coordinates:
            print("❌ FAILED - No coordinates found")
            return

        print("✅ SUCCESS")
        print(f"   Coordinates: [{coordinates[0]}, {coordinates[1]}] (RD format)")

        # Step 2: Get functional structure references
        print(f"\n2️⃣ GETTING FUNCTIONAL STRUCTURE REFERENCES")
        print("-" * 30)

        search_result = search_client.search_activities(renovation_type)

        if not search_result['success']:
            print("❌ FAILED - Cannot get search results")
            print(f"   Error: {search_result.get('error')}")
            return

        functional_refs = search_client.extract_functional_structure_refs(search_result)

        if not functional_refs:
            print("❌ FAILED - No functional structure references found")
            return

        print("✅ SUCCESS")
        print(f"   Found {len(functional_refs)} functional references")
        print(f"   Sample: {functional_refs[0][:80]}...")

        print(f"\n" + "=" * 50)
        print("🚀 RUNNING DSO INTERACTIVE TESTS")
        print("=" * 50)

        # Test 1: Permit Requirement Check
        print(f"\n1️⃣ PERMIT REQUIREMENT CHECK")
        print("-" * 30)

        permit_result = interactive_client.check_permit_requirement(
            functional_structure_refs=functional_refs[:5],  # Use first 5 refs
            coordinates=coordinates,
            renovation_type=renovation_type
        )

        if permit_result['success']:
            print("✅ SUCCESS")
            analysis = permit_result['data']['permit_analysis']

            print(f"📊 Permit Analysis:")
            print(f"   Activities analyzed: {analysis['activities_analyzed']}")
            print(f"   Permit required: {analysis['permit_required']}")
            print(f"   Conclusions found: {len(analysis['conclusions'])}")
            print(f"   Question groups: {len(analysis['question_groups'])}")

            if analysis['conclusions']:
                print(f"\n📋 Key Conclusions:")
                for i, conclusion in enumerate(analysis['conclusions'][:3], 1):
                    print(f"   {i}. {conclusion['text'][:80]}...")

            if analysis['issues']:
                print(f"\n⚠️ Issues:")
                for issue in analysis['issues']:
                    print(f"   • {issue}")
        else:
            print("❌ FAILED")
            print(f"   Error: {permit_result.get('error')}")

        # Test 2: Filing Requirements
        print(f"\n2️⃣ FILING REQUIREMENTS")
        print("-" * 30)

        filing_result = interactive_client.get_filing_requirements(
            functional_structure_refs=functional_refs[:5],
            coordinates=coordinates,
            renovation_type=renovation_type
        )

        if filing_result['success']:
            print("✅ SUCCESS")
            analysis = filing_result['data']['filing_analysis']

            print(f"📊 Filing Analysis:")
            print(f"   Total requirements: {analysis['total_requirements']}")
            print(f"   Documents required: {len(analysis['documents_required'])}")

            if analysis['categories']:
                print(f"\n📂 Document Categories:")
                for category, count in analysis['categories'].items():
                    print(f"   • {category}: {count} documents")

            if analysis['documents_required']:
                print(f"\n📄 Required Documents (top 3):")
                for i, doc in enumerate(analysis['documents_required'][:3], 1):
                    required = "Required" if doc['required'] else "Optional"
                    print(f"   {i}. {doc['name']} ({required})")
        else:
            print("❌ FAILED")
            print(f"   Error: {filing_result.get('error')}")

        # Test 3: Compliance Measures
        print(f"\n3️⃣ COMPLIANCE MEASURES")
        print("-" * 30)

        compliance_result = interactive_client.get_compliance_measures(
            functional_structure_refs=functional_refs[:5],
            coordinates=coordinates,
            renovation_type=renovation_type
        )

        if compliance_result['success']:
            print("✅ SUCCESS")
            analysis = compliance_result['data']['compliance_analysis']

            print(f"📊 Compliance Analysis:")
            print(f"   Total measures: {analysis['total_measures']}")
            print(f"   Compliance score: {analysis['compliance_score']}/100")

            if analysis['measures']:
                print(f"\n📋 Key Measures (top 3):")
                for i, measure in enumerate(analysis['measures'][:3], 1):
                    mandatory = "Mandatory" if measure['mandatory'] else "Optional"
                    print(f"   {i}. {measure['name']} ({mandatory})")
        else:
            print("❌ FAILED")
            print(f"   Error: {compliance_result.get('error')}")

        # Test 4: Complete Interactive Flow
        print(f"\n4️⃣ COMPLETE INTERACTIVE FLOW")
        print("-" * 30)

        flow_result = interactive_client.run_complete_interactive_flow(
            functional_structure_refs=functional_refs[:3],
            coordinates=coordinates,
            renovation_type=renovation_type
        )

        if flow_result['success']:
            print("✅ SUCCESS")
            summary = flow_result['data']['flow_summary']

            print(f"📊 Flow Summary:")
            print(f"   Steps completed: {summary['steps_completed']}")
            print(f"   Steps successful: {summary['steps_successful']}")
            print(f"   Success rate: {summary['success_rate']*100:.1f}%")
            print(f"   Total duration: {summary['total_duration']:.2f}s")
        else:
            print("❌ FAILED")
            print(f"   Error: {flow_result.get('error')}")

        print(f"\n" + "=" * 50)
        print("🎉 DSO INTERACTIVE API TEST COMPLETE")
        print("=" * 50)

        # Calculate overall success
        tests = [permit_result, filing_result, compliance_result, flow_result]
        successful = sum(1 for test in tests if test.get('success'))
        success_rate = (successful / len(tests)) * 100

        print(f"📊 Overall Success Rate: {success_rate:.1f}% ({successful}/{len(tests)})")

        if success_rate >= 75:
            print("✅ DSO Interactive API working excellently!")
        elif success_rate >= 50:
            print("✅ DSO Interactive API working with some issues")
        else:
            print("❌ DSO Interactive API has significant issues")

        # Business summary
        if permit_result.get('success'):
            permit_analysis = permit_result['data']['permit_analysis']
            permit_required = permit_analysis.get('permit_required')

            print(f"\n🎯 Business Summary for {address}:")
            if permit_required is True:
                print(f"   🟡 PERMIT REQUIRED for {renovation_type}")
            elif permit_required is False:
                print(f"   🟢 NO PERMIT REQUIRED for {renovation_type}")
            else:
                print(f"   🟡 PERMIT STATUS UNCLEAR for {renovation_type}")

            if filing_result.get('success'):
                filing_analysis = filing_result['data']['filing_analysis']
                print(f"   📄 Documents needed: {filing_analysis['total_requirements']}")

        # Save test summary to files
        test_summary = {
            "address": address,
            "renovation_type": renovation_type,
            "test_timestamp": datetime.now().isoformat(),
            "results": {
                "permit_check": permit_result.get('success', False),
                "filing_requirements": filing_result.get('success', False),
                "compliance_measures": compliance_result.get('success', False),
                "complete_flow": flow_result.get('success', False)
            },
            "coordinates": coordinates_result.get('coordinates', []) if coordinates_result.get('success') else [],
            "functional_references": functional_refs,
            "permit_analysis": permit_result.get('data', {}).get('permit_analysis', {}) if permit_result.get('success') else {},
            "filing_analysis": filing_result.get('data', {}).get('filing_analysis', {}) if filing_result.get('success') else {},
            "compliance_analysis": compliance_result.get('data', {}).get('compliance_analysis', {}) if compliance_result.get('success') else {},
            "success_rate": success_rate
        }

        # Save to house-specific folder
        house_logger.save_renovation_test_results("dso_interactive_test", test_summary)

        print(f"\n📁 Results saved to:")
        print(f"   • House folder: {house_logger.house_folder}")
        print(f"   • Output folder: {house_logger.output_folder}")

        print(f"\n📁 Next steps:")
        print(f"   • Test DSO Routing: python tools/test_dso_routing.py '{address}' {renovation_type}")
        print(f"   • View saved results: ls {house_logger.house_folder}")
        print(f"   • Test full integration: python run_tests.py")

    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description='Test DSO Interactive API with specific address and renovation')
    parser.add_argument('address', help='Dutch address (e.g., "1082GB 43-2")')
    parser.add_argument('renovation_type', help='Renovation type (e.g., "dakkapel", "uitbouw")')

    args = parser.parse_args()
    test_dso_interactive(args.address, args.renovation_type)

if __name__ == "__main__":
    main()