#!/usr/bin/env python3
# ============================================================================
# VAELIX | PROJECT CITADEL — TASK XV: KINGPIN LATCH TEST
# ============================================================================
# FILE:     test_tamper.py
# PURPOSE:  Verification suite for the tamper detection (BRICK state) logic.
# TARGET:   IHP 130nm SG13G2 (Tiny Tapeout 06 / IHP26a)
# AUTHOR:   Vaelix Systems R&D
# ============================================================================
#
# TEST OBJECTIVE:
# Verify that when any of the unused input pins uio_in[7:1] toggle
# (indicating potential debug probe activity), the device enters a
# BRICK state where it becomes unresponsive:
#   - uo_out driven to 8'h00 (All Dark)
#   - ui_in input logic disabled (no authorization possible)
#   - Only power cycle (ena toggle) can exit BRICK state
#
# ============================================================================
# SPDX-License-Identifier: Apache-2.0

import sys

# ============================================================================
# VAELIX MISSION CONSTANTS
# ============================================================================
VAELIX_KEY      = 0xB6   # The one true key: 1011_0110
SEG_LOCKED      = 0xC7   # 7-Segment 'L' (Active-LOW, Common Anode)
SEG_VERIFIED    = 0xC1   # 7-Segment 'U' (Active-LOW, Common Anode)
SEG_BRICK       = 0x00   # All Dark (BRICK state)
GLOW_ACTIVE     = 0xFF   # All status LEDs ignited
GLOW_DORMANT    = 0x00   # All status LEDs dark
CLOCK_PERIOD_NS = 40     # 25 MHz = 40ns period


# ============================================================================
# COCOTB TESTS
# ============================================================================
try:
    import cocotb
    from cocotb.clock import Clock
    from cocotb.triggers import ClockCycles
    COCOTB_AVAILABLE = True
except ImportError:
    COCOTB_AVAILABLE = False

