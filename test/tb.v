// ============================================================================
// VAELIX | PROJECT CITADEL — VERIFICATION HARNESS
// ============================================================================
// FILE:     tb.v
// PURPOSE:  Cocotb-compatible wrapper for the S1-90 Sentinel Core.
// TARGET:   IHP 130nm SG13G2 (Tiny Tapeout 06 / IHP26a)
// STANDARD: Vaelix Missionary Standard v1.2
// ============================================================================

`default_nettype none
`timescale 1ns / 1ps

module tb ();

  // -----------------------------------------------------------
  // TELEMETRY RECORDING — FST for high-speed waveform analysis
  // -----------------------------------------------------------
  initial begin
    $dumpfile("tb.fst");
    $dumpvars(0, tb);
    #1;
  end

  // -----------------------------------------------------------
  // SYSTEM WIRES
  // -----------------------------------------------------------
  reg        clk;
  reg        rst_n;
  reg        ena;
  reg  [7:0] ui_in;
  reg  [7:0] uio_in;
  wire [7:0] uo_out;
  wire [7:0] uio_out;
  wire [7:0] uio_oe;

  // -----------------------------------------------------------
  // DUT: SENTINEL MARK I
  // Module name must match the top_module in info.yaml exactly.
  // -----------------------------------------------------------
  tt_um_vaelix_sentinel user_project (
      .ui_in   (ui_in),
      .uo_out  (uo_out),
      .uio_in  (uio_in),
      .uio_out (uio_out),
      .uio_oe  (uio_oe),
      .ena     (ena),
      .clk     (clk),
      .rst_n   (rst_n)
  );

endmodule
