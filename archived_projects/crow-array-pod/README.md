# crow-array-pod

Remote microphone pod PCB of the Crow Acoustic Localization Array
(commission: ../crow-array/01_docs/BRIEF.md). AOM-5024L-HD-R electret ->
OPA1678 two-stage active-balanced driver (~3 V/V differential) ->
8-position screw terminal onto a custom-pinout Cat5e home run; CMT-8504
calibration transducer driven from the central board. 2-layer 94.5x44.5mm,
fits the Hammond 1551WYBK max-PCB envelope.

- Docs: 01_docs/ (ARCHITECTURE, DETAIL_DESIGN, ADRs, board-local BRIEF).
- Everything regenerable: `03_src/rebuild_all.sh` (schematic -> ERC ->
  board -> audit -> route import -> stitch -> rules -> DRC 0/0/0 gate).
- Releases: 07_releases/ (immutable, per fab order).

## Gain changes (D8 — single-value gain parts, change table)

Differential gain = 2 x (1 + R6/R7). Stage B (R8=R9=20k) stays unity.

| Diff gain | R6 (OUT_A->FB_A) | R7 (FB_A->VMID) | Headroom note |
|---|---|---|---|
| 2.0 V/V | 0R (or short) | omit | unity stage A |
| **3.0 V/V (ship)** | **10k** | **20k** | clips ~116 dB SPL |
| 4.4 V/V | 12k | 10k | clips ~113 dB SPL |
| 6.0 V/V | 20k | 10k | clips ~110 dB SPL = mic THD limit |

Keep R6+R7 in the 10-30k window (noise vs op-amp load). The PCM1865 PGA
at the central end does fine ranging first — change board gain only if the
PGA runs out of range (source doc: start at 0 dB).

## Beeper clamp swap (ADR-0002)

Ship: D2 SS14 flyback populated, D3 SMAJ6.0A TVS empty. To trial the TVS
envelope: remove D2, fit an SMAJ6.0A at D3 (same orientation, cathode to
the +5V_BEEP side — both silked). R12 (0R) is the series swap point.
