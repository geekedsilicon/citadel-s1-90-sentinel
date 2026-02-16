/*
 * ============================================================================
 * PROJECT CITADEL | FORMAL VERIFICATION ASSERTIONS
 * ============================================================================
 * AUTHOR:    Vaelix Systems Engineering / R&D Division
 * MODULE:    vaelix_sentinel_assertions
 * PURPOSE:   Formal verification properties for tt_um_vaelix_sentinel
 *
 * DESCRIPTION:
 * This module contains SystemVerilog assertions (SVA) for formal verification
 * of the Sentinel Lock logic using SymbiYosys.
 * ============================================================================
 */

`default_nettype none

module vaelix_sentinel_assertions (
    input wire [7:0] ui_in,
    input wire [7:0] uo_out,
    input wire [7:0] uio_in,
    input wire [7:0] uio_out,
    input wire [7:0] uio_oe,
    input wire       ena,
    input wire       clk,
    input wire       rst_n
);

    // Previous cycle ui_in value register
    reg [7:0] ui_in_prev;
    
    always @(posedge clk) begin
        if (!rst_n) begin
            ui_in_prev <= 8'h00;
        end else begin
            ui_in_prev <= ui_in;
        end
    end

    /* -------------------------------------------------------------------------
     * ASSERTION: VERIFIED STATE SECURITY
     * -------------------------------------------------------------------------
     * uo_out NEVER equals 8'hC1 (VERIFIED) unless ui_in was 8'hB6 in the
     * previous clock cycle.
     *
     * This ensures that the VERIFIED state can only be reached with the
     * correct authorization key.
     */
    always @(posedge clk) begin
        if (rst_n && ena) begin
            // If output shows VERIFIED (0xC1), previous input must have been key (0xB6)
            if (uo_out == 8'hC1) begin
                assert (ui_in_prev == 8'hB6);
            end
        end
    end

    /* -------------------------------------------------------------------------
     * COVER: AUTHORIZATION SEQUENCE TRACE
     * -------------------------------------------------------------------------
     * Cover a trace where:
     * 1. rst_n is held low for 5 cycles
     * 2. rst_n is released (goes high)
     * 3. ui_in is set to 0xB6 (authorization key)
     *
     * This demonstrates that the formal tool can find a valid authorization
     * sequence path through the design.
     */
    reg [2:0] reset_counter;
    reg       reset_phase_done;
    reg       key_applied;
    
    always @(posedge clk) begin
        if (!rst_n) begin
            reset_counter <= 3'd0;
            reset_phase_done <= 1'b0;
            key_applied <= 1'b0;
        end else begin
            // Count cycles after reset release
            if (!reset_phase_done && reset_counter < 3'd5) begin
                reset_counter <= reset_counter + 3'd1;
            end
            
            // Mark reset phase as done after 5 cycles
            if (reset_counter >= 3'd5) begin
                reset_phase_done <= 1'b1;
            end
            
            // Check if key was applied after reset phase
            if (reset_phase_done && ui_in == 8'hB6) begin
                key_applied <= 1'b1;
            end
        end
    end
    
    // Cover property: we want to find a trace where key is applied after proper reset
    always @(posedge clk) begin
        if (rst_n && reset_phase_done && key_applied) begin
            cover (1);
        end
    end

endmodule

/* -------------------------------------------------------------------------
 * BIND STATEMENT
 * -------------------------------------------------------------------------
 * This bind statement connects the assertion module to the DUT.
 * It creates an instance of vaelix_sentinel_assertions within the
 * tt_um_vaelix_sentinel module scope, allowing the assertions to
 * observe all internal signals.
 */
bind tt_um_vaelix_sentinel vaelix_sentinel_assertions assertion_inst (
    .ui_in   (ui_in),
    .uo_out  (uo_out),
    .uio_in  (uio_in),
    .uio_out (uio_out),
    .uio_oe  (uio_oe),
    .ena     (ena),
    .clk     (clk),
    .rst_n   (rst_n)
);
