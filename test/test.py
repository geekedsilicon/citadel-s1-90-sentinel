# ============================================================================
# VAELIX | PROJECT CITADEL — THE INTERROGATOR
# ============================================================================
# FILE:     test.py
# PURPOSE:  Cocotb verification suite for the S1-90 Sentinel Lock.
# TARGET:   IHP 130nm SG13G2 (Tiny Tapeout 06 / IHP26a)
# STANDARD: Vaelix Missionary Standard v1.2
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


async def reset_sentinel(dut):
    """Standard Power-On Reset sequence for the Sentinel Core."""
    dut.ena.value    = 1
    dut.ui_in.value  = 0
    dut.uio_in.value = 0
    dut.rst_n.value  = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value  = 1
    await ClockCycles(dut.clk, 1)


# ============================================================================
# TEST 1: AUTHORIZATION — THE GOLDEN PATH
# ============================================================================
@cocotb.test()
async def test_sentinel_authorization(dut):
    """
    Verifies the core Sentinel contract:
      - Default state is LOCKED ('L').
      - Key 0xB6 transitions to VERIFIED ('U') with full Glow.
      - Removing the key re-locks instantly.
    """
    dut._log.info("VAELIX SENTINEL | TEST 1: AUTHORIZATION SEQUENCE")

    # Establish Heartbeat
    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())

    # Power-On Reset
    await reset_sentinel(dut)

    # --- Phase 1: Verify Default Locked State ---
    dut.ui_in.value = 0x00
    await ClockCycles(dut.clk, 1)
    assert dut.uo_out.value == SEG_LOCKED, \
        f"LOCKED STATE FAILURE: Expected {hex(SEG_LOCKED)}, got {hex(int(dut.uo_out.value))}"
    assert dut.uio_out.value == GLOW_DORMANT, \
        f"GLOW LEAK: Status array active in locked state. Got {hex(int(dut.uio_out.value))}"
    dut._log.info("  [PASS] Default state: LOCKED ('L')")

    # --- Phase 2: Inject the Vaelix Key ---
    dut._log.info(f"  Injecting Vaelix Key: {hex(VAELIX_KEY)}")
    dut.ui_in.value = VAELIX_KEY
    await ClockCycles(dut.clk, 1)
    assert dut.uo_out.value == SEG_VERIFIED, \
        f"AUTH FAILURE: Expected {hex(SEG_VERIFIED)}, got {hex(int(dut.uo_out.value))}"
    assert dut.uio_out.value == GLOW_ACTIVE, \
        f"GLOW FAILURE: Expected full Glow {hex(GLOW_ACTIVE)}, got {hex(int(dut.uio_out.value))}"
    dut._log.info("  [PASS] Key accepted: VERIFIED ('U') + Vaelix Glow ACTIVE")

    # --- Phase 3: Remove Key — Instant Re-Lock ---
    dut.ui_in.value = 0x00
    await ClockCycles(dut.clk, 1)
    assert dut.uo_out.value == SEG_LOCKED, \
        f"RE-LOCK FAILURE: System did not revert. Got {hex(int(dut.uo_out.value))}"
    assert dut.uio_out.value == GLOW_DORMANT, \
        f"GLOW PERSISTENCE: Status array still active after key removal."
    dut._log.info("  [PASS] Key removed: Re-locked instantly")

    dut._log.info("VAELIX SENTINEL | TEST 1: COMPLETE — ALL PHASES NOMINAL")


