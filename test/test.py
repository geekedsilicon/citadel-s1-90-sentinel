# ============================================================================
# VAELIX | PROJECT CITADEL — THE INTERROGATOR v2.0
# ============================================================================
# FILE:     test.py
# PURPOSE:  Cocotb verification suite for the S1-90 Sentinel Lock.
# TARGET:   IHP 130nm SG13G2 (Tiny Tapeout 06 / IHP26a)
# STANDARD: Vaelix Missionary Standard v1.2
# ============================================================================
#
# TWO EXECUTION MODES:
#   1. RTL SIMULATION:   cd test && make -B     (requires iverilog + cocotb)
#   2. STANDALONE MODEL: python test.py          (pure Python, no simulator)
#
# Mode 2 runs a software model of the Sentinel logic so you can validate
# the test suite anywhere — laptop, CI, Alpine, wherever. Every test
# prints verbose output to stdout.
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
GLOW_ACTIVE     = 0xFF   # All status LEDs ignited
GLOW_DORMANT    = 0x00   # All status LEDs dark
UIO_ALL_OUTPUT  = 0xFF   # All bidirectional pins driven as output
CLOCK_PERIOD_NS = 40     # 25 MHz = 40ns period


# ============================================================================
# ============================================================================
#
#   SECTION A: PURE PYTHON SOFTWARE MODEL
#   Runs with: python test.py
#
# ============================================================================
# ============================================================================

class SentinelModel:
    """
    Pure Python behavioral model of the Sentinel Lock.
    Mirrors the Verilog combinational logic exactly.
    """

    def __init__(self):
        self.ui_in   = 0x00
        self.uo_out  = SEG_LOCKED
        self.uio_out = GLOW_DORMANT
        self.uio_oe  = UIO_ALL_OUTPUT

    def evaluate(self, key_input):
        """Combinational: no clock needed. Input → Output, instant."""
        self.ui_in = key_input & 0xFF
        if self.ui_in == VAELIX_KEY:
            self.uo_out  = SEG_VERIFIED
            self.uio_out = GLOW_ACTIVE
        else:
            self.uo_out  = SEG_LOCKED
            self.uio_out = GLOW_DORMANT
        self.uio_oe = UIO_ALL_OUTPUT
        return self.uo_out, self.uio_out, self.uio_oe


# ============================================================================
# CONSOLE FORMATTING UTILITIES
# ============================================================================

class Console:
    """Terminal output with ANSI color codes for visibility."""

    BOLD    = "\033[1m"
    GREEN   = "\033[92m"
    RED     = "\033[91m"
    YELLOW  = "\033[93m"
    CYAN    = "\033[96m"
    MAGENTA = "\033[95m"
    DIM     = "\033[2m"
    RESET   = "\033[0m"

    @staticmethod
    def header(text):
        print(f"\n{Console.BOLD}{Console.CYAN}{'='*72}")
        print(f"  {text}")
        print(f"{'='*72}{Console.RESET}")

    @staticmethod
    def subheader(text):
        print(f"  {Console.BOLD}{Console.MAGENTA}--- {text} ---{Console.RESET}")

    @staticmethod
    def passed(text):
        print(f"  {Console.GREEN}  [PASS]{Console.RESET} {text}")

    @staticmethod
    def failed(text):
        print(f"  {Console.RED}  [FAIL]{Console.RESET} {text}")

    @staticmethod
    def info(text):
        print(f"  {Console.DIM}  [INFO]{Console.RESET} {text}")

    @staticmethod
    def skip(text):
        print(f"  {Console.YELLOW}  [SKIP]{Console.RESET} {text}")

    @staticmethod
    def result(test_name, passed_flag):
        if passed_flag:
            print(f"  {Console.GREEN}{Console.BOLD}  ✓ {test_name}: PASSED{Console.RESET}")
        else:
            print(f"  {Console.RED}{Console.BOLD}  ✗ {test_name}: FAILED{Console.RESET}")

    @staticmethod
    def banner():
        print(f"""
{Console.BOLD}{Console.CYAN}
  ██╗   ██╗ █████╗ ███████╗██╗     ██╗██╗  ██╗
  ██║   ██║██╔══██╗██╔════╝██║     ██║╚██╗██╔╝
  ██║   ██║███████║█████╗  ██║     ██║ ╚███╔╝
  ╚██╗ ██╔╝██╔══██║██╔══╝  ██║     ██║ ██╔██╗
   ╚████╔╝ ██║  ██║███████╗███████╗██║██╔╝ ██╗
    ╚═══╝  ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝╚═╝  ╚═╝
  SENTINEL INTERROGATOR v2.0 — Software Model
  Key: 0xB6 | Locked: 0xC7 ('L') | Verified: 0xC1 ('U')
{Console.RESET}""")


# ============================================================================
# STANDALONE TEST FUNCTIONS (Software Model)
# ============================================================================

