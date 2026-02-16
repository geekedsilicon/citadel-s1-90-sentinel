/*
 * ============================================================================
 * PROJECT CITADEL | TECHNOLOGY MAPPING FILE
 * ============================================================================
 * FILE:      techmap_citadel_sg13g2.v
 * VERSION:   1.0.0
 * PURPOSE:   Explicit technology mapping from Citadel behavioral primitives
 *            to IHP SG13G2 standard cell library
 * TARGET:    IHP 130nm SG13G2
 *
 * USAGE:
 *   This file can be used with Yosys to explicitly map the Citadel behavioral
 *   cells (defined in cells.v) to specific SG13G2 standard cell instances.
 *
 *   Yosys command:
 *     techmap -map techmap_citadel_sg13g2.v
 *
 * NOTES:
 *   - This techmap is OPTIONAL. Yosys with ABC and Liberty files will
 *     automatically map to SG13G2 cells.
 *   - Use this for explicit control over cell selection
 *   - Adjust drive strengths (_1, _2, _4, etc.) based on design needs
 *   - Current mappings use conservative drive strengths
 *
 * REFERENCES:
 *   - See docs/pdk_primitive_mapping.md for detailed mapping guide
 *   - See docs/sg13g2_cell_reference.txt for quick reference
 * ============================================================================
 */

