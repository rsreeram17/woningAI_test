#!/usr/bin/env python3
"""Individual DSO Search API testing tool."""

import os
import sys
import argparse
from datetime import datetime

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.config import load_config
from src.api_clients.dso_search_api import DSOSearchAPI
from src.utils.house_logger import HouseSpecificLogger

def test_dso_search(address: str, renovation_type: str):
    """Test DSO Search API with specific renovation type.

    Args:
        address: Dutch address (for display only)
        renovation_type: Type of renovation (e.g., "dakkapel", "uitbouw")
    """
    print("🔍 DSO Search API Individual Test")
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
        house_logger = HouseSpecificLogger(address, f"DSO_Search_Test_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        print(f"📁 Created house-specific folder: {house_logger.house_folder}")

        # Initialize DSO Search client with house logger
        search_client = DSOSearchAPI(dso_config, house_logger=house_logger)
        print("✅ DSO Search Client initialized with logging")

        # Get search terms for this renovation type
        renovation_scenarios = config.get_renovation_scenarios()
        scenario = None
        for s in renovation_scenarios:
            if s['type'] == renovation_type:
                scenario = s
                break

        if not scenario:
            # Use the renovation type directly
            search_terms = [renovation_type]
            print(f"⚠️ No predefined scenario for '{renovation_type}', using direct search")
        else:
            search_terms = scenario.get('search_terms', [renovation_type])
            print(f"📋 Using scenario: {scenario['description']}")

        print(f"🔍 Search terms: {search_terms}")

        print(f"\n" + "=" * 50)
        print("🚀 RUNNING DSO SEARCH TESTS")
        print("=" * 50)

        # Initialize result variables
        single_result = {}
        multi_result = {}
        functional_refs = []
        analysis = {}
        suggestions_result = {}

        # Test 1: Single Search
        print(f"\n1️⃣ SINGLE SEARCH TEST")
        print("-" * 30)

        primary_term = search_terms[0]
        print(f"Searching for: '{primary_term}'")

        single_result = search_client.search_activities(primary_term, renovation_type=renovation_type)

        if single_result['success']:
            print("✅ SUCCESS")
            data = single_result['data']

            print(f"📊 Results:")
            print(f"   Activities found: {data['total_found']}")
            print(f"   Response time: {data['response_metadata']['duration']:.2f}s")

            if data['activities']:
                print(f"\n📋 Top 3 Activities:")
                for i, activity in enumerate(data['activities'][:3], 1):
                    name = activity.get('naam', 'Unknown')
                    ref = activity.get('functioneleStructuurRef', 'No reference')
                    print(f"   {i}. {name}")
                    print(f"      Reference: {ref[:80]}...")
        else:
            print("❌ FAILED")
            print(f"   Error: {single_result.get('error')}")
            return

        # Test 2: Multiple Search Terms
        if len(search_terms) > 1:
            print(f"\n2️⃣ MULTIPLE SEARCH TERMS TEST")
            print("-" * 30)

            multi_result = search_client.search_with_multiple_terms(search_terms, renovation_type=renovation_type)

            if multi_result['success']:
                print("✅ SUCCESS")
                data = multi_result['data']
                summary = data['summary']

                print(f"📊 Multi-Search Results:")
                print(f"   Terms searched: {summary['terms_searched']}")
                print(f"   Successful searches: {summary['successful_searches']}")
                print(f"   Total unique activities: {summary['total_activities_found']}")

                print(f"\n📋 Results by search term:")
                for term, result in data['individual_results'].items():
                    if result.get('success'):
                        count = len(result['data']['activities'])
                        print(f"   '{term}': {count} activities")
                    else:
                        print(f"   '{term}': Failed")

                # Use multi_result for functional refs
                final_result = multi_result
            else:
                print("❌ FAILED")
                print(f"   Error: {multi_result.get('error')}")
                final_result = single_result
        else:
            final_result = single_result

        # Test 3: Extract Functional Structure References
        print(f"\n3️⃣ FUNCTIONAL STRUCTURE REFERENCES")
        print("-" * 30)

        functional_refs = search_client.extract_functional_structure_refs(final_result)

        if functional_refs:
            print("✅ SUCCESS")
            print(f"📋 Extracted {len(functional_refs)} references:")
            for i, ref in enumerate(functional_refs[:5], 1):
                print(f"   {i}. {ref}")
            if len(functional_refs) > 5:
                print(f"   ... and {len(functional_refs) - 5} more")

            print(f"\n💾 References saved for next API tests")
        else:
            print("❌ FAILED")
            print("   No functional structure references found")

        # Test 4: Search Quality Analysis
        print(f"\n4️⃣ SEARCH QUALITY ANALYSIS")
        print("-" * 30)

        analysis = search_client.analyze_search_quality(final_result, renovation_type)

        print(f"📈 Quality Analysis:")
        print(f"   Quality Score: {analysis['quality_score']}/100")
        print(f"   Total Activities: {analysis['total_activities']}")
        print(f"   Relevant Activities: {analysis['relevant_activities']}")

        if analysis['activity_types']:
            print(f"   Activity Types:")
            for activity_type, count in analysis['activity_types'].items():
                print(f"     • {activity_type}: {count}")

        if analysis['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in analysis['recommendations']:
                print(f"   • {rec}")

        # Test 5: Search Suggestions
        print(f"\n5️⃣ SEARCH SUGGESTIONS")
        print("-" * 30)

        partial_term = primary_term[:4]
        suggestions_result = search_client.get_suggestions(partial_term, renovation_type=renovation_type)

        if suggestions_result['success']:
            print("✅ SUCCESS")
            data = suggestions_result['data']
            suggestions = data['suggestions']

            print(f"📊 Suggestions for '{partial_term}':")
            if suggestions:
                for i, suggestion in enumerate(suggestions[:5], 1):
                    print(f"   {i}. {suggestion}")
            else:
                print("   No suggestions found")
        else:
            print("❌ FAILED")
            print(f"   Error: {suggestions_result.get('error')}")

        # Save test summary to files
        test_summary = {
            "address": address,
            "renovation_type": renovation_type,
            "test_timestamp": datetime.now().isoformat(),
            "results": {
                "single_search": single_result.get('success', False),
                "multiple_search": multi_result.get('success', False) if len(search_terms) > 1 else True,
                "functional_refs_extraction": len(functional_refs) > 0 if functional_refs else False,
                "suggestions": suggestions_result.get('success', False)
            },
            "search_terms": search_terms,
            "functional_references": functional_refs if functional_refs else [],
            "quality_analysis": analysis,
            "total_activities_found": final_result.get('data', {}).get('total_found', 0) if final_result.get('success') else 0
        }

        # Save to house-specific folder
        house_logger.save_renovation_test_results("dso_search_test", test_summary)

        print(f"\n" + "=" * 50)
        print("🎉 DSO SEARCH API TEST COMPLETE")
        print("=" * 50)

        if functional_refs:
            print("✅ DSO Search API working perfectly!")
            print(f"✅ Found {len(functional_refs)} functional references")
            print("🚀 Ready to test DSO Interactive API")
        else:
            print("⚠️ DSO Search API working but no references found")
            print("💡 Try different search terms")

        print(f"\n📁 Results saved to:")
        print(f"   • House folder: {house_logger.house_folder}")
        print(f"   • Output folder: {house_logger.output_folder}")

        print(f"\n📁 Next steps:")
        if functional_refs:
            print(f"   • Test DSO Interactive: python tools/test_dso_interactive.py '{address}' {renovation_type}")
        print(f"   • Test different renovation: python tools/test_dso_search.py '{address}' uitbouw")
        print(f"   • View saved results: ls {house_logger.house_folder}")
        print(f"   • Test full integration: python run_tests.py")

    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description='Test DSO Search API with specific renovation type')
    parser.add_argument('address', help='Dutch address (e.g., "1082GB 43-2")')
    parser.add_argument('renovation_type', help='Renovation type (e.g., "dakkapel", "uitbouw")')

    args = parser.parse_args()
    test_dso_search(args.address, args.renovation_type)

if __name__ == "__main__":
    main()