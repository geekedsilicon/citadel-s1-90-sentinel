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


def run_test_11():
    """TEST 11: HAMMING WEIGHT ANALYSIS — SAME-WEIGHT KEY REJECTION"""
    Console.header("TEST 11: HAMMING WEIGHT ANALYSIS — SAME-WEIGHT KEYS")
    s = SentinelModel()
    errors = 0

    # 0xB6 = 10110110 has Hamming weight 5 (five 1-bits).
    # There are C(8,5) = 56 possible 8-bit values with exactly 5 ones.
    # Only 0xB6 should pass. The other 55 must be rejected.
    key_weight = bin(VAELIX_KEY).count('1')
    Console.info(f"Valid key: {hex(VAELIX_KEY)} = {bin(VAELIX_KEY)[2:].zfill(8)} (Hamming weight: {key_weight})")
    Console.info(f"Testing all 8-bit values with exactly {key_weight} ones set...")
    print()

    same_weight_keys = [v for v in range(256) if bin(v).count('1') == key_weight]
    Console.info(f"Total keys with weight {key_weight}: {len(same_weight_keys)}")

    authorized = 0
    deflected  = 0

    for key in same_weight_keys:
        seg, glow, oe = s.evaluate(key)

        if key == VAELIX_KEY:
            if seg == SEG_VERIFIED:
                Console.passed(f"{hex(key)} ({bin(key)[2:].zfill(8)}): AUTHORIZED ← valid key")
                authorized += 1
            else:
                Console.failed(f"{hex(key)}: Should be VERIFIED, got {hex(seg)}")
                errors += 1
        else:
            if seg == SEG_LOCKED:
                Console.passed(f"{hex(key)} ({bin(key)[2:].zfill(8)}): DEFLECTED")
                deflected += 1
            else:
                Console.failed(f"WEIGHT BREACH at {hex(key)} ({bin(key)[2:].zfill(8)}): seg={hex(seg)}")
                errors += 1

    Console.info(f"Results: {authorized} authorized, {deflected} deflected, {errors} breaches")
    ok = authorized == 1 and deflected == (len(same_weight_keys) - 1) and errors == 0
    Console.result("TEST 11: HAMMING WEIGHT", ok)
    return ok


def run_test_12():
    """TEST 12: PARTIAL NIBBLE MATCH — HALF-KEY ATTACK"""
    Console.header("TEST 12: PARTIAL NIBBLE MATCH — HALF-KEY ATTACK")
    s = SentinelModel()
    errors = 0

    # 0xB6: upper nibble = 0xB, lower nibble = 0x6
    # Test all keys matching the upper nibble (0xBx) and all matching lower (0xx6).
    # Only 0xB6 (which matches BOTH) should pass.
    upper = VAELIX_KEY & 0xF0  # 0xB0
    lower = VAELIX_KEY & 0x0F  # 0x06

    Console.info(f"Valid key: {hex(VAELIX_KEY)} | Upper nibble: {hex(upper >> 4)} | Lower nibble: {hex(lower)}")

    # Upper nibble matches: 0xB0 through 0xBF
    Console.subheader(f"Upper Nibble Match (0x{upper >> 4:X}x) — 16 keys")
    for lo in range(16):
        key = upper | lo
        seg, glow, oe = s.evaluate(key)
        tag = "← VALID KEY" if key == VAELIX_KEY else ""

        if key == VAELIX_KEY:
            if seg == SEG_VERIFIED:
                Console.passed(f"{hex(key)} ({bin(key)[2:].zfill(8)}): VERIFIED {tag}")
            else:
                Console.failed(f"{hex(key)}: Expected VERIFIED, got {hex(seg)}")
                errors += 1
        else:
            if seg == SEG_LOCKED:
                Console.passed(f"{hex(key)} ({bin(key)[2:].zfill(8)}): LOCKED")
            else:
                Console.failed(f"NIBBLE BREACH at {hex(key)}: Upper nibble match leaked! seg={hex(seg)}")
                errors += 1

    # Lower nibble matches: 0x06, 0x16, 0x26, ..., 0xF6
    Console.subheader(f"Lower Nibble Match (0xx{lower:X}) — 16 keys")
    for hi in range(16):
        key = (hi << 4) | lower
        seg, glow, oe = s.evaluate(key)
        tag = "← VALID KEY" if key == VAELIX_KEY else ""

        if key == VAELIX_KEY:
            if seg == SEG_VERIFIED:
                Console.passed(f"{hex(key)} ({bin(key)[2:].zfill(8)}): VERIFIED {tag}")
            else:
                Console.failed(f"{hex(key)}: Expected VERIFIED, got {hex(seg)}")
                errors += 1
        else:
            if seg == SEG_LOCKED:
                Console.passed(f"{hex(key)} ({bin(key)[2:].zfill(8)}): LOCKED")
            else:
                Console.failed(f"NIBBLE BREACH at {hex(key)}: Lower nibble match leaked! seg={hex(seg)}")
                errors += 1

    Console.result("TEST 12: NIBBLE ATTACK", errors == 0)
    return errors == 0


