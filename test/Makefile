# ============================================================================
# VAELIX | PROJECT CITADEL — AUTOMATED VERIFICATION PROTOCOL
# ============================================================================
# FILE:      test/Makefile
# VERSION:   1.3.0 — Citadel Standard
# TARGET:    Tiny Tapeout 06 (IHP 130nm SG13G2)
# ENGINE:    Cocotb 2.0.1 + Icarus Verilog / Verilator
# PURPOSE:   RTL & Gate-Level Verification of the Sentinel Mark I
# FIX LOG:
#   v1.0.0 — Initial Makefile
#   v1.1.0 — MODULE → COCOTB_TEST_MODULES (cocotb 2.0 migration)
#   v1.1.0 — PROJECT_SOURCES corrected to tt_um_vaelix_sentinel.v
#   v1.2.0 — [CRITICAL] Added cells.v to PROJECT_SOURCES (buffer_cell,
#             and_cell, or_cell, etc. required by the Sentinel design)
#   v1.3.0 — [CRITICAL] Added coverage analysis support (COVERAGE=1 flag)
#             Requires Verilator 5.036+ for coverage collection
#             Added coverage-report and check-coverage targets
# ============================================================================

# --- SIMULATION CONFIGURATION -----------------------------------------------
SIM            ?= icarus
FST            ?= -fst
TOPLEVEL_LANG  ?= verilog

# --- SOURCE DEFINITIONS -----------------------------------------------------
SRC_DIR         = $(PWD)/../src

# CRITICAL: All files are required. The Sentinel instantiates Citadel
# Primitives (buffer_cell, xnor_cell, and_cell, etc.) defined in cells.v.
# ring_oscillator.v provides the silicon fingerprint functionality.
# Missing cells.v causes: "error: Unknown module type: buffer_cell"
PROJECT_SOURCES = tt_um_vaelix_sentinel.v cells.v ring_oscillator.v

# --- SIMULATION MODES -------------------------------------------------------
ifneq ($(GATES),yes)

# MODE: RTL — Fast functional verification of the Vaelix logic intent.
SIM_BUILD        = sim_build/rtl
VERILOG_SOURCES += $(addprefix $(SRC_DIR)/,$(PROJECT_SOURCES))

else

# MODE: GLS — Physical reality check against the IHP SG13G2 PDK.
SIM_BUILD        = sim_build/gl

COMPILE_ARGS    += -DGL_TEST
COMPILE_ARGS    += -DFUNCTIONAL
COMPILE_ARGS    += -DSIM

VERILOG_SOURCES += $(PDK_ROOT)/ihp-sg13g2/libs.ref/sg13g2_io/verilog/sg13g2_io.v
VERILOG_SOURCES += $(PDK_ROOT)/ihp-sg13g2/libs.ref/sg13g2_stdcell/verilog/sg13g2_stdcell.v
VERILOG_SOURCES += $(PWD)/gate_level_netlist.v

endif

# --- ENVIRONMENT SETUP ------------------------------------------------------
COMPILE_ARGS    += -I$(SRC_DIR)

# --- TESTBENCH INTEGRATION --------------------------------------------------
VERILOG_SOURCES += $(PWD)/tb.v
TOPLEVEL         = tb

# --- TEST MODULE (cocotb 2.0 — overridable for different test suites) ------
COCOTB_TEST_MODULES ?= test

