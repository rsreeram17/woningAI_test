#!/usr/bin/env python3
"""Individual DSO Catalog API testing tool."""

import os
import sys
import argparse
from datetime import datetime

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.config import load_config
from src.api_clients.dso_catalog_api import DSOCatalogAPI
from src.utils.house_logger import HouseSpecificLogger

def test_dso_catalog(address: str, renovation_type: str):
    """Test DSO Catalog API with specific renovation type and related terms.

    Args:
        address: Dutch address (for context and logging)
        renovation_type: Type of renovation (e.g., "dakkapel", "uitbouw")
    """
    print("📚 DSO Catalog API Individual Test")
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
        house_logger = HouseSpecificLogger(address, f"DSO_Catalog_Test_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        print(f"📁 Created house-specific folder: {house_logger.house_folder}")

        # Initialize catalog client with house logger
        catalog_client = DSOCatalogAPI(dso_config, house_logger=house_logger)
        print("✅ DSO Catalog Client initialized with logging")

        # Define search terms related to renovation
        renovation_terms = [renovation_type]
        general_terms = ["omgevingsvergunning", "meldingsplicht", "bouwen"]
        legal_terms = ["activiteit", "toepasbare regels", "bevoegd gezag"]

        all_search_terms = renovation_terms + general_terms + legal_terms

        print(f"\n📋 Search terms to test:")
        for i, term in enumerate(all_search_terms, 1):
            print(f"   {i}. {term}")

        print(f"\n" + "=" * 50)
        print("🚀 RUNNING DSO CATALOG TESTS")
        print("=" * 50)

        # Initialize result variables
        concept_searches = {}
        concept_details = {}
        successful_searches = 0
        total_concepts_found = 0

        # Step 1: Search Concepts for Each Term
        print(f"\n1️⃣ CONCEPT SEARCH TESTS")
        print("-" * 50)

        for i, search_term in enumerate(all_search_terms, 1):
            print(f"\n🔍 {i}) Searching for: '{search_term}'")
            print("-" * 30)

            result = catalog_client.search_concepts(search_term, renovation_type=renovation_type)

            concept_searches[search_term] = result

            if result['success']:
                print("✅ SUCCESS")
                data = result['data']

                print(f"📊 Search Results:")
                print(f"   Concepts found: {data['total_concepts']}")
                print(f"   Response time: {data['response_metadata']['duration']:.2f}s")

                if data['concepts']:
                    successful_searches += 1
                    total_concepts_found += data['total_concepts']

                    print(f"\n📋 Top Concepts (first 3):")
                    for j, concept in enumerate(data['concepts'][:3], 1):
                        print(f"   {j}. {concept.get('label', 'Unknown')}")
                        print(f"      URI: {concept.get('uri', 'No URI')}")
                        print(f"      Definition: {concept.get('definitie', 'No definition')[:80]}...")

                        # Store concept URI for detailed lookup test
                        if j == 1 and concept.get('uri'):  # Use first concept for detailed test
                            concept_details[search_term] = concept.get('uri')
                else:
                    print("   No concepts found")
            else:
                print("❌ FAILED")
                print(f"   Error: {result.get('error')}")

        # Step 2: Detailed Concept Lookup Tests
        print(f"\n2️⃣ DETAILED CONCEPT LOOKUP TESTS")
        print("-" * 50)

        concept_detail_results = {}
        successful_detail_lookups = 0

        if concept_details:
            for search_term, concept_uri in list(concept_details.items())[:3]:  # Test first 3
                print(f"\n🔍 Getting details for: '{search_term}' concept")
                print(f"URI: {concept_uri}")
                print("-" * 30)

                detail_result = catalog_client.get_concept_by_uri(concept_uri, renovation_type=renovation_type)

                concept_detail_results[search_term] = detail_result

                if detail_result['success']:
                    print("✅ SUCCESS")
                    data = detail_result['data']

                    print(f"📊 Concept Details:")
                    print(f"   Response time: {data['response_metadata']['duration']:.2f}s")

                    if data['concept_info']:
                        successful_detail_lookups += 1
                        concept_info = data['concept_info']

                        print(f"\n📋 Detailed Information:")
                        print(f"   Label: {concept_info.get('label', 'Unknown')}")
                        print(f"   Definition: {concept_info.get('definitie', 'No definition')}")
                        print(f"   Source: {concept_info.get('bron', 'Unknown source')}")
                        print(f"   Type: {concept_info.get('type', 'Unknown type')}")

                        if concept_info.get('relaties'):
                            print(f"   Related concepts: {len(concept_info['relaties'])}")
                    else:
                        print("   No detailed concept information found")
                else:
                    print("❌ FAILED")
                    print(f"   Error: {detail_result.get('error')}")
        else:
            print("⚠️ No concept URIs available for detailed lookup tests")

        # Step 3: Advanced Search Tests
        print(f"\n3️⃣ ADVANCED SEARCH TESTS")
        print("-" * 50)

        # Test larger page size
        print(f"\n🔍 Large page size test")
        print("-" * 30)

        large_search_result = catalog_client.search_concepts(
            renovation_type, page_size=50, renovation_type=renovation_type
        )

        if large_search_result['success']:
            print("✅ SUCCESS")
            data = large_search_result['data']
            print(f"📊 Large Search Results:")
            print(f"   Concepts found: {data['total_concepts']}")
            print(f"   Page size used: {data.get('page_size', 'Unknown')}")
        else:
            print("❌ FAILED")
            print(f"   Error: {large_search_result.get('error')}")

        # Test partial search
        if renovation_type and len(renovation_type) > 3:
            partial_term = renovation_type[:4]
            print(f"\n🔍 Partial search test: '{partial_term}'")
            print("-" * 30)

            partial_search_result = catalog_client.search_concepts(
                partial_term, renovation_type=renovation_type
            )

            if partial_search_result['success']:
                print("✅ SUCCESS")
                data = partial_search_result['data']
                print(f"📊 Partial Search Results:")
                print(f"   Concepts found: {data['total_concepts']}")
                print(f"   Relevant matches: {len([c for c in data['concepts'] if renovation_type.lower() in c.get('label', '').lower()])}")
            else:
                print("❌ FAILED")
                print(f"   Error: {partial_search_result.get('error')}")

        # Save test summary to files
        test_summary = {
            "address": address,
            "renovation_type": renovation_type,
            "test_timestamp": datetime.now().isoformat(),
            "search_terms": all_search_terms,
            "results": {
                "concept_searches": {term: result.get('success', False) for term, result in concept_searches.items()},
                "concept_details": {term: result.get('success', False) for term, result in concept_detail_results.items()},
                "large_search": large_search_result.get('success', False),
                "partial_search": partial_search_result.get('success', False) if 'partial_search_result' in locals() else False
            },
            "statistics": {
                "total_search_terms": len(all_search_terms),
                "successful_searches": successful_searches,
                "total_concepts_found": total_concepts_found,
                "successful_detail_lookups": successful_detail_lookups,
                "search_success_rate": (successful_searches / len(all_search_terms)) * 100 if all_search_terms else 0
            },
            "concept_samples": {
                term: {
                    "total_found": result.get('data', {}).get('total_concepts', 0),
                    "sample_concepts": [
                        {
                            "label": c.get('label', 'Unknown'),
                            "uri": c.get('uri', 'No URI'),
                            "definition_preview": c.get('definitie', 'No definition')[:100] + "..." if c.get('definitie') and len(c.get('definitie', '')) > 100 else c.get('definitie', 'No definition')
                        } for c in result.get('data', {}).get('concepts', [])[:2]
                    ]
                } for term, result in concept_searches.items() if result.get('success')
            }
        }

        # Save to house-specific folder
        house_logger.save_renovation_test_results("dso_catalog_test", test_summary)

        print(f"\n" + "=" * 50)
        print("🎉 DSO CATALOG API TEST COMPLETE")
        print("=" * 50)

        # Calculate overall success rate
        total_tests = len(concept_searches) + len(concept_detail_results) + 1  # +1 for large search
        if 'partial_search_result' in locals():
            total_tests += 1

        successful_tests = successful_searches + successful_detail_lookups
        if large_search_result.get('success'):
            successful_tests += 1
        if 'partial_search_result' in locals() and partial_search_result.get('success'):
            successful_tests += 1

        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0

        print(f"📊 Overall Success Rate: {success_rate:.1f}% ({successful_tests}/{total_tests})")

        if success_rate >= 75:
            print("✅ DSO Catalog API working excellently!")
            print("🚀 Ready to provide comprehensive term definitions")
        elif success_rate >= 50:
            print("⚠️ DSO Catalog API partially working")
            print("💡 Some concept lookups may be limited")
        else:
            print("❌ DSO Catalog API having significant issues")
            print("💡 Check concept search and definition lookup")

        # Business summary
        print(f"\n🎯 Business Summary:")
        print(f"   📚 Total concepts found: {total_concepts_found}")
        print(f"   🎯 Renovation-specific concepts: {concept_searches.get(renovation_type, {}).get('data', {}).get('total_concepts', 0)}")
        print(f"   📖 Legal terms explained: {len([term for term in legal_terms if concept_searches.get(term, {}).get('success')])}")
        print(f"   💡 User guidance: Comprehensive term definitions available")

        print(f"\n📁 Results saved to:")
        print(f"   • House folder: {house_logger.house_folder}")
        print(f"   • Output folder: {house_logger.output_folder}")

        print(f"\n📁 Next steps:")
        print(f"   • Test complete integration: python run_tests.py")
        print(f"   • View saved results: ls {house_logger.house_folder}")
        print(f"   • Review concept definitions for user interface design")

    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description='Test DSO Catalog API with specific renovation type')
    parser.add_argument('address', help='Dutch address (e.g., "1082GB 43-2")')
    parser.add_argument('renovation_type', help='Renovation type (e.g., "dakkapel", "uitbouw")')

    args = parser.parse_args()
    test_dso_catalog(args.address, args.renovation_type)

if __name__ == "__main__":
    main()