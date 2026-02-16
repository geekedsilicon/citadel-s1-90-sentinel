# VAELIX | PROJECT CITADEL — Coverage Analysis Setup

## Overview

This document describes how to enable and run coverage analysis on the Sentinel Mark I core. The coverage analysis tool ("The Inspector") enforces 100% line and branch coverage requirements.

## Requirements

### Software Dependencies

1. **Verilator 5.036 or later** (required for coverage collection)
2. **Python 3.8+** (for coverage analysis)
3. **Cocotb 2.0.1+** (for test execution)

### Installing Verilator 5.036+

Most Linux distributions ship with older versions of Verilator. You'll need to build from source:

```bash
# Install build dependencies
sudo apt-get install git ccache flex bison libfl-dev

# Clone Verilator repository
cd /tmp
git clone https://github.com/verilator/verilator.git
cd verilator

# Checkout version 5.036 or later
git checkout v5.036

# Build and install
autoconf
./configure --prefix=/usr/local
make -j$(nproc)
sudo make install

# Verify installation
verilator --version
# Should show: Verilator 5.036 or later
```

## Running Coverage Analysis

### Step 1: Run Tests with Coverage Collection

```bash
cd test
make COVERAGE=1
```

This command:
- Switches to Verilator simulator
- Enables line and branch coverage collection
- Runs all test cases
- Generates `sim_build/coverage.dat`

### Step 2: Generate Coverage Report

```bash
cd test
make coverage-report
```

This generates `coverage.info` in lcov format.

### Step 3: Check Coverage Requirements

```bash
cd test
make check-coverage
```

Or run the script directly:

```bash
python3 scripts/check_coverage.py test/coverage.info
```

The script will:
- Parse the coverage data
- Report line and branch coverage percentages
- List any missed lines or branches
- Exit with status 0 if 100% coverage achieved
- Exit with status 1 if coverage < 100%

## Expected Output

### Successful Coverage (100%)

```
================================================================================
VAELIX | PROJECT CITADEL — THE INSPECTOR (Coverage Analysis)
================================================================================

Line Coverage:   156/156 (100.00%)
Branch Coverage: 24/24 (100.00%)

================================================================================
RESULT: ✓ COVERAGE VERIFICATION PASSED — 100% Sentinel Standard Met
================================================================================
```

### Failed Coverage (< 100%)

```
================================================================================
VAELIX | PROJECT CITADEL — THE INSPECTOR (Coverage Analysis)
================================================================================

Line Coverage:   150/156 (96.15%)
Branch Coverage: 22/24 (91.67%)

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
CRITICAL: Line coverage is below 100%!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

Missed Lines:

  File: ../src/tt_um_vaelix_sentinel.v
    Line 45
    Lines 67-69

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
CRITICAL: Branch coverage is below 100%!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

Missed Branches:

  File: ../src/tt_um_vaelix_sentinel.v
    Line 75, Block 0, Branch 1

================================================================================
RESULT: ✗ COVERAGE VERIFICATION FAILED — Incomplete Path Coverage
================================================================================

Vaelix Standard: We accept nothing less than 100% on a core this critical.
```

## Integration with CI/CD

Add to your GitHub Actions workflow:

```yaml
- name: Run Coverage Analysis
  run: |
    cd test
    make COVERAGE=1
    make check-coverage
```

The job will fail if coverage is less than 100%.

## Troubleshooting

### "Verilator version too old" Error

```
make: *** COVERAGE=1 requires Verilator 5.036+. Current: 5.020.
```

**Solution**: Build and install Verilator 5.036+ from source (see installation instructions above).

### "No coverage.dat found" Error

**Solution**: Make sure to run `make COVERAGE=1` first to generate coverage data.

### Missing Dependencies

If you see errors about missing tools:

```bash
# Install required packages
pip install -r test/requirements.txt
```

## Coverage File Format

The `coverage.info` file uses the standard lcov format:

- `SF:` Source file path
- `DA:line,count` Line hit data
- `LF:` Lines found
- `LH:` Lines hit
- `BRDA:line,block,branch,taken` Branch hit data  
- `BRF:` Branches found
- `BRH:` Branches hit

## Vaelix Standard

"We accept nothing less than 100% on a core this critical."

The Inspector enforces the Vaelix standard: both line coverage and branch coverage must be exactly 100%. Any code path not executed during testing is considered a security vulnerability.