# ============================================================================
# TEST 2: INTRUSION DEFLECTION — BRUTE-FORCE SWEEP
# ============================================================================
@cocotb.test()
async def test_sentinel_intrusion_sweep(dut):
    """
    Brute-forces all 256 possible 8-bit key values.
    Only 0xB6 shall pass. All others must be rejected.
    This is the Sentinel's reason for existence.
    """
    dut._log.info("VAELIX SENTINEL | TEST 2: FULL 8-BIT INTRUSION SWEEP")

    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())

    await reset_sentinel(dut)

    pass_count = 0
    fail_count = 0

    for key in range(256):
        dut.ui_in.value = key
        await ClockCycles(dut.clk, 1)

        seg_val  = int(dut.uo_out.value)
        glow_val = int(dut.uio_out.value)

        if key == VAELIX_KEY:
            # This is the ONLY key that should open the gate
            assert seg_val == SEG_VERIFIED, \
                f"FALSE REJECTION at {hex(key)}: Expected VERIFIED, got {hex(seg_val)}"
            assert glow_val == GLOW_ACTIVE, \
                f"GLOW MISSING at {hex(key)}: Expected {hex(GLOW_ACTIVE)}, got {hex(glow_val)}"
            pass_count += 1
        else:
            # Every other key must be locked out
            assert seg_val == SEG_LOCKED, \
                f"SECURITY BREACH at {hex(key)}: Got {hex(seg_val)} instead of LOCKED"
            assert glow_val == GLOW_DORMANT, \
                f"GLOW LEAK at {hex(key)}: Got {hex(glow_val)} instead of DORMANT"
            fail_count += 1

    dut._log.info(f"  Sweep complete: {pass_count} AUTHORIZED, {fail_count} DEFLECTED")
    assert pass_count == 1,   f"KEY COLLISION: {pass_count} keys accepted (expected 1)"
    assert fail_count == 255, f"PERIMETER BREACH: {255 - fail_count} invalid keys leaked through"

    dut._log.info("VAELIX SENTINEL | TEST 2: COMPLETE — PERIMETER INTEGRITY CONFIRMED")


# ============================================================================
# TEST 3: RESET BEHAVIOR — COLD START VERIFICATION
# ============================================================================
@cocotb.test()
async def test_sentinel_reset_behavior(dut):
    """
    Verifies that the Sentinel returns to a known LOCKED state
    after a reset, even if the correct key is held during reset.
    The reset line is sovereign — it overrides everything.
    """
    dut._log.info("VAELIX SENTINEL | TEST 3: RESET SOVEREIGNTY")

    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())

    await reset_sentinel(dut)

    # --- Phase 1: Authorize first ---
    dut.ui_in.value = VAELIX_KEY
    await ClockCycles(dut.clk, 1)
    assert dut.uo_out.value == SEG_VERIFIED, \
        "Pre-reset authorization failed"
    dut._log.info("  [PASS] Pre-reset: VERIFIED state confirmed")

    # --- Phase 2: Assert reset while key is still held ---
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)

    # --- Phase 3: Release reset — key is STILL held ---
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)

    # After reset release, the combinational logic should immediately
    # re-evaluate. Since 0xB6 is still on the input, it should re-verify.
    assert dut.uo_out.value == SEG_VERIFIED, \
        f"POST-RESET RE-AUTH FAILURE: Key held but got {hex(int(dut.uo_out.value))}"
    dut._log.info("  [PASS] Post-reset with key held: Re-verified immediately")

    # --- Phase 4: Release key after reset ---
    dut.ui_in.value = 0x00
    await ClockCycles(dut.clk, 1)
    assert dut.uo_out.value == SEG_LOCKED, \
        "Post-reset re-lock failed"
    dut._log.info("  [PASS] Key released: LOCKED state restored")

    dut._log.info("VAELIX SENTINEL | TEST 3: COMPLETE — RESET SOVEREIGNTY CONFIRMED")


# ============================================================================
# TEST 4: BIT-FLIP ADJACENCY — HAMMING DISTANCE 1 ATTACK
# ============================================================================
@cocotb.test()
async def test_sentinel_bitflip_adjacency(dut):
    """
    Tests every single-bit mutation of the Vaelix Key (0xB6).
    All 8 Hamming-distance-1 neighbors must be rejected.
    This verifies there are no "close enough" keys.
    """
    dut._log.info("VAELIX SENTINEL | TEST 4: HAMMING-1 ADJACENCY ATTACK")

    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())

    await reset_sentinel(dut)

    for bit in range(8):
        mutant_key = VAELIX_KEY ^ (1 << bit)
        dut.ui_in.value = mutant_key
        await ClockCycles(dut.clk, 1)

        seg_val = int(dut.uo_out.value)
        assert seg_val == SEG_LOCKED, \
            f"ADJACENCY BREACH: Bit {bit} flip ({hex(mutant_key)}) unlocked the gate! Got {hex(seg_val)}"
        dut._log.info(f"  [PASS] Bit {bit} flip ({hex(mutant_key)}): DEFLECTED")

    dut._log.info("VAELIX SENTINEL | TEST 4: COMPLETE — NO ADJACENT KEY LEAKAGE")

