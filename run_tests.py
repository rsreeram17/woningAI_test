#!/usr/bin/env python3
"""Main test runner for the Integrated Renovation API Testing Framework."""

import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import load_config
from src.api_clients.bag_client import BAGAPIClient
from src.api_clients.dso_search_api import DSOSearchAPI
from src.api_clients.dso_interactive_api import DSOInteractiveAPI
from src.api_clients.dso_routing_api import DSORoutingAPI
from src.api_clients.dso_catalog_api import DSOCatalogAPI
from src.api_clients.integration_client import IntegratedRenovationAnalysis
from src.utils.console_display import RealTimeDisplay

def initialize_api_clients(config):
    """Initialize all API clients with configuration."""
    console = RealTimeDisplay()

    console.print_section("Initializing API Clients")

    try:
        # BAG API Client
        print("🏠 Initializing BAG API client...")
        bag_config = config.get_bag_config()

        if not bag_config.get('api_key'):
            console.error("BAG API key not found. Please set BAG_API_KEY in your .env file.")
            return None

        bag_client = BAGAPIClient(bag_config)
        console.success("BAG API client initialized")

        # DSO API Clients
        print("🏛️ Initializing DSO API clients...")
        dso_config = config.get_dso_config()

        if not dso_config.get('api_key'):
            console.error("DSO API key not found. Please set DSO_API_KEY in your .env file.")
            return None

        dso_clients = {
            'search': DSOSearchAPI(dso_config),
            'interactive': DSOInteractiveAPI(dso_config),
            'routing': DSORoutingAPI(dso_config),
            'catalog': DSOCatalogAPI(dso_config)
        }

        console.success("All DSO API clients initialized")

        return {
            'bag': bag_client,
            'dso': dso_clients
        }

    except Exception as e:
        console.error(f"Failed to initialize API clients: {str(e)}")
        return None

def run_single_test(analyzer, address, renovation_type, console):
    """Run a single test scenario."""
    try:
        result = analyzer.analyze_renovation_feasibility(address, renovation_type)
        return result
    except Exception as e:
        console.error(f"Test failed with exception: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'address': address,
            'renovation_type': renovation_type
        }

