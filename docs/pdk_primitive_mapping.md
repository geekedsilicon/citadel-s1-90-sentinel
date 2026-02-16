# PDK PRIMITIVE MAPPING GUIDE
## IHP SG13G2 Standard Cell Library Mapping for Project Citadel

**Document Version:** 1.0.0  
**Target PDK:** IHP 130nm SG13G2  
**Purpose:** Bridge behavioral Verilog models with physical foundry primitives

---

## EXECUTIVE SUMMARY

This document provides the mapping between Project Citadel's behavioral logic primitives (defined in `src/cells.v`) and the IHP SG13G2 Standard Cell Library primitives. This mapping is essential for accurate post-synthesis simulation and improved timing/area estimation during the design flow.

**Key Benefits:**
- Improved post-synthesis accuracy
- Better timing correlation with physical implementation
- Optimized cell selection based on drive strength requirements
- Enhanced DRC/LVS compliance

---

## 1. COMBINATIONAL LOGIC PRIMITIVES

### 1.1 Buffer Cell
**Behavioral Model:** `buffer_cell`
```verilog
module buffer_cell (
    input  wire in,
    output wire out
);
```

**SG13G2 Mapping:**
| Cell Name | Drive Strength | Use Case |
|-----------|---------------|----------|
| `sg13g2_buf_1` | 1x (lowest) | Low fanout, signal conditioning |
| `sg13g2_buf_2` | 2x | Medium fanout |
| `sg13g2_buf_4` | 4x | High fanout |
| `sg13g2_buf_8` | 8x | Very high fanout |
| `sg13g2_buf_16` | 16x (highest) | Clock/critical path buffering |

**Port Mapping:**
```verilog
sg13g2_buf_1 instance_name (
    .X(out),  // Output
    .A(in)    // Input
);
```

**Recommendation:** For the Sentinel design, use `sg13g2_buf_2` for general signal integrity applications. The `internal_ena` signal can use `sg13g2_buf_1` due to low fanout.

---

### 1.2 AND Gate (2-input)
**Behavioral Model:** `and_cell`
```verilog
module and_cell (
    input  wire a,
    input  wire b,
    output wire out
);
```

**SG13G2 Mapping:**
| Cell Name | Drive Strength | Notes |
|-----------|---------------|-------|
| `sg13g2_and2_1` | 1x | Standard drive |
| `sg13g2_and2_2` | 2x | Higher drive for fanout |

**Port Mapping:**
```verilog
sg13g2_and2_1 instance_name (
    .X(out),  // Output
    .A(a),    // Input A
    .B(b)     // Input B
);
```

---

### 1.3 OR Gate (2-input)
**Behavioral Model:** `or_cell`
```verilog
module or_cell (
    input  wire a,
    input  wire b,
    output wire out
);
```

**SG13G2 Mapping:**
| Cell Name | Drive Strength | Notes |
|-----------|---------------|-------|
| `sg13g2_or2_1` | 1x | Standard drive |
| `sg13g2_or2_2` | 2x | Higher drive for fanout |

**Port Mapping:**
```verilog
sg13g2_or2_1 instance_name (
    .X(out),  // Output
    .A(a),    // Input A
    .B(b)     // Input B
);
```

---

### 1.4 XOR Gate (2-input)
**Behavioral Model:** `xor_cell`
```verilog
module xor_cell (
    input  wire a,
    input  wire b,
    output wire out
);
```

**SG13G2 Mapping:**
| Cell Name | Drive Strength | Notes |
|-----------|---------------|-------|
| `sg13g2_xor2_1` | 1x | Standard drive |

**Port Mapping:**
```verilog
sg13g2_xor2_1 instance_name (
    .X(out),  // Output
    .A(a),    // Input A
    .B(b)     // Input B
);
```

**Note:** XOR gates typically have higher delay and area than basic gates. Consider optimization opportunities.

---

### 1.5 NAND Gate (2-input)
**Behavioral Model:** `nand_cell`
```verilog
module nand_cell (
    input  wire a,
    input  wire b,
    output wire out
);
```