def run_test_1():
    """TEST 1: AUTHORIZATION — THE GOLDEN PATH"""
    Console.header("TEST 1: AUTHORIZATION — THE GOLDEN PATH")
    s = SentinelModel()
    errors = 0

    # Phase 1: Default locked
    Console.subheader("Phase 1: Default Locked State")
    seg, glow, oe = s.evaluate(0x00)
    Console.info(f"Input: 0x00 → Segment: {hex(seg)}, Glow: {hex(glow)}")
    if seg == SEG_LOCKED and glow == GLOW_DORMANT:
        Console.passed(f"Default state: LOCKED ('L') = {hex(seg)}")
    else:
        Console.failed(f"Expected seg={hex(SEG_LOCKED)} glow={hex(GLOW_DORMANT)}, got seg={hex(seg)} glow={hex(glow)}")
        errors += 1

    # Phase 2: Inject key
    Console.subheader("Phase 2: Inject Vaelix Key (0xB6)")
    seg, glow, oe = s.evaluate(VAELIX_KEY)
    Console.info(f"Input: {hex(VAELIX_KEY)} → Segment: {hex(seg)}, Glow: {hex(glow)}")
    if seg == SEG_VERIFIED and glow == GLOW_ACTIVE:
        Console.passed(f"Key accepted: VERIFIED ('U') = {hex(seg)}, Glow = {hex(glow)}")
    else:
        Console.failed(f"Expected seg={hex(SEG_VERIFIED)} glow={hex(GLOW_ACTIVE)}, got seg={hex(seg)} glow={hex(glow)}")
        errors += 1

    # Phase 3: Remove key
    Console.subheader("Phase 3: Remove Key — Instant Re-Lock")
    seg, glow, oe = s.evaluate(0x00)
    Console.info(f"Input: 0x00 → Segment: {hex(seg)}, Glow: {hex(glow)}")
    if seg == SEG_LOCKED and glow == GLOW_DORMANT:
        Console.passed(f"Re-locked instantly: {hex(seg)}")
    else:
        Console.failed(f"System did not re-lock. Got seg={hex(seg)}")
        errors += 1

    Console.result("TEST 1: AUTHORIZATION", errors == 0)
    return errors == 0


def run_test_2():
    """TEST 2: INTRUSION DEFLECTION — BRUTE-FORCE SWEEP"""
    Console.header("TEST 2: INTRUSION DEFLECTION — FULL 256-KEY SWEEP")
    s = SentinelModel()
    pass_count = 0
    fail_count = 0
    breaches   = []

    for key in range(256):
        seg, glow, oe = s.evaluate(key)

        if key == VAELIX_KEY:
            if seg == SEG_VERIFIED and glow == GLOW_ACTIVE:
                pass_count += 1
                Console.passed(f"Key {hex(key)}: AUTHORIZED (correct)")
            else:
                breaches.append(key)
                Console.failed(f"Key {hex(key)}: Should be VERIFIED, got seg={hex(seg)}")
        else:
            if seg == SEG_LOCKED and glow == GLOW_DORMANT:
                fail_count += 1
            else:
                breaches.append(key)
                Console.failed(f"BREACH at {hex(key)}: seg={hex(seg)} glow={hex(glow)}")

    Console.info(f"Sweep results: {pass_count} authorized, {fail_count} deflected, {len(breaches)} breaches")

    if pass_count == 1 and fail_count == 255 and len(breaches) == 0:
        Console.passed(f"1/256 authorized, 255/256 deflected — PERIMETER SEALED")
    else:
        Console.failed(f"Breaches detected at: {[hex(k) for k in breaches]}")

    ok = pass_count == 1 and fail_count == 255
    Console.result("TEST 2: BRUTE-FORCE SWEEP", ok)
    return ok


def run_test_3():
    """TEST 3: RESET BEHAVIOR — COLD START VERIFICATION"""
    Console.header("TEST 3: RESET BEHAVIOR — COLD START VERIFICATION")
    s = SentinelModel()
    errors = 0

    # Authorize
    Console.subheader("Phase 1: Establish VERIFIED state")
    seg, glow, oe = s.evaluate(VAELIX_KEY)
    Console.info(f"Input: {hex(VAELIX_KEY)} → seg={hex(seg)}")
    if seg == SEG_VERIFIED:
        Console.passed("Pre-reset: VERIFIED confirmed")
    else:
        Console.failed(f"Pre-reset auth failed: {hex(seg)}")
        errors += 1

    # Simulate reset: re-init the model
    Console.subheader("Phase 2: Assert Reset (re-initialize model)")
    s = SentinelModel()
    Console.info(f"Model reset → seg={hex(s.uo_out)}, glow={hex(s.uio_out)}")
    if s.uo_out == SEG_LOCKED:
        Console.passed("Post-reset: LOCKED (default)")
    else:
        Console.failed(f"Post-reset not locked: {hex(s.uo_out)}")
        errors += 1

    # Re-inject key after reset
    Console.subheader("Phase 3: Re-inject Key After Reset")
    seg, glow, oe = s.evaluate(VAELIX_KEY)
    Console.info(f"Input: {hex(VAELIX_KEY)} → seg={hex(seg)}")
    if seg == SEG_VERIFIED:
        Console.passed("Post-reset re-auth: VERIFIED")
    else:
        Console.failed(f"Post-reset re-auth failed: {hex(seg)}")
        errors += 1

    # Release key
    Console.subheader("Phase 4: Release Key")
    seg, glow, oe = s.evaluate(0x00)
    if seg == SEG_LOCKED:
        Console.passed("Key released: LOCKED restored")
    else:
        Console.failed(f"Failed to re-lock: {hex(seg)}")
        errors += 1

    Console.result("TEST 3: RESET BEHAVIOR", errors == 0)
    return errors == 0


