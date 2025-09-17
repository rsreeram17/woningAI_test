"""DSO Routing API client for finding responsible authorities."""

from typing import Dict, Any, List, Optional
from .base_client import BaseAPIClient

class DSORoutingAPI(BaseAPIClient):
    """Client for DSO Routing API - Verzoeksroutering."""

    def __init__(self, config: Dict[str, Any], house_logger=None):
        """Initialize DSO Routing API client."""
        # Set specific endpoint for routing API
        routing_config = config.copy()
        routing_config['base_url'] = f"{config['base_url']}/toepasbare-regels/api/verzoeksroutering/v2"

        super().__init__(routing_config, "DSO_Routing", house_logger)

    def find_responsible_authority(self, functional_structure_refs: List[str],
                                  coordinates: List[float],
                                  renovation_type: str = None) -> Dict[str, Any]:
        """Find responsible government authority.

        Args:
            functional_structure_refs: List of functional structure references
            coordinates: [X, Y] coordinates in RD format
            renovation_type: Current renovation type being tested

        Returns:
            Dict with responsible authority information
        """
        if not functional_structure_refs:
            return {
                "success": False,
                "error": "No functional structure references provided",
                "error_type": "missing_references"
            }

        if not coordinates or len(coordinates) < 2:
            return {
                "success": False,
                "error": "Invalid coordinates provided",
                "error_type": "invalid_coordinates"
            }

        payload = {
            "functioneleStructuurRefs": functional_structure_refs,
            "locatie": {
                "type": "Point",
                "coordinates": coordinates
            }
        }

        result = self.post(
            endpoint="/bevoegd-gezag-bepalen",
            data=payload,
            renovation_type=renovation_type
        )

        if not result['success']:
            return result

        response_data = result['data']

        # Process authority response
        authority_analysis = self._analyze_authority_response(response_data)

        return {
            "success": True,
            "data": {
                "authority_analysis": authority_analysis,
                "functional_refs": functional_structure_refs,
                "coordinates": coordinates,
                "raw_response": response_data,
                "response_metadata": {
                    "duration": result['duration'],
                    "request_id": result['request_id']
                }
            }
        }

    def check_concept_request_allowed(self, authority_oin: str,
                                     functional_structure_refs: List[str],
                                     renovation_type: str = None) -> Dict[str, Any]:
        """Check if concept request is allowed.

        Args:
            authority_oin: Authority OIN (organization identification number)
            functional_structure_refs: List of functional structure references
            renovation_type: Current renovation type being tested

        Returns:
            Dict with concept request allowance information
        """
        payload = {
            "bevoegdGezagOin": authority_oin,
            "functioneleStructuurRefs": functional_structure_refs
        }

        result = self.post(
            endpoint="/conceptverzoek-bepalen",
            data=payload,
            renovation_type=renovation_type
        )

        if not result['success']:
            return result

        response_data = result['data']

        return {
            "success": True,
            "data": {
                "concept_request_allowed": response_data.get('toegestaan', False),
                "authority_oin": authority_oin,
                "functional_refs": functional_structure_refs,
                "raw_response": response_data,
                "response_metadata": {
                    "duration": result['duration'],
                    "request_id": result['request_id']
                }
            }
        }

    def find_processing_service(self, authority_oin: str,
                               functional_structure_refs: List[str],
                               coordinates: List[float],
                               renovation_type: str = None) -> Dict[str, Any]:
        """Find processing service for the application.

        Args:
            authority_oin: Authority OIN
            functional_structure_refs: List of functional structure references
            coordinates: [X, Y] coordinates in RD format
            renovation_type: Current renovation type being tested

        Returns:
            Dict with processing service information
        """
        payload = {
            "bevoegdGezagOin": authority_oin,
            "functioneleStructuurRefs": functional_structure_refs,
            "locatie": {
                "type": "Point",
                "coordinates": coordinates
            }
        }

        result = self.post(
            endpoint="/behandeldienst-bepalen",
            data=payload,
            renovation_type=renovation_type
        )

        if not result['success']:
            return result

        response_data = result['data']

        return {
            "success": True,
            "data": {
                "processing_service": response_data,
                "authority_oin": authority_oin,
                "functional_refs": functional_structure_refs,
                "coordinates": coordinates,
                "raw_response": response_data,
                "response_metadata": {
                    "duration": result['duration'],
                    "request_id": result['request_id']
                }
            }
        }

    def _analyze_authority_response(self, response_data: Any) -> Dict[str, Any]:
        """Analyze responsible authority response."""
        analysis = {
            "authorities_found": 0,
            "primary_authority": None,
            "all_authorities": [],
            "contact_info": {},
            "issues": []
        }

        if not response_data:
            analysis['issues'].append("Empty response")
            return analysis

        # Handle different response formats
        if isinstance(response_data, list):
            authorities = response_data
        elif isinstance(response_data, dict) and 'bevoegdeGezagen' in response_data:
            authorities = response_data['bevoegdeGezagen']
        else:
            analysis['issues'].append("Unexpected response format")
            return analysis

        analysis['authorities_found'] = len(authorities)

        for authority in authorities:
            if not isinstance(authority, dict):
                continue

            authority_info = {
                "name": authority.get('naam', ''),
                "oin": authority.get('oin', ''),
                "type": authority.get('type', ''),
                "contact": {}
            }

            # Extract contact information
            if 'contactgegevens' in authority:
                contact = authority['contactgegevens']
                authority_info['contact'] = {
                    "address": contact.get('adres', ''),
                    "phone": contact.get('telefoon', ''),
                    "email": contact.get('email', ''),
                    "website": contact.get('website', '')
                }

            analysis['all_authorities'].append(authority_info)

            # Set primary authority (first one or most complete)
            if not analysis['primary_authority'] or len(authority_info['contact']) > len(analysis['primary_authority'].get('contact', {})):
                analysis['primary_authority'] = authority_info

        # Extract general contact info
        if analysis['primary_authority']:
            analysis['contact_info'] = analysis['primary_authority']['contact']

        return analysis

    def run_complete_routing_flow(self, functional_structure_refs: List[str],
                                 coordinates: List[float],
                                 renovation_type: str = None) -> Dict[str, Any]:
        """Run complete routing flow to find authority and processing service.

        Args:
            functional_structure_refs: List of functional structure references
            coordinates: [X, Y] coordinates in RD format
            renovation_type: Current renovation type being tested

        Returns:
            Dict with complete routing flow results
        """
        print(f"  🏛️ Running authority routing flow...")

        flow_results = {
            "responsible_authority": None,
            "concept_request_check": None,
            "processing_service": None,
            "flow_summary": {
                "steps_completed": 0,
                "steps_successful": 0,
                "total_duration": 0
            }
        }

        # Step 1: Find Responsible Authority
        print(f"    1️⃣ Finding responsible authority...")
        authority_result = self.find_responsible_authority(
            functional_structure_refs, coordinates, renovation_type=renovation_type
        )
        flow_results["responsible_authority"] = authority_result
        flow_results["flow_summary"]["steps_completed"] += 1
        flow_results["flow_summary"]["total_duration"] += authority_result.get("data", {}).get("response_metadata", {}).get("duration", 0)

        if authority_result.get("success"):
            flow_results["flow_summary"]["steps_successful"] += 1

            # Extract primary authority OIN for next steps
            authority_data = authority_result.get("data", {})
            authority_analysis = authority_data.get("authority_analysis", {})
            primary_authority = authority_analysis.get("primary_authority")

            if primary_authority and primary_authority.get("oin"):
                authority_oin = primary_authority["oin"]

                # Step 2: Check Concept Request
                print(f"    2️⃣ Checking concept request allowance...")
                concept_result = self.check_concept_request_allowed(
                    authority_oin, functional_structure_refs, renovation_type=renovation_type
                )
                flow_results["concept_request_check"] = concept_result
                flow_results["flow_summary"]["steps_completed"] += 1
                flow_results["flow_summary"]["total_duration"] += concept_result.get("data", {}).get("response_metadata", {}).get("duration", 0)

                if concept_result.get("success"):
                    flow_results["flow_summary"]["steps_successful"] += 1

                # Step 3: Find Processing Service
                print(f"    3️⃣ Finding processing service...")
                service_result = self.find_processing_service(
                    authority_oin, functional_structure_refs, coordinates, renovation_type=renovation_type
                )
                flow_results["processing_service"] = service_result
                flow_results["flow_summary"]["steps_completed"] += 1
                flow_results["flow_summary"]["total_duration"] += service_result.get("data", {}).get("response_metadata", {}).get("duration", 0)

                if service_result.get("success"):
                    flow_results["flow_summary"]["steps_successful"] += 1
            else:
                print(f"    ⚠️ No authority OIN found, skipping additional steps")

        # Calculate success rate
        if flow_results["flow_summary"]["steps_completed"] > 0:
            success_rate = flow_results["flow_summary"]["steps_successful"] / flow_results["flow_summary"]["steps_completed"]
            flow_results["flow_summary"]["success_rate"] = success_rate
        else:
            flow_results["flow_summary"]["success_rate"] = 0

        return {
            "success": flow_results["flow_summary"]["success_rate"] > 0,
            "data": flow_results
        }