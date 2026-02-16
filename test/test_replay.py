# ============================================================================
# VAELIX | PROJECT CITADEL — REPLAY ATTACK DEFENSE TEST SUITE
# ============================================================================
# FILE:     test_replay.py
# PURPOSE:  Cocotb verification suite for Replay Attack Defense (Time-Window)
# TARGET:   IHP 130nm SG13G2 (Tiny Tapeout 06 / IHP26a)
# TASK:     TASK XXII - THE FLIPPER TRAP
# ============================================================================
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

# ============================================================================
# VAELIX MISSION CONSTANTS
# ============================================================================
VAELIX_KEY      = 0xB6   # The one true key: 1011_0110
SEG_LOCKED      = 0xC7   # 7-Segment 'L' (Active-LOW, Common Anode)
SEG_VERIFIED    = 0xC1   # 7-Segment 'U' (Active-LOW, Common Anode)
GLOW_ACTIVE     = 0xFF   # All status LEDs ignited
GLOW_DORMANT    = 0x00   # All status LEDs dark
CLOCK_PERIOD_NS = 40     # 25 MHz = 40ns period
LOCKOUT_TIME_S  = 10     # Lockout duration in seconds
LOCKOUT_CYCLES  = int(LOCKOUT_TIME_S * 25_000_000)  # At 25 MHz


async def reset_sentinel(dut):
    """Standard Power-On Reset sequence for the Sentinel Core."""
    dut.ena.value    = 0
    dut.ui_in.value  = 0
    dut.uio_in.value = 0
    dut.rst_n.value  = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value  = 1
    await ClockCycles(dut.clk, 5)


# ============================================================================
# COCOTB TEST 1: VALID KEY IN TIME WINDOW (Cycles 3-5)
# ============================================================================
@cocotb.test()
async def test_replay_valid_timing_cycle3(dut):
    """Test that the key is accepted when entered at cycle 3"""
    dut._log.info("REPLAY TEST 1: VALID KEY AT CYCLE 3")
    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_sentinel(dut)
    
    # Start with no key
    dut.ui_in.value = 0x00
    
    # Raise ena to start timing
    dut.ena.value = 1
    await ClockCycles(dut.clk, 1)  # Cycle 0: ena rising edge detected
    
    # Wait until cycle 3 (we're at cycle 1 after ena, so wait 2 more)
    await ClockCycles(dut.clk, 2)  # Now at cycle 3
    
    # Present the key at cycle 3
    dut.ui_in.value = VAELIX_KEY
    await ClockCycles(dut.clk, 1)
    
    # Check authorization
    assert int(dut.uo_out.value) == SEG_VERIFIED, \
        f"Key at cycle 3 rejected! Expected {hex(SEG_VERIFIED)}, got {hex(int(dut.uo_out.value))}"
    assert int(dut.uio_out.value) == GLOW_ACTIVE
    dut._log.info("  [PASS] Key accepted at cycle 3")


@cocotb.test()
async def test_replay_valid_timing_cycle4(dut):
    """Test that the key is accepted when entered at cycle 4"""
    dut._log.info("REPLAY TEST 2: VALID KEY AT CYCLE 4")
    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_sentinel(dut)
    
    # Start with no key
    dut.ui_in.value = 0x00
    
    # Raise ena
    dut.ena.value = 1
    await ClockCycles(dut.clk, 1)  # Cycle 0
    
    # Wait until cycle 4
    await ClockCycles(dut.clk, 3)  # Now at cycle 4
    
    # Present the key
    dut.ui_in.value = VAELIX_KEY
    await ClockCycles(dut.clk, 1)
    
    # Check authorization
    assert int(dut.uo_out.value) == SEG_VERIFIED, \
        f"Key at cycle 4 rejected!"
    assert int(dut.uio_out.value) == GLOW_ACTIVE
    dut._log.info("  [PASS] Key accepted at cycle 4")


@cocotb.test()
async def test_replay_valid_timing_cycle5(dut):
    """Test that the key is accepted when entered at cycle 5"""
    dut._log.info("REPLAY TEST 3: VALID KEY AT CYCLE 5")
    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_sentinel(dut)
    
    # Start with no key
    dut.ui_in.value = 0x00
    
    # Raise ena
    dut.ena.value = 1
    await ClockCycles(dut.clk, 1)  # Cycle 0
    
    # Wait until cycle 5
    await ClockCycles(dut.clk, 4)  # Now at cycle 5
    
    # Present the key
    dut.ui_in.value = VAELIX_KEY
    await ClockCycles(dut.clk, 1)
    
    # Check authorization
    assert int(dut.uo_out.value) == SEG_VERIFIED, \
        f"Key at cycle 5 rejected!"
    assert int(dut.uio_out.value) == GLOW_ACTIVE
    dut._log.info("  [PASS] Key accepted at cycle 5")


