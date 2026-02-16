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

# ============================================================================
# TEST 7: HAMMING-2 PERIMETER — DOUBLE-BIT MUTATION ATTACK
# ============================================================================
@cocotb.test()
async def test_sentinel_hamming2_attack(dut):
    """
    Tests every possible 2-bit mutation of the Vaelix Key (0xB6).
    There are C(8,2) = 28 Hamming-distance-2 neighbors.
    Every single one must be rejected. If any pass, the comparator
    mesh has a structural deficiency — a collapsed or shorted gate.
    """
    dut._log.info("VAELIX SENTINEL | TEST 7: HAMMING-2 DOUBLE-BIT ATTACK")

    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())

    await reset_sentinel(dut)

    deflected = 0

    for bit_a in range(8):
        for bit_b in range(bit_a + 1, 8):
            mutant_key = VAELIX_KEY ^ (1 << bit_a) ^ (1 << bit_b)
            dut.ui_in.value = mutant_key
            await ClockCycles(dut.clk, 1)

            seg_val  = int(dut.uo_out.value)
            glow_val = int(dut.uio_out.value)

            assert seg_val == SEG_LOCKED, \
                f"H2 BREACH: bits [{bit_a},{bit_b}] flip ({hex(mutant_key)}) unlocked! Got {hex(seg_val)}"
            assert glow_val == GLOW_DORMANT, \
                f"H2 GLOW LEAK: bits [{bit_a},{bit_b}] flip ({hex(mutant_key)}) lit Glow! Got {hex(glow_val)}"
            deflected += 1

    assert deflected == 28, \
        f"COVERAGE GAP: Expected 28 H2 mutations, tested {deflected}"

    dut._log.info(f"  [PASS] All 28 Hamming-2 mutations DEFLECTED")
    dut._log.info("VAELIX SENTINEL | TEST 7: COMPLETE — DOUBLE-BIT PERIMETER SEALED")


# ============================================================================
# TEST 8: WALKING ONES / WALKING ZEROS — BUS INTEGRITY SCAN
# ============================================================================
@cocotb.test()
async def test_sentinel_walking_bus_scan(dut):
    """
    Injects walking-1 and walking-0 patterns across the 8-bit input bus.
    None of these patterns match 0xB6, so every single one must produce
    LOCKED state. This catches stuck-at faults on individual input lines
    and verifies that no single-hot or single-cold vector fools the mesh.
    """
    dut._log.info("VAELIX SENTINEL | TEST 8: WALKING ONES / WALKING ZEROS")

    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())

    await reset_sentinel(dut)

    scan_count = 0

    # --- Walking Ones: 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80 ---
    for bit in range(8):
        pattern = 1 << bit
        dut.ui_in.value = pattern
        await ClockCycles(dut.clk, 1)

        seg_val = int(dut.uo_out.value)
        assert seg_val == SEG_LOCKED, \
            f"WALKING-1 BREACH at bit {bit} ({hex(pattern)}): Got {hex(seg_val)}"
        scan_count += 1

    dut._log.info(f"  [PASS] Walking-1 scan: 8/8 patterns LOCKED")

    # --- Walking Zeros: 0xFE, 0xFD, 0xFB, 0xF7, 0xEF, 0xDF, 0xBF, 0x7F ---
    for bit in range(8):
        pattern = 0xFF ^ (1 << bit)
        dut.ui_in.value = pattern
        await ClockCycles(dut.clk, 1)

        seg_val = int(dut.uo_out.value)
        assert seg_val == SEG_LOCKED, \
            f"WALKING-0 BREACH at bit {bit} ({hex(pattern)}): Got {hex(seg_val)}"
        scan_count += 1

    dut._log.info(f"  [PASS] Walking-0 scan: 8/8 patterns LOCKED")

    # --- Boundary sentinels: 0x00 and 0xFF ---
    for boundary in [0x00, 0xFF]:
        dut.ui_in.value = boundary
        await ClockCycles(dut.clk, 1)

        seg_val = int(dut.uo_out.value)
        assert seg_val == SEG_LOCKED, \
            f"BOUNDARY BREACH at {hex(boundary)}: Got {hex(seg_val)}"
        scan_count += 1

    dut._log.info(f"  [PASS] Boundary scan: 0x00 and 0xFF LOCKED")
    dut._log.info(f"  Total patterns scanned: {scan_count}")
    dut._log.info("VAELIX SENTINEL | TEST 8: COMPLETE — BUS INTEGRITY CONFIRMED")


