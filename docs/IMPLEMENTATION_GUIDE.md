# PDK Primitive Mapping - Implementation Guide
## How to Use the SG13G2 Mapping Resources

This guide explains how to leverage the PDK primitive mapping resources for Project Citadel.

---

## Quick Start

### 1. For Design Review & Understanding
**Use:** `docs/sg13g2_cell_reference.txt`

This quick reference provides:
- One-line behavioral → SG13G2 mappings
- Drive strength recommendations
- Port name conversions

**Best for:** Quick lookups during design review or code reading.

---

### 2. For Detailed Implementation
**Use:** `docs/pdk_primitive_mapping.md`

This comprehensive guide includes:
- Detailed cell-by-cell mapping with examples
- Port mapping diagrams
- Reset polarity conversion details
- Timing and verification considerations
- Implementation strategies

**Best for:** Synthesis planning, post-synthesis verification, documentation.

---

### 3. For Explicit Synthesis Mapping (Optional)
**Use:** `src/techmap_citadel_sg13g2.v`

This Yosys techmap file enables explicit control over cell selection.

**Usage in OpenLane/Yosys:**
```tcl
# In your synthesis script or flow
techmap -map src/techmap_citadel_sg13g2.v
```

**When to use:**
- Need explicit control over drive strength selection
- Want predictable cell mapping (not ABC optimization)
- Debugging synthesis issues
- Educational purposes to see exact mapping

**When NOT to use:**
- Default OpenLane flow (automatic mapping is usually better)
- Want optimal area/timing (ABC with Liberty files optimizes better)
- First-time synthesis runs (try automatic first)

---

## Common Use Cases

### Use Case 1: Gate-Level Simulation Setup
**Problem:** Need to simulate post-synthesis netlist with accurate timing.

**Solution:**
1. Refer to `docs/pdk_primitive_mapping.md` Section 4.1
2. Include SG13G2 standard cell Verilog models:
   ```makefile
   VERILOG_SOURCES += $(PDK_ROOT)/ihp-sg13g2/libs.ref/sg13g2_stdcell/verilog/sg13g2_stdcell.v
   ```
3. Set simulation defines: `-DFUNCTIONAL -DGL_TEST -DSIM`
4. Compare RTL vs. gate-level simulation results

---

### Use Case 2: Understanding Synthesis Reports
**Problem:** Synthesis report shows unfamiliar SG13G2 cell names.

**Solution:**
1. Open `docs/sg13g2_cell_reference.txt`
2. Look up the cell name (e.g., `sg13g2_and2_1`)
3. Find corresponding behavioral primitive (`and_cell`)
4. Check drive strength and optimization opportunities

---

### Use Case 3: Timing Closure Issues
**Problem:** Critical path failing timing with current cell selection.

**Solution:**
1. Identify cells on critical path from timing report
2. Check `docs/pdk_primitive_mapping.md` Section 3 for drive strength options
3. Options:
   - **Automatic:** Add timing constraints, re-synthesize
   - **Manual:** Use techmap with higher drive strength cells
   - **Hybrid:** Use synthesis attributes on specific instances

Example timing constraint:
```tcl
set_max_delay -from [get_pins buffer_cell/in] -to [get_pins buffer_cell/out] 2.0
```

---

### Use Case 4: Area Optimization
**Problem:** Design uses more area than expected.

**Solution:**
1. Review synthesis cell usage statistics
2. Check `docs/pdk_primitive_mapping.md` Section 5.2 for compound gates
3. Look for optimization patterns:
   - Multiple 2-input gates → single multi-input gate
   - Cascaded logic → AOI/OAI compound gates
   - Over-sized buffers → reduce drive strength

**Example Optimization:**
```
Before: AND(a,b) → AND(c,temp) → out
After:  sg13g2_and3_1(a,b,c,out)  // Single 3-input AND
```

---

### Use Case 5: Power Analysis
**Problem:** Need to estimate power consumption for different drive strengths.

**Solution:**
1. Refer to drive strength table in `docs/sg13g2_cell_reference.txt`
2. General rule: Higher drive = Higher power
3. Use Liberty files for accurate power modeling:
   ```
   ${PDK_ROOT}/ihp-sg13g2/libs.ref/sg13g2_stdcell/liberty/*.lib
   ```
4. Analyze across PVT corners (typical, fast, slow)

---

## Understanding Reset Polarity Conversion

**Critical:** Behavioral models use **active-high** reset; SG13G2 uses **active-low** RESET_B.

### Behavioral Model (Active-High)
```verilog
dffr_cell my_dff (
    .clk(clk),
    .d(data),
    .r(reset),      // Active-HIGH: 1 = reset
    .q(q)
);
```

### SG13G2 Mapping (Active-Low)
```verilog
wire reset_b = ~reset;  // Inversion needed!

sg13g2_dfrbp_1 my_dff (
    .CLK(clk),
    .D(data),
    .RESET_B(reset_b),  // Active-LOW: 0 = reset
    .Q(q)
);
```

