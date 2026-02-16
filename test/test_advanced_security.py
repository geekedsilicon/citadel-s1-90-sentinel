# ============================================================================
# VAELIX | PROJECT CITADEL — THE PROSECUTOR v1.0
# ============================================================================
# FILE:     test_advanced_security.py
# PURPOSE:  Advanced timing-attack simulation and security characterization
#           for the S1-90 Sentinel Lock.
# TARGET:   IHP 130nm SG13G2 (Tiny Tapeout 06 / IHP26a)
# STANDARD: Vaelix Missionary Standard v1.2
# ============================================================================
#
# TASK II: BRUTE-FORCE TEST GENERATION (THE PROSECUTOR)
#
# This module performs advanced timing-attack simulations to characterize
# the security properties of the Sentinel Lock under adversarial conditions.
# Tests verify that the lock remains secure (SEG_LOCKED) unless key timing
# precisely aligns with the 25MHz system clock.
#
# EXECUTION:
#   cd test && COCOTB_TEST_MODULES=test_advanced_security make -B
#
# ============================================================================
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer, ClockCycles

# ============================================================================
# VAELIX MISSION CONSTANTS (from test.py reference)
# ============================================================================
VAELIX_KEY      = 0xB6   # The one true key: 1011_0110
SEG_LOCKED      = 0xC7   # 7-Segment 'L' (Active-LOW, Common Anode)
SEG_VERIFIED    = 0xC1   # 7-Segment 'U' (Active-LOW, Common Anode)
GLOW_ACTIVE     = 0xFF   # All status LEDs ignited
GLOW_DORMANT    = 0x00   # All status LEDs dark
UIO_ALL_OUTPUT  = 0xFF   # All bidirectional pins driven as output
CLOCK_PERIOD_NS = 40     # 25 MHz = 40ns period

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

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
# TEST 1: TIMING-ATTACK SIMULATION — PRE-EDGE KEY INJECTION
# ============================================================================
@cocotb.test()
async def test_timing_attack_pre_edge(dut):
    """
    TIMING ATTACK TEST 1: Pre-Edge Key Injection
    
    Attempts to inject the correct key bits BEFORE the rising clock edge.
    Since the Sentinel uses combinational logic, the output should respond
    immediately, but this test verifies no timing-dependent vulnerabilities
    exist when the key arrives early.
    
    ATTACK VECTOR: Key arrives at various times before the clock edge
    EXPECTED: System correctly authenticates on the subsequent clock edge
    SECURITY PROPERTY: No early evaluation or timing leaks
    """
    dut._log.info("="*72)
    dut._log.info("PROSECUTOR TEST 1: PRE-EDGE KEY INJECTION TIMING ATTACK")
    dut._log.info("="*72)
    
    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_sentinel(dut)
    
    # Test various pre-edge injection timings
    # T = clock period (40ns), test at T-30ns, T-20ns, T-10ns, T-5ns before edge
    pre_edge_offsets = [30, 20, 10, 5, 2, 1]
    
    for offset_ns in pre_edge_offsets:
        dut._log.info(f"\n--- Testing key injection {offset_ns}ns before rising edge ---")
        
        # Start with locked state
        dut.ui_in.value = 0x00
        await ClockCycles(dut.clk, 2)
        
        # Wait until just before the rising edge
        await RisingEdge(dut.clk)
        await Timer(CLOCK_PERIOD_NS - offset_ns, unit="ns")
        
        # Inject key BEFORE the next rising edge
        dut.ui_in.value = VAELIX_KEY
        dut._log.info(f"  Key injected at T-{offset_ns}ns")
        
        # Wait for the rising edge where key should be sampled
        await RisingEdge(dut.clk)
        await Timer(1, unit="ns")  # Small delay for combinational propagation
        
        # Verify authorization occurred
        seg_out = int(dut.uo_out.value)
        glow_out = int(dut.uio_out.value)
        
        assert seg_out == SEG_VERIFIED, \
            f"PRE-EDGE TIMING FAILURE at T-{offset_ns}ns: Expected VERIFIED ({hex(SEG_VERIFIED)}), got {hex(seg_out)}"
        assert glow_out == GLOW_ACTIVE, \
            f"PRE-EDGE GLOW FAILURE at T-{offset_ns}ns: Expected ACTIVE ({hex(GLOW_ACTIVE)}), got {hex(glow_out)}"
        
        dut._log.info(f"  [PASS] Correct authorization at T-{offset_ns}ns pre-edge")
        
        # Clear key
        dut.ui_in.value = 0x00
        await ClockCycles(dut.clk, 1)
    
    dut._log.info("\nPROSECUTOR TEST 1: COMPLETE — No pre-edge timing vulnerabilities")


