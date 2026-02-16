/*
 * ============================================================================
 * PROJECT CITADEL | SILICON FINGERPRINT MODULE
 * ============================================================================
 * AUTHOR:    Vaelix Systems Engineering / R&D Division
 * MODULE:    ring_oscillator
 * TARGET:    Tiny Tapeout 06 (IHP 130nm SG13G2)
 *
 * DESCRIPTION:
 * Process Usage Monitor - A ring oscillator based silicon fingerprint.
 * Uses a chain of 31 inverters (sg13g2_inv_1) looped back to create
 * high-frequency oscillation. The frequency depends on the specific physics
 * of the IHP 130nm process.
 *
 * The oscillator feeds a counter that only runs when enabled via the
 * control signal. This provides a unique frequency signature that can
 * be used to validate the chip was fabricated on the correct process.
 *
 * Expected frequency: 50-70 MHz (IHP 130nm SG13G2 process)
 * ============================================================================
 */
`default_nettype none

(* keep_hierarchy *)
module ring_oscillator (
    input  wire clk,          // System clock for counter
    input  wire rst_n,        // Reset (active low)
    input  wire enable,       // Enable signal (from uio_in[0])
    output wire [31:0] count  // Oscillation counter output
);

    // Ring oscillator chain - 31 inverters
    // NOTE: This is intentionally a combinational feedback loop (ring oscillator)
    // The loop creates oscillation - this is the desired behavior
    // Simulators may warn about combinational loops - this is expected
    wire [30:0] ring_chain;
    
    // For simulation, use behavioral inverters
    // For synthesis with IHP SG13G2, these will map to sg13g2_inv_1 cells
    `ifdef GL_TEST
        // Gate-level: use actual sg13g2_inv_1 cells
        sg13g2_inv_1 inv_0  (.A(ring_chain[30]), .Y(ring_chain[0]));
        sg13g2_inv_1 inv_1  (.A(ring_chain[0]),  .Y(ring_chain[1]));
        sg13g2_inv_1 inv_2  (.A(ring_chain[1]),  .Y(ring_chain[2]));
        sg13g2_inv_1 inv_3  (.A(ring_chain[2]),  .Y(ring_chain[3]));
        sg13g2_inv_1 inv_4  (.A(ring_chain[3]),  .Y(ring_chain[4]));
        sg13g2_inv_1 inv_5  (.A(ring_chain[4]),  .Y(ring_chain[5]));
        sg13g2_inv_1 inv_6  (.A(ring_chain[5]),  .Y(ring_chain[6]));
        sg13g2_inv_1 inv_7  (.A(ring_chain[6]),  .Y(ring_chain[7]));
        sg13g2_inv_1 inv_8  (.A(ring_chain[7]),  .Y(ring_chain[8]));
        sg13g2_inv_1 inv_9  (.A(ring_chain[8]),  .Y(ring_chain[9]));
        sg13g2_inv_1 inv_10 (.A(ring_chain[9]),  .Y(ring_chain[10]));
        sg13g2_inv_1 inv_11 (.A(ring_chain[10]), .Y(ring_chain[11]));
        sg13g2_inv_1 inv_12 (.A(ring_chain[11]), .Y(ring_chain[12]));
        sg13g2_inv_1 inv_13 (.A(ring_chain[12]), .Y(ring_chain[13]));
        sg13g2_inv_1 inv_14 (.A(ring_chain[13]), .Y(ring_chain[14]));
        sg13g2_inv_1 inv_15 (.A(ring_chain[14]), .Y(ring_chain[15]));
        sg13g2_inv_1 inv_16 (.A(ring_chain[15]), .Y(ring_chain[16]));
        sg13g2_inv_1 inv_17 (.A(ring_chain[16]), .Y(ring_chain[17]));
        sg13g2_inv_1 inv_18 (.A(ring_chain[17]), .Y(ring_chain[18]));
        sg13g2_inv_1 inv_19 (.A(ring_chain[18]), .Y(ring_chain[19]));
        sg13g2_inv_1 inv_20 (.A(ring_chain[19]), .Y(ring_chain[20]));
        sg13g2_inv_1 inv_21 (.A(ring_chain[20]), .Y(ring_chain[21]));
        sg13g2_inv_1 inv_22 (.A(ring_chain[21]), .Y(ring_chain[22]));
        sg13g2_inv_1 inv_23 (.A(ring_chain[22]), .Y(ring_chain[23]));
        sg13g2_inv_1 inv_24 (.A(ring_chain[23]), .Y(ring_chain[24]));
        sg13g2_inv_1 inv_25 (.A(ring_chain[24]), .Y(ring_chain[25]));
        sg13g2_inv_1 inv_26 (.A(ring_chain[25]), .Y(ring_chain[26]));
        sg13g2_inv_1 inv_27 (.A(ring_chain[26]), .Y(ring_chain[27]));
        sg13g2_inv_1 inv_28 (.A(ring_chain[27]), .Y(ring_chain[28]));
        sg13g2_inv_1 inv_29 (.A(ring_chain[28]), .Y(ring_chain[29]));
        sg13g2_inv_1 inv_30 (.A(ring_chain[29]), .Y(ring_chain[30]));
    `else
        // RTL simulation: behavioral inverters
        // Use combinational logic with keep attribute to prevent optimization
        assign ring_chain[0]  = ~ring_chain[30];
        assign ring_chain[1]  = ~ring_chain[0];
        assign ring_chain[2]  = ~ring_chain[1];
        assign ring_chain[3]  = ~ring_chain[2];
        assign ring_chain[4]  = ~ring_chain[3];
        assign ring_chain[5]  = ~ring_chain[4];
        assign ring_chain[6]  = ~ring_chain[5];
        assign ring_chain[7]  = ~ring_chain[6];
        assign ring_chain[8]  = ~ring_chain[7];
        assign ring_chain[9]  = ~ring_chain[8];
        assign ring_chain[10] = ~ring_chain[9];
        assign ring_chain[11] = ~ring_chain[10];
        assign ring_chain[12] = ~ring_chain[11];
        assign ring_chain[13] = ~ring_chain[12];
        assign ring_chain[14] = ~ring_chain[13];
        assign ring_chain[15] = ~ring_chain[14];
        assign ring_chain[16] = ~ring_chain[15];
        assign ring_chain[17] = ~ring_chain[16];
        assign ring_chain[18] = ~ring_chain[17];
        assign ring_chain[19] = ~ring_chain[18];
        assign ring_chain[20] = ~ring_chain[19];
        assign ring_chain[21] = ~ring_chain[20];
        assign ring_chain[22] = ~ring_chain[21];
        assign ring_chain[23] = ~ring_chain[22];
        assign ring_chain[24] = ~ring_chain[23];
        assign ring_chain[25] = ~ring_chain[24];
        assign ring_chain[26] = ~ring_chain[25];
        assign ring_chain[27] = ~ring_chain[26];
        assign ring_chain[28] = ~ring_chain[27];
        assign ring_chain[29] = ~ring_chain[28];
        assign ring_chain[30] = ~ring_chain[29];
    `endif

    // Oscillator output (tap from the ring)
    wire osc_out;
    assign osc_out = ring_chain[30];

    // Edge detection for oscillator output
    reg osc_prev;
    wire osc_edge;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            osc_prev <= 1'b0;
        end else begin
            osc_prev <= osc_out;
        end
    end
    
    // Detect rising edge of oscillator
    assign osc_edge = osc_out & ~osc_prev;

    // Counter - counts oscillations when enabled
    // 32-bit counter provides long-term measurement capability
    // Only lower 8 bits are exposed via output port for compatibility with 8-bit interface
    reg [31:0] counter;
    
    // Counter logic - increment on oscillator edges when enabled
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            counter <= 32'h0;
        end else if (enable && osc_edge) begin
            counter <= counter + 1;
        end
    end

    assign count = counter;

endmodule
