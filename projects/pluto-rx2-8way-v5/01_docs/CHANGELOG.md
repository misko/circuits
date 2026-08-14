# Changelog

One entry per REVISION (a design state, git-tagged). Reverse-chronological.
`Released:` is `no`, or the name of the `07_releases/` directory that shipped it
— it is the only link between a revision and a fab order.

Most revisions never ship. That is normal: a board can go v4.4 → v4.10 in a
day and fab exactly one of them.

## v0.0 — 2026-08-13  [untagged checkpoint]
- Accepted D13 and backtracked before routing: replaced five loose SWD pads
  with exact keyed Samtec FTSH-105-01-L-DV-K-P-TR / JLC C2932107 header J11,
  using the standard Cortex/MIPI10 target pinout and preserving target-only
  USB-C power.
- Rechecked the suspicious SMA render against the exact Amphenol drawing. The
  five-hole copper and all nine edge anchors were correct; replacing only the
  misregistered converted WRL with its native STEP restores correct body-to-
  hole alignment in render evidence.
- Accepted the clean-room one-of-eight SP8T, autonomous dwell controller and
  independent power-only USB-C architectures.
- Selected 13 exact BOM codes and closed their source, package, pin, power,
  protection and JLC evidence before schematic generation.
- Replaced the initial slow timing with generated `fast20-v1`: unique
  20–50 ms antenna dwells, 5 ms guards, 80 ms marker and a 386 ms cycle.
- Selected direct Raspberry Pi GPIO SWD through the keyed Cortex J11 header as
  the normal profile-update path, retaining ST-LINK compatibility as a
  fallback and prohibiting programmer power into target VTref.
- Generated and hash-bound the clean-room four-page, 29-component schematic;
  manifest/Circuit JSON/KiCad/netlist agree 29/29, 131/131 source pin mappings
  and 32/32 electrical invariants pass, ERC has zero errors, and independent RF
  schematic review passes all four exact-artifact-bound requirements.
- Rejected the first otherwise-green human PDF for incorrect unused-STM32 pin
  function labels, corrected it against DS13866 and regenerated the complete
  checkpoint before signing the topology/readability reviews.
- Rejected a 10-V protected-input capacitor after clamp coordination and
  replaced it with the exact 16-V code.
- Selected the JLC04161H-7628 four-layer basis; exact RF geometry remains
  intentionally pending the official calculator at PCB stage.
- Promoted all nine Amphenol RF 901-143-6RFX female right-angle THT SMA
  connectors from provisional D9 to user-confirmed D12.
- Rejected the stale 901-40129 drawing association before footprint generation;
  retained and hash-bound exact drawing SMA6252A2-3GT50G-50 Rev C plus
  PCN-031726, and corrected the ground-hole requirement from 1.52 to 1.70 mm.
- Solved the JLC04161H-7628 coated CPWG source geometry with JLC's live
  calculator: 0.295-mm width, 0.200-mm ground gap, 49.9719-ohm result; retained
  the exact model inputs and the live-versus-written mask-parameter discrepancy.
- Closed a discovered project-slug versus board-stem mismatch in all three RF
  artifact contracts before advancing the stage.
- Authored exact manufacturer lands for the Amphenol SMA, pSemi QFN and GCT
  USB-C connector, retaining fresh exact-code JLC CAD as an independent
  assembly comparator and explicitly recording every dimensional delta.
- Commissioned a 100 x 100 mm four-layer unrouted placement with nine outward
  right-angle SMAs in the PE42482's cyclic package order, four M3 torque
  points, three fiducials and an exact south-edge power-only USB-C datum.
- Justified the advanced JLC option solely by the nine filled/capped 0.45/0.25
  mm RF-ground vias in U1's exposed pad; ordinary routing does not depend on
  advanced-width traces or small vias.
- Closed the first placement grind before routing: exact-package clearance,
  SMA silk, numeric-to-alphanumeric USB pin identity, keyed J11 pin identity
  and explicit zero critical-pair denominator. Current placement DRC is 0
  violations / 39 expected unrouted items / 0 parity findings; P-OUT, P-CAP,
  P-BODYCLR, P-PADSEP and 127-identity P-PINMAP all pass.
- Rejected the first apparently successful final render because the USB-C
  body was absent under an unresolved headless KiCad model token; vendored and
  hash-bound the exact GCT STEP model, then regenerated the board, gates and
  complete top/oblique/edge evidence before pausing for review.
- Rejected the first SMA visual evidence because a converted JLC WRL body was
  offset from the exact Amphenol five-hole footprint. The native exact-code
  STEP aligns all nine bodies, legs and edge mating datums; J11's exact body is
  also present in the regenerated top/oblique/edge evidence.
- Closed the remaining modeled-placement population gap before routing: pinned
  the eight official KiCad 10.0.4 package-model files used by 17 R/C/U/D/F
  references into project source with upstream licence and SHA-256 provenance,
  regenerated without geometry movement, and promoted complete D14 top,
  oblique and edge renders. The new independent P-MODEL gate passes 29/29 and
  is wired into canonical full and reuse rebuilds with a red fixture.
