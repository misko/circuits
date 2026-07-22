# Fresh-context render review — crow-array-pod v1.0 (2026-07-18)

Reviewer: independent fresh-context agent (no design-session context),
inputs: schematic PNG, pcb_layers pages, assembly view, six twin renders.

## Graded verdicts (canon S5/S6/S7)

- **S5 design math: PASS.** Both spot-checked values re-derived against
  DETAIL_DESIGN.md: stage-A gain 1 + 10k/20k = x1.5 (R6/R7) and midpoint
  2.47V from the 10k/10k divider on 5VF (~4.93V after the 100R drop).
- **S6 schematic readability: EFFORTFUL.** Story-critical hops are drawn
  (mic bias -> capsule pads, coupling -> 100k bias, both feedback strings,
  isolation -> choke, beeper series -> transducer, V+ -> decoupler), but
  inter-region flow (e.g. A_OUT from region 6 into region 7) is
  label-glued and must be mentally re-netted. Recorded as the expected
  schwriter2-era grade; debt stays visible.
- **S7 decoupling adjacency: PARTIAL (adequate).** C6 100n is drawn wired
  to U1 V+ in the amplifier region; C7 10u bulk sits in the same region
  but connects by labels.

## Findings and dispositions (fix evidence in this directory)

1. **MAJOR — J1 had no 3D body in the twin renders** (KF128L-3.5-8P is
   consign-only; EasyEDA has no CAD for C5342501 — adjudicated NO-CAD).
   FIXED for verification: four bodies of the same-series KF128L-3.5-2P
   (C474930, CAD available; identical 3.5mm pitch, same body section)
   mounted along the 8P row at local x = 1.75/8.75/15.75/22.75mm on a
   twin-board copy. Evidence: twin_j1_top.png (wire mouth faces WEST
   toward the gland wall, body inside the outline, clear of H1/H3),
   twin_j1_edge_west.png (8 wire entries, ~9mm body height vs the
   1551WY's 16mm interior above board plane; THT pins protrude ~3mm
   below — the enclosure bosses provide the standoff), twin_j1_iso.png.
2. **D2/D3 flyback polarity silk.** The D_SMA footprint's own cathode
   bar exists but graded too subtle. FIXED in the generator: an explicit
   "K" glyph is now placed beside pad 1 (cathode) of BOTH clamp
   positions, collision-checked. Evidence: twin_j1_top.png shows "K" on
   the west (BZ_P) side of D2 and D3; audit I9 machine-checks pad1 net =
   BZ_P for both. CPL rotation: D_SMA is in the rotations DB; order-day
   preview check item 3 in ORDER_README covers the reel-orientation
   residual.
3. **U1 refdes printed UNDER the SOIC body.** Root cause found and
   reported: the refdes de-collision pass used pads + silk as obstacles
   but not part BODIES, and audit I10 checked only layer+visibility — a
   checker hole. FIXED both: generator now treats every footprint's body
   bbox as an obstacle (wider search rings added), and the audit gained
   I10b (visible refdes must not intersect any body bbox). Evidence:
   twin_j1_top.png shows "U1" printed north of the SOIC; audit.txt PASS
   includes the new I10b check; DRC stayed 0/0/0 after the silk moves.
4. **Cosmetic — assembly_top.pdf value-text overlap** in dense clusters
   (F.Fab values at fixed positions). Known issue, noted in ORDER_README;
   the silkscreen (what the assembler/user sees) is clean and DRC-checked.