**SG13G2 Mapping:**
| Cell Name | Drive Strength | Notes |
|-----------|---------------|-------|
| `sg13g2_nand2_1` | 1x | Standard drive |
| `sg13g2_nand2_2` | 2x | Higher drive for fanout |

**Port Mapping:**
```verilog
sg13g2_nand2_1 instance_name (
    .Y(out),  // Output
    .A(a),    // Input A
    .B(b)     // Input B
);
```

---

### 1.6 NOR Gate (2-input)
**Behavioral Model:** `nor_cell`
```verilog
module nor_cell (
    input  wire a,
    input  wire b,
    output wire out
);
```

**SG13G2 Mapping:**
| Cell Name | Drive Strength | Notes |
|-----------|---------------|-------|
| `sg13g2_nor2_1` | 1x | Standard drive |
| `sg13g2_nor2_2` | 2x | Higher drive for fanout |

**Port Mapping:**
```verilog
sg13g2_nor2_1 instance_name (
    .Y(out),  // Output
    .A(a),    // Input A
    .B(b)     // Input B
);
```

---

### 1.7 XNOR Gate (2-input)
**Behavioral Model:** `xnor_cell`
```verilog
module xnor_cell (
    input  wire a,
    input  wire b,
    output wire out
);
```

**SG13G2 Mapping:**
| Cell Name | Drive Strength | Notes |
|-----------|---------------|-------|
| `sg13g2_xnor2_1` | 1x | Standard drive only |

**Port Mapping:**
```verilog
sg13g2_xnor2_1 instance_name (
    .Y(out),  // Output
    .A(a),    // Input A
    .B(b)     // Input B
);
```

---

### 1.8 Inverter (NOT Gate)
**Behavioral Model:** `not_cell`
```verilog
module not_cell (
    input  wire in,
    output wire out
);
```

**SG13G2 Mapping:**
| Cell Name | Drive Strength | Use Case |
|-----------|---------------|----------|
| `sg13g2_inv_1` | 1x | Low fanout |
| `sg13g2_inv_2` | 2x | Medium fanout |
| `sg13g2_inv_4` | 4x | High fanout |
| `sg13g2_inv_8` | 8x | Very high fanout |
| `sg13g2_inv_16` | 16x | Clock/critical paths |

**Port Mapping:**
```verilog
sg13g2_inv_1 instance_name (
    .Y(out),  // Output
    .A(in)    // Input
);
```

---

### 1.9 2-to-1 Multiplexer
**Behavioral Model:** `mux_cell`
```verilog
module mux_cell (
    input  wire a,
    input  wire b,
    input  wire sel,
    output wire out
);
```

**SG13G2 Mapping:**
| Cell Name | Drive Strength | Notes |
|-----------|---------------|-------|
| `sg13g2_mux2_1` | 1x | Standard drive |
| `sg13g2_mux2_2` | 2x | Higher drive for fanout |

**Port Mapping:**
```verilog
sg13g2_mux2_1 instance_name (
    .X(out),   // Output
    .A0(a),    // Input when S=0
    .A1(b),    // Input when S=1
    .S(sel)    // Select signal
);
```

**Important:** Note the select logic: `out = sel ? A1 : A0`

---

## 2. SEQUENTIAL LOGIC PRIMITIVES

### 2.1 D Flip-Flop (Basic)
**Behavioral Model:** `dff_cell`
```verilog
module dff_cell (
    input  wire clk,
    input  wire d,
    output reg  q,
    output wire notq
);
```

**SG13G2 Mapping Challenge:**
The SG13G2 library does not provide a simple D flip-flop without reset. All flip-flops include at least a reset input.

**Recommended Mapping:**
| Cell Name | Configuration | Notes |
|-----------|--------------|-------|
| `sg13g2_dfrbp_1` | Tie RESET_B high | Use with reset disabled |
| `sg13g2_dfrbpq_1` | Tie RESET_B high | Q-only version (no Q_N) |

**Port Mapping (with unused reset):**
```verilog
wire vdd_const = 1'b1;  // Tie-off for unused reset

sg13g2_dfrbp_1 instance_name (
    .Q(q),           // Output Q
    .Q_N(notq),      // Output Q_N (inverted)
    .D(d),           // Data input
    .CLK(clk),       // Clock
    .RESET_B(vdd_const)  // Reset tied inactive (active-low)
);
```