if COCOTB_AVAILABLE:

    async def reset_sentinel(dut):
        """Standard Power-On Reset sequence for the Sentinel Core."""
        dut.ena.value    = 1
        dut.ui_in.value  = 0
        dut.uio_in.value = 0
        dut.rst_n.value  = 0
        await ClockCycles(dut.clk, 10)
        dut.rst_n.value  = 1
        await ClockCycles(dut.clk, 1)

    # ================================================================
    # TEST 1: TAMPER DETECTION — UIO[4] WIGGLE TEST
    # ================================================================
    @cocotb.test()
    async def test_tamper_detection_uio4(dut):
        """
        TEST 1: Wiggle uio_in[4] and verify device enters BRICK state.
        
        Sequence:
        1. Reset device to normal operation
        2. Verify normal authorization works
        3. Wiggle uio_in[4] (tamper event)
        4. Verify device enters BRICK state (uo_out = 0x00)
        5. Verify device ignores authorization key in BRICK state
        6. Verify soft reset (rst_n) cannot exit BRICK
        7. Verify power cycle (ena toggle) exits BRICK
        """
        dut._log.info("=" * 72)
        dut._log.info("TASK XV: KINGPIN LATCH — UIO[4] TAMPER TEST")
        dut._log.info("=" * 72)
        
        clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
        cocotb.start_soon(clock.start())
        await reset_sentinel(dut)

        # ----------------------------------------------------------------
        # Phase 1: Verify normal operation before tamper
        # ----------------------------------------------------------------
        dut._log.info("Phase 1: Verify normal operation")
        
        # Test locked state
        dut.ui_in.value = 0x00
        await ClockCycles(dut.clk, 2)
        assert int(dut.uo_out.value) == SEG_LOCKED, \
            f"Pre-tamper LOCKED check failed: expected {hex(SEG_LOCKED)}, got {hex(int(dut.uo_out.value))}"
        dut._log.info(f"  [PASS] Pre-tamper: LOCKED (uo_out = {hex(int(dut.uo_out.value))})")
        
        # Test verified state
        dut.ui_in.value = VAELIX_KEY
        await ClockCycles(dut.clk, 2)
        assert int(dut.uo_out.value) == SEG_VERIFIED, \
            f"Pre-tamper VERIFIED check failed: expected {hex(SEG_VERIFIED)}, got {hex(int(dut.uo_out.value))}"
        assert int(dut.uio_out.value) == GLOW_ACTIVE, \
            f"Pre-tamper GLOW check failed: expected {hex(GLOW_ACTIVE)}, got {hex(int(dut.uio_out.value))}"
        dut._log.info(f"  [PASS] Pre-tamper: VERIFIED + GLOW (uo_out = {hex(int(dut.uo_out.value))})")
        
        # Return to locked
        dut.ui_in.value = 0x00
        await ClockCycles(dut.clk, 2)
        
        # ----------------------------------------------------------------
        # Phase 2: Trigger tamper by wiggling uio_in[4]
        # ----------------------------------------------------------------
        dut._log.info("Phase 2: Trigger tamper by wiggling uio_in[4]")
        
        # Wiggle uio_in[4]: 0 -> 1
        dut.uio_in.value = 0x10  # Bit 4 set
        await ClockCycles(dut.clk, 2)
        
        # Device should now be in BRICK state
        brick_output = int(dut.uo_out.value)
        brick_glow = int(dut.uio_out.value)
        dut._log.info(f"  Post-tamper: uo_out = {hex(brick_output)}, uio_out = {hex(brick_glow)}")
        
        assert brick_output == SEG_BRICK, \
            f"BRICK state not entered: expected uo_out = {hex(SEG_BRICK)}, got {hex(brick_output)}"
        assert brick_glow == GLOW_DORMANT, \
            f"BRICK state glow incorrect: expected {hex(GLOW_DORMANT)}, got {hex(brick_glow)}"
        dut._log.info(f"  [PASS] BRICK state entered (All Dark: {hex(brick_output)})")
        
        # ----------------------------------------------------------------
        # Phase 3: Verify device is unresponsive in BRICK state
        # ----------------------------------------------------------------
        dut._log.info("Phase 3: Verify device ignores authorization in BRICK state")
        
        # Try to authorize with correct key — should be ignored
        dut.ui_in.value = VAELIX_KEY
        await ClockCycles(dut.clk, 2)
        
        brick_output_after_key = int(dut.uo_out.value)
        assert brick_output_after_key == SEG_BRICK, \
            f"BRICK state compromised: device responded to key! uo_out = {hex(brick_output_after_key)}"
        dut._log.info(f"  [PASS] Authorization key ignored in BRICK (uo_out = {hex(brick_output_after_key)})")
        
        # ----------------------------------------------------------------
        # Phase 4: Verify soft reset cannot exit BRICK state
        # ----------------------------------------------------------------
        dut._log.info("Phase 4: Verify soft reset (rst_n) cannot exit BRICK")
        
        dut.rst_n.value = 0
        await ClockCycles(dut.clk, 5)
        dut.rst_n.value = 1
        await ClockCycles(dut.clk, 2)
        
        brick_after_reset = int(dut.uo_out.value)
        assert brick_after_reset == SEG_BRICK, \
            f"BRICK state exited via soft reset! uo_out = {hex(brick_after_reset)}"
        dut._log.info(f"  [PASS] Soft reset ineffective (still BRICK: {hex(brick_after_reset)})")
        
        # ----------------------------------------------------------------
        # Phase 5: Verify power cycle (ena toggle) exits BRICK state
        # ----------------------------------------------------------------
        dut._log.info("Phase 5: Verify power cycle (ena toggle) exits BRICK")
        
        # Power cycle: ena 1 -> 0 -> 1
        dut.ena.value = 0
        await ClockCycles(dut.clk, 5)
        dut.ena.value = 1
        dut.uio_in.value = 0  # Clear tamper input
        dut.ui_in.value = 0   # Clear authorization input
        await ClockCycles(dut.clk, 5)
        
        # Device should return to normal LOCKED state
        post_cycle_output = int(dut.uo_out.value)
        assert post_cycle_output == SEG_LOCKED, \
            f"Power cycle recovery failed: expected {hex(SEG_LOCKED)}, got {hex(post_cycle_output)}"
        dut._log.info(f"  [PASS] Power cycle successful (LOCKED: {hex(post_cycle_output)})")
        
        # Verify normal authorization works again
        dut.ui_in.value = VAELIX_KEY
        await ClockCycles(dut.clk, 2)
        post_recovery = int(dut.uo_out.value)
        assert post_recovery == SEG_VERIFIED, \
            f"Post-recovery auth failed: expected {hex(SEG_VERIFIED)}, got {hex(post_recovery)}"
        dut._log.info(f"  [PASS] Post-recovery authorization works (VERIFIED: {hex(post_recovery)})")
        
        dut._log.info("=" * 72)
        dut._log.info("TEST 1: TAMPER DETECTION (UIO[4]) — COMPLETE")
        dut._log.info("=" * 72)

    # ================================================================
    # TEST 2: TAMPER DETECTION — SWEEP ALL UIO[7:1] PINS
    # ================================================================
    @cocotb.test()
    async def test_tamper_detection_all_pins(dut):
        """
        TEST 2: Verify all uio_in[7:1] pins trigger BRICK state.
        
        Test each pin individually to ensure complete coverage.
        """
        dut._log.info("=" * 72)
        dut._log.info("TASK XV: KINGPIN LATCH — ALL PINS SWEEP TEST")
        dut._log.info("=" * 72)
        
        clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
        cocotb.start_soon(clock.start())
        
        # Test each bit of uio_in[7:1]
        for bit_idx in range(1, 8):
            dut._log.info(f"Testing uio_in[{bit_idx}]...")
            
            # Power cycle to reset device to NORMAL state
            dut.ena.value = 0
            await ClockCycles(dut.clk, 3)
            dut.ena.value = 1
            dut.ui_in.value = 0
            dut.uio_in.value = 0
            dut.rst_n.value = 0
            await ClockCycles(dut.clk, 5)
            dut.rst_n.value = 1
            await ClockCycles(dut.clk, 2)
            
            # Verify normal operation
            pre_tamper = int(dut.uo_out.value)
            assert pre_tamper == SEG_LOCKED, \
                f"Bit {bit_idx}: Pre-tamper check failed (got {hex(pre_tamper)})"
            
            # Trigger tamper on this specific bit
            tamper_value = 1 << bit_idx
            dut.uio_in.value = tamper_value
            await ClockCycles(dut.clk, 2)
            
            # Verify BRICK state
            post_tamper = int(dut.uo_out.value)
            assert post_tamper == SEG_BRICK, \
                f"Bit {bit_idx}: BRICK not entered (got {hex(post_tamper)})"
            dut._log.info(f"  [PASS] uio_in[{bit_idx}] (mask={hex(tamper_value)}) triggered BRICK")
        
        dut._log.info("=" * 72)
        dut._log.info("TEST 2: ALL PINS SWEEP — COMPLETE")
        dut._log.info("=" * 72)

    # ================================================================
    # TEST 3: TAMPER DETECTION — UIO[0] IMMUNITY
    # ================================================================
    @cocotb.test()
    async def test_tamper_uio0_immunity(dut):
        """
        TEST 3: Verify uio_in[0] does NOT trigger BRICK state.
        
        Only uio_in[7:1] are monitored; uio_in[0] is not considered a tamper.
        """
        dut._log.info("=" * 72)
        dut._log.info("TASK XV: KINGPIN LATCH — UIO[0] IMMUNITY TEST")
        dut._log.info("=" * 72)
        
        clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
        cocotb.start_soon(clock.start())
        await reset_sentinel(dut)
        
        # Verify normal state
        dut.ui_in.value = 0x00
        await ClockCycles(dut.clk, 2)
        pre_check = int(dut.uo_out.value)
        assert pre_check == SEG_LOCKED
        dut._log.info(f"  [INFO] Pre-test: LOCKED ({hex(pre_check)})")
        
        # Toggle uio_in[0] — should NOT trigger BRICK
        dut.uio_in.value = 0x01  # Only bit 0 set
        await ClockCycles(dut.clk, 2)
        
        post_toggle = int(dut.uo_out.value)
        assert post_toggle == SEG_LOCKED, \
            f"uio_in[0] incorrectly triggered BRICK: got {hex(post_toggle)}"
        dut._log.info(f"  [PASS] uio_in[0] toggle ignored (still LOCKED: {hex(post_toggle)})")
        
        # Verify authorization still works
        dut.ui_in.value = VAELIX_KEY
        await ClockCycles(dut.clk, 2)
        verified = int(dut.uo_out.value)
        assert verified == SEG_VERIFIED, \
            f"Authorization broken by uio_in[0]: got {hex(verified)}"
        dut._log.info(f"  [PASS] Authorization still works (VERIFIED: {hex(verified)})")
        
        dut._log.info("=" * 72)
        dut._log.info("TEST 3: UIO[0] IMMUNITY — COMPLETE")
        dut._log.info("=" * 72)


# ============================================================================
# STANDALONE EXECUTION (SOFTWARE MODEL)
# ============================================================================
if __name__ == "__main__":
    if not COCOTB_AVAILABLE:
        print("=" * 72)
        print("TASK XV: KINGPIN LATCH — SOFTWARE MODEL TEST")
        print("=" * 72)
        print()
        print("NOTE: This test is designed for cocotb RTL simulation.")
        print("      To run: cd test && make COCOTB_TEST_MODULES=test_tamper")
        print()
        print("The tamper detection logic requires state machine simulation")
        print("and cannot be accurately modeled in pure Python.")
        print()
        print("=" * 72)
        sys.exit(0)
