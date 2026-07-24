# RESUME — smc0985-cooksense (multi-board project; MAIN board = cooksense)

**Stopped:** 2026-07-23 ~18:55, mid pre-seal batch, on the Fable-5 session quota (resets 8:10pm PT).
Closest of the three in-flight boards to seal.

## Where it stands
- **Routing gate committed** (`349372c`, later fix commit `9f5c385`): DRC 0/0/0, reproducible.
- **Full verification fan-out DONE** — all clean/dispositioned:
  - **Twin: GREEN** (23 CRITICALs adjudicated with measured per-class evidence; the one "MIRRORED" J_PI
    proven to be a pin-numbering-wind, not a physical mirror).
  - **Pin review: 5/5 groups, 0 confirmed pin-map defects** across ~50 parts.
  - **Render/silk: PASS** (all 77 S-OCCL occlusions individually cosmetic-OK; iso-barrier 6.12mm measured).
  - Reviews in `08_reviews/` + `06_build/verification/`. Beacon: `01_docs/STATUS-cooksense.md`.
    Journal: `01_docs/journal/routing_cooksense.md`. (Lead was mid-writing the DISPOSITIONS ledger.)

## The batch to fold in ONE rebuild (before seal)
Three schematic/board changes:
1. **'238 decoder pull-downs** — SAFETY: on a watchdog trip the shift registers tri-state, floating the
   SN74HC238 (Nexperia 74HC238D, C5620) enable pins → a floated-high enable can phantom-fire a relay while
   the coil rail is live. Add pull-downs (or gate COIL_EN through the fault chain). Real fix, not a waiver.
2. **J_MODE re-pin** to the sibling 3V3/GND convention (unkeyed GH housing cross-plug shorts COIL_EN↔3V3).
3. **J_TC footprint** — add the 4× dia-1.77mm NPTH bracket/PC-pin holes its own part.yaml + the Omega
   drawing require (missing = no mechanical retention; round pins may not fit the 0.9mm slot pads).

Plus these dispositions (trace/decide/document, mostly ORDER_README or waiver-with-evidence):
- **PWR_GOOD_N polarity** (safety chain): U_EFUSE.6 FLT is LOW=fault but the net name implies low=power-good
  — trace the consumer; confirm the AND-chain logic is right or fix + rename honestly.
- **D_REVCLAMP** on 5V_IN is upstream of the polyfuse (unfused reverse path) — document or move downstream of F1.
- **J_PWR** Molex pin-1-vs-key never confirmed vs the SD drawing → ORDER_README bring-up check.
- **J_ESTOP** contactor loop through a 1.0A/50V GH contact → cite coil inrush/hold vs rating or waive w/ evidence.
- **J_TC chromel(+)-to-pad-1** mapping unconfirmed (keyed jack) → ORDER_README continuity check.
- **U_COMP Vicr corner**: open-thermistor pulls sense to 3.3V vs 3.0V guaranteed (VCC=5V) → verify LM393
  behavior or note Pi ADC open-detect (brief C14) as the covering mechanism.
- **J_PI**: net map is 40/40 CORRECT vs Pi J8. The "FAIL" was an assembly-doc contradiction — design is the
  **ribbon SIDECAR** (silk + ADR-0007 agree; gotcha #1 is stale). Fix the stale gotcha + specify in
  ORDER_README a 40-way ribbon with a **MALE DIL-IDC** board-end plug (standard Pi ribbons are female-female
  and cannot mate this socket) + pin-1 keying discipline. No board change if confirmed ribbon-sidecar.

## Next steps to seal
Fold the 3 board changes + dispositions → ONE rebuild → DRC 0/0/0 → finalize ORDER_README (self-supplied
DO-NOT-SUBSTITUTE: DIP05-1A72-12L ×12 + PCC-SMP-K J_TC; order-day stock rechecks; the bring-up checks above;
no draft markers) → seal build → independent seal-verify (DRC + MANIFEST + ignore-sweep + freshness gate +
semantic M-BOM) → seal `cooksense-v1.0`.

## Watch-outs
- **INTERPOSER (Board C) is DEFERRED** — coupon-gated on a physical connector measurement; do not work it.
- Process gap the review exposed: hand-solder parts absent from `bom_jlc.csv` got NO pin_audit dossier
  (the safety-relevant J_TC went structurally unreviewed until a human lens caught it) — harvest item.
- Multi-board project (ADR-0007): per-board `03_src/cooksense/`, `04_kicad/cooksense.*`, `07_releases/cooksense-v*`.
  Tasks #23/#24 (this board), #25 (interposer).
