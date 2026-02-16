# ============================================================================
# PROJECT CITADEL | TARNOVSKY SHUFFLE PLACEMENT STRATEGY NOTES
# ============================================================================
# FILE:     placement_strategy_notes.tcl
# PURPOSE:  Physical layout obfuscation strategy documentation
# TARGET:   OpenLane 2.x / OpenROAD
#
# DESCRIPTION:
# This TCL script provides placement hints to scatter the 8 individual
# key storage registers across the die area. While standard cells cannot
# be placed with absolute coordinates like macros, we can provide strong
# placement hints to encourage the placer to distribute them widely.
#
# REGISTER NAMING:
#   key_validator.sys_state_a  - Bit 0 (inverted storage)
#   key_validator.timer_ref_b  - Bit 1 (normal storage)
#   key_validator.calib_val_c  - Bit 2 (inverted storage)
#   key_validator.pwr_mon_d    - Bit 3 (normal storage)
#   key_validator.clk_div_e    - Bit 4 (inverted storage)
#   key_validator.stat_flag_f  - Bit 5 (normal storage)
#   key_validator.mux_sel_g    - Bit 6 (inverted storage)
#   key_validator.ena_ctrl_h   - Bit 7 (normal storage)
# ============================================================================

# NOTE: These are placement HINTS, not absolute constraints
# The actual placement will be determined by the OpenROAD placer
# based on timing, congestion, and other factors

# Attempt to guide placement of key storage registers
# Using region constraints to encourage distribution

# Get die dimensions
set die_width [expr {[lindex [ord::get_die_area] 2] - [lindex [ord::get_die_area] 0]}]
set die_height [expr {[lindex [ord::get_die_area] 3] - [lindex [ord::get_die_area] 1]}]

# Define regions for scattered placement
# Bottom-left region (10-30% of die)
set region_bl_llx [expr {int($die_width * 0.10)}]
set region_bl_lly [expr {int($die_height * 0.10)}]
set region_bl_urx [expr {int($die_width * 0.30)}]
set region_bl_ury [expr {int($die_height * 0.30)}]

# Top-right region (70-90% of die)
set region_tr_llx [expr {int($die_width * 0.70)}]
set region_tr_lly [expr {int($die_height * 0.70)}]
set region_tr_urx [expr {int($die_width * 0.90)}]
set region_tr_ury [expr {int($die_height * 0.90)}]

# Bottom-right region
set region_br_llx [expr {int($die_width * 0.70)}]
set region_br_lly [expr {int($die_height * 0.10)}]
set region_br_urx [expr {int($die_width * 0.90)}]
set region_br_ury [expr {int($die_height * 0.30)}]

# Top-left region
set region_tl_llx [expr {int($die_width * 0.10)}]
set region_tl_lly [expr {int($die_height * 0.70)}]
set region_tl_urx [expr {int($die_width * 0.30)}]
set region_tl_ury [expr {int($die_height * 0.90)}]

# Center-bottom region
set region_cb_llx [expr {int($die_width * 0.40)}]
set region_cb_lly [expr {int($die_height * 0.10)}]
set region_cb_urx [expr {int($die_width * 0.60)}]
set region_cb_ury [expr {int($die_height * 0.30)}]

# Left-center region
set region_lc_llx [expr {int($die_width * 0.10)}]
set region_lc_lly [expr {int($die_height * 0.40)}]
set region_lc_urx [expr {int($die_width * 0.30)}]
set region_lc_ury [expr {int($die_height * 0.60)}]

# Right-center region
set region_rc_llx [expr {int($die_width * 0.70)}]
set region_rc_lly [expr {int($die_height * 0.40)}]
set region_rc_urx [expr {int($die_width * 0.90)}]
set region_rc_ury [expr {int($die_height * 0.60)}]

# Center-top region
set region_ct_llx [expr {int($die_width * 0.40)}]
set region_ct_lly [expr {int($die_height * 0.70)}]
set region_ct_urx [expr {int($die_width * 0.60)}]
set region_ct_ury [expr {int($die_height * 0.90)}]

puts "CITADEL: Tarnovsky Shuffle placement hints configured"
puts "Die dimensions: ${die_width}x${die_height}"

# Note: Actual register placement commands would go here
# However, standard cell placement is typically handled by the placer
# This script serves as documentation of the intended physical distribution
