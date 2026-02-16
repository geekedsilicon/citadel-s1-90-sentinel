#!/usr/bin/env python3
# ==============================================================================
# VAELIX | PROJECT CITADEL — MISSION DEBRIEF AUTOMATION
# ==============================================================================
# FILE:     analyze_telemetry.py
# PURPOSE:  Parse Cocotb results.xml and extract failure timestamps from FST
# VERSION:  1.0.0
# USAGE:    python analyze_telemetry.py [--results-xml PATH] [--fst-file PATH]
#           [--output PATH]
# ==============================================================================
# SPDX-License-Identifier: Apache-2.0

import argparse
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import sys


class TelemetryAnalyzer:
    """Analyzes Cocotb test results and extracts failure information."""

    def __init__(self, results_xml_path: Path, fst_file_path: Path):
        self.results_xml_path = results_xml_path
        self.fst_file_path = fst_file_path
        self.test_results: List[Dict] = []
        self.failure_count = 0
        self.pass_count = 0
        self.total_count = 0

    def parse_results_xml(self) -> None:
        """Parse the Cocotb results.xml file."""
        if not self.results_xml_path.exists():
            raise FileNotFoundError(
                f"Results file not found: {self.results_xml_path}"
            )

        try:
            tree = ET.parse(self.results_xml_path)
            root = tree.getroot()

            # Cocotb results.xml follows JUnit XML format
            # <testsuites> or <testsuite> as root
            testsuites = root.findall(".//testsuite")
            if not testsuites:
                # Check if root is already a testsuite
                if root.tag == "testsuite":
                    testsuites = [root]
                else:
                    testsuites = []

            for testsuite in testsuites:
                for testcase in testsuite.findall("testcase"):
                    test_info = self._parse_testcase(testcase)
                    self.test_results.append(test_info)
                    self.total_count += 1

                    if test_info["status"] == "FAILED":
                        self.failure_count += 1
                    elif test_info["status"] == "PASSED":
                        self.pass_count += 1

        except ET.ParseError as e:
            raise ValueError(f"Failed to parse XML file: {e}")

    def _parse_testcase(self, testcase: ET.Element) -> Dict:
        """Parse a single testcase element."""
        name = testcase.get("name", "Unknown Test")
        classname = testcase.get("classname", "")
        time = testcase.get("time", "0")

        # Check for failure or error elements
        failure = testcase.find("failure")
        error = testcase.find("error")

        status = "PASSED"
        message = ""
        failure_type = ""
        traceback = ""

        if failure is not None:
            status = "FAILED"
            message = failure.get("message", "")
            failure_type = failure.get("type", "AssertionError")
            traceback = failure.text or ""
        elif error is not None:
            status = "ERROR"
            message = error.get("message", "")
            failure_type = error.get("type", "Error")
            traceback = error.text or ""

        return {
            "name": name,
            "classname": classname,
            "time": float(time) if time else 0.0,
            "status": status,
            "message": message,
            "failure_type": failure_type,
            "traceback": traceback,
        }

    def extract_failure_timestamps(self) -> List[Tuple[str, Optional[float]]]:
        """
        Extract failure timestamps from FST file.
        Returns list of (test_name, timestamp) tuples.
        """
        timestamps = []

        # For now, we'll extract simulation time from the traceback if available
        # FST parsing requires vcdvcd or similar library which may not be available
        # We'll use a heuristic approach based on the test failure information

        for test in self.test_results:
            if test["status"] == "FAILED":
                timestamp = self._extract_timestamp_from_traceback(
                    test["traceback"]
                )
                timestamps.append((test["name"], timestamp))

        return timestamps

    def _extract_timestamp_from_traceback(
        self, traceback: str
    ) -> Optional[float]:
        """
        Extract simulation timestamp from traceback.
        Cocotb often includes simulation time in error messages.
        """
        if not traceback:
            return None

        # Look for common patterns in Cocotb error messages
        # Example: "at 1000.0 ns" or "Simulation time: 1000"
        import re

        # Pattern 1: "at XXX ns"
        pattern1 = r"at\s+(\d+\.?\d*)\s*ns"
        # Pattern 2: "time: XXX"
        pattern2 = r"time:\s*(\d+\.?\d*)"
        # Pattern 3: "XXX ns"
        pattern3 = r"(\d+\.?\d*)\s*ns"

        for pattern in [pattern1, pattern2, pattern3]:
            match = re.search(pattern, traceback, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except (ValueError, IndexError):
                    continue

        return None

    def generate_markdown_report(self) -> str:
        """Generate a Markdown-formatted summary report."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        report_lines = [
            "# 🔍 MISSION DEBRIEF — SENTINEL INTERROGATION REPORT",
            "",
            f"**Generated:** {timestamp}",
            f"**Results File:** `{self.results_xml_path.name}`",
            "",
            "---",
            "",
            "## 📊 EXECUTIVE SUMMARY",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| **Total Tests** | {self.total_count} |",
            f"| **✅ Passed** | {self.pass_count} |",
            f"| **❌ Failed** | {self.failure_count} |",
            f"| **Success Rate** | {self._calculate_success_rate():.1f}% |",
            "",
        ]

        if self.failure_count == 0:
            report_lines.extend(
                [
                    "## ✅ MISSION STATUS: **VERIFIED**",
                    "",
                    "All tests passed. The Sentinel Mark I logic is fully verified.",
                    "No defects detected. Authorization protocol confirmed.",
                    "",
                ]
            )
        else:
            report_lines.extend(
                [
                    "## ⚠️ MISSION STATUS: **COMPROMISED**",
                    "",
                    f"**{self.failure_count}** test(s) failed. "
                    "Immediate investigation required.",
                    "",
                    "---",
                    "",
                    "## 🚨 FAILURE ANALYSIS",
                    "",
                ]
            )

            failure_timestamps = self.extract_failure_timestamps()

            for i, test in enumerate(self.test_results, 1):
                if test["status"] == "FAILED":
                    report_lines.extend(
                        [
                            f"### Test {i}: `{test['name']}`",
                            "",
                            f"- **Status:** ❌ FAILED",
                            f"- **Duration:** {test['time']:.3f}s",
                            f"- **Failure Type:** `{test['failure_type']}`",
                        ]
                    )

                    # Find timestamp for this test
                    timestamp = None
                    for name, ts in failure_timestamps:
                        if name == test["name"]:
                            timestamp = ts
                            break

                    if timestamp is not None:
                        report_lines.append(
                            f"- **Failure Timestamp:** `{timestamp:.1f} ns`"
                        )
                    else:
                        report_lines.append(
                            "- **Failure Timestamp:** Not available"
                        )

                    if test["message"]:
                        report_lines.extend(
                            [
                                "",
                                "**Error Message:**",
                                "```",
                                test["message"],
                                "```",
                            ]
                        )

                    if test["traceback"]:
                        # Only show first 20 lines of traceback
                        tb_lines = test["traceback"].strip().split("\n")
                        if len(tb_lines) > 20:
                            tb_lines = tb_lines[:20] + [
                                "... (truncated)"
                            ]

                        report_lines.extend(
                            [
                                "",
                                "**Traceback:**",
                                "```",
                            ]
                            + tb_lines
                            + [
                                "```",
                                "",
                            ]
                        )

        report_lines.extend(
            [
                "---",
                "",
                "## 📋 TEST RESULTS DETAIL",
                "",
                "| # | Test Name | Status | Duration (s) |",
                "|---|-----------|--------|--------------|",
            ]
        )

        for i, test in enumerate(self.test_results, 1):
            status_icon = "✅" if test["status"] == "PASSED" else "❌"
            report_lines.append(
                f"| {i} | `{test['name']}` | {status_icon} "
                f"{test['status']} | {test['time']:.3f} |"
            )

        report_lines.extend(
            [
                "",
                "---",
                "",
                "## 🔬 WAVEFORM ANALYSIS",
                "",
                f"**FST File:** `{self.fst_file_path.name}`",
                "",
            ]
        )

        if self.fst_file_path.exists():
            file_size = self.fst_file_path.stat().st_size / 1024  # KB
            report_lines.extend(
                [
                    f"- File Size: {file_size:.2f} KB",
                    "- Status: Available for analysis",
                    f"- Location: `{self.fst_file_path}`",
                    "",
                    "To view waveforms, open the FST file in GTKWave:",
                    "```bash",
                    f"gtkwave {self.fst_file_path} {self.fst_file_path.parent}/tb.gtkw",
                    "```",
                    "",
                ]
            )
        else:
            report_lines.extend(
                [
                    "- Status: ⚠️ FST file not found",
                    "- This may indicate a simulation failure or incomplete test run",
                    "",
                ]
            )

        report_lines.extend(
            [
                "---",
                "",
                "**VAELIX SYSTEMS** | *Tier 1 Defense Technology*",
                "",
                f"*Report generated by analyze_telemetry.py v1.0.0*",
                "",
            ]
        )

        return "\n".join(report_lines)

    def _calculate_success_rate(self) -> float:
        """Calculate test success rate as percentage."""
        if self.total_count == 0:
            return 0.0
        return (self.pass_count / self.total_count) * 100


def main():
    """Main entry point for the telemetry analyzer."""
    parser = argparse.ArgumentParser(
        description="VAELIX Sentinel Telemetry Analyzer - Parse Cocotb results and generate mission debrief",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze with default paths
  python analyze_telemetry.py

  # Analyze with custom paths
  python analyze_telemetry.py --results-xml test/results.xml --fst-file test/tb.fst

  # Write output to file
  python analyze_telemetry.py --output MISSION_DEBRIEF.md

  # Update README.md section
  python analyze_telemetry.py --update-readme
        """,
    )

    parser.add_argument(
        "--results-xml",
        type=Path,
        default=Path("test/results.xml"),
        help="Path to Cocotb results.xml file (default: test/results.xml)",
    )

    parser.add_argument(
        "--fst-file",
        type=Path,
        default=Path("test/tb.fst"),
        help="Path to FST waveform file (default: test/tb.fst)",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output file for the report (default: print to stdout)",
    )

    parser.add_argument(
        "--update-readme",
        action="store_true",
        help="Append report to README.md",
    )

    args = parser.parse_args()

    try:
        # Create analyzer
        analyzer = TelemetryAnalyzer(args.results_xml, args.fst_file)

        # Parse results
        print(f"📊 Parsing test results from: {args.results_xml}")
        analyzer.parse_results_xml()

        print(
            f"✅ Found {analyzer.total_count} tests: "
            f"{analyzer.pass_count} passed, {analyzer.failure_count} failed"
        )

        # Generate report
        print("📝 Generating mission debrief report...")
        report = analyzer.generate_markdown_report()

        # Output report
        if args.output:
            args.output.write_text(report)
            print(f"✅ Report written to: {args.output}")
        else:
            print("\n" + "=" * 80)
            print(report)
            print("=" * 80 + "\n")

        # Update README if requested
        if args.update_readme:
            readme_path = Path("README.md")
            if readme_path.exists():
                print("📄 Updating README.md with test results...")
                update_readme_with_report(readme_path, report)
                print("✅ README.md updated successfully")
            else:
                print("⚠️  README.md not found, skipping update")

        # Exit with appropriate code
        sys.exit(0 if analyzer.failure_count == 0 else 1)

    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(3)


def update_readme_with_report(readme_path: Path, report: str) -> None:
    """
    Update README.md by appending or replacing the test results section.
    """
    readme_content = readme_path.read_text()

    # Define markers for the test results section
    start_marker = "<!-- TEST_RESULTS_START -->"
    end_marker = "<!-- TEST_RESULTS_END -->"

    # Create the section content
    section_content = (
        f"\n{start_marker}\n"
        f"## 🔬 LATEST TEST RESULTS\n\n"
        f"{report}\n"
        f"{end_marker}\n"
    )

    # Check if markers already exist
    if start_marker in readme_content and end_marker in readme_content:
        # Replace existing section
        pattern = (
            f"{re.escape(start_marker)}.*?{re.escape(end_marker)}"
        )
        new_content = re.sub(
            pattern, section_content.strip(), readme_content, flags=re.DOTALL
        )
    else:
        # Append to end of file
        new_content = readme_content.rstrip() + "\n\n" + section_content

    readme_path.write_text(new_content)


if __name__ == "__main__":
    main()
