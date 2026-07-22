# Journal — usb-hub-3s-v2 board backend (placement/route)

## 2026-07-22 — start (schematic gate → board backend)
- did: Resumed from schematic-gate handoff. Audited the netlist for the hand-written
  KiCad backend and found TWO source defects that blocked/would-corrupt the board:
  1. **9 specialty parts had EMPTY footprints** (C1/C2 polymer, L1/L2 inductor,
     RS1/RS2/RS3 shunt, F1 fuse holder, U1 TPS25740A) — v2's 02_parts/*/part.yaml
     lacked `footprint:` fields (v1's carried them) and 3 part folders did not exist.
     FIX: added `footprint:` to TPS25740ARGER (Texas_RGE0024H_VQFN-24 EP2.7x2.7 ThermalVias)
     + lcsc:C5249699 to 3568; copied v1's proven part.yaml for the shunt(2512)/
     polymer(CP_Elec_6.3x7.7)/inductor(L_Sunlord_MWSA1206S-6R8) folders; copied v1's
     usb_hub_3s.pretty custom-footprint lib into 03_src/lib.
  2. **Layout-mode net merge: BOOT_A absorbed VCC_A** — the converter's default
     `--mode layout` merged buck-A's BOOT_A and VCC_A by wire-endpoint coincidence,
     SHORTING boot diode D3 (both pads on one net) and tying VCC=BOOT. Buck C was
     correct (identical tsx) — a stochastic geometry coincidence, the exact hazard
     v1 avoided with `--mode grid`. FIX: regenerated the converter .kicad_sch with
     `--mode grid` (label-glue, parity-safe by construction).
- result: MEASURED — 112/112 footprints resolved; BOOT_A={C7.1,D3.1,U2.18} and
  VCC_A={C8.1,D3.2,U2.16} now SEPARATE (D3 un-shorted); ERC 0 errors; count_parity
  112==112==112. Schematic gate GREEN and now electrically correct.
- next: This board REQUIRES `--mode grid` (gen_tscircuit.sh defaults to layout and
  re-introduces the merge). Author 03_src/floorplan.yaml (4 self-contained cells),
  generate_rules, route.yaml, grind to DRC 0/0/0.

## 2026-07-22 — placement finish
- did: Authored 03_src/floorplan.yaml (power-hub archetype, 4 self-contained cells
  on a 130x92 4-layer board: In1=GND, In2=VIN). Reused v1's proven LM5116 buck
  geometry TWICE (buck A north, buck C south, identical), v1's USB-A bank shape
  (east column, mouths east), fresh simple PD cell (TPS25740A + back-to-back path
  FETs, no switching). Wrote 03_src/audit_board.py (I-POL/I-PROX/I-EDGE/I-SILK).
  Relocated the two east mounting holes off the 18mm-tall connector column into
  clear board; nudged D1/D2/U12/RS3 out of bbox collisions.
- result: MEASURED — generate_board_generic: 112 placed (37 anchored), 26/26
  orientation asserts PASS, 38 legalized. audit_board: PASS (20 polarity, 21
  proximity, 4 edge, 116 silk). bbox overlaps >0.4mm^2: 0.
- next: generate_rules (netclasses/DRU, advanced tier) BEFORE route-prep; author
  route.yaml; KRT fanout-first; grind to DRC 0/0/0.

## 2026-07-22 — routing WIP checkpoint (planned handoff, context budget)
- did: Built the KiCad backend end-to-end and drove the DRC grind. Wrote
  03_src/{generate uses generate_board_generic}, floorplan.yaml, route.yaml,
  audit_board.py, rebuild_all.sh; added the PD_NET netclass to rules/nets.yaml;
  promoted the KRT chain to 03_src/route/final_chain.kicad_pcb (canon M3).
  Pipeline: generate_board -> audit(PASS) -> generate_rules -> prep -> route
  (KRT, 50 signal nets) -> import -> taps (28 deterministic taps) -> stitch
  (pours+pad_rescue+fill) -> generate_rules LAST -> DRC.
- result (MEASURED): full DRC gate `kicad-cli pcb drc --severity-all
  --refill-zones --schematic-parity` = **28 violations / 21 unconnected / 0
  parity**. Trajectory this session: 69/32 -> 42/30 -> 44/23 -> 28/21.
  Placement GREEN (audit: 20 pol/21 prox/4 edge/116 silk, 0 courtyard except the
  1 below). ALL 50 signal nets routed; all power poured; buck A/C + input +
  USB-A + DCP cells fully clean.
- REMAINING 28 violations:
  * silk_over_copper (17) + silk_overlap (2): refdes/caption silk clipped over
    pads. Cosmetic; needs a silk de-collision tune (raise `silk.refdes.clearance`
    or shrink text, or move captions off dense pad fields). Non-electrical.
  * track_dangling (8): the pour-connection TAP tracks end at a POINT that the
    filled pour doesn't quite bond -> free end flags. Fix: retarget each such tap
    to a same-net PAD inside the pour (not a bare point), or extend the pour to
    cover the tap endpoint, or add a stitch via at the endpoint.
  * courtyards_overlap (1): U12 (rot180 @126,103) vs J5 — nudge U12 ~1.5mm NE
    (watch the DPC/DMC taps that depend on U12 pin positions).
- REMAINING 21 unconnected (pour-bond opens — pad sits outside its filled pour
  OR the tap track didn't bond): 5VC(C31.1,RS3.1,C44.1,U1.20), 5VA(C34.1),
  VBUSA(C38/C39/C40.1), VBUSC(U1.21), RSNS(Q6.5,U1.19), CS(R9.1,R18.1),
  DPC/DMC(J5.A6/B6/B7,U12.6), PDSRC(U1.23). Most are the tap-endpoint-not-bonded
  class above (same fix). Two are STRUCTURAL:
  * **PDSRC U1.23** and the TPS25740A QFN north-edge sense pins (19 RSNS / 20
    5VC / 21 VBUSC / 23 PDSRC) are the KEY remaining challenge. All 6 north pins
    (0.5mm pitch) must escape to islands, but the FET row (Q6/Q7) sits directly
    north and the island net-order does NOT match the pin order -> pins get
    boxed. U1.21 uses a pad_rescue B.Cu-bridge drop (partial); U1.23 is west of
    Q6 while the PDSRC island is east of Q6 (cannot cross the FET) -> its tap is
    commented out. This is a PLACEMENT/ESCAPE problem (D-BACK -> placement),
    NOT a router tweak.
- NEXT STEP (routing-gate work order for the successor):
  1. **PD-cell escape re-design (highest leverage).** Options: (a) rotate U1 so
     its north power/sense pins face an OPEN side with a via-in-pad fan-out
     (advanced tier allows via-in-pad — the whole reason for the tier); (b)
     spread the FET row so a clear escape channel sits directly north of each
     sense pin; (c) give each of pins 19/20/21/23 its own via-in-pad drop to a
     dedicated short B.Cu finger (non-overlapping — they are 0.5mm apart, so
     alternate F.Cu/B.Cu). Re-add the PDSRC U1.23 tap once reachable.
  2. **Tap-endpoint bonding:** retarget the ~10 pour-connection taps
     (5VA/5VC/VBUSA/CS/RSNS) from bare points to same-net PADS inside the pour,
     or extend the pours to swallow the endpoints. Clears most of the 21
     unconnected + the 8 track_dangling together.
  3. **Silk:** tune silk de-collision to clear the 19 silk findings.
  4. Nudge U12 to clear the J5 courtyard.
  Then DRC 0/0/0 -> commit routing gate -> verification stage.
- OPEN HYPOTHESES: the board is intrinsically ~90% clean; the residual is
  concentrated ENTIRELY in the TPS25740A/USB-C corner (the advanced-tier cell)
  and mechanical pour-bond/silk cleanup. v2's "no shared hot loop" win held —
  buck A, buck C, input, and all 3 USB-A ports routed without congestion.

## 2026-07-22 — D-BACK decision + sourcing disposition (Opus-tier call)
- SOURCING (human-escalation, user decided): proceed with TPS25740A (NRND,
  single-source, alternates: []) FOR NOW. Risk ACCEPTED by user. Order-day
  LCSC C544309 stock recheck stays MANDATORY; IP2726 is the backup-if-forced
  (thin stock) — qualify only if TPS25740A goes unavailable at order time.
- ROUTING WALL (geometry, machine-decided — NOT escalated to user): the
  TPS25740A north-edge sense pins boxed. Root cause = D-ADJ placement, not a
  router/via trick. Pins 19-23 are already in current-flow order
  (ISNS-VPWR-VBUS-GDNG-GDNS); the cell was placed out of order and Q6 sits
  across the PDSRC path. DECISION:
  1. Re-place PD cell to PIN ORDER: Rs straddling pins 19/20 at the package
     edge; FLIP/ROTATE Q6 so its SOURCE (PDSRC) faces pin 23 (drain toward
     connector) — un-boxes U1.23 with no FET crossing; VBUS divider at pin 21;
     fine-pin side faces the open escape corridor.
  2. Via-in-pad ring escape for the north pins = the legitimate use of the
     advanced tier (not a crutch for mis-placed parts).
  3. THEN cheap-tier cleanup: tap-endpoint bonding, silk de-collision, U12 nudge.
  Target: DRC 0/0/0 -> verification -> red-team -> seal.

## 2026-07-22 — routing grind (28/21 -> 1/4) + PD-escape wall (Opus-tier)
- FIRST, restored REPRODUCIBILITY: the committed 28/21 board was NOT regenerable —
  the promoted final_chain.kicad_pcb was a STALE KRT result that still contained
  DPC/DMC/CC tracks the current route.yaml assigns to deterministic taps, so import
  doubled them (DPC shorted to U12.2). Re-ran KRT config-consistent, re-promoted,
  added `route.final` + `03_src/rebuild_fast.sh` (import promoted chain -> taps ->
  stitch -> DRC, ~48s deterministic; no stochastic re-route unless a signal pin
  moves). Fresh reproducible base = 33/20.
- SYSTEMIC TAP BUG (root cause of most opens): a tap with `layer: B.Cu` FROM an
  F.Cu pad -> joinpath strategy-1 drew a B.Cu track at the pad XY that NEVER
  via-bonded the F.Cu pad (dangling free end + pad shows unconnected). FIX: the
  stub `layer` MUST be the pad's own layer so via_hop drops a via-in-pad AT the
  pad; `hop_layer` carries the run. Flipped RSNS/5VC(U1.20)/DPC/DMC-J5 taps ->
  those pins bonded. Also: `joinpath` silently falls back to 0.2mm when the asked
  width collides (SWITCH_NODE min 0.6) -> retargeted C7.2/C22.2 boot-SW taps to a
  clear interior island point. Sense taps [90,40]/[90,74] landed INSIDE the SW_A/
  SW_C islands (net-conflict dangling vias) -> moved to clean 5VA/5VC. Extended
  5VA/5VC/CS_A/CS_C pours to swallow legalized pads; added TPS2557 OUT->VBUSAn
  taps; bonded the C44/U1.20 5VC island; nudged U12 north 1.3mm (J5 courtyard);
  relocated 2 captions off J1/F1 silk.
- PD RE-PLACE (executed the D-BACK call, adapted): moved the FET row RS3/Q6/Q7
  +3mm NORTH (y91->y88) to widen the U1-north escape channel 2mm->5mm; islands
  followed; removed the dead B.Cu VBUSC bridge; re-routed KRT + re-promoted. This
  cleanly fixed RSNS(19) + 5VC(20) (they escape WEST on B.Cu).
- RESULT (MEASURED, reproducible via rebuild_fast.sh): **DRC 1/4/0**
  (was 28/21/0). 1 violation = a B.Cu copper_sliver (severity warning). 4
  unconnected, ALL in the TPS25740A north corner:
    * U1.21 VBUSC (pad -> zone)   — boxed north pin, EAST-going
    * U1.23 PDSRC (pad -> zone)   — boxed north pin, EAST-going
    * VBUSC zone(107,103 J5-west) -> zone(122.3 J5-east)  — pour split
    * PDSRC zone -> zone          — island split by the PDGATE F.Cu track
- THE WALL (why U1.21/U1.23 still won't route, precisely): U1 (VQFN-24, 0.5mm
  pitch) has SIX north-edge pins that all interface the FET row — 19 RSNS, 20 5VC,
  21 VBUSC, 22 GDNG, 23 PDSRC, 24 DSCG_N. Their nets are cross-ordered vs the
  FET-row copper: the FET-row chain (5VC-RS3-RSNS-Q6-PDSRC-Q7-VBUSC) is monotonic
  W->E, but the package puts the EAST-going nets (VBUSC/PDSRC) on the WEST pins
  (21@110.25, 23@109.25) and the WEST-going nets (RSNS/5VC) on the EAST pins
  (19@111.25, 20@110.75). Two escapes must cross. Widening the channel let RSNS/
  5VC out (B.Cu west) but NOT VBUSC/PDSRC because (a) KRT fills the F.Cu channel
  with GDNG/DSCG_N/PDGATE (pins 22/24 + FET gate) BEFORE the taps run, leaving no
  F.Cu lane east; (b) a via-in-pad at pin 21 or 23 COLLIDES with the adjacent
  pin's via at 0.5mm pitch (0.25 via + 0.13 clr needs 0.38mm center gap; pitch is
  0.50, but the neighbor via already occupies it). Verified: the tap router A*
  FAILS both U1.21->VBUSC and U1.23->PDSRC on the widened board. This is NOT a tap
  or pour tweak — it is intrinsic to routing 6 same-edge 0.5mm pins where 3 are
  KRT-claimed and 2 are cross-ordered.
- RECOMMENDED NEXT MOVE (for the successor, in preference order):
  1. STAGGERED via-in-pad dogbone on the 6 north pins: drop each pin to B.Cu with
     the via pushed alternately N/inward (2 rows) so adjacent vias clear 0.5mm
     pitch, then fan on B.Cu with the FETs no longer overhead (they are at y88
     now, so B.Cu y92-96 is clear). The tap `via_hop` cannot stagger; this needs a
     dedicated dogbone-fanout emitter (promote to stitch.seed_stubs or a new
     generic pass) — the "via-in-pad RING" the D-BACK note called for.
  2. Force GDNG + DSCG_N onto B.Cu (or reroute their targets R25/R26) so the F.Cu
     channel frees for straight-N F.Cu stubs from pins 21/23 into PDSRC/VBUSC
     channel fingers (fingers were prototyped, see git history of floorplan.yaml).
  3. Failing both, evaluate the IP2726 alternate (the sourcing backup) — a
     different PD-controller pinout may not cross-order the FET-row pins.
- Also still open (mechanical, not the wall): the copper_sliver (B.Cu), the VBUSC
  J5 west/east pour split, and the PDGATE-split PDSRC island — all in the same PD
  corner; a successor solving the pin escape will rework this copper anyway.
- STATE: committed d648337 (1/4/0), fully reproducible from 03_src. NOT sealed —
  verification/red-team/seal is a separate zero-context stage.