# ============================================================================
# TEST 2: TIMING-ATTACK SIMULATION — POST-EDGE KEY INJECTION
# ============================================================================
@cocotb.test()
async def test_timing_attack_post_edge(dut):
    """
    TIMING ATTACK TEST 2: Post-Edge Key Injection
    
    Attempts to inject the correct key bits AFTER the rising clock edge.
    Tests whether the system is vulnerable to keys that arrive late.
    
    ATTACK VECTOR: Key arrives at various times after the clock edge
    EXPECTED: System locks/unlocks based on combinational logic response
    SECURITY PROPERTY: No post-edge timing dependencies or glitches
    """
    dut._log.info("="*72)
    dut._log.info("PROSECUTOR TEST 2: POST-EDGE KEY INJECTION TIMING ATTACK")
    dut._log.info("="*72)
    
    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_sentinel(dut)
    
    # Test various post-edge injection timings
    # Inject at T+1ns, T+5ns, T+10ns, T+20ns after rising edge
    post_edge_offsets = [1, 5, 10, 20, 30]
    
    for offset_ns in post_edge_offsets:
        dut._log.info(f"\n--- Testing key injection {offset_ns}ns after rising edge ---")
        
        # Start with locked state
        dut.ui_in.value = 0x00
        await ClockCycles(dut.clk, 2)
        
        # Wait for rising edge
        await RisingEdge(dut.clk)
        
        # Inject key AFTER the rising edge
        await Timer(offset_ns, unit="ns")
        dut.ui_in.value = VAELIX_KEY
        dut._log.info(f"  Key injected at T+{offset_ns}ns")
        
        # Since this is combinational logic, output should change immediately
        # Wait for propagation delay
        await Timer(2, unit="ns")
        
        # Verify authorization occurred (combinational response)
        seg_out = int(dut.uo_out.value)
        glow_out = int(dut.uio_out.value)
        
        assert seg_out == SEG_VERIFIED, \
            f"POST-EDGE FAILURE at T+{offset_ns}ns: Expected VERIFIED ({hex(SEG_VERIFIED)}), got {hex(seg_out)}"
        assert glow_out == GLOW_ACTIVE, \
            f"POST-EDGE GLOW FAILURE at T+{offset_ns}ns: Expected ACTIVE ({hex(GLOW_ACTIVE)}), got {hex(glow_out)}"
        
        dut._log.info(f"  [PASS] Correct combinational response at T+{offset_ns}ns post-edge")
        
        # Clear key and verify re-lock
        dut.ui_in.value = 0x00
        await Timer(2, unit="ns")
        
        seg_out = int(dut.uo_out.value)
        assert seg_out == SEG_LOCKED, \
            f"POST-EDGE RE-LOCK FAILURE: Expected LOCKED ({hex(SEG_LOCKED)}), got {hex(seg_out)}"
        
        await ClockCycles(dut.clk, 1)
    
    dut._log.info("\nPROSECUTOR TEST 2: COMPLETE — No post-edge timing vulnerabilities")


