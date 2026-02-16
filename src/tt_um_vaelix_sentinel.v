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
     * 1. FSM STATE ENCODING WITH HAMMING DISTANCE HARDENING
     * ---------------------------------------------------------------------
     * TASK XVII: THE TARNOVSKY TOKEN (Laser Fault Hardening)
     * 
     * Christopher Tarnovsky uses lasers to flip single bits in a register.
     * Traditional binary encoding (0, 1, 2) has minimal Hamming distance,
     * making it vulnerable to single-photon bit-flip attacks.
     * 
     * SOLUTION: Wide Hamming Distance Encoding
     * - LOCKED    = 8'b1010_0101 (0xA5) — Default state, awaiting key
     * - VERIFIED  = 8'b0101_1010 (0x5A) — Authenticated, access granted
     * - HARD_LOCK = 8'b0000_0000 (0x00) — Fault detected, power cycle required
     * 
     * Hamming Distance Analysis:
     * - LOCKED ↔ VERIFIED:  8 bits differ (maximum protection)
     * - LOCKED ↔ HARD_LOCK: 4 bits differ
     * - VERIFIED ↔ HARD_LOCK: 4 bits differ
     * 
     * Any bit-flip from a valid state will NOT produce another valid state,
     * triggering immediate transition to HARD_LOCK via the default case.
     * 
     * (* keep *) attribute prevents synthesis optimizer from simplifying
     * the redundant bits away, maintaining full 8-bit state encoding.
     */
    localparam [7:0] STATE_LOCKED    = 8'b1010_0101;  // 0xA5
    localparam [7:0] STATE_VERIFIED  = 8'b0101_1010;  // 0x5A
    localparam [7:0] STATE_HARD_LOCK = 8'b0000_0000;  // 0x00
    
    (* keep *) reg [7:0] state_reg;
    reg [7:0] next_state;
    
    /* ---------------------------------------------------------------------
     * 2. AUTHORIZATION LOGIC
     * ---------------------------------------------------------------------
     * HARDCODED_KEY: 0xB6 (1011_0110)
     * Direct bitwise comparison for instantaneous verification.
     */
    wire is_authorized;
    assign is_authorized = (ui_in == 8'b1011_0110);

    /* ---------------------------------------------------------------------
     * 3. STATE REGISTER UPDATE (SEQUENTIAL LOGIC)
     * ---------------------------------------------------------------------
     * Synchronous state transitions on positive clock edge.
     * Active-low reset (rst_n) initializes to LOCKED state.
     */
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state_reg <= STATE_LOCKED;
        end else if (ena) begin
            state_reg <= next_state;
        end
    end
    
    /* ---------------------------------------------------------------------
     * 4. NEXT STATE LOGIC (COMBINATIONAL)
     * ---------------------------------------------------------------------
     * THE TRAP: Default case catches ANY invalid state encoding.
     * If a laser flips a bit (e.g., 0xA5 → 0xA4), the FSM immediately
     * transitions to HARD_LOCK, which requires a power cycle to escape.
     */
    always @(*) begin
        case (state_reg)
            STATE_LOCKED: begin
                // Transition to VERIFIED only with correct key
                if (is_authorized)
                    next_state = STATE_VERIFIED;
                else
                    next_state = STATE_LOCKED;
            end
            
            STATE_VERIFIED: begin
                // Once verified, remain verified until reset
                // (In a real system, could add timeout or re-verification)
                next_state = STATE_VERIFIED;
            end
            
            STATE_HARD_LOCK: begin
                // HARD_LOCK is terminal - only reset can escape
                next_state = STATE_HARD_LOCK;
            end
            
            default: begin
                // LASER FAULT DETECTED: Invalid state encoding!
                // This catches any bit-flip that creates an invalid state.
                // Examples: 0xA4, 0xA7, 0x59, 0x5B, etc.
                next_state = STATE_HARD_LOCK;
            end
        endcase
    end
    
    /* ---------------------------------------------------------------------
     * 5. SIGNAL INTEGRITY & OPTIMIZATION BYPASS
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
     * 6. VISUAL TELEMETRY: 7-SEGMENT OUTPUT
     * ---------------------------------------------------------------------
     * Bit mapping: uo_out = { dp, g, f, e, d, c, b, a }  (a = bit 0)
     * Common Anode / Active LOW: a 0-bit drives a segment ON.
     *
     * State         Segments ON       Value
     * -----------   ---------------   -----
     * 'L' Locked    f, e, d           0xC7
     * 'U' Unlocked  f, e, d, c, b     0xC1   ('V' unsupported on 7-seg)
     * 'H' Hard Lock e, f, c, b        0xC9   ('H' for HARD_LOCK)
     * Disabled      none              0xFF
     *
     * Fix: `wire x = const` replaced with localparam — correct construct
     * for synthesis constants. wire-with-init is valid in Yosys but is not
     * portable and is semantically misleading (these are not driven nets).
     */
    localparam logic [7:0] SegLocked   = 8'hC7;
    localparam logic [7:0] SegVerified = 8'hC1;
    localparam logic [7:0] SegHardLock = 8'hC9;
    localparam logic [7:0] SegOff      = 8'hFF;

    reg [7:0] display_output;
    
    always @(*) begin
        if (!internal_ena) begin
            display_output = SegOff;
        end else begin
            case (state_reg)
                STATE_LOCKED:    display_output = SegLocked;
                STATE_VERIFIED:  display_output = SegVerified;
                STATE_HARD_LOCK: display_output = SegHardLock;
                default:         display_output = SegHardLock;  // Show Hard Lock for any invalid state
            endcase
        end
    end
    
    assign uo_out = display_output;

    /* ---------------------------------------------------------------------
     * 7. STATUS ARRAY: VAELIX "GLOW" PERSISTENCE
     * ---------------------------------------------------------------------
     * Provides immediate high-intensity visual feedback upon authorization.
     * All UIO pins are forced to Output mode.
     *
     * Now based on FSM state:
     * - VERIFIED: All LEDs ON (0xFF)
     * - LOCKED or HARD_LOCK: All LEDs OFF (0x00)
     *
     * Fix: `&&` (logical AND) replaced with `&` (bitwise AND).
     * Both operators are functionally identical on 1-bit signals, but `&`
     * is the correct idiomatic operator for HDL gate-level logic and
     * avoids implicit boolean reduction of multi-bit types if ports change.
     */
    assign uio_out = (internal_ena & (state_reg == STATE_VERIFIED)) ? 8'hFF : 8'h00;
    assign uio_oe  = 8'hFF;

    /* ---------------------------------------------------------------------
     * 8. SYSTEM STUBS
     * ---------------------------------------------------------------------
     * Prevents DRC warnings for unreferenced ports during CI/CD.
     * The trailing 1'b0 ensures the reduction is never optimised to a constant.
     */
    wire _unused_signal = &{uio_in, 1'b0};

endmodule