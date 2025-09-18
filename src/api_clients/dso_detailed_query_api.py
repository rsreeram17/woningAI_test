"""DSO Detailed Query API client for getting detailed legal information about activities."""

from typing import Dict, Any, List, Optional
from .base_client import BaseAPIClient

class DSODetailedQueryAPI(BaseAPIClient):
    """Client for DSO Detailed Query API - Omgevingsdocument Toepasbaar Opvragen."""

    def __init__(self, config: Dict[str, Any], house_logger=None):
        """Initialize DSO Detailed Query API client."""
        # Set specific endpoint for detailed query API
        detailed_config = config.copy()
        detailed_config['base_url'] = f"{config['base_url']}/omgevingsdocumenten/api/toepasbaaropvragen/v7"

        super().__init__(detailed_config, "DSO_DetailedQuery", house_logger)

    def search_activity_identifications(self, coordinates: List[float],
                                      spatial_operator: str = "intersects",
                                      renovation_type: str = None) -> Dict[str, Any]:
        """Search for activity identifications based on geographic criteria.

        Args:
            coordinates: [X, Y] coordinates in RD format
            spatial_operator: 'intersects' or 'within'
            renovation_type: Current renovation type being tested

        Returns:
            Dict with activity identification search results
        """
        if not coordinates or len(coordinates) < 2:
            return {
                "success": False,
                "error": "Invalid coordinates provided",
                "error_type": "invalid_coordinates"
            }

        # Create polygon around the point for search
        # Using a small buffer around the point (10 meters)
        x, y = coordinates[0], coordinates[1]
        buffer = 10  # 10 meter buffer

        payload = {
            "geometrie": {
                "type": "Polygon",
                "coordinates": [[
                    [x - buffer, y - buffer],
                    [x + buffer, y - buffer],
                    [x + buffer, y + buffer],
                    [x - buffer, y + buffer],
                    [x - buffer, y - buffer]
                ]]
            },
            "spatialOperator": spatial_operator
        }

        result = self.post(
            endpoint="/activiteitidentificaties/_zoek",
            data=payload,
            renovation_type=renovation_type,
            include_crs=True  # Required for geographic searches
        )

        if not result['success']:
            return result

        # Process response
        response_data = result['data']

        # The response should be a list of activity identifications
        activity_ids = []
        if isinstance(response_data, list):
            activity_ids = response_data
        elif isinstance(response_data, dict) and '_embedded' in response_data:
            activity_ids = response_data.get('_embedded', {}).get('activiteitidentificaties', [])

        return {
            "success": True,
            "data": {
                "activity_identifications": activity_ids,
                "total_found": len(activity_ids),
                "search_criteria": {
                    "coordinates": coordinates,
                    "spatial_operator": spatial_operator,
                    "buffer_meters": buffer
                },
                "raw_response": response_data,
                "response_metadata": {
                    "duration": result['duration'],
                    "request_id": result['request_id']
                }
            }
        }

    def get_aggregated_activities(self, page: int = 0, size: int = 20,
                                renovation_type: str = None) -> Dict[str, Any]:
        """Get aggregated activities from the system.

        Args:
            page: Page number (default: 0)
            size: Items per page (1-200, default: 20)
            renovation_type: Current renovation type being tested

        Returns:
            Dict with aggregated activities information
        """
        params = {
            'page': page,
            'size': size
        }

        result = self.get(
            endpoint="/activiteitengeaggregeerd/levenscyclus",
            params=params,
            renovation_type=renovation_type
        )

        if not result['success']:
            return result

        # Process response
        response_data = result['data']

        # Extract activities
        activities = []
        if '_embedded' in response_data and 'activiteitengeaggregeerd' in response_data['_embedded']:
            activities = response_data['_embedded']['activiteitengeaggregeerd']
        elif isinstance(response_data, list):
            activities = response_data

        # Extract pagination info
        page_info = response_data.get('page', {}) if isinstance(response_data, dict) else {}

        return {
            "success": True,
            "data": {
                "activities": activities,
                "total_found": len(activities),
                "pagination": page_info,
                "raw_response": response_data,
                "response_metadata": {
                    "duration": result['duration'],
                    "request_id": result['request_id']
                }
            }
        }

    def search_locations(self, coordinates: List[float], spatial_operator: str = "intersects",
                        location_ids: List[str] = None, renovation_type: str = None) -> Dict[str, Any]:
        """Find locations based on geographic criteria.

        Args:
            coordinates: [X, Y] coordinates in RD format
            spatial_operator: 'intersects' or 'within'
            location_ids: Optional list of specific location identifiers to search
            renovation_type: Current renovation type being tested

        Returns:
            Dict with location search results
        """
        if not coordinates or len(coordinates) < 2:
            return {
                "success": False,
                "error": "Invalid coordinates provided",
                "error_type": "invalid_coordinates"
            }

        payload = {
            "geo": {
                "geometrie": {
                    "type": "Point",
                    "coordinates": coordinates
                },
                "spatialOperator": spatial_operator
            }
        }

        if location_ids:
            payload["locatieIdentificaties"] = location_ids

        result = self.post(
            endpoint="/locaties/_zoek",
            data=payload,
            renovation_type=renovation_type,
            include_crs=True  # Required for geographic searches
        )

        if not result['success']:
            return result

        # Process response
        response_data = result['data']

        # Extract locations
        locations = []
        if '_embedded' in response_data and 'locaties' in response_data['_embedded']:
            locations = response_data['_embedded']['locaties']
        elif isinstance(response_data, list):
            locations = response_data

        return {
            "success": True,
            "data": {
                "locations": locations,
                "total_found": len(locations),
                "search_criteria": {
                    "coordinates": coordinates,
                    "spatial_operator": spatial_operator,
                    "location_ids": location_ids
                },
                "raw_response": response_data,
                "response_metadata": {
                    "duration": result['duration'],
                    "request_id": result['request_id']
                }
            }
        }

    def search_location_identifications(self, coordinates: List[float],
                                      spatial_operator: str = "intersects",
                                      renovation_type: str = None) -> Dict[str, Any]:
        """Search for location identifications based on geographic criteria.

        Args:
            coordinates: [X, Y] coordinates in RD format
            spatial_operator: 'intersects' or 'within'
            renovation_type: Current renovation type being tested

        Returns:
            Dict with location identification search results
        """
        if not coordinates or len(coordinates) < 2:
            return {
                "success": False,
                "error": "Invalid coordinates provided",
                "error_type": "invalid_coordinates"
            }

        # Create polygon around the point for search
        x, y = coordinates[0], coordinates[1]
        buffer = 10  # 10 meter buffer

        payload = {
            "geometrie": {
                "type": "Polygon",
                "coordinates": [[
                    [x - buffer, y - buffer],
                    [x + buffer, y - buffer],
                    [x + buffer, y + buffer],
                    [x - buffer, y + buffer],
                    [x - buffer, y - buffer]
                ]]
            },
            "spatialOperator": spatial_operator
        }

        result = self.post(
            endpoint="/locatieidentificaties/_zoek",
            data=payload,
            renovation_type=renovation_type,
            include_crs=True  # Required for geographic searches
        )

        if not result['success']:
            return result

        # Process response
        response_data = result['data']

        # The response should be a list of location identifications
        location_ids = []
        if isinstance(response_data, list):
            location_ids = response_data
        elif isinstance(response_data, dict) and '_embedded' in response_data:
            location_ids = response_data.get('_embedded', {}).get('locatieidentificaties', [])

        return {
            "success": True,
            "data": {
                "location_identifications": location_ids,
                "total_found": len(location_ids),
                "search_criteria": {
                    "coordinates": coordinates,
                    "spatial_operator": spatial_operator,
                    "buffer_meters": buffer
                },
                "raw_response": response_data,
                "response_metadata": {
                    "duration": result['duration'],
                    "request_id": result['request_id']
                }
            }
        }

    def get_single_location(self, location_id: str, renovation_type: str = None) -> Dict[str, Any]:
        """Get detailed information about a specific location.

        Args:
            location_id: Location identifier
            renovation_type: Current renovation type being tested

        Returns:
            Dict with location information
        """
        result = self.get(
            endpoint=f"/locaties/{location_id}",
            renovation_type=renovation_type
        )

        if not result['success']:
            return result

        # Process response
        response_data = result['data']

        return {
            "success": True,
            "data": {
                "location_id": location_id,
                "location_info": response_data,
                "raw_response": response_data,
                "response_metadata": {
                    "duration": result['duration'],
                    "request_id": result['request_id']
                }
            }
        }

    def validate_coordinates_and_get_context(self, coordinates: List[float],
                                           renovation_type: str = None) -> Dict[str, Any]:
        """Validate coordinates and get comprehensive context information.

        Args:
            coordinates: [X, Y] coordinates in RD format
            renovation_type: Current renovation type being tested

        Returns:
            Dict with validation results and context information
        """
        if not coordinates or len(coordinates) < 2:
            return {
                "success": False,
                "error": "Invalid coordinates provided",
                "error_type": "invalid_coordinates"
            }

        print(f"🔍 Validating coordinates and getting context: [{coordinates[0]}, {coordinates[1]}]")

        # Test 1: Search for activity identifications
        print("  📋 Searching for activity identifications...")
        activity_ids_result = self.search_activity_identifications(coordinates, renovation_type=renovation_type)

        # Test 2: Search for location identifications
        print("  📍 Searching for location identifications...")
        location_ids_result = self.search_location_identifications(coordinates, renovation_type=renovation_type)

        # Test 3: Search for locations
        print("  🗺️ Searching for locations...")
        locations_result = self.search_locations(coordinates, renovation_type=renovation_type)

        # Test 4: Get sample aggregated activities
        print("  📚 Getting sample aggregated activities...")
        activities_result = self.get_aggregated_activities(size=10, renovation_type=renovation_type)

        successful_tests = sum([
            activity_ids_result.get('success', False),
            location_ids_result.get('success', False),
            locations_result.get('success', False),
            activities_result.get('success', False)
        ])

        return {
            "success": successful_tests > 0,
            "data": {
                "coordinates": coordinates,
                "activity_identifications": activity_ids_result,
                "location_identifications": location_ids_result,
                "locations": locations_result,
                "sample_activities": activities_result,
                "test_summary": {
                    "successful_tests": successful_tests,
                    "total_tests": 4,
                    "success_rate": (successful_tests / 4) * 100
                }
            }
        }

    def get_activity_lifecycle(self, activity_id: str, renovation_type: str = None) -> Dict[str, Any]:
        """Get lifecycle information for a specific activity, including location relationships.

        Args:
            activity_id: Activity identifier (e.g., 'nl.imow-gm0363.activiteit.abc123')
            renovation_type: Current renovation type being tested

        Returns:
            Dict with activity lifecycle and location relationships
        """
        result = self.get(
            endpoint=f"/activiteiten/{activity_id}/levenscyclus",
            renovation_type=renovation_type
        )

        if not result['success']:
            return result

        # Process response
        response_data = result['data']

        return {
            "success": True,
            "data": {
                "activity_id": activity_id,
                "lifecycle_info": response_data,
                "raw_response": response_data,
                "response_metadata": {
                    "duration": result['duration'],
                    "request_id": result['request_id']
                }
            }
        }

    def get_activity_location_mapping(self, activity_ids: List[str],
                                    renovation_type: str = None) -> Dict[str, Any]:
        """Get location relationships for multiple activities.

        Args:
            activity_ids: List of activity identifiers
            renovation_type: Current renovation type being tested

        Returns:
            Dict with activity-location mapping information
        """
        if not activity_ids:
            return {
                "success": False,
                "error": "No activity IDs provided",
                "error_type": "invalid_input"
            }

        print(f"🔍 Getting location relationships for {len(activity_ids)} activities...")

        activity_mappings = {}
        successful_lookups = 0

        # Test with first few activities (to avoid too many API calls)
        test_activities = activity_ids[:5]

        for i, activity_id in enumerate(test_activities, 1):
            print(f"  📋 {i}/{len(test_activities)}: {activity_id[:50]}...")

            lifecycle_result = self.get_activity_lifecycle(activity_id, renovation_type=renovation_type)

            if lifecycle_result['success']:
                successful_lookups += 1
                lifecycle_data = lifecycle_result['data']['lifecycle_info']

                # Extract location references from lifecycle data
                locations = []

                # Handle _embedded structure
                activities_data = []
                if isinstance(lifecycle_data, dict) and '_embedded' in lifecycle_data:
                    activities_data = lifecycle_data['_embedded'].get('activiteiten', [])
                elif isinstance(lifecycle_data, list):
                    activities_data = lifecycle_data
                elif isinstance(lifecycle_data, dict):
                    activities_data = [lifecycle_data]

                for activity in activities_data:
                    if 'isGereguleerdVoor' in activity:
                        for location_ref in activity['isGereguleerdVoor']:
                            if isinstance(location_ref, dict) and 'identificatie' in location_ref:
                                locations.append(location_ref['identificatie'])
                            elif isinstance(location_ref, str):
                                locations.append(location_ref)

                activity_mappings[activity_id] = {
                    "locations": list(set(locations)),  # Remove duplicates
                    "lifecycle_versions": len(lifecycle_data) if isinstance(lifecycle_data, list) else 1
                }
            else:
                activity_mappings[activity_id] = {
                    "error": lifecycle_result.get('error', 'Unknown error'),
                    "locations": []
                }

        return {
            "success": successful_lookups > 0,
            "data": {
                "total_activities_tested": len(test_activities),
                "successful_lookups": successful_lookups,
                "activity_location_mappings": activity_mappings,
                "summary": {
                    "activities_with_locations": len([a for a in activity_mappings.values() if a.get('locations')]),
                    "total_unique_locations": len(set(
                        loc for mapping in activity_mappings.values()
                        for loc in mapping.get('locations', [])
                    ))
                }
            }
        }