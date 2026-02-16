# 🔍 VAELIX Telemetry Analyzer

## Overview

The `analyze_telemetry.py` script automates the "Mission Debrief" process for the Sentinel Mark I verification suite. It parses Cocotb test results, extracts failure timestamps from waveform files, and generates comprehensive Markdown reports.

## Features

- ✅ **Automated Test Result Parsing**: Reads JUnit XML format results from Cocotb
- ⏱️ **Failure Timestamp Extraction**: Extracts simulation timestamps from test failures
- 📊 **Comprehensive Reporting**: Generates detailed Markdown reports with:
  - Executive summary with pass/fail statistics
  - Detailed failure analysis with timestamps
  - Complete test results table
  - Waveform file information
- 📝 **README Integration**: Can automatically update README.md with test results
- 🎯 **Flexible Output**: Print to stdout or write to file

## Installation

No additional dependencies are required beyond Python 3.7+. The script uses only standard library modules:
- `xml.etree.ElementTree` for XML parsing
- `argparse` for command-line interface
- `pathlib` for file system operations

## Usage

### Basic Usage

Run with default paths (looks for `test/results.xml` and `test/tb.fst`):

```bash
python analyze_telemetry.py
```

### Custom Paths

Specify custom input files:

```bash
python analyze_telemetry.py --results-xml path/to/results.xml --fst-file path/to/tb.fst
```

### Output to File

Write the report to a file instead of stdout:

```bash
python analyze_telemetry.py --output MISSION_DEBRIEF.md
```

### Update README.md

Automatically append the report to README.md:

```bash
python analyze_telemetry.py --update-readme
```

This will insert the report between `<!-- TEST_RESULTS_START -->` and `<!-- TEST_RESULTS_END -->` markers in README.md. If the markers don't exist, the report is appended to the end.

### Combined Example

```bash
python analyze_telemetry.py \
  --results-xml test/results.xml \
  --fst-file test/tb.fst \
  --output reports/debrief_$(date +%Y%m%d).md \
  --update-readme
```

## Integration with CI/CD

### GitHub Actions Workflow

Add to your `.github/workflows/test.yaml`:

```yaml
- name: Run Tests
  run: |
    cd test
    make -B

- name: Generate Mission Debrief
  if: always()  # Run even if tests fail
  run: |
    python analyze_telemetry.py \
      --results-xml test/results.xml \
      --fst-file test/tb.fst \
      --output MISSION_DEBRIEF.md

- name: Upload Debrief Report
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: mission-debrief
    path: MISSION_DEBRIEF.md
```

### Local Development

Add to your test Makefile:

```makefile
.PHONY: debrief
debrief:
	python ../analyze_telemetry.py --update-readme
	@echo "Mission debrief complete. Check README.md for results."
```

Then run:

```bash
cd test
make -B  # Run tests
make debrief  # Generate report
```

## Report Format

The generated report includes:

### 1. Executive Summary
- Total number of tests
- Pass/fail counts
- Success rate percentage
- Overall mission status

### 2. Failure Analysis (if any)
For each failed test:
- Test name and number
- Failure status and duration
- Failure type (e.g., AssertionError)
- **Failure timestamp** extracted from simulation
- Complete error message
- Relevant traceback

### 3. Complete Test Results
A table listing all tests with:
- Test number and name
- Pass/fail status
- Test duration

### 4. Waveform Analysis
- FST file location and size
- GTKWave command for viewing waveforms
- Notes on viewing specific failure timestamps

## Timestamp Extraction

The script automatically extracts failure timestamps from Cocotb error messages using pattern matching. It looks for:

- `at XXX ns` patterns
- `time: XXX` patterns  
- `XXX ns` patterns

These timestamps can be used to jump directly to the failure point in GTKWave:

```bash
gtkwave test/tb.fst test/tb.gtkw
# Then use View > Go To Time and enter the failure timestamp
```

## Command-Line Options

```
usage: analyze_telemetry.py [-h] [--results-xml PATH] [--fst-file PATH]
                            [--output PATH] [--update-readme]

VAELIX Sentinel Telemetry Analyzer

optional arguments:
  -h, --help           show this help message and exit
  --results-xml PATH   Path to Cocotb results.xml file (default: test/results.xml)
  --fst-file PATH      Path to FST waveform file (default: test/tb.fst)
  --output PATH        Output file for the report (default: print to stdout)
  --update-readme      Append report to README.md
```

## Exit Codes

- `0`: All tests passed
- `1`: One or more tests failed
- `2`: Results file not found
- `3`: Unexpected error during processing

## Examples

### Example 1: Quick Check After Testing

```bash
cd test && make -B && python ../analyze_telemetry.py
```

### Example 2: Generate Report for Archival

```bash
python analyze_telemetry.py \
  --output reports/verification_$(git rev-parse --short HEAD).md
```

### Example 3: Update Project Documentation

```bash
# Run tests
cd test && make -B

# Generate and save report
cd ..
python analyze_telemetry.py --update-readme

# Commit results
git add README.md
git commit -m "docs: Update test results in README"
```

## Troubleshooting

### "Results file not found" Error

Ensure you've run the tests first:
```bash
cd test
make -B
```

### Empty or Invalid XML

If `results.xml` is empty or malformed, check:
1. Cocotb is properly installed: `pip install cocotb>=1.9.2`
2. Tests actually ran (check `make` output)
3. No compilation errors in the test suite

### No Timestamp Extracted

If timestamps aren't showing in the report:
- Check that the FST file exists in the expected location
- Verify that Cocotb error messages include timing information
- Check the traceback format in the report

## Advanced: FST Waveform Analysis

While the script extracts timestamps from text, you can view the actual waveforms:

```bash
# Open waveforms at failure point
gtkwave test/tb.fst test/tb.gtkw

# In GTKWave menu:
# View > Go To Time > enter failure timestamp (e.g., "340.0 ns")
```

The FST file format is more compact than VCD and faster to load for large simulations.

## Contributing

To extend the analyzer:

1. **Add new timestamp patterns**: Edit `_extract_timestamp_from_traceback()` method
2. **Customize report format**: Modify `generate_markdown_report()` method
3. **Add new output formats**: Add methods for HTML, JSON, etc.

## License

Apache-2.0 - See LICENSE file for details

---

**VAELIX SYSTEMS** | *Tier 1 Defense Technology*

© 2026 Vaelix Systems. All Rights Reserved.
