# Example Workflow: Using the Telemetry Analyzer

This document demonstrates a complete workflow using the `analyze_telemetry.py` script.

## Scenario 1: Local Development

### Step 1: Run Tests
```bash
cd test
make -B  # Run all Cocotb tests
```

### Step 2: Generate Report
```bash
cd ..
python analyze_telemetry.py \
  --results-xml test/results.xml \
  --fst-file test/tb.fst \
  --output reports/debrief_$(date +%Y%m%d_%H%M%S).md
```

### Step 3: View Results
```bash
cat reports/debrief_*.md
```

### Step 4: If Tests Failed - View Waveforms
```bash
# Open GTKWave at specific failure timestamp
gtkwave test/tb.fst test/tb.gtkw
# In GTKWave: View > Go To Time > enter timestamp from report (e.g., "340.0 ns")
```

---

## Scenario 2: CI/CD Integration (GitHub Actions)

The workflow automatically runs after tests complete:

```yaml
- name: Run Tests
  run: |
    cd test
    make -B

- name: Generate Mission Debrief
  if: always()
  run: |
    python analyze_telemetry.py \
      --results-xml test/results.xml \
      --fst-file test/tb.fst \
      --output MISSION_DEBRIEF.md

- name: Upload Artifacts
  uses: actions/upload-artifact@v4
  with:
    name: test-artifacts
    path: |
      test/*.fst
      test/results.xml
      MISSION_DEBRIEF.md
```

---

## Scenario 3: Update Project Documentation

```bash
# Run tests
cd test && make -B && cd ..

# Update README.md automatically
python analyze_telemetry.py --update-readme

# Commit results
git add README.md
git commit -m "docs: Update test results"
git push
```

---

## Sample Report Output

### All Tests Passing

```markdown
# 🔍 MISSION DEBRIEF — SENTINEL INTERROGATION REPORT

**Generated:** 2026-02-16 06:59:33 UTC
**Results File:** `results.xml`

---

## 📊 EXECUTIVE SUMMARY

| Metric | Value |
|--------|-------|
| **Total Tests** | 15 |
| **✅ Passed** | 15 |
| **❌ Failed** | 0 |
| **Success Rate** | 100.0% |

## ✅ MISSION STATUS: **VERIFIED**

All tests passed. The Sentinel Mark I logic is fully verified.
No defects detected. Authorization protocol confirmed.
```

### With Test Failures

```markdown
## ⚠️ MISSION STATUS: **COMPROMISED**

**2** test(s) failed. Immediate investigation required.

---

## 🚨 FAILURE ANALYSIS

### Test 4: `test_sentinel_bitflip_adjacency`

- **Status:** ❌ FAILED
- **Duration:** 2.123s
- **Failure Type:** `AssertionError`
- **Failure Timestamp:** `340.0 ns`

**Error Message:**
```
H1 BREACH bit 3 (0xbe): 0xc1
```

**Traceback:**
```
Traceback (most recent call last):
  File "test.py", line 999, in test_sentinel_bitflip_adjacency
    assert int(dut.uo_out.value) == SEG_LOCKED, ...
AssertionError: H1 BREACH bit 3 (0xbe): 0xc1
Failure occurred at simulation time: 340.0 ns
```
```

---

## Exit Codes

- `0`: All tests passed
- `1`: One or more tests failed  
- `2`: Results file not found
- `3`: Unexpected error

Example:
```bash
python analyze_telemetry.py
if [ $? -eq 0 ]; then
  echo "✅ All tests passed!"
else
  echo "❌ Tests failed - check report"
fi
```

---

## Tips and Tricks

### 1. Quick Status Check
```bash
# Just check if tests passed
python analyze_telemetry.py > /dev/null 2>&1 && echo "PASS" || echo "FAIL"
```

### 2. Archive Reports
```bash
# Create dated archive
mkdir -p reports/$(date +%Y%m)
python analyze_telemetry.py --output reports/$(date +%Y%m)/debrief_$(git rev-parse --short HEAD).md
```

### 3. Compare with Previous Run
```bash
# Generate current report
python analyze_telemetry.py --output current.md

# Compare with baseline
diff baseline_debrief.md current.md
```

### 4. Extract Failure Count
```bash
# Parse failure count from output
python analyze_telemetry.py 2>&1 | grep "Found" | awk '{print $8}'
```

---

**VAELIX SYSTEMS** | *Tier 1 Defense Technology*
