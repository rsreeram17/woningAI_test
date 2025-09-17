"""DSO Catalog API client for term definitions and explanations."""

from typing import Dict, Any, List, Optional
from .base_client import BaseAPIClient

class DSOCatalogAPI(BaseAPIClient):
    """Client for DSO Catalog API - Catalogus Opvragen."""

    def __init__(self, config: Dict[str, Any], house_logger=None):
        """Initialize DSO Catalog API client."""
        # Set specific endpoint for catalog API
        catalog_config = config.copy()
        catalog_config['base_url'] = f"{config['base_url']}/catalogus/api/opvragen/v3"

        super().__init__(catalog_config, "DSO_Catalog", house_logger)

    def search_concepts(self, search_term: str, page_size: int = 20,
                       renovation_type: str = None) -> Dict[str, Any]:
        """Search for concept definitions and explanations.

        Args:
            search_term: Term to search for
            page_size: Number of results per page
            renovation_type: Current renovation type being tested

        Returns:
            Dict with concept search results
        """
        params = {
            "zoekTerm": search_term,
            "pageSize": page_size
        }

        result = self.get(
            endpoint="/concepten",
            params=params,
            renovation_type=renovation_type
        )

        if not result['success']:
            return result

        response_data = result['data']

        # Process concept search results
        concepts = response_data.get('concepten', [])
        total_found = len(concepts)

        return {
            "success": True,
            "data": {
                "concepts": concepts,
                "total_found": total_found,
                "search_term": search_term,
                "page_size": page_size,
                "raw_response": response_data,
                "response_metadata": {
                    "duration": result['duration'],
                    "request_id": result['request_id']
                }
            }
        }

    def get_concept_by_uri(self, concept_uri: str,
                          renovation_type: str = None) -> Dict[str, Any]:
        """Get specific concept by URI.

        Args:
            concept_uri: URI of the concept
            renovation_type: Current renovation type being tested

        Returns:
            Dict with concept details
        """
        params = {"uri": concept_uri}

        result = self.get(
            endpoint="/concepten",
            params=params,
            renovation_type=renovation_type
        )

        if not result['success']:
            return result

        response_data = result['data']

        return {
            "success": True,
            "data": {
                "concept": response_data,
                "concept_uri": concept_uri,
                "raw_response": response_data,
                "response_metadata": {
                    "duration": result['duration'],
                    "request_id": result['request_id']
                }
            }
        }

    def search_multiple_concepts(self, search_terms: List[str],
                                renovation_type: str = None) -> Dict[str, Any]:
        """Search for multiple concepts and combine results.

        Args:
            search_terms: List of terms to search for
            renovation_type: Current renovation type being tested

        Returns:
            Dict with combined concept search results
        """
        all_results = {}
        combined_concepts = []
        total_concepts = 0

        for term in search_terms:
            print(f"  📚 Searching concepts for: '{term}'")

            result = self.search_concepts(term, renovation_type=renovation_type)

            if result['success']:
                concepts = result['data']['concepts']
                concept_count = len(concepts)

                all_results[term] = result
                combined_concepts.extend(concepts)
                total_concepts += concept_count

                print(f"    ✅ Found {concept_count} concept definitions")
            else:
                print(f"    ❌ Search failed: {result.get('error', 'Unknown error')}")
                all_results[term] = result

        # Remove duplicates based on URI
        unique_concepts = []
        seen_uris = set()

        for concept in combined_concepts:
            concept_uri = concept.get('uri') or concept.get('identificatie')
            if concept_uri and concept_uri not in seen_uris:
                unique_concepts.append(concept)
                seen_uris.add(concept_uri)

        return {
            "success": len(unique_concepts) > 0,
            "data": {
                "combined_concepts": unique_concepts,
                "total_unique_concepts": len(unique_concepts),
                "search_terms_used": search_terms,
                "individual_results": all_results,
                "summary": {
                    "terms_searched": len(search_terms),
                    "successful_searches": len([r for r in all_results.values() if r.get('success')]),
                    "total_concepts_found": len(unique_concepts)
                }
            }
        }

    def get_renovation_related_concepts(self, renovation_type: str) -> Dict[str, Any]:
        """Get concepts related to a specific renovation type.

        Args:
            renovation_type: Type of renovation (e.g., 'dakkapel', 'uitbouw')

        Returns:
            Dict with renovation-related concepts
        """
        # Define search terms based on renovation type
        concept_search_terms = {
            'dakkapel': ['dakkapel', 'dakraam', 'omgevingsvergunning', 'bouwvergunning'],
            'uitbouw': ['uitbouw', 'aanbouw', 'omgevingsvergunning', 'bouwwerk'],
            'badkamer_verbouwen': ['verbouwing', 'sanitair', 'omgevingsvergunning'],
            'extra_verdieping': ['optopping', 'extra verdieping', 'bouwvergunning'],
            'garage_bouwen': ['bijgebouw', 'garage', 'bouwvergunning'],
            'keuken_verbouwen': ['verbouwing', 'omgevingsvergunning']
        }

        # Get search terms for this renovation type
        search_terms = concept_search_terms.get(renovation_type, [renovation_type, 'omgevingsvergunning'])

        # Add common terms
        search_terms.extend(['meldingsplicht', 'vergunningvrij'])

        print(f"  📖 Getting concepts for renovation type: {renovation_type}")

        return self.search_multiple_concepts(search_terms, renovation_type=renovation_type)

    def analyze_concept_quality(self, concept_result: Dict[str, Any],
                               renovation_type: str) -> Dict[str, Any]:
        """Analyze the quality and usefulness of concept results.

        Args:
            concept_result: Result from concept search
            renovation_type: Type of renovation

        Returns:
            Dict with quality analysis
        """
        if not concept_result.get('success'):
            return {
                "quality_score": 0,
                "issues": ["Concept search failed"],
                "recommendations": ["Check search terms", "Verify API connectivity"]
            }

        data = concept_result.get('data', {})
        concepts = data.get('concepts') or data.get('combined_concepts', [])

        analysis = {
            "quality_score": 0,
            "total_concepts": len(concepts),
            "useful_concepts": 0,
            "definition_quality": {},
            "issues": [],
            "recommendations": [],
            "concept_types": {}
        }

        if not concepts:
            analysis['issues'].append("No concepts found")
            analysis['recommendations'].append("Try different search terms")
            return analysis

        # Analyze each concept
        renovation_keywords = renovation_type.lower().split('_')

        for concept in concepts:
            concept_name = concept.get('naam', '').lower()
            concept_description = concept.get('omschrijving', '').lower()

            # Check usefulness
            if any(keyword in concept_name or keyword in concept_description for keyword in renovation_keywords):
                analysis['useful_concepts'] += 1

            # Analyze definition quality
            description_length = len(concept_description)
            if description_length > 100:
                quality = "good"
            elif description_length > 50:
                quality = "moderate"
            else:
                quality = "poor"

            analysis['definition_quality'][concept.get('naam', 'unknown')] = quality

            # Count concept types
            concept_type = concept.get('type', 'unknown')
            analysis['concept_types'][concept_type] = analysis['concept_types'].get(concept_type, 0) + 1

        # Calculate quality score (0-100)
        base_score = min(len(concepts) * 5, 30)  # 5 points per concept, max 30
        usefulness_score = (analysis['useful_concepts'] / len(concepts)) * 40  # 40 points for usefulness
        quality_scores = list(analysis['definition_quality'].values())
        quality_score = (quality_scores.count('good') * 3 + quality_scores.count('moderate') * 2 + quality_scores.count('poor') * 1) / len(quality_scores) * 10 if quality_scores else 0

        analysis['quality_score'] = int(base_score + usefulness_score + quality_score)

        # Generate recommendations
        if analysis['useful_concepts'] == 0:
            analysis['issues'].append("No concepts seem directly relevant")
            analysis['recommendations'].append("Try more specific search terms")

        if len(concepts) < 3:
            analysis['issues'].append("Few concepts found")
            analysis['recommendations'].append("Try broader search terms")

        good_definitions = quality_scores.count('good')
        if good_definitions / len(quality_scores) < 0.5:
            analysis['issues'].append("Many concepts have poor definitions")
            analysis['recommendations'].append("Look for alternative information sources")

        if analysis['quality_score'] >= 80:
            analysis['recommendations'].append("Excellent concept coverage - good for user education")
        elif analysis['quality_score'] >= 60:
            analysis['recommendations'].append("Good concept coverage - should help users")
        elif analysis['quality_score'] >= 40:
            analysis['recommendations'].append("Moderate concept coverage - may need supplementation")
        else:
            analysis['recommendations'].append("Poor concept coverage - consider alternative explanations")

        return analysis

    def create_concept_glossary(self, concept_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create a user-friendly glossary from concept results.

        Args:
            concept_result: Result from concept search

        Returns:
            Dict with formatted glossary
        """
        if not concept_result.get('success'):
            return {
                "success": False,
                "error": "Cannot create glossary from failed concept search"
            }

        data = concept_result.get('data', {})
        concepts = data.get('concepts') or data.get('combined_concepts', [])

        glossary = {
            "terms": {},
            "categories": {},
            "total_terms": len(concepts)
        }

        for concept in concepts:
            term_name = concept.get('naam', '').strip()
            term_description = concept.get('omschrijving', '').strip()
            term_category = concept.get('type', 'general')

            if term_name and term_description:
                glossary['terms'][term_name] = {
                    "definition": term_description,
                    "category": term_category,
                    "uri": concept.get('uri', ''),
                    "source": "DSO Catalog"
                }

                # Group by category
                if term_category not in glossary['categories']:
                    glossary['categories'][term_category] = []
                glossary['categories'][term_category].append(term_name)

        return {
            "success": True,
            "data": glossary
        }