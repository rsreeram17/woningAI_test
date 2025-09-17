"""House-specific logging system for organizing test results by individual houses."""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

class HouseSpecificLogger:
    """Organizes all logs and outputs by individual house."""

    def __init__(self, house_identifier: str, test_session_id: str = None):
        """Initialize house-specific logger.

        Args:
            house_identifier: Address like "1012JS 1" or "2631CR 15C"
            test_session_id: Optional session ID for grouping tests
        """
        self.house_id = self._normalize_house_id(house_identifier)
        self.house_identifier = house_identifier
        self.session_id = test_session_id or str(uuid.uuid4())[:8]

        self.house_folder = f"logs/by_house/house_{self.house_id}"
        self.output_folder = f"outputs/by_house/house_{self.house_id}"

        # Create house-specific directories
        self._create_house_directories()

        # Initialize log files
        self.current_test_logs = {}

    def _normalize_house_id(self, identifier: str) -> str:
        """Convert '1012JS 1' to '1012JS_1' for folder names."""
        return identifier.replace(" ", "_").replace("/", "_").replace("\\", "_")

    def _create_house_directories(self):
        """Create all necessary directories for this house."""
        directories = [
            f"{self.house_folder}/raw_api_calls",
            f"{self.house_folder}/formatted_outputs",
            f"{self.house_folder}/analysis",
            f"{self.output_folder}"
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def log_raw_api_call(self, api_name: str, endpoint: str, request: Dict[str, Any],
                        response: Dict[str, Any], success: bool, duration: float,
                        renovation_type: str = None):
        """Log raw API call data for this specific house."""

        timestamp = datetime.now().isoformat()

        api_entry = {
            "timestamp": timestamp,
            "session_id": self.session_id,
            "house_id": self.house_id,
            "house_address": self.house_identifier,
            "renovation_type": renovation_type,
            "api_details": {
                "api_name": api_name,
                "endpoint": endpoint,
                "success": success,
                "duration_seconds": round(duration, 3),
                "http_status": response.get("status_code") if isinstance(response, dict) else None
            },
            "request_data": self._sanitize_request(request),
            "response_data": self._truncate_response(response),
            "response_size_kb": round(len(str(response)) / 1024, 2) if response else 0
        }

        # Save to house-specific API log file
        raw_log_file = f"{self.house_folder}/raw_api_calls/{api_name}_requests.json"
        self._append_to_json_log(raw_log_file, api_entry)

        # Create human-readable version
        self._create_readable_api_log(api_name, api_entry)

        print(f"  📝 Logged {api_name} call: {endpoint} ({'✅' if success else '❌'}) ({duration:.2f}s)")

    def _sanitize_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive data from request logging."""
        if not request:
            return {}

        sanitized = request.copy()

        # Remove or mask sensitive headers
        if 'headers' in sanitized:
            headers = sanitized['headers'].copy()
            for key in headers:
                if 'api-key' in key.lower() or 'authorization' in key.lower():
                    headers[key] = "***REDACTED***"
            sanitized['headers'] = headers

        return sanitized

    def _truncate_response(self, response: Any, max_size: int = 5000) -> Any:
        """Truncate large responses for logging."""
        if not response:
            return response

        response_str = str(response)
        if len(response_str) > max_size:
            if isinstance(response, dict):
                truncated = {"_truncated": True, "_original_size": len(response_str)}

                # Keep important fields
                important_fields = ['success', 'error', 'status_code', '_embedded', '_links', 'message']
                for field in important_fields:
                    if field in response:
                        truncated[field] = response[field]

                return truncated
            else:
                return {"_truncated": True, "_content": response_str[:max_size] + "..."}

        return response

    def _append_to_json_log(self, file_path: str, entry: Dict[str, Any]):
        """Append entry to JSON log file."""
        # Read existing entries
        entries = []
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    entries = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                entries = []

        # Add new entry
        entries.append(entry)

        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)

    def _create_readable_api_log(self, api_name: str, entry: Dict[str, Any]):
        """Create human-readable API log entry."""

        readable_file = f"{self.house_folder}/formatted_outputs/api_calls_readable.md"

        status_emoji = "✅" if entry['api_details']['success'] else "❌"
        timestamp = entry['timestamp']
        endpoint = entry['api_details']['endpoint']
        duration = entry['api_details']['duration_seconds']

        readable_entry = f"""
## {api_name} API Call - {datetime.fromisoformat(timestamp).strftime('%H:%M:%S')}

**House:** {entry['house_address']} | **Session:** {entry['session_id']}
**Endpoint:** `{endpoint}`
**Status:** {status_emoji} {"SUCCESS" if entry['api_details']['success'] else "FAILED"}
**Duration:** {duration}s

### Request Summary:
```json
{json.dumps(entry['request_data'], indent=2)}
```

### Response Summary:
- **Size:** {entry['response_size_kb']} KB
- **HTTP Status:** {entry['api_details'].get('http_status', 'N/A')}

### Key Response Data:
```json
{json.dumps(self._extract_key_response_data(entry['response_data']), indent=2)}
```

---
"""

        # Append to readable log
        with open(readable_file, 'a', encoding='utf-8') as f:
            f.write(readable_entry)

    def _extract_key_response_data(self, response: Any) -> Dict[str, Any]:
        """Extract key information from response for summary."""
        if not isinstance(response, dict):
            return {"response_type": type(response).__name__, "value": str(response)[:200]}

        key_data = {}

        # Common important fields
        important_fields = [
            'success', 'error', 'message', 'status_code',
            '_embedded', '_links', 'page',
            'activiteiten', 'adressen', 'panden'
        ]

        for field in important_fields:
            if field in response:
                value = response[field]
                if isinstance(value, (list, dict)) and len(str(value)) > 500:
                    key_data[field] = f"<{type(value).__name__} with {len(value) if hasattr(value, '__len__') else 'complex'} items>"
                else:
                    key_data[field] = value

        return key_data

    def save_renovation_test_results(self, renovation_type: str, results: Dict[str, Any]):
        """Save formatted test results for specific renovation type."""

        formatted_file = f"{self.house_folder}/formatted_outputs/{renovation_type}_test_results.md"
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

        # Calculate success metrics
        integration_success = results.get('integration_success', False)
        steps = results.get('steps', {})
        total_steps = len(steps)
        successful_steps = sum(1 for step in steps.values() if step.get('success', False))

        formatted_content = f"""# {renovation_type.title()} Test Results - House {self.house_id}

## Test Summary
- **House:** {self.house_identifier}
- **House ID:** {self.house_id}
- **Renovation Type:** {renovation_type}
- **Test Date:** {timestamp}
- **Session ID:** {self.session_id}
- **Overall Success:** {'✅ PASSED' if integration_success else '❌ FAILED'}
- **Steps Completed:** {successful_steps}/{total_steps}

## Step-by-Step Results

"""

        # Add results for each step
        for step_name, step_result in steps.items():
            success = step_result.get('success', False)
            duration = step_result.get('duration', 0)
            status_icon = "✅" if success else "❌"

            formatted_content += f"""### {step_name.title()}
{status_icon} **Status:** {'SUCCESS' if success else 'FAILED'}
⏱️ **Duration:** {duration:.2f}s

"""

            # Add step details
            if 'data' in step_result:
                formatted_content += f"""**Response Data:**
```json
{json.dumps(step_result['data'], indent=2)[:1000]}{'...' if len(str(step_result['data'])) > 1000 else ''}
```

"""

            if 'error' in step_result:
                formatted_content += f"""**Error Details:**
```
{step_result['error']}
```

"""

        # Add analysis section
        analysis = results.get('analysis', {})
        if analysis:
            formatted_content += f"""## Business Analysis

### Data Completeness
```json
{json.dumps(analysis.get('data_completeness', {}), indent=2)}
```

### Regulatory Coverage
```json
{json.dumps(analysis.get('regulatory_coverage', {}), indent=2)}
```

### Issues Found
"""
            issues = analysis.get('issues', [])
            for issue in issues:
                formatted_content += f"- {issue}\n"

            recommendations = analysis.get('recommendations', [])
            if recommendations:
                formatted_content += f"""

### Recommendations
"""
                for rec in recommendations:
                    formatted_content += f"- {rec}\n"

        # Add navigation section
        formatted_content += f"""

## Quick Access Commands
```bash
# View raw API calls for this house
cat logs/by_house/house_{self.house_id}/raw_api_calls/*.json

# View all renovation results for this house
ls logs/by_house/house_{self.house_id}/formatted_outputs/

# Open house dashboard
open outputs/by_house/house_{self.house_id}/dashboard.html

# Quick house lookup
python tools/house_viewer.py "{self.house_identifier}"
```

## Files Generated
- Raw API calls: `logs/by_house/house_{self.house_id}/raw_api_calls/`
- Formatted outputs: `logs/by_house/house_{self.house_id}/formatted_outputs/`
- Analysis data: `logs/by_house/house_{self.house_id}/analysis/`
"""

        with open(formatted_file, 'w', encoding='utf-8') as f:
            f.write(formatted_content)

        print(f"  📄 Saved formatted results: {formatted_file}")

    def generate_house_summary(self, all_renovation_results: Dict[str, Any]):
        """Generate complete summary for this house."""

        summary_file = f"{self.house_folder}/formatted_outputs/summary_all_renovations.md"
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

        # Calculate house-level metrics
        total_tests = len(all_renovation_results)
        successful_tests = sum(1 for r in all_renovation_results.values()
                              if r.get('integration_success', False))
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0

        # Calculate total API calls and duration
        total_api_calls = 0
        total_duration = 0
        all_issues = []

        for results in all_renovation_results.values():
            steps = results.get('steps', {})
            total_api_calls += len(steps)
            total_duration += sum(step.get('duration', 0) for step in steps.values())

            analysis = results.get('analysis', {})
            all_issues.extend(analysis.get('issues', []))

        summary_content = f"""# Complete Test Summary - House {self.house_id}

## House Information
- **Address:** {self.house_identifier}
- **House ID:** {self.house_id}
- **Test Session:** {self.session_id}
- **Test Date:** {timestamp}

## Overall Performance
- **Total Renovation Types Tested:** {total_tests}
- **Successful Tests:** {successful_tests}/{total_tests}
- **Success Rate:** {success_rate:.1f}%
- **Total API Calls Made:** {total_api_calls}
- **Total Test Duration:** {total_duration:.1f}s
- **Average Test Duration:** {(total_duration/total_tests):.1f}s per renovation

## Renovation Type Results
| Renovation Type | Success | Duration | API Calls | Issues |
|----------------|---------|----------|-----------|--------|"""

        for renovation_type, results in all_renovation_results.items():
            success = "✅" if results.get('integration_success', False) else "❌"
            steps = results.get('steps', {})
            duration = sum(step.get('duration', 0) for step in steps.values())
            api_calls = len(steps)
            issues_count = len(results.get('analysis', {}).get('issues', []))

            summary_content += f"\n| {renovation_type} | {success} | {duration:.1f}s | {api_calls} | {issues_count} |"

        # Best and worst performing renovations
        if all_renovation_results:
            best_renovations = [k for k, v in all_renovation_results.items()
                              if v.get('integration_success', False)]
            failed_renovations = [k for k, v in all_renovation_results.items()
                                if not v.get('integration_success', False)]

            summary_content += f"""

## Performance Analysis

### ✅ Successful Renovations ({len(best_renovations)}/{total_tests})
"""
            for renovation in best_renovations:
                summary_content += f"- {renovation}\n"

            if failed_renovations:
                summary_content += f"""
### ❌ Failed Renovations ({len(failed_renovations)}/{total_tests})
"""
                for renovation in failed_renovations:
                    summary_content += f"- {renovation}\n"

        # Common issues
        if all_issues:
            unique_issues = list(set(all_issues))
            summary_content += f"""

## Common Issues Found
"""
            for issue in unique_issues[:10]:  # Top 10 issues
                count = all_issues.count(issue)
                summary_content += f"- {issue} (occurred {count} times)\n"

        # Navigation and file access
        summary_content += f"""

## Quick Navigation
- 📁 **Raw API Data:** `logs/by_house/house_{self.house_id}/raw_api_calls/`
- 📄 **Formatted Results:** `logs/by_house/house_{self.house_id}/formatted_outputs/`
- 📊 **Analysis Data:** `logs/by_house/house_{self.house_id}/analysis/`
- 🌐 **Dashboard:** `outputs/by_house/house_{self.house_id}/dashboard.html`

## Quick Commands
```bash
# View this house's data
python tools/house_viewer.py "{self.house_identifier}"

# View raw API calls
find logs/by_house/house_{self.house_id}/raw_api_calls/ -name "*.json" -exec cat {{}} \;

# View all test results
ls -la logs/by_house/house_{self.house_id}/formatted_outputs/

# Generate Claude-friendly report for this house
python analyze_logs.py --house "{self.house_identifier}" --claude-report
```

## Files Created in This Session
- Raw API logs: {total_api_calls} API calls logged
- Formatted results: {total_tests} renovation test reports
- This summary: `{summary_file}`

---
*Generated by Integrated Renovation Tester on {timestamp}*
"""

        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_content)

        print(f"  📋 Generated house summary: {summary_file}")

        return summary_file

    def get_house_stats(self) -> Dict[str, Any]:
        """Get statistics for this house."""
        stats = {
            'house_id': self.house_id,
            'house_address': self.house_identifier,
            'session_id': self.session_id,
            'folders': {
                'logs': self.house_folder,
                'outputs': self.output_folder
            }
        }

        # Count files
        raw_api_folder = f"{self.house_folder}/raw_api_calls"
        if os.path.exists(raw_api_folder):
            api_files = [f for f in os.listdir(raw_api_folder) if f.endswith('.json')]
            stats['api_log_files'] = len(api_files)

        formatted_folder = f"{self.house_folder}/formatted_outputs"
        if os.path.exists(formatted_folder):
            formatted_files = [f for f in os.listdir(formatted_folder) if f.endswith('.md')]
            stats['formatted_files'] = len(formatted_files)

        return stats