def run_test_4():
    """TEST 4: BIT-FLIP ADJACENCY — HAMMING DISTANCE 1 ATTACK"""
    Console.header("TEST 4: HAMMING-1 ADJACENCY ATTACK (8 single-bit flips)")
    s = SentinelModel()
    errors = 0

    Console.info(f"Valid key: {hex(VAELIX_KEY)} = {bin(VAELIX_KEY)}")
    Console.info(f"Testing all 8 single-bit mutations...")
    print()

    for bit in range(8):
        mutant = VAELIX_KEY ^ (1 << bit)
        seg, glow, oe = s.evaluate(mutant)

        flipped_str = bin(mutant)[2:].zfill(8)
        key_str     = bin(VAELIX_KEY)[2:].zfill(8)
        # Highlight the flipped bit
        diff_marker = "".join("^" if key_str[i] != flipped_str[i] else " " for i in range(8))

        Console.info(f"Bit {bit}: {hex(mutant)} ({flipped_str})")
        Console.info(f"         {' '*len(hex(mutant))} ({diff_marker}) ← flipped")

        if seg == SEG_LOCKED:
            Console.passed(f"Bit {bit} flip ({hex(mutant)}): DEFLECTED")
        else:
            Console.failed(f"Bit {bit} flip ({hex(mutant)}): UNLOCKED! seg={hex(seg)}")
            errors += 1

    Console.result("TEST 4: HAMMING-1 ADJACENCY", errors == 0)
    return errors == 0


def run_test_5():
    """TEST 5: UIO DIRECTION INTEGRITY — OUTPUT ENABLE VERIFICATION"""
    Console.header("TEST 5: UIO DIRECTION INTEGRITY (uio_oe must be 0xFF always)")
    s = SentinelModel()
    errors = 0

    test_vectors = [0x00, 0xFF, 0xB6, 0xB7, 0x49, 0xA5, 0x5A, 0x01, 0x80, 0x55, 0xAA, 0xFE]

    for vec in test_vectors:
        seg, glow, oe = s.evaluate(vec)
        state = "VERIFIED" if vec == VAELIX_KEY else "LOCKED"

        if oe == UIO_ALL_OUTPUT:
            Console.passed(f"Input {hex(vec):>4s} [{state:>8s}]: uio_oe = {hex(oe)} ✓")
        else:
            Console.failed(f"Input {hex(vec):>4s} [{state:>8s}]: uio_oe = {hex(oe)} (expected 0xFF)")
            errors += 1

    Console.result("TEST 5: UIO DIRECTION", errors == 0)
    return errors == 0


def run_test_6():
    """TEST 6: RAPID KEY CYCLING — COMBINATIONAL STABILITY STRESS"""
    Console.header("TEST 6: RAPID CYCLING STRESS (200 valid/invalid alternations)")
    s = SentinelModel()
    errors       = 0
    cycles       = 200
    invalid_keys = [0x00, 0xFF, 0xB7, 0xB4, 0x49, 0xA6, 0x36, 0x96]

    for i in range(cycles):
        # Valid key
        seg, glow, oe = s.evaluate(VAELIX_KEY)
        if seg != SEG_VERIFIED or glow != GLOW_ACTIVE:
            Console.failed(f"Cycle {i:>3d} VALID:   seg={hex(seg)} glow={hex(glow)}")
            errors += 1

        # Invalid key
        bad = invalid_keys[i % len(invalid_keys)]
        seg, glow, oe = s.evaluate(bad)
        if seg != SEG_LOCKED or glow != GLOW_DORMANT:
            Console.failed(f"Cycle {i:>3d} INVALID ({hex(bad)}): seg={hex(seg)} glow={hex(glow)}")
            errors += 1

    if errors == 0:
        Console.passed(f"{cycles} cycles — zero errors, zero latching")
    else:
        Console.failed(f"{errors} errors in {cycles} cycles")

    Console.result("TEST 6: RAPID CYCLING", errors == 0)
    return errors == 0