def generate_session_summary(all_results, start_time):
    """Generate summary of the entire test session."""
    end_time = time.time()
    total_duration = end_time - start_time

    summary = {
        'session_info': {
            'start_time': datetime.fromtimestamp(start_time).isoformat(),
            'end_time': datetime.fromtimestamp(end_time).isoformat(),
            'total_duration_seconds': total_duration,
            'total_duration_formatted': f"{total_duration:.1f}s"
        },
        'test_statistics': {
            'total_houses': len(all_results),
            'total_tests': sum(len(house_results) for house_results in all_results.values()),
            'successful_tests': 0,
            'failed_tests': 0,
            'average_test_duration': 0
        },
        'house_results': {},
        'renovation_type_analysis': {},
        'recommendations': []
    }

    # Calculate statistics
    total_test_duration = 0
    renovation_stats = {}

    for house_address, house_results in all_results.items():
        house_successful = 0
        house_total = len(house_results)

        for renovation_type, result in house_results.items():
            # Update renovation type stats
            if renovation_type not in renovation_stats:
                renovation_stats[renovation_type] = {'total': 0, 'successful': 0, 'scores': []}

            renovation_stats[renovation_type]['total'] += 1

            if result.get('integration_success'):
                summary['test_statistics']['successful_tests'] += 1
                house_successful += 1
                renovation_stats[renovation_type]['successful'] += 1

                # Get business viability score
                business_score = result.get('analysis', {}).get('business_viability', {}).get('overall_score', 0)
                renovation_stats[renovation_type]['scores'].append(business_score)
            else:
                summary['test_statistics']['failed_tests'] += 1

            # Add to total duration
            steps = result.get('steps', {})
            test_duration = sum(step.get('duration', 0) for step in steps.values())
            total_test_duration += test_duration

        # House summary
        house_success_rate = (house_successful / house_total * 100) if house_total > 0 else 0
        summary['house_results'][house_address] = {
            'success_rate': house_success_rate,
            'successful_tests': house_successful,
            'total_tests': house_total,
            'status': 'excellent' if house_success_rate >= 80 else 'good' if house_success_rate >= 60 else 'moderate' if house_success_rate >= 40 else 'poor'
        }

    # Calculate average test duration
    total_tests = summary['test_statistics']['total_tests']
    if total_tests > 0:
        summary['test_statistics']['average_test_duration'] = total_test_duration / total_tests

    # Analyze renovation types
    for renovation_type, stats in renovation_stats.items():
        success_rate = (stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0
        avg_score = sum(stats['scores']) / len(stats['scores']) if stats['scores'] else 0

        summary['renovation_type_analysis'][renovation_type] = {
            'success_rate': success_rate,
            'average_score': avg_score,
            'total_tests': stats['total'],
            'successful_tests': stats['successful'],
            'recommendation': (
                'high_priority' if success_rate >= 80 and avg_score >= 70 else
                'medium_priority' if success_rate >= 60 and avg_score >= 50 else
                'low_priority' if success_rate >= 40 else
                'not_recommended'
            )
        }

    # Generate recommendations
    high_priority = [k for k, v in summary['renovation_type_analysis'].items() if v['recommendation'] == 'high_priority']
    medium_priority = [k for k, v in summary['renovation_type_analysis'].items() if v['recommendation'] == 'medium_priority']

    overall_success = (summary['test_statistics']['successful_tests'] / total_tests * 100) if total_tests > 0 else 0

    if overall_success >= 70:
        summary['recommendations'].append("✅ Excellent overall results - APIs are ready for MVP development")
    elif overall_success >= 50:
        summary['recommendations'].append("✅ Good results - APIs can support MVP with some limitations")
    elif overall_success >= 30:
        summary['recommendations'].append("⚠️ Moderate results - MVP possible but requires careful feature selection")
    else:
        summary['recommendations'].append("❌ Poor results - APIs may not be suitable for current MVP approach")

    if high_priority:
        summary['recommendations'].append(f"🎯 Prioritize these renovation types in MVP: {', '.join(high_priority)}")

    if medium_priority:
        summary['recommendations'].append(f"🔄 Consider these for phase 2: {', '.join(medium_priority)}")

    return summary

def save_results(all_results, summary):
    """Save results to various output formats."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Ensure output directories exist
    Path("outputs/combined").mkdir(parents=True, exist_ok=True)

    # Save detailed results
    results_file = f"outputs/combined/test_results_{timestamp}.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    # Save summary
    summary_file = f"outputs/combined/test_summary_{timestamp}.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # Save AI-readable summary
    ai_summary_file = f"logs/ai_readable/session_summary_{timestamp}.md"
    Path("logs/ai_readable").mkdir(parents=True, exist_ok=True)

    with open(ai_summary_file, 'w', encoding='utf-8') as f:
        f.write(f"""# API Testing Session Summary - {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Executive Summary
- **Total Tests:** {summary['test_statistics']['total_tests']}
- **Success Rate:** {(summary['test_statistics']['successful_tests'] / summary['test_statistics']['total_tests'] * 100):.1f}%
- **Total Duration:** {summary['session_info']['total_duration_formatted']}
- **Houses Tested:** {summary['test_statistics']['total_houses']}

## Key Recommendations
""")
        for rec in summary['recommendations']:
            f.write(f"- {rec}\n")

        f.write(f"""

## Renovation Type Analysis
| Renovation Type | Success Rate | Avg Score | Recommendation |
|----------------|--------------|-----------|----------------|
""")

        for renovation_type, analysis in summary['renovation_type_analysis'].items():
            f.write(f"| {renovation_type} | {analysis['success_rate']:.1f}% | {analysis['average_score']:.0f}/100 | {analysis['recommendation']} |\n")

        f.write(f"""

## House Performance
| House Address | Success Rate | Status |
|---------------|--------------|--------|
""")

        for house, result in summary['house_results'].items():
            f.write(f"| {house} | {result['success_rate']:.1f}% | {result['status']} |\n")

        f.write(f"""

## Files Generated
- Detailed results: `{results_file}`
- Summary data: `{summary_file}`
- House-specific logs: `logs/by_house/`
- This AI summary: `{ai_summary_file}`

*Use this file to ask Claude specific questions about the test results.*
""")

    return {
        'results_file': results_file,
        'summary_file': summary_file,
        'ai_summary_file': ai_summary_file
    }

def main():
    """Main test runner function."""
    console = RealTimeDisplay()

    console.print_header("Integrated Renovation API Testing Framework")

    # Load configuration
    try:
        config = load_config()
        console.success("Configuration loaded successfully")
    except Exception as e:
        console.error(f"Failed to load configuration: {str(e)}")
        console.info("Make sure config.yaml exists and .env file contains API keys")
        return 1

    # Initialize API clients
    clients = initialize_api_clients(config)
    if not clients:
        console.error("Failed to initialize API clients")
        return 1

    # Create integration analyzer
    analyzer = IntegratedRenovationAnalysis(clients['bag'], clients['dso'])

    # Get test scenarios
    addresses = config.get_test_addresses()
    renovation_scenarios = config.get_renovation_scenarios()

    if not addresses:
        console.error("No test addresses found in configuration")
        return 1

    if not renovation_scenarios:
        console.error("No renovation scenarios found in configuration")
        return 1

    # Display test plan
    console.print_section("Test Plan")
    print(f"📍 Addresses to test: {len(addresses)}")
    for addr in addresses:
        priority_icon = "🔴" if addr.get('priority') == 'high' else "🟡" if addr.get('priority') == 'medium' else "🟢"
        print(f"   {priority_icon} {addr['postcode']} {addr['huisnummer']}{addr.get('huisletter', '')} - {addr['house_name']}")

    print(f"\n🔧 Renovation types: {len(renovation_scenarios)}")
    for scenario in renovation_scenarios:
        complexity_icon = "🔴" if scenario.get('complexity') == 'complex' else "🟡" if scenario.get('complexity') == 'medium' else "🟢"
        print(f"   {complexity_icon} {scenario['type']} - {scenario['description']}")

    total_tests = len(addresses) * len(renovation_scenarios)
    estimated_duration = total_tests * 1.5  # 1.5 minutes per test estimate

    print(f"\n📊 Total test scenarios: {total_tests}")
    print(f"⏱️ Estimated duration: {estimated_duration:.1f} minutes")
    print(f"📁 Results will be saved to: outputs/ and logs/")

    # Confirm before starting
    if input("\n🚀 Start testing? (y/N): ").lower() != 'y':
        console.info("Testing cancelled by user")
        return 0

    # Run tests
    start_time = time.time()
    all_results = {}

    for i, address_config in enumerate(addresses, 1):
        # Create display address for console output
        display_address = f"{address_config['postcode']} {address_config['huisnummer']}{address_config.get('huisletter', '')}{address_config.get('huisnummertoevoeging', '')}"
        house_name = address_config.get('house_name', display_address)

        console.print_section(f"Testing House {i}/{len(addresses)}: {house_name}")

        house_results = {}

        for j, scenario in enumerate(renovation_scenarios, 1):
            renovation_type = scenario['type']
            search_terms = scenario.get('search_terms', [])

            print(f"\n🏗️ Test {j}/{len(renovation_scenarios)}: {renovation_type}")

            # Pass the full address config instead of constructed string
            result = run_single_test(analyzer, address_config, renovation_type, console)
            house_results[renovation_type] = result

            # Brief pause between tests
            testing_config = config.get_testing_config()
            delay = testing_config.get('delay_between_tests', 1.0)
            if delay > 0:
                console.wait_with_countdown(delay, "Pausing")

        all_results[display_address] = house_results
        console.show_house_completion(display_address, house_results)

    # Generate summary and save results
    console.print_section("Generating Reports")

    summary = generate_session_summary(all_results, start_time)
    file_paths = save_results(all_results, summary)

    # Final summary
    console.show_session_summary(all_results)

    console.print_section("Test Session Complete")

    total_tests = summary['test_statistics']['total_tests']
    successful_tests = summary['test_statistics']['successful_tests']
    success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0

    console.success(f"Completed {total_tests} tests with {success_rate:.1f}% success rate")

    console.show_file_locations()

    print(f"\n📋 Key files generated:")
    print(f"   • AI-readable summary: {file_paths['ai_summary_file']}")
    print(f"   • Detailed results: {file_paths['results_file']}")
    print(f"   • House-specific logs: logs/by_house/")

    print(f"\n🤖 Next steps:")
    print(f"   • Share {file_paths['ai_summary_file']} with Claude for analysis")
    print(f"   • Use python tools/house_viewer.py to explore individual houses")
    print(f"   • Check logs/by_house/ for detailed house information")

    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)