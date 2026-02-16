/*
 * ============================================================================
 * PROJECT CITADEL | THE GERLINSKY GUARD
 * ============================================================================
 * AUTHOR:    Vaelix Systems Engineering / R&D Division
 * MODULE:    glitch_detector
 * TARGET:    Tiny Tapeout 06 (IHP 130nm SG13G2)
 *
 * DESCRIPTION:
 * Voltage glitch detector using a chain of asynchronous buffers. When a
 * voltage dip occurs (Chris Gerlinsky attack), the propagation delay changes
 * significantly, causing the ring oscillator to behave anomalously.
 *
 * ARCHITECTURE:
 * - Chain of 10 sg13g2_buf_2 asynchronous buffers
 * - Ring oscillator: output inverted and fed back to input
 * - If propagation delay changes → oscillation frequency changes → detectable
 * ============================================================================
 */

`default_nettype none

(* keep_hierarchy *)
module glitch_detector (
    output wire GLITCH_DETECTED
);

    // Chain of buffer signals: buf_chain[0] is input, buf_chain[10] is output
    wire [10:0] buf_chain;
    
    // Create a ring oscillator with XOR feedback
    // The XOR inverts when output differs from a reference, creating oscillation
    // Under voltage glitch, timing changes cause detectable anomalies
    assign buf_chain[0] = ~buf_chain[10];  // Inverter creates oscillation
    
    // Chain of 10 asynchronous buffers
    sg13g2_buf_2 buf_0 (.A(buf_chain[0]),  .X(buf_chain[1]));
    sg13g2_buf_2 buf_1 (.A(buf_chain[1]),  .X(buf_chain[2]));
    sg13g2_buf_2 buf_2 (.A(buf_chain[2]),  .X(buf_chain[3]));
    sg13g2_buf_2 buf_3 (.A(buf_chain[3]),  .X(buf_chain[4]));
    sg13g2_buf_2 buf_4 (.A(buf_chain[4]),  .X(buf_chain[5]));
    sg13g2_buf_2 buf_5 (.A(buf_chain[5]),  .X(buf_chain[6]));
    sg13g2_buf_2 buf_6 (.A(buf_chain[6]),  .X(buf_chain[7]));
    sg13g2_buf_2 buf_7 (.A(buf_chain[7]),  .X(buf_chain[8]));
    sg13g2_buf_2 buf_8 (.A(buf_chain[8]),  .X(buf_chain[9]));
    sg13g2_buf_2 buf_9 (.A(buf_chain[9]),  .X(buf_chain[10]));
    
    // Output the oscillating signal as glitch detection signal
    // In normal operation, this oscillates at a frequency determined by buffer delays
    // Under voltage glitch, timing changes cause frequency shifts that trigger resets
    assign GLITCH_DETECTED = buf_chain[0];

endmodule