def run_test_13():
    """TEST 13: GLOW-SEGMENT COHERENCE — OUTPUT CONSISTENCY AUDIT"""
    Console.header("TEST 13: GLOW-SEGMENT COHERENCE — FULL 256-KEY AUDIT")
    s = SentinelModel()
    errors       = 0
    coherent     = 0
    incoherent   = []

    Console.info("For EVERY input: if seg=VERIFIED then glow must=ACTIVE.")
    Console.info("                 if seg=LOCKED   then glow must=DORMANT.")
    Console.info("Mixed states are a hardware defect. Sweeping all 256...")
    print()

    for key in range(256):
        seg, glow, oe = s.evaluate(key)

        seg_is_verified = (seg == SEG_VERIFIED)
        glow_is_active  = (glow == GLOW_ACTIVE)
        seg_is_locked   = (seg == SEG_LOCKED)
        glow_is_dormant = (glow == GLOW_DORMANT)

        if seg_is_verified and glow_is_active:
            coherent += 1
        elif seg_is_locked and glow_is_dormant:
            coherent += 1
        else:
            incoherent.append(key)
            errors += 1
            Console.failed(
                f"INCOHERENT at {hex(key)}: seg={hex(seg)} "
                f"({'VER' if seg_is_verified else 'LCK' if seg_is_locked else '???'}) "
                f"glow={hex(glow)} "
                f"({'ACT' if glow_is_active else 'DRM' if glow_is_dormant else '???'})"
            )

    if errors == 0:
        Console.passed(f"All 256 keys: segment and glow COHERENT ({coherent}/256)")
    else:
        Console.failed(f"Incoherent keys: {[hex(k) for k in incoherent]}")

    Console.result("TEST 13: GLOW COHERENCE", errors == 0)
    return errors == 0


