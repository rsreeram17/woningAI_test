"""DSO Interactive Services API client for permit checks and compliance."""

from typing import Dict, Any, List, Optional
from .base_client import BaseAPIClient

class DSOInteractiveAPI(BaseAPIClient):
    """Client for DSO Interactive Services API - Uitvoeren Services."""

    def __init__(self, config: Dict[str, Any], house_logger=None):
        """Initialize DSO Interactive Services API client."""
        # Set specific endpoint for interactive API
        interactive_config = config.copy()
        interactive_config['base_url'] = f"{config['base_url']}/toepasbare-regels/api/uitvoerenservices/v2"

        super().__init__(interactive_config, "DSO_Interactive", house_logger)

    def check_permit_requirement(self, functional_structure_refs: List[str],
                                coordinates: List[float], answers: List[Dict] = None,
                                renovation_type: str = None) -> Dict[str, Any]:
        """Interactive permit requirement check.

        Args:
            functional_structure_refs: List of functional structure references
            coordinates: [X, Y] coordinates in RD format
            answers: Optional list of question answers
            renovation_type: Current renovation type being tested

        Returns:
            Dict with permit requirement results
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
            "functioneleStructuurRefs": [
                {
                    "functioneleStructuurRef": ref,
                    "antwoorden": answers or []
                } for ref in functional_structure_refs
            ],
            "_geo": {
                "intersects": {
                    "type": "Point",
                    "coordinates": coordinates
                }
            }
        }

        result = self.post(
            endpoint="/conclusie/_bepaal",
            data=payload,
            include_crs=True,
            renovation_type=renovation_type
        )

        if not result['success']:
            return result

        response_data = result['data']

        # Process permit check results
        permit_analysis = self._analyze_permit_response(response_data)

        return {
            "success": True,
            "data": {
                "permit_analysis": permit_analysis,
                "functional_refs": functional_structure_refs,
                "coordinates": coordinates,
                "raw_response": response_data,
                "response_metadata": {
                    "duration": result['duration'],
                    "request_id": result['request_id']
                }
            }
        }

    def get_filing_requirements(self, functional_structure_refs: List[str],
                               coordinates: List[float], answers: List[Dict] = None,
                               role: str = "INITIATIEFNEMER",
                               renovation_type: str = None) -> Dict[str, Any]:
        """Get filing requirements and documents needed.

        Args:
            functional_structure_refs: List of functional structure references
            coordinates: [X, Y] coordinates in RD format
            answers: Optional list of question answers
            role: Role designation (default: INITIATIEFNEMER)
            renovation_type: Current renovation type being tested

        Returns:
            Dict with filing requirements
        """
        if not functional_structure_refs:
            return {
                "success": False,
                "error": "No functional structure references provided",
                "error_type": "missing_references"
            }

        payload = {
            "functioneleStructuurRefs": [
                {
                    "functioneleStructuurRef": ref,
                    "antwoorden": answers or []
                } for ref in functional_structure_refs
            ],
            "_geo": {
                "intersects": {
                    "type": "Point",
                    "coordinates": coordinates
                }
            },
            "rolaanduiding": {
                "rol": role
            }
        }

        result = self.post(
            endpoint="/indieningsvereisten/_bepaal",
            data=payload,
            include_crs=True,
            renovation_type=renovation_type
        )

        if not result['success']:
            return result

        response_data = result['data']

        # Process filing requirements
        filing_analysis = self._analyze_filing_response(response_data)

        return {
            "success": True,
            "data": {
                "filing_analysis": filing_analysis,
                "role": role,
                "functional_refs": functional_structure_refs,
                "coordinates": coordinates,
                "raw_response": response_data,
                "response_metadata": {
                    "duration": result['duration'],
                    "request_id": result['request_id']
                }
            }
        }

    def get_compliance_measures(self, functional_structure_refs: List[str],
                               coordinates: List[float], answers: List[Dict] = None,
                               renovation_type: str = None) -> Dict[str, Any]:
        """Get compliance measures and rules to follow.

        Args:
            functional_structure_refs: List of functional structure references
            coordinates: [X, Y] coordinates in RD format
            answers: Optional list of question answers
            renovation_type: Current renovation type being tested

        Returns:
            Dict with compliance measures
        """
        payload = {
            "functioneleStructuurRefs": [
                {
                    "functioneleStructuurRef": ref,
                    "antwoorden": answers or []
                } for ref in functional_structure_refs
            ],
            "_geo": {
                "intersects": {
                    "type": "Point",
                    "coordinates": coordinates
                }
            }
        }

        result = self.post(
            endpoint="/maatregelen/_bepaal",
            data=payload,
            include_crs=True,
            renovation_type=renovation_type
        )

        if not result['success']:
            return result

        response_data = result['data']

        # Process compliance measures
        compliance_analysis = self._analyze_compliance_response(response_data)

        return {
            "success": True,
            "data": {
                "compliance_analysis": compliance_analysis,
                "functional_refs": functional_structure_refs,
                "coordinates": coordinates,
                "raw_response": response_data,
                "response_metadata": {
                    "duration": result['duration'],
                    "request_id": result['request_id']
                }
            }
        }

    def _analyze_permit_response(self, response_data: Any) -> Dict[str, Any]:
        """Analyze permit requirement response."""
        analysis = {
            "permit_required": None,
            "activities_analyzed": 0,
            "conclusions": [],
            "question_groups": [],
            "issues": []
        }

        if not isinstance(response_data, list):
            analysis['issues'].append("Unexpected response format")
            return analysis

        for item in response_data:
            if not isinstance(item, dict):
                continue

            analysis['activities_analyzed'] += 1

            # Extract conclusions
            if 'conclusies' in item:
                conclusions = item['conclusies']
                for conclusion in conclusions:
                    conclusion_text = conclusion.get('conclusieTekst', '')
                    conclusion_type = conclusion.get('conclusieType', '')

                    analysis['conclusions'].append({
                        "text": conclusion_text,
                        "type": conclusion_type
                    })

                    # Determine if permit is required
                    if 'vergunning' in conclusion_text.lower() or 'melding' in conclusion_text.lower():
                        analysis['permit_required'] = True
                    elif 'geen' in conclusion_text.lower() and 'vergunning' in conclusion_text.lower():
                        analysis['permit_required'] = False

            # Extract question groups
            if 'vraaggroepen' in item:
                question_groups = item['vraaggroepen']
                for group in question_groups:
                    group_info = {
                        "title": group.get('titel', ''),
                        "questions": []
                    }

                    if 'vragen' in group:
                        for question in group['vragen']:
                            group_info['questions'].append({
                                "text": question.get('vraag', ''),
                                "type": question.get('vraagType', ''),
                                "required": question.get('verplicht', False)
                            })

                    analysis['question_groups'].append(group_info)

        return analysis

    def _analyze_filing_response(self, response_data: Any) -> Dict[str, Any]:
        """Analyze filing requirements response."""
        analysis = {
            "documents_required": [],
            "total_requirements": 0,
            "categories": {},
            "issues": []
        }

        if not isinstance(response_data, list):
            analysis['issues'].append("Unexpected response format")
            return analysis

        for item in response_data:
            if not isinstance(item, dict):
                continue

            if 'indieningsvereisten' in item:
                requirements = item['indieningsvereisten']

                for req in requirements:
                    analysis['total_requirements'] += 1

                    doc_info = {
                        "name": req.get('naam', ''),
                        "description": req.get('beschrijving', ''),
                        "required": req.get('verplicht', False),
                        "category": req.get('categorie', 'unknown')
                    }

                    analysis['documents_required'].append(doc_info)

                    # Count by category
                    category = doc_info['category']
                    analysis['categories'][category] = analysis['categories'].get(category, 0) + 1

        return analysis

    def _analyze_compliance_response(self, response_data: Any) -> Dict[str, Any]:
        """Analyze compliance measures response."""
        analysis = {
            "measures": [],
            "total_measures": 0,
            "categories": {},
            "compliance_score": 0,
            "issues": []
        }

        if not isinstance(response_data, list):
            analysis['issues'].append("Unexpected response format")
            return analysis

        for item in response_data:
            if not isinstance(item, dict):
                continue

            if 'maatregelen' in item:
                measures = item['maatregelen']

                for measure in measures:
                    analysis['total_measures'] += 1

                    measure_info = {
                        "name": measure.get('naam', ''),
                        "description": measure.get('beschrijving', ''),
                        "type": measure.get('type', ''),
                        "mandatory": measure.get('verplicht', False)
                    }

                    analysis['measures'].append(measure_info)

                    # Count by type
                    measure_type = measure_info['type']
                    analysis['categories'][measure_type] = analysis['categories'].get(measure_type, 0) + 1

        # Calculate compliance score (simple heuristic)
        if analysis['total_measures'] > 0:
            mandatory_count = sum(1 for m in analysis['measures'] if m['mandatory'])
            analysis['compliance_score'] = int((mandatory_count / analysis['total_measures']) * 100)

        return analysis

    def run_complete_interactive_flow(self, functional_structure_refs: List[str],
                                     coordinates: List[float],
                                     renovation_type: str = None) -> Dict[str, Any]:
        """Run complete interactive flow: permit check, filing, and compliance.

        Args:
            functional_structure_refs: List of functional structure references
            coordinates: [X, Y] coordinates in RD format
            renovation_type: Current renovation type being tested

        Returns:
            Dict with complete interactive flow results
        """
        print(f"  🎯 Running complete interactive flow...")

        flow_results = {
            "permit_check": None,
            "filing_requirements": None,
            "compliance_measures": None,
            "flow_summary": {
                "steps_completed": 0,
                "steps_successful": 0,
                "total_duration": 0
            }
        }

        # Step 1: Permit Check
        print(f"    1️⃣ Checking permit requirements...")
        permit_result = self.check_permit_requirement(
            functional_structure_refs, coordinates, renovation_type=renovation_type
        )
        flow_results["permit_check"] = permit_result
        flow_results["flow_summary"]["steps_completed"] += 1
        flow_results["flow_summary"]["total_duration"] += permit_result.get("data", {}).get("response_metadata", {}).get("duration", 0)

        if permit_result.get("success"):
            flow_results["flow_summary"]["steps_successful"] += 1

        # Step 2: Filing Requirements
        print(f"    2️⃣ Getting filing requirements...")
        filing_result = self.get_filing_requirements(
            functional_structure_refs, coordinates, renovation_type=renovation_type
        )
        flow_results["filing_requirements"] = filing_result
        flow_results["flow_summary"]["steps_completed"] += 1
        flow_results["flow_summary"]["total_duration"] += filing_result.get("data", {}).get("response_metadata", {}).get("duration", 0)

        if filing_result.get("success"):
            flow_results["flow_summary"]["steps_successful"] += 1

        # Step 3: Compliance Measures
        print(f"    3️⃣ Getting compliance measures...")
        compliance_result = self.get_compliance_measures(
            functional_structure_refs, coordinates, renovation_type=renovation_type
        )
        flow_results["compliance_measures"] = compliance_result
        flow_results["flow_summary"]["steps_completed"] += 1
        flow_results["flow_summary"]["total_duration"] += compliance_result.get("data", {}).get("response_metadata", {}).get("duration", 0)

        if compliance_result.get("success"):
            flow_results["flow_summary"]["steps_successful"] += 1

        # Calculate success rate
        success_rate = flow_results["flow_summary"]["steps_successful"] / flow_results["flow_summary"]["steps_completed"]
        flow_results["flow_summary"]["success_rate"] = success_rate

        return {
            "success": success_rate > 0.5,  # At least 50% success rate
            "data": flow_results
        }