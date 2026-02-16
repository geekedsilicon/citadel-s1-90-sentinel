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

# West Edge: Input pins (ui_in[0:7])
set ::env(FP_PIN_ORDER_CFG) [list \
    ui_in\[0\] W \
    ui_in\[1\] W \
    ui_in\[2\] W \
    ui_in\[3\] W \
    ui_in\[4\] W \
    ui_in\[5\] W \
    ui_in\[6\] W \
    ui_in\[7\] W \
    uo_out\[0\] E \
    uo_out\[1\] E \
    uo_out\[2\] E \
    uo_out\[3\] E \
    uo_out\[4\] E \
    uo_out\[5\] E \
    uo_out\[6\] E \
    uo_out\[7\] E \
]

puts "VAELIX SENTINEL: Floorplan configuration loaded."
puts "  FP_CORE_UTIL: $::env(FP_CORE_UTIL)%"
puts "  PL_TARGET_DENSITY: $::env(PL_TARGET_DENSITY)"
puts "  Pin Configuration: ui_in->WEST, uo_out->EAST"