**Alternative:** Use synthesis directives to map to reset-less flip-flop if supported by the flow.

---

### 2.2 D Flip-Flop with Asynchronous Reset
**Behavioral Model:** `dffr_cell`
```verilog
module dffr_cell (
    input  wire clk,
    input  wire d,
    input  wire r,
    output reg  q,
    output wire notq
);
```

**SG13G2 Mapping:**
| Cell Name | Drive Strength | Outputs | Notes |
|-----------|---------------|---------|-------|
| `sg13g2_dfrbp_1` | 1x | Q, Q_N | Standard drive |
| `sg13g2_dfrbp_2` | 2x | Q, Q_N | Higher drive |
| `sg13g2_dfrbpq_1` | 1x | Q only | No inverted output |
| `sg13g2_dfrbpq_2` | 2x | Q only | No inverted output |

**Port Mapping:**
```verilog
wire reset_b = ~r;  // Convert active-high to active-low

sg13g2_dfrbp_1 instance_name (
    .Q(q),           // Output Q
    .Q_N(notq),      // Output Q_N (inverted)
    .D(d),           // Data input
    .CLK(clk),       // Clock
    .RESET_B(reset_b) // Active-low reset
);
```

**Critical Note:** The behavioral model uses active-high reset (`r`), but SG13G2 uses active-low reset (`RESET_B`). An inverter must be used for proper mapping.

---

### 2.3 D Flip-Flop with Set and Reset
**Behavioral Model:** `dffsr_cell`
```verilog
module dffsr_cell (
    input  wire clk,
    input  wire d,
    input  wire s,
    input  wire r,
    output reg  q,
    output wire notq
);
```

**SG13G2 Mapping:**
The SG13G2 library provides a scan flip-flop with set and reset functionality, but for simple set/reset operation, we need to tie off the scan inputs.

| Cell Name | Configuration | Notes |
|-----------|--------------|-------|
| `sg13g2_sdfbbp_1` | Disable scan chain | Full set/reset functionality |

**Port Mapping:**
```verilog
wire reset_b = ~r;     // Convert active-high to active-low
wire set_b = ~s;       // Convert active-high to active-low
wire scan_disable = 1'b0;  // Disable scan mode

sg13g2_sdfbbp_1 instance_name (
    .Q(q),           // Output Q
    .Q_N(notq),      // Output Q_N (inverted)
    .D(d),           // Data input
    .CLK(clk),       // Clock
    .RESET_B(reset_b), // Active-low reset
    .SET_B(set_b),   // Active-low set
    .SCD(1'b0),      // Scan data (tied low)
    .SCE(scan_disable) // Scan enable (disabled)
);
```

**Priority:** The SG13G2 cell implements `RESET > SET > DATA` priority, which matches the behavioral model.

---

## 3. SYNTHESIS DIRECTIVES

To guide the synthesis tool to use these mappings, you can create a technology mapping file for your synthesis tool (Yosys, Design Compiler, etc.).

### 3.1 Yosys Technology Mapping (Example)

For OpenLane/Yosys flows, the standard cell library is automatically mapped. However, you can create explicit mappings in a techmap file:

```verilog
// techmap_citadel_to_sg13g2.v
(* techmap_celltype = "buffer_cell" *)
module _techmap_buffer_cell (in, out);
    input in;
    output out;
    sg13g2_buf_2 _TECHMAP_REPLACE_ (.A(in), .X(out));
endmodule

(* techmap_celltype = "and_cell" *)
module _techmap_and_cell (a, b, out);
    input a, b;
    output out;
    sg13g2_and2_1 _TECHMAP_REPLACE_ (.A(a), .B(b), .X(out));
endmodule

// ... additional mappings ...
```

---

## 4. VERIFICATION CONSIDERATIONS

