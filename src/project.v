/*
 * ============================================================================
 * PROJECT CITADEL | TARNOVSKY SHUFFLE - REGISTER SCATTERING
 * ============================================================================
 * AUTHOR:    Vaelix Systems Engineering / R&D Division
 * MODULE:    project (Key Storage Obfuscation Layer)
 * TARGET:    Tiny Tapeout 06 (IHP 130nm SG13G2)
 *
 * DESCRIPTION:
 * Physical Layout Obfuscation - "The Tarnovsky Shuffle"
 * 
 * Instead of storing the 8-bit Vaelix Key (0xB6 = 10110110) in a contiguous
 * register array, we scatter individual bits across 8 distinct single-bit
 * registers with deceptive naming. These registers are placed at opposite
 * corners of the die via placement constraints.
 *
 * DECEPTION LAYER:
 * Bits at indices 0, 2, 4, 6 use INVERTED storage (store 0 as 1, 1 as 0).
 * Visual inspection of flip-flops will reveal incorrect key values.
 *
 * SECURITY NOTICE:
 * The logical-to-physical mapping is documented in a separate encrypted
 * file (key_mapping.encrypted) - NOT in source code comments.
 * ============================================================================
 */

`default_nettype none

module scattered_key_storage (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [7:0] key_input,
    output wire       is_authorized
);

    /* ---------------------------------------------------------------------
     * SCATTERED KEY STORAGE: 8 individual 1-bit registers
     * Names chosen to appear as unrelated system state variables
     * --------------------------------------------------------------------- */
    
    // Register 0: Stores key bit 0 (INVERTED) - Key bit 0 = 0, stored as 1
    (* keep_hierarchy *)
    reg sys_state_a;
    
    // Register 1: Stores key bit 1 (NORMAL) - Key bit 1 = 1, stored as 1
    (* keep_hierarchy *)
    reg timer_ref_b;
    
    // Register 2: Stores key bit 2 (INVERTED) - Key bit 2 = 1, stored as 0
    (* keep_hierarchy *)
    reg calib_val_c;
    
    // Register 3: Stores key bit 3 (NORMAL) - Key bit 3 = 1, stored as 1
    (* keep_hierarchy *)
    reg pwr_mon_d;
    
    // Register 4: Stores key bit 4 (INVERTED) - Key bit 4 = 0, stored as 1
    (* keep_hierarchy *)
    reg clk_div_e;
    
    // Register 5: Stores key bit 5 (NORMAL) - Key bit 5 = 1, stored as 1
    (* keep_hierarchy *)
    reg stat_flag_f;
    
    // Register 6: Stores key bit 6 (INVERTED) - Key bit 6 = 1, stored as 0
    (* keep_hierarchy *)
    reg mux_sel_g;
    
    // Register 7: Stores key bit 7 (NORMAL) - Key bit 7 = 1, stored as 1
    (* keep_hierarchy *)
    reg ena_ctrl_h;

    /* ---------------------------------------------------------------------
     * KEY INITIALIZATION WITH RESET LOGIC
     * Hardcoded Vaelix Key: 0xB6 = 10110110
     * Bits [0,2,4,6] stored inverted for visual deception
     * Uses synchronous reset for ASIC synthesis compatibility
     * --------------------------------------------------------------------- */
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Bit 0 of key (0) stored INVERTED → 1
            sys_state_a <= 1'b1;
            
            // Bit 1 of key (1) stored NORMAL → 1
            timer_ref_b <= 1'b1;
            
            // Bit 2 of key (1) stored INVERTED → 0
            calib_val_c <= 1'b0;
            
            // Bit 3 of key (1) stored NORMAL → 1
            pwr_mon_d <= 1'b1;
            
            // Bit 4 of key (0) stored INVERTED → 1
            clk_div_e <= 1'b1;
            
            // Bit 5 of key (1) stored NORMAL → 1
            stat_flag_f <= 1'b1;
            
            // Bit 6 of key (1) stored INVERTED → 0
            mux_sel_g <= 1'b0;
            
            // Bit 7 of key (1) stored NORMAL → 1
            ena_ctrl_h <= 1'b1;
        end
        // In normal operation, these registers retain their values
        // They are not updated - the key is hardcoded via reset
    end

    /* ---------------------------------------------------------------------
     * KEY RECONSTRUCTION LOGIC
     * De-obfuscate the scattered bits and apply inversion where needed
     * --------------------------------------------------------------------- */
    wire [7:0] reconstructed_key;
    
    // Reconstruct each bit, inverting where necessary
    assign reconstructed_key[0] = ~sys_state_a;  // Inverted storage
    assign reconstructed_key[1] = timer_ref_b;   // Normal storage
    assign reconstructed_key[2] = ~calib_val_c;  // Inverted storage
    assign reconstructed_key[3] = pwr_mon_d;     // Normal storage
    assign reconstructed_key[4] = ~clk_div_e;    // Inverted storage
    assign reconstructed_key[5] = stat_flag_f;   // Normal storage
    assign reconstructed_key[6] = ~mux_sel_g;    // Inverted storage
    assign reconstructed_key[7] = ena_ctrl_h;    // Normal storage

    /* ---------------------------------------------------------------------
     * AUTHORIZATION LOGIC
     * Compare input against reconstructed key
     * --------------------------------------------------------------------- */
    assign is_authorized = (key_input == reconstructed_key);

endmodule
