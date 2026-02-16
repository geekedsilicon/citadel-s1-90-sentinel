![](../../workflows/gds/badge.svg) ![](../../workflows/docs/badge.svg) ![](../../workflows/test/badge.svg)

# VAELIX | SENTINEL MARK I
## THE "ZERO-DAY" CHALLENGE COIN
**"Si Vis Pacem, Para Bellum."**

---

## 01 | THE ARTIFACT
The **Sentinel Mark I** is the physical manifestation of the Vaelix security philosophy. It is a functional 130nm ASIC designed not for computation, but for **Verification**. 

This chip serves as a hardware-level "Challenge Coin"—a sovereign token distributed only to TIER 1 partners. It carries a single, hardcoded cryptographic puzzle buried in the silicon logic. 

**Mission Status:**
* **Fabrication:** IHP 130nm SG13G2 (Tiny Tapeout 06 / IHP26a).
* **Function:** 8-Bit Hardware Authorization Gate.
* **Custody:** Vaelix Systems Engineering.



---

## 02 | THE LOGIC: "INDIVISIBLE"
Unlike software, which can be patched, the logic of the Sentinel Mark I is immutable. It is etched into the transistor mesh using **Citadel Primitives**.

* **The Lock:** A Finite State Machine (FSM) monitoring the 8-bit input bus.
* **The Key:** A specific 8-bit vector (`0xB6`) hardcoded into the gate layout.
* **The Response:** * **State A (Denied):** The 7-segment display shows a "Locked" pattern (`0xC7`). The chip remains silent.
    * **State B (Verified):** Upon correct key entry, the display shifts to "Verified" (`0xC1`) and the Status Array ignites.

---

## 03 | OPERATIONAL INTERFACE
To verify custody of the Sentinel Mark I, the operator must interface with the **Vaelix Evaluation Terminal** (TT06 Demo Board).

### **Authorization Sequence**
1.  **Insert:** Place the Sentinel Coin into the socket.
2.  **Input:** Toggle the DIP switches to match the **Vaelix Key** (`10110110`).
3.  **Confirm:** Observe the telemetry. 
    * If the **"V"** (Verified) pattern appears, the token is authentic.
    * Any deviation results in immediate logic rejection.

> **Note:** The layout includes a microscopic **Vaelix Logo** etched onto the Metal 5 layer, visible only via electron microscopy, serving as a physical watermark of authenticity.

---

## 04 | FOUNDRY SPECIFICATIONS
**"The Luxury of Silence."**

| Parameter | Specification |
| :--- | :--- |
| **Foundry** | IHP (Innovations for High Performance Microelectronics) |
| **Node** | 130nm SG13G2 (BiCMOS) |
| **Clock Speed** | 25 MHz (Stability Optimized) |
| **Logic Density** | 65% (Fortified) |
| **Power Profile** | Passive / Event-Triggered |

---

## 05 | ENGINEERING LINEAGE
This chip is the direct descendant of the **Project Citadel** FPGA prototyping performed on the **Xilinx RFSoC 4x2** and **PYNQ-Z2**. It translates the "Brain" of the S1-90 into a tangible, holdable asset.

---

## 06 | CI/CD HARDENING: THE WARDEN
The Sentinel Mark I employs automated metrics monitoring to enforce design efficiency and prevent unwanted bloat.

**The Warden** is an automated CI/CD guard that:
* Compares gate count (cell count) between the current branch and the main branch baseline
* **Fails the build if gate count increases by more than 5%** without explicit authorization
* Provides two bypass mechanisms for justified increases:
  * Include `[bypass-metrics]` in your commit message
  * Manually trigger the workflow with the "Bypass metrics threshold check" option enabled

**Why This Matters:**
* Gate count correlates directly with power consumption and silicon area
* Prevents accidental logic bloat from degrading the design
* Enforces "symmetry and efficiency" — the Vaelix engineering standard

**Pipeline Flow:**
```
gds → metrics (THE WARDEN) → viewer
```



---
**VAELIX SYSTEMS** *Tier 1 Defense Technology.* © 2026 Vaelix Systems. All Rights Reserved.