`default_nettype none

/* ==========================================================================
 * 1. COMBINATIONAL LOGIC CELL MAPPINGS
 * ========================================================================== */

// BUFFER: Map to 2x drive strength buffer for moderate fanout
(* techmap_celltype = "buffer_cell" *)
module _techmap_buffer_cell (in, out);
    input in;
    output out;
    
    // Using _2 variant for good balance of drive and power
    sg13g2_buf_2 _TECHMAP_REPLACE_ (
        .A(in),
        .X(out)
    );
endmodule

// AND GATE: Map to standard 1x drive 2-input AND
(* techmap_celltype = "and_cell" *)
module _techmap_and_cell (a, b, out);
    input a, b;
    output out;
    
    sg13g2_and2_1 _TECHMAP_REPLACE_ (
        .A(a),
        .B(b),
        .X(out)
    );
endmodule

// OR GATE: Map to standard 1x drive 2-input OR
(* techmap_celltype = "or_cell" *)
module _techmap_or_cell (a, b, out);
    input a, b;
    output out;
    
    sg13g2_or2_1 _TECHMAP_REPLACE_ (
        .A(a),
        .B(b),
        .X(out)
    );
endmodule

// XOR GATE: Map to standard 2-input XOR
(* techmap_celltype = "xor_cell" *)
module _techmap_xor_cell (a, b, out);
    input a, b;
    output out;
    
    sg13g2_xor2_1 _TECHMAP_REPLACE_ (
        .A(a),
        .B(b),
        .X(out)
    );
endmodule

// NAND GATE: Map to standard 1x drive 2-input NAND
(* techmap_celltype = "nand_cell" *)
module _techmap_nand_cell (a, b, out);
    input a, b;
    output out;
    
    sg13g2_nand2_1 _TECHMAP_REPLACE_ (
        .A(a),
        .B(b),
        .Y(out)
    );
endmodule

// NOR GATE: Map to standard 1x drive 2-input NOR
(* techmap_celltype = "nor_cell" *)
module _techmap_nor_cell (a, b, out);
    input a, b;
    output out;
    
    sg13g2_nor2_1 _TECHMAP_REPLACE_ (
        .A(a),
        .B(b),
        .Y(out)
    );
endmodule

// XNOR GATE: Map to standard 2-input XNOR
(* techmap_celltype = "xnor_cell" *)
module _techmap_xnor_cell (a, b, out);
    input a, b;
    output out;
    
    sg13g2_xnor2_1 _TECHMAP_REPLACE_ (
        .A(a),
        .B(b),
        .Y(out)
    );
endmodule

// INVERTER: Map to standard 1x drive inverter
(* techmap_celltype = "not_cell" *)
module _techmap_not_cell (in, out);
    input in;
    output out;
    
    sg13g2_inv_1 _TECHMAP_REPLACE_ (
        .A(in),
        .Y(out)
    );
endmodule

// MULTIPLEXER: Map to standard 2-to-1 mux
// Note: Behavioral is out = sel ? b : a
//       SG13G2 is X = S ? A1 : A0
//       Mapping: A0 <- a, A1 <- b, S <- sel
(* techmap_celltype = "mux_cell" *)
module _techmap_mux_cell (a, b, sel, out);
    input a, b, sel;
    output out;
    
    sg13g2_mux2_1 _TECHMAP_REPLACE_ (
        .A0(a),    // Selected when S=0
        .A1(b),    // Selected when S=1
        .S(sel),
        .X(out)
    );
endmodule


/* ==========================================================================
 * 2. SEQUENTIAL LOGIC CELL MAPPINGS
 * ========================================================================== */

// D FLIP-FLOP (Basic, no reset)
// Challenge: SG13G2 doesn't have reset-less DFF
// Solution: Use DFF with reset and tie RESET_B high
(* techmap_celltype = "dff_cell" *)
module _techmap_dff_cell (clk, d, q, notq);
    input clk, d;
    output q, notq;
    
    // Create a constant high signal for unused reset
    // This will be optimized by synthesis
    wire reset_b_unused;
    sg13g2_tiehi tie_reset (
        .L_HI(reset_b_unused)
    );
    
    sg13g2_dfrbp_1 _TECHMAP_REPLACE_ (
        .D(d),
        .CLK(clk),
        .RESET_B(reset_b_unused),  // Tied high = reset inactive
        .Q(q),
        .Q_N(notq)
    );
endmodule

// D FLIP-FLOP with Asynchronous Reset
// Critical: Behavioral reset 'r' is active-HIGH
//           SG13G2 RESET_B is active-LOW
//           Must insert inverter
(* techmap_celltype = "dffr_cell" *)
module _techmap_dffr_cell (clk, d, r, q, notq);
    input clk, d, r;
    output q, notq;
    
    // Convert active-high reset to active-low
    wire reset_b;
    sg13g2_inv_1 reset_inverter (
        .A(r),
        .Y(reset_b)
    );
    
    sg13g2_dfrbp_1 _TECHMAP_REPLACE_ (
        .D(d),
        .CLK(clk),
        .RESET_B(reset_b),
        .Q(q),
        .Q_N(notq)
    );
endmodule

// D FLIP-FLOP with Set and Reset
// Critical: Behavioral s, r are active-HIGH
//           SG13G2 SET_B, RESET_B are active-LOW
//           Must insert inverters
//           Scan inputs must be tied off
(* techmap_celltype = "dffsr_cell" *)
module _techmap_dffsr_cell (clk, d, s, r, q, notq);
    input clk, d, s, r;
    output q, notq;
    
    // Convert active-high signals to active-low
    wire reset_b, set_b;
    sg13g2_inv_1 reset_inverter (
        .A(r),
        .Y(reset_b)
    );
    sg13g2_inv_1 set_inverter (
        .A(s),
        .Y(set_b)
    );
    
    // Create tie-off signals for scan chain (unused)
    wire scan_data_tie, scan_enable_tie;
    sg13g2_tielo tie_scan_data (
        .L_LO(scan_data_tie)
    );
    sg13g2_tielo tie_scan_enable (
        .L_LO(scan_enable_tie)
    );
    
    sg13g2_sdfbbp_1 _TECHMAP_REPLACE_ (
        .D(d),
        .CLK(clk),
        .RESET_B(reset_b),
        .SET_B(set_b),
        .SCD(scan_data_tie),     // Scan data = 0 (disabled)
        .SCE(scan_enable_tie),   // Scan enable = 0 (disabled)
        .Q(q),
        .Q_N(notq)
    );
endmodule


/* ==========================================================================
 * 3. MODULE CONTAINER (Required for techmap file)
 * ========================================================================== */

// Empty module to satisfy Verilog requirements
// The techmap cells above will replace the original cell instantiations
module techmap_citadel_sg13g2 ();
    // This module intentionally left empty
    // Techmap operates on the module definitions above
endmodule


/* ==========================================================================
 * REVISION NOTES
 * ==========================================================================
 *
 * Version 1.0.0 (2026-02-16):
 *   - Initial techmap file
 *   - All Citadel primitive cells mapped
 *   - Conservative drive strength selections
 *   - Reset polarity conversions implemented
 *   - Scan chain tie-offs for sequential cells
 *
 * Known Limitations:
 *   - Drive strengths are fixed (not adaptive)
 *   - For high-fanout nets, may need manual optimization
 *   - Techmap adds inverters for reset polarity - consider impact on timing
 *
 * Optimization Opportunities:
 *   - Could use parameterized techmap for drive strength selection
 *   - Could add fanout-based drive strength selection
 *   - Could leverage AOI/OAI cells for compound logic
 *
 * ========================================================================== */
