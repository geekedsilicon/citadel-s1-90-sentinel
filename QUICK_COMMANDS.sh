#!/bin/bash

# ============================================================================
# VAELIX SENTINEL - QUICK REFERENCE COMMANDS
# ============================================================================
# Run this file to see all available test commands
# ============================================================================

cat << 'EOF'

╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║           VAELIX SENTINEL - QUICK COMMAND REFERENCE                       ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝

1. PYTHON BEHAVIORAL TESTS (Pure Python, No Simulator)
   ═════════════════════════════════════════════════════════════════════════

   cd /workspaces/citadel-s1-90-sentinel/test
   python3 test.py [--verbose]

   → Runs all 16 core tests (Golden Path, Security, Stability)
   → No external tools required
   → Output: Detailed test assertions
   → Time: ~10 seconds

   Status: ✅ ALWAYS WORKS

---

2. RTL SIMULATION WITH COCOTB (Icarus Verilog Backend)
   ═════════════════════════════════════════════════════════════════════════

   cd /workspaces/citadel-s1-90-sentinel/test
   make -B            # Build and run RTL tests
   make clean         # Clean build artifacts

   → Simulates Verilog RTL with Cocotb framework
   → Generates: results.xml, tb.fst (waveforms)
   → Runs: 15 Cocotb tests + Python model tests
   → Time: ~30-60 seconds

   Status: ✅ READY (with Icarus Verilog)

---

3. COVERAGE ANALYSIS (NEW! - Verilator)
   ═════════════════════════════════════════════════════════════════════════

   cd /workspaces/citadel-s1-90-sentinel/test

   # Run tests with coverage instrumentation
   make COVERAGE=1

   # Generate coverage report
   make coverage-report

   # Analyze coverage with enforcement
   make check-coverage

   → Requires: Verilator 5.036+ (✓ Installed: 5.042)
   → Generates: coverage.dat, coverage.info
   → Metrics: Line coverage, toggle coverage
   → Output: coverage.txt, coverage.info

   Status: ✅ NOW AVAILABLE

---

4. WAVEFORM VISUALIZATION - FST Files
   ═════════════════════════════════════════════════════════════════════════

   OPTION A: Web-based Viewer (Recommended)
   ────────────────────────────────────────
   a) Generate waveforms: cd test && make -B
   b) Visit: https://edaformal.org/
   c) Upload: test/tb.fst
   d) View in browser

   OPTION B: Docker with X11 Display
   ────────────────────────────────────────
   docker run -e DISPLAY=$DISPLAY \
     -v /tmp/.X11-unix:/tmp/.X11-unix \
     sentinel:latest gtkwave /workspace/test/tb.fst

   OPTION C: VS Code Dev Containers
   ────────────────────────────────────────
   Remote-Containers: Reopen in Container
   (Then: gtkwave test/tb.fst test/tb.gtkw)

   Status: ✅ FST files available | ⚠ GTKWave use workarounds

---

5. LOGIC SCHEMATIC GENERATION (Yosys)
   ═════════════════════════════════════════════════════════════════════════

   OPTION A: Use Docker
   ────────────────────────────────────────
   docker run sentinel:latest yosys \
     -p "read_verilog src/tt_um_vaelix_sentinel.v; \
          prep -top tt_um_vaelix_sentinel; \
          write_json sentinel_schematic.json"

   OPTION B: View in VS Code
   ────────────────────────────────────────
   Install extension: "Verilog-HDL/Systemverilog/Bluespec"
   Right-click RTL file → View Diagram

   OPTION C: Web Viewer
   ────────────────────────────────────────
   Use DigitalJS: https://digitaljs.tilk.eu/
   (Manually draw from schematic.json)

   Status: ⚠ Yosys not in Alpine | Docker/VS Code available

---

6. COMPREHENSIVE TEST SUITE (Everything)
   ═════════════════════════════════════════════════════════════════════════

   cd /workspaces/citadel-s1-90-sentinel
   bash run_all_tests.sh

   → Runs all phases sequentially
   → Auto-detects available tools
   → Generates detailed report
   → Prints VAELIX-style plaintext summary
   → Time: ~2-5 minutes

   Status: ✅ READY

