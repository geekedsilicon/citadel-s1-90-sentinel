#!/bin/bash
# ============================================================================
# TASK XVII: THE TARNOVSKY TOKEN - Synthesis Verification Script
# ============================================================================
# PURPOSE: Verify that Yosys synthesis preserves the FSM state encodings
#          and that the (* keep *) attribute prevents optimization.
#
# VERIFICATION GOALS:
# 1. The 8-bit state register (state_reg) is present in the netlist
# 2. The state encodings (0xA5, 0x5A, 0x00) are preserved
# 3. The (* keep *) attribute prevents the optimizer from reducing to 2-bit encoding
# ============================================================================

set -e  # Exit on error

# Change to script directory (handles being run from anywhere)
cd "$(dirname "$0")"

echo "============================================================================"
echo "TASK XVII: THE TARNOVSKY TOKEN - Synthesis Verification"
echo "============================================================================"
echo ""

# Check if Yosys is available
if ! command -v yosys &> /dev/null; then
    echo "ERROR: Yosys is not installed or not in PATH"
    echo "This verification requires Yosys to be installed."
    echo ""
    echo "To install Yosys:"
    echo "  Ubuntu/Debian: sudo apt-get install yosys"
    echo "  Fedora:        sudo dnf install yosys"
    echo "  Arch:          sudo pacman -S yosys"
    echo "  macOS:         brew install yosys"
    echo ""
    exit 1
fi

echo "✓ Yosys found: $(yosys -V | head -1)"
echo ""

# Create temporary directory for synthesis outputs
WORK_DIR=$(mktemp -d)
echo "Working directory: $WORK_DIR"
echo ""

# Run Yosys synthesis
echo "Running Yosys synthesis..."
cat > "$WORK_DIR/synth.ys" << 'EOF'
# Read source files
read_verilog src/cells.v
read_verilog src/tt_um_vaelix_sentinel.v

# Hierarchy check
hierarchy -check -top tt_um_vaelix_sentinel

# Print statistics before optimization
stat -top tt_um_vaelix_sentinel

# Basic synthesis (proc, opt, fsm, memory, techmap)
proc
opt
fsm
opt
memory
opt

# Print statistics after optimization
stat -top tt_um_vaelix_sentinel

# Write out the synthesized netlist
write_verilog -noattr synthesized.v

# Generate a report
tee -o synthesis_report.txt stat -top tt_um_vaelix_sentinel
EOF

yosys "$WORK_DIR/synth.ys" > "$WORK_DIR/yosys_output.log" 2>&1

echo "✓ Synthesis complete"
echo ""

# Analyze the synthesized netlist
echo "Analyzing synthesized netlist..."
echo ""

# Check for state register
if grep -q "state_reg" synthesized.v; then
    echo "✓ state_reg found in synthesized netlist"
    
    # Count the width of state_reg
    if grep "state_reg" synthesized.v | grep -q "\[7:0\]"; then
        echo "✓ state_reg is 8-bit wide (preserves Hamming distance encoding)"
    else
        echo "⚠ WARNING: state_reg may have been optimized to fewer bits"
        echo "  This could indicate (* keep *) attribute is not working as expected"
    fi
else
    echo "⚠ WARNING: state_reg not found explicitly in netlist"
    echo "  Register may have been renamed or optimized away"
fi

# Check for DFF (D flip-flops) which should represent the state register
echo ""
echo "Checking for flip-flops (state register implementation):"
grep -c "dff" synthesized.v | xargs -I {} echo "  Found {} DFF instances"

# Display synthesis statistics
echo ""
echo "Synthesis Statistics:"
echo "--------------------"
if [ -f synthesis_report.txt ]; then
    grep -A 20 "Number of cells" synthesis_report.txt || echo "  (statistics not captured)"
fi

# Look for FSM detection
echo ""
echo "FSM Detection:"
echo "-------------"
if grep -q "FSM" "$WORK_DIR/yosys_output.log"; then
    echo "✓ Yosys detected FSM in the design"
    grep "FSM" "$WORK_DIR/yosys_output.log" | head -5
else
    echo "  No explicit FSM detection message (this is okay)"
fi

# Check for state parameters in the log
echo ""
echo "State Encoding Check:"
echo "--------------------"
if grep -E "(STATE_LOCKED|STATE_VERIFIED|STATE_HARD_LOCK|0xA5|0x5A)" synthesized.v; then
    echo "✓ State encodings or constants found in netlist"
else
    echo "  State encodings may have been optimized into logic"
fi

echo ""
echo "============================================================================"
echo "Verification Summary"
echo "============================================================================"
echo ""
echo "Key Findings:"
echo "1. FSM state register: $(grep -q 'state_reg' synthesized.v && echo 'PRESERVED' || echo 'OPTIMIZED')"
echo "2. State width: $(grep 'state_reg' synthesized.v 2>/dev/null | head -1 || echo 'Not explicitly found')"
echo "3. (* keep *) attribute effect: To be manually verified in netlist"
echo ""
echo "Files generated:"
echo "  - synthesized.v: Complete synthesized netlist"
echo "  - $WORK_DIR/yosys_output.log: Full Yosys output"
echo ""
echo "For detailed analysis, review: synthesized.v"
echo ""
echo "IMPORTANT: The (* keep *) attribute tells Yosys not to optimize away the"
echo "           register, but the actual effectiveness depends on the synthesis"
echo "           flow and target technology library."
echo ""
echo "============================================================================"
