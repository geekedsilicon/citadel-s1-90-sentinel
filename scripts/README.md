# VAELIX | PROJECT CITADEL — Scripts Directory

This directory contains analysis and utility scripts for the Sentinel Mark I project.

## Scripts

### check_coverage.py

**Purpose:** Parse coverage.info files and enforce 100% coverage requirements.

**Usage:**
```bash
python3 scripts/check_coverage.py [coverage.info]
```

**Description:**
The Inspector - enforces the Vaelix standard of 100% line and branch coverage. Parses LCOV format coverage data and reports:
- Line coverage percentage
- Branch coverage percentage
- Specific lines that were not executed
- Specific branches that were not taken

**Exit Codes:**
- `0` - Coverage meets 100% requirement
- `1` - Coverage is below 100% or file not found

**Example:**
```bash
cd test
make COVERAGE=1
make check-coverage
```

### demo_coverage.sh

**Purpose:** Demonstrate coverage analysis functionality without requiring Verilator installation.

**Usage:**
```bash
bash scripts/demo_coverage.sh
```

**Description:**
Creates mock coverage data and tests the coverage checker with both passing (100%) and failing (< 100%) scenarios. Useful for:
- Verifying the coverage checker works correctly
- Understanding coverage report format
- CI/CD testing without Verilator

**Tests:**
1. 100% coverage scenario (should pass)
2. Incomplete coverage scenario (should fail)

## Coverage Workflow

### Full Workflow with Verilator

```bash
# 1. Run tests with coverage collection
cd test
make COVERAGE=1

# 2. Generate coverage.info
make coverage-report

# 3. Check coverage requirements
make check-coverage
```

### Quick Test with Demo

```bash
# Test the coverage checker without running actual tests
bash scripts/demo_coverage.sh
```

## Requirements

### check_coverage.py
- Python 3.8+
- No additional dependencies

### demo_coverage.sh
- Bash
- Python 3.8+
- check_coverage.py in scripts directory

### Coverage Collection (make COVERAGE=1)
- Verilator 5.036+
- Cocotb 2.0.1+
- Python 3.8+

## Coverage File Format

The coverage.info file uses the standard LCOV format:

```
TN:test_name
SF:source_file_path
DA:line_number,execution_count
LF:lines_found
LH:lines_hit
BRDA:line,block,branch,taken_count
BRF:branches_found
BRH:branches_hit
end_of_record
```

## Vaelix Standard

"We accept nothing less than 100% on a core this critical."

All code paths must be exercised during testing. The Inspector will reject any coverage report below 100% for either line or branch coverage.

## See Also

- `docs/COVERAGE.md` - Detailed coverage analysis setup guide
- `test/Makefile` - Coverage targets and configuration
- `test/test.py` - Test suite that generates coverage data
