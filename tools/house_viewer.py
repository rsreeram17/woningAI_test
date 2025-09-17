#!/usr/bin/env python3
"""Interactive house data viewer for exploring test results by house."""

import os
import sys
import json
import glob
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.utils.console_display import RealTimeDisplay

class HouseDataViewer:
    """Easy access to house-specific data and results."""

    def __init__(self):
        """Initialize house data viewer."""
        self.houses_folder = "logs/by_house"
        self.outputs_folder = "outputs/by_house"
        self.console = RealTimeDisplay()
        self.available_houses = self._discover_houses()

    def _discover_houses(self):
        """Discover available house data."""
        houses = []
        if os.path.exists(self.houses_folder):
            for item in os.listdir(self.houses_folder):
                if item.startswith('house_') and os.path.isdir(os.path.join(self.houses_folder, item)):
                    houses.append(item)
        return sorted(houses)

    def _normalize_house_id(self, house_input):
        """Convert user input to house folder name."""
        # Remove 'house_' prefix if present
        if house_input.startswith('house_'):
            return house_input

        # Convert address format to folder name
        normalized = house_input.replace(' ', '_').replace('/', '_').replace('\\', '_')
        return f"house_{normalized}"

    def show_house_menu(self):
        """Interactive menu for house data access."""
        if not self.available_houses:
            self.console.error("No house data found. Run tests first with: python run_tests.py")
            return

        self.console.print_header("House Data Viewer")

        print("Available houses with test data:")
        for i, house_id in enumerate(self.available_houses, 1):
            house_name = house_id.replace('house_', '').replace('_', ' ')
            print(f"  {i}. {house_name}")

        try:
            choice = input(f"\nSelect house (1-{len(self.available_houses)}) or enter address: ")

            # Check if it's a number selection
            if choice.isdigit():
                house_index = int(choice) - 1
                if 0 <= house_index < len(self.available_houses):
                    selected_house = self.available_houses[house_index]
                    self.show_house_data(selected_house)
                else:
                    self.console.error("Invalid selection")
            else:
                # Treat as address input
                house_id = self._normalize_house_id(choice)
                if house_id in self.available_houses:
                    self.show_house_data(house_id)
                else:
                    self.console.error(f"No data found for house: {choice}")

        except (ValueError, KeyboardInterrupt):
            self.console.info("Cancelled")

    def show_house_data(self, house_id):
        """Show all data for specific house."""
        house_name = house_id.replace('house_', '').replace('_', ' ')
        house_folder = f"{self.houses_folder}/{house_id}"

        self.console.print_header(f"House Data: {house_name}")

        # Show summary first
        self._show_house_summary(house_folder, house_name)

        # Show available files
        self._show_available_files(house_folder, house_id)

        # Interactive options
        self._show_house_actions(house_folder, house_id, house_name)

    def _show_house_summary(self, house_folder, house_name):
        """Show house summary information."""
        summary_file = f"{house_folder}/formatted_outputs/summary_all_renovations.md"

        if os.path.exists(summary_file):
            self.console.print_section("Summary")
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract key metrics from summary
                lines = content.split('\n')
                for line in lines:
                    if 'Success Rate:' in line or 'Total Renovation Types:' in line or 'Successful Tests:' in line:
                        print(f"  {line.strip()}")

                print(f"\n  📄 Full summary: {summary_file}")

            except Exception as e:
                self.console.error(f"Could not read summary: {e}")
        else:
            self.console.warning("No summary file found for this house")

    def _show_available_files(self, house_folder, house_id):
        """Show available files and their contents."""
        self.console.print_section("Available Data")

        # Raw API calls
        raw_api_folder = f"{house_folder}/raw_api_calls"
        if os.path.exists(raw_api_folder):
            api_files = [f for f in os.listdir(raw_api_folder) if f.endswith('.json')]
            print(f"  📊 Raw API Data ({len(api_files)} files):")
            for file in sorted(api_files):
                file_path = f"{raw_api_folder}/{file}"
                file_size = os.path.getsize(file_path)
                print(f"    • {file} ({file_size} bytes)")

        # Formatted outputs
        formatted_folder = f"{house_folder}/formatted_outputs"
        if os.path.exists(formatted_folder):
            formatted_files = [f for f in os.listdir(formatted_folder) if f.endswith('.md')]
            print(f"\n  📄 Formatted Results ({len(formatted_files)} files):")
            for file in sorted(formatted_files):
                print(f"    • {file}")

        # Dashboard
        dashboard_path = f"outputs/by_house/{house_id}/dashboard.html"
        if os.path.exists(dashboard_path):
            print(f"\n  🌐 Dashboard: {dashboard_path}")

    def _show_house_actions(self, house_folder, house_id, house_name):
        """Show interactive actions for the house."""
        self.console.print_section("Actions")

        while True:
            print("\nWhat would you like to do?")
            print("  1. View specific renovation results")
            print("  2. View raw API calls")
            print("  3. View house summary")
            print("  4. Open dashboard (if available)")
            print("  5. Generate Claude-friendly report")
            print("  6. Show file locations")
            print("  7. Back to main menu")

            try:
                action = input("\nSelect action (1-7): ")

                if action == "1":
                    self._view_renovation_results(house_folder)
                elif action == "2":
                    self._view_raw_api_calls(house_folder)
                elif action == "3":
                    self._view_house_summary(house_folder)
                elif action == "4":
                    self._open_dashboard(house_id)
                elif action == "5":
                    self._generate_claude_report(house_id, house_name)
                elif action == "6":
                    self._show_file_locations(house_folder, house_id)
                elif action == "7":
                    break
                else:
                    self.console.warning("Invalid selection")

            except (KeyboardInterrupt, EOFError):
                break

    def _view_renovation_results(self, house_folder):
        """View results for specific renovation types."""
        formatted_folder = f"{house_folder}/formatted_outputs"
        if not os.path.exists(formatted_folder):
            self.console.error("No formatted results found")
            return

        result_files = [f for f in os.listdir(formatted_folder) if f.endswith('_test_results.md')]

        if not result_files:
            self.console.warning("No renovation test results found")
            return

        print("\nAvailable renovation results:")
        for i, file in enumerate(sorted(result_files), 1):
            renovation_type = file.replace('_test_results.md', '')
            print(f"  {i}. {renovation_type}")

        try:
            choice = input(f"Select renovation (1-{len(result_files)}): ")
            file_index = int(choice) - 1

            if 0 <= file_index < len(result_files):
                selected_file = sorted(result_files)[file_index]
                file_path = f"{formatted_folder}/{selected_file}"

                print(f"\n📄 Reading: {selected_file}")
                print("="*80)

                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Show first 2000 characters
                    if len(content) > 2000:
                        print(content[:2000])
                        print(f"\n... (truncated, full file: {file_path})")
                    else:
                        print(content)

            else:
                self.console.error("Invalid selection")

        except (ValueError, FileNotFoundError) as e:
            self.console.error(f"Error reading file: {e}")

    def _view_raw_api_calls(self, house_folder):
        """View raw API call data."""
        raw_folder = f"{house_folder}/raw_api_calls"
        if not os.path.exists(raw_folder):
            self.console.error("No raw API data found")
            return

        api_files = [f for f in os.listdir(raw_folder) if f.endswith('.json')]

        if not api_files:
            self.console.warning("No API call data found")
            return

        print("\nAvailable API call logs:")
        for i, file in enumerate(sorted(api_files), 1):
            api_name = file.replace('_requests.json', '')
            print(f"  {i}. {api_name}")

        try:
            choice = input(f"Select API log (1-{len(api_files)}): ")
            file_index = int(choice) - 1

            if 0 <= file_index < len(api_files):
                selected_file = sorted(api_files)[file_index]
                file_path = f"{raw_folder}/{selected_file}"

                print(f"\n📊 Reading: {selected_file}")
                print("="*80)

                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                print(f"Total API calls: {len(data)}")

                if data:
                    print("\nMost recent calls:")
                    for i, call in enumerate(data[-3:], 1):  # Show last 3 calls
                        timestamp = call.get('timestamp', 'unknown')
                        success = call.get('api_details', {}).get('success', False)
                        duration = call.get('api_details', {}).get('duration_seconds', 0)
                        status = "✅" if success else "❌"

                        print(f"  {i}. {timestamp} - {status} ({duration:.2f}s)")

                print(f"\nFull log file: {file_path}")

            else:
                self.console.error("Invalid selection")

        except (ValueError, FileNotFoundError, json.JSONDecodeError) as e:
            self.console.error(f"Error reading file: {e}")

    def _view_house_summary(self, house_folder):
        """View complete house summary."""
        summary_file = f"{house_folder}/formatted_outputs/summary_all_renovations.md"

        if os.path.exists(summary_file):
            print(f"\n📋 House Summary")
            print("="*80)

            with open(summary_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(content)

        else:
            self.console.error("Summary file not found")

    def _open_dashboard(self, house_id):
        """Open house dashboard if available."""
        dashboard_path = f"outputs/by_house/{house_id}/dashboard.html"

        if os.path.exists(dashboard_path):
            import webbrowser
            try:
                webbrowser.open(f"file://{os.path.abspath(dashboard_path)}")
                self.console.success(f"Opened dashboard in browser: {dashboard_path}")
            except Exception as e:
                self.console.error(f"Could not open dashboard: {e}")
                print(f"Manual path: {os.path.abspath(dashboard_path)}")
        else:
            self.console.warning("Dashboard not available for this house")

    def _generate_claude_report(self, house_id, house_name):
        """Generate Claude-friendly report for this house."""
        house_folder = f"{self.houses_folder}/{house_id}"
        timestamp = os.popen('date +%Y%m%d_%H%M%S').read().strip()

        output_file = f"logs/ai_readable/house_report_{house_id}_{timestamp}.md"
        Path("logs/ai_readable").mkdir(parents=True, exist_ok=True)

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# House Analysis Report - {house_name}\n\n")
                f.write(f"Generated: {timestamp}\n\n")

                # Include summary
                summary_file = f"{house_folder}/formatted_outputs/summary_all_renovations.md"
                if os.path.exists(summary_file):
                    f.write("## House Summary\n\n")
                    with open(summary_file, 'r', encoding='utf-8') as sf:
                        f.write(sf.read())
                    f.write("\n\n")

                # Include renovation results
                formatted_folder = f"{house_folder}/formatted_outputs"
                if os.path.exists(formatted_folder):
                    result_files = [f for f in os.listdir(formatted_folder) if f.endswith('_test_results.md')]

                    f.write("## Detailed Renovation Results\n\n")
                    for result_file in sorted(result_files):
                        f.write(f"### {result_file.replace('_test_results.md', '').title()}\n\n")
                        with open(f"{formatted_folder}/{result_file}", 'r', encoding='utf-8') as rf:
                            content = rf.read()
                            # Include first 1000 characters of each result
                            f.write(content[:1000])
                            if len(content) > 1000:
                                f.write("\n... (truncated)")
                            f.write("\n\n")

                f.write("## Questions You Can Ask Claude\n\n")
                f.write("- What renovation types work best for this house?\n")
                f.write("- What are the main issues with API integration for this address?\n")
                f.write("- How does this house compare to others in terms of data availability?\n")
                f.write("- What would you recommend for MVP development based on this house's results?\n")

            self.console.success(f"Generated Claude report: {output_file}")
            print(f"Share this file with Claude Desktop for detailed analysis")

        except Exception as e:
            self.console.error(f"Failed to generate report: {e}")

    def _show_file_locations(self, house_folder, house_id):
        """Show all file locations for this house."""
        house_name = house_id.replace('house_', '').replace('_', ' ')

        print(f"\n📁 File Locations for {house_name}")
        print("="*60)

        print(f"House folder: {house_folder}")
        print(f"Raw API logs: {house_folder}/raw_api_calls/")
        print(f"Formatted results: {house_folder}/formatted_outputs/")
        print(f"Dashboard: outputs/by_house/{house_id}/dashboard.html")

        print(f"\nQuick commands:")
        print(f"# View all files")
        print(f"find {house_folder} -type f")
        print(f"\n# View summary")
        print(f"cat '{house_folder}/formatted_outputs/summary_all_renovations.md'")
        print(f"\n# View raw API data")
        print(f"cat {house_folder}/raw_api_calls/*.json")

    def quick_house_lookup(self, house_identifier):
        """Quick lookup for specific house."""
        house_id = self._normalize_house_id(house_identifier)

        if house_id not in self.available_houses:
            self.console.error(f"No data found for house: {house_identifier}")
            print(f"Available houses: {[h.replace('house_', '').replace('_', ' ') for h in self.available_houses]}")
            return

        self.console.success(f"Found data for house: {house_identifier}")
        self.show_house_data(house_id)

def main():
    """Main function for house viewer."""
    viewer = HouseDataViewer()

    if len(sys.argv) > 1:
        # Direct house lookup: python house_viewer.py "1012JS 1"
        house_address = sys.argv[1]
        viewer.quick_house_lookup(house_address)
    else:
        # Interactive menu
        viewer.show_house_menu()

if __name__ == "__main__":
    main()