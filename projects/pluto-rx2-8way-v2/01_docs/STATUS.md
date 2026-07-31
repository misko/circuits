# STATUS beacon — the live head of the journal

This file is the ONE place a coordinator reads to know, in a glance, where this
board is between gates. It is OVERWRITTEN (not appended) at every transition —
the append-only history lives in `journal/<stage>.md`; this is only the current
frame. Rewrite it at every stage enter/finish, every iterate, and IMMEDIATELY
BEFORE and AFTER every long blocking op (see SKILL.md "Journal discipline").

Read by `skills/kicad-pcb/scripts/pcb_status.py`. Everything below the fence is
`key: value` (one per line); `#` lines and blanks are ignored by the reader.

Multi-board projects: one beacon PER board, named `STATUS-<board>.md`
(mirroring the per-board `journal/<stage>.md` suffix). A single-board
project uses this bare `STATUS.md`.

## Schema

| field | meaning | vocabulary |
|---|---|---|
| `stage` | which pipeline stage the board is in | `commission` \| `parts` \| `schematic` \| `placement` \| `routing` \| `verify` \| `seal` |
| `step` | the specific thing happening RIGHT NOW, one line | free text |
| `measure` | the last MEASURED numbers (gate output, counts) — never hope | free text; the rebuild loop tees its last line here |
| `state` | the coordinator's traffic light | `working` (progressing) \| `blocked` (STOPPED, escalated to coordinator) \| `done` (this stage's gate is green) |
| `next` | what happens on the next transition | free text |
| `op_pid` | pid of the running long op, or empty when idle | integer or empty |
| `updated` | when this frame was written, ISO-8601 local | `YYYY-MM-DDTHH:MM:SS` |

`state: working` + a fresh `updated` + a live `op_pid` = progressing (coordinator
POLLS, does not interrupt). `state: working` + a STALE `updated` + no live
`op_pid` = STALLED (the reader flags it). `state: blocked` = a decision or
D-BACK wall the agent has PUSHED up — the coordinator acts. `state: done` =
terminal for this stage.