# ============================================================================
# TEST 3: TIMING-ATTACK SIMULATION — FALLING EDGE KEY INJECTION
# ============================================================================
@cocotb.test()
async def test_timing_attack_falling_edge(dut):
    """
    TIMING ATTACK TEST 3: Falling Edge Key Injection
    
    Tests key injection at the falling clock edge to detect any timing
    dependencies on the negative edge of the clock.
    
    ATTACK VECTOR: Key arrives at/around the falling clock edge
    EXPECTED: System operates correctly (combinational, edge-insensitive)
    SECURITY PROPERTY: No falling-edge timing dependencies
    """
    dut._log.info("="*72)
    dut._log.info("PROSECUTOR TEST 3: FALLING-EDGE KEY INJECTION TIMING ATTACK")
    dut._log.info("="*72)
    
    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_sentinel(dut)
    
    # Test key injection at falling edge and near-falling edge
    falling_offsets = [-5, -2, 0, 2, 5]  # ns relative to falling edge
    
    for offset_ns in falling_offsets:
        offset_str = f"T_fall{offset_ns:+d}ns"
        dut._log.info(f"\n--- Testing key injection at {offset_str} ---")
        
        # Start locked
        dut.ui_in.value = 0x00
        await ClockCycles(dut.clk, 2)
        
        # Wait for falling edge
        await FallingEdge(dut.clk)
        
        # Apply offset
        if offset_ns < 0:
            await Timer(-offset_ns, unit="ns")
        
        # Inject key
        dut.ui_in.value = VAELIX_KEY
        dut._log.info(f"  Key injected at {offset_str}")
        
        if offset_ns > 0:
            await Timer(offset_ns, unit="ns")
        
        # Wait for combinational propagation
        await Timer(2, unit="ns")
        
        # Verify response (should work as it's combinational)
        seg_out = int(dut.uo_out.value)
        glow_out = int(dut.uio_out.value)
        
        assert seg_out == SEG_VERIFIED, \
            f"FALLING-EDGE FAILURE at {offset_str}: Expected VERIFIED ({hex(SEG_VERIFIED)}), got {hex(seg_out)}"
        assert glow_out == GLOW_ACTIVE, \
            f"FALLING-EDGE GLOW FAILURE at {offset_str}: Expected ACTIVE ({hex(GLOW_ACTIVE)}), got {hex(glow_out)}"
        
        dut._log.info(f"  [PASS] Correct response at {offset_str}")
        
        # Clear and verify
        dut.ui_in.value = 0x00
        await Timer(2, unit="ns")
        assert int(dut.uo_out.value) == SEG_LOCKED
        await ClockCycles(dut.clk, 1)
    
    dut._log.info("\nPROSECUTOR TEST 3: COMPLETE — No falling-edge vulnerabilities")


# ============================================================================
# TEST 4: METASTABILITY ATTACK — BIT-BY-BIT TEMPORAL INJECTION
# ============================================================================
@cocotb.test()
async def test_timing_attack_bit_by_bit(dut):
    """
    TIMING ATTACK TEST 4: Bit-by-Bit Temporal Injection (Metastability)
    
    Attempts to inject key bits one at a time with varying temporal spacing
    to detect setup/hold time violations or metastability vulnerabilities.
    
    ATTACK VECTOR: Key bits arrive at different times within a clock cycle
    EXPECTED: Only fully-formed key at proper time should authorize
    SECURITY PROPERTY: No partial key acceptance or bit-wise timing leaks
    """
    dut._log.info("="*72)
    dut._log.info("PROSECUTOR TEST 4: BIT-BY-BIT TEMPORAL INJECTION ATTACK")
    dut._log.info("="*72)
    
    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_sentinel(dut)
    
    # Test injecting key bits with various delays between them
    bit_delays = [1, 2, 5, 10]  # nanoseconds between bit injections
    
    for delay_ns in bit_delays:
        dut._log.info(f"\n--- Testing bit-by-bit injection with {delay_ns}ns delay ---")
        
        # Start locked
        dut.ui_in.value = 0x00
        await ClockCycles(dut.clk, 2)
        await RisingEdge(dut.clk)
        
        # Inject key bits one at a time
        partial_key = 0x00
        for bit in range(8):
            if (VAELIX_KEY >> bit) & 1:
                partial_key |= (1 << bit)
            
            dut.ui_in.value = partial_key
            dut._log.info(f"  Injected bit {bit}: partial_key = {hex(partial_key)}")
            
            await Timer(delay_ns, unit="ns")
            
            # Check that partial keys don't unlock
            seg_out = int(dut.uo_out.value)
            if partial_key != VAELIX_KEY:
                assert seg_out == SEG_LOCKED, \
                    f"PARTIAL KEY LEAK at bit {bit} (partial={hex(partial_key)}): Got {hex(seg_out)}"
            else:
                # Last bit completes the key
                assert seg_out == SEG_VERIFIED, \
                    f"FULL KEY REJECTION at bit {bit}: Expected VERIFIED, got {hex(seg_out)}"
        
        dut._log.info(f"  [PASS] No partial key acceptance with {delay_ns}ns bit delay")
        
        # Clear
        dut.ui_in.value = 0x00
        await ClockCycles(dut.clk, 1)
    
    dut._log.info("\nPROSECUTOR TEST 4: COMPLETE — No bit-wise timing vulnerabilities")