- Stopped before route preparation when tier preflight exposed a 0.09-mm
  router-clearance setting below the applicable 0.20-mm DRC floor and a
  0.15-mm drill at 1.6-mm thickness above the declared 10:1 PTH aspect limit.
- Corrected those source-known route constraints before copper: every wave now
  inherits 0.20-mm clearance and 0.45/0.20-mm ordinary vias, while the
  legalizer reserves the actual 0.58-mm drill-plus-hole-clearance pocket.
  R-PREFLIGHT is 0 FAIL / 0 WARN and regeneration remains byte-identical at
  board SHA-256 `8429ce851ed4`.
- Accepted D14 and replaced the conservative four-edge 100 x 100 mm ring with
  a 90 x 65 mm open-bottom U: ANT2/ANT1/PLUTO RX/ANT8/ANT7 across the north
  edge, ANT3/ANT4 west and ANT6/ANT5 east. This cuts board area by 41.5% while
  preserving the PE42482 cyclic order and zero proper straight RF-corridor
  crossings.
- Shortened the common straight placement span from 36.501 to 14.502 mm and
  the longest throw span from 46.580 to 35.676 mm. The resulting throw spans
  are 19.983–35.676 mm placement metrics, not routed length or phase claims.
- Regenerated the exact track-free board and moved only F1 by 1 mm after the
  first compact pass exposed a degraded J1 reference-designator ownership
  warning. The final generator reports 29/29 owned silk labels; P-PINMAP,
  P-OUT/P-CAP/P-BODYCLR, P-MODEL, P-PADSEP, P-LAND, placement DRC and
  R-PREFLIGHT all pass.
- Promoted fresh D15 top, oblique and edge renders of board SHA-256
  `3fffbc690051`; all nine exact SMA bodies face outward with visible gaps,
  corner mounting access remains open, and keyed SWD plus power-only USB-C
  remain unobstructed. D15 user approval now binds that exact placement.
- Authored the D16 route contract with five bounded non-RF waves and exact
  deterministic RF geometry. The first 0.41-second preparation correctly
  refused seven naive oblique endpoint approaches that crossed U1/SMA ground
  pads; package-normal and launch-normal corrections pass exact collision
  checks without weakening clearance.
- Prepared derived r0 SHA-256 `d598d305f5d7`: 23 RF segments at 0.295 mm on
  F.Cu, zero RF vias, six short U1 ground-to-exposed-pad links, 32/32 SMD GND
  pads pre-served, and zero quick copper violations. The only 30 non-deferred
  open items are exactly the five declared stochastic control/power waves;
  KRT has not run yet.
- Separated ordinary 5 mm whole-board stitching from the RF-fence contract.
  The final RF fence must follow and be measured against saved RF centrelines
  at <=1.40 mm along-route pitch before RF PCB approval (IMP-080).
- Fixed shared route-prep UUID nondeterminism before route progress existed.
  Two identical v5 preparations are now byte-identical at r0 SHA-256
  `d598d305f5d7`; the new regression exercises keepouts, seed copper and early
  plane rescue (IMP-081).
- Promoted the final five-wave chain at SHA-256 `ddb5b901d9d8`; all five
  no-new-via-in-pad guards pass, P-ROUTEBASE covers 36 footprints / 46
  base-prepared vias / 83 prepared segments, and quick reports zero routed-net
  opens or copper violations.
- Rejected the first post-stitch result rather than accepting 18 DRC findings:
  twelve unused endpoint barrels were dangling and two grid vias violated the
  authored fiducial copper/mask envelopes. Shared site admission now consumes
  pad-local clearance and mask expansion, with a known-bad regression.
- Replaced R3.1's fragile cap-overlap-only join with an assembly-safe source
  via and a strictly via-contained 0.10-mm topology bridge. The bridge and
  dogbone share `(68.80,57.00)` after the unused barrel is removed; the strict
  boundary fixture accepts 0.100 mm and refuses 0.101 mm.
- Replayed import and stitching from the exact promoted source: 32/32 GND SMD
  pads served, 200 ordinary stitch vias, four zones filled, no split islands,
  and clean stitch gate. Final saved-board DRC is 0 violations / 0 opens / 0
  parity findings; rules audit is 20/20.
- Made the existing no-rigid-Pluto, SMA-cable boundary machine-readable.
  D-MATE now grades SMA gender, port order and AD936x RX absolute maximum 3/3
  from their single external-fact home; no Pluto dimension is consumed.
- Pinned the exact post-stitch pause in a 23/23 checkpoint. This is not a fab
  release: the <=1.40-mm route-following 5.9-GHz RF fence and exact RF PCB
  review remain open.
- Completed IMP-080 without moving the approved RF copper. A contract-driven
  route-following emitter added 394 ordinary 0.45/0.20-mm GND vias, including
  22 corner anchors; the independent saved-board checker grades 18/18 flanks
  with worst along-route aperture 1.3979 mm against the 1.4000-mm bound.