**Impact:**
- Techmap file automatically adds inverters
- May affect timing (inverter delay)
- Ensures functional correctness

**Note:** The Sentinel design uses `rst_n` (already active-low), so it maps directly to `RESET_B` without inversion.

---

## Port Name Reference

| Function | Behavioral | SG13G2 | Example Cell |
|----------|-----------|---------|--------------|
| Input | `in` | `A` | `sg13g2_buf_1` |
| Output | `out` | `X` | `sg13g2_buf_1`, `sg13g2_and2_1` |
| Output | `out` | `Y` | `sg13g2_inv_1`, `sg13g2_nand2_1` |
| Inputs | `a, b` | `A, B` | All 2-input gates |
| Clock | `clk` | `CLK` | All flip-flops |
| Data | `d` | `D` | All flip-flops |
| Q output | `q` | `Q` | All flip-flops |
| Q_N output | `notq` | `Q_N` | Flip-flops with both outputs |
| Reset | `r` (high) | `RESET_B` (low) | `sg13g2_dfrbp_1` |
| Set | `s` (high) | `SET_B` (low) | `sg13g2_sdfbbp_1` |

---

## Integration with OpenLane Flow

### Default Flow (Recommended)
OpenLane automatically maps cells using:
1. **Yosys synthesis:** Uses ABC with SG13G2 Liberty files
2. **Optimization:** ABC selects optimal cells for area/timing
3. **Result:** Usually best QoR (Quality of Results)

**No action needed** - mapping happens automatically.

### Custom Flow (Advanced)
If you need explicit control:

```tcl
# In your custom synthesis script
# After initial synthesis
techmap -map src/techmap_citadel_sg13g2.v

# Continue with rest of flow
dfflibmap -liberty ${PDK_ROOT}/ihp-sg13g2/libs.ref/sg13g2_stdcell/liberty/sg13g2_stdcell_typ.lib
abc -liberty ${PDK_ROOT}/ihp-sg13g2/libs.ref/sg13g2_stdcell/liberty/sg13g2_stdcell_typ.lib
```

---

## Verification Checklist

After using these mapping resources:

- [ ] Behavioral simulation passes (RTL)
- [ ] Gate-level simulation passes (GL)
- [ ] RTL vs. GL simulation results match
- [ ] Timing analysis shows no violations
- [ ] Area meets design constraints
- [ ] Power consumption acceptable
- [ ] No DRC/LVS violations

---

## FAQ

### Q: Do I need to modify cells.v?
**A:** No. Keep `cells.v` as behavioral models. Synthesis maps them automatically.

### Q: When should I use the techmap file?
**A:** Only for explicit control or debugging. Default flow is usually better.

### Q: Why are there multiple drive strengths?
**A:** Different fanouts require different drive strengths. Higher fanout = higher drive needed.

### Q: What if I need a 3-input AND gate?
**A:** Synthesis will automatically use `sg13g2_and3_1` if it's optimal. See Section 5.2 in the detailed guide.

### Q: Can I mix behavioral and explicit SG13G2 cells?
**A:** Yes, but not recommended. Stick to one approach for consistency.

### Q: How do I choose drive strength?
**A:** Start with _1, upsize (_2, _4, _8) if timing fails. See drive strength guide in `sg13g2_cell_reference.txt`.

---

## Troubleshooting

### Problem: Synthesis fails to find SG13G2 cells
**Solution:** Ensure PDK_ROOT is set and points to IHP-Open-PDK installation.

### Problem: Gate-level simulation shows X's
**Solution:** Check that all SG13G2 primitive models are included and properly defined.

### Problem: Timing violations on flip-flops
**Solution:** Check clock distribution. May need higher drive buffers on clock tree.

### Problem: Techmap causes synthesis errors
**Solution:** Ensure SG13G2 primitives (tiehi, tielo) are available in your library.

---

## Next Steps

1. **First Time:** Read `docs/pdk_primitive_mapping.md` completely
2. **Daily Use:** Keep `docs/sg13g2_cell_reference.txt` handy for lookups
3. **Advanced:** Experiment with `src/techmap_citadel_sg13g2.v` on test designs
4. **Optimization:** Profile synthesis reports and iterate on cell selection

---

## Resources

- **IHP SG13G2 PDK:** https://github.com/IHP-GmbH/IHP-Open-PDK
- **Documentation:** https://ihp-open-designlib.readthedocs.io/
- **Liberty Files:** `${PDK_ROOT}/ihp-sg13g2/libs.ref/sg13g2_stdcell/liberty/`
- **Verilog Models:** `${PDK_ROOT}/ihp-sg13g2/libs.ref/sg13g2_stdcell/verilog/`

---

**Last Updated:** 2026-02-16  
**Version:** 1.0.0  
**Project:** Vaelix Systems - Project Citadel / Sentinel Mark I
