# journal: routing — interposer (Board C)

## 2026-07-24 09:15 — iterate 1 (two systematic opens, diagnosed to PREP config)
- did: prep + KRT race 3 (shadow root: root-scoped generics read the OTHER
  board's 03_src/rules symlinks; see route.yaml header + rebuild_all.sh).
- result: ALL candidates 2 unconnected + 2 violations — systematic. Measured
  diagnosis: (a) prep's mounting_holes NPTH matcher fenced the two 10FDZ-BT
  polarization BOSSES (NPTH 2.54mm from pin 1); the r=3.0 keepout squares
  swallowed J_MEMBRANE.1 + J_CN1_JUMPER.1 (KRT failed in 5002 iters — start
  blocked). (b) track_width 0.5 grid-rounds to 0.4998 < KEYPAD_ISO 0.5 floor.
- fix (upstream config, not board): mounting_holes refdes_prefix "H" (only
  real mounting holes fenced); wave track_width 0.508.

## 2026-07-24 09:20 — finish (routing gate GREEN, all measured)
- KRT race 3: ALL candidates CLEAN (0 unconnected / 0 violations); winner c0
  imported: 183 segments, 35 vias. quick: CLEAN. Chain promoted to
  03_src/interposer/route/final_chain.kicad_pcb (canon M3).
- DRC --severity-all --refill-zones --schematic-parity: 0 / 0 / 0.
- M-REPRO: bash 03_src/interposer/rebuild_all.sh (fresh shadow root, promoted
  chain) -> DRC 0/0/0 reproduced.
- ISOLATION (BRIEF §5) measured structurally: copper nets on board = exactly
  the 10 KP_* nets; 0 zones; no GND/power net exists anywhere. Floating
  keypad domain by construction.
- board: 54.1 x 46.1mm, 2-layer, tier jlc_2layer_default.
- next: verification battery (fab export, twin, pin review, render review,
  red-team lenses, policy audit) -> seal interposer-v1.0-2026-07-24.
