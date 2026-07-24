    date: 2026-07-24
    subject: smc0985-cooksense interposer v1.0 (pre-seal staging)
    reviewer: redteam-agent (fable-medium, lens b: layout/mechanical/manufacturability)
    context-given: zero-context (board + fab outputs + datasheets, measured with pcbnew)
    verdict: ORDER

# Red-team lens (b) layout/mechanical/manufacturability — interposer v1.0 (verbatim)

Board: 54.0 x 46.0mm outline, 2 layers, 0 zones, DRC --severity-all --refill-zones --schematic-parity = 0/0/0.

1. 10FDZ-BT vs eFDZ (p.2-3): pin drill 0.900 (20x) vs 0.9±0.05; pitch 2.540; span 22.860 = A; NPTH boss 1.800 @ x=22.46 colinear; annular 0.35mm hand-solder ok; mask openings all 20 pads. All match.
2. Mechanical: housing-to-housing gap 17.71mm; both top-entry, sliders open vertically (12.7mm) with nothing taller than the 4mm GH nearby — finger/slider access to both, both tails insertable from top. Side margins 9.4/7.7mm; no courtyard overlaps; all 4 mounting holes clear.
3-4. Copper/drills: 183 segments all 0.508mm; vias 35x 0.6/0.3 (annular 0.15 >= JLC 0.13 min). Drill files exact: NPTH = 2x 1.800 + 4x 2.700, PTH = 20x 0.900 + 35x 0.300. Floating-domain claim holds: every track/via/pad on one of the 10 KP_* nets; 0 zones; each net exactly 5 pads; 0 unconnected.
5. Edge clearance: worst track 1.146mm, worst pad 2.30mm — all >= 0.3.

| Sev | Finding | Evidence |
|---|---|---|
| P2 | Three near-zero-angle same-net track junctions (redundant/doubled-back stubs) | (30.10,28.00) 0.0deg, (31.70,37.10) 3.6deg, (28.40,37.10) 8.7deg — DRC-silent, cosmetic |
| P2 | Via annular 0.15mm close to JLC 0.13mm floor | 35x via 0.6/0.3 |
| P2 | 26.6deg fanout angles at GH pads — wedge filled by pad, not true acid traps | 8 junctions at x=16.8 |

Verdict: ORDER. All P0-class checks pass with measured margins; P2s cosmetic.
