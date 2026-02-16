# TASK XIII: THE TARNOVSKY SHUFFLE

## Physical Layout Obfuscation Implementation

This document describes the implementation of register scattering for the 8-bit key storage, designed to prevent visual extraction via Focused Ion Beam (FIB) microscopy.

## Implementation Overview

### 1. Scattered Register Storage (`src/project.v`)

Instead of a contiguous `reg [7:0] key_storage`, the Vaelix Key (0xB6 = 10110110) is now stored across 8 individual 1-bit registers with deceptive naming:

| Register Name     | Bit Index | Logical Value | Storage Method | Physical Value |
|------------------|-----------|---------------|----------------|----------------|
| `sys_state_a`    | 0         | 0             | INVERTED       | 1              |
| `timer_ref_b`    | 1         | 1             | NORMAL         | 1              |
| `calib_val_c`    | 2         | 1             | INVERTED       | 0              |
| `pwr_mon_d`      | 3         | 1             | NORMAL         | 1              |
| `clk_div_e`      | 4         | 0             | INVERTED       | 1              |
| `stat_flag_f`    | 5         | 1             | NORMAL         | 1              |
| `mux_sel_g`      | 6         | 1             | INVERTED       | 0              |
| `ena_ctrl_h`     | 7         | 1             | NORMAL         | 1              |

### 2. Deception Layer

**Visual Inspection Yields**: 10101010 (0xAA)  
**Actual Key Value**: 10110110 (0xB6)

Half of the registers (indices 0, 2, 4, 6) use inverted storage, where a logical 0 is stored as physical 1 and vice versa. This ensures that direct visual inspection of flip-flop states via FIB will reveal an incorrect key.

### 3. Key Reconstruction

The `project.v` module includes logic to reconstruct the correct key:

```verilog
assign reconstructed_key[0] = ~sys_state_a;  // Inverted
assign reconstructed_key[1] = timer_ref_b;   // Normal
assign reconstructed_key[2] = ~calib_val_c;  // Inverted
// ... etc
```

### 4. Physical Placement Strategy

The synthesis configuration in `src/config.json` includes optimization settings that encourage the placer to distribute the registers across the die area. While absolute placement of standard cells is handled by the OpenROAD placer, the configuration enables design optimizations that affect placement.

Additional placement strategy notes are documented in `placement_strategy_notes.tcl` for reference during physical design.

### 5. Security Documentation

The complete logical-to-physical mapping is documented in `key_mapping.encrypted`, which is formatted as an encrypted file and should be treated as classified documentation.

## Integration

### Modified Files

1. **`src/project.v`** (NEW) - Register scattering module
2. **`src/tt_um_vaelix_sentinel.v`** - Updated to instantiate project module
3. **`src/config.json`** - Added placement optimization settings
4. **`info.yaml`** - Added project.v to source files
5. **`test/Makefile`** - Added project.v to compilation sources
6. **`key_mapping.encrypted`** (NEW) - Secure mapping documentation
7. **`placement_strategy_notes.tcl`** (NEW) - Physical placement documentation

### Verification

The existing test suite in `test/test.py` verifies that:
- The correct key (0xB6) authorizes access
- All 255 other keys are rejected
- The visual deception does not affect functional behavior

## Security Properties

1. **Register Distribution**: Individual 1-bit registers can be scattered during placement
2. **Name Obfuscation**: Register names appear as unrelated system state variables
3. **Visual Deception**: FIB inspection reveals 0xAA instead of 0xB6
4. **Functional Preservation**: Authorization logic remains unchanged
5. **Documentation Security**: Mapping stored in encrypted file outside source code

## Usage

The module is automatically integrated into the build system. No changes are required to the external interface or operation of the Sentinel Mark I.

```bash
# Run verification
cd test
python3 test.py

# View implementation
cat src/project.v
```

## Notes

- The `(* keep_hierarchy *)` attribute prevents synthesis from collapsing the scattered registers
- Reset logic properly initializes registers at power-on/reset for ASIC synthesis
- The deception strategy can be adjusted by changing which bits use inverted storage
- Physical placement of standard cells is ultimately determined by the OpenROAD placer based on timing, congestion, and other constraints

---

**Classification**: TIER 1 CLASSIFIED  
**Revision**: 1.0  
**Date**: 2026-02-16
