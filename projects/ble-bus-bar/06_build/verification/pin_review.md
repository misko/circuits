# Fresh-context pin review — ble-bus-bar v1.0 (2026-07-18)

Protocol: kicad-pcb/references/pin-review-protocol.md. Four independent
fresh-context agents, one per part group, each derived expected pinouts
from the datasheet figures (rendered via pdftoppm) and judged the board's
actual nets from the pin_audit dossiers. **Zero FAILs.** QUESTIONs below
carry the orchestrator's dispositions with evidence.

## Verdicts

| Part | Reviewer verdict | Disposition |
|---|---|---|
| U7 ESP32-C3-WROOM-02 | PASS (winding CCW match, FSPI set coherent, USB D+/D− not swapped) + QUESTION on strap pull-ups | RESOLVED: R20 10k→IO8, R18 10k→IO2/MISO, R19 10k→FLASH_CS, R21 10k+C10 1µ+SW1 on EN, SW2 on IO9 — all present in the schematic (region 4) and netlist |
| U11 W25Q64JVSSIQ | PASS + QUESTION on FLASH_CS pull-up | RESOLVED: R19 10k FLASH_CS→3V3 (protects the IO2 strap read) |
| U1 INA238 (×6) | PASS on winding/pins/VBUS-to-KB legitimacy + QUESTION on address uniqueness and KA-side | RESOLVED: board query shows U1..U6 straps → 0x40,0x41,0x42,0x43,0x44,0x45 (all distinct); KA(IN+) taps the VF (fuse/supply) side via RP pad1=VF (generator assert) and audit IK verifies the attach inside RS pad1 [VF] — positive-current sign convention correct |
| RS1 WSLP2726 | PASS (pads 5.71×2.69 @ 4.92mm vs 4.93 spec = dossier rounding) | Kelvin-tap note satisfied: taps leave the pad INNER edges (audit IK), not the current path |
| F1 3557-2 | PASS pattern/nets + QUESTION on drill | RESOLVED: finished drills are Ø1.7mm (board query) vs catalog Ø1.6 nominal — +0.1mm on a 1.57×0.69mm pin is a standard hand-solder fit |
| U8 LMR16006X | PASS (all 6 pins, BOOT/FB/SHDN/SW topologies verified) | — |
| U9 AMS1117-3.3 | PASS (tab=VOUT merge correct) | — |
| D7/D8/D9/D10/D11 | PASS (all five cathode orientations independently derived and correct) | — |
| LED1/LED2 KT-0805G | QUESTION (nets correct iff pad1=cathode; no per-part datasheet) | ACTION CARRIED: "verify cathode mark on first reel" added to ORDER_README preview checklist (assembly-time check; wiring is correct under the KiCad LED pad1=cathode convention used consistently) |
| J9 TYPE-C-31-M-12 | PASS (contact table exact, CC1/CC2 independent 5.1k Rd, no A/B swap) | — |
| U10 USBLC6-2SC6 | PASS (pass-through pairs consistent, VBUS on USB 5V) | — |

## Result

PASS — no order-blocking findings. Full reviewer transcripts summarized
above; QUESTIONs all resolved with board-file evidence or carried as
explicit assembly-time actions in ORDER_README.
