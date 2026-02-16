#!/bin/bash

# ============================================================================
# VAELIX SENTINEL - VENV-AWARE TEST RUNNER
# ============================================================================
# This script properly activates the Python venv before running tests
# ============================================================================

set -e

WORKSPACE_ROOT="/workspaces/citadel-s1-90-sentinel"
VENV="${WORKSPACE_ROOT}/.venv"

# Activate virtual environment
if [ ! -d "$VENV" ]; then
    echo "ERROR: Virtual environment not found at $VENV"
    exit 1
fi

echo "Activating Python virtual environment..."
source "${VENV}/bin/activate"

echo "Python: $(python --version)"
echo "Cocotb: $(python -c 'import cocotb; print(cocotb.__version__)' 2>/dev/null || echo 'NOT FOUND')"
echo ""

# Navigate to test directory
cd "${WORKSPACE_ROOT}/test"

# Show usage if no arguments
if [ $# -eq 0 ]; then
    cat << 'USAGE'

VAELIX SENTINEL - TEST RUNNER

Usage: run_tests.sh [COMMAND] [OPTIONS]

COMMANDS:

  python [OPTIONS]
    Run Python behavioral model tests
    Options: [--verbose]
    Example: run_tests.sh python --verbose

  rtl [OPTIONS]
    Run RTL simulation with Cocotb + Icarus
    Options: [--clean] [--verbose]
    Example: run_tests.sh rtl

  coverage [OPTIONS]
    Run tests with coverage analysis
    Options: [--report] [--threshold 90]
    Example: run_tests.sh coverage --report

  gates
    Run gate-level simulation (requires PDK)
    Example: run_tests.sh gates

  all
    Run all tests (RTL + Coverage)
    Example: run_tests.sh all

  help
    Show this help message

EXAMPLES:

  # Run Python model
  run_tests.sh python

  # Run RTL simulation with coverage
  run_tests.sh coverage --report

  # Run all tests sequentially
  run_tests.sh all

USAGE
    exit 0
fi

# Parse command
CMD=$1
shift

case "$CMD" in
    python)
        echo "═════════════════════════════════════════"
        echo "Running Python Behavioral Model Tests..."
        echo "═════════════════════════════════════════"
        python test.py "$@"
        ;;

    rtl)
        echo "═════════════════════════════════════════"
        echo "Running RTL Simulation (Cocotb + Icarus)..."
        echo "═════════════════════════════════════════"
        if [[ "$*" == *"--clean"* ]]; then
            make clean
        fi
        make -B "$@"
        ;;

    coverage)
        echo "═════════════════════════════════════════"
        echo "Running Coverage Analysis (Verilator)..."
        echo "═════════════════════════════════════════"
        echo "Building with coverage instrumentation..."
        make COVERAGE=1 "$@"

        echo ""
        echo "Generating coverage report..."
        make coverage-report

        echo ""
        echo "Checking coverage..."
        make check-coverage

        if [[ "$*" == *"--report"* ]]; then
            echo ""
            echo "Coverage report saved to: coverage.info"
        fi
        ;;

    gates)
        echo "═════════════════════════════════════════"
        echo "Running Gate-Level Simulation..."
        echo "═════════════════════════════════════════"
        make GATES=yes "$@"
        ;;

    all)
        echo "═════════════════════════════════════════"
        echo "Running All Tests Sequentially..."
        echo "═════════════════════════════════════════"

        echo ""
        echo "1. Python Model Tests..."
        python test.py

        echo ""
        echo "2. RTL Simulation..."
        make -B

        echo ""
        echo "3. Coverage Analysis..."
        make COVERAGE=1
        make coverage-report
        make check-coverage

        echo ""
        echo "═════════════════════════════════════════"
        echo "All tests completed!"
        echo "═════════════════════════════════════════"
        ;;

    help|--help|-h)
        cat << 'HELP'

VAELIX SENTINEL - TEST RUNNER HELP

This script properly activates the Python virtual environment and runs tests.

AVAILABLE TOOLS:
  ✅ Python 3.12.12 (with Cocotb 2.0.1, Pytest 8.3.4)
  ✅ Verilator 5.042 (coverage analysis)
  ✅ Icarus Verilog 12.0 (RTL simulation)

TEST COMMANDS:

  run_tests.sh python
    └─ Pure Python behavioral model (all 16 core tests)
    └─ No external tools required
    └─ Time: ~10 seconds

  run_tests.sh rtl
    └─ RTL simulation with Cocotb framework
    └─ Generates: results.xml, tb.fst waveforms
    └─ Time: ~30-60 seconds

  run_tests.sh coverage
    └─ Coverage analysis with Verilator instrumentation
    └─ Generates: coverage.dat, coverage.info
    └─ With 100% enforcement
    └─ Time: ~1-2 minutes

  run_tests.sh gates
    └─ Gate-level simulation (SG13G2 PDK required)
    └─ Time: varies

  run_tests.sh all
    └─ Run all tests in sequence
    └─ Time: ~3-5 minutes

EXAMPLES:

  # Run just Python tests
  run_tests.sh python

  # Run RTL tests with fresh build
  cd test && bash ../run_tests.sh rtl

  # Run coverage with report
  bash run_tests.sh coverage --report

  # Run everything
  bash run_tests.sh all

OUTPUT:

  Each test generates detailed logs and metrics:
  - Python: stdout with test assertions
  - RTL: results.xml, tb.fst waveforms
  - Coverage: coverage.info, HTML reports
  - Gate: gate-level simulation results

HELP
        ;;

    *)
        echo "ERROR: Unknown command '$CMD'"
        echo "Run 'run_tests.sh help' for usage"
        exit 1
        ;;
esac