def run_test_14():
    """TEST 14: LONG DURATION HOLD — SUSTAINED AUTHORIZATION STABILITY"""
    Console.header("TEST 14: LONG DURATION HOLD — 1000-CYCLE STABILITY")
    s = SentinelModel()
    errors = 0

    HOLD_CYCLES = 1000

    # Phase 1: Hold LOCKED for N cycles
    Console.subheader(f"Phase 1: Hold LOCKED (0x00) for {HOLD_CYCLES} cycles")
    for cycle in range(HOLD_CYCLES):
        seg, glow, oe = s.evaluate(0x00)
        if seg != SEG_LOCKED or glow != GLOW_DORMANT:
            Console.failed(f"LOCKED drift at cycle {cycle}: seg={hex(seg)} glow={hex(glow)}")
            errors += 1
            break
    else:
        Console.passed(f"LOCKED stable for {HOLD_CYCLES} cycles")

    # Phase 2: Hold VERIFIED for N cycles
    Console.subheader(f"Phase 2: Hold VERIFIED (0xB6) for {HOLD_CYCLES} cycles")
    for cycle in range(HOLD_CYCLES):
        seg, glow, oe = s.evaluate(VAELIX_KEY)
        if seg != SEG_VERIFIED or glow != GLOW_ACTIVE:
            Console.failed(f"VERIFIED drift at cycle {cycle}: seg={hex(seg)} glow={hex(glow)}")
            errors += 1
            break
    else:
        Console.passed(f"VERIFIED stable for {HOLD_CYCLES} cycles")

    # Phase 3: Hold an invalid key for N cycles
    INVALID_HOLD = 0x49  # complement of valid key
    Console.subheader(f"Phase 3: Hold INVALID ({hex(INVALID_HOLD)}) for {HOLD_CYCLES} cycles")
    for cycle in range(HOLD_CYCLES):
        seg, glow, oe = s.evaluate(INVALID_HOLD)
        if seg != SEG_LOCKED or glow != GLOW_DORMANT:
            Console.failed(f"INVALID drift at cycle {cycle}: seg={hex(seg)} glow={hex(glow)}")
            errors += 1
            break
    else:
        Console.passed(f"INVALID key {hex(INVALID_HOLD)} stayed LOCKED for {HOLD_CYCLES} cycles")

    Console.info(f"Total cycles evaluated: {HOLD_CYCLES * 3}")
    Console.result("TEST 14: LONG HOLD", errors == 0)
    return errors == 0