# --- COVERAGE CONFIGURATION -------------------------------------------------
# Enable coverage collection with: make COVERAGE=1
# Requires Verilator 5.036+ (install from source if system version is older)
ifeq ($(COVERAGE),1)
    # Verify Verilator version
    VERILATOR_VERSION := $(shell verilator --version 2>/dev/null | head -1 | awk '{print $$2}')
    VERILATOR_MAJOR := $(shell echo $(VERILATOR_VERSION) | cut -d. -f1)
    VERILATOR_MINOR_RAW := $(shell echo $(VERILATOR_VERSION) | cut -d. -f2)
    # Force base-10 interpretation to avoid octal issues with leading zeros (e.g., 036)
    VERILATOR_MINOR := $(shell echo $$((10#$(VERILATOR_MINOR_RAW))) 2>/dev/null || echo 0)
    
    # Check if Verilator meets minimum version (5.036)
    # Note: Verilator uses format 5.036, where minor version may have leading zeros
    VERILATOR_OK := $(shell [ "$(VERILATOR_MAJOR)" -gt 5 -o \( "$(VERILATOR_MAJOR)" -eq 5 -a "$(VERILATOR_MINOR)" -ge 36 \) ] && echo 1 || echo 0)
    
    ifneq ($(VERILATOR_OK),1)
        $(error COVERAGE=1 requires Verilator 5.036 or later. Current: $(VERILATOR_VERSION). Install from: https://github.com/verilator/verilator)
    endif
    
    # Switch to Verilator for coverage support
    SIM = verilator
    
    # Enable line and toggle coverage
    EXTRA_ARGS += --coverage --coverage-line --coverage-toggle
    
    # Verilator-specific flags for better compatibility
    EXTRA_ARGS += --trace-fst
endif

# --- COVERAGE POST-PROCESSING -----------------------------------------------
.PHONY: coverage-report
coverage-report:
	@echo "VAELIX: Generating coverage report..."
	@if [ ! -f sim_build/coverage.dat ]; then \
	    echo "VAELIX ERROR: No coverage.dat found. Run 'make COVERAGE=1' first."; \
	    exit 1; \
	fi
	verilator_coverage --write-info coverage.info sim_build/coverage.dat
	@echo "VAELIX: Coverage report generated: coverage.info"

.PHONY: check-coverage
check-coverage: coverage-report
	@echo "VAELIX: Analyzing coverage..."
	python3 ../scripts/check_coverage.py coverage.info

# --- COCOTB EXECUTION -------------------------------------------------------
include $(shell cocotb-config --makefiles)/Makefile.sim

# ============================================================================
# VAELIX LINTING ENGINE
# ============================================================================
# Strict Verilator linting enforces zero-defect RTL:
# - -Wall: Enable all warnings
# - -Wwarn-UNDRIVEN: Flag wires with no driver (unused signals)
# - Verilator exits with error code 1 on any warning (use -Wno-fatal to disable)
# - INITIAL blocks with non-blocking assignments trigger INITIALDLY warning
# ============================================================================

lint:
	@echo "VAELIX: Running strict Verilator linting on RTL sources..."
	verilator --lint-only -Wall -Wwarn-UNDRIVEN --top-module tt_um_vaelix_sentinel -I$(SRC_DIR) $(addprefix $(SRC_DIR)/,$(PROJECT_SOURCES))
	@echo "VAELIX: ✓ All linting checks passed with zero warnings."

# ============================================================================
# VAELIX VISUALIZATION ENGINE
# ============================================================================

visualize:
	@echo "VAELIX: Generating Logic Schematic for DigitalJS..."
	yosys -p "read_verilog ../src/cells.v ../src/tt_um_vaelix_sentinel.v; prep -top tt_um_vaelix_sentinel; write_json sentinel_schematic.json"
	@echo "VAELIX: Schematic generated: test/sentinel_schematic.json"
	@echo "VAELIX: Upload this file to https://digitaljs.tilk.eu/ to see the Gate."

# ============================================================================
# HELP & USAGE
# ============================================================================

.PHONY: coverage-help
coverage-help:
	@echo "================================================================================"
	@echo "VAELIX | PROJECT CITADEL — Coverage Analysis Commands"
	@echo "================================================================================"
	@echo ""
	@echo "Standard Testing:"
	@echo "  make               - Run RTL tests with Icarus Verilog"
	@echo "  make GATES=yes     - Run gate-level simulation"
	@echo "  make clean         - Remove build artifacts"
	@echo ""
	@echo "Coverage Analysis (requires Verilator 5.036+):"
	@echo "  make COVERAGE=1         - Run tests with coverage collection"
	@echo "  make coverage-report    - Generate coverage.info from coverage.dat"
	@echo "  make check-coverage     - Analyze coverage and enforce 100% requirement"
	@echo ""
	@echo "Full Coverage Workflow:"
	@echo "  make COVERAGE=1 && make check-coverage"
	@echo ""
	@echo "Visualization:"
	@echo "  make visualize     - Generate logic schematic (requires yosys)"
	@echo ""
	@echo "Documentation:"
	@echo "  See docs/COVERAGE.md for detailed coverage setup instructions"
	@echo ""