---

7. TELEMETRY ANALYSIS & MISSION DEBRIEF
   ═════════════════════════════════════════════════════════════════════════

   cd /workspaces/citadel-s1-90-sentinel

   python3 analyze_telemetry.py \
     --results-xml test/results.xml \
     --fst-file test/tb.fst \
     --output test/MISSION_DEBRIEF.md

   → Parses Cocotb results.xml
   → Extracts failure timestamps from FST
   → Generates Markdown report
   → Exit code: 0=success, 1=failures, 2=not found, 3=error

   Status: ✅ READY

---

8. GATE-LEVEL SIMULATION (Verilator)
   ═════════════════════════════════════════════════════════════════════════

   cd /workspaces/citadel-s1-90-sentinel/test
   make GATES=yes

   → Requires: SG13G2 PDK (set PDK_ROOT env var)
   → Simulates gate-level netlist
   → Physical timing validation
   → Output: Gate-level results.xml

   Status: ✅ AVAILABLE (conditional on PDK)

---

9. VIEW TEST RESULTS
   ═════════════════════════════════════════════════════════════════════════

   View full test output:
   ────────────────────
   cat /workspaces/citadel-s1-90-sentinel/results_comprehensive_python.log

   View execution report:
   ────────────────────
   cat /workspaces/citadel-s1-90-sentinel/LATEST_RESULTS/EXECUTION_REPORT.md

   View coverage results:
   ────────────────────
   cat /workspaces/citadel-s1-90-sentinel/test/coverage.info

   View mission debrief:
   ────────────────────
   cat /workspaces/citadel-s1-90-sentinel/test/MISSION_DEBRIEF.md

---

10. TOOL STATUS CHECK
    ═════════════════════════════════════════════════════════════════════════

    Check all installed tools:
    ────────────────────────
    verilator --version        # ✅ 5.042
    iverilog -v                # ✅ 12.0
    python3 --version          # ✅ 3.12.12

    Activate Python environment:
    ────────────────────────────
    source /workspaces/citadel-s1-90-sentinel/.venv/bin/activate
    python3 -c "import cocotb; print('Cocotb:', cocotb.__version__)"

    View installation status:
    ───────────────────────────
    cat INSTALLATION_STATUS.md

---

SUMMARY TABLE
═════════════════════════════════════════════════════════════════════════════

Test Type              │ Command                          │ Status  │ Time
───────────────────────┼──────────────────────────────────┼─────────┼────────
Python Model           │ python3 test.py                  │ ✅      │ 10 sec
RTL Simulation         │ cd test && make -B               │ ✅      │ 30-60s
Coverage Analysis      │ cd test && make COVERAGE=1       │ ✅ NEW  │ 1-2 min
Gate-Level            │ cd test && make GATES=yes         │ ✅      │ varies
Comprehensive Suite    │ bash run_all_tests.sh            │ ✅      │ 2-5 min
Waveform Generation    │ make -B → tb.fst                 │ ✅      │ included
Telemetry Analysis     │ python3 analyze_telemetry.py ... │ ✅      │ <10 sec

═════════════════════════════════════════════════════════════════════════════

TROUBLESHOOTING
═════════════════════════════════════════════════════════════════════════════

Issue: "make: not found"
Solution: Install make → apt/apk/brew install make

Issue: "cocotb not found"
Solution: Activate venv → source .venv/bin/activate

Issue: "verilator: command not found"
Solution: Already installed! Check: which verilator

Issue: "gtkwave not found"
Solution: Use web viewer (https://edaformal.org/) or Docker

Issue: "yosys not found"
Solution: Use Docker container (pre-installed) or VS Code extension

═════════════════════════════════════════════════════════════════════════════

MORE INFORMATION
═════════════════════════════════════════════════════════════════════════════

For detailed info, see:
  • INSTALLATION_STATUS.md - Complete setup reference
  • COMPREHENSIVE_TEST_RESULTS.md - Full test statistics
  • docs/IMPLEMENTATION_GUIDE.md - Hardware details
  • docs/KAMKAR_EQUALIZER.md - Security architecture

═════════════════════════════════════════════════════════════════════════════

EOF