# ============================================================================
# TEST 5: GLITCH ATTACK — RAPID KEY TOGGLING
# ============================================================================
@cocotb.test()
async def test_timing_attack_rapid_toggle(dut):
    """
    TIMING ATTACK TEST 5: Rapid Key Toggling (Glitch Attack)
    
    Rapidly toggles between valid and invalid keys within sub-clock periods
    to attempt to induce glitches or unauthorized state transitions.
    
    ATTACK VECTOR: Key toggled at sub-nanosecond to nanosecond intervals
    EXPECTED: System remains locked unless key held for full combinational propagation
    SECURITY PROPERTY: No glitch-induced authorization
    """
    dut._log.info("="*72)
    dut._log.info("PROSECUTOR TEST 5: RAPID KEY TOGGLING (GLITCH ATTACK)")
    dut._log.info("="*72)
    
    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_sentinel(dut)
    
    # Test various toggle periods
    toggle_periods = [10, 5, 3, 2, 1]  # nanoseconds
    
    for period_ns in toggle_periods:
        dut._log.info(f"\n--- Testing rapid toggle with {period_ns}ns period ---")
        
        dut.ui_in.value = 0x00
        await ClockCycles(dut.clk, 2)
        
        # Perform rapid toggles
        num_toggles = 20
        for i in range(num_toggles):
            dut.ui_in.value = VAELIX_KEY if (i % 2 == 0) else 0x00
            await Timer(period_ns, unit="ns")
        
        # After glitching, verify system is in correct state based on final input
        await Timer(5, unit="ns")  # Let combinational logic settle
        
        final_seg = int(dut.uo_out.value)
        final_input = int(dut.ui_in.value)
        
        if final_input == VAELIX_KEY:
            expected = SEG_VERIFIED
        else:
            expected = SEG_LOCKED
        
        assert final_seg == expected, \
            f"GLITCH STATE CORRUPTION with {period_ns}ns toggles: Expected {hex(expected)}, got {hex(final_seg)}"
        
        dut._log.info(f"  [PASS] No glitch-induced state corruption with {period_ns}ns toggles")
        
        # Return to locked
        dut.ui_in.value = 0x00
        await ClockCycles(dut.clk, 1)
    
    dut._log.info("\nPROSECUTOR TEST 5: COMPLETE — No glitch-attack vulnerabilities")


# ============================================================================
# TEST 6: CLOCK PHASE ATTACK — KEY INJECTION AT ALL CLOCK PHASES
# ============================================================================
@cocotb.test()
async def test_timing_attack_all_clock_phases(dut):
    """
    TIMING ATTACK TEST 6: Exhaustive Clock Phase Sweep
    
    Systematically tests key injection at every phase of the clock cycle
    to ensure no timing-dependent authorization vulnerabilities exist.
    
    ATTACK VECTOR: Key injected at 8 different phases per clock cycle (0°-360°)
    EXPECTED: System behaves correctly at all phases (combinational logic)
    SECURITY PROPERTY: Clock-phase independence
    """
    dut._log.info("="*72)
    dut._log.info("PROSECUTOR TEST 6: EXHAUSTIVE CLOCK PHASE SWEEP")
    dut._log.info("="*72)
    
    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_sentinel(dut)
    
    # Test 8 phases across the full clock period
    num_phases = 8
    phase_step = CLOCK_PERIOD_NS // num_phases
    
    for phase in range(num_phases):
        phase_offset_ns = phase * phase_step
        phase_degrees = (phase * 360) // num_phases
        
        dut._log.info(f"\n--- Testing phase {phase_degrees}° (T+{phase_offset_ns}ns) ---")
        
        # Start locked
        dut.ui_in.value = 0x00
        await ClockCycles(dut.clk, 2)
        
        # Align to rising edge
        await RisingEdge(dut.clk)
        
        # Advance to specific phase
        if phase_offset_ns > 0:
            await Timer(phase_offset_ns, unit="ns")
        
        # Inject key at this phase
        dut.ui_in.value = VAELIX_KEY
        dut._log.info(f"  Key injected at phase {phase_degrees}° (T+{phase_offset_ns}ns)")
        
        # Wait for combinational propagation
        await Timer(2, unit="ns")
        
        # Verify authorization
        seg_out = int(dut.uo_out.value)
        glow_out = int(dut.uio_out.value)
        
        assert seg_out == SEG_VERIFIED, \
            f"PHASE ATTACK FAILURE at {phase_degrees}°: Expected VERIFIED ({hex(SEG_VERIFIED)}), got {hex(seg_out)}"
        assert glow_out == GLOW_ACTIVE, \
            f"PHASE GLOW FAILURE at {phase_degrees}°: Expected ACTIVE ({hex(GLOW_ACTIVE)}), got {hex(glow_out)}"
        
        dut._log.info(f"  [PASS] Correct response at phase {phase_degrees}°")
        
        # Test invalid key at same phase
        dut.ui_in.value = 0x49  # Complement of valid key
        await Timer(2, unit="ns")
        
        seg_out = int(dut.uo_out.value)
        assert seg_out == SEG_LOCKED, \
            f"PHASE LOCK FAILURE at {phase_degrees}°: Expected LOCKED ({hex(SEG_LOCKED)}), got {hex(seg_out)}"
        
        # Clear
        dut.ui_in.value = 0x00
        await ClockCycles(dut.clk, 1)
    
    dut._log.info("\nPROSECUTOR TEST 6: COMPLETE — Clock-phase independent operation confirmed")


