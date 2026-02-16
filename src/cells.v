/*
 * ============================================================================
 * PROJECT CITADEL | ELEMENTAL LOGIC PRIMITIVES
 * ============================================================================
 * AUTHOR:    Vaelix Systems Engineering / R&D Division
 * MODULE:    cells
 * TARGET:    Tiny Tapeout 06 (IHP 130nm SG13G2)
 *
 * DESCRIPTION:
 * Mapping layer for Wokwi primitive modules to Vaelix-standard logic gates.
 * All modules include 'keep_hierarchy' to preserve netlist structural
 * integrity during the OpenLane synthesis flow.
 *
 * LINTING & DIRECTIVES:
 * - `default_nettype none: Enforces explicit declaration of all nets.
 * - Bitwise Operators (~, &, |): Preferred for physical gate mapping.
 * - DECLFILENAME disabled: This file intentionally contains multiple modules.
 * ============================================================================
 */

/* verilator lint_off DECLFILENAME */
`default_nettype none

// CITADEL_CELLS: Mapping layer for Wokwi primitive modules to Vaelix-standard logic gates.
(* keep_hierarchy *)
module cells ();
endmodule

/* ---------------------------------------------------------------------
 * 1. COMBINATIONAL LOGIC PRIMITIVES
 * --------------------------------------------------------------------- */

// CITADEL_BUFFER: Signal conditioning and mesh synchronization.
(* keep_hierarchy *)
module buffer_cell (
    input  wire in,
    output wire out
);
    assign out = in;
endmodule

// CITADEL_AND: Conjunction logic for multi-factor verification.
(* keep_hierarchy *)
module and_cell (
    input  wire a,
    input  wire b,
    output wire out
);
    assign out = a & b;
endmodule

// CITADEL_OR: Redundancy logic for system failovers.
(* keep_hierarchy *)
module or_cell (
    input  wire a,
    input  wire b,
    output wire out
);
    assign out = a | b;
endmodule

// CITADEL_XOR: Parity and cryptographic scrambling.
(* keep_hierarchy *)
module xor_cell (
    input  wire a,
    input  wire b,
    output wire out
);
    assign out = a ^ b;
endmodule

// CITADEL_NAND: Universal fundamental logic gate.
(* keep_hierarchy *)
module nand_cell (
    input  wire a,
    input  wire b,
    output wire out
);
    assign out = ~(a & b);
endmodule

// CITADEL_NOR: Hardened system rejection logic.
(* keep_hierarchy *)
module nor_cell (
    input  wire a,
    input  wire b,
    output wire out
);
    assign out = ~(a | b);
endmodule

// CITADEL_XNOR: Hardware-level equivalence verification.
(* keep_hierarchy *)
module xnor_cell (
    input  wire a,
    input  wire b,
    output wire out
);
    assign out = ~(a ^ b);
endmodule

// CITADEL_NOT: Logical inversion for secure signal routing.
(* keep_hierarchy *)
module not_cell (
    input  wire in,
    output wire out
);
    assign out = ~in;
endmodule

// CITADEL_MUX: Dynamic data routing for the Sentinel Mesh.
(* keep_hierarchy *)
module mux_cell (
    input  wire a,
    input  wire b,
    input  wire sel,
    output wire out
);
    assign out = sel ? b : a;
endmodule


/* ---------------------------------------------------------------------
 * 2. SEQUENTIAL LOGIC PRIMITIVES (MEMORY)
 * --------------------------------------------------------------------- */

// CITADEL_DFF: Standard state persistence cell.
(* keep_hierarchy *)
module dff_cell (
    input  wire clk,
    input  wire d,
    output reg  q,
    output wire notq
);
    assign notq = ~q;
    always @(posedge clk)
        q <= d;
endmodule

// CITADEL_DFFR: Memory cell with Asynchronous Hard Reset (Tactical Wipe).
(* keep_hierarchy *)
module dffr_cell (
    input  wire clk,
    input  wire d,
    input  wire r,
    output reg  q,
    output wire notq
);
    assign notq = ~q;
    always @(posedge clk or posedge r) begin
        if (r)
            q <= 1'b0;
        else
            q <= d;
    end
endmodule

// CITADEL_DFFSR: Asynchronous Set/Reset Memory cell.
// Priority Architecture: Reset > Set > Capture.
(* keep_hierarchy *)
module dffsr_cell (
    input  wire clk,
    input  wire d,
    input  wire s,
    input  wire r,
    output reg  q,
    output wire notq
);
    assign notq = ~q;
    always @(posedge clk or posedge s or posedge r) begin
        if (r)
            q <= 1'b0;
        else if (s)
            q <= 1'b1;
        else
            q <= d;
    end
endmodule