### 4.1 Gate-Level Simulation
When performing gate-level simulation (GLS), ensure:
1. Include the SG13G2 standard cell Verilog models from the PDK
2. Use the correct library path: `${PDK_ROOT}/ihp-sg13g2/libs.ref/sg13g2_stdcell/verilog/sg13g2_stdcell.v`
3. Set appropriate simulation defines: `-DFUNCTIONAL -DGL_TEST -DSIM`

### 4.2 Timing Considerations
- Drive strength selection impacts timing closure
- Critical paths may require higher drive strength variants
- Buffer insertion may be needed for high fanout nets

### 4.3 Power Considerations
- Higher drive strength cells consume more power
- Optimize drive strength based on actual fanout requirements
- Consider using clock gating cells for power optimization

---

## 5. ADDITIONAL SG13G2 RESOURCES

### 5.1 Complex Logic Gates
The SG13G2 library also provides compound gates that can optimize area and timing:

| Cell Type | Example | Description |
|-----------|---------|-------------|
| AOI (AND-OR-INVERT) | `sg13g2_a21oi_1` | (A1 & A2 \| B1)' |
| OAI (OR-AND-INVERT) | `sg13g2_o21ai_1` | (A1 \| A2 & B1)' |
| AOI22 | `sg13g2_a22oi_1` | (A1 & A2 \| B1 & B2)' |

These can be used by synthesis tools for optimization but are not directly mapped from the behavioral primitives.

### 5.2 Multi-Input Variants
The library includes 3-input and 4-input versions of basic gates:
- `sg13g2_and3_1`, `sg13g2_and4_1`
- `sg13g2_or3_1`, `sg13g2_or4_1`
- `sg13g2_nand3_1`, `sg13g2_nand4_1`
- `sg13g2_nor3_1`, `sg13g2_nor4_1`

These can provide better area/timing than cascaded 2-input gates.

---

## 6. IMPLEMENTATION RECOMMENDATIONS

### 6.1 For Project Citadel Sentinel
Based on the design analysis:

1. **System Enable Path (`buffer_cell` for `ena`):**
   - Map to: `sg13g2_buf_2`
   - Rationale: Moderate fanout to output logic

2. **Authorization Comparator:**
   - The `is_authorized` signal is purely combinational
   - No explicit cell instantiation needed
   - Synthesis will map to optimal gate network

3. **Output Multiplexers:**
   - Map behavioral mux to: `sg13g2_mux2_1`
   - Or allow synthesis to use AOI/OAI compounds for better optimization

4. **Future Sequential Logic:**
   - If FSM is added, use `sg13g2_dfrbp_1` for state registers
   - Utilize the active-low reset matching `rst_n` signal

### 6.2 Synthesis Strategy
1. **Option A - Behavioral Synthesis:**
   - Keep `cells.v` as behavioral models
   - Let synthesis map to SG13G2 cells automatically
   - Provides best optimization

2. **Option B - Explicit Mapping:**
   - Replace behavioral cells with SG13G2 instantiations
   - Provides more control over cell selection
   - Better post-synthesis accuracy
   - Recommended for critical paths only

3. **Option C - Hybrid Approach (RECOMMENDED):**
   - Keep behavioral models for synthesis
   - Use this mapping guide for post-synthesis verification
   - Annotate critical paths with synthesis constraints
   - Review synthesis reports and manually optimize bottlenecks

---

## 7. REFERENCES

- **IHP SG13G2 PDK:** https://github.com/IHP-GmbH/IHP-Open-PDK
- **Standard Cell Verilog:** `ihp-sg13g2/libs.ref/sg13g2_stdcell/verilog/sg13g2_stdcell.v`
- **Liberty Files:** `ihp-sg13g2/libs.ref/sg13g2_stdcell/liberty/`
- **Documentation:** https://ihp-open-designlib.readthedocs.io/

---

## REVISION HISTORY

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2026-02-16 | Vaelix Systems / Citadel Team | Initial PDK primitive mapping guide |

---

**CLASSIFICATION:** UNCLASSIFIED // FOR VAELIX ENGINEERING USE  
**DISTRIBUTION:** Approved for Tiny Tapeout 06 / IHP26a Fabrication  
**NEXT REVIEW:** Post-silicon validation
