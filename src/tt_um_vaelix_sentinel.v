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
     * 1. AUTHORIZATION LOGIC WITH KEY REGISTER
     * ---------------------------------------------------------------------
     * HARDCODED_KEY: 0xB6 (1011_0110)
     * Direct bitwise comparison for instantaneous verification.
     * 
     * KEY REGISTER: Stores authorization state. Can be erased by tamper detection.
     * This register maintains the verified state across clock cycles and provides
     * a target for tamper-triggered erasure (Huang Loopback requirement).
     */
    wire key_match;
    assign key_match = (ui_in == 8'b1011_0110);
    
    reg  key_register;
    wire is_authorized;
    
    // Authorization requires both correct key AND untampered key register
    assign is_authorized = key_match & key_register;

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
     * 5. OUTPUT INTEGRITY MONITORING (HUANG LOOPBACK)
     * ---------------------------------------------------------------------
     * Andrew "bunnie" Huang warns: external attackers may force output pins
     * LOW even when we drive HIGH, to hide "Verified" status.
     * 
     * MECHANISM:
     * - Even though uio_out drives as outputs, we read back via uio_in
     * - Compare driven value (uio_out) with read-back value (uio_in)
     * - If mismatch persists for 2+ clock cycles → DRIVE FIGHT detected
     * - Assert TAMPER_DETECT to erase key_register
     * 
     * NOTE: uio_oe = 8'hFF means all UIO pins are outputs, but the GPIO
     * cells (sg13g2_io) maintain input buffers (IB_MODE) allowing loopback.
     */
    reg [1:0] drive_fight_counter;
    wire      drive_fight_detected;
    wire      tamper_detect;
    
    // Detect mismatch between what we're driving and what we're reading
    assign drive_fight_detected = (uio_out != uio_in);
    
    // Count consecutive mismatches
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            drive_fight_counter <= 2'b00;
        end else if (drive_fight_detected) begin
            // Increment counter if mismatch (saturate at 2'b11)
            if (drive_fight_counter != 2'b11)
                drive_fight_counter <= drive_fight_counter + 2'b01;
        end else begin
            // Reset counter if values match
            drive_fight_counter <= 2'b00;
        end
    end
    
    // Tamper detected after 2 consecutive mismatches (counter reaches 2)
    assign tamper_detect = (drive_fight_counter >= 2'b10);
    
    /* ---------------------------------------------------------------------
     * 6. KEY REGISTER MANAGEMENT
     * ---------------------------------------------------------------------
     * The key register stores authorization state and can be erased on:
     * - Reset (rst_n = 0)
     * - Tamper detection (drive fight for 2+ cycles)
     * - Loss of valid key input (automatic re-lock)
     */
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            key_register <= 1'b1;  // Start in enabled state
        end else if (tamper_detect) begin
            key_register <= 1'b0;  // Erase on tamper
        end else if (key_match) begin
            key_register <= 1'b1;  // Set when correct key present
        end else begin
            key_register <= 1'b0;  // Clear when key removed
        end
    end
    
    /* ---------------------------------------------------------------------
     * 7. SYSTEM STUBS
     * ---------------------------------------------------------------------
     * Prevents DRC warnings for unreferenced ports during CI/CD.
     */
    wire _unused_signal = &{1'b0};

endmodule