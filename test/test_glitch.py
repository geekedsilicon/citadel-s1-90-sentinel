# ============================================================================
# VAELIX | PROJECT CITADEL — THE GLITCH HUNTER (Gate-Level Stability)
# ============================================================================
# FILE:     test_glitch.py
# PURPOSE:  Gate-level glitch detection for the S1-90 Sentinel Lock.
# TARGET:   IHP 130nm SG13G2 (Tiny Tapeout 06 / IHP26a)
# MODE:     Gate-Level Simulation ONLY (GL_TEST=1)
# TASK:     TASK VIII - Detect transient spikes during key transitions
# ============================================================================
#
# EXECUTION:
#   cd test && make -B GATES=yes COCOTB_TEST_MODULES=test_glitch
#
# WHAT IT DOES:
#   In RTL, signals change instantly. In silicon, they wobble. If the lock
#   output glitches to "Verified" (0xC1) for even 1 nanosecond during a
#   transition between two wrong keys, the Citadel is breached.
#
#   This test drives ui_in from 0x00 to 0xFF in a loop while continuously
#   monitoring uo_out for ANY transition. If uo_out ever transitions to
#   0xC1 (Verified) when ui_in is NOT 0xB6, the test immediately fails.
#
# ============================================================================
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Edge, RisingEdge
from cocotb.utils import get_sim_time

# ============================================================================
# VAELIX MISSION CONSTANTS
# ============================================================================
VAELIX_KEY      = 0xB6   # The one true key: 1011_0110
SEG_LOCKED      = 0xC7   # 7-Segment 'L' (Active-LOW, Common Anode)
SEG_VERIFIED    = 0xC1   # 7-Segment 'U' (Active-LOW, Common Anode)
CLOCK_PERIOD_NS = 40     # 25 MHz = 40ns period


# ============================================================================
# RESET HELPER
# ============================================================================
async def reset_sentinel(dut):
    """Reset the Sentinel and wait for stabilization."""
    dut.rst_n.value = 0
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)


# ============================================================================
# COCOTB TEST: GLITCH HUNTER
# ============================================================================
@cocotb.test()
async def test_glitch_hunter(dut):
    """
    TASK VIII: THE GLITCH HUNTER (Gate-Level Stability)
    
    Scenario:
    - Drive ui_in from 0x00 to 0xFF in a loop
    - Monitor uo_out for ANY edge/transition
    - Assert: If uo_out transitions to 0xC1 (Verified) when ui_in is NOT 0xB6,
      immediately fail the test
    - Catch transient spikes that last less than 1 clock cycle
    - Log the exact picosecond timestamp of any glitch
    """
    dut._log.info("="*72)
    dut._log.info("VAELIX SENTINEL | TASK VIII: THE GLITCH HUNTER")
    dut._log.info("Gate-Level Stability Test — Transient Spike Detection")
    dut._log.info("="*72)
    
    # Start clock
    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())
    
    # Reset the design
    await reset_sentinel(dut)
    
    dut._log.info("Starting glitch monitoring loop...")
    dut._log.info(f"Valid key: {hex(VAELIX_KEY)}")
    dut._log.info(f"Verified pattern: {hex(SEG_VERIFIED)}")
    dut._log.info("")
    
    # Flag to track if a glitch was detected
    glitch_detected = False
    glitch_info = []
    
    # Create a monitoring coroutine that watches for edges on uo_out
    async def glitch_monitor():
        """
        Continuously monitor uo_out for any edge/transition.
        If uo_out transitions to 0xC1 when ui_in != 0xB6, flag as glitch.
        """
        nonlocal glitch_detected, glitch_info
        
        while True:
            # Wait for ANY edge (rising or falling) on uo_out
            await Edge(dut.uo_out)
            
            # Get current values immediately after edge
            current_output = int(dut.uo_out.value)
            current_input = int(dut.ui_in.value)
            
            # Get the current simulation time in picoseconds
            timestamp_ps = get_sim_time('ps')
            timestamp_ns = get_sim_time('ns')
            
            # Check if output is VERIFIED (0xC1)
            if current_output == SEG_VERIFIED:
                # If input is NOT the valid key, this is a glitch!
                if current_input != VAELIX_KEY:
                    glitch_detected = True
                    glitch_info.append({
                        'timestamp_ps': timestamp_ps,
                        'timestamp_ns': timestamp_ns,
                        'input': current_input,
                        'output': current_output
                    })
                    
                    dut._log.error("="*72)
                    dut._log.error("🚨 GLITCH DETECTED! CITADEL BREACHED! 🚨")
                    dut._log.error("="*72)
                    dut._log.error(f"Timestamp: {timestamp_ps} ps ({timestamp_ns} ns)")
                    dut._log.error(f"Input (ui_in): {hex(current_input)} (Expected ONLY {hex(VAELIX_KEY)})")
                    dut._log.error(f"Output (uo_out): {hex(current_output)} (VERIFIED - UNAUTHORIZED!)")
                    dut._log.error("="*72)
                    
                    # Immediately fail the test
                    assert False, \
                        f"GLITCH BREACH at {timestamp_ps} ps: " \
                        f"uo_out={hex(current_output)} (VERIFIED) " \
                        f"when ui_in={hex(current_input)} (NOT {hex(VAELIX_KEY)})"
    
    # Start the glitch monitor as a background coroutine
    monitor_task = cocotb.start_soon(glitch_monitor())
    
    try:
        # Main test loop: Drive ui_in through all 256 possible values
        dut._log.info("Sweeping ui_in from 0x00 to 0xFF...")
        dut._log.info("Monitoring for transient VERIFIED (0xC1) spikes...")
        dut._log.info("")
        
        for key in range(256):
            # Set the input
            dut.ui_in.value = key
            
            # Wait for a clock cycle to allow the output to settle
            await ClockCycles(dut.clk, 1)
            
            # Log progress every 32 keys
            if key % 32 == 0:
                dut._log.info(f"  Progress: Testing key {hex(key)}... (no glitches detected so far)")
            
            # If a glitch was detected, the monitor will have already failed the test
            if glitch_detected:
                break
        
        # If we made it through the entire sweep without glitches
        if not glitch_detected:
            dut._log.info("")
            dut._log.info("="*72)
            dut._log.info("✓ GLITCH HUNTER: COMPLETE")
            dut._log.info("="*72)
            dut._log.info(f"✓ All 256 keys tested")
            dut._log.info(f"✓ Zero transient spikes detected")
            dut._log.info(f"✓ Gate-level stability: VERIFIED")
            dut._log.info("="*72)
    finally:
        # Clean up: Stop the monitor coroutine (ensures cleanup even on assertion failure)
        monitor_task.kill()