def run_test_7():
    """TEST 7: HAMMING-2 PERIMETER — DOUBLE-BIT MUTATION ATTACK"""
    Console.header("TEST 7: HAMMING-2 DOUBLE-BIT ATTACK (28 combinations)")
    s = SentinelModel()
    errors    = 0
    deflected = 0

    for bit_a in range(8):
        for bit_b in range(bit_a + 1, 8):
            mutant = VAELIX_KEY ^ (1 << bit_a) ^ (1 << bit_b)
            seg, glow, oe = s.evaluate(mutant)

            if seg == SEG_LOCKED and glow == GLOW_DORMANT:
                Console.passed(f"Bits [{bit_a},{bit_b}] → {hex(mutant)} ({bin(mutant)[2:].zfill(8)}): DEFLECTED")
                deflected += 1
            else:
                Console.failed(f"Bits [{bit_a},{bit_b}] → {hex(mutant)}: BREACH! seg={hex(seg)}")
                errors += 1

    Console.info(f"Total tested: {deflected + errors}, Deflected: {deflected}, Breached: {errors}")
    Console.result("TEST 7: HAMMING-2 ATTACK", errors == 0 and deflected == 28)
    return errors == 0


def run_test_8():
    """TEST 8: WALKING ONES / WALKING ZEROS — BUS INTEGRITY SCAN"""
    Console.header("TEST 8: WALKING ONES / WALKING ZEROS — BUS SCAN")
    s = SentinelModel()
    errors = 0

    # Walking Ones
    Console.subheader("Walking Ones (single bit HIGH)")
    for bit in range(8):
        pattern = 1 << bit
        seg, glow, oe = s.evaluate(pattern)
        if seg == SEG_LOCKED:
            Console.passed(f"0x{pattern:02X} ({bin(pattern)[2:].zfill(8)}): LOCKED")
        else:
            Console.failed(f"0x{pattern:02X}: BREACH! seg={hex(seg)}")
            errors += 1

    # Walking Zeros
    Console.subheader("Walking Zeros (single bit LOW)")
    for bit in range(8):
        pattern = 0xFF ^ (1 << bit)
        seg, glow, oe = s.evaluate(pattern)
        if seg == SEG_LOCKED:
            Console.passed(f"0x{pattern:02X} ({bin(pattern)[2:].zfill(8)}): LOCKED")
        else:
            Console.failed(f"0x{pattern:02X}: BREACH! seg={hex(seg)}")
            errors += 1

    # Boundaries
    Console.subheader("Boundary Values")
    for boundary in [0x00, 0xFF]:
        seg, glow, oe = s.evaluate(boundary)
        if seg == SEG_LOCKED:
            Console.passed(f"0x{boundary:02X}: LOCKED")
        else:
            Console.failed(f"0x{boundary:02X}: BREACH! seg={hex(seg)}")
            errors += 1

    Console.result("TEST 8: BUS INTEGRITY", errors == 0)
    return errors == 0


def run_test_9():
    """TEST 9: SEGMENT ENCODING FIDELITY — PIN-BY-PIN TRUTH TABLE"""
    Console.header("TEST 9: SEGMENT ENCODING FIDELITY — PIN-BY-PIN")
    s = SentinelModel()
    errors = 0

    SEG_NAMES = ["A", "B", "C", "D", "E", "F", "G", "DP"]

    # LOCKED state
    Console.subheader("LOCKED State ('L') — Expected: 0xC7")
    seg, glow, oe = s.evaluate(0x00)
    Console.info(f"Raw output: {hex(seg)} = {bin(seg)[2:].zfill(8)}")
    #                  A  B  C  D  E  F  G  DP
    expected_locked = [1, 1, 1, 0, 0, 0, 1, 1]

    for i, (exp, name) in enumerate(zip(expected_locked, SEG_NAMES)):
        actual = (seg >> i) & 1
        state  = "OFF (inactive)" if actual == 1 else "ON  (lit)"
        if actual == exp:
            Console.passed(f"SEG_{name} [bit {i}]: {state}")
        else:
            Console.failed(f"SEG_{name} [bit {i}]: Expected {exp}, got {actual}")
            errors += 1

    # VERIFIED state
    Console.subheader("VERIFIED State ('U') — Expected: 0xC1")
    seg, glow, oe = s.evaluate(VAELIX_KEY)
    Console.info(f"Raw output: {hex(seg)} = {bin(seg)[2:].zfill(8)}")
    #                    A  B  C  D  E  F  G  DP
    expected_verified = [1, 0, 0, 0, 0, 0, 1, 1]

    for i, (exp, name) in enumerate(zip(expected_verified, SEG_NAMES)):
        actual = (seg >> i) & 1
        state  = "OFF (inactive)" if actual == 1 else "ON  (lit)"
        if actual == exp:
            Console.passed(f"SEG_{name} [bit {i}]: {state}")
        else:
            Console.failed(f"SEG_{name} [bit {i}]: Expected {exp}, got {actual}")
            errors += 1

    # Delta check
    Console.subheader("State Transition Delta")
    locked_val   = SEG_LOCKED
    verified_val = SEG_VERIFIED
    diff = locked_val ^ verified_val
    Console.info(f"LOCKED ^ VERIFIED = {hex(locked_val)} ^ {hex(verified_val)} = {hex(diff)}")
    Console.info(f"Changed bits: {bin(diff)[2:].zfill(8)}")

    changed_segs = [SEG_NAMES[i] for i in range(8) if (diff >> i) & 1]
    Console.info(f"Segments that toggle: {', '.join(changed_segs)}")

    if diff == 0x06:
        Console.passed(f"Delta = 0x06 — only SEG_B and SEG_C toggle (correct)")
    else:
        Console.failed(f"Delta = {hex(diff)} — unexpected segments changed")
        errors += 1

    Console.result("TEST 9: SEGMENT ENCODING", errors == 0)
    return errors == 0


