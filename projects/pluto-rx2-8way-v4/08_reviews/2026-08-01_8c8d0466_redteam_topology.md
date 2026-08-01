# Targeted exact-artifact topology rebind

subject: pluto-rx2-8way-v4 8c8d0466
date: 2026-08-01
reviewer: redteam-agent (topology/protection/ratings lens)
context-given: full-tree
review_type: redteam_topology
source_commit: 8c8d0466fb3ffca63335c40b284f2f864185e058
board_sha256: 4828a4a0dab6fed6e1d17afcd806877f84cf9e77bbf9b7741d3164fb880f0e30
fab_zip_sha256: 38c7bb16f22cc58d44e2d225429ff20bbbf404376cd70972bc75c4064eabf45f
design_verdict: SOUND
order_verdict: DO-NOT-ORDER

## Scope and verdict

This is a targeted topology/protection rebind after the final RF-fence repair,
not a new broad review. The new exact board remains **SOUND**: the schematic,
netlist, part dossiers, BOM source, firmware mapping, power tree, component
placement, routed signal copper, and zones are unchanged. The material board
delta is exactly two added GND fence vias plus the source/driver integration of
the shared fence-pitch gate. No topology, signal path, pin assignment, control
truth-table mapping, protection boundary, or population decision moved.

The order verdict remains **DO-NOT-ORDER**, not `BLOCKED-SOURCING`. Current
catalog evidence is clear at 11/11 lines, but the documented JLC process,
exact-artifact release-freshness, uploader, and first-article physical gates
remain open.

## Exact-artifact evidence

- MEASURED: source commit resolves exactly to
  `8c8d0466fb3ffca63335c40b284f2f864185e058`.
- MEASURED: the current board and Gerber archive reproduce the exact SHA-256
  values in the header.
- MEASURED semantic diff against source commit
  `344dfba05f7160b99b56dc9722cf8be72e846c7e`: all 32 footprints, their
  values/FPIDs/positions/orientations/pad-net maps, all 179 routed segments,
  and all seven zones are identical. Via count moves from 3440 to 3442 with no
  removal. The only additions are GND, 0.15-mm drill, at
  `(41.060, 57.800)` and `(46.312, 42.281)` mm.
- MEASURED source diff: `01_docs/`, `02_parts/`, `03_tscircuit/`,
  `05_firmware/`, floorplan, electrical invariants, power tree, assembly rules,
  and promoted signal route are unchanged. `03_src/route.yaml` adds only the
  two GND via sites. The rebuild drivers add the shared `fence_pitch.py` gate;
  `cpwg_field_solver.py` changes only its geometry-source description. The
  complete `872e4f4a..8c8d0466` delta touches only the shared fence gate's
  G-INPUT/G-COVER output and its red/green saved-board test; it changes no
  project design, generated board, BOM, CPL, netlist, or fabrication artifact.
- MEASURED current generated identity:
  BOM SHA-256 `1d29b2f3d50320c6c604be3077ea88bdf71209db5474ef1709dad167f5eb1e8d`,
  CPL SHA-256 `5865a2b4badb74f2417f477cd12d9b083da8b9496c61feb53d9d0e39ba4189d0`,
  netlist SHA-256 `f11374a217b3520a3f6502471683a9684118be8f698428104032249bede79c6a`.

## Compact regression battery

| Check | Measured result |
|---|---|
| Net-label survival | PASS, 23/23 labels |
| Electrical intent | PASS, 25/25 invariants |
| Component parity | PASS, four source pairs agree over 28/28 refdes |
| BOM vs source | PASS, 11 BOM rows and 7/7 R/C rows value-graded |
| Power topology | PASS, 1/1 rail and converter |
| Setpoint/load margin | PASS, 934 mV headroom; 12 mV graded delivery drop |
| Off control | N-A by construction: externally USB-powered, de-energized by unplugging |
| Routing gate | PASS, 0 violations / 0 unconnected / 0 parity |
| RF fence gate | PASS, 22/22 arm-sides; worst interior gap 1.1769 mm <= 1.191 mm |
| Catalog stock | PASS, 11/11 graded lines; zero failures and zero uncoded lines |

## Topology re-confirmation

- RF mapping is unchanged: J_ANT1..J_ANT7 feed PE42482 RF1..RF7;
  J_ANT8/J_RX1 share `RX1_MAIN`; the two 220-ohm series pickoff resistors feed
  RF8; RFC feeds J_RX2. SMA pad 1 remains signal and pads 2..5 remain GND.
- Control mapping is unchanged: RP2040-Zero GP0..GP3 drive V1..V4 through
  R_S1..R_S4, with R_PD1..R_PD4 on the switch side. Reset defaults to
  `0000`/RF1, and explicit `0x08` selects the all-ports-terminated state.
- Power/protection is unchanged: module pin 21 feeds `3V3_MOD -> FB_3V3 -> 3V3`;
  module USB/5V pad 23 remains no-connect; the module owns USB entry and
  regulation; unplugging its only USB-C de-energizes the carrier.
- Population is unchanged: U_MCU remains user-fitted and absent from BOM/CPL/
  paste; all ten SMA jacks remain declared JLC plug-in placements.

## Findings

| Finding | Severity | Evidence | Disposition |
|---|---|---|---|
| RB-TOP-001 — The fence repair is topology-neutral and closes its measured layout subject. | CLOSED; no P0/P1 topology defect | Semantic board diff is identical except for the two added GND vias; shared fence gate passes all 22 arm-sides with 1.1769 mm worst gap against 1.191 mm. | Accept the targeted rebind. No schematic, BOM, firmware, or connector change is required. |
| RB-TOP-002 — Vendor/order qualifications remain open despite clear catalog stock. | P1 order blocker; not a design or sourcing blocker | Stock is PASS 11/11. The build still requires written JLC plug-in acceptance for ten SMA jacks, POFV acceptance for the authored filled/capped via set and ten U_SW via-in-pad sites, the exact 1.2-mm advanced-via stack, controlled-impedance production plots/coupon, and uploader BOM/polarity confirmation. | Do not pay/order until the ORDER_README gates are discharged. A vendor-requested geometry or population change requires revised production artifacts and a new seal. |
| RB-TOP-003 — Physical integration remains a first-article qualification. | P1 bring-up blocker; not a frozen-design defect | RP2040-Zero is intentionally user-fitted above carrier-facing module components. Actual USB operation, supported-envelope current/temperature, free-running cadence drift, and RF loss/isolation/phase remain hardware measurements. | Complete module metrology/fixture/joint inspection, USB/firmware tests, rail and thermal measurements, cadence characterization, and VNA acceptance before hardware acceptance. Preserve the explicit non-claim of phase-locked Pluto sample boundaries without a shared clock/trigger. |
| RB-TOP-004 — Current release-level evidence files predate the repaired exact board. | P1 seal/order blocker; not an electrical defect | `06_build/layout_seal.json` still binds board SHA-256 `dbbb3fce...`, not `4828a4a0...`; the current `policy_audit.md` also predates the repair and reports the candidate-era A-POP/MANIFEST failure. | Regenerate the exact-artifact layout seal, policy audit, staged MANIFEST, and final release battery. Do not copy the stale files into the release. |

## Severity summary

- P0: 0
- P1 topology/design defects: 0
- P1 order/bring-up/release qualifications: 3
- New P2 findings: 0

The two added GND vias and shared fence gate do not invalidate the earlier
topology reasoning; the fresh compact battery binds the `SOUND` verdict to the
new commit, board hash, and fabrication archive above.
