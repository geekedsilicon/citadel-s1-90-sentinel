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
     * 1. GERLINSKY GUARD: VOLTAGE GLITCH DETECTOR
     * ---------------------------------------------------------------------
     * The Gerlinsky Guard detects voltage glitches by monitoring propagation
     * delay changes in a buffer chain. If a glitch is detected, it forces
     * an immediate hard reset to protect the system integrity.
     */
    wire glitch_detected;
    glitch_detector gerlinsky_guard (
        .GLITCH_DETECTED(glitch_detected)
    );
    
    // Internal reset: combines external reset with glitch detection
    // Active LOW: reset asserted when rst_n=0 OR glitch_detected=1
    wire internal_rst_n;
    assign internal_rst_n = rst_n & ~glitch_detected;

    /* ---------------------------------------------------------------------
     * 2. AUTHORIZATION LOGIC
     * 1. AUTHORIZATION LOGIC WITH KEY REGISTER
     * ---------------------------------------------------------------------
     * HARDCODED_KEY: 0xB6 (1011_0110)
     * Direct bitwise comparison for instantaneous verification.
     * 
     * KEY REGISTER: Stores authorization enable bit. Can be erased by tamper detection.
     * When key_register=1, normal operation. When key_register=0 (tampered), 
     * authorization is permanently disabled until reset.
     */
    wire key_match;
    assign key_match = (ui_in == 8'b1011_0110);
    
    reg  key_register;
    wire is_authorized;
    
    // Authorization requires correct key AND non-tampered state
    // key_register acts as a security fuse - once blown by tamper, system is locked
    assign is_authorized = key_match & key_register;

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
     * 3. SIGNAL INTEGRITY & OPTIMIZATION BYPASS
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
     * 5. VISUAL TELEMETRY: 7-SEGMENT OUTPUT
     * 4. VISUAL TELEMETRY: 7-SEGMENT OUTPUT
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
     * 5. STATUS ARRAY: VAELIX "GLOW" PERSISTENCE
     * 7. STATUS ARRAY: VAELIX "GLOW" PERSISTENCE
     * ---------------------------------------------------------------------
     * Provides immediate high-intensity visual feedback upon authorization.
     * When not measuring oscillator (uio_in[0]=0), shows glow status.
     * When measuring oscillator (uio_in[0]=1), shows lower 8 bits of counter.
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
    wire [7:0] glow_output;
    assign glow_output = (internal_ena & is_authorized) ? 8'hFF : 8'h00;
    assign uio_out = uio_in[0] ? osc_count[7:0] : glow_output;
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
     * The key register acts as a security fuse/enable bit:
     * - Starts at 1 (enabled) after reset
     * - Set to 0 (disabled) when tamper detected
     * - Once tampered (0), stays 0 until reset - system permanently locked
     * 
     * This provides the "erase key register" behavior required by Huang Loopback,
     * while maintaining the original combinational authorization behavior when
     * not tampered.
     */
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            key_register <= 1'b1;  // Reset: enable authorization
        end else if (tamper_detect) begin
            key_register <= 1'b0;  // Tamper: disable permanently (until reset)
        end
        // else: maintain current state (no change unless tampered)
    end
    
    /* ---------------------------------------------------------------------
     * 7. SYSTEM STUBS
     * ---------------------------------------------------------------------
     * Prevents DRC warnings for unreferenced ports during CI/CD.
     */
    wire _unused_signal = &{1'b0};

endmodule
