"""BAG API client for Dutch address and building registry."""

import re
from typing import Dict, Any, List, Optional, Tuple
from .base_client import BaseAPIClient

class BAGAPIClient(BaseAPIClient):
    """Client for Dutch BAG API - address and building registry."""

    def __init__(self, config: Dict[str, Any], house_logger=None):
        """Initialize BAG API client."""
        super().__init__(config, "BAG", house_logger)

    def _parse_address(self, address: str) -> Dict[str, Any]:
        """Parse Dutch address string into components.

        Args:
            address: Address string like "1012JS 1" or "2631CR 15C"

        Returns:
            Dict with postcode, huisnummer, huisletter, etc.
        """
        # Remove extra whitespace
        address = address.strip()

        # Pattern for Dutch address: postcode + space + number + optional letter
        pattern = r'^(\d{4}\s?[A-Z]{2})\s+(\d+)([A-Z]?).*$'
        match = re.match(pattern, address.upper())

        if not match:
            raise ValueError(f"Invalid Dutch address format: {address}")

        postcode = match.group(1).replace(' ', '')  # Remove space from postcode
        huisnummer = int(match.group(2))
        huisletter = match.group(3) if match.group(3) else None

        return {
            'postcode': postcode,
            'huisnummer': huisnummer,
            'huisletter': huisletter,
            'original_address': address
        }

    def search_address(self, address, renovation_type: str = None) -> Dict[str, Any]:
        """Search for address and return basic info.

        Args:
            address: Dutch address string OR dict with address components
            renovation_type: Current renovation type being tested

        Returns:
            Dict with address search results
        """
        # Handle both string addresses and config dict addresses
        if isinstance(address, dict):
            # Address from config with components
            params = {
                'postcode': address['postcode'],
                'huisnummer': address['huisnummer']
            }
            if address.get('huisletter'):
                params['huisletter'] = address['huisletter']
            if address.get('huisnummertoevoeging'):
                params['huisnummertoevoeging'] = address['huisnummertoevoeging']
        else:
            # String address - parse it
            try:
                parsed = self._parse_address(address)
            except ValueError as e:
                return {
                    "success": False,
                    "error": str(e),
                    "error_type": "address_parsing"
                }

            # Prepare search parameters
            params = {
                'postcode': parsed['postcode'],
                'huisnummer': parsed['huisnummer']
            }

            if parsed['huisletter']:
                params['huisletter'] = parsed['huisletter']

        # Make API request
        result = self.get(
            endpoint="/adressen",
            params=params,
            renovation_type=renovation_type
        )

        if not result['success']:
            return result

        # Process response
        response_data = result['data']

        # Debug: Log the actual response structure (removed for production)

        # Handle different response structures from BAG API
        addresses = None

        # Try the documented _embedded.adressen structure first
        if isinstance(response_data, dict) and '_embedded' in response_data and 'adressen' in response_data['_embedded']:
            addresses = response_data['_embedded']['adressen']
        # Try direct adressen array
        elif isinstance(response_data, dict) and 'adressen' in response_data:
            addresses = response_data['adressen']
        # Try if response is direct array
        elif isinstance(response_data, list):
            addresses = response_data
        # Try if response is a single address object
        elif isinstance(response_data, dict) and 'openbareRuimteNaam' in response_data:
            addresses = [response_data]

        if not addresses:
            return {
                "success": False,
                "error": "No addresses found in response",
                "error_type": "not_found",
                "request_details": params,
                "debug_info": {
                    "response_type": type(response_data).__name__,
                    "response_keys": list(response_data.keys()) if isinstance(response_data, dict) else "Not a dict",
                    "response_structure": str(response_data)[:500] + "..." if len(str(response_data)) > 500 else str(response_data)
                }
            }

        # Return first address (most relevant)
        address_data = addresses[0]

        return {
            "success": True,
            "data": {
                "address_found": address_data,
                "total_matches": len(addresses),
                "search_params": params,
                "response_metadata": {
                    "duration": result['duration'],
                    "request_id": result['request_id']
                }
            }
        }

    def get_address_extended(self, address, renovation_type: str = None) -> Dict[str, Any]:
        """Get extended address info including building details.

        Args:
            address: Dutch address string OR dict with address components
            renovation_type: Current renovation type being tested

        Returns:
            Dict with extended address and building information
        """
        # Handle both string addresses and config dict addresses
        if isinstance(address, dict):
            # Address from config with components
            params = {
                'postcode': address['postcode'],
                'huisnummer': address['huisnummer']
            }
            if address.get('huisletter'):
                params['huisletter'] = address['huisletter']
            if address.get('huisnummertoevoeging'):
                params['huisnummertoevoeging'] = address['huisnummertoevoeging']
        else:
            # String address - parse it
            try:
                parsed = self._parse_address(address)
            except ValueError as e:
                return {
                    "success": False,
                    "error": str(e),
                    "error_type": "address_parsing"
                }

            # Prepare search parameters
            params = {
                'postcode': parsed['postcode'],
                'huisnummer': parsed['huisnummer']
            }

            if parsed['huisletter']:
                params['huisletter'] = parsed['huisletter']

        # Make API request to extended endpoint with CRS headers
        result = self.get(
            endpoint="/adressenuitgebreid",
            params=params,
            renovation_type=renovation_type,
            include_crs=True  # Extended endpoint might require coordinate system headers
        )

        if not result['success']:
            return result

        # Process response
        response_data = result['data']

        # Debug: Log the actual response structure (removed for production)

        # Handle different response structures from BAG API
        addresses = None

        # Try the documented _embedded.adressen structure first
        if isinstance(response_data, dict) and '_embedded' in response_data and 'adressen' in response_data['_embedded']:
            addresses = response_data['_embedded']['adressen']
        # Try direct adressen array
        elif isinstance(response_data, dict) and 'adressen' in response_data:
            addresses = response_data['adressen']
        # Try if response is direct array
        elif isinstance(response_data, list):
            addresses = response_data
        # Try if response is a single address object
        elif isinstance(response_data, dict) and 'openbareRuimteNaam' in response_data:
            addresses = [response_data]

        if not addresses:
            return {
                "success": False,
                "error": "No extended address information found in response",
                "error_type": "not_found",
                "request_details": params,
                "debug_info": {
                    "response_type": type(response_data).__name__,
                    "response_keys": list(response_data.keys()) if isinstance(response_data, dict) else "Not a dict",
                    "response_structure": str(response_data)[:500] + "..." if len(str(response_data)) > 500 else str(response_data)
                }
            }

        # Get the first address
        address_data = addresses[0]

        # Extract coordinates and building information
        processed_data = self._process_extended_address(address_data)

        return {
            "success": True,
            "data": {
                "address": processed_data['address_info'],
                "building": processed_data['building_info'],
                "coordinates": processed_data['coordinates'],
                "raw_data": address_data,
                "response_metadata": {
                    "duration": result['duration'],
                    "request_id": result['request_id']
                }
            }
        }

    def _process_extended_address(self, address_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process extended address data and extract key information."""

        # Debug: Log the address data structure (removed for production)

        # Extract basic address info
        address_info = {
            "formatted_address": address_data.get('weergavenaam', ''),
            "postcode": address_data.get('postcode', ''),
            "huisnummer": address_data.get('huisnummer', ''),
            "huisletter": address_data.get('huisletter', ''),
            "straatnaam": address_data.get('korteNaam', ''),
            "plaatsnaam": address_data.get('woonplaatsNaam', ''),
            "gemeente": address_data.get('gemeenteNaam', '')
        }

        # Extract coordinates (RD/EPSG:28992)
        coordinates = None
        # Check for coordinates in the extended response structure
        if 'adresseerbaarObjectGeometrie' in address_data:
            geom = address_data['adresseerbaarObjectGeometrie']
            if 'punt' in geom and 'coordinates' in geom['punt']:
                coords = geom['punt']['coordinates']
                if len(coords) >= 2:
                    # Take X, Y coordinates (ignore Z if present)
                    coordinates = [coords[0], coords[1]]

        # Extract building information from extended response structure
        building_info = {
            "object_type": address_data.get('typeAdresseerbaarObject', ''),
            "status": address_data.get('adresseerbaarObjectStatus', ''),
            "oppervlakte": address_data.get('oppervlakte', None),
            "gebruiksdoel": address_data.get('gebruiksdoelen', []),
            "bouwjaar": address_data.get('oorspronkelijkBouwjaar', [None])[0] if address_data.get('oorspronkelijkBouwjaar') else None,
            "pand_status": address_data.get('pandStatussen', [None])[0] if address_data.get('pandStatussen') else None,
            "pand_id": address_data.get('pandIdentificaties', [None])[0] if address_data.get('pandIdentificaties') else None
        }

        return {
            "address_info": address_info,
            "building_info": building_info,
            "coordinates": coordinates
        }

    def get_building_details(self, pand_id: str, renovation_type: str = None) -> Dict[str, Any]:
        """Get detailed building information by building ID.

        Args:
            pand_id: Building identification number
            renovation_type: Current renovation type being tested

        Returns:
            Dict with detailed building information
        """
        result = self.get(
            endpoint=f"/panden/{pand_id}",
            renovation_type=renovation_type
        )

        if not result['success']:
            return result

        building_data = result['data']

        return {
            "success": True,
            "data": {
                "building_details": building_data,
                "response_metadata": {
                    "duration": result['duration'],
                    "request_id": result['request_id']
                }
            }
        }

    def extract_coordinates(self, address_result: Dict[str, Any]) -> Optional[List[float]]:
        """Extract RD coordinates from address result for DSO API use.

        Args:
            address_result: Result from get_address_extended

        Returns:
            List of [X, Y] coordinates in RD format or None
        """
        if not address_result.get('success'):
            return None

        data = address_result.get('data', {})
        coordinates = data.get('coordinates')

        if coordinates and isinstance(coordinates, list) and len(coordinates) >= 2:
            # Return as [X, Y] format required by DSO APIs
            return [float(coordinates[0]), float(coordinates[1])]

        return None

    def validate_address_for_testing(self, address) -> Dict[str, Any]:
        """Validate address and return comprehensive information for testing.

        Args:
            address: Dutch address string OR dict with address components

        Returns:
            Dict with validation results and complete address information
        """
        # Format address for display
        if isinstance(address, dict):
            display_address = f"{address['postcode']} {address['huisnummer']}{address.get('huisletter', '')}{address.get('huisnummertoevoeging', '')}"
        else:
            display_address = address

        print(f"🔍 Validating address: {display_address}")

        # Step 1: Basic address search
        basic_result = self.search_address(address)

        if not basic_result['success']:
            return {
                "success": False,
                "error": basic_result['error'],
                "validation_step": "basic_search",
                "address": display_address
            }

        # Step 2: Extended address information
        extended_result = self.get_address_extended(address)

        if not extended_result['success']:
            return {
                "success": False,
                "error": extended_result.get('error', 'Extended search failed'),
                "validation_step": "extended_search",
                "address": display_address,
                "basic_result": basic_result,
                "extended_result": extended_result
            }

        # Step 3: Extract and validate coordinates
        coordinates = self.extract_coordinates(extended_result)

        if not coordinates:
            return {
                "success": False,
                "error": "Could not extract valid coordinates",
                "validation_step": "coordinate_extraction",
                "address": display_address,
                "extended_result": extended_result
            }

        # Successful validation
        return {
            "success": True,
            "address": display_address,
            "address_info": extended_result['data']['address'],
            "building_info": extended_result['data']['building'],
            "coordinates": coordinates,
            "validation_summary": {
                "basic_search": "✅ Success",
                "extended_search": "✅ Success",
                "coordinate_extraction": "✅ Success",
                "ready_for_dso_testing": True
            }
        }