def run_test_10():
    """TEST 10: BYTE COMPLEMENT REJECTION — MIRROR & TRANSFORM ATTACK"""
    Console.header("TEST 10: BYTE COMPLEMENT & TRANSFORM REJECTION")
    s = SentinelModel()
    errors    = 0
    deflected = 0

    def rot_l(val, n):
        return ((val << n) | (val >> (8 - n))) & 0xFF

    def rot_r(val, n):
        return ((val >> n) | (val << (8 - n))) & 0xFF

    def rev_bits(val):
        r = 0
        for i in range(8):
            r |= ((val >> i) & 1) << (7 - i)
        return r

    def swap_nib(val):
        return ((val & 0x0F) << 4) | ((val & 0xF0) >> 4)

    transforms = {
        "COMPLEMENT (~0xB6)":        (~VAELIX_KEY) & 0xFF,
        "NIBBLE SWAP":               swap_nib(VAELIX_KEY),
        "ROTATE LEFT 1":             rot_l(VAELIX_KEY, 1),
        "ROTATE LEFT 2":             rot_l(VAELIX_KEY, 2),
        "ROTATE LEFT 4":             rot_l(VAELIX_KEY, 4),
        "ROTATE RIGHT 1":            rot_r(VAELIX_KEY, 1),
        "ROTATE RIGHT 2":            rot_r(VAELIX_KEY, 2),
        "BIT REVERSE":               rev_bits(VAELIX_KEY),
        "XOR 0xAA (ALT MASK)":       VAELIX_KEY ^ 0xAA,
        "XOR 0x55 (ALT MASK PH2)":   VAELIX_KEY ^ 0x55,
        "XOR 0x0F (NIBBLE MASK)":     VAELIX_KEY ^ 0x0F,
        "XOR 0xF0 (UPPER MASK)":      VAELIX_KEY ^ 0xF0,
    }

    for name, attack_key in transforms.items():
        if attack_key == VAELIX_KEY:
            Console.skip(f"{name} = {hex(attack_key)} (produces valid key — not an attack)")
            continue

        seg, glow, oe = s.evaluate(attack_key)
        Console.info(f"{name:.<40s} {hex(attack_key)} ({bin(attack_key)[2:].zfill(8)})")

        if seg == SEG_LOCKED and glow == GLOW_DORMANT:
            Console.passed(f"{name}: DEFLECTED")
            deflected += 1
        else:
            Console.failed(f"{name}: BREACH! seg={hex(seg)} glow={hex(glow)}")
            errors += 1

    Console.info(f"Transforms deflected: {deflected}, Breaches: {errors}")
    Console.result("TEST 10: TRANSFORM REJECTION", errors == 0)
    return errors == 0


# ============================================================================
# STANDALONE MAIN — RUN ALL TESTS WITH FULL CONSOLE OUTPUT
# ============================================================================

def main():
    Console.banner()

    tests = [
        ("TEST  1: Authorization — Golden Path",     run_test_1),
        ("TEST  2: Intrusion — 256-Key Sweep",       run_test_2),
        ("TEST  3: Reset Behavior — Cold Start",     run_test_3),
        ("TEST  4: Hamming-1 Adjacency Attack",      run_test_4),
        ("TEST  5: UIO Direction Integrity",          run_test_5),
        ("TEST  6: Rapid Cycling Stress",             run_test_6),
        ("TEST  7: Hamming-2 Double-Bit Attack",      run_test_7),
        ("TEST  8: Walking Ones/Zeros Bus Scan",      run_test_8),
        ("TEST  9: Segment Encoding Fidelity",        run_test_9),
        ("TEST 10: Transform & Complement Rejection", run_test_10),
    ]

    results  = []
    passed   = 0
    failed   = 0

    for name, func in tests:
        try:
            ok = func()
            results.append((name, ok))
            if ok:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            Console.failed(f"EXCEPTION in {name}: {e}")
            results.append((name, False))
            failed += 1

    # ── FINAL SCOREBOARD ──
    print(f"\n{Console.BOLD}{Console.CYAN}{'='*72}")
    print(f"  SENTINEL INTERROGATION — FINAL SCOREBOARD")
    print(f"{'='*72}{Console.RESET}\n")

    for name, ok in results:
        status = f"{Console.GREEN}PASS{Console.RESET}" if ok else f"{Console.RED}FAIL{Console.RESET}"
        print(f"  [{status}]  {name}")

    print(f"\n  {Console.BOLD}────────────────────────────────────────{Console.RESET}")
    print(f"  {Console.BOLD}  TOTAL: {passed + failed}  |  PASSED: {Console.GREEN}{passed}{Console.RESET}{Console.BOLD}  |  FAILED: {Console.RED}{failed}{Console.RESET}")

    if failed == 0:
        print(f"\n  {Console.GREEN}{Console.BOLD}  ✓ ALL TESTS PASSED — SENTINEL LOGIC VERIFIED{Console.RESET}")
        print(f"  {Console.DIM}  Software model confirmed. Run 'cd test && make -B' for RTL simulation.{Console.RESET}")
    else:
        print(f"\n  {Console.RED}{Console.BOLD}  ✗ {failed} TEST(S) FAILED — INVESTIGATE IMMEDIATELY{Console.RESET}")

    print()
    return 0 if failed == 0 else 1


