subject: pluto-rx2-8way-v4 git 8c8d0466fb3ffca63335c40b284f2f864185e058
date: 2026-08-01
reviewer: redteam-agent (GPT-5, targeted layout/RF re-gate)
context-given: full-tree
review_type: redteam_layout
source_commit: 8c8d0466fb3ffca63335c40b284f2f864185e058
board_sha256: 4828a4a0dab6fed6e1d17afcd806877f84cf9e77bbf9b7741d3164fb880f0e30
fab_zip_sha256: 38c7bb16f22cc58d44e2d225429ff20bbbf404376cd70972bc75c4064eabf45f
design_verdict: SOUND
order_verdict: DO-NOT-ORDER

# Targeted final adversarial layout / RF re-gate

## Scope and verdict

This is the exact-artifact re-gate of the sole P0 found in the final review of
commit `344dfba05f7160b99b56dc9722cf8be72e846c7e`: two realized RF-fence
apertures exceeded the binding 1.1910 mm limit. The repaired board is **SOUND**.
The shared saved-board gate now grades all 22 configured arm-sides, the two
formerly failing flanks are below the limit, and every targeted regression gate
passes. There is no open P0 layout, RF, PI, thermal, or manufacturability defect
in the reviewed artifact.

The order verdict remains **DO-NOT-ORDER**, not `BLOCKED-SOURCING`. Catalog
stock evidence is clear at 11/11 lines. The hold is for the documented vendor,
exact-artifact release, uploader, and first-article qualifications, not for a
known design defect or unavailable part.

## Frozen subject and repair-delta proof

- `git rev-parse HEAD` resolves exactly to the source commit in the header.
- The board and Gerber archive reproduce the exact SHA-256 values in the
  header. Fresh DRC with zone refill left the board hash unchanged.
- The saved RF field evidence is
  `06_build/verify/cpwg_field.json`, SHA-256
  `90ddd56b8ca0baccf3bca1424ddd1ad9010a801a8865abdc72df1a58664ed7fc`.
- An independent top-level KiCad-form comparison against the `344dfba0` board,
  with UUID/tstamp and whitespace noise removed, finds exactly two semantic
  copper additions: 0.25/0.15 mm through GND vias at
  `(41.060, 57.800)` and `(46.312, 42.281)` mm. The only other changed board
  form is the regenerated F.Cu GND filled zone. Footprints, pads, nets, routed
  signal copper, other vias, outline, and authored zone geometry are unchanged.
- The complete source delta `872e4f4a..8c8d0466` changes only the shared fence
  checker's G-INPUT/G-COVER reporting and adds a red/green saved-board test. It
  changes no project design, generated board, BOM, CPL, netlist, or fabrication
  artifact.

## Findings

| ID | Severity | Finding | Evidence | Disposition |
|---|---|---|---|---|
| LRF-01-RG | CLOSED P0 | The prior ANT4-W / ANT7-W fence defect is repaired on the saved board. | Shared gate: 22/22 arm-sides graded, 0 over; `ANT4 W = 1.1500 mm`, `ANT7 W = 1.1502 mm`, board worst `RX1_TAP E = 1.1769 mm`, all against `<=1.1910 mm`. | Closed. The repair is exactly the two documented legal GND vias plus regenerated zone fill. |
| LMF-01 | P1 order gate; not a design defect | POFV intent is authored, but the production process is not yet vendor-qualified. | Board setup contains `(filling yes)` and `(capping yes)`. Direct pad-hit measurement finds ten unique 0.25/0.15 mm via centres on U_SW lands: seven in pad 25 and one each in pads 18, 8, and 11. Gerbers alone do not select/confirm the service. | Before payment, obtain written whole-board resin-fill/copper-cap and flat-land DFM acceptance; verify production-file interpretation; inspect the first panel by X-ray or cross-section. |
| LMF-02 | P1 order/first-article gate; not a design defect | Controlled impedance, plug-in SMA assembly, and the user-fitted RP2040-Zero remain physical/vendor qualifications. | The masked field solve is green; the ten C504007 SMA jacks remain `Plugin` PTH placements; U_MCU remains intentionally excluded from BOM/CPL/paste. | Obtain production-stack/coupon TDR approval, VNA characterization, written plug-in assembly acceptance, and module fit/fillet/current/thermal evidence. |
| LREL-01 | P1 release-process gate; not a design defect | The checked-in layout seal predates this repaired exact board. | `06_build/layout_seal.json` binds board SHA `dbbb3fce...`, not reviewed SHA `4828a4a0...`. | Regenerate the exact-artifact layout seal, policy audit, staged manifest, and final release battery before order release. |
| LPI-01 | P2 process debt | The documented LS-pin geometric assertion is still absent from the project audit, although the reviewed geometry previously passed direct measurement. | The PE42482 dossier assigns the check to audit I8; `audit_board.py` does not implement it. This targeted repair did not move U_SW or its local copper. | Promote the assertion into a shared/project gate before a future local geometry change. No current-board defect. |
| LDOC-01 | P2 documentation debt | Historical comments still contain stale board dimensions/via counts. | The reviewed board is 50.0 x 73.0 mm and now contains 3,442 vias; older prose cites prior values. | Correct narrative text in a later source-only revision; no copper consequence. |

