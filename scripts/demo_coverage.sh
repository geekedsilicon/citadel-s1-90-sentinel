#!/bin/bash
# ============================================================================
# VAELIX | PROJECT CITADEL — Coverage Analysis Demo
# ============================================================================
# This script demonstrates the coverage analysis functionality using mock data

set -e

echo "================================================================================"
echo "VAELIX | PROJECT CITADEL — Coverage Analysis Demo"
echo "================================================================================"
echo ""

# Create temporary directory
DEMO_DIR="/tmp/coverage_demo_$$"
mkdir -p "$DEMO_DIR"

echo "[1/4] Creating mock coverage data with 100% coverage..."

cat > "$DEMO_DIR/perfect_coverage.info" << 'EOF'
TN:test_sentinel_perfect
SF:/home/runner/work/citadel-s1-90-sentinel/citadel-s1-90-sentinel/src/tt_um_vaelix_sentinel.v
FN:22,tt_um_vaelix_sentinel
FNDA:1,tt_um_vaelix_sentinel
FNF:1
FNH:1
DA:22,1
DA:40,100
DA:50,50
DA:75,150
DA:76,150
DA:89,150
DA:90,150
DA:98,100
LF:8
LH:8
BRDA:75,0,0,75
BRDA:75,0,1,75
BRDA:89,0,0,75
BRDA:89,0,1,75
BRF:4
BRH:4
end_of_record
EOF

echo "[2/4] Testing coverage checker with 100% coverage..."
echo ""
python3 scripts/check_coverage.py "$DEMO_DIR/perfect_coverage.info"
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✓ Test 1 PASSED: 100% coverage correctly identified"
else
    echo ""
    echo "✗ Test 1 FAILED: Expected exit code 0, got $EXIT_CODE"
    exit 1
fi

echo ""
echo "[3/4] Creating mock coverage data with incomplete coverage..."

cat > "$DEMO_DIR/incomplete_coverage.info" << 'EOF'
TN:test_sentinel_incomplete
SF:/home/runner/work/citadel-s1-90-sentinel/citadel-s1-90-sentinel/src/tt_um_vaelix_sentinel.v
FN:22,tt_um_vaelix_sentinel
FNDA:1,tt_um_vaelix_sentinel
FNF:1
FNH:1
DA:22,1
DA:40,100
DA:45,0
DA:50,0
DA:75,150
DA:76,150
DA:89,150
DA:90,150
DA:98,100
LF:9
LH:7
BRDA:75,0,0,150
BRDA:75,0,1,0
BRDA:89,0,0,75
BRDA:89,0,1,75
BRF:4
BRH:3
end_of_record
EOF

echo "[4/4] Testing coverage checker with incomplete coverage..."
echo ""

# This should fail
if python3 scripts/check_coverage.py "$DEMO_DIR/incomplete_coverage.info"; then
    echo ""
    echo "✗ Test 2 FAILED: Incomplete coverage should have failed but passed"
    exit 1
else
    echo ""
    echo "✓ Test 2 PASSED: Incomplete coverage correctly rejected"
fi

echo ""
echo "================================================================================"
echo "DEMO COMPLETE: All coverage analysis tests passed!"
echo "================================================================================"
echo ""
echo "Next Steps:"
echo "  1. Install Verilator 5.036+ (see docs/COVERAGE.md)"
echo "  2. Run: cd test && make COVERAGE=1"
echo "  3. Run: make check-coverage"
echo ""

# Cleanup
rm -rf "$DEMO_DIR"
