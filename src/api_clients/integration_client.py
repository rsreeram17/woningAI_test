"""Integration client that combines BAG property data with DSO regulatory data."""

import time
from datetime import datetime
from typing import Dict, Any, List, Optional

from .bag_client import BAGAPIClient
from .dso_search_api import DSOSearchAPI
from .dso_interactive_api import DSOInteractiveAPI
from .dso_routing_api import DSORoutingAPI
from .dso_catalog_api import DSOCatalogAPI
from ..utils.house_logger import HouseSpecificLogger
from ..utils.console_display import RealTimeDisplay

class IntegratedRenovationAnalysis:
    """Combines BAG property data with DSO regulatory data for renovation analysis."""

    def __init__(self, bag_client: BAGAPIClient, dso_clients: Dict[str, Any]):
        """Initialize integrated analysis client.

        Args:
            bag_client: BAG API client instance
            dso_clients: Dictionary of DSO API clients
        """
        self.bag_client = bag_client
        self.dso_search = dso_clients['search']
        self.dso_interactive = dso_clients['interactive']
        self.dso_routing = dso_clients['routing']
        self.dso_catalog = dso_clients['catalog']

        self.console = RealTimeDisplay()

    def analyze_renovation_feasibility(self, address, renovation_type: str,
                                     search_terms: List[str] = None) -> Dict[str, Any]:
        """End-to-end analysis combining both BAG and DSO APIs.

        Args:
            address: Dutch address string OR dict with address components
            renovation_type: Type of renovation (e.g., "dakkapel")
            search_terms: Optional custom search terms

        Returns:
            Dict with complete analysis results
        """
        # Format address for display and logging
        if isinstance(address, dict):
            display_address = f"{address['postcode']} {address['huisnummer']}{address.get('huisletter', '')}{address.get('huisnummertoevoeging', '')}"
        else:
            display_address = address

        # Initialize house-specific logger
        house_logger = HouseSpecificLogger(display_address)

        # Update API clients to use house logger
        self.bag_client.house_logger = house_logger
        self.dso_search.house_logger = house_logger
        self.dso_interactive.house_logger = house_logger
        self.dso_routing.house_logger = house_logger
        self.dso_catalog.house_logger = house_logger

        # Start test tracking
        total_steps = 7  # BAG, DSO Search, Interactive, Routing, Catalog, Integration, Summary
        self.console.start_test(
            test_name=f"{display_address} → {renovation_type}",
            house_address=display_address,
            renovation_type=renovation_type,
            total_steps=total_steps
        )

        results = {
            'address': display_address,
            'renovation_type': renovation_type,
            'timestamp': datetime.now().isoformat(),
            'steps': {},
            'integration_success': False,
            'analysis': {},
            'session_id': house_logger.session_id
        }

        # Step 1: BAG - Resolve address and get building details
        self.console.log_step("BAG Address Resolution", "running", 0, "Validating address...")

        bag_result = self._resolve_address_with_details(address, renovation_type)
        results['steps']['bag_resolution'] = bag_result

        if bag_result.get('success'):
            self.console.log_step("BAG Address Resolution", "success", bag_result.get('duration', 0),
                                f"Found: {bag_result['data']['address_info']['formatted_address']}")
        else:
            self.console.log_step("BAG Address Resolution", "failed", bag_result.get('duration', 0),
                                f"Error: {bag_result.get('error', 'Unknown error')}")
            results['error'] = 'Address resolution failed'
            results['integration_success'] = False
            house_logger.save_renovation_test_results(renovation_type, results)
            return results

        # Extract coordinates and building context
        coordinates = bag_result['data']['coordinates']
        building_context = bag_result['data']['building_info']

        # Step 2: DSO - Search applicable rules
        self.console.log_step("DSO Rule Search", "running", 0, f"Searching for '{renovation_type}' rules...")

        dso_search_result = self._search_renovation_rules(renovation_type, search_terms)
        results['steps']['dso_search'] = dso_search_result

        if dso_search_result.get('success'):
            activities_found = len(dso_search_result['data'].get('combined_activities', []))
            self.console.log_step("DSO Rule Search", "success", dso_search_result.get('duration', 0),
                                f"Found {activities_found} applicable rules")
        else:
            self.console.log_step("DSO Rule Search", "failed", dso_search_result.get('duration', 0),
                                f"Error: {dso_search_result.get('error', 'Unknown error')}")

        # Step 3: DSO - Interactive permit and filing checks (if search succeeded)
        interactive_result = {'success': False, 'error': 'Skipped due to search failure'}

        if dso_search_result.get('success'):
            functional_refs = self._extract_functional_structure_refs(dso_search_result)

            if functional_refs:
                self.console.log_step("DSO Interactive Services", "running", 0, "Checking permits and filing...")

                interactive_result = self.dso_interactive.run_complete_interactive_flow(
                    functional_refs, coordinates, renovation_type=renovation_type
                )

                if interactive_result.get('success'):
                    flow_data = interactive_result['data']['flow_summary']
                    success_rate = flow_data.get('success_rate', 0) * 100
                    self.console.log_step("DSO Interactive Services", "success", flow_data.get('total_duration', 0),
                                        f"{success_rate:.0f}% success rate")
                else:
                    self.console.log_step("DSO Interactive Services", "failed", 0,
                                        "Interactive services failed")
            else:
                self.console.log_step("DSO Interactive Services", "warning", 0,
                                    "No functional references found")
                interactive_result = {'success': False, 'error': 'No functional structure references'}

        results['steps']['dso_interactive'] = interactive_result

        # Step 4: DSO - Find responsible authority
        authority_result = {'success': False, 'error': 'Skipped due to search failure'}

        if dso_search_result.get('success') and functional_refs:
            self.console.log_step("DSO Authority Routing", "running", 0, "Finding responsible authority...")

            authority_result = self.dso_routing.run_complete_routing_flow(
                functional_refs, coordinates, renovation_type=renovation_type
            )

            if authority_result.get('success'):
                authority_data = authority_result['data']['responsible_authority']['data']['authority_analysis']
                authorities_found = authority_data.get('authorities_found', 0)
                self.console.log_step("DSO Authority Routing", "success",
                                    authority_result['data']['flow_summary'].get('total_duration', 0),
                                    f"Found {authorities_found} authorities")
            else:
                self.console.log_step("DSO Authority Routing", "failed", 0, "Authority lookup failed")

        results['steps']['dso_routing'] = authority_result

        # Step 5: DSO - Get concept definitions
        self.console.log_step("DSO Concept Lookup", "running", 0, f"Getting definitions for '{renovation_type}'...")

        concept_result = self.dso_catalog.get_renovation_related_concepts(renovation_type)
        results['steps']['dso_concepts'] = concept_result

        if concept_result.get('success'):
            concepts_found = len(concept_result['data'].get('combined_concepts', []))
            self.console.log_step("DSO Concept Lookup", "success", 0, f"Found {concepts_found} definitions")
        else:
            self.console.log_step("DSO Concept Lookup", "failed", 0, "Concept lookup failed")

        # Step 6: Integration analysis
        self.console.log_step("Integration Analysis", "running", 0, "Analyzing combined results...")

        integration_success = self._assess_integration_success(results)
        results['integration_success'] = integration_success

        analysis = self._generate_combined_analysis(results, building_context, renovation_type)
        results['analysis'] = analysis

        if integration_success:
            self.console.log_step("Integration Analysis", "success", 0,
                                f"Integration successful - {analysis.get('business_viability', {}).get('overall_score', 0)}/100 viability")
        else:
            self.console.log_step("Integration Analysis", "warning", 0, "Partial integration only")

        # Step 7: Save results and generate summary
        self.console.log_step("Save Results", "running", 0, "Generating reports...")

        # Save detailed results
        house_logger.save_renovation_test_results(renovation_type, results)

        self.console.log_step("Save Results", "success", 0, "Reports saved to house folder")

        # Show test summary
        self.console.show_test_summary(results)

        return results

    def _resolve_address_with_details(self, address, renovation_type: str) -> Dict[str, Any]:
        """Comprehensive address resolution with building details."""
        # Format address for display
        if isinstance(address, dict):
            display_address = f"{address['postcode']} {address['huisnummer']}{address.get('huisletter', '')}{address.get('huisnummertoevoeging', '')}"
        else:
            display_address = address

        print(f"  🏠 Resolving address: {display_address}")

        start_time = time.time()

        # Use BAG client's comprehensive validation
        result = self.bag_client.validate_address_for_testing(address)

        # Add duration to result
        duration = time.time() - start_time
        if result.get('success'):
            result['duration'] = duration
        else:
            result['duration'] = duration

        return result

    def _search_renovation_rules(self, renovation_type: str,
                                search_terms: List[str] = None) -> Dict[str, Any]:
        """Search for renovation rules using multiple terms."""
        print(f"  🔍 Searching DSO rules for: {renovation_type}")

        start_time = time.time()

        # Use provided search terms or get from config
        if not search_terms:
            # Default search terms based on renovation type
            default_terms = {
                'dakkapel': ['dakkapel', 'dakraam', 'dormer'],
                'uitbouw': ['uitbouw', 'aanbouw', 'extension'],
                'badkamer_verbouwen': ['badkamer verbouwen', 'sanitair'],
                'extra_verdieping': ['extra verdieping', 'optopping'],
                'garage_bouwen': ['garage bouwen', 'bijgebouw'],
                'keuken_verbouwen': ['keuken verbouwen', 'keuken renovatie']
            }
            search_terms = default_terms.get(renovation_type, [renovation_type])

        # Search with multiple terms
        result = self.dso_search.search_with_multiple_terms(search_terms, renovation_type=renovation_type)

        # Add duration
        duration = time.time() - start_time
        if result.get('success'):
            result['duration'] = duration
        else:
            result['duration'] = duration

        return result

    def _extract_functional_structure_refs(self, search_result: Dict[str, Any]) -> List[str]:
        """Extract functional structure references from search results."""
        if not search_result.get('success'):
            return []

        data = search_result.get('data', {})
        activities = data.get('combined_activities', [])

        refs = []
        for activity in activities:
            ref = activity.get('functioneleStructuurRef')
            if ref and ref not in refs:
                refs.append(ref)

        return refs

    def _assess_integration_success(self, results: Dict[str, Any]) -> bool:
        """Assess overall integration success."""
        steps = results.get('steps', {})

        # Critical steps that must succeed
        critical_success = (
            steps.get('bag_resolution', {}).get('success', False) and
            steps.get('dso_search', {}).get('success', False)
        )

        if not critical_success:
            return False

        # Count successful steps
        successful_steps = sum(1 for step in steps.values() if step.get('success', False))
        total_steps = len(steps)

        # Consider integration successful if > 60% of steps succeed
        success_rate = successful_steps / total_steps if total_steps > 0 else 0
        return success_rate > 0.6

    def _generate_combined_analysis(self, results: Dict[str, Any], building_context: Dict[str, Any],
                                   renovation_type: str) -> Dict[str, Any]:
        """Generate actionable insights from combined data."""
        steps = results.get('steps', {})

        analysis = {
            'data_completeness': {},
            'regulatory_coverage': {},
            'business_viability': {},
            'technical_feasibility': {},
            'recommendations': [],
            'issues': []
        }

        # Data Completeness Analysis
        analysis['data_completeness'] = self._analyze_data_completeness(steps, building_context)

        # Regulatory Coverage Analysis
        analysis['regulatory_coverage'] = self._analyze_regulatory_coverage(steps, renovation_type)

        # Business Viability Analysis
        analysis['business_viability'] = self._analyze_business_viability(steps, renovation_type)

        # Technical Feasibility Analysis
        analysis['technical_feasibility'] = self._analyze_technical_feasibility(steps)

        # Generate Recommendations
        analysis['recommendations'] = self._generate_recommendations(analysis, renovation_type)

        # Identify Issues
        analysis['issues'] = self._identify_issues(steps, analysis)

        return analysis

    def _analyze_data_completeness(self, steps: Dict[str, Any], building_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze completeness of available data."""
        completeness = {
            'bag_data_score': 0,
            'dso_data_score': 0,
            'overall_score': 0,
            'missing_data': []
        }

        # BAG Data Analysis
        bag_result = steps.get('bag_resolution', {})
        if bag_result.get('success'):
            bag_data = bag_result.get('data', {})
            score = 20  # Base score for successful resolution

            if bag_data.get('coordinates'):
                score += 20
            if building_context.get('bouwjaar'):
                score += 15
            if building_context.get('oppervlakte'):
                score += 15
            if building_context.get('gebruiksdoel'):
                score += 15
            if building_context.get('pand_status'):
                score += 15

            completeness['bag_data_score'] = min(score, 100)
        else:
            completeness['missing_data'].append('BAG address data')

        # DSO Data Analysis
        dso_search = steps.get('dso_search', {})
        if dso_search.get('success'):
            score = 30  # Base score for finding rules

            activities = dso_search.get('data', {}).get('combined_activities', [])
            if len(activities) >= 3:
                score += 20
            elif len(activities) >= 1:
                score += 10

            # Interactive data
            interactive = steps.get('dso_interactive', {})
            if interactive.get('success'):
                score += 25
            else:
                completeness['missing_data'].append('DSO interactive services data')

            # Authority data
            authority = steps.get('dso_routing', {})
            if authority.get('success'):
                score += 15
            else:
                completeness['missing_data'].append('Authority information')

            # Concept data
            concepts = steps.get('dso_concepts', {})
            if concepts.get('success'):
                score += 10

            completeness['dso_data_score'] = min(score, 100)
        else:
            completeness['missing_data'].append('DSO regulatory data')

        # Overall score
        completeness['overall_score'] = int((completeness['bag_data_score'] + completeness['dso_data_score']) / 2)

        return completeness

    def _analyze_regulatory_coverage(self, steps: Dict[str, Any], renovation_type: str) -> Dict[str, Any]:
        """Analyze regulatory coverage for the renovation type."""
        coverage = {
            'rules_found': False,
            'permit_clarity': False,
            'authority_identified': False,
            'compliance_guidance': False,
            'coverage_score': 0
        }

        # Rules found
        dso_search = steps.get('dso_search', {})
        if dso_search.get('success'):
            activities = dso_search.get('data', {}).get('combined_activities', [])
            if activities:
                coverage['rules_found'] = True
                coverage['coverage_score'] += 30

        # Permit clarity
        interactive = steps.get('dso_interactive', {})
        if interactive.get('success'):
            permit_data = interactive.get('data', {})
            if permit_data.get('permit_check', {}).get('success'):
                coverage['permit_clarity'] = True
                coverage['coverage_score'] += 25

        # Authority identified
        authority = steps.get('dso_routing', {})
        if authority.get('success'):
            auth_data = authority.get('data', {}).get('responsible_authority', {}).get('data', {})
            if auth_data.get('authority_analysis', {}).get('authorities_found', 0) > 0:
                coverage['authority_identified'] = True
                coverage['coverage_score'] += 25

        # Compliance guidance
        if interactive.get('success'):
            filing_data = interactive.get('data', {}).get('filing_requirements', {})
            compliance_data = interactive.get('data', {}).get('compliance_measures', {})
            if filing_data.get('success') or compliance_data.get('success'):
                coverage['compliance_guidance'] = True
                coverage['coverage_score'] += 20

        return coverage

    def _analyze_business_viability(self, steps: Dict[str, Any], renovation_type: str) -> Dict[str, Any]:
        """Calculate business viability for MVP development."""
        viability = {
            'overall_score': 0,
            'user_questions_answerable': 0,
            'automation_potential': 0,
            'market_readiness': 0
        }

        # Calculate scores based on data availability and quality
        data_completeness = self._analyze_data_completeness(steps, {})
        regulatory_coverage = self._analyze_regulatory_coverage(steps, renovation_type)

        # User questions answerable (40% weight)
        question_score = 0
        if steps.get('bag_resolution', {}).get('success'):
            question_score += 15  # Can answer "Is this address valid?"

        if regulatory_coverage['rules_found']:
            question_score += 15  # Can answer "What rules apply?"

        if regulatory_coverage['permit_clarity']:
            question_score += 15  # Can answer "Do I need a permit?"

        if regulatory_coverage['authority_identified']:
            question_score += 10  # Can answer "Who is responsible?"

        if regulatory_coverage['compliance_guidance']:
            question_score += 5   # Can answer "What documents needed?"

        viability['user_questions_answerable'] = min(question_score, 40)

        # Automation potential (30% weight)
        auto_score = 0
        if data_completeness['overall_score'] >= 80:
            auto_score += 15
        elif data_completeness['overall_score'] >= 60:
            auto_score += 10
        elif data_completeness['overall_score'] >= 40:
            auto_score += 5

        if regulatory_coverage['coverage_score'] >= 80:
            auto_score += 15
        elif regulatory_coverage['coverage_score'] >= 60:
            auto_score += 10
        elif regulatory_coverage['coverage_score'] >= 40:
            auto_score += 5

        viability['automation_potential'] = min(auto_score, 30)

        # Market readiness (30% weight)
        market_score = 0

        # API reliability
        successful_apis = sum(1 for step in steps.values() if step.get('success', False))
        total_apis = len(steps)
        api_reliability = successful_apis / total_apis if total_apis > 0 else 0

        if api_reliability >= 0.8:
            market_score += 15
        elif api_reliability >= 0.6:
            market_score += 10
        elif api_reliability >= 0.4:
            market_score += 5

        # Response times
        total_duration = sum(step.get('duration', 0) for step in steps.values())
        if total_duration <= 10:
            market_score += 15
        elif total_duration <= 20:
            market_score += 10
        elif total_duration <= 30:
            market_score += 5

        viability['market_readiness'] = min(market_score, 30)

        # Overall score
        viability['overall_score'] = (
            viability['user_questions_answerable'] +
            viability['automation_potential'] +
            viability['market_readiness']
        )

        return viability

    def _analyze_technical_feasibility(self, steps: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze technical feasibility of implementation."""
        feasibility = {
            'api_reliability': 0,
            'performance_score': 0,
            'error_handling_needed': [],
            'implementation_complexity': 'medium'
        }

        # API Reliability
        successful_steps = sum(1 for step in steps.values() if step.get('success', False))
        total_steps = len(steps)
        reliability = successful_steps / total_steps if total_steps > 0 else 0
        feasibility['api_reliability'] = int(reliability * 100)

        # Performance Score
        total_duration = sum(step.get('duration', 0) for step in steps.values())
        if total_duration <= 5:
            feasibility['performance_score'] = 100
        elif total_duration <= 10:
            feasibility['performance_score'] = 80
        elif total_duration <= 20:
            feasibility['performance_score'] = 60
        elif total_duration <= 30:
            feasibility['performance_score'] = 40
        else:
            feasibility['performance_score'] = 20

        # Error handling needed
        for step_name, step_result in steps.items():
            if not step_result.get('success'):
                feasibility['error_handling_needed'].append(step_name)

        # Implementation complexity
        failed_steps = len(feasibility['error_handling_needed'])
        if failed_steps == 0:
            feasibility['implementation_complexity'] = 'low'
        elif failed_steps <= 2:
            feasibility['implementation_complexity'] = 'medium'
        else:
            feasibility['implementation_complexity'] = 'high'

        return feasibility

    def _generate_recommendations(self, analysis: Dict[str, Any], renovation_type: str) -> List[str]:
        """Generate actionable recommendations for MVP development."""
        recommendations = []

        business_score = analysis['business_viability']['overall_score']
        data_score = analysis['data_completeness']['overall_score']
        regulatory_score = analysis['regulatory_coverage']['coverage_score']

        # Overall viability recommendations
        if business_score >= 80:
            recommendations.append(f"✅ Excellent viability for {renovation_type} - prioritize in MVP")
        elif business_score >= 60:
            recommendations.append(f"✅ Good viability for {renovation_type} - include in MVP")
        elif business_score >= 40:
            recommendations.append(f"⚠️ Moderate viability for {renovation_type} - consider for later phases")
        else:
            recommendations.append(f"❌ Poor viability for {renovation_type} - not recommended for MVP")

        # Data completeness recommendations
        if data_score < 60:
            recommendations.append("🔧 Improve data completeness with additional API calls or data sources")

        # Regulatory coverage recommendations
        if regulatory_score < 50:
            recommendations.append("📋 Limited regulatory coverage - consider manual fallbacks")

        # Technical recommendations
        tech_feasibility = analysis['technical_feasibility']
        if tech_feasibility['api_reliability'] < 70:
            recommendations.append("⚡ Implement robust error handling and retry logic")

        if tech_feasibility['performance_score'] < 60:
            recommendations.append("🚀 Optimize API calls for better performance")

        return recommendations

    def _identify_issues(self, steps: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
        """Identify issues that need attention."""
        issues = []

        # API failures
        for step_name, step_result in steps.items():
            if not step_result.get('success'):
                error = step_result.get('error', 'Unknown error')
                issues.append(f"{step_name}: {error}")

        # Data quality issues
        if analysis['data_completeness']['overall_score'] < 50:
            issues.append("Poor data completeness may limit user experience")

        # Performance issues
        if analysis['technical_feasibility']['performance_score'] < 60:
            issues.append("Slow response times may impact user satisfaction")

        return issues

    def run_bulk_analysis(self, addresses: List[str], renovation_types: List[str]) -> Dict[str, Any]:
        """Run analysis for multiple addresses and renovation types.

        Args:
            addresses: List of addresses to test
            renovation_types: List of renovation types to test

        Returns:
            Dict with bulk analysis results
        """
        bulk_results = {}
        summary_stats = {
            'total_tests': 0,
            'successful_tests': 0,
            'failed_tests': 0,
            'average_duration': 0,
            'best_renovation_types': [],
            'worst_renovation_types': []
        }

        total_duration = 0

        print(f"\n🏗️ Running bulk analysis: {len(addresses)} addresses × {len(renovation_types)} renovations")

        for address in addresses:
            house_results = {}

            for renovation_type in renovation_types:
                print(f"\n🏠 Testing {address} → {renovation_type}")

                start_time = time.time()
                result = self.analyze_renovation_feasibility(address, renovation_type)
                test_duration = time.time() - start_time

                house_results[renovation_type] = result
                summary_stats['total_tests'] += 1
                total_duration += test_duration

                if result.get('integration_success'):
                    summary_stats['successful_tests'] += 1
                else:
                    summary_stats['failed_tests'] += 1

                # Brief pause between tests
                time.sleep(0.5)

            bulk_results[address] = house_results

            # Generate house summary
            house_logger = HouseSpecificLogger(address)
            house_logger.generate_house_summary(house_results)

            self.console.show_house_completion(address, house_results)

        # Calculate summary statistics
        if summary_stats['total_tests'] > 0:
            summary_stats['average_duration'] = total_duration / summary_stats['total_tests']

        # Identify best and worst renovation types
        renovation_scores = {}
        for renovation_type in renovation_types:
            scores = []
            for house_results in bulk_results.values():
                result = house_results.get(renovation_type, {})
                if result.get('integration_success'):
                    business_score = result.get('analysis', {}).get('business_viability', {}).get('overall_score', 0)
                    scores.append(business_score)

            if scores:
                renovation_scores[renovation_type] = sum(scores) / len(scores)

        # Sort by score
        sorted_renovations = sorted(renovation_scores.items(), key=lambda x: x[1], reverse=True)
        summary_stats['best_renovation_types'] = [r[0] for r in sorted_renovations[:3]]
        summary_stats['worst_renovation_types'] = [r[0] for r in sorted_renovations[-3:]]

        self.console.show_session_summary(bulk_results)

        return {
            'results': bulk_results,
            'summary': summary_stats,
            'timestamp': datetime.now().isoformat()
        }