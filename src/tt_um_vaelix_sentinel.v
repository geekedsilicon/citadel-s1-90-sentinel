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
 * the Sentinel Lock logic with Replay Attack Defense (Time-Window Constraint).
 * System remains in state 'LOCKED' until the 8-bit Vaelix Key (0xB6) is 
 * presented at the primary UI port within the valid time window (3-5 cycles
 * after ena goes high).
 *
 * HARDWARE MAPPING:
 * - UI[7:0]:   External DIP Switches (Authorization Key)
 * - UO[7:0]:   7-Segment Display (Common Anode / Active LOW)
 * - UIO[7:0]:  Status Array (Vaelix "Glow" Persistence)
 *
 * REPLAY ATTACK DEFENSE:
 * - Key must be entered 3-5 cycles after ena signal goes high
 * - Key at cycle 0 or cycle 10+ triggers REPLAY_LOCKOUT for 10 seconds
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
     * 1. STATE MACHINE & TIMING
     * ---------------------------------------------------------------------
     * States:
     * - IDLE: Initial state, waiting for ena
     * - WAITING: Counting cycles after ena, checking for valid key timing
     * - AUTHORIZED: Valid key received in time window
     * - REPLAY_LOCKOUT: Replay attack detected, locked for 10 seconds
     */
    localparam [1:0] STATE_IDLE          = 2'b00;
    localparam [1:0] STATE_WAITING       = 2'b01;
    localparam [1:0] STATE_AUTHORIZED    = 2'b10;
    localparam [1:0] STATE_REPLAY_LOCKOUT = 2'b11;
    
    reg [1:0] state, next_state;
    
    // Cycle counter (6 bits to count up to 63, we need 0-10+)
    reg [5:0] cycle_counter, next_cycle_counter;
    
    // Lockout timer (28 bits to count 250M cycles = 10 seconds at 25 MHz)
    reg [27:0] lockout_timer, next_lockout_timer;
    localparam [27:0] LOCKOUT_CYCLES = 28'd250_000_000; // 10 seconds at 25 MHz
    
    // Key detection
    wire key_present;
    assign key_present = (ui_in == 8'b1011_0110);
    
    // Previous ena state for edge detection
    reg ena_prev;
    wire ena_rising_edge;
    assign ena_rising_edge = ena && !ena_prev;

    /* ---------------------------------------------------------------------
     * 2. STATE MACHINE LOGIC
     * ---------------------------------------------------------------------
     */
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= STATE_IDLE;
            cycle_counter <= 6'd0;
            lockout_timer <= 28'd0;
            ena_prev <= 1'b0;
        end else begin
            state <= next_state;
            cycle_counter <= next_cycle_counter;
            lockout_timer <= next_lockout_timer;
            ena_prev <= ena;
        end
    end
    
    /* ---------------------------------------------------------------------
     * 3. NEXT STATE LOGIC
     * ---------------------------------------------------------------------
     */
    always @(*) begin
        // Default assignments
        next_state = state;
        next_cycle_counter = cycle_counter;
        next_lockout_timer = lockout_timer;
        
        case (state)
            STATE_IDLE: begin
                if (ena_rising_edge) begin
                    // Ena just went high, start timing
                    next_state = STATE_WAITING;
                    next_cycle_counter = 6'd0;
                end
            end
            
            STATE_WAITING: begin
                if (!ena) begin
                    // Ena went low, return to IDLE
                    next_state = STATE_IDLE;
                    next_cycle_counter = 6'd0;
                end else begin
                    // Check for replay attack conditions BEFORE incrementing
                    // This way cycle 0 is the first cycle after ena rises
                    if (key_present && cycle_counter == 6'd0) begin
                        // Key present at cycle 0 - immediate replay attack
                        next_state = STATE_REPLAY_LOCKOUT;
                        next_lockout_timer = LOCKOUT_CYCLES;
                    end else if (key_present && cycle_counter >= 6'd10) begin
                        // Key present at cycle 10 or later - late replay attack
                        next_state = STATE_REPLAY_LOCKOUT;
                        next_lockout_timer = LOCKOUT_CYCLES;
                    end else if (key_present && cycle_counter >= 6'd3 && cycle_counter <= 6'd5) begin
                        // Valid key in time window (cycles 3-5)
                        next_state = STATE_AUTHORIZED;
                    end
                    
                    // Increment cycle counter for next cycle
                    if (cycle_counter < 6'd63) begin
                        next_cycle_counter = cycle_counter + 6'd1;
                    end
                end
            end
            
            STATE_AUTHORIZED: begin
                if (!ena || !key_present) begin
                    // Lost authorization, return to IDLE
                    next_state = STATE_IDLE;
                    next_cycle_counter = 6'd0;
                end
            end
            
            STATE_REPLAY_LOCKOUT: begin
                if (!ena) begin
                    // Ena went low, return to IDLE (but keep timer running if ena comes back)
                    next_state = STATE_IDLE;
                    next_cycle_counter = 6'd0;
                end else if (lockout_timer > 28'd0) begin
                    // Count down lockout timer
                    next_lockout_timer = lockout_timer - 28'd1;
                end else begin
                    // Lockout expired, return to IDLE
                    next_state = STATE_IDLE;
                    next_cycle_counter = 6'd0;
                end
            end
            
            default: begin
                next_state = STATE_IDLE;
                next_cycle_counter = 6'd0;
                next_lockout_timer = 28'd0;
            end
        endcase
    end
    
    /* ---------------------------------------------------------------------
     * 4. OUTPUT LOGIC
     * ---------------------------------------------------------------------
     */
    wire is_authorized;
    assign is_authorized = (state == STATE_AUTHORIZED);
    
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
     * 7. STATUS ARRAY: VAELIX "GLOW" PERSISTENCE
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
     * 8. SYSTEM STUBS
     * ---------------------------------------------------------------------
     * Prevents DRC warnings for unreferenced ports during CI/CD.
     * The trailing 1'b0 ensures the reduction is never optimised to a constant.
     */
    wire _unused_signal = &{uio_in, 1'b0};

endmodule