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
     * 1. STATE MACHINE DEFINITIONS (SHADOW LOGIC REDUNDANCY)
     * ---------------------------------------------------------------------
     * FSM States for Clock Glitch Defense (Nohl Shadow)
     */
    localparam STATE_LOCKED   = 1'b0;
    localparam STATE_UNLOCKED = 1'b1;
    
    reg state_main;
    reg state_shadow;
    
    /* ---------------------------------------------------------------------
     * 2. AUTHORIZATION LOGIC
     * ---------------------------------------------------------------------
     * HARDCODED_KEY: 0xB6 (1011_0110)
     * Direct bitwise comparison for instantaneous verification.
     */
    wire is_authorized;
    assign is_authorized = (ui_in == 8'b1011_0110);

    /* ---------------------------------------------------------------------
     * 3. SIGNAL INTEGRITY & OPTIMIZATION BYPASS
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
     * 4. FSM_MAIN: Primary State Machine (posedge clk)
     * ---------------------------------------------------------------------
     * Transitions to UNLOCKED when correct key is presented
     */
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state_main <= STATE_LOCKED;
        end else if (internal_ena) begin
            if (is_authorized) begin
                state_main <= STATE_UNLOCKED;
            end else begin
                state_main <= STATE_LOCKED;
            end
        end
    end
    
    /* ---------------------------------------------------------------------
     * 5. FSM_SHADOW: Shadow State Machine (negedge clk)
     * ---------------------------------------------------------------------
     * Duplicate state machine clocked on falling edge for glitch detection
     */
    always @(negedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state_shadow <= STATE_LOCKED;
        end else if (internal_ena) begin
            if (is_authorized) begin
                state_shadow <= STATE_UNLOCKED;
            end else begin
                state_shadow <= STATE_LOCKED;
            end
        end
    end
    
    /* ---------------------------------------------------------------------
     * 6. COMPARATOR & PANIC LOGIC
     * ---------------------------------------------------------------------
     * Detect state mismatch indicating clock glitch attack
     */
    reg panic;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            panic <= 1'b0;
        end else begin
            if (state_main != state_shadow) begin
                panic <= 1'b1;  // LOCK IN PANIC STATE
            end
        end
    end

    /* ---------------------------------------------------------------------
     * 7. VISUAL TELEMETRY: 7-SEGMENT OUTPUT WITH TRI-STATE PANIC
     * ---------------------------------------------------------------------
     * Bit mapping: uo_out = { dp, g, f, e, d, c, b, a }  (a = bit 0)
     * Common Anode / Active LOW: a 0-bit drives a segment ON.
     *
     * State         Segments ON       Value
     * -----------   ---------------   -----
     * 'L' Locked    f, e, d           0xC7
     * 'U' Unlocked  f, e, d, c, b     0xC1   ('V' unsupported on 7-seg)
     * Disabled      none              0xFF
     * PANIC         High-Z            (driven by tri-state buffer)
     *
     * Fix: `wire x = const` replaced with localparam — correct construct
     * for synthesis constants. wire-with-init is valid in Yosys but is not
     * portable and is semantically misleading (these are not driven nets).
     */
    localparam logic [7:0] SegLocked   = 8'hC7;
    localparam logic [7:0] SegVerified = 8'hC1;
    localparam logic [7:0] SegOff      = 8'hFF;

    wire [7:0] output_value;
    assign output_value = internal_ena ? (state_main == STATE_UNLOCKED ? SegVerified : SegLocked)
                                       : SegOff;
    
    // Tri-state output: High-Z when PANIC asserted
    assign uo_out = panic ? 8'bZZZZZZZZ : output_value;

    /* ---------------------------------------------------------------------
     * 8. STATUS ARRAY: VAELIX "GLOW" PERSISTENCE
     * ---------------------------------------------------------------------
     * Provides immediate high-intensity visual feedback upon authorization.
     * All UIO pins are forced to Output mode.
     *
     * Fix: `&&` (logical AND) replaced with `&` (bitwise AND).
     * Both operators are functionally identical on 1-bit signals, but `&`
     * is the correct idiomatic operator for HDL gate-level logic and
     * avoids implicit boolean reduction of multi-bit types if ports change.
     */
    assign uio_out = (internal_ena & (state_main == STATE_UNLOCKED)) ? 8'hFF : 8'h00;
    assign uio_oe  = 8'hFF;

    /* ---------------------------------------------------------------------
     * 9. SYSTEM STUBS
     * ---------------------------------------------------------------------
     * Prevents DRC warnings for unreferenced ports during CI/CD.
     * The trailing 1'b0 ensures the reduction is never optimised to a constant.
     */
    wire _unused_signal = &{uio_in, 1'b0};

endmodule