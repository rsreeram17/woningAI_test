"""Base API client with comprehensive logging and error handling."""

import time
import uuid
import requests
from typing import Dict, Any, Optional
from datetime import datetime

from ..utils.rate_limiter import RateLimiter
from ..utils.console_display import RealTimeDisplay

class BaseAPIClient:
    """Base client with comprehensive logging and debugging."""

    def __init__(self, config: Dict[str, Any], api_name: str, house_logger=None):
        """Initialize base API client.

        Args:
            config: API configuration dictionary
            api_name: Name of the API (e.g., 'BAG', 'DSO_Search')
            house_logger: Optional house-specific logger
        """
        self.config = config
        self.api_name = api_name
        self.base_url = config.get('base_url')
        self.timeout = config.get('timeout', 30)
        self.house_logger = house_logger

        # Initialize rate limiter
        rate_limit_config = config.get('rate_limit', {})
        self.rate_limiter = RateLimiter(rate_limit_config)

        # Console display
        self.console = RealTimeDisplay()

        # Request tracking
        self.request_count = 0
        self.total_duration = 0

    def _get_headers(self, include_crs: bool = False) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Dutch-Renovation-Tester/1.0'
        }

        # Add API key
        api_key = self.config.get('api_key')
        if api_key:
            # BAG uses X-Api-Key, DSO uses x-api-key
            if self.api_name == 'BAG':
                headers['X-Api-Key'] = api_key
            else:
                headers['x-api-key'] = api_key

        # Add coordinate system headers
        if include_crs:
            if self.api_name == 'BAG':
                # BAG API uses Accept-Crs for coordinate system
                headers['Accept-Crs'] = 'EPSG:28992'
            else:
                # DSO APIs use Content-Crs
                headers['Content-Crs'] = 'EPSG:28992'

        return headers

    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Remove sensitive data from headers for logging."""
        sanitized = headers.copy()
        for key in sanitized:
            if 'api-key' in key.lower() or 'authorization' in key.lower():
                sanitized[key] = "***REDACTED***"
        return sanitized

    def _make_request(self, method: str, endpoint: str, include_crs: bool = False,
                     renovation_type: str = None, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with comprehensive logging.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            include_crs: Whether to include coordinate system headers
            renovation_type: Current renovation type being tested
            **kwargs: Additional arguments for requests

        Returns:
            Dict containing response data and metadata
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())[:8]

        # Construct full URL
        if endpoint.startswith('http'):
            url = endpoint
        else:
            url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        # Prepare headers
        headers = self._get_headers(include_crs=include_crs)
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
        kwargs['headers'] = headers

        # Prepare request summary for logging - FULL DETAILS for transparency
        request_summary = {
            "request_id": request_id,
            "method": method,
            "url": url,
            "headers": self._sanitize_headers(headers),
            "payload": kwargs.get('json', kwargs.get('data')),  # Full payload for logs
            "params": kwargs.get('params'),  # Full params for logs
            "timeout": self.timeout,
            "timestamp": time.time()
        }

        # Create request summary string
        request_str = f"{method} {endpoint}"
        if kwargs.get('params'):
            params_str = str(kwargs['params'])[:100]
            request_str += f" (params: {params_str})"
        if kwargs.get('json'):
            payload_str = str(kwargs['json'])[:100]
            request_str += f" (payload: {payload_str})"

        # Console output - start
        print(f"🔄 {self.api_name}: {request_str} (ID: {request_id})")

        try:
            # Rate limiting
            self.rate_limiter.wait_if_needed()

            # Make actual request
            response = requests.request(method, url, timeout=self.timeout, **kwargs)
            duration = time.time() - start_time

            # Update stats
            self.request_count += 1
            self.total_duration += duration

            # Parse response
            try:
                content_type = response.headers.get('content-type', '').lower()
                # Try JSON parsing if content-type suggests JSON or if response looks like JSON
                if ('json' in content_type or
                    response.text.strip().startswith(('{', '['))):
                    response_data = response.json()
                else:
                    response_data = {"raw_response": response.text}
            except Exception as e:
                # If JSON parsing fails, but content looks like JSON, log the error
                if response.text.strip().startswith(('{', '[')):
                    print(f"Warning: JSON parsing failed for JSON-like content: {str(e)}")
                response_data = {"raw_response": response.text}

            success = response.status_code < 400

            # Prepare response summary
            response_summary = self._create_response_summary(response_data, response.status_code)

            # Log to house-specific logger if available
            if self.house_logger:
                self.house_logger.log_raw_api_call(
                    api_name=self.api_name,
                    endpoint=endpoint,
                    request=request_summary,
                    response={
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                        "data": response_data
                    },
                    success=success,
                    duration=duration,
                    renovation_type=renovation_type
                )

            # Console output - API interaction
            self.console.show_api_interaction(
                api_name=self.api_name,
                endpoint=endpoint,
                method=method,
                request_summary=request_str,
                response_summary=response_summary,
                success=success,
                duration=duration,
                status_code=response.status_code
            )

            return {
                "success": success,
                "status_code": response.status_code,
                "data": response_data,
                "duration": duration,
                "request_id": request_id,
                "headers": dict(response.headers)
            }

        except requests.exceptions.Timeout:
            duration = time.time() - start_time
            error_msg = f"Request timeout after {self.timeout}s"

            self._log_error(request_summary, error_msg, duration, request_id, renovation_type)
            return self._create_error_response(error_msg, duration, request_id, "timeout")

        except requests.exceptions.ConnectionError as e:
            duration = time.time() - start_time
            error_msg = f"Connection error: {str(e)}"

            self._log_error(request_summary, error_msg, duration, request_id, renovation_type)
            return self._create_error_response(error_msg, duration, request_id, "connection_error")

        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            error_msg = f"Request error: {str(e)}"

            self._log_error(request_summary, error_msg, duration, request_id, renovation_type)
            return self._create_error_response(error_msg, duration, request_id, "request_error")

        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Unexpected error: {str(e)}"

            self._log_error(request_summary, error_msg, duration, request_id, renovation_type)
            return self._create_error_response(error_msg, duration, request_id, "unexpected_error")

    def _create_response_summary(self, response_data: Any, status_code: int) -> str:
        """Create human-readable response summary."""
        if not response_data:
            return "Empty response"

        if isinstance(response_data, dict):
            # Count important elements
            elements = []

            if '_embedded' in response_data:
                embedded = response_data['_embedded']
                for key, value in embedded.items():
                    if isinstance(value, list):
                        elements.append(f"{len(value)} {key}")

            if 'error' in response_data:
                elements.append(f"Error: {response_data['error']}")

            if elements:
                return f"HTTP {status_code}, {', '.join(elements)}"
            else:
                return f"HTTP {status_code}, {len(response_data)} fields"
        else:
            return f"HTTP {status_code}, {type(response_data).__name__}"

    def _log_error(self, request_summary: Dict[str, Any], error_msg: str,
                  duration: float, request_id: str, renovation_type: str = None):
        """Log error details."""
        error_details = {
            "error": error_msg,
            "error_type": "api_error",
            "duration": duration,
            "request_id": request_id,
            "timestamp": datetime.now().isoformat()
        }

        # Log to house-specific logger if available
        if self.house_logger:
            self.house_logger.log_raw_api_call(
                api_name=self.api_name,
                endpoint=request_summary.get('url', 'unknown'),
                request=request_summary,
                response=error_details,
                success=False,
                duration=duration,
                renovation_type=renovation_type
            )

        # Console error output
        print(f"  ❌ {self.api_name} Error: {error_msg} ({duration:.2f}s)")

    def _create_error_response(self, error_msg: str, duration: float,
                              request_id: str, error_type: str) -> Dict[str, Any]:
        """Create standardized error response."""
        return {
            "success": False,
            "error": error_msg,
            "error_type": error_type,
            "duration": duration,
            "request_id": request_id,
            "timestamp": datetime.now().isoformat()
        }

    def get(self, endpoint: str, params: Dict[str, Any] = None,
            include_crs: bool = False, renovation_type: str = None) -> Dict[str, Any]:
        """Make GET request."""
        return self._make_request(
            method="GET",
            endpoint=endpoint,
            params=params,
            include_crs=include_crs,
            renovation_type=renovation_type
        )

    def post(self, endpoint: str, data: Dict[str, Any] = None,
             include_crs: bool = False, renovation_type: str = None) -> Dict[str, Any]:
        """Make POST request."""
        return self._make_request(
            method="POST",
            endpoint=endpoint,
            json=data,
            include_crs=include_crs,
            renovation_type=renovation_type
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            'api_name': self.api_name,
            'request_count': self.request_count,
            'total_duration': self.total_duration,
            'average_duration': self.total_duration / self.request_count if self.request_count > 0 else 0,
            'rate_limiter_stats': self.rate_limiter.get_stats()
        }