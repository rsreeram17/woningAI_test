"""DSO Search API client for finding applicable rules and activities."""

from typing import Dict, Any, List, Optional
from .base_client import BaseAPIClient

class DSOSearchAPI(BaseAPIClient):
    """Client for DSO Search API - Toepasbare Regels Zoeken."""

    def __init__(self, config: Dict[str, Any], house_logger=None):
        """Initialize DSO Search API client."""
        # Set specific endpoint for search API
        search_config = config.copy()
        search_config['base_url'] = f"{config['base_url']}/toepasbare-regels/api/zoekinterface/v2"

        super().__init__(search_config, "DSO_Search", house_logger)

    def search_activities(self, search_term: str, sorting: str = "besteMatch",
                         renovation_type: str = None) -> Dict[str, Any]:
        """Search for applicable rules and activities.

        Args:
            search_term: Term to search for (e.g., 'dakkapel', 'uitbouw')
            sorting: Sorting method ('besteMatch', 'alfabetisch', etc.)
            renovation_type: Current renovation type being tested

        Returns:
            Dict with search results
        """
        payload = {
            "zoekterm": search_term,
            "sortering": sorting
        }

        result = self.post(
            endpoint="/activiteiten/_zoek",
            data=payload,
            renovation_type=renovation_type
        )

        if not result['success']:
            return result

        # Process search results
        response_data = result['data']

        # Extract activities if found
        activities = []
        total_found = 0

        if '_embedded' in response_data and 'activiteiten' in response_data['_embedded']:
            activities = response_data['_embedded']['activiteiten']
            total_found = len(activities)

        return {
            "success": True,
            "data": {
                "activities": activities,
                "total_found": total_found,
                "search_term": search_term,
                "sorting": sorting,
                "raw_response": response_data,
                "response_metadata": {
                    "duration": result['duration'],
                    "request_id": result['request_id']
                }
            }
        }

    def get_suggestions(self, search_term: str, renovation_type: str = None) -> Dict[str, Any]:
        """Get autocomplete suggestions for search terms.

        Args:
            search_term: Partial search term
            renovation_type: Current renovation type being tested

        Returns:
            Dict with suggested search terms
        """
        payload = {"zoekterm": search_term}

        result = self.post(
            endpoint="/activiteiten/_suggereer",
            data=payload,
            renovation_type=renovation_type
        )

        if not result['success']:
            return result

        response_data = result['data']

        # Extract suggestions
        suggestions = response_data.get('suggesties', [])

        return {
            "success": True,
            "data": {
                "suggestions": suggestions,
                "search_term": search_term,
                "total_suggestions": len(suggestions),
                "raw_response": response_data,
                "response_metadata": {
                    "duration": result['duration'],
                    "request_id": result['request_id']
                }
            }
        }

    def search_with_multiple_terms(self, search_terms: List[str],
                                  renovation_type: str = None) -> Dict[str, Any]:
        """Search with multiple terms and combine results.

        Args:
            search_terms: List of search terms to try
            renovation_type: Current renovation type being tested

        Returns:
            Dict with combined search results
        """
        all_results = {}
        combined_activities = []
        best_result = None
        best_count = 0

        for term in search_terms:
            print(f"  🔍 Searching for: '{term}'")

            result = self.search_activities(term, renovation_type=renovation_type)

            if result['success']:
                activities = result['data']['activities']
                activity_count = len(activities)

                all_results[term] = result
                combined_activities.extend(activities)

                # Track best result (most activities found)
                if activity_count > best_count:
                    best_count = activity_count
                    best_result = result

                print(f"    ✅ Found {activity_count} activities")
            else:
                print(f"    ❌ Search failed: {result.get('error', 'Unknown error')}")
                all_results[term] = result

        # Remove duplicates from combined activities
        unique_activities = []
        seen_ids = set()

        for activity in combined_activities:
            activity_id = activity.get('identificatie') or activity.get('functioneleStructuurRef')
            if activity_id and activity_id not in seen_ids:
                unique_activities.append(activity)
                seen_ids.add(activity_id)

        return {
            "success": len(unique_activities) > 0,
            "data": {
                "combined_activities": unique_activities,
                "total_unique_activities": len(unique_activities),
                "search_terms_used": search_terms,
                "individual_results": all_results,
                "best_single_result": best_result,
                "summary": {
                    "terms_searched": len(search_terms),
                    "successful_searches": len([r for r in all_results.values() if r.get('success')]),
                    "total_activities_found": len(unique_activities)
                }
            }
        }

    def extract_functional_structure_refs(self, search_result: Dict[str, Any]) -> List[str]:
        """Extract functional structure references from search results.

        Args:
            search_result: Result from search_activities or search_with_multiple_terms

        Returns:
            List of functional structure reference strings
        """
        refs = []

        if not search_result.get('success'):
            return refs

        data = search_result.get('data', {})

        # Handle single search result
        if 'activities' in data:
            activities = data['activities']
        # Handle multiple search result
        elif 'combined_activities' in data:
            activities = data['combined_activities']
        else:
            return refs

        # Extract references
        for activity in activities:
            ref = activity.get('functioneleStructuurRef')
            if ref and ref not in refs:
                refs.append(ref)

        return refs

    def analyze_search_quality(self, search_result: Dict[str, Any],
                              renovation_type: str) -> Dict[str, Any]:
        """Analyze the quality and relevance of search results.

        Args:
            search_result: Result from search operation
            renovation_type: Type of renovation being searched for

        Returns:
            Dict with quality analysis
        """
        if not search_result.get('success'):
            return {
                "quality_score": 0,
                "issues": ["Search failed"],
                "recommendations": ["Check search terms", "Verify API connectivity"]
            }

        data = search_result.get('data', {})
        activities = data.get('activities') or data.get('combined_activities', [])

        analysis = {
            "quality_score": 0,
            "total_activities": len(activities),
            "relevant_activities": 0,
            "issues": [],
            "recommendations": [],
            "activity_types": {}
        }

        if not activities:
            analysis['issues'].append("No activities found")
            analysis['recommendations'].append("Try different search terms")
            return analysis

        # Analyze activity relevance
        renovation_keywords = renovation_type.lower().split('_')

        for activity in activities:
            activity_name = activity.get('naam', '').lower()
            activity_type = activity.get('type', 'unknown')

            # Count activity types
            analysis['activity_types'][activity_type] = analysis['activity_types'].get(activity_type, 0) + 1

            # Check relevance
            if any(keyword in activity_name for keyword in renovation_keywords):
                analysis['relevant_activities'] += 1

        # Calculate quality score (0-100)
        base_score = min(len(activities) * 10, 50)  # 10 points per activity, max 50
        relevance_score = (analysis['relevant_activities'] / len(activities)) * 30  # 30 points for relevance
        completeness_score = 20 if len(activities) >= 3 else len(activities) * 7  # 20 points for completeness

        analysis['quality_score'] = int(base_score + relevance_score + completeness_score)

        # Generate recommendations
        if analysis['relevant_activities'] == 0:
            analysis['issues'].append("No activities seem directly relevant")
            analysis['recommendations'].append("Try more specific search terms")

        if len(activities) < 3:
            analysis['issues'].append("Few activities found")
            analysis['recommendations'].append("Try broader search terms")

        if analysis['quality_score'] >= 80:
            analysis['recommendations'].append("Excellent search results - proceed with testing")
        elif analysis['quality_score'] >= 60:
            analysis['recommendations'].append("Good search results - should work for testing")
        elif analysis['quality_score'] >= 40:
            analysis['recommendations'].append("Moderate results - may need refinement")
        else:
            analysis['recommendations'].append("Poor results - consider different approach")

        return analysis