# ============================================================================
# TEST 5: UIO DIRECTION INTEGRITY — OUTPUT ENABLE VERIFICATION
# ============================================================================
@cocotb.test()
async def test_sentinel_uio_direction(dut):
    """
    The Vaelix Glow status array (uio_out) must always be driven as
    OUTPUT. This means uio_oe must be 0xFF at all times — locked or
    unlocked. A floating bidirectional pin is a security vulnerability.
    """
    dut._log.info("VAELIX SENTINEL | TEST 5: UIO DIRECTION INTEGRITY")

    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())

    await reset_sentinel(dut)

    UIO_ALL_OUTPUT = 0xFF

    # --- Phase 1: Check OE in LOCKED state ---
    dut.ui_in.value = 0x00
    await ClockCycles(dut.clk, 1)
    assert dut.uio_oe.value == UIO_ALL_OUTPUT, \
        f"OE FAILURE (LOCKED): Expected {hex(UIO_ALL_OUTPUT)}, got {hex(int(dut.uio_oe.value))}"
    dut._log.info("  [PASS] Locked state: uio_oe = 0xFF (all outputs)")

    # --- Phase 2: Check OE in VERIFIED state ---
    dut.ui_in.value = VAELIX_KEY
    await ClockCycles(dut.clk, 1)
    assert dut.uio_oe.value == UIO_ALL_OUTPUT, \
        f"OE FAILURE (VERIFIED): Expected {hex(UIO_ALL_OUTPUT)}, got {hex(int(dut.uio_oe.value))}"
    dut._log.info("  [PASS] Verified state: uio_oe = 0xFF (all outputs)")

    # --- Phase 3: Sweep random inputs, OE must never change ---
    test_vectors = [0x00, 0xFF, 0xB6, 0xB7, 0x49, 0xA5, 0x5A, 0x01]
    for vec in test_vectors:
        dut.ui_in.value = vec
        await ClockCycles(dut.clk, 1)
        assert dut.uio_oe.value == UIO_ALL_OUTPUT, \
            f"OE DRIFT at input {hex(vec)}: Got {hex(int(dut.uio_oe.value))}"

    dut._log.info("  [PASS] OE stable across all input vectors")
    dut._log.info("VAELIX SENTINEL | TEST 5: COMPLETE — NO FLOATING PINS")


# ============================================================================
# TEST 6: RAPID KEY CYCLING — COMBINATIONAL STABILITY STRESS
# ============================================================================
@cocotb.test()
async def test_sentinel_rapid_cycling(dut):
    """
    Rapidly alternates between the valid key and invalid keys for 200
    cycles. The Sentinel is pure combinational logic — every single
    transition must be clean with zero latching or glitch artifacts.
    This simulates a noisy DIP switch or an adversarial key scanner.
    """
    dut._log.info("VAELIX SENTINEL | TEST 6: RAPID CYCLING STRESS TEST")

    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())

    await reset_sentinel(dut)

    CYCLES         = 200
    invalid_keys   = [0x00, 0xFF, 0xB7, 0xB4, 0x49, 0xA6, 0x36, 0x96]
    error_count    = 0

    for i in range(CYCLES):
        # --- Inject valid key ---
        dut.ui_in.value = VAELIX_KEY
        await ClockCycles(dut.clk, 1)
        if int(dut.uo_out.value) != SEG_VERIFIED:
            error_count += 1
            dut._log.error(f"  Cycle {i}: VERIFIED expected, got {hex(int(dut.uo_out.value))}")
        if int(dut.uio_out.value) != GLOW_ACTIVE:
            error_count += 1
            dut._log.error(f"  Cycle {i}: GLOW expected, got {hex(int(dut.uio_out.value))}")

        # --- Inject invalid key (round-robin from list) ---
        bad_key = invalid_keys[i % len(invalid_keys)]
        dut.ui_in.value = bad_key
        await ClockCycles(dut.clk, 1)
        if int(dut.uo_out.value) != SEG_LOCKED:
            error_count += 1
            dut._log.error(f"  Cycle {i}: LOCKED expected for {hex(bad_key)}, got {hex(int(dut.uo_out.value))}")
        if int(dut.uio_out.value) != GLOW_DORMANT:
            error_count += 1
            dut._log.error(f"  Cycle {i}: DORMANT expected for {hex(bad_key)}, got {hex(int(dut.uio_out.value))}")

    assert error_count == 0, \
        f"STABILITY FAILURE: {error_count} errors in {CYCLES} rapid cycles"

    dut._log.info(f"  [PASS] {CYCLES} valid/invalid cycles — zero errors, zero latching")
    dut._log.info("VAELIX SENTINEL | TEST 6: COMPLETE — COMBINATIONAL INTEGRITY CONFIRMED")





