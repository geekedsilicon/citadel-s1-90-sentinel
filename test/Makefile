# ============================================================================
# VAELIX | PROJECT CITADEL — AUTOMATED VERIFICATION PROTOCOL
# ============================================================================
# FILE:      test/Makefile
# VERSION:   1.2.0 — Citadel Standard
# TARGET:    Tiny Tapeout 06 (IHP 130nm SG13G2)
# ENGINE:    Cocotb 2.0.1 + Icarus Verilog
# PURPOSE:   RTL & Gate-Level Verification of the Sentinel Mark I
# FIX LOG:
#   v1.0.0 — Initial Makefile
#   v1.1.0 — MODULE → COCOTB_TEST_MODULES (cocotb 2.0 migration)
#   v1.1.0 — PROJECT_SOURCES corrected to tt_um_vaelix_sentinel.v
#   v1.2.0 — [CRITICAL] Added cells.v to PROJECT_SOURCES (buffer_cell,
#             and_cell, or_cell, etc. required by the Sentinel design)
# ============================================================================

# --- SIMULATION CONFIGURATION -----------------------------------------------
SIM            ?= icarus
FST            ?= -fst
TOPLEVEL_LANG  ?= verilog

# --- SOURCE DEFINITIONS -----------------------------------------------------
SRC_DIR         = $(PWD)/../src

# CRITICAL: Both files are required. The Sentinel instantiates Citadel
# Primitives (buffer_cell, xnor_cell, and_cell, etc.) defined in cells.v.
# Missing cells.v causes: "error: Unknown module type: buffer_cell"
PROJECT_SOURCES = tt_um_vaelix_sentinel.v cells.v

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

# --- TEST MODULE (cocotb 2.0 — variable renamed from MODULE) ----------------
COCOTB_TEST_MODULES = test

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
