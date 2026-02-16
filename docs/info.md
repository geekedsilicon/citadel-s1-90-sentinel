# VAELIX | SENTINEL MARK I
**"The Luxury of Silence. The Certainty of Logic."**

## How it works

The **Sentinel Mark I** is a hardware-level cryptographic "Challenge Coin" implemented on the IHP 130nm SG13G2 process. Unlike software authentication, which is vulnerable to memory injection, the Sentinel relies on **Indivisible Logic**—a hardcoded transistor mesh that physically rejects unauthorized input vectors.

**Architectural Overview:**
* **The Core:** An 8-bit combinational comparator gate monitoring the `ui_in` bus.
* **The Vaelix Key:** The system is permanently fused to authorize only the input vector `0xB6` (Binary: `1011_0110`).
* **The Response:** * **Locked State (Default):** The logic drives the 7-segment display to a "Locked" pattern (`0xC7`) and silences the Status Array.
    * **Verified State:** Upon exact key entry, the logic instantaneously switches the display to "Verified" (`0xC1`) and ignites the Status Array ("Vaelix Glow").

## How to test

The Sentinel Mark I is designed for immediate field verification using the **Tiny Tapeout 06 Demo Board**.

**Authorization Sequence:**
1.  **Power On:** Ensure the board is active and the project is selected.
2.  **Observe:** The 7-segment display will show the **'L'** pattern (Segments F, E, D active). This confirms the "Sentinel Lock" is active and securing the perimeter.
3.  **Challenge:** Set the Input DIP Switches (`ui_in[7:0]`) to the **Vaelix Key**:
    * **Binary:** `1 0 1 1 0 1 1 0`
    * **Hex:** `0xB6`
4.  **Verify:** * The 7-segment display will shift to the **'U'** pattern (Segments F, E, D, C, B active).
    * The Bidirectional LEDs (`uio_out[7:0]`) will illuminate, confirming the logic path is open.
5.  **Intrusion Test:** Flip any single switch away from the key. The system must immediately revert to the **'L'** state, demonstrating zero-latency rejection.

## External hardware

This silicon is engineered to interface with standard Vaelix-cleared laboratory equipment:

* **Tiny Tapeout 06 Demo Board:** Primary evaluation platform.
* **Common Anode 7-Segment Display:** Required for visual telemetry (Active-LOW logic).
* **DIP Switch Bank:** Required for 8-bit key injection.