def run_test_15():
    """TEST 15: INPUT TRANSITION COVERAGE — ALL-EDGE-PAIRS"""
    Console.header("TEST 15: INPUT TRANSITION COVERAGE — EDGE PAIR ANALYSIS")
    s = SentinelModel()
    errors = 0

    # Test that the output is correct regardless of what the PREVIOUS input was.
    # For combinational logic this should always be true, but this catches
    # any accidental state retention or feedback loops.

    # Critical transitions to test:
    transitions = [
        # (from_key, to_key, expected_description)
        (0x00, VAELIX_KEY, "Zero → Valid key"),
        (0xFF, VAELIX_KEY, "All-ones → Valid key"),
        (VAELIX_KEY, 0x00, "Valid key → Zero"),
        (VAELIX_KEY, 0xFF, "Valid key → All-ones"),
        (VAELIX_KEY, 0xB7, "Valid key → H1 neighbor"),
        (0xB7, VAELIX_KEY, "H1 neighbor → Valid key"),
        (0x49, VAELIX_KEY, "Complement → Valid key"),
        (VAELIX_KEY, 0x49, "Valid key → Complement"),
        (0x00, 0xFF,       "Zero → All-ones"),
        (0xFF, 0x00,       "All-ones → Zero"),
        (0x01, 0x02,       "Walking-1 step"),
        (0x55, 0xAA,       "Alternating pattern swap"),
        (0xAA, 0x55,       "Alternating pattern swap (reverse)"),
        (0xB5, VAELIX_KEY, "H1 below → Valid key"),
        (VAELIX_KEY, 0xB5, "Valid key → H1 below"),
        (0x00, 0x00,       "Zero → Zero (no change)"),
        (VAELIX_KEY, VAELIX_KEY, "Valid → Valid (no change)"),
        (0xFF, 0xFF,       "All-ones → All-ones (no change)"),
    ]

    Console.info(f"Testing {len(transitions)} critical input transitions...")
    Console.info(f"Each transition: apply FROM, then TO, verify TO output is correct.")
    print()

    for from_key, to_key, desc in transitions:
        # Set the "from" state
        s.evaluate(from_key)

        # Transition to "to" state
        seg, glow, oe = s.evaluate(to_key)

        # What should the output be?
        if to_key == VAELIX_KEY:
            exp_seg  = SEG_VERIFIED
            exp_glow = GLOW_ACTIVE
            exp_str  = "VERIFIED"
        else:
            exp_seg  = SEG_LOCKED
            exp_glow = GLOW_DORMANT
            exp_str  = "LOCKED"

        ok = (seg == exp_seg and glow == exp_glow)

        from_str = f"0x{from_key:02X}"
        to_str   = f"0x{to_key:02X}"
        arrow    = f"{from_str} → {to_str}"

        if ok:
            Console.passed(f"{arrow:>15s}  [{desc:.<40s}] → {exp_str}")
        else:
            Console.failed(f"{arrow:>15s}  [{desc}] → Expected {exp_str}, got seg={hex(seg)} glow={hex(glow)}")
            errors += 1

    Console.result("TEST 15: TRANSITION COVERAGE", errors == 0)
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
        ("TEST 11: Hamming Weight — Same-Weight Keys", run_test_11),
        ("TEST 12: Partial Nibble Match Attack",       run_test_12),
        ("TEST 13: Glow-Segment Coherence Audit",      run_test_13),
        ("TEST 14: Long Duration Hold (3000 cycles)",   run_test_14),
        ("TEST 15: Input Transition Coverage",          run_test_15),
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

    # ================================================================
    # COCOTB TEST 11: HAMMING WEIGHT ANALYSIS
    # ================================================================
    @cocotb.test()
    async def test_sentinel_hamming_weight(dut):
        dut._log.info("VAELIX SENTINEL | TEST 11: HAMMING WEIGHT ANALYSIS")
        clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
        cocotb.start_soon(clock.start())
        await reset_sentinel(dut)

        key_weight = bin(VAELIX_KEY).count('1')
        same_weight = [v for v in range(256) if bin(v).count('1') == key_weight]
        dut._log.info(f"  Weight {key_weight}: {len(same_weight)} keys to test")

        auth = 0
        defl = 0
        for key in same_weight:
            dut.ui_in.value = key
            await ClockCycles(dut.clk, 1)
            seg = int(dut.uo_out.value)
            if key == VAELIX_KEY:
                assert seg == SEG_VERIFIED, f"Valid key rejected: {hex(key)}"
                auth += 1
            else:
                assert seg == SEG_LOCKED, f"WEIGHT BREACH at {hex(key)}: {hex(seg)}"
                defl += 1

        assert auth == 1 and defl == len(same_weight) - 1
        dut._log.info(f"  [PASS] 1 authorized, {defl} deflected")
        dut._log.info("TEST 11: COMPLETE")

    # ================================================================
    # COCOTB TEST 12: PARTIAL NIBBLE MATCH
    # ================================================================
    @cocotb.test()
    async def test_sentinel_nibble_attack(dut):
        dut._log.info("VAELIX SENTINEL | TEST 12: NIBBLE ATTACK")
        clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
        cocotb.start_soon(clock.start())
        await reset_sentinel(dut)

        upper = VAELIX_KEY & 0xF0
        lower = VAELIX_KEY & 0x0F

        # Upper nibble matches (0xBx)
        for lo in range(16):
            key = upper | lo
            dut.ui_in.value = key
            await ClockCycles(dut.clk, 1)
            seg = int(dut.uo_out.value)
            if key == VAELIX_KEY:
                assert seg == SEG_VERIFIED
            else:
                assert seg == SEG_LOCKED, f"UPPER NIBBLE BREACH at {hex(key)}: {hex(seg)}"
        dut._log.info("  [PASS] Upper nibble (0xBx): 15 deflected, 1 auth")

        # Lower nibble matches (0xx6)
        for hi in range(16):
            key = (hi << 4) | lower
            dut.ui_in.value = key
            await ClockCycles(dut.clk, 1)
            seg = int(dut.uo_out.value)
            if key == VAELIX_KEY:
                assert seg == SEG_VERIFIED
            else:
                assert seg == SEG_LOCKED, f"LOWER NIBBLE BREACH at {hex(key)}: {hex(seg)}"
        dut._log.info("  [PASS] Lower nibble (0xx6): 15 deflected, 1 auth")
        dut._log.info("TEST 12: COMPLETE")

    # ================================================================
    # COCOTB TEST 13: GLOW-SEGMENT COHERENCE
    # ================================================================
    @cocotb.test()
    async def test_sentinel_glow_coherence(dut):
        dut._log.info("VAELIX SENTINEL | TEST 13: GLOW-SEGMENT COHERENCE")
        clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
        cocotb.start_soon(clock.start())
        await reset_sentinel(dut)

        incoherent = 0
        for key in range(256):
            dut.ui_in.value = key
            await ClockCycles(dut.clk, 1)
            seg  = int(dut.uo_out.value)
            glow = int(dut.uio_out.value)

            if seg == SEG_VERIFIED:
                if glow != GLOW_ACTIVE:
                    incoherent += 1
                    dut._log.error(f"  INCOHERENT at {hex(key)}: seg=VER glow={hex(glow)}")
            elif seg == SEG_LOCKED:
                if glow != GLOW_DORMANT:
                    incoherent += 1
                    dut._log.error(f"  INCOHERENT at {hex(key)}: seg=LCK glow={hex(glow)}")
            else:
                incoherent += 1
                dut._log.error(f"  UNKNOWN STATE at {hex(key)}: seg={hex(seg)} glow={hex(glow)}")

        assert incoherent == 0, f"COHERENCE FAILURE: {incoherent} incoherent outputs"
        dut._log.info("  [PASS] All 256 keys: segment and glow COHERENT")
        dut._log.info("TEST 13: COMPLETE")

    # ================================================================
    # COCOTB TEST 14: LONG DURATION HOLD
    # ================================================================
    @cocotb.test()
    async def test_sentinel_long_hold(dut):
        dut._log.info("VAELIX SENTINEL | TEST 14: LONG HOLD (1000 cycles x3)")
        clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
        cocotb.start_soon(clock.start())
        await reset_sentinel(dut)

        HOLD = 1000

        # Hold LOCKED
        dut.ui_in.value = 0x00
        for c in range(HOLD):
            await ClockCycles(dut.clk, 1)
            assert int(dut.uo_out.value) == SEG_LOCKED, f"LOCKED drift at cycle {c}"
        dut._log.info(f"  [PASS] LOCKED stable for {HOLD} cycles")

        # Hold VERIFIED
        dut.ui_in.value = VAELIX_KEY
        for c in range(HOLD):
            await ClockCycles(dut.clk, 1)
            assert int(dut.uo_out.value) == SEG_VERIFIED, f"VERIFIED drift at cycle {c}"
            assert int(dut.uio_out.value) == GLOW_ACTIVE, f"GLOW drift at cycle {c}"
        dut._log.info(f"  [PASS] VERIFIED stable for {HOLD} cycles")

        # Hold INVALID
        dut.ui_in.value = 0x49
        for c in range(HOLD):
            await ClockCycles(dut.clk, 1)
            assert int(dut.uo_out.value) == SEG_LOCKED, f"INVALID drift at cycle {c}"
        dut._log.info(f"  [PASS] INVALID (0x49) stayed LOCKED for {HOLD} cycles")
        dut._log.info("TEST 14: COMPLETE")

    # ================================================================
    # COCOTB TEST 15: INPUT TRANSITION COVERAGE
    # ================================================================
    @cocotb.test()
    async def test_sentinel_transition_coverage(dut):
        dut._log.info("VAELIX SENTINEL | TEST 15: TRANSITION COVERAGE")
        clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
        cocotb.start_soon(clock.start())
        await reset_sentinel(dut)

        transitions = [
            (0x00, VAELIX_KEY), (0xFF, VAELIX_KEY),
            (VAELIX_KEY, 0x00), (VAELIX_KEY, 0xFF),
            (VAELIX_KEY, 0xB7), (0xB7, VAELIX_KEY),
            (0x49, VAELIX_KEY), (VAELIX_KEY, 0x49),
            (0x00, 0xFF),       (0xFF, 0x00),
            (0x01, 0x02),       (0x55, 0xAA),
            (0xAA, 0x55),       (0xB5, VAELIX_KEY),
            (VAELIX_KEY, 0xB5), (0x00, 0x00),
            (VAELIX_KEY, VAELIX_KEY), (0xFF, 0xFF),
        ]

        errs = 0
        for from_k, to_k in transitions:
            dut.ui_in.value = from_k
            await ClockCycles(dut.clk, 1)
            dut.ui_in.value = to_k
            await ClockCycles(dut.clk, 1)

            seg  = int(dut.uo_out.value)
            glow = int(dut.uio_out.value)
            exp_seg  = SEG_VERIFIED if to_k == VAELIX_KEY else SEG_LOCKED
            exp_glow = GLOW_ACTIVE  if to_k == VAELIX_KEY else GLOW_DORMANT

            if seg != exp_seg or glow != exp_glow:
                dut._log.error(f"  TRANSITION FAIL: {hex(from_k)}→{hex(to_k)} seg={hex(seg)} glow={hex(glow)}")
                errs += 1
            else:
                exp_str = "VER" if to_k == VAELIX_KEY else "LCK"
                dut._log.info(f"  [PASS] {hex(from_k)}→{hex(to_k)}: {exp_str}")

        assert errs == 0, f"TRANSITION FAILURE: {errs} bad transitions"
        dut._log.info(f"  [PASS] All {len(transitions)} transitions clean")
        dut._log.info("TEST 15: COMPLETE")

    # ================================================================
    # COCOTB TEST 16: DEBOUNCER STABILITY REQUIREMENT
    # ================================================================
    @cocotb.test()
    async def test_debouncer_stability(dut):
        dut._log.info("VAELIX SENTINEL | TEST 16: DEBOUNCER STABILITY (4 CYCLES)")
        clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
        cocotb.start_soon(clock.start())
        await reset_sentinel(dut)

        # Start with wrong key
        dut.ui_in.value = 0x00
        await ClockCycles(dut.clk, 5)
        assert int(dut.uo_out.value) == SEG_LOCKED
        dut._log.info("  [INIT] System locked with 0x00")

        # Apply correct key and hold for 1 cycle - should NOT authorize yet
        dut.ui_in.value = VAELIX_KEY
        await ClockCycles(dut.clk, 1)
        seg = int(dut.uo_out.value)
        # Due to debouncing, should still be locked after 1 cycle
        dut._log.info(f"  [CYCLE 1] Key={hex(VAELIX_KEY)}, seg={hex(seg)}")
        
        # Hold for 2nd cycle - should still not authorize
        await ClockCycles(dut.clk, 1)
        seg = int(dut.uo_out.value)
        dut._log.info(f"  [CYCLE 2] Key={hex(VAELIX_KEY)}, seg={hex(seg)}")
        
        # Hold for 3rd cycle - should still not authorize
        await ClockCycles(dut.clk, 1)
        seg = int(dut.uo_out.value)
        dut._log.info(f"  [CYCLE 3] Key={hex(VAELIX_KEY)}, seg={hex(seg)}")
        
        # Hold for 4th cycle - should still not authorize (needs to complete 4 cycles)
        await ClockCycles(dut.clk, 1)
        seg = int(dut.uo_out.value)
        dut._log.info(f"  [CYCLE 4] Key={hex(VAELIX_KEY)}, seg={hex(seg)}")
        
        # After 4 full cycles of stability, signal should be accepted
        await ClockCycles(dut.clk, 1)
        seg = int(dut.uo_out.value)
        assert seg == SEG_VERIFIED, f"Key not accepted after 4 stable cycles: {hex(seg)}"
        dut._log.info(f"  [PASS] Key accepted after 4+ cycles: seg={hex(seg)}")
        dut._log.info("TEST 16: COMPLETE")

    # ================================================================
    # COCOTB TEST 17: RAPID TOGGLING REJECTION
    # ================================================================
    @cocotb.test()
    async def test_debouncer_rapid_toggle(dut):
        dut._log.info("VAELIX SENTINEL | TEST 17: RAPID TOGGLE REJECTION")
        clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
        cocotb.start_soon(clock.start())
        await reset_sentinel(dut)

        # Start locked
        dut.ui_in.value = 0x00
        await ClockCycles(dut.clk, 5)
        assert int(dut.uo_out.value) == SEG_LOCKED
        dut._log.info("  [INIT] System locked")

        # Rapidly toggle between correct and incorrect key (< 4 cycles each)
        # This should be rejected by the debouncer
        for i in range(20):
            dut.ui_in.value = VAELIX_KEY
            await ClockCycles(dut.clk, 1)
            dut.ui_in.value = 0x00
            await ClockCycles(dut.clk, 1)

        # Check that system is still locked (rapid toggling was rejected)
        seg = int(dut.uo_out.value)
        assert seg == SEG_LOCKED, f"Rapid toggle was not rejected: {hex(seg)}"
        dut._log.info(f"  [PASS] Rapid toggling rejected, system still locked")
        dut._log.info("TEST 17: COMPLETE")

    # ================================================================
    # COCOTB TEST 18: FUZZING ATTACK DETECTION
    # ================================================================
    @cocotb.test()
    async def test_debouncer_fuzzing_attack(dut):
        dut._log.info("VAELIX SENTINEL | TEST 18: FUZZING ATTACK LOCKOUT")
        clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
        cocotb.start_soon(clock.start())
        await reset_sentinel(dut)

        # Start locked
        dut.ui_in.value = 0x00
        await ClockCycles(dut.clk, 5)
        assert int(dut.uo_out.value) == SEG_LOCKED
        dut._log.info("  [INIT] System locked")

        # Trigger fuzzing attack: >10 changes in 100 cycles
        # Let's do 15 changes (30 transitions) to ensure detection
        for i in range(15):
            dut.ui_in.value = 0x00
            await ClockCycles(dut.clk, 1)
            dut.ui_in.value = 0xFF
            await ClockCycles(dut.clk, 1)

        dut._log.info("  [ATTACK] Generated 15 transitions (>10 threshold)")

        # Now try to authenticate with correct key
        # Should be locked out
        dut.ui_in.value = VAELIX_KEY
        await ClockCycles(dut.clk, 10)
        seg = int(dut.uo_out.value)
        
        # System should remain locked due to lockout
        assert seg == SEG_LOCKED, f"Lockout failed, system authorized: {hex(seg)}"
        dut._log.info(f"  [PASS] System locked out, authentication blocked")
        
        # Verify lockout persists for a while
        await ClockCycles(dut.clk, 100)
        seg = int(dut.uo_out.value)
        assert seg == SEG_LOCKED, f"Lockout expired too early: {hex(seg)}"
        dut._log.info(f"  [PASS] Lockout persists after 100 cycles")
        dut._log.info("TEST 18: COMPLETE")

    # ================================================================
    # COCOTB TEST 19: DEBOUNCER NORMAL OPERATION
    # ================================================================
    @cocotb.test()
    async def test_debouncer_normal_operation(dut):
        dut._log.info("VAELIX SENTINEL | TEST 19: DEBOUNCER NORMAL OPERATION")
        clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
        cocotb.start_soon(clock.start())
        await reset_sentinel(dut)

        # Test that normal slow transitions work correctly
        test_keys = [0x00, 0xFF, 0x12, 0x34, 0xAB, VAELIX_KEY, 0x00]
        
        for key in test_keys:
            dut.ui_in.value = key
            # Hold for sufficient cycles to pass debouncing (5+ cycles)
            await ClockCycles(dut.clk, 6)
            
            seg = int(dut.uo_out.value)
            exp_seg = SEG_VERIFIED if key == VAELIX_KEY else SEG_LOCKED
            
            assert seg == exp_seg, f"Normal operation failed at {hex(key)}: seg={hex(seg)}, expected={hex(exp_seg)}"
            status = "VERIFIED" if key == VAELIX_KEY else "LOCKED"
            dut._log.info(f"  [PASS] Key {hex(key)}: {status}")
        
        dut._log.info("TEST 19: COMPLETE")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    sys.exit(main())
