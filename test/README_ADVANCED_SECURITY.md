# Advanced Security Testing — The Prosecutor

## Overview

`test_advanced_security.py` is a comprehensive timing-attack simulation suite for the S1-90 Sentinel Lock. This module performs advanced security characterization beyond functional testing.

## Purpose

This test suite was created to fulfill **TASK II: BRUTE-FORCE TEST GENERATION (THE PROSECUTOR)** — moving beyond functional testing into Security Characterization through timing-attack simulation.

## Requirements

- Python 3.8+
- Cocotb 2.0+
- Icarus Verilog (iverilog)
- pytest 8.3+

Install dependencies:
```bash
pip install -r requirements.txt
sudo apt-get install iverilog  # On Ubuntu/Debian
```

## Running the Tests

### Run Advanced Security Tests Only

```bash
cd test
make COCOTB_TEST_MODULES=test_advanced_security
```

### Run Original Functional Tests

```bash
cd test
make
# or
make COCOTB_TEST_MODULES=test
```

### Run All Tests (Sequential)

```bash
cd test
# Run functional tests
make
# Run security tests
make COCOTB_TEST_MODULES=test_advanced_security
```

## Test Suite Contents

The module contains 10 comprehensive timing-attack tests:

### 1. Pre-Edge Key Injection (`test_timing_attack_pre_edge`)
Tests key injection at various times before the rising clock edge (T-30ns to T-1ns).

**Attack Vector:** Early key arrival  
**Expected:** Correct authentication at clock edge  
**Verifies:** No early evaluation or timing leaks

### 2. Post-Edge Key Injection (`test_timing_attack_post_edge`)
Tests key injection at various times after the rising clock edge (T+1ns to T+30ns).

**Attack Vector:** Late key arrival  
**Expected:** Immediate combinational response  
**Verifies:** No post-edge timing dependencies

### 3. Falling-Edge Key Injection (`test_timing_attack_falling_edge`)
Tests key injection around the falling clock edge.

**Attack Vector:** Non-standard clock edge timing  
**Expected:** Correct operation (edge-insensitive)  
**Verifies:** No falling-edge dependencies

### 4. Bit-by-Bit Temporal Injection (`test_timing_attack_bit_by_bit`)
Tests sequential bit injection with varying delays to detect metastability.

**Attack Vector:** Partial key injection  
**Expected:** Only complete key authorizes  
**Verifies:** No bit-wise timing leaks, metastability resistance

### 5. Rapid Key Toggling (`test_timing_attack_rapid_toggle`)
Tests rapid key toggling to attempt glitch-induced authorization.

**Attack Vector:** High-frequency glitch injection  
**Expected:** No unauthorized states  
**Verifies:** Glitch immunity, correct state recovery

### 6. Exhaustive Clock Phase Sweep (`test_timing_attack_all_clock_phases`)
Tests key injection at all phases of the clock cycle (0°-360°).

**Attack Vector:** Phase-dependent behavior  
**Expected:** Correct operation at all phases  
**Verifies:** Clock-phase independence

### 7. Setup/Hold Time Violation (`test_timing_attack_setup_hold_violation`)
Tests key changes very close to clock edges to violate timing constraints.

**Attack Vector:** Setup/hold time violations  
**Expected:** Secure behavior despite violations  
**Verifies:** Timing constraint immunity

### 8. Simultaneous Key and Reset (`test_timing_attack_key_with_reset`)
Tests race conditions between key and reset signal.

**Attack Vector:** Reset timing manipulation  
**Expected:** Correct reset priority  
**Verifies:** Reset atomicity, no race conditions

### 9. Clock Frequency Variation (`test_timing_attack_clock_frequency_variation`)
Tests system at multiple clock frequencies (10MHz, 25MHz, 50MHz).

**Attack Vector:** Frequency-dependent vulnerabilities  
**Expected:** Correct operation at all frequencies  
**Verifies:** Frequency-independent security

### 10. Comprehensive Edge Case Battery (`test_timing_attack_comprehensive_edge_cases`)
Tests various edge cases including zero-duration pulses, enable transitions, etc.

**Attack Vector:** Corner case exploitation  
**Expected:** All edge cases handled securely  
**Verifies:** Comprehensive edge case coverage

## Test Results

All 10 tests **PASS** on the S1-90 Sentinel Lock design:

```
** TESTS=10 PASS=10 FAIL=0 SKIP=0 **
```

See `SECURITY_CHARACTERIZATION.md` for detailed security analysis.

## Understanding Test Output

Each test produces verbose logging showing:
- Test phase and timing parameters
- Key injection points relative to clock edges
- Expected vs. actual outputs
- Pass/fail status for each sub-test

Example output:
```
PROSECUTOR TEST 1: PRE-EDGE KEY INJECTION TIMING ATTACK
--- Testing key injection 30ns before rising edge ---
  Key injected at T-30ns
  [PASS] Correct authorization at T-30ns pre-edge
```

## Key Assertions

Tests verify:
- `uo_out == SEG_LOCKED (0xC7)` when key is invalid
- `uo_out == SEG_VERIFIED (0xC1)` when key is valid (0xB6)
- `uio_out == GLOW_ACTIVE (0xFF)` when authorized
- `uio_out == GLOW_DORMANT (0x00)` when locked

## Security Properties Verified

✅ **Clock-phase independence** - Works at all clock phases  
✅ **Frequency independence** - Works at 10-50 MHz  
✅ **Metastability resistance** - No partial key acceptance  
✅ **Glitch immunity** - No glitch-induced authorization  
✅ **Reset atomicity** - No reset race conditions  

## Design Notes

The S1-90 Sentinel uses **purely combinational logic**, which provides inherent immunity to many timing attacks:
- No internal state to exploit
- Output responds immediately to input
- No sequential logic timing dependencies
- No clock-edge-dependent behavior

## Extending the Tests

To add new timing-attack tests:

1. Add a new test function with `@cocotb.test()` decorator
2. Follow the naming convention: `test_timing_attack_*`
3. Use the helper function `reset_sentinel(dut)` for initialization
4. Use cocotb triggers: `RisingEdge`, `FallingEdge`, `Timer`, `ClockCycles`
5. Assert expected behavior with descriptive error messages

Example:
```python
@cocotb.test()
async def test_timing_attack_custom(dut):
    """Custom timing attack test"""
    dut._log.info("PROSECUTOR TEST: CUSTOM ATTACK")
    
    clock = Clock(dut.clk, CLOCK_PERIOD_NS, unit="ns")
    cocotb.start_soon(clock.start())
    await reset_sentinel(dut)
    
    # Your test logic here
    
    dut._log.info("TEST COMPLETE")
```

## References

- Original Test Suite: `test.py`
- Hardware Design: `../src/tt_um_vaelix_sentinel.v`
- Security Report: `SECURITY_CHARACTERIZATION.md`
- Cocotb Documentation: https://docs.cocotb.org/

## License

SPDX-License-Identifier: Apache-2.0

---

**Module:** test_advanced_security.py  
**Version:** 1.0  
**Created:** 2026-02-16  
**Author:** TASK II — The Prosecutor  
**Standard:** Vaelix Missionary Standard v1.2