## Targeted regression evidence

| Gate | Fresh measured result |
|---|---|
| Shared saved-board fence | PASS, 22/22 arm-sides; 1.1769 mm worst <= 1.1910 mm |
| Fence checker red/green test | PASS; full `tests/t1_copper_length.py` battery 26/26, including 14 known-bad fixtures that failed their checker as required |
| KiCad 10.0.4 DRC | PASS, 0 violations / 0 unconnected / 0 schematic-parity issues |
| Project geometry audit | PASS, module keepout clear; SW_V4/ANT4 crossing remains on In2.Cu; In1.Cu GND uninterrupted |
| Tier / aspect preflight | PASS, 0 failures / 2 explained scoped-clearance warnings; 1.2/0.15 = 8.0:1 versus 10:1 tier limit |
| R-LEN | PASS, 8/8 paths, 0 UNREACHED; 0.1208 mm spread <= 1.0 mm, equal to 0.718 ps / 1.55 degrees at 6 GHz |
| RF field solve | PASS; finest mesh `Z0 = 52.0877 ohm`, `epsilon_eff = 3.173354`, relative residual `<2e-9`; saved tuple uses measured worst pitch 1.1769 mm |
| POFV source intent | PASS source-side: native fill/cap flags and all ten fixed U_SW sites present; vendor execution remains LMF-01 |
| Sourcing | CLEAR, stock check PASS 11/11 lines, 0 failures / 0 uncoded lines |

The tier preflight's two warnings are deliberate 0.14 mm RF/rule-area
clearances and explicitly defer their geometric enforcement to KiCad DRC; the
fresh DRC is clean. Board thickness is 1.2 mm, so nominal via aspect ratio is
8.0:1; even the documented +0.10 mm thickness tolerance gives 8.67:1, below the
10:1 declared tier limit.

The regenerated field solve is now downstream of the shared saved-board fence
gate in both rebuild drivers. Its model records `via_pitch_mm: 1.1769` and
`geometry_source: saved PCB direct measurement; shared fence_pitch gate`.
Thus the old contradiction between the saved board and the solver tuple is
closed rather than merely judged electrically insensitive.

## Severity summary

- P0: 0 open; prior LRF-01 is closed.
- P1 design defects: 0.
- P1 order/release/first-article qualifications: 3.
- P2 process/documentation debts: 2, neither changed by the two-via repair.

## Final verdict

`design_verdict: SOUND`. The final adversarial layout/RF re-gate passes for
source commit `8c8d0466`, board SHA `4828a4a0...`, and fabrication archive SHA
`38c7bb16...`.

`order_verdict: DO-NOT-ORDER`. Sourcing is clear, but the documented POFV,
controlled-impedance, plug-in assembly, exact-artifact release, uploader, and
first-article gates must be discharged before payment or production release.