# ============================================================================
# COCOTB TEST 4: REPLAY ATTACK - IMMEDIATE (Cycle 0)
# ============================================================================
@cocotb.test()
async def test_replay_attack_immediate(dut):
    """Test that key present at cycle 0 triggers REPLAY_LOCKOUT"""
    dut._log.info("REPLAY TEST 4: IMMEDIATE REPLAY ATTACK (Cycle 0)")
    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_sentinel(dut)
    
    # Present key BEFORE raising ena (static signal / jammed pin)
    dut.ui_in.value = VAELIX_KEY
    
    # Raise ena with key already present
    dut.ena.value = 1
    await ClockCycles(dut.clk, 1)  # Cycle 0: ena rises, key already there
    
    # System should detect replay and enter REPLAY_LOCKOUT
    # Check that we're locked (not authorized)
    assert int(dut.uo_out.value) == SEG_LOCKED, \
        f"BREACH! Key accepted at cycle 0 (should be locked)"
    assert int(dut.uio_out.value) == GLOW_DORMANT
    dut._log.info("  [PASS] Immediate replay detected, system locked")
    
    # Try to present key again in valid window - should still be locked
    await ClockCycles(dut.clk, 3)  # Now at cycle 4
    dut.ui_in.value = 0x00
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = VAELIX_KEY
    await ClockCycles(dut.clk, 1)
    
    # Should still be locked
    assert int(dut.uo_out.value) == SEG_LOCKED, \
        f"BREACH! System unlocked during lockout"
    dut._log.info("  [PASS] System remains locked during replay lockout")


# ============================================================================
# COCOTB TEST 5: REPLAY ATTACK - TOO EARLY (Cycle 1-2)
# ============================================================================
@cocotb.test()
async def test_replay_attack_too_early(dut):
    """Test that key at cycle 1 or 2 is rejected (too early)"""
    dut._log.info("REPLAY TEST 5: KEY TOO EARLY (Cycle 1-2)")
    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_sentinel(dut)
    
    # Start with no key
    dut.ui_in.value = 0x00
    
    # Raise ena
    dut.ena.value = 1
    await ClockCycles(dut.clk, 1)  # Cycle 0
    
    # Present key at cycle 1 (too early)
    await ClockCycles(dut.clk, 1)  # Now at cycle 1
    dut.ui_in.value = VAELIX_KEY
    await ClockCycles(dut.clk, 1)
    
    # Should be locked (key too early)
    assert int(dut.uo_out.value) == SEG_LOCKED, \
        f"BREACH! Key accepted at cycle 1 (too early)"
    dut._log.info("  [PASS] Key at cycle 1 rejected")


# ============================================================================
# COCOTB TEST 6: REPLAY ATTACK - TOO LATE (Cycle 10+)
# ============================================================================
@cocotb.test()
async def test_replay_attack_too_late(dut):
    """Test that key at cycle 10 or later triggers REPLAY_LOCKOUT"""
    dut._log.info("REPLAY TEST 6: LATE REPLAY ATTACK (Cycle 10+)")
    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_sentinel(dut)
    
    # Start with no key
    dut.ui_in.value = 0x00
    
    # Raise ena
    dut.ena.value = 1
    await ClockCycles(dut.clk, 1)  # Cycle 0
    
    # Wait until cycle 10
    await ClockCycles(dut.clk, 10)  # Now at cycle 10
    
    # Present key at cycle 10 (too late, replay attack)
    dut.ui_in.value = VAELIX_KEY
    await ClockCycles(dut.clk, 1)
    
    # System should detect replay and enter REPLAY_LOCKOUT
    assert int(dut.uo_out.value) == SEG_LOCKED, \
        f"BREACH! Key accepted at cycle 10 (should trigger lockout)"
    assert int(dut.uio_out.value) == GLOW_DORMANT
    dut._log.info("  [PASS] Late replay detected, system locked")


