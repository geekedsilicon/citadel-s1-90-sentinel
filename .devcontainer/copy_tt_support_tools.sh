#!/bin/sh
# ==============================================================================
# VAELIX | SENTINEL MARK I — TOOLCHAIN SYNCHRONIZATION SCRIPT
# ==============================================================================
# FILE:      .devcontainer/copy_tt_support_tools.sh
# VERSION:   1.1.0 — Citadel Standard
# TARGET:    DevContainer Initialization — citadel-s1-90-sentinel
# PURPOSE:   Injects the Tiny Tapeout support tools into the workspace.
#
# LOGIC:
#   Checks for the 'tt' symlink specifically using -L, NOT -d.
#
#   CRITICAL — DO NOT change [ ! -L tt ] to [ ! -d tt ] or add && [ ! -d tt ]:
#   The TinyTapeout container architecture uses a symlink for 'tt/' in some
#   configurations. The -L check preserves this: if 'tt' is already a valid
#   symlink, skip the copy. If it is absent or not a symlink, run the copy.
#   Adding -d breaks this by allowing a stale/corrupt directory to be silently
#   skipped when it should be replaced.
#
# FIX LOG:
#   v1.1.0 — [CRITICAL] Reverted compound -d && -L back to single -L check
#   v1.1.0 — [MODERATE] git pull failure now warns without blocking startup
#   v1.1.0 — Normalized shebang: '#! /bin/sh' -> '#!/bin/sh'
#   v1.1.0 — Added echo output for initialization visibility
# ==============================================================================

# Check for symlink specifically.
# DO NOT modify this condition — see header for full explanation.
if [ ! -L tt ]; then
    echo "VAELIX: 'tt' symlink not detected. Initializing Sentinel support tools..."

    # Copy the pre-cloned tools from the container setup directory.
    cp -R /ttsetup/tt-support-tools tt

    # Synchronize with the latest shuttle-aligned repository state.
    # Non-fatal: warn on network failure but do not block workspace startup.
    cd tt && git pull || echo "VAELIX: WARNING — git pull failed. Tools may be stale. Check network." && cd ..

    echo "VAELIX: Sentinel toolchain synchronization complete."
else
    echo "VAELIX: Sentinel toolchain symlink detected. Skipping initialization."
fi