- Rejected the apparent greedy-placement local minimum rather than shrinking
  the general via geometry or rerouting RF. The accepted general fix reserves
  constrained bends first and lets one physical plated return serve both
  adjacent finite segments where the saved geometry proves it does.
- Corrected a resumability false failure exposed by the disposable promotion:
  `stitch_grid.min` now grades realized same-net plated returns rather than
  newly-added-via count. The exact rerun emits zero duplicates while measuring
  200/234 declared sites served (IMP-087).
- Regenerated adopted rules after the last board save. The exact fenced board
  SHA-256 is `0b8ab1962ef7`; saved pours are present, rules audit is 20/20, and
  final KiCad DRC remains 0 violations / 0 unconnected / 0 parity findings.
- Refused that otherwise-green exact board during independent final review:
  one unfilled ordinary GND grid via was centred in J11.3's SMD paste land.
  Same-net DRC silence was not accepted as assembly-process approval.
- Moved the correction to shared process boundaries before replay. Ordinary
  stitch emitters now refuse exact SMD-pad hits and V-PROCESS independently
  rejects unprotected via-in-pad or native fill/cap intent with no unambiguous
  assembly selector; regression fixtures reproduce both failure classes.
- Made selective U1 POFV orderable: its nine protected vias are now
  0.45/0.25 mm while all 629 ordinary vias remain 0.45/0.20 mm. The complete
  replay removes exactly the J11 via, keeps RF fence 18/18 at 1.3979 mm worst,
  and finishes DRC 0/0/0 on corrected board SHA-256 `39251c24d4b3`.
- Rejected a final-review assembly-process ambiguity before layout seal. J2-J10
  remain on the CPL under an explicit required JLCPCB through-hole connector
  process; exact C429844 is currently catalogued as a stocked Plugin part, but
  uploader refusal stops this release and requires a separately generated
  hand-solder population contract/CPL. A-POP's nine THT-placeability findings
  are closed; only the expected not-yet-generated release MANIFEST remains.
- Replaced the misleading local `DS13866-Rev4.pdf` (internally Rev 3) with
  correctly named Rev 3 history plus ST's current official DS13866 Rev 5 bytes.
  The current digest is now dossier authority; a focused comparison confirms
  no change to the TSSOP-20 pin map, BOR4, HSI48 or package facts used here.
- Closed `V5-F2-source-document-lifecycle` in the authoritative findings
  ledger with the Rev 5 digest and focused comparison evidence; the project no
  longer contradicts its own current source-document state.
- Corrected J11's dossier `mates:` field from a cable-family name to the
  schema's physical role `plug`; the keyed FFSD receptacle relationship remains
  explicit in the part note. This source-only correction makes P-ESC 13/13.
- Renewed all six exact-final review lenses against source commit `4cf5c818`
  and unchanged board SHA-256 `39251c24d4b3`; every lens is SOUND with zero
  P0/P1/P2 layout findings. The remaining findings are fabrication, order,
  firmware and first-article controls rather than layout defects.
- Minted the reviewed-commit layout seal after the full gate replay: DRC
  0/0/0, P-ESC 13/13, P-LAND 62/62, P-PADSEP pass, RF reviews 9/9 and via
  process 638/638. This seal covers PCB layout only and is not a fab release.
- Recorded a provenance-discovery defect after ignored tsCircuit cache bytes
  blocked the first seal attempt. Relocating the ignored cache restored the
  correct source set without a design change; IMP-092 carries the general fix.
- Entered fabrication with a strict rather than permissive export. The first
  run stopped before writing uploadable BOM/CPL data because six exact LCSC
  rotation rows were missing; independent pad and marking measurements now
  cover C2866134, C2932107, C429844, C5184243, C5452432 and C83270, and the
  complete 99-row authority passes M-PROV/A-POL.
- Generated the first exact JLC package from unchanged board SHA-256
  `39251c24d4b3`: 11 Gerber layers plus separate PTH/NPTH drills, 13 coded BOM
  lines and 29 top-side CPL placements. BOM source/legibility, 13/13 live stock,
  archive integrity, four-layer pour census, A-POP/A-POS, selective via process
  and 18/18 RF fence gates pass.
- Resolved the final exact-code JLC twin without weakening global tolerances.
  All 29 fitted bodies mount; a pixel-independent overlay grades 14/14
  resolvable bodies within 1.00 mm and names the 15 sub-resolution/occluded
  bodies. Evidence-bound adjudications retain Amphenol and Samtec manufacturer
  lands over conflicting generic catalog CAD and retain Littelfuse's compliant
  SMB pad dimensions; every order-preview and DFM obligation remains explicit.
- Corrected the RF fabrication artifact contract from a hand-typed hyphenated
  ZIP name to the strict exporter's actual underscore name before dispatching
  the exact-Gerber review. IMP-093 and IMP-094 record the repeated-pad matcher
  and generated-artifact-index improvements exposed by this stage.
Released: no
