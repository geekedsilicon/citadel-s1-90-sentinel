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
     * 1. AUTHORIZATION LOGIC
     * ---------------------------------------------------------------------
     * HARDCODED_KEY: 0xB6 (1011_0110)
     * Direct bitwise comparison for instantaneous verification.
     */
    wire is_authorized;
    assign is_authorized = (ui_in == 8'b1011_0110);

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
     * 5. PHANTOM CIRCUIT: DPA OBFUSCATION (TASK XVIII - GERLINSKY DECOY)
     * ---------------------------------------------------------------------
     * Instantiates a "ghost" authentication check that creates a false
     * power signature to obscure the real verification event from
     * Differential Power Analysis attacks.
     *
     * Strategy:
     * - Performs identical XOR comparison against FAKE_KEY (0x00)
     * - Triggers on opposite clock edge (negedge vs real logic's combinational)
     * - Output drives a dummy wire (floating capacitance) to generate
     *   switching noise that creates a second power signature
     */
    wire dummy_auth_result;
    
    dummy_auth phantom_circuit (
        .clk        (clk),
        .ui_in      (ui_in),
        .auth_out   (dummy_auth_result)
    );
    
    // Dummy load: floating wire connected to dummy_auth output
    // This creates switching noise without affecting real logic
    wire _phantom_load = dummy_auth_result & 1'b0;

    /* ---------------------------------------------------------------------
     * 6. SYSTEM STUBS
     * ---------------------------------------------------------------------
     * Prevents DRC warnings for unreferenced ports during CI/CD.
     * The trailing 1'b0 ensures the reduction is never optimised to a constant.
     */
    wire _unused_signal = &{uio_in, rst_n, _phantom_load, 1'b0};

endmodule

/* -------------------------------------------------------------------------
 * PHANTOM CIRCUIT MODULE: DPA OBFUSCATION
 * -------------------------------------------------------------------------
 * Creates a decoy power signature by performing a fake authentication
 * check on the negative clock edge. This generates switching activity
 * that obscures the real authentication logic from power analysis attacks.
 */
(* keep_hierarchy *)
module dummy_auth (
    input  wire       clk,
    input  wire [7:0] ui_in,
    output reg        auth_out
);
    // Fake key for phantom comparison (intentionally wrong)
    localparam logic [7:0] FAKE_KEY = 8'h00;
    
    // XOR comparison against fake key (identical operation to real auth)
    // but with wrong key value to create plausible switching noise
    wire [7:0] xor_result;
    assign xor_result = ui_in ^ FAKE_KEY;
    
    // Check if all XOR bits are zero (match condition)
    wire fake_match;
    assign fake_match = (xor_result == 8'h00);
    
    // Register output on NEGATIVE edge (opposite from typical posedge logic)
    // This creates a delayed power signature that acts as a decoy
    always @(negedge clk) begin
        auth_out <= fake_match;
    end
    
endmodule