"""Real-time console display utilities for showing test progress and API interactions."""

import time
from typing import Dict, Any, Optional
from datetime import datetime

class RealTimeDisplay:
    """Beautiful real-time console output with progress tracking."""

    def __init__(self, use_colors: bool = True):
        """Initialize console display.

        Args:
            use_colors: Whether to use colored output
        """
        self.use_colors = use_colors
        self.current_test = ""
        self.step_count = 0
        self.total_steps = 0
        self.start_time = None

        # Color codes
        self.colors = {
            'green': '\033[92m',
            'red': '\033[91m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'purple': '\033[95m',
            'cyan': '\033[96m',
            'white': '\033[97m',
            'bold': '\033[1m',
            'end': '\033[0m'
        } if use_colors else {k: '' for k in ['green', 'red', 'yellow', 'blue', 'purple', 'cyan', 'white', 'bold', 'end']}

    def print_header(self, title: str):
        """Print a beautiful header."""
        print(f"\n{self.colors['bold']}{self.colors['cyan']}{'='*80}{self.colors['end']}")
        print(f"{self.colors['bold']}{self.colors['cyan']}🚀 {title}{self.colors['end']}")
        print(f"{self.colors['bold']}{self.colors['cyan']}{'='*80}{self.colors['end']}")

    def print_section(self, title: str):
        """Print a section header."""
        print(f"\n{self.colors['bold']}{self.colors['blue']}📋 {title}{self.colors['end']}")
        print(f"{self.colors['blue']}{'-'*60}{self.colors['end']}")

    def start_test(self, test_name: str, house_address: str, renovation_type: str, total_steps: int):
        """Start a new test with progress tracking."""
        self.current_test = test_name
        self.step_count = 0
        self.total_steps = total_steps
        self.start_time = time.time()

        print(f"\n{self.colors['bold']}🏠 Testing: {self.colors['purple']}{house_address}{self.colors['end']}")
        print(f"{self.colors['bold']}🔧 Renovation: {self.colors['yellow']}{renovation_type}{self.colors['end']}")
        print(f"{self.colors['bold']}📊 Steps: {self.colors['white']}{total_steps} total{self.colors['end']}")

        # Initial progress bar
        self._show_progress_bar()

    def _show_progress_bar(self):
        """Show current progress bar."""
        if self.total_steps == 0:
            return

        progress_percentage = (self.step_count / self.total_steps) * 100
        progress_chars = int((self.step_count / self.total_steps) * 50)
        progress_bar = f"[{'='*progress_chars}{'-'*(50-progress_chars)}]"

        elapsed_time = time.time() - self.start_time if self.start_time else 0
        print(f"{self.colors['cyan']}Progress: {progress_bar} {self.step_count}/{self.total_steps} ({progress_percentage:.0f}%) - {elapsed_time:.1f}s{self.colors['end']}")

    def log_step(self, step_name: str, status: str, duration: float, details: str = ""):
        """Log individual step with real-time progress."""
        self.step_count += 1

        status_icons = {
            "success": f"{self.colors['green']}✅{self.colors['end']}",
            "failed": f"{self.colors['red']}❌{self.colors['end']}",
            "warning": f"{self.colors['yellow']}⚠️{self.colors['end']}",
            "info": f"{self.colors['blue']}ℹ️{self.colors['end']}",
            "running": f"{self.colors['yellow']}🔄{self.colors['end']}"
        }

        icon = status_icons.get(status.lower(), "•")

        # Format step output
        step_line = f"  {icon} {step_name:<25} {self.colors['white']}({duration:.2f}s){self.colors['end']}"
        if details:
            step_line += f" {self.colors['cyan']}{details}{self.colors['end']}"

        print(step_line)

        # Update progress bar
        self._show_progress_bar()

    def show_api_interaction(self, api_name: str, endpoint: str, method: str,
                           request_summary: str, response_summary: str,
                           success: bool, duration: float, status_code: int = None):
        """Show detailed API interaction in console."""

        status_color = self.colors['green'] if success else self.colors['red']
        status_text = f"{status_color}{'SUCCESS' if success else 'FAILED'}{self.colors['end']}"

        print(f"\n{self.colors['bold']}🔌 API INTERACTION{self.colors['end']}")
        print(f"   {self.colors['purple']}API:{self.colors['end']} {api_name}")
        print(f"   {self.colors['blue']}Method:{self.colors['end']} {method}")
        print(f"   {self.colors['blue']}Endpoint:{self.colors['end']} {endpoint}")
        print(f"   {self.colors['cyan']}Request:{self.colors['end']} {request_summary}")
        print(f"   {self.colors['cyan']}Response:{self.colors['end']} {response_summary}")
        if status_code:
            print(f"   {self.colors['white']}HTTP Status:{self.colors['end']} {status_code}")
        print(f"   {self.colors['white']}Status:{self.colors['end']} {status_text} {self.colors['white']}({duration:.2f}s){self.colors['end']}")

    def show_test_summary(self, test_results: Dict[str, Any]):
        """Show summary of test results."""
        integration_success = test_results.get('integration_success', False)
        steps = test_results.get('steps', {})

        print(f"\n{self.colors['bold']}📊 TEST SUMMARY{self.colors['end']}")

        # Overall result
        overall_status = f"{self.colors['green']}✅ PASSED{self.colors['end']}" if integration_success else f"{self.colors['red']}❌ FAILED{self.colors['end']}"
        print(f"   {self.colors['bold']}Overall Result:{self.colors['end']} {overall_status}")

        # Step breakdown
        successful_steps = sum(1 for step in steps.values() if step.get('success', False))
        total_steps = len(steps)
        print(f"   {self.colors['bold']}Steps Completed:{self.colors['end']} {successful_steps}/{total_steps}")

        # Duration
        total_duration = sum(step.get('duration', 0) for step in steps.values())
        print(f"   {self.colors['bold']}Total Duration:{self.colors['end']} {total_duration:.2f}s")

        # Issues
        analysis = test_results.get('analysis', {})
        issues = analysis.get('issues', [])
        if issues:
            print(f"   {self.colors['yellow']}Issues Found:{self.colors['end']} {len(issues)}")
            for issue in issues[:3]:  # Show first 3 issues
                print(f"     - {issue}")
            if len(issues) > 3:
                print(f"     ... and {len(issues) - 3} more")

    def show_house_completion(self, house_address: str, renovation_results: Dict[str, Any]):
        """Show completion status for a house."""
        total_renovations = len(renovation_results)
        successful_renovations = sum(1 for r in renovation_results.values()
                                   if r.get('integration_success', False))
        success_rate = (successful_renovations / total_renovations * 100) if total_renovations > 0 else 0

        print(f"\n{self.colors['bold']}{self.colors['green']}🏠 HOUSE COMPLETED: {house_address}{self.colors['end']}")
        print(f"   {self.colors['bold']}Success Rate:{self.colors['end']} {success_rate:.1f}% ({successful_renovations}/{total_renovations})")

        # Show renovation breakdown
        print(f"   {self.colors['bold']}Renovation Results:{self.colors['end']}")
        for renovation_type, results in renovation_results.items():
            success = results.get('integration_success', False)
            icon = f"{self.colors['green']}✅{self.colors['end']}" if success else f"{self.colors['red']}❌{self.colors['end']}"
            print(f"     {icon} {renovation_type}")

    def show_session_summary(self, all_results: Dict[str, Dict[str, Any]]):
        """Show final session summary."""
        print(f"\n{self.colors['bold']}{self.colors['cyan']}🎉 SESSION COMPLETED{self.colors['end']}")

        # Calculate overall stats
        total_tests = sum(len(house_results) for house_results in all_results.values())
        successful_tests = sum(
            sum(1 for test in house_results.values() if test.get('integration_success', False))
            for house_results in all_results.values()
        )
        overall_success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"   {self.colors['bold']}Total Tests:{self.colors['end']} {total_tests}")
        print(f"   {self.colors['bold']}Successful Tests:{self.colors['end']} {successful_tests}")
        print(f"   {self.colors['bold']}Overall Success Rate:{self.colors['end']} {overall_success_rate:.1f}%")

        # House breakdown
        print(f"\n   {self.colors['bold']}House Results:{self.colors['end']}")
        for house_id, house_results in all_results.items():
            house_tests = len(house_results)
            house_successful = sum(1 for test in house_results.values() if test.get('integration_success', False))
            house_rate = (house_successful / house_tests * 100) if house_tests > 0 else 0

            rate_color = self.colors['green'] if house_rate >= 70 else self.colors['yellow'] if house_rate >= 40 else self.colors['red']
            print(f"     {house_id}: {rate_color}{house_rate:.1f}%{self.colors['end']} ({house_successful}/{house_tests})")

    def show_file_locations(self, house_address: str = None):
        """Show where to find generated files."""
        print(f"\n{self.colors['bold']}📁 Generated Files:{self.colors['end']}")

        if house_address:
            house_id = house_address.replace(" ", "_").replace("/", "_")
            print(f"   {self.colors['cyan']}House-specific logs:{self.colors['end']} logs/by_house/house_{house_id}/")
            print(f"   {self.colors['cyan']}House dashboard:{self.colors['end']} outputs/by_house/house_{house_id}/dashboard.html")
            print(f"   {self.colors['cyan']}Quick access:{self.colors['end']} python tools/house_viewer.py \"{house_address}\"")
        else:
            print(f"   {self.colors['cyan']}All house logs:{self.colors['end']} logs/by_house/")
            print(f"   {self.colors['cyan']}Combined reports:{self.colors['end']} outputs/combined/")
            print(f"   {self.colors['cyan']}AI-readable logs:{self.colors['end']} logs/ai_readable/")

    def wait_with_countdown(self, seconds: float, message: str = "Waiting"):
        """Show a countdown while waiting."""
        if seconds < 0.1:
            return

        print(f"   {self.colors['yellow']}{message}...{self.colors['end']}", end="")

        for i in range(int(seconds * 10)):
            remaining = seconds - (i / 10)
            print(f"\r   {self.colors['yellow']}{message}... {remaining:.1f}s{self.colors['end']}", end="")
            time.sleep(0.1)

        print(f"\r   {self.colors['green']}{message}... Done!{self.colors['end']}")

    def error(self, message: str):
        """Display error message."""
        print(f"{self.colors['red']}❌ ERROR: {message}{self.colors['end']}")

    def warning(self, message: str):
        """Display warning message."""
        print(f"{self.colors['yellow']}⚠️  WARNING: {message}{self.colors['end']}")

    def info(self, message: str):
        """Display info message."""
        print(f"{self.colors['blue']}ℹ️  INFO: {message}{self.colors['end']}")

    def success(self, message: str):
        """Display success message."""
        print(f"{self.colors['green']}✅ SUCCESS: {message}{self.colors['end']}")