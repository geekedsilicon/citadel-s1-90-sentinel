# ============================================================================
# PROJECT CITADEL | SYNOPSYS DESIGN CONSTRAINTS (SDC)
# ============================================================================
# AUTHOR:    Vaelix Systems Engineering / Physical Design Division
# TARGET:    IHP 130nm SG13G2 Process
# PURPOSE:   Timing and Load Constraints for Silicon Fabrication
#
# DESCRIPTION:
# This SDC file defines the temporal boundaries and electrical characteristics
# that govern signal propagation in the Citadel hardware. We do not let the
# foundry guess. We dictate the tempo.
# ============================================================================

# -----------------------------------------------------------------------------
# 1. SYSTEM CLOCK DEFINITION
# -----------------------------------------------------------------------------
# Clock: clk
# Period: 40ns (25 MHz)
# Duty Cycle: 50%
#
# This establishes the fundamental timing reference for all sequential logic
# within the Sentinel module. The 25 MHz operating frequency provides robust
# timing margins against process, voltage, and temperature (PVT) variations.
# -----------------------------------------------------------------------------
create_clock -name clk -period 40.0 -waveform {0.0 20.0} [get_ports clk]

# -----------------------------------------------------------------------------
# 2. INPUT TIMING CONSTRAINTS
# -----------------------------------------------------------------------------
# Input Delay: ui_in (8-bit authorization key interface)
# Delay: 5ns relative to the rising edge of clk
#
# This constraint models the PCB trace delay and setup time requirement for
# external signals arriving at the input ports. The 5ns delay ensures proper
# synchronization with the internal clock domain.
# -----------------------------------------------------------------------------
set_input_delay -clock clk -max 5.0 [get_ports ui_in[*]]

# -----------------------------------------------------------------------------
# 3. OUTPUT TIMING CONSTRAINTS
# -----------------------------------------------------------------------------
# Output Delay: uo_out (7-segment display interface)
# Delay: 5ns
#
# This constraint ensures that output signals meet the setup time requirements
# of downstream devices (in this case, the 7-segment display driver).
# -----------------------------------------------------------------------------
set_output_delay -clock clk -max 5.0 [get_ports uo_out[*]]

# -----------------------------------------------------------------------------
# 4. ELECTRICAL LOAD CONSTRAINTS
# -----------------------------------------------------------------------------
# Load Capacitance: 5pF on all output ports
#
# This models the physical capacitive load presented by the 7-segment display
# and other output devices. Proper load modeling is critical for accurate
# timing analysis and buffer insertion during physical synthesis.
#
# Output Ports:
# - uo_out[7:0]:  7-segment display interface (Common Anode / Active LOW)
# - uio_out[7:0]: Status array (Vaelix "Glow" persistence)
# - uio_oe[7:0]:  Bidirectional port direction control
# -----------------------------------------------------------------------------
set_load -pin_load 5.0 [get_ports uo_out[*]]
set_load -pin_load 5.0 [get_ports uio_out[*]]
set_load -pin_load 5.0 [get_ports uio_oe[*]]

# ============================================================================
# END OF SDC CONSTRAINTS
# ============================================================================