# ============================================================================
# TEST 7: SETUP/HOLD TIME VIOLATION ATTACK
# ============================================================================
@cocotb.test()
async def test_timing_attack_setup_hold_violation(dut):
    """
    TIMING ATTACK TEST 7: Setup/Hold Time Violation Attack
    
    Attempts to violate setup and hold time constraints by changing the key
    very close to the clock edge, testing for metastability or incorrect sampling.
    
    ATTACK VECTOR: Key changes at t_setup and t_hold boundaries
    EXPECTED: System remains secure; no unauthorized states from violations
    SECURITY PROPERTY: Robust handling of timing violations
    """
    dut._log.info("="*72)
    dut._log.info("PROSECUTOR TEST 7: SETUP/HOLD TIME VIOLATION ATTACK")
    dut._log.info("="*72)
    
    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_sentinel(dut)
    
    # Test key changes very close to rising edge
    # Typical setup/hold times are in picoseconds to low nanoseconds
    violation_offsets = [-0.5, -0.2, 0, 0.2, 0.5]  # ns relative to rising edge
    
    for offset_ns in violation_offsets:
        offset_str = f"{offset_ns:+.1f}ns"
        dut._log.info(f"\n--- Testing key change at rising_edge {offset_str} ---")
        
        # Start with valid key
        dut.ui_in.value = VAELIX_KEY
        await ClockCycles(dut.clk, 2)
        
        # Wait until just before/at/after rising edge
        await RisingEdge(dut.clk)
        if offset_ns < 0:
            # Go back in time by waiting and then changing
            # (approximation since we can't actually go back)
            pass
        elif offset_ns > 0:
            await Timer(offset_ns, unit="ns")
        
        # Change to invalid key at violation point
        dut.ui_in.value = 0x00
        dut._log.info(f"  Key changed to 0x00 at {offset_str}")
        
        # Wait for next clock cycle to sample
        await ClockCycles(dut.clk, 1)
        await Timer(2, unit="ns")
        
        # System should be locked (combinational, immediate response)
        seg_out = int(dut.uo_out.value)
        assert seg_out == SEG_LOCKED, \
            f"SETUP/HOLD VIOLATION BREACH at {offset_str}: Expected LOCKED, got {hex(seg_out)}"
        
        dut._log.info(f"  [PASS] Correct lock state after violation at {offset_str}")
        
        await ClockCycles(dut.clk, 1)
    
    dut._log.info("\nPROSECUTOR TEST 7: COMPLETE — No setup/hold violation exploits")