# ============================================================================
# ============================================================================
#
#   SECTION B: COCOTB RTL TESTS
#   Runs with: cd test && make -B
#
#   These tests drive the actual Verilog through Icarus Verilog.
#   They are IGNORED when running `python test.py` directly.
#
# ============================================================================
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
    # COCOTB TEST 1: AUTHORIZATION
    # ================================================================
    @cocotb.test()
    async def test_sentinel_authorization(dut):
        dut._log.info("VAELIX SENTINEL | TEST 1: AUTHORIZATION SEQUENCE")
        clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
        cocotb.start_soon(clock.start())
        await reset_sentinel(dut)

        # Locked
        dut.ui_in.value = 0x00
        await ClockCycles(dut.clk, 1)
        assert dut.uo_out.value == SEG_LOCKED, \
            f"LOCKED FAILURE: Expected {hex(SEG_LOCKED)}, got {hex(int(dut.uo_out.value))}"
        assert dut.uio_out.value == GLOW_DORMANT, \
            f"GLOW LEAK: Got {hex(int(dut.uio_out.value))}"
        dut._log.info("  [PASS] Default: LOCKED")

        # Verified
        dut.ui_in.value = VAELIX_KEY
        await ClockCycles(dut.clk, 1)
        assert dut.uo_out.value == SEG_VERIFIED, \
            f"AUTH FAILURE: Expected {hex(SEG_VERIFIED)}, got {hex(int(dut.uo_out.value))}"
        assert dut.uio_out.value == GLOW_ACTIVE, \
            f"GLOW FAILURE: Expected {hex(GLOW_ACTIVE)}, got {hex(int(dut.uio_out.value))}"
        dut._log.info("  [PASS] Key 0xB6: VERIFIED + GLOW")

        # Re-lock
        dut.ui_in.value = 0x00
        await ClockCycles(dut.clk, 1)
        assert dut.uo_out.value == SEG_LOCKED
        assert dut.uio_out.value == GLOW_DORMANT
        dut._log.info("  [PASS] Re-locked")
        dut._log.info("TEST 1: COMPLETE")

    # ================================================================
    # COCOTB TEST 2: BRUTE-FORCE SWEEP
    # ================================================================
    @cocotb.test()
    async def test_sentinel_intrusion_sweep(dut):
        dut._log.info("VAELIX SENTINEL | TEST 2: 256-KEY SWEEP")
        clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
        cocotb.start_soon(clock.start())
        await reset_sentinel(dut)

        pass_count = 0
        fail_count = 0
        for key in range(256):
            dut.ui_in.value = key
            await ClockCycles(dut.clk, 1)
            seg  = int(dut.uo_out.value)
            glow = int(dut.uio_out.value)
            if key == VAELIX_KEY:
                assert seg == SEG_VERIFIED, f"FALSE REJECT at {hex(key)}: {hex(seg)}"
                assert glow == GLOW_ACTIVE
                pass_count += 1
            else:
                assert seg == SEG_LOCKED, f"BREACH at {hex(key)}: {hex(seg)}"
                assert glow == GLOW_DORMANT
                fail_count += 1

        dut._log.info(f"  Sweep: {pass_count} auth, {fail_count} deflected")
        assert pass_count == 1 and fail_count == 255
        dut._log.info("TEST 2: COMPLETE")

    # ================================================================
    # COCOTB TEST 3: RESET BEHAVIOR
    # ================================================================
    @cocotb.test()
    async def test_sentinel_reset_behavior(dut):
        dut._log.info("VAELIX SENTINEL | TEST 3: RESET SOVEREIGNTY")
        clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
        cocotb.start_soon(clock.start())
        await reset_sentinel(dut)

        dut.ui_in.value = VAELIX_KEY
        await ClockCycles(dut.clk, 1)
        assert dut.uo_out.value == SEG_VERIFIED
        dut._log.info("  [PASS] Pre-reset: VERIFIED")

        dut.rst_n.value = 0
        await ClockCycles(dut.clk, 5)
        dut.rst_n.value = 1
        await ClockCycles(dut.clk, 1)
        assert dut.uo_out.value == SEG_VERIFIED
        dut._log.info("  [PASS] Post-reset with key held: Re-verified")

        dut.ui_in.value = 0x00
        await ClockCycles(dut.clk, 1)
        assert dut.uo_out.value == SEG_LOCKED
        dut._log.info("  [PASS] Key released: LOCKED")
        dut._log.info("TEST 3: COMPLETE")

    # ================================================================
    # COCOTB TEST 4: HAMMING-1 ADJACENCY
    # ================================================================
    @cocotb.test()
    async def test_sentinel_bitflip_adjacency(dut):
        dut._log.info("VAELIX SENTINEL | TEST 4: HAMMING-1 ATTACK")
        clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
        cocotb.start_soon(clock.start())
        await reset_sentinel(dut)

        for bit in range(8):
            mutant = VAELIX_KEY ^ (1 << bit)
            dut.ui_in.value = mutant
            await ClockCycles(dut.clk, 1)
            assert int(dut.uo_out.value) == SEG_LOCKED, \
                f"H1 BREACH bit {bit} ({hex(mutant)}): {hex(int(dut.uo_out.value))}"
            dut._log.info(f"  [PASS] Bit {bit} ({hex(mutant)}): DEFLECTED")
        dut._log.info("TEST 4: COMPLETE")

    # ================================================================
    # COCOTB TEST 5: UIO DIRECTION
    # ================================================================
    @cocotb.test()
    async def test_sentinel_uio_direction(dut):
        dut._log.info("VAELIX SENTINEL | TEST 5: UIO DIRECTION")
        clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
        cocotb.start_soon(clock.start())
        await reset_sentinel(dut)

        for vec in [0x00, 0xFF, VAELIX_KEY, 0xB7, 0x49, 0xA5, 0x5A, 0x01]:
            dut.ui_in.value = vec
            await ClockCycles(dut.clk, 1)
            assert dut.uio_oe.value == UIO_ALL_OUTPUT, \
                f"OE DRIFT at {hex(vec)}: {hex(int(dut.uio_oe.value))}"
            dut._log.info(f"  [PASS] {hex(vec)}: uio_oe=0xFF")
        dut._log.info("TEST 5: COMPLETE")

    # ================================================================
    # COCOTB TEST 6: RAPID CYCLING
    # ================================================================
    @cocotb.test()
    async def test_sentinel_rapid_cycling(dut):
        dut._log.info("VAELIX SENTINEL | TEST 6: RAPID CYCLING (200 rounds)")
        clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
        cocotb.start_soon(clock.start())
        await reset_sentinel(dut)

        bad_keys = [0x00, 0xFF, 0xB7, 0xB4, 0x49, 0xA6, 0x36, 0x96]
        errs = 0
        for i in range(200):
            dut.ui_in.value = VAELIX_KEY
            await ClockCycles(dut.clk, 1)
            if int(dut.uo_out.value) != SEG_VERIFIED:
                errs += 1
            bad = bad_keys[i % len(bad_keys)]
            dut.ui_in.value = bad
            await ClockCycles(dut.clk, 1)
            if int(dut.uo_out.value) != SEG_LOCKED:
                errs += 1
        assert errs == 0, f"STABILITY: {errs} errors in 200 cycles"
        dut._log.info("  [PASS] 200 cycles clean")
        dut._log.info("TEST 6: COMPLETE")

    # ================================================================
    # COCOTB TEST 7: HAMMING-2 ATTACK
    # ================================================================
    @cocotb.test()
    async def test_sentinel_hamming2_attack(dut):
        dut._log.info("VAELIX SENTINEL | TEST 7: HAMMING-2 ATTACK")
        clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
        cocotb.start_soon(clock.start())
        await reset_sentinel(dut)

        count = 0
        for a in range(8):
            for b in range(a + 1, 8):
                mutant = VAELIX_KEY ^ (1 << a) ^ (1 << b)
                dut.ui_in.value = mutant
                await ClockCycles(dut.clk, 1)
                assert int(dut.uo_out.value) == SEG_LOCKED, \
                    f"H2 BREACH [{a},{b}] ({hex(mutant)})"
                count += 1
        assert count == 28
        dut._log.info(f"  [PASS] All 28 H2 mutations deflected")
        dut._log.info("TEST 7: COMPLETE")

    # ================================================================
    # COCOTB TEST 8: WALKING BUS SCAN
    # ================================================================
    @cocotb.test()
    async def test_sentinel_walking_bus_scan(dut):
        dut._log.info("VAELIX SENTINEL | TEST 8: WALKING BUS SCAN")
        clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
        cocotb.start_soon(clock.start())
        await reset_sentinel(dut)

        for bit in range(8):
            dut.ui_in.value = 1 << bit
            await ClockCycles(dut.clk, 1)
            assert int(dut.uo_out.value) == SEG_LOCKED, \
                f"WALK-1 BREACH bit {bit}"
        dut._log.info("  [PASS] Walking-1: 8/8 locked")

        for bit in range(8):
            dut.ui_in.value = 0xFF ^ (1 << bit)
            await ClockCycles(dut.clk, 1)
            assert int(dut.uo_out.value) == SEG_LOCKED, \
                f"WALK-0 BREACH bit {bit}"
        dut._log.info("  [PASS] Walking-0: 8/8 locked")

        for bnd in [0x00, 0xFF]:
            dut.ui_in.value = bnd
            await ClockCycles(dut.clk, 1)
            assert int(dut.uo_out.value) == SEG_LOCKED
        dut._log.info("  [PASS] Boundaries locked")
        dut._log.info("TEST 8: COMPLETE")

    # ================================================================
    # COCOTB TEST 9: SEGMENT ENCODING
    # ================================================================
    @cocotb.test()
    async def test_sentinel_segment_encoding(dut):
        dut._log.info("VAELIX SENTINEL | TEST 9: SEGMENT ENCODING")
        clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
        cocotb.start_soon(clock.start())
        await reset_sentinel(dut)

        NAMES = ["A", "B", "C", "D", "E", "F", "G", "DP"]

        dut.ui_in.value = 0x00
        await ClockCycles(dut.clk, 1)
        locked = int(dut.uo_out.value)
        exp_l  = [1, 1, 1, 0, 0, 0, 1, 1]
        for i, (e, n) in enumerate(zip(exp_l, NAMES)):
            assert ((locked >> i) & 1) == e, f"LOCKED SEG_{n}: expected {e}"
            dut._log.info(f"  SEG_{n}: {'OFF' if e else 'ON'} ✓")
        dut._log.info(f"  [PASS] LOCKED = {hex(locked)}")

        dut.ui_in.value = VAELIX_KEY
        await ClockCycles(dut.clk, 1)
        verified = int(dut.uo_out.value)
        exp_v    = [1, 0, 0, 0, 0, 0, 1, 1]
        for i, (e, n) in enumerate(zip(exp_v, NAMES)):
            assert ((verified >> i) & 1) == e, f"VERIFIED SEG_{n}: expected {e}"
            dut._log.info(f"  SEG_{n}: {'OFF' if e else 'ON'} ✓")
        dut._log.info(f"  [PASS] VERIFIED = {hex(verified)}")

        diff = locked ^ verified
        assert diff == 0x06, f"Delta {hex(diff)} != 0x06"
        dut._log.info(f"  [PASS] Delta = {hex(diff)} (B,C only)")
        dut._log.info("TEST 9: COMPLETE")

    # ================================================================
    # COCOTB TEST 10: TRANSFORM REJECTION
    # ================================================================
    @cocotb.test()
    async def test_sentinel_complement_rejection(dut):
        dut._log.info("VAELIX SENTINEL | TEST 10: TRANSFORM REJECTION")
        clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
        cocotb.start_soon(clock.start())
        await reset_sentinel(dut)

        def rl(v, n): return ((v << n) | (v >> (8 - n))) & 0xFF
        def rr(v, n): return ((v >> n) | (v << (8 - n))) & 0xFF
        def rev(v):
            r = 0
            for i in range(8): r |= ((v >> i) & 1) << (7 - i)
            return r
        def swp(v): return ((v & 0x0F) << 4) | ((v & 0xF0) >> 4)

        transforms = {
            "~0xB6":    (~VAELIX_KEY) & 0xFF,
            "NIB_SWAP": swp(VAELIX_KEY),
            "ROL1":     rl(VAELIX_KEY, 1),
            "ROL2":     rl(VAELIX_KEY, 2),
            "ROL4":     rl(VAELIX_KEY, 4),
            "ROR1":     rr(VAELIX_KEY, 1),
            "ROR2":     rr(VAELIX_KEY, 2),
            "BITREV":   rev(VAELIX_KEY),
            "XOR_AA":   VAELIX_KEY ^ 0xAA,
            "XOR_55":   VAELIX_KEY ^ 0x55,
            "XOR_0F":   VAELIX_KEY ^ 0x0F,
            "XOR_F0":   VAELIX_KEY ^ 0xF0,
        }

        for name, key in transforms.items():
            if key == VAELIX_KEY:
                dut._log.info(f"  [SKIP] {name}={hex(key)} (identity)")
                continue
            dut.ui_in.value = key
            await ClockCycles(dut.clk, 1)
            assert int(dut.uo_out.value) == SEG_LOCKED, \
                f"TRANSFORM BREACH [{name}] {hex(key)}"
            assert int(dut.uio_out.value) == GLOW_DORMANT
            dut._log.info(f"  [PASS] {name} ({hex(key)}): DEFLECTED")
        dut._log.info("TEST 10: COMPLETE")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    sys.exit(main())
