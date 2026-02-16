# ============================================================================
# VAELIX | SENTINEL MARK I - FLOORPLAN INJECTION
# ============================================================================
# PROJECT: Citadel S1-90 Sentinel
# PURPOSE: Manual override of placement density for high-density layout
# TARGET: OpenLane Flow Integration
# ============================================================================

# CORE UTILIZATION: Set to 55% for dense, efficient layout
set ::env(FP_CORE_UTIL) 55

# PLACEMENT DENSITY: Target 60% for optimal cell packing
set ::env(PL_TARGET_DENSITY) 0.60

# ============================================================================
# PIN PLACEMENT CONFIGURATION
# ============================================================================
# DIRECTIVE: Force ui_in pins to West edge, uo_out pins to East edge

# Set pin order configuration file
set ::env(FP_PIN_ORDER_CFG) [file join $::env(DESIGN_DIR) pin_order.cfg]

puts "VAELIX SENTINEL: Floorplan configuration loaded."
puts "  FP_CORE_UTIL: $::env(FP_CORE_UTIL)%"
puts "  PL_TARGET_DENSITY: $::env(PL_TARGET_DENSITY)"
puts "  Pin Configuration: ui_in->WEST, uo_out->EAST"
puts "  Pin Order File: $::env(FP_PIN_ORDER_CFG)"