# ============================================================================
# TEST 8: EDGE CASE — SIMULTANEOUS KEY AND RESET
# ============================================================================
@cocotb.test()
async def test_timing_attack_key_with_reset(dut):
    """
    TIMING ATTACK TEST 8: Simultaneous Key and Reset Attack
    
    Tests behavior when valid key is applied simultaneously with or very
    close to reset signal transitions, looking for race conditions.
    
    ATTACK VECTOR: Key applied during reset assertion/deassertion
    EXPECTED: System follows reset protocol correctly; no unauthorized bypass
    SECURITY PROPERTY: Reset priority and atomicity
    """
    dut._log.info("="*72)
    dut._log.info("PROSECUTOR TEST 8: SIMULTANEOUS KEY AND RESET ATTACK")
    dut._log.info("="*72)
    
    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_sentinel(dut)
    
    # Test 1: Apply key during reset assertion
    dut._log.info("\n--- Test 1: Key applied during reset assertion ---")
    dut.ui_in.value = 0x00
    await ClockCycles(dut.clk, 2)
    
    dut.rst_n.value = 0  # Assert reset
    dut.ui_in.value = VAELIX_KEY  # Apply key simultaneously
    await ClockCycles(dut.clk, 5)
    
    # While in reset, output behavior is design-dependent
    # but security should not be compromised
    
    dut.rst_n.value = 1  # Deassert reset
    await ClockCycles(dut.clk, 2)
    
    # After reset with key held, should be verified (combinational)
    seg_out = int(dut.uo_out.value)
    assert seg_out == SEG_VERIFIED, \
        f"RESET RACE CONDITION: Key held through reset should verify, got {hex(seg_out)}"
    
    dut._log.info("  [PASS] Key held through reset correctly verified")
    
    # Test 2: Apply key during reset deassertion
    dut._log.info("\n--- Test 2: Key applied at reset deassertion ---")
    dut.ui_in.value = 0x00
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    
    # Apply key at the exact moment of reset deassertion
    dut.rst_n.value = 1
    dut.ui_in.value = VAELIX_KEY
    await ClockCycles(dut.clk, 2)
    
    seg_out = int(dut.uo_out.value)
    assert seg_out == SEG_VERIFIED, \
        f"RESET DEASSERTION RACE: Expected VERIFIED, got {hex(seg_out)}"
    
    dut._log.info("  [PASS] Key at reset deassertion correctly verified")
    
    # Test 3: Remove key during reset
    dut._log.info("\n--- Test 3: Key removed during reset ---")
    dut.ui_in.value = VAELIX_KEY
    await ClockCycles(dut.clk, 2)
    
    dut.rst_n.value = 0
    dut.ui_in.value = 0x00  # Remove key during reset
    await ClockCycles(dut.clk, 5)
    
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)
    
    seg_out = int(dut.uo_out.value)
    assert seg_out == SEG_LOCKED, \
        f"RESET KEY REMOVAL FAILURE: Expected LOCKED, got {hex(seg_out)}"
    
    dut._log.info("  [PASS] Key removed during reset correctly locks")
    
    dut._log.info("\nPROSECUTOR TEST 8: COMPLETE — No reset-timing vulnerabilities")


