/*
 * ============================================================================
 * PROJECT CITADEL | INPUT SANITIZER MODULE (KAMKAR HYSTERESIS)
 * ============================================================================
 * AUTHOR:    Vaelix Systems Engineering / R&D Division
 * MODULE:    debouncer
 * TARGET:    Tiny Tapeout 06 (IHP 130nm SG13G2)
 *
 * DESCRIPTION:
 * Input debouncing and anti-fuzzing protection module. Protects against
 * signal bounce attacks and rapid toggling attempts (Kamkar-style attacks).
 *
 * FEATURES:
 * 1. Stability Requirement: Input must remain stable for 4 consecutive
 *    clock cycles before being accepted by the main logic.
 * 2. Fast Transition Rejection: If signal changes faster than 4 cycles
 *    (frequency > 6 MHz at 25MHz clock), the transition is ignored.
 * 3. Fuzzing Attack Detection: If more than 10 changes occur within 100
 *    cycles, the input interface is locked for 1 second (25M cycles).
 *
 * PARAMETERS:
 * - DEBOUNCE_CYCLES: Number of stable cycles required (default: 4)
 * - ATTACK_WINDOW: Cycle window for fuzzing detection (default: 100)
 * - ATTACK_THRESHOLD: Max changes allowed in window (default: 10)
 * - LOCKOUT_CYCLES: Lockout duration in cycles (default: 25M for 1s @ 25MHz)
 * ============================================================================
 */

`default_nettype none

(* keep_hierarchy *)
module debouncer #(
    parameter DEBOUNCE_CYCLES  = 4,
    parameter ATTACK_WINDOW    = 100,
    parameter ATTACK_THRESHOLD = 10,
    parameter LOCKOUT_CYCLES   = 25_000_000
) (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [7:0] signal_in,
    output reg  [7:0] signal_out
);

    // Per-bit debouncing state
    reg [7:0] stable_signal;
    reg [1:0] stability_counter [7:0];  // 2-bit counter for each bit (0 to DEBOUNCE_CYCLES-1)
    reg [7:0] prev_signal;
    
    // Fuzzing attack detection
    reg [6:0] change_counter;           // Count changes (max 127)
    reg [6:0] cycle_counter;            // Count cycles in window (0-99)
    reg [24:0] lockout_counter;         // Lockout timer (up to 25M)
    reg locked;                         // Lockout active flag
    
    integer i;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset all state
            signal_out <= 8'h00;
            stable_signal <= 8'h00;
            for (i = 0; i < 8; i = i + 1) begin
                stability_counter[i] <= 2'b00;
            end
            prev_signal <= 8'h00;
            change_counter <= 7'd0;
            cycle_counter <= 7'd0;
            lockout_counter <= 25'd0;
            locked <= 1'b0;
        end else begin
            // Lockout timer management
            if (locked) begin
                if (lockout_counter < (LOCKOUT_CYCLES - 1)) begin
                    lockout_counter <= lockout_counter + 1;
                end else begin
                    // Lockout expired
                    locked <= 1'b0;
                    lockout_counter <= 25'd0;
                    change_counter <= 7'd0;
                    cycle_counter <= 7'd0;
                end
            end else begin
                // Not locked - perform debouncing and attack detection
                
                // Update attack detection window
                if (cycle_counter < (ATTACK_WINDOW - 1)) begin
                    cycle_counter <= cycle_counter + 1;
                end else begin
                    // Window complete - reset counters
                    cycle_counter <= 7'd0;
                    change_counter <= 7'd0;
                end
                
                // Detect any changes from previous cycle
                if (signal_in != prev_signal) begin
                    // Saturating increment to prevent overflow
                    if (change_counter < 7'd127) begin
                        change_counter <= change_counter + 1;
                    end
                    
                    // Check for fuzzing attack
                    if (change_counter >= (ATTACK_THRESHOLD - 1)) begin
                        // Attack detected! Initiate lockout
                        locked <= 1'b1;
                        lockout_counter <= 25'd0;
                        // Freeze output during lockout
                    end
                end
                
                prev_signal <= signal_in;
                
                // Per-bit debouncing logic
                for (i = 0; i < 8; i = i + 1) begin
                    if (signal_in[i] == stable_signal[i]) begin
                        // Signal matches current stable value - reset counter
                        stability_counter[i] <= 2'b00;
                    end else begin
                        // Signal differs - increment stability counter
                        if (stability_counter[i] < (DEBOUNCE_CYCLES - 1)) begin
                            stability_counter[i] <= stability_counter[i] + 1;
                        end else begin
                            // Signal has been stable for required cycles
                            // Accept the new value
                            stable_signal[i] <= signal_in[i];
                            stability_counter[i] <= 2'b00;
                        end
                    end
                end
                
                // Update output (frozen during lockout)
                if (!locked) begin
                    signal_out <= stable_signal;
                end
            end
        end
    end

endmodule