<!-- reader parses from here down -->
stage:   routing
step:    "STOPPED AT THE COPPER BOUNDARY, DELIBERATELY. The RF line type was settled BY MEASUREMENT before anything was graded: the arms are GROUNDED COPLANAR WAVEGUIDE, not the bare microstrip every v2 document described. The constant set and the via-fence CRITERION were both re-derived for the real cross-section and COMMITTED TO THE JOURNAL BEFORE the board was re-measured against them (entries 23:20 and 23:35 in journal/05_verify.md, written before fence_pitch.py was re-run). The correct bound came out 13% TIGHTER, not looser, so correcting the physics does NOT rescue this board - it fails harder. All non-copper artifacts are corrected and committed; the board needs a re-stitch and a CTRL re-route and is NOT sealed. No release directory exists and none was staged."
measure: "LINE TYPE (MEASURED, 03_src/line_type.py off 04_kicad/*.kicad_pcb through pcbnew, 6007 side-samples): GND pour flanks EVERY arm at 0.2005-0.2010 mm edge-to-edge on BOTH sides - median 0.2010, min 0.2005, i.e. the pour ran to the 0.200 mm DRC clearance and stopped. g/h 0.955, g/w 0.558, w 0.360 on every segment. Two-sided coplanar over 61.3-93.2% of each arm (mean 75.2%; ANT5 66.9 ANT1 77.2 ANT4 76.7 ANT6 78.4 RX2_OUT 78.4 ANT2 84.5 ANT3 85.2 ANT7 87.7 RX1_TAP 93.2 RX1_MAIN 61.3). The 8-29% remainder is NOT microstrip: one interval per arm, 1.40-1.75 mm at the SMA end, coinciding EXACTLY with the In1.Cu antipad void - that is the LAUNCH, no coplanar ground and no reference plane. NO BARE-MICROSTRIP SECTION EXISTS ON THIS BOARD. In1.Cu otherwise continuous beneath every arm; RX1_TAP has no void at all. CONSTANTS (DERIVED, ADR-0004, tuple = JLC04161H-7628 h0.2104 er4.4 t0.035 / w 0.360 / conductor-backed CPW s 0.2005 both sides BARE / conformal mapping Ghione-Naghed-Wolff): eps_eff 3.1557 (was 3.3286, -5.19%), Z0 51.249 ohm (was 50.29, +1.9%), t_pd 5.9255 ps/mm, lambda_g 28.1269 mm, 12.7991 deg/mm (was 13.145) = -4.97 deg on a 14.366 mm arm. Independent r2 layout lens got 3.1552 with its own script - 0.016% apart. BOUND (DERIVED AND COMMITTED BEFORE MEASURING): the coplanar pour already IS the lateral wall (aperture zero), so the vias' job is to SHORT that pour to In1.Cu against the parasitic parallel-plate mode, which fills the dielectric between two planes and runs at BULK er: lambda_pp = lambda_0/sqrt(4.4) = 23.8201, lambda_pp/20 = 1.1910 mm. Ranked: microstrip lg/20 1.3693 - CBCPW lg/20 1.4063 - parallel-plate 1.1910 BINDING - free space 2.4983. 13% TIGHTER, and tighter across the whole Dk window 4.2-4.6 (1.2190/1.1648). M-BOUND CITED, regenerates 1.1910 exact, GOVERNS 20.0001>=20. GRADE (MEASURED): worst interior along-arm aperture 3.0500 mm at ANT4 sideW s=7.12..10.17 = lambda_pp/7.81 = 2.56x the bound, 17 of 20 arm-sides OVER (was 11 of 20 at 1.35), 34 apertures total, VERDICT FAIL, exit 1. CLASSIFIED BY CAUSE not counted: A lattice projection 18 (NO occupier at all - 12 are exactly 0.95*sqrt(2); closes by re-stitching at pitch 0.80) - B SMA avoid rings 5 - C SSE control corridor 5 incl the 3.0500 worst (SW_V1/V3/V4+3V3 on F.Cu; nets.yaml ALREADY declares CTRL inner-layer) - D star hub/tap 6. BOARD UNCHANGED AND STILL GREEN: DRC --severity-all --refill-zones --schematic-parity --exit-code-violations = 0 violations / 0 unconnected / 0 parity, exit 0, both halves empty. policy_audit FAIL=2 (S-OCCL, now that its falsified waiver is withdrawn; A-POP MANIFEST-UNDECLARED, because there is deliberately no release), PASS=30, WAIVED=0. R-LEN PASS 8/8. E-NETREF PASS 88/88. generate_rules re-run leaves 04_kicad byte-identical, so no source edit reached copper."
state:   blocked
next:    "THE BOARD NEEDS COPPER AND THAT IS THE ESCALATION. No honest reading of the physics passes a 3.0500 mm aperture: lambda_pp/8 = 2.9775 still fails it and only a lambda/4-class criterion would let it through, which is a resonance limit and not a fence criterion. The re-route, in order: (1) route.yaml stitch pitch 0.95 -> 0.80 (closes class A = 18 of 34, and it is a config value); (2) CTRL onto In2.Cu across the rosette, which rules/nets.yaml already declares and 90-96% of SW_V1/V2/V4 copper does not do - closes class C incl the worst aperture; (3) drop meander_amplitude from the rf wave, since the placement matches to 0.001 mm so the pass had nothing to correct and left six 37-ohm sections (layout L-03); (4) move the two SW_V4 vias >= 0.30 mm off ANT5 (L-04: 0.0224 mm of In1 antipad margin, inside registration tolerance); (5) de-collide the schematic labels in the tsx - closes S-OCCL and the N3V3_MOD x ANT2 overlap that makes the shipped PDF say the 3V3 rail is wired to an RF port; (6) rebuild, then re-gate ALL FOUR lenses fresh-context with DISTINCT filenames. CLASSES B AND D SURVIVE ALL OF THAT (11 of 34) and need either a per-arm fence pass the shared stitcher does not have, or a declared exception whose evidence is a MEASUREMENT of what those apertures cost in isolation. A candidate argument for class B is written down in ARCHITECTURE sec 6 and deliberately NOT applied, because it was formed after seeing which apertures failed. TWO PROPOSED skills/ PATCHES REPORTED, NOT MADE (partition): promote the four RF instruments into the shared backend (this is the second board to need them, which the 03_src contract says triggers mandatory promotion), and point the S-OCCL occlusion checker at the SHIPPED tscircuit render rather than only the converter .kicad_sch - the withdrawn waiver's premise was a claim about which file a defect appears in, and no gate compares those two files."
op_pid:
updated: 2026-07-31T00:15:00
