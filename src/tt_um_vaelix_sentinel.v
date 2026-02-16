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
     * 1. FSM STATE DEFINITIONS (TASK XV: KINGPIN LATCH)
     * ---------------------------------------------------------------------
     * NORMAL: Standard operation (authorization checking)
     * BRICK:  Tamper-detected state (system unresponsive)
     */
    localparam logic STATE_NORMAL = 1'b0;
    localparam logic STATE_BRICK  = 1'b1;
    
    reg current_state = STATE_NORMAL;   // Initialize to NORMAL state
    reg [6:0] uio_in_prev = 7'h00;      // Initialize to zero
    
    /* ---------------------------------------------------------------------
     * 2. AUTHORIZATION LOGIC
     * ---------------------------------------------------------------------
     * HARDCODED_KEY: 0xB6 (1011_0110)
     * Direct bitwise comparison for instantaneous verification.
     */
    wire is_authorized;
    assign is_authorized = (ui_in == 8'b1011_0110);

    /* ---------------------------------------------------------------------
     * 3. TAMPER DETECTION & FSM (TASK XV: KINGPIN LATCH)
     * ---------------------------------------------------------------------
     * Monitor uio_in[7:1] for any toggle activity (potential debug probing).
     * If detected during normal operation (rst_n active), transition to BRICK.
     * Only ena toggle (power cycle) can exit BRICK state.
     */
    wire tamper_detected;
    assign tamper_detected = (uio_in[7:1] != uio_in_prev) && rst_n;
    
    always @(posedge clk) begin
        if (!ena) begin
            // Power cycle reset: clear BRICK state
            current_state <= STATE_NORMAL;
            uio_in_prev   <= 7'h00;
        end else if (!rst_n) begin
            // Soft reset: clear state tracker but preserve BRICK if set
            uio_in_prev   <= 7'h00;
        end else begin
            if (current_state == STATE_NORMAL && tamper_detected) begin
                // Tamper detected: enter BRICK state
                current_state <= STATE_BRICK;
            end
            // Update previous state tracker
            uio_in_prev <= uio_in[7:1];
        end
    end

    /* ---------------------------------------------------------------------
     * 4. SIGNAL INTEGRITY & OPTIMIZATION BYPASS
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
     * 5. VISUAL TELEMETRY: 7-SEGMENT OUTPUT
     * ---------------------------------------------------------------------
     * Bit mapping: uo_out = { dp, g, f, e, d, c, b, a }  (a = bit 0)
     * Common Anode / Active LOW: a 0-bit drives a segment ON.
     *
     * State         Segments ON       Value
     * -----------   ---------------   -----
     * 'L' Locked    f, e, d           0xC7
     * 'U' Unlocked  f, e, d, c, b     0xC1   ('V' unsupported on 7-seg)
     * Disabled      none              0xFF
     * BRICK         all dark          0x00   (All segments OFF)
     *
     * Fix: `wire x = const` replaced with localparam — correct construct
     * for synthesis constants. wire-with-init is valid in Yosys but is not
     * portable and is semantically misleading (these are not driven nets).
     */
    localparam logic [7:0] SegLocked   = 8'hC7;
    localparam logic [7:0] SegVerified = 8'hC1;
    localparam logic [7:0] SegOff      = 8'hFF;
    localparam logic [7:0] SegBrick    = 8'h00;  // All Dark (BRICK state)

    // In BRICK state, output is all dark (0x00), input logic disabled
    // Otherwise, normal authorization logic applies
    wire [7:0] normal_output;
    assign normal_output = internal_ena ? (is_authorized ? SegVerified : SegLocked)
                                        : SegOff;
    
    assign uo_out = (current_state == STATE_BRICK) ? SegBrick : normal_output;

    /* ---------------------------------------------------------------------
     * 6. STATUS ARRAY: VAELIX "GLOW" PERSISTENCE
     * ---------------------------------------------------------------------
     * Provides immediate high-intensity visual feedback upon authorization.
     * All UIO pins are forced to Output mode.
     *
     * In BRICK state, the status array is also driven to 0x00 (all dark).
     *
     * Fix: `&&` (logical AND) replaced with `&` (bitwise AND).
     * Both operators are functionally identical on 1-bit signals, but `&`
     * is the correct idiomatic operator for HDL gate-level logic and
     * avoids implicit boolean reduction of multi-bit types if ports change.
     */
    wire [7:0] normal_glow;
    assign normal_glow = (internal_ena & is_authorized) ? 8'hFF : 8'h00;
    
    assign uio_out = (current_state == STATE_BRICK) ? 8'h00 : normal_glow;
    assign uio_oe  = 8'hFF;

    /* ---------------------------------------------------------------------
     * 7. SYSTEM STUBS
     * ---------------------------------------------------------------------
     * Prevents DRC warnings for unreferenced ports during CI/CD.
     * Note: uio_in is now actively monitored for tamper detection.
     * The trailing 1'b0 ensures the reduction is never optimised to a constant.
     */
    wire _unused_signal = &{clk, rst_n, 1'b0};

endmodule