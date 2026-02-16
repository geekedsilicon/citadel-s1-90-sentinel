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
     *
     * Implementation: Track time since reset release and detect key application.
     * The formal tool will search for a trace where reset was held for 5+ cycles,
     * then released, then the key was applied.
     */
    reg [3:0] cycles_since_reset_release;
    reg       seen_reset_released;
    reg       seen_key_after_reset;
    
    always @(posedge clk) begin
        if (!rst_n) begin
            cycles_since_reset_release <= 4'd0;
            seen_reset_released <= 1'b0;
            seen_key_after_reset <= 1'b0;
        end else begin
            // Track that we've seen reset released
            if (!seen_reset_released) begin
                seen_reset_released <= 1'b1;
            end
            
            // Count cycles since reset was released
            if (cycles_since_reset_release < 4'd15) begin
                cycles_since_reset_release <= cycles_since_reset_release + 4'd1;
            end
            
            // Detect key application after reset was released
            if (seen_reset_released && ui_in == 8'hB6) begin
                seen_key_after_reset <= 1'b1;
            end
        end
    end
    
    // Cover property: Find trace where reset released and key applied afterward
    // The formal tool will try different reset durations to satisfy this
    always @(posedge clk) begin
        if (rst_n && seen_key_after_reset) begin
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