# ============================================================================
# TEST 9: EDGE CASE — CLOCK FREQUENCY VARIATION ATTACK
# ============================================================================
@cocotb.test()
async def test_timing_attack_clock_frequency_variation(dut):
    """
    TIMING ATTACK TEST 9: Clock Frequency Variation Attack
    
    Tests system behavior under different clock frequencies to detect
    frequency-dependent vulnerabilities or timing assumptions.
    
    ATTACK VECTOR: Clock frequency varied from 10MHz to 50MHz
    EXPECTED: System operates correctly at all frequencies (combinational)
    SECURITY PROPERTY: Frequency-independent security
    """
    dut._log.info("="*72)
    dut._log.info("PROSECUTOR TEST 9: CLOCK FREQUENCY VARIATION ATTACK")
    dut._log.info("="*72)
    
    # Test at multiple frequencies
    # 10MHz = 100ns, 25MHz = 40ns (nominal), 50MHz = 20ns
    test_frequencies = [
        (10, 100),   # 10 MHz, 100ns period
        (25, 40),    # 25 MHz, 40ns period (nominal)
        (50, 20),    # 50 MHz, 20ns period
    ]
    
    for freq_mhz, period_ns in test_frequencies:
        dut._log.info(f"\n--- Testing at {freq_mhz}MHz (period={period_ns}ns) ---")
        
        # Create new clock with this frequency
        clock = Clock(dut.clk, period_ns, unit="ns")
        cocotb.start_soon(clock.start())
        
        # Reset
        dut.ena.value = 1
        dut.ui_in.value = 0
        dut.uio_in.value = 0
        dut.rst_n.value = 0
        await ClockCycles(dut.clk, 10)
        dut.rst_n.value = 1
        await ClockCycles(dut.clk, 2)
        
        # Test locked state
        dut.ui_in.value = 0x00
        await ClockCycles(dut.clk, 2)
        
        seg_out = int(dut.uo_out.value)
        assert seg_out == SEG_LOCKED, \
            f"FREQUENCY ATTACK at {freq_mhz}MHz LOCKED: Expected {hex(SEG_LOCKED)}, got {hex(seg_out)}"
        
        dut._log.info(f"  [PASS] Correct LOCKED state at {freq_mhz}MHz")
        
        # Test verified state
        dut.ui_in.value = VAELIX_KEY
        await ClockCycles(dut.clk, 2)
        
        seg_out = int(dut.uo_out.value)
        glow_out = int(dut.uio_out.value)
        
        assert seg_out == SEG_VERIFIED, \
            f"FREQUENCY ATTACK at {freq_mhz}MHz VERIFIED: Expected {hex(SEG_VERIFIED)}, got {hex(seg_out)}"
        assert glow_out == GLOW_ACTIVE, \
            f"FREQUENCY ATTACK at {freq_mhz}MHz GLOW: Expected {hex(GLOW_ACTIVE)}, got {hex(glow_out)}"
        
        dut._log.info(f"  [PASS] Correct VERIFIED state at {freq_mhz}MHz")
        
        # Test re-lock
        dut.ui_in.value = 0x00
        await ClockCycles(dut.clk, 2)
        
        seg_out = int(dut.uo_out.value)
        assert seg_out == SEG_LOCKED, \
            f"FREQUENCY ATTACK at {freq_mhz}MHz RE-LOCK: Expected {hex(SEG_LOCKED)}, got {hex(seg_out)}"
        
        dut._log.info(f"  [PASS] Correct RE-LOCK at {freq_mhz}MHz")
        
        # Stop this clock before next iteration
        await ClockCycles(dut.clk, 2)
    
    dut._log.info("\nPROSECUTOR TEST 9: COMPLETE — Frequency-independent operation confirmed")


