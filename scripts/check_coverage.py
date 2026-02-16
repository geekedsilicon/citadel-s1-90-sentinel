#!/usr/bin/env python3
# ============================================================================
# VAELIX | PROJECT CITADEL — COVERAGE ANALYSIS TOOL
# ============================================================================
# FILE:      scripts/check_coverage.py
# VERSION:   1.0.0 — The Inspector
# PURPOSE:   Parse coverage.info and enforce 100% coverage requirement
# STANDARD:  Vaelix Missionary Standard v1.2
# ============================================================================
# SPDX-License-Identifier: Apache-2.0

import sys
import os
import re
from pathlib import Path


class CoverageAnalyzer:
    """
    Parse LCOV coverage.info format and enforce 100% coverage requirements.
    
    Format specification:
        TN:test name
        SF:source file path
        FN:line,function_name
        FNDA:execution_count,function_name
        FNF:functions found
        FNH:functions hit
        DA:line,execution_count
        LF:lines found
        LH:lines hit
        BRDA:line,block,branch,taken_count
        BRF:branches found
        BRH:branches hit
        end_of_record
    """
    
    def __init__(self, coverage_file):
        self.coverage_file = coverage_file
        self.files = {}  # {filename: {lines: {}, branches: {}}}
        
    def parse(self):
        """Parse the coverage.info file."""
        if not os.path.exists(self.coverage_file):
            print(f"ERROR: Coverage file not found: {self.coverage_file}")
            sys.exit(1)
            
        with open(self.coverage_file, 'r') as f:
            current_file = None
            
            for line in f:
                line = line.strip()
                
                # Source file
                if line.startswith('SF:'):
                    current_file = line[3:]
                    if current_file not in self.files:
                        self.files[current_file] = {
                            'lines': {},
                            'branches': {},
                            'lines_found': 0,
                            'lines_hit': 0,
                            'branches_found': 0,
                            'branches_hit': 0
                        }
                
                # Line coverage: DA:line_number,execution_count
                elif line.startswith('DA:') and current_file:
                    parts = line[3:].split(',')
                    if len(parts) >= 2:
                        line_num = int(parts[0])
                        exec_count = int(parts[1])
                        self.files[current_file]['lines'][line_num] = exec_count
                
                # Line statistics
                elif line.startswith('LF:') and current_file:
                    self.files[current_file]['lines_found'] = int(line[3:])
                    
                elif line.startswith('LH:') and current_file:
                    self.files[current_file]['lines_hit'] = int(line[3:])
                
                # Branch coverage: BRDA:line,block,branch,taken
                elif line.startswith('BRDA:') and current_file:
                    parts = line[5:].split(',')
                    if len(parts) >= 4:
                        line_num = int(parts[0])
                        block = parts[1]
                        branch = parts[2]
                        # taken can be: '-' (not executed), '0' (not taken), 'n/a' (not applicable), or numeric count
                        taken = parts[3].strip()
                        
                        if line_num not in self.files[current_file]['branches']:
                            self.files[current_file]['branches'][line_num] = []
                        
                        self.files[current_file]['branches'][line_num].append({
                            'block': block,
                            'branch': branch,
                            'taken': taken
                        })
                
                # Branch statistics
                elif line.startswith('BRF:') and current_file:
                    self.files[current_file]['branches_found'] = int(line[4:])
                    
                elif line.startswith('BRH:') and current_file:
                    self.files[current_file]['branches_hit'] = int(line[4:])
    
    def calculate_coverage(self):
        """Calculate overall coverage statistics."""
        total_lines_found = 0
        total_lines_hit = 0
        total_branches_found = 0
        total_branches_hit = 0
        
        for filename, data in self.files.items():
            total_lines_found += data['lines_found']
            total_lines_hit += data['lines_hit']
            total_branches_found += data['branches_found']
            total_branches_hit += data['branches_hit']
        
        line_coverage = (total_lines_hit / total_lines_found * 100) if total_lines_found > 0 else 100.0
        branch_coverage = (total_branches_hit / total_branches_found * 100) if total_branches_found > 0 else 100.0
        
        return {
            'lines_found': total_lines_found,
            'lines_hit': total_lines_hit,
            'line_coverage': line_coverage,
            'branches_found': total_branches_found,
            'branches_hit': total_branches_hit,
            'branch_coverage': branch_coverage
        }
    
    def find_missed_lines(self):
        """Find all lines that were not executed."""
        missed = {}
        
        for filename, data in self.files.items():
            missed_lines = []
            for line_num, exec_count in data['lines'].items():
                if exec_count == 0:
                    missed_lines.append(line_num)
            
            if missed_lines:
                missed[filename] = sorted(missed_lines)
        
        return missed
    
    def find_missed_branches(self):
        """Find all branches that were not taken."""
        missed = {}
        
        for filename, data in self.files.items():
            missed_branches = []
            for line_num, branches in data['branches'].items():
                for branch in branches:
                    # Branch is missed if: '-' (not executed), '0' (not taken)
                    # 'n/a' indicates not applicable and should not be counted as missed
                    if branch['taken'] in ('-', '0'):
                        missed_branches.append({
                            'line': line_num,
                            'block': branch['block'],
                            'branch': branch['branch']
                        })
            
            if missed_branches:
                missed[filename] = missed_branches
        
        return missed
    
    def report(self):
        """Generate coverage report and exit with appropriate status code."""
        print("=" * 80)
        print("VAELIX | PROJECT CITADEL — THE INSPECTOR (Coverage Analysis)")
        print("=" * 80)
        
        stats = self.calculate_coverage()
        
        print(f"\nLine Coverage:   {stats['lines_hit']}/{stats['lines_found']} " +
              f"({stats['line_coverage']:.2f}%)")
        print(f"Branch Coverage: {stats['branches_hit']}/{stats['branches_found']} " +
              f"({stats['branch_coverage']:.2f}%)")
        
        # Check if coverage meets requirements
        passed = True
        
        if stats['line_coverage'] < 100.0:
            passed = False
            print(f"\n{'!' * 80}")
            print(f"CRITICAL: Line coverage is below 100%!")
            print(f"{'!' * 80}")
            
            missed_lines = self.find_missed_lines()
            if missed_lines:
                print("\nMissed Lines:")
                for filename, lines in missed_lines.items():
                    print(f"\n  File: {filename}")
                    # Group consecutive lines for better readability
                    ranges = self._group_consecutive(lines)
                    for r in ranges:
                        if len(r) == 1:
                            print(f"    Line {r[0]}")
                        else:
                            print(f"    Lines {r[0]}-{r[-1]}")
        
        if stats['branch_coverage'] < 100.0:
            passed = False
            print(f"\n{'!' * 80}")
            print(f"CRITICAL: Branch coverage is below 100%!")
            print(f"{'!' * 80}")
            
            missed_branches = self.find_missed_branches()
            if missed_branches:
                print("\nMissed Branches:")
                for filename, branches in missed_branches.items():
                    print(f"\n  File: {filename}")
                    for branch in branches:
                        print(f"    Line {branch['line']}, Block {branch['block']}, " +
                              f"Branch {branch['branch']}")
        
        print("\n" + "=" * 80)
        
        if passed:
            print("RESULT: ✓ COVERAGE VERIFICATION PASSED — 100% Sentinel Standard Met")
            print("=" * 80)
            return 0
        else:
            print("RESULT: ✗ COVERAGE VERIFICATION FAILED — Incomplete Path Coverage")
            print("=" * 80)
            print("\nVaelix Standard: We accept nothing less than 100% on a core this critical.")
            return 1
    
    def _group_consecutive(self, numbers):
        """Group consecutive numbers into ranges."""
        if not numbers:
            return []
        
        ranges = []
        current_range = [numbers[0]]
        
        for num in numbers[1:]:
            if num == current_range[-1] + 1:
                current_range.append(num)
            else:
                ranges.append(current_range)
                current_range = [num]
        
        ranges.append(current_range)
        return ranges


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        coverage_file = sys.argv[1]
    else:
        # Default location relative to test directory
        coverage_file = 'coverage.info'
    
    if not os.path.exists(coverage_file):
        print(f"ERROR: Coverage file not found: {coverage_file}")
        print("\nUsage: python check_coverage.py [coverage.info]")
        print("\nMake sure to run 'make COVERAGE=1' first to generate coverage data.")
        sys.exit(1)
    
    analyzer = CoverageAnalyzer(coverage_file)
    analyzer.parse()
    exit_code = analyzer.report()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
