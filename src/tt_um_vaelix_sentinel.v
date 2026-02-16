/*
 * ============================================================================
 * PROJECT CITADEL | SECURE PERIMETER GATE
 * ============================================================================
 * AUTHOR:    Vaelix Systems Engineering / R&D Division
 * MODULE:    tt_um_vaelix_sentinel
 * TARGET:    Tiny Tapeout 06 (IHP 130nm SG13G2)
 *
 * DESCRIPTION:
 * A hardware-level cryptographic "Challenge Coin." This module implements
 * the Sentinel Lock logic. System remains in state 'LOCKED' until the
 * 8-bit Vaelix Key (0xB6) is presented at the primary UI port.
 *
 * HARDWARE MAPPING:
 * - UI[7:0]:   External DIP Switches (Authorization Key)
 * - UO[7:0]:   7-Segment Display (Common Anode / Active LOW)
 * - UIO[7:0]:  Status Array (Vaelix "Glow" Persistence)
 * ============================================================================
 */
`default_nettype none

module tt_um_vaelix_sentinel (
    input  wire [7:0] ui_in,    // Dedicated inputs  — Key Interface
    output wire [7:0] uo_out,   // Dedicated outputs — Display Interface
    input  wire [7:0] uio_in,   // IOs: Input path   — Secondary Telemetry
    output wire [7:0] uio_out,  // IOs: Output path  — Status Array
    output wire [7:0] uio_oe,   // IOs: Enable path  — Port Directional Control
    input  wire       ena,      // Power-state enable
    input  wire       clk,      // System Clock
    input  wire       rst_n     // Global Reset (Active LOW)
);

    /* ---------------------------------------------------------------------
     * 1. AUTHORIZATION LOGIC — STRUCTURAL IMPLEMENTATION
     * ---------------------------------------------------------------------
     * HARDCODED_KEY: 0xB6 (1011_0110)
     * 
     * ARCHITECTURE:
     * This Key Comparator is implemented using explicit IHP SG13G2 standard
     * cells to enable precise control over physical placement and routing.
     * 
     * STAGE 1: Bit-level Equality (8x sg13g2_xnor2_1)
     *   - Each XNOR gate compares one bit of ui_in[7:0] against the
     *     corresponding bit of the hardcoded key 0xB6.
     *   - XNOR output is HIGH (1) when bits match, LOW (0) on mismatch.
     *   - Standard drive strength (_1) chosen for internal nodes to minimize
     *     power consumption and reduce parasitic capacitance.
     * 
     * STAGE 2: Hierarchical Reduction Tree (2x sg13g2_and4_1)
     *   - First level:  Combines bits [3:0] and [7:4] separately (2 AND4 gates)
     *   - Second level: Final AND of the two intermediate results
     *   - Result is HIGH only when ALL 8 bits match (is_authorized = 1)
     * 
     * RATIONALE FOR IHP PRIMITIVES:
     *   - sg13g2_xnor2_1: Optimal for bit equality checking (single gate vs.
     *     XOR + inverter). Lower drive strength (_1 suffix) reduces internal
     *     node power draw since these signals don't drive heavy loads.
     *   - sg13g2_and4_1: Efficient 4-input reduction. Using 4-input gates
     *     instead of cascaded 2-input gates reduces stage count and improves
     *     timing while maintaining compact layout.
     */
    
    // HARDCODED_KEY bits for comparison: 0xB6 = 1011_0110
    localparam [7:0] VAELIX_KEY = 8'b1011_0110;
    
    // Stage 1: Bit-level equality checking (8 XNOR gates)
    // Each comparator output is HIGH when corresponding bits match
    wire cmp_bit0, cmp_bit1, cmp_bit2, cmp_bit3;
    wire cmp_bit4, cmp_bit5, cmp_bit6, cmp_bit7;
    
    sg13g2_xnor2_1 xnor_bit0 (.A(ui_in[0]), .B(VAELIX_KEY[0]), .X(cmp_bit0));
    sg13g2_xnor2_1 xnor_bit1 (.A(ui_in[1]), .B(VAELIX_KEY[1]), .X(cmp_bit1));
    sg13g2_xnor2_1 xnor_bit2 (.A(ui_in[2]), .B(VAELIX_KEY[2]), .X(cmp_bit2));
    sg13g2_xnor2_1 xnor_bit3 (.A(ui_in[3]), .B(VAELIX_KEY[3]), .X(cmp_bit3));
    sg13g2_xnor2_1 xnor_bit4 (.A(ui_in[4]), .B(VAELIX_KEY[4]), .X(cmp_bit4));
    sg13g2_xnor2_1 xnor_bit5 (.A(ui_in[5]), .B(VAELIX_KEY[5]), .X(cmp_bit5));
    sg13g2_xnor2_1 xnor_bit6 (.A(ui_in[6]), .B(VAELIX_KEY[6]), .X(cmp_bit6));
    sg13g2_xnor2_1 xnor_bit7 (.A(ui_in[7]), .B(VAELIX_KEY[7]), .X(cmp_bit7));
    
    // Stage 2: Hierarchical AND reduction tree
    // Intermediate signals from first level of 4-input ANDs
    wire match_lower;  // Result of AND(cmp_bit[3:0])
    wire match_upper;  // Result of AND(cmp_bit[7:4])
    
    // First level: Combine lower and upper nibbles separately
    sg13g2_and4_1 and4_lower (
        .A(cmp_bit0), 
        .B(cmp_bit1), 
        .C(cmp_bit2), 
        .D(cmp_bit3), 
        .X(match_lower)
    );
    
    sg13g2_and4_1 and4_upper (
        .A(cmp_bit4), 
        .B(cmp_bit5), 
        .C(cmp_bit6), 
        .D(cmp_bit7), 
        .X(match_upper)
    );
    
    // Second level: Final authorization signal (AND of both nibble matches)
    // Using sg13g2_and2_1 to maintain consistency with IHP standard cell usage
    wire is_authorized;
    sg13g2_and2_1 final_and (
        .A(match_lower),
        .B(match_upper),
        .X(is_authorized)
    );

    /* ---------------------------------------------------------------------
     * 2. SIGNAL INTEGRITY & OPTIMIZATION BYPASS
     * ---------------------------------------------------------------------
     * The 'buffer_cell' (defined in cells.v, compiled together by TT build)
     * is our structural signature. Gating outputs with 'internal_ena'
     * prevents synthesis tools from pruning the instance as dead logic.
     */
    wire internal_ena;
    buffer_cell sys_ena (
        .in  (ena),
        .out (internal_ena)
    );

    /* ---------------------------------------------------------------------
     * 3. VISUAL TELEMETRY: 7-SEGMENT OUTPUT
     * ---------------------------------------------------------------------
     * Bit mapping: uo_out = { dp, g, f, e, d, c, b, a }  (a = bit 0)
     * Common Anode / Active LOW: a 0-bit drives a segment ON.
     *
     * State         Segments ON       Value
     * -----------   ---------------   -----
     * 'L' Locked    f, e, d           0xC7
     * 'U' Unlocked  f, e, d, c, b     0xC1   ('V' unsupported on 7-seg)
     * Disabled      none              0xFF
     *
     * Fix: `wire x = const` replaced with localparam — correct construct
     * for synthesis constants. wire-with-init is valid in Yosys but is not
     * portable and is semantically misleading (these are not driven nets).
     */
    localparam logic [7:0] SegLocked   = 8'hC7;
    localparam logic [7:0] SegVerified = 8'hC1;
    localparam logic [7:0] SegOff      = 8'hFF;

    assign uo_out = internal_ena ? (is_authorized ? SegVerified : SegLocked)
                                 : SegOff;

    /* ---------------------------------------------------------------------
     * 4. STATUS ARRAY: VAELIX "GLOW" PERSISTENCE
     * ---------------------------------------------------------------------
     * Provides immediate high-intensity visual feedback upon authorization.
     * All UIO pins are forced to Output mode.
     *
     * Fix: `&&` (logical AND) replaced with `&` (bitwise AND).
     * Both operators are functionally identical on 1-bit signals, but `&`
     * is the correct idiomatic operator for HDL gate-level logic and
     * avoids implicit boolean reduction of multi-bit types if ports change.
     */
    assign uio_out = (internal_ena & is_authorized) ? 8'hFF : 8'h00;
    assign uio_oe  = 8'hFF;

    /* ---------------------------------------------------------------------
     * 5. SYSTEM STUBS
     * ---------------------------------------------------------------------
     * Prevents DRC warnings for unreferenced ports during CI/CD.
     * The trailing 1'b0 ensures the reduction is never optimised to a constant.
     */
    wire _unused_signal = &{uio_in, clk, rst_n, 1'b0};

endmodule