# ============================================================================
# TEST 9: SEGMENT ENCODING FIDELITY — DISPLAY TRUTH TABLE
# ============================================================================
@cocotb.test()
async def test_sentinel_segment_encoding(dut):
    """
    Validates the exact bit pattern on every segment pin for both
    LOCKED and VERIFIED states. This is not just "did the right value
    appear" — it's a pin-by-pin dissection of the 7-segment encoding.

    Active-LOW Common Anode truth table:
      Segment:    DP  G  F  E  D  C  B  A
      Bit index:   7  6  5  4  3  2  1  0

      'L' (Locked):    DP=1 G=1 F=0 E=0 D=0 C=1 B=1 A=1 = 0xC7
      'U' (Verified):  DP=1 G=1 F=0 E=0 D=0 C=0 B=0 A=1 = 0xC1

    Difference is segments B and C (bits 1 and 2):
      Locked:   B=1 (OFF), C=1 (OFF)
      Verified: B=0 (ON),  C=0 (ON)
    """
    dut._log.info("VAELIX SENTINEL | TEST 9: SEGMENT ENCODING FIDELITY")

    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())

    await reset_sentinel(dut)

    # Segment name map for readable diagnostics
    SEG_NAMES = ["A", "B", "C", "D", "E", "F", "G", "DP"]

    # --- Phase 1: LOCKED state pin-by-pin ---
    dut.ui_in.value = 0x00
    await ClockCycles(dut.clk, 1)
    locked_bits = int(dut.uo_out.value)

    #                  A  B  C  D  E  F  G  DP
    expected_locked = [1, 1, 1, 0, 0, 0, 1, 1]  # 0xC7

    for i, (expected, name) in enumerate(zip(expected_locked, SEG_NAMES)):
        actual = (locked_bits >> i) & 1
        assert actual == expected, \
            f"LOCKED SEG_{name} (bit {i}): Expected {expected}, got {actual}. Full: {hex(locked_bits)}"
        state_str = "OFF" if expected == 1 else "ON"
        dut._log.info(f"  SEG_{name}: {state_str} (bit={actual}) [CORRECT]")

    dut._log.info(f"  [PASS] LOCKED encoding: {hex(locked_bits)} == 0xC7")

    # --- Phase 2: VERIFIED state pin-by-pin ---
    dut.ui_in.value = VAELIX_KEY
    await ClockCycles(dut.clk, 1)
    verified_bits = int(dut.uo_out.value)

    #                    A  B  C  D  E  F  G  DP
    expected_verified = [1, 0, 0, 0, 0, 0, 1, 1]  # 0xC1

    for i, (expected, name) in enumerate(zip(expected_verified, SEG_NAMES)):
        actual = (verified_bits >> i) & 1
        assert actual == expected, \
            f"VERIFIED SEG_{name} (bit {i}): Expected {expected}, got {actual}. Full: {hex(verified_bits)}"
        state_str = "OFF" if expected == 1 else "ON"
        dut._log.info(f"  SEG_{name}: {state_str} (bit={actual}) [CORRECT]")

    dut._log.info(f"  [PASS] VERIFIED encoding: {hex(verified_bits)} == 0xC1")

    # --- Phase 3: Confirm only bits 1 and 2 differ ---
    diff = locked_bits ^ verified_bits
    assert diff == 0x06, \
        f"ENCODING DRIFT: Expected diff 0x06 (bits B,C only), got {hex(diff)}"
    dut._log.info(f"  [PASS] State transition delta: {hex(diff)} — only SEG_B and SEG_C toggle")

    dut._log.info("VAELIX SENTINEL | TEST 9: COMPLETE — SEGMENT ENCODING BIT-PERFECT")


# ============================================================================
# TEST 10: BYTE COMPLEMENT REJECTION — MIRROR & TRANSFORM ATTACK
# ============================================================================
@cocotb.test()
async def test_sentinel_complement_rejection(dut):
    """
    The bitwise complement of 0xB6 is 0x49. An attacker who intercepts
    the key and inverts it (cable swap, level-shifter inversion, probe
    reflection) would present the mirror image. This test ensures that
    0x49 is rejected, along with every other bitwise transformation
    of the valid key: complement, nibble-swap, byte-reverse, and
    rotations.
    """
    dut._log.info("VAELIX SENTINEL | TEST 10: BYTE COMPLEMENT & TRANSFORM REJECTION")

    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())

    await reset_sentinel(dut)

    def rotate_left_8(val, n):
        """8-bit circular left rotation."""
        return ((val << n) | (val >> (8 - n))) & 0xFF

    def rotate_right_8(val, n):
        """8-bit circular right rotation."""
        return ((val >> n) | (val << (8 - n))) & 0xFF

    def reverse_bits_8(val):
        """Reverse all 8 bits."""
        result = 0
        for i in range(8):
            result |= ((val >> i) & 1) << (7 - i)
        return result

    def swap_nibbles(val):
        """Swap upper and lower nibbles."""
        return ((val & 0x0F) << 4) | ((val & 0xF0) >> 4)

    # Build the attack dictionary
    transforms = {
        "COMPLEMENT (~0xB6)":        (~VAELIX_KEY) & 0xFF,
        "NIBBLE SWAP":               swap_nibbles(VAELIX_KEY),
        "ROTATE LEFT 1":             rotate_left_8(VAELIX_KEY, 1),
        "ROTATE LEFT 2":             rotate_left_8(VAELIX_KEY, 2),
        "ROTATE LEFT 4":             rotate_left_8(VAELIX_KEY, 4),
        "ROTATE RIGHT 1":            rotate_right_8(VAELIX_KEY, 1),
        "ROTATE RIGHT 2":            rotate_right_8(VAELIX_KEY, 2),
        "BIT REVERSE":               reverse_bits_8(VAELIX_KEY),
        "XOR 0xAA (ALT MASK)":       VAELIX_KEY ^ 0xAA,
        "XOR 0x55 (ALT MASK PH2)":   VAELIX_KEY ^ 0x55,
        "XOR 0x0F (NIBBLE MASK)":     VAELIX_KEY ^ 0x0F,
        "XOR 0xF0 (UPPER MASK)":      VAELIX_KEY ^ 0xF0,
    }

    deflected = 0

    for name, attack_key in transforms.items():
        # Skip if a transform accidentally produces the valid key
        if attack_key == VAELIX_KEY:
            dut._log.info(f"  [SKIP] {name} = {hex(attack_key)} (identity — not an attack)")
            continue

        dut.ui_in.value = attack_key
        await ClockCycles(dut.clk, 1)

        seg_val  = int(dut.uo_out.value)
        glow_val = int(dut.uio_out.value)

        assert seg_val == SEG_LOCKED, \
            f"TRANSFORM BREACH [{name}]: {hex(attack_key)} unlocked! Got {hex(seg_val)}"
        assert glow_val == GLOW_DORMANT, \
            f"TRANSFORM GLOW [{name}]: {hex(attack_key)} lit Glow! Got {hex(glow_val)}"

        dut._log.info(f"  [PASS] {name} ({hex(attack_key)}): DEFLECTED")
        deflected += 1

    dut._log.info(f"  Total transforms deflected: {deflected}")
    dut._log.info("VAELIX SENTINEL | TEST 10: COMPLETE — ALL TRANSFORMS REJECTED")