# ============================================================================
# COCOTB TEST 7: REPLAY ATTACK - HELD CONSTANT
# ============================================================================
@cocotb.test()
async def test_replay_attack_constant_key(dut):
    """Test that a constant key held on the bus is detected as replay attack"""
    dut._log.info("REPLAY TEST 7: CONSTANT KEY REPLAY (Static Signal)")
    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_sentinel(dut)
    
    # Hold key constant from the start
    dut.ui_in.value = VAELIX_KEY
    await ClockCycles(dut.clk, 5)
    
    # Raise ena with key already held constant
    dut.ena.value = 1
    await ClockCycles(dut.clk, 10)
    
    # System should be locked (key was present at cycle 0)
    assert int(dut.uo_out.value) == SEG_LOCKED, \
        f"BREACH! Constant key accepted (replay attack)"
    assert int(dut.uio_out.value) == GLOW_DORMANT
    dut._log.info("  [PASS] Constant key detected as replay, system locked")


# ============================================================================
# COCOTB TEST 8: LOCKOUT DURATION (Simplified Test)
# ============================================================================
@cocotb.test()
async def test_replay_lockout_duration(dut):
    """Test that lockout lasts for the specified duration (simplified)"""
    dut._log.info("REPLAY TEST 8: LOCKOUT DURATION (Simplified)")
    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_sentinel(dut)
    
    # Trigger replay lockout (key at cycle 0)
    dut.ui_in.value = VAELIX_KEY
    dut.ena.value = 1
    await ClockCycles(dut.clk, 1)
    
    # Verify we're in lockout
    assert int(dut.uo_out.value) == SEG_LOCKED
    dut._log.info("  [INFO] Lockout triggered")
    
    # Remove the key
    dut.ui_in.value = 0x00
    
    # Wait a bit (not full 10 seconds for simulation time)
    # Test that we stay locked for a reasonable number of cycles
    await ClockCycles(dut.clk, 1000)
    assert int(dut.uo_out.value) == SEG_LOCKED
    dut._log.info("  [PASS] System remains locked during lockout period")
    
    # Note: Full 10-second test would take too long in simulation
    # The important thing is that we enter lockout and stay there


# ============================================================================
# COCOTB TEST 9: RECOVERY AFTER LOCKOUT
# ============================================================================
@cocotb.test()
async def test_replay_recovery_after_reset(dut):
    """Test that system recovers after reset"""
    dut._log.info("REPLAY TEST 9: RECOVERY AFTER RESET")
    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_sentinel(dut)
    
    # Trigger replay lockout
    dut.ui_in.value = VAELIX_KEY
    dut.ena.value = 1
    await ClockCycles(dut.clk, 1)
    
    # Verify lockout
    assert int(dut.uo_out.value) == SEG_LOCKED
    dut._log.info("  [INFO] Lockout triggered")
    
    # Reset the system
    await reset_sentinel(dut)
    
    # Try valid sequence
    dut.ui_in.value = 0x00
    dut.ena.value = 1
    await ClockCycles(dut.clk, 1)  # Cycle 0
    await ClockCycles(dut.clk, 3)  # Cycle 3
    dut.ui_in.value = VAELIX_KEY
    await ClockCycles(dut.clk, 1)
    
    # Should be authorized now
    assert int(dut.uo_out.value) == SEG_VERIFIED, \
        f"System didn't recover after reset"
    dut._log.info("  [PASS] System recovered after reset, valid key accepted")


# ============================================================================
# COCOTB TEST 10: BOUNDARY TEST - CYCLE 6 (Just Outside Window)
# ============================================================================
@cocotb.test()
async def test_replay_boundary_cycle6(dut):
    """Test that key at cycle 6 is rejected (just outside valid window)"""
    dut._log.info("REPLAY TEST 10: BOUNDARY TEST - CYCLE 6")
    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_sentinel(dut)
    
    # Start with no key
    dut.ui_in.value = 0x00
    
    # Raise ena
    dut.ena.value = 1
    await ClockCycles(dut.clk, 1)  # Cycle 0
    
    # Wait until cycle 6 (just after valid window)
    await ClockCycles(dut.clk, 5)  # Now at cycle 6
    
    # Present key at cycle 6
    dut.ui_in.value = VAELIX_KEY
    await ClockCycles(dut.clk, 1)
    
    # Should be locked (outside window, but not yet triggering lockout)
    assert int(dut.uo_out.value) == SEG_LOCKED, \
        f"BREACH! Key accepted at cycle 6 (outside valid window)"
    dut._log.info("  [PASS] Key at cycle 6 rejected (outside window)")