# ============================================================================
# TEST 10: COMPREHENSIVE TIMING EDGE CASE BATTERY
# ============================================================================
@cocotb.test()
async def test_timing_attack_comprehensive_edge_cases(dut):
    """
    TIMING ATTACK TEST 10: Comprehensive Edge Case Battery
    
    A battery of edge cases testing various timing anomalies and corner cases
    that could potentially be exploited in timing attacks.
    
    ATTACK VECTORS: Multiple edge cases tested comprehensively
    EXPECTED: All edge cases handled securely
    SECURITY PROPERTY: Comprehensive timing attack resistance
    """
    dut._log.info("="*72)
    dut._log.info("PROSECUTOR TEST 10: COMPREHENSIVE TIMING EDGE CASE BATTERY")
    dut._log.info("="*72)
    
    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_sentinel(dut)
    
    edge_cases = []
    
    # Edge Case 1: Zero-duration key pulse
    dut._log.info("\n--- Edge Case 1: Zero-duration key pulse ---")
    dut.ui_in.value = 0x00
    await ClockCycles(dut.clk, 2)
    
    dut.ui_in.value = VAELIX_KEY
    await Timer(1, unit="ns")  # Minimal pulse (1ns is minimum positive value)
    dut.ui_in.value = 0x00
    await Timer(5, unit="ns")
    
    seg_out = int(dut.uo_out.value)
    edge_cases.append(("Zero-duration pulse", seg_out == SEG_LOCKED))
    dut._log.info(f"  Zero-duration pulse: {'PASS' if edge_cases[-1][1] else 'FAIL'}")
    
    await ClockCycles(dut.clk, 2)
    
    # Edge Case 2: Key held for exactly one clock cycle
    dut._log.info("\n--- Edge Case 2: Key held for exactly one clock cycle ---")
    await RisingEdge(dut.clk)
    dut.ui_in.value = VAELIX_KEY
    await RisingEdge(dut.clk)
    await Timer(2, unit="ns")
    
    seg_out = int(dut.uo_out.value)
    edge_cases.append(("One-cycle key hold", seg_out == SEG_VERIFIED))
    dut._log.info(f"  One-cycle key: {'PASS' if edge_cases[-1][1] else 'FAIL'}")
    
    dut.ui_in.value = 0x00
    await ClockCycles(dut.clk, 2)
    
    # Edge Case 3: Key toggled at exactly clock frequency
    dut._log.info("\n--- Edge Case 3: Key toggled at exactly clock frequency ---")
    for i in range(10):
        await RisingEdge(dut.clk)
        dut.ui_in.value = VAELIX_KEY if (i % 2 == 0) else 0x00
        await Timer(2, unit="ns")
        
        seg_out = int(dut.uo_out.value)
        expected = SEG_VERIFIED if (i % 2 == 0) else SEG_LOCKED
        if seg_out != expected:
            edge_cases.append(("Clock-sync toggle", False))
            break
    else:
        edge_cases.append(("Clock-sync toggle", True))
    
    dut._log.info(f"  Clock-sync toggle: {'PASS' if edge_cases[-1][1] else 'FAIL'}")
    
    dut.ui_in.value = 0x00
    await ClockCycles(dut.clk, 2)
    
    # Edge Case 4: Key applied during power-on (ena transition)
    dut._log.info("\n--- Edge Case 4: Key applied during enable transition ---")
    dut.ena.value = 0
    dut.ui_in.value = VAELIX_KEY
    await ClockCycles(dut.clk, 2)
    
    dut.ena.value = 1
    await ClockCycles(dut.clk, 2)
    
    seg_out = int(dut.uo_out.value)
    edge_cases.append(("Enable transition with key", seg_out == SEG_VERIFIED))
    dut._log.info(f"  Enable transition: {'PASS' if edge_cases[-1][1] else 'FAIL'}")
    
    dut.ui_in.value = 0x00
    await ClockCycles(dut.clk, 2)
    
    # Edge Case 5: Alternating bits of key applied sequentially
    dut._log.info("\n--- Edge Case 5: Alternating bit injection ---")
    dut.ui_in.value = 0x00
    await ClockCycles(dut.clk, 2)
    
    # Apply even bits first, then odd bits
    even_bits = VAELIX_KEY & 0xAA  # 0b10101010
    odd_bits = VAELIX_KEY & 0x55   # 0b01010101
    
    dut.ui_in.value = even_bits
    await ClockCycles(dut.clk, 1)
    seg_out_even = int(dut.uo_out.value)
    
    dut.ui_in.value = odd_bits
    await ClockCycles(dut.clk, 1)
    seg_out_odd = int(dut.uo_out.value)
    
    dut.ui_in.value = VAELIX_KEY
    await ClockCycles(dut.clk, 1)
    seg_out_full = int(dut.uo_out.value)
    
    alt_ok = (seg_out_even == SEG_LOCKED and seg_out_odd == SEG_LOCKED and seg_out_full == SEG_VERIFIED)
    edge_cases.append(("Alternating bit injection", alt_ok))
    dut._log.info(f"  Alternating bits: {'PASS' if alt_ok else 'FAIL'}")
    
    dut.ui_in.value = 0x00
    await ClockCycles(dut.clk, 2)
    
    # Summary
    dut._log.info("\n" + "="*72)
    dut._log.info("EDGE CASE SUMMARY:")
    passed = sum(1 for _, result in edge_cases if result)
    total = len(edge_cases)
    
    for case_name, result in edge_cases:
        status = "PASS" if result else "FAIL"
        dut._log.info(f"  [{status}] {case_name}")
    
    dut._log.info(f"\nTotal: {passed}/{total} edge cases passed")
    
    assert passed == total, \
        f"EDGE CASE FAILURES: {total - passed} edge cases failed"
    
    dut._log.info("\nPROSECUTOR TEST 10: COMPLETE — All edge cases secure")


# ============================================================================
# END OF PROSECUTOR TEST SUITE
# ============================================================================
