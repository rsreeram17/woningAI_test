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

    def get_activity_lifecycle(self, activity_id: str, renovation_type: str = None) -> Dict[str, Any]:
        """Get complete lifecycle information for an activity.

        Args:
            activity_id: Activity identifier (e.g., 'nl.imow-gm0037.activiteit.2019000242example')
            renovation_type: Current renovation type being tested

        Returns:
            Dict with activity lifecycle information
        """
        result = self.get(
            endpoint=f"/activiteiten/{activity_id}/levenscyclus",
            renovation_type=renovation_type
        )

        if not result['success']:
            return result

        # Process response
        response_data = result['data']

        # Extract activities if found
        activities = []
        if '_embedded' in response_data and 'activiteiten' in response_data['_embedded']:
            activities = response_data['_embedded']['activiteiten']

        return {
            "success": True,
            "data": {
                "activity_id": activity_id,
                "activities": activities,
                "total_found": len(activities),
                "raw_response": response_data,
                "response_metadata": {
                    "duration": result['duration'],
                    "request_id": result['request_id']
                }
            }
        }

    def get_legal_source(self, activity_id: str, renovation_type: str = None,
                        valid_on: str = None, in_effect_on: str = None,
                        available_at: str = None) -> Dict[str, Any]:
        """Get legal source information for an activity.

        Args:
            activity_id: Activity identifier
            renovation_type: Current renovation type being tested
            valid_on: Valid on specific date (yyyy-mm-dd)
            in_effect_on: In effect on specific date (yyyy-mm-dd)
            available_at: Available at specific datetime (ISO 8601)

        Returns:
            Dict with legal source information
        """
        params = {}
        if valid_on:
            params['geldigOp'] = valid_on
        if in_effect_on:
            params['inWerkingOp'] = in_effect_on
        if available_at:
            params['beschikbaarOp'] = available_at

        result = self.get(
            endpoint=f"/activiteiten/{activity_id}/juridischebron",
            params=params,
            renovation_type=renovation_type
        )

        if not result['success']:
            return result

        # Process response
        response_data = result['data']

        # Extract legal source information
        document_id = response_data.get('documentIdentificatie', '')
        rule_texts = response_data.get('regelteksten', [])

        return {
            "success": True,
            "data": {
                "activity_id": activity_id,
                "document_identification": document_id,
                "rule_texts": rule_texts,
                "total_rule_texts": len(rule_texts),
                "raw_response": response_data,
                "response_metadata": {
                    "duration": result['duration'],
                    "request_id": result['request_id']
                }
            }
        }

    def get_rule_texts(self, activity_id: str, renovation_type: str = None,
                      valid_on: str = None, in_effect_on: str = None,
                      available_at: str = None, page: int = 0, size: int = 20) -> Dict[str, Any]:
        """Get all legal texts that mention this activity.

        Args:
            activity_id: Activity identifier
            renovation_type: Current renovation type being tested
            valid_on: Valid on specific date (yyyy-mm-dd)
            in_effect_on: In effect on specific date (yyyy-mm-dd)
            available_at: Available at specific datetime (ISO 8601)
            page: Page number (default: 0)
            size: Items per page (1-200, default: 20)

        Returns:
            Dict with rule texts information
        """
        params = {
            'page': page,
            'size': size
        }
        if valid_on:
            params['geldigOp'] = valid_on
        if in_effect_on:
            params['inWerkingOp'] = in_effect_on
        if available_at:
            params['beschikbaarOp'] = available_at

        result = self.get(
            endpoint=f"/activiteiten/{activity_id}/regelteksten",
            params=params,
            renovation_type=renovation_type
        )

        if not result['success']:
            return result

        # Process response
        response_data = result['data']

        # Extract rule texts
        rule_texts = []
        if '_embedded' in response_data and 'regelteksten' in response_data['_embedded']:
            rule_texts = response_data['_embedded']['regelteksten']
        elif isinstance(response_data, list):
            rule_texts = response_data

        # Extract pagination info
        page_info = response_data.get('page', {}) if isinstance(response_data, dict) else {}

        return {
            "success": True,
            "data": {
                "activity_id": activity_id,
                "rule_texts": rule_texts,
                "total_found": len(rule_texts),
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

    def get_single_location(self, location_id: str, renovation_type: str = None,
                           valid_on: str = None, in_effect_on: str = None,
                           available_at: str = None) -> Dict[str, Any]:
        """Get detailed information about a specific location.

        Args:
            location_id: Location identifier
            renovation_type: Current renovation type being tested
            valid_on: Valid on specific date (yyyy-mm-dd)
            in_effect_on: In effect on specific date (yyyy-mm-dd)
            available_at: Available at specific datetime (ISO 8601)

        Returns:
            Dict with location information
        """
        params = {}
        if valid_on:
            params['geldigOp'] = valid_on
        if in_effect_on:
            params['inWerkingOp'] = in_effect_on
        if available_at:
            params['beschikbaarOp'] = available_at

        result = self.get(
            endpoint=f"/locaties/{location_id}",
            params=params,
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

    def extract_activity_ids_from_functional_refs(self, functional_refs: List[str]) -> List[str]:
        """Extract activity IDs from functional structure references.

        Args:
            functional_refs: List of functional structure reference URLs

        Returns:
            List of activity IDs that can be used with this API
        """
        activity_ids = []

        for ref in functional_refs:
            if not ref:
                continue

            # Try to extract activity ID from URL
            # Expected format: https://.../.../activiteiten/{activity_id}/...
            if '/activiteiten/' in ref:
                parts = ref.split('/activiteiten/')
                if len(parts) > 1:
                    # Get the part after /activiteiten/
                    activity_part = parts[1]
                    # Take everything before the next slash (if any)
                    activity_id = activity_part.split('/')[0]
                    if activity_id and activity_id not in activity_ids:
                        activity_ids.append(activity_id)
            else:
                # If it's already just an ID, use it directly
                # Check if it looks like an activity ID (contains 'activiteit')
                if 'activiteit' in ref:
                    activity_ids.append(ref)

        return activity_ids

    def validate_and_get_activity_details(self, functional_refs: List[str],
                                         renovation_type: str = None) -> Dict[str, Any]:
        """Validate functional references and get detailed activity information.

        Args:
            functional_refs: List of functional structure references from search
            renovation_type: Current renovation type being tested

        Returns:
            Dict with validation results and activity details
        """
        if not functional_refs:
            return {
                "success": False,
                "error": "No functional structure references provided",
                "error_type": "missing_references"
            }

        print(f"🔍 Extracting activity IDs from {len(functional_refs)} functional references...")

        # Extract activity IDs
        activity_ids = self.extract_activity_ids_from_functional_refs(functional_refs)

        if not activity_ids:
            return {
                "success": False,
                "error": "Could not extract activity IDs from functional references",
                "error_type": "invalid_references",
                "functional_refs": functional_refs
            }

        print(f"✅ Found {len(activity_ids)} activity IDs")

        # Get details for each activity
        activity_details = {}
        successful_lookups = 0

        for activity_id in activity_ids:
            print(f"  📋 Getting details for activity: {activity_id}")

            # Get lifecycle information
            lifecycle_result = self.get_activity_lifecycle(activity_id, renovation_type)

            # Get legal source
            legal_source_result = self.get_legal_source(activity_id, renovation_type)

            # Get rule texts
            rule_texts_result = self.get_rule_texts(activity_id, renovation_type)

            if lifecycle_result['success'] or legal_source_result['success'] or rule_texts_result['success']:
                successful_lookups += 1
                activity_details[activity_id] = {
                    "lifecycle": lifecycle_result,
                    "legal_source": legal_source_result,
                    "rule_texts": rule_texts_result
                }
                print(f"    ✅ Successfully retrieved details")
            else:
                print(f"    ❌ Failed to retrieve details")
                activity_details[activity_id] = {
                    "lifecycle": lifecycle_result,
                    "legal_source": legal_source_result,
                    "rule_texts": rule_texts_result
                }

        return {
            "success": successful_lookups > 0,
            "data": {
                "activity_ids": activity_ids,
                "activity_details": activity_details,
                "successful_lookups": successful_lookups,
                "total_attempted": len(activity_ids),
                "functional_refs": functional_refs
            }
        }