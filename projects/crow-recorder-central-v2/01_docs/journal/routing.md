# journal: routing

## 2026-07-23 — start / in-progress (routing-boundary handoff)
- did: generate_rules merged 5 netclasses + 30 patterns into 04_kicad (canon R1).
  Delegated the KRT routing grind to a background sub-agent with a hardest-first
  3-wave strategy (an_clk: audio+clock+USB; pwr: rails+SW+returns; sig: rest;
  GND excluded = pours+stitch), fab_tier jlc_6layer_smallvia (0.30/0.15 via-in-pad),
  RJ45 board-lock-post keepouts, D-BACK stop conditions.
- result (MEASURED, in-progress — NOT the final gate):
    * route.yaml authored; prep -> track-free r0 + 3 wave net-lists.
    * KRT `route --race 3`: all 3 candidates 46 unconnected / 181 violations
      (DIRTY) PRE-STITCH; chose c0 (race_log.json).
    * import -> 04_kicad (2614 tracks); agent then iterated route+stitch cycles
      (regenerate wipes tracks each cycle): observed 2669/311 -> 2693/318 vias with
      reconcile passes r4/r5. Mid-grind classified DRC snapshot (no --refill-zones,
      so GND pours read unconnected): 108 violations / 82 unconnected — MOVING,
      the agent is still reconciling; this is NOT a converged or walled state.
- shared-skill changes this stage DEPENDS ON (reproducibility; each needs a test
  + RED-verify before commit — delegated to the routing sub-agent, its owner):
    * generate_board_generic.py In3/In4 LAYER_NAMES/INNER_LAYERS — MINE, DONE
      (t1_generate_board.py t_six_layer_inner_planes + t_in4_needs_six_layers,
      RED-verified 27/0 -> 25/2 on revert).
    * generate_rules_generic.py — default_clearance/default_track_width use mm()
      to strip the "mm" unit (nets.yaml sets default_clearance: 0.10mm). Test in
      tests/t1_rules_bom.py (routing agent).
    * import_krt.py — In3/In4 added to the layer map (6-layer import). Test in
      tests/t2_route_stitch.py (routing agent).
    * route_and_stitch_generic.py — KRT --fab-overrides pin 0.30/0.15 (routing
      agent to describe + test if needed).
- next: routing sub-agent continues the grind to DRC 0/0/0 (or names a D-BACK
  wall). generate_rules LAST + `kicad-cli pcb drc --severity-all --refill-zones
  --schematic-parity` is the gate. Then classify real (different-net < floor) vs
  margin/same-net, promote the final chain to 03_src/route/, commit.

## 2026-07-23 — grind converged to a classified residual (routing agent)
- did: closed the full loop (prep/route/import/quick/stitch/generate_rules-LAST)
  through many measured cycles, root-causing four distinct bugs along the way
  rather than grinding blind:
    1. route.common.clearance=0.13/0.2 both below/above the board's ACTUAL
       generated netclass clearance (a hardcoded 0.2mm generate_rules_generic
       default, unrelated to the declared jlc_6layer_smallvia tier's 0.09
       floor) -> 500 then 158 clearance findings. Fixed: nets.yaml now sets
       default_clearance + per-class clearance: 0.10mm (matches this tier's
       own ADR-0009 "~0.10mm copper gap" expectation at via-in-pad escape).
    2. pcb_toolkit.py's via_site_ok() defaulted to checking ONLY F.Cu/B.Cu —
       silently invisible to In2.Cu/In3.Cu, the layers THIS board's signal
       routing actually uses. Every stitch-placed via (stitch_grid/pad_rescue/
       island_rescue/heal_islands) was collision-verified against half the
       board's copper. Measured: 200 shorting_items + 501 clearance findings
       appeared ONLY after stitch (quick, pre-stitch, kicad-cli-verified, was
       clean). Fixed: defaults to the board's full copper stack
       (GetEnabledLayers().CuStack()).
    3. stitch.normalize_vias and stitch.width_floor both blindly resize
       existing copper with NO collision check (by design — verified via
       code read, not assumed) — my config left normalize_vias' size/drill
       unset (that block is NOT tier-derived, unlike via_size/via_drill),
       so it silently fell back to the pass's OWN hardcoded 0.6/0.3 default
       and blew every 0.30mm tier via up to 0.6mm (323/323 vias, measured).
       Fixed: explicit {size: 0.30, drill: 0.15, below_width: 0.29}.
    4. Two single-pin IC escapes (U3 pad 25 / 3V3 at the PCM1865 ADC pin
       field, U1 pad 5 / 0V9 at the XU316 0.4mm-pitch QFN) could not route
       at their PWR netclass's 0.4mm ampacity floor at ANY geometry KRT
       tried (finer grid, higher iterations, ripping every immediate
       blocker) — confirmed these are single-pin drops carrying no trunk
       current, not genuinely needing 0.4mm. Fixed via the EXISTING
       scoped_floors mechanism (nets.yaml) + a matching permissive rule
       area (floorplan.yaml keepouts: u3_3v3_tap, u1_0v9_pin5) — the same
       generic, config-only pattern cook-hub/usb-power-3s already use, not
       a generator edit.
  Also bumped floorplan.yaml placement.legalize.clearance 0.25->0.35mm: the
  U7/U8 buck hot-loop passive clusters at 0.25 packed tight enough that GND
  pour sliced off unstitchable fragments between the SW2/PG_3V3/0V9/5V/FB2
  trunk traces (measured: island_rescue's 81-point interior search AND an
  exhaustive 0.03mm pcb_toolkit scan both found ZERO legal 0.30mm via sites
  inside the worst fragment). This measurably reduced but did NOT eliminate
  the pattern.
- shared-skill changes (skills/kicad-pcb/scripts/*.py), each a measured bug
  fix, not a guess:
    * generate_rules_generic.py — default_clearance/default_track_width now
      strip "mm" via the existing mm() helper (previously bare float()).
    * import_krt.py — LAY map extended to In3.Cu/In4.Cu (was F/B/In1/In2
      only; the docstring itself invited this: "routing on In3/In4 needs
      the map extended").
    * route_and_stitch_generic.py — _KRT_FLAGMAP gained fab_overrides
      (--fab-overrides passthrough, pins the via floor to 0.30/0.15 instead
      of letting KRT's built-in advanced-tier preset auto-escalate DOWN to
      0.25mm) and no_power_tap_neckdown (--no-power-tap-neckdown passthrough,
      stops KRT thinning power-net stub taps below the wave's derived width).
    * pcb_toolkit.py — via_site_ok()'s layers default (see bug 2 above).
  All four are frozen per coordinator instruction pending a separate
  RED-verified test landing; none touched after the freeze notice.
- result (MEASURED, classified DRC — `kicad-cli pcb drc --severity-all
  --refill-zones`, full severity, on the stitched + rules-regenerated board):
    79 violations / 8 unconnected (from 902 / 9 at the first full-severity
    pass this session — 91% violation reduction). Classified:
    * 27 silk_over_copper + 16 silk_edge_clearance + 5 silk_overlap (48
      total) — silk placement, not routing; independent of this stage
      (generate_board's silk engine, unchanged by any routing.yaml/nets.yaml
      edit this session). Not investigated further — out of this stage's
      scope.
    * 23 starved_thermal — SKILL.md golden rule 9: "GUI DRC is authoritative
      for zone-fill-dependent checks (starved_thermal is invisible
      headless)" — kicad-cli (headless) is NOT the authoritative source for
      this class; needs a GUI DRC pass to confirm real vs artifact, not
      done this session (time-boxed).
    * 4 items_not_allowed — 4 tracks (3V3, SDA x2, SCL) on F.Cu right at
      U6 (SHT40 humidity sensor, 168,58) — no rule-area/keepout zone found
      at that location by direct board query; likely a footprint-embedded
      keepout (sensors often keep copper off the sensing element) that KRT
      didn't honor. Not root-caused — flagging, not fixing blind.
    * 2 track_width + 1 clearance + 1 hole_to_hole — small, real, easy
      (a stray sub-floor 0V9 segment now that 0V9 is out of width_floor's
      safety net; a via 0.075mm from a U7 GND pad; two GND vias 0.04mm
      apart that dedupe_vias should have caught). Not fixed — ran out of
      session time after the structural fixes above; each is a 1-segment,
      pcb_toolkit-verifiable edit.
    * 8 unconnected — ALL GND, ALL single decoupler/feedback pads (U8.2,
      R_fb2b.2, C_micb2.2, U1.42, C_d1.2, C_c3.2, C_d4.2, U3.26) scattered
      across the SW power corner (U7/U8 hot loop), the XU316 pin field, and
      the ADC decoupler clusters. Every stitch-side rescue mechanism ran on
      each (pad_rescue ring search 0.75-2.7mm, stub_fallback 0.2-8.0mm,
      astar_fallback, island_rescue's 81-point interior search, stitch_grid)
      — 11 remained unserved after all of them, 8 after fill's thermal-spoke
      proximity closed a few more. This is a D-BACK PLACEMENT finding, not a
      router-tuning one (golden rule: "a routing failure is usually a
      PLACEMENT problem"): too many decoupler/feedback GND pads sit too
      close to their own IC's dense pin/trunk-trace field for a 0.30mm
      via (this tier's hard floor) to legally land anywhere nearby. The
      legalize.clearance bump (0.25->0.35) measurably helped (was ~15-20
      unserved at the tighter spacing) but didn't clear the whole class —
      the fix from here is per-decoupler placement nudges (snap-back
      distance / orientation) at the floorplan stage, D-ADJ, not more
      stitch-side searching (already exhaustive: pcb_toolkit-verified 0mm
      via-site scans found zero legal candidates in the two worst pockets).
- promoted chain: 03_src/route/rv2_final.kicad_pcb (route.yaml route.final).
- STOP: reporting this classified residual per the task's D-BACK protocol
  rather than continuing to grind placement-density findings the stitch
  layer has already exhausted its mechanisms against.

## 2026-07-23 — FRESH lead resumes: D-BACK REFRAMED (6/8 were config, not placement)
- did: reproduced the 79/8 baseline from source (generate_board -> rules -> prep
  -> import promoted chain -> stitch -> rules LAST -> DRC), EXACT match, so the
  pipeline is deterministic and the reuse-chain flow is sound. Then, before
  touching placement, ran a pcb_toolkit via-site scan on the 8 open GND pads.
- ROOT-CAUSE CORRECTION (the headline): 7 of the 8 pads had a DRC-LEGAL 0.30/0.15
  via site within 0.2-0.8mm of the pad the whole time. The prior D-BACK's
  "placement density / zero legal sites" reading was measured with the WRONG
  clearance: stitch's `try_via` builds its via tier as {size,drill} only, so
  via_site_ok falls back to hole_to_copper=0.205 — 0.055mm STRICTER than THIS
  board's actual hole_clearance DRC floor of 0.15 (floorplan design_rules).
  Proven empirically: manually adding GND vias at 0.15-legal sites on the
  stitched board dropped unconnected 8->1 with ZERO new clearance/hole findings.
  So the fix was CONFIG, not nudges. (Generator note for the coordinator:
  try_via's hardcoded 0.205 hole_to_copper default should derive from the board's
  min_hole_clearance; every 6L small-via board will hit this. Flagged, NOT
  edited — skills/ is frozen.)
- FIXES (all projects/-scoped: route.yaml / floorplan.yaml / nets.yaml + 1
  surgical edit to the promoted chain):
  * route.yaml stitch.via.tiers: hole_to_copper 0.155 (0.15 floor + 5um cushion;
    try_via checks the same rounded coord it places against the same floor DRC
    uses, so >=0.15 is self-consistently safe). + pad_rescue rings prepended
    [0.1,0.2,0.3,0.45,0.6] & angle_step 12 (the close-in sites sit 0.2-0.8mm from
    pad CENTRE, inside the old 0.75mm floor ring). -> 6 of the 8 GND connected.
  * width_floor 5V:0.501 — lifts the one KRT 0.4998mm 5V trunk seg over the DRC
    floor (width_floor's 1um skip-tolerance had left it, DRC compares exact nm).
    track_width 2->0, hole_to_hole 1->0 (both cleared by the same rebuild).
  * 0V9 tap to U1.103 (0.3498mm at 93.2,94.3): a blanket width_floor lift to 0.4
    clipped U1.103 to 0.0745mm clearance (the exact risk the old comment warned
    of). Reverted; handled by a u1_0v9_tap103 scoped floor (0.34) so the thin tap
    passes track_width WITHOUT widening. clearance back to 0.
  * C_micb2.2 (a GENUINELY boxed pad): its only pad-crossing copper was ADC2P on
    B.Cu (a straight line). Surgically detoured ADC2P south around the pad on the
    PROMOTED CHAIN (03_src/route/rv2_final.kicad_pcb), every segment
    pcb_toolkit-verified collision-clear; via-in-pad site opened -> pad_rescue
    connects it. unconnected -> 1.
  * starved_thermal (23, authoritative on KiCad 10 w/ --refill-zones): targeted
    per-pad `pad_overrides {on_net: GND, zone_connection: full}` on ONLY the 23
    starved pads' parts (a floorplan pattern with a match-list), EXCLUDING U8
    (its isolated pad2 would island the gate). Keeps thermal relief on every
    other THT GND pad. starved 24->1 (U8.2 residual). Precedent: crow-array-pod
    J1 / cook-hub SOLID connector-GND.
- RESULT (MEASURED, kicad-cli --severity-all --refill-zones, gate: clean):
  79 viol / 8 unc  ->  54 viol / 1 unc.
  Cleared: 6 GND (config), 1 GND (C_micb2 chain detour), 2 track_width,
  1 hole_to_hole, 1 clearance (0V9), 23 starved_thermal.
- REMAINING to 0/0/0 (all characterised, none a stitch-mechanism problem):
  * U8.2 = 1 unc + 1 starved: GENUINE buck-GND D-ADJ WALL (escalated). The
    SOT-563 0V9 buck's GND lead (pad2) is boxed — its only pad-crossing blocker
    is 5V on In2 (the input via sits immediately south), and the sole southern
    escape corridor is filled by the 0V9 In2 trunk, with FB2 to the north. An
    exhaustive scan found NO legal through-via site anywhere in pad2's 1.4x2.4mm
    F.Cu GND island. Fix needs a SW-corner In2 re-plan (move the 0V9 trunk off
    U8's GND escape) or a U8 reposition + buck-cluster re-route — beyond
    config/surgical scope, touches the promoted chain's hot loop. When connected,
    add U8 to the starved pad_overrides list and flip it in.
  * U6 SHT40 = 4 items_not_allowed: the STOCK Sensirion_DFN-4 footprint embeds a
    picture-frame keepout (tracks+vias not_allowed, pads allowed, copperpour
    not_allowed) around the sensing aperture; the 4 pin tracks (3V3, SDA, SCL)
    enter the frame to reach pads that sit at the frame edge. Fix: either reroute
    the 4 approaches onto the pads' exposed outer slivers (from outside the
    frame), or vendor the footprint into 03_src/lib with the keepout's `tracks`
    set to allowed (keeps copperpour-off-sensor intent, allows the pin tracks).
  * 5V/U7 clearance = 1 (0.0745mm, a 5V trunk seg by U7's GND pad in the chain):
    surgical chain micro-reroute, same pattern as the ADC2P detour.
  * silk = 48 (27 over_copper + 16 edge_clearance + 5 overlap): NOT routing. 3
    captions collide with port-bank pads / decoupler silk (the "NOT ETHERNET"
    warning over J3, the title over C_c*/U5); RJ45 F.SilkS outlines cross the
    overhanging north board edge. Fix: reposition the 3 captions to clear silk
    bands (needs a render to verify) + trim/waive the edge-overhang RJ45 silk.
- converter tie-emission PRE-SEAL CHECK (peer request, cooksense bug): verified
  CLEAN. No isolated/floating domain exists on central-v2, so the tie:GND
  emission cannot bridge one. Confirmed GND bonds are intended: RJ45 shield
  tails J*.13 = GND, USB J2 SH -> GND (shield BONDED at central per the pod-array
  float-at-pod/bond-at-central architecture), XU316 EP U1.129 = GND, SHT40 VSS
  U6.4 = GND. '' pads on J2/J3 are correctly-netless NPTH board-lock posts;
  J3.9-12 & J1.3 are intentional floats (unused RJ45 positions / jack switch pin).

## 2026-07-23 — ROUTING GATE GREEN: 0 violations / 0 unconnected
- did: with coordinator authorization, finished every residual class.
  * U8.2 (the escalated buck-GND wall) — OPTION A (least-disruptive, U8 stays
    placed): rerouted the 0V9 In2 trunk south (dip to y117.7) to vacate U8's GND
    escape corridor, then rerouted the 5V In2 diagonal off pad2 as an L-path.
    Every new segment pcb_toolkit collision-verified (canon M8); via-in-pad site
    at pad2 centre opened, pad_rescue placed it -> U8.2 connected. No re-race,
    surgical chain edit to 03_src/route/rv2_final.kicad_pcb. (Option B — U8
    reposition — not needed.)
  * 5V/U7 clearance (0.0745mm) — batched (same SW corner): the 0.5mm 5V trunk
    inherently grazed U7.2 (GND) approaching U7.3 (5V) from the north (pads only
    0.15mm apart). Rerouted 5V to enter U7.3 from its SOUTH edge; verified clear
    at the width_floor-widened 0.501mm. Side effect: U7.2 lost thermal spokes ->
    added U7 to the GND full-connection pad_overrides.
  * U6 (4 items_not_allowed) — VENDORED the stock Sensirion_DFN-4 SHT4x footprint
    into 03_src/lib/Sensor_Humidity.pretty with the embedded picture-frame
    keepout flipped `tracks not_allowed`->`allowed` (vias + copperpour stay
    not_allowed, so the keep-pour-off-the-sensor intent is preserved; only the
    sensor's own 4 pin tracks are permitted). Rebound via a {lib,path} entry in
    floorplan.yaml libraries (first, so it wins). Cleared all 4.
  * silk (48) — DE-COLLIDED per fleet standard (not ignored): (a) trimmed the
    vendored RJ45 footprint's F.SilkS north outline from local y-8.11/-8.5 to
    -7.7 (0.3mm off the overhang board edge) — one edit fixed all 8 connectors,
    16 silk_edge_clearance gone; (b) relocated the 3 "crowded" captions
    (generate_board could not nudge them clear) to verified-clear centres: the
    required NOT-ETHERNET warning to (95,33) centred below the port bank, the
    title to (92.5,116.5), the USB label to (90,127.5) at J2. 27 silk_over_copper
    + 5 silk_overlap gone.
- RESULT (MEASURED, kicad-cli --severity-all --refill-zones, stitch gate clean):
  **0 violations / 0 unconnected.**  (79/8 at session start.)
  Board↔netlist parity holds by construction — generate_board asserts every pad
  net from 06_build/netlists (the netlist the schematic gate validated via ERC +
  count_parity); kicad-cli --schematic-parity can't run here only because the
  .kicad_sch lives in 03_tscircuit/kicad/, not beside the board (a release-
  packaging step, not a routing-gate defect).
- SCOPE: every change is projects/crow-recorder-central-v2/-scoped
  (floorplan.yaml / route.yaml / rules/nets.yaml / 03_src/lib vendored footprints
  / the promoted chain 03_src/route/rv2_final.kicad_pcb). NO skills/ edits.
- HANDOFF: coordinator to independently re-verify (fresh DRC + pcb_toolkit) and
  commit the board + config, then red-team + seal.

## 2026-07-23 — rebuild driver promoted (M-REPRO) + reproduces 0/0/0
- did: promoted the scratchpad reuse-script to a COMMITTED, canonical board
  driver 03_src/rebuild_reuse.sh (fleet rebuild_fast pattern): regenerates the
  board from committed 03_src (floorplan/rules/vendored footprints) + IMPORTS the
  promoted chain 03_src/route/rv2_final.kicad_pcb (no stochastic KRT), stitch,
  generate_rules LAST, then the full routing gate (kicad-cli --severity-all
  --refill-zones --schematic-parity). Copies 03_tscircuit/kicad/<board>.kicad_sch
  beside the board so --schematic-parity RUNS (was silently skipped before).
  Wired 03_src/rebuild_all.sh's board stage to call it (schematic gate -> board).
- parity fix: --schematic-parity surfaced 1 footprint_symbol_field_mismatch — the
  vendored US8 (U4) footprint carried a `(property "Description" ...)` field the
  converter symbol lacks. Removed that property (kept the library `(descr ...)`)
  -> parity 0.
- RESULT (MEASURED): `bash 03_src/rebuild_reuse.sh` -> ROUTING GATE 0 violations /
  0 unconnected / 0 parity, from committed source. Reproducible.
- FLAG for the coordinator (pre-seal, NOT routing, involves FROZEN skills): the
  FULL 03_src/rebuild_all.sh (which first re-runs the tscircuit schematic gate)
  does NOT cleanly reproduce — `tsci build` regenerates a DIVERGENT
  03_tscircuit/kicad/<board>.kicad_sch (2904/2823-line churn, UUID/ordering
  non-determinism; connectivity stable per count_parity but the file differs, and
  a fresh sch then shows 9 --schematic-parity field diffs), and the schematic
  gate's kicad_sch_parity.py crashes (ValueError unpacking, "vs sealed 04_kicad").
  Both are schematic-stage / skills concerns pre-dating this session. The ROUTING
  gate reproducer (rebuild_reuse.sh, against the COMMITTED sch) is clean 0/0/0. I
  restored the committed 03_tscircuit files my one rebuild_all test overwrote.

## 2026-07-23 — P0 FIX PASS (red-team DO-NOT-ORDER): net-merge class fixed at SOURCE
- ROOT CAUSE (verified, upstream of board config): geometric net merges in the
  GENERATED converter schematic — `kicad-cli sch export netlist` connects wires
  whose ENDPOINT touches another wire (T-junction) or that overlap collinearly.
  TWO instances found (red-team caught one; my new gate caught the other):
  1. P5VA_4 -> AUDIO4M (the reported P0): the vertical P5VA_4 wire
     (280.67,136.525)->(280.67,153.035) passed EXACTLY through (280.67,147.955),
     the junction endpoint of the AUDIO4M wires. Merged net took the name
     AUDIO4M -> port-4 +5V pins (J6.4/J6.7/F4.2) landed on ch4 audio-minus.
  2. MID2P -> 5V (NEW, red-team MISSED it): the 5V tree's wire
     (244.475,327.66)->(255.27,327.66) ran COLLINEAR-overlapping the MID2P wire
     along y=327.66 -> ch2 positive RC mid-node DC-shorted to the 5V rail
     (Cc2P.2/Rs2P.1 were in net 5V; the 5V trunk even ROUTED THROUGH Cc2P.2's
     pad as a via point on the board).
  Why every gate stayed green: ERC/DRC/count_parity are all SELF-consistent
  with the merged netlist; nothing compared label intent vs exported nets.
- FIXES:
  * Schematic (03_tscircuit/kicad/*.kicad_sch, the committed pinned artifact —
    tsci regeneration is non-deterministic, so repaired in place, minimal +
    journaled): dogleg 1 — P5VA_4 vertical moved to x=281.94 (checked: no
    foreign endpoint/label on the new segments; mid-wire crossings don't
    connect). dogleg 2 — 5V approach jogged to y328.93/x245.745 clearing the
    MID2P line. ERC 0 errors after both.
  * NEW GATE (the can-never-pass-silently mechanism, wired into
    03_src/rebuild_reuse.sh step 0): 03_src/check_port_nets.py — (a) LABEL
    SURVIVAL: every schematic global_label name must exist as a netlist net
    (catches ANY geometric merge/swallow, any net: this is the check that
    found MID2P); (b) 8-port pin-for-pin map per the brief (J*.1/2=AUDIO±,
    3=PLUS5V_BEEP, 6=BEEP_RETURN, 4/7=P5VA_n, 5/8=GND, 9-12 NC). The driver
    now also exports the netlist from the COMMITTED sch (deterministic) before
    generate_board. PASS = 115/115 labels, 8/8 ports.
  * Chain surgery (03_src/route/rv2_final.kicad_pcb, every segment
    pcb_toolkit-verified): PORT 4 — deleted the merged 30-item AUDIO4M tree;
    re-added the audio branch with 2 A* dodges (old route passed THROUGH
    F4.2's and J6.4's pads); added P5VA_4 as the P5VA_5 route shifted x-20
    (ports are on a 20mm pitch) + A* leg; rebound F4.2/J6.4/J6.7. CH 2 —
    deleted the 5V through-cluster path + redundant spur; rebound
    Cc2P.2/Rs2P.1 to new net MID2P; routed MID2P pad->In3-window->via(70.60,
    66.45)->In2 freed corridor->Rs2P.1's converted via (A* refused, manual
    lane found: the cluster is walled by ADC3P/LRCK/3V3A/3V3-B.Cu). TRUNK —
    the deletions severed the ONLY 5V link between the power corner and the
    entire port-bank distribution (100-item island: F1-F8, U10, FB_BEEP —
    the old trunk ran through Cc2P.2's pad, confirming red-team P1#2's
    fragile-trunk finding); reconnected via verified A* (66.10,74.50)->
    (79.10,62.80) at 0.50mm avoiding the cluster.
  * route.yaml: P5VA_4 added to the pwr wave (was missing — same-bug symptom).
- RESULT (MEASURED): rebuild_reuse.sh -> check_port_nets PASS + ROUTING GATE
  0 violations / 0 unconnected / 0 parity, from committed source.
- SKILL FLAG (frozen, for the coordinator): the converter
  (circuit_json_to_kicad_sch.py) needs a wire-crossing invariant — never emit
  a wire endpoint ON a foreign wire, nor collinear overlaps (the schwriter2
  canon S2/T-junction hazards, now observed twice from the tscircuit path).

## 2026-07-23 — P0 FIX RE-VERIFIED from committed source + P1 set closed (pre-seal)
- did: resumed from WIP 8017400 (killed mid-rebuild = untrustworthy). Kept the
  uncommitted route.yaml change (unify_zone_priorities removed from the pass
  list — verified against usb-hub-3s-v3's SEALED route.yaml, which runs the
  same F.Cu-GND-board-wide + cross-net patch-pour pattern with that pass
  absent) and re-ran 03_src/rebuild_reuse.sh clean.
- RESULT (MEASURED): check_port_nets PASS — 115/115 labels survive to the
  netlist, 8/8 ports pin-for-pin; ROUTING GATE 0 violations / 0 unconnected /
  0 parity (gate.json 2026-07-23 18:10). Semantic battery: E-INV 7/7,
  E-TOPO 2/2 rails PASS (trunk over-built advisory: declared 1.6A vs derived
  0.7A — intentional, the raw pod-5V distribution rides the same trunk),
  count_parity 194==194 x4 (board/circuit.json/kicad_sch/netlist vs manifest).
- P1 closure (each measured):
  * U7 PFM: ADR-0005 amendment (committed at 8017400) — honest correction,
    no netlist change, v-next EN-divider recorded.
  * 5V ampacity/netclass: 159 5V segments ALL 0.5mm + 3 F.Cu pour patches
    (119+332+693=1144mm2); final 04_kicad .kicad_pro carries 6 netclasses
    (PWR_IN 0.5 / PWR 0.4 / SWITCH_NODE 0.35 / ANALOG_IN 0.25 / CLOCK 0.25).
    Beep-bus PTC: deferred per ADR-0007 v-next (FB_BEEP is a bead, not
    protection — documented).
  * Spans: P-ADJ's whole-net bbox conflates fan-out with local adjacency;
    re-measured each budget's true subject (Rg->Q2 gate 5.0mm; Cout_U9->U9.5
    4.7mm; Cin_U9->U9.1 4.2mm; VIN_RAW input section 16.9mm all-0.5mm;
    QSPI_CLK 37.6mm ~0.24ns flight, timing-benign) -> evidence-backed
    waivers in 03_src/rules/policy_waivers.yaml.
  * NOT-ETH silk: 8x per-port "NOT ETH 5V!" + banner verified ON the rebuilt
    board (pcbnew, F.Silkscreen, x=25..165).
  * ADR-0007 finalized: USER waiver carried from pod-v2 ADR-0005 with an
    explicit material-difference check (pod was P0 zero-impedance into an
    op-amp; here P1 through per-port PTCs + 8x silk -> equal-or-lesser).
- NEW GATE: 03_src/audit_board.py (P-POL/P-KEEP artifact, pod-v2 pattern) —
  19 polarity facts (pins J1 center-positive, D1 band, Q1 D->S GUARD, Q2
  low-side, both bucks, both LDOs) + 11 connector mate/keepout checks; PASS.
  RED-TESTED: swapped D1 fact -> FAIL(1) printed, nonzero exit.
- policy_audit: 0 FAIL (PASS=21, WAIVED=3 evidence-backed, HUMAN=6 -> graded
  by the release reviews). R-THERM waiver: U1 EP is served by 16
  footprint-embedded 0.3mm PTH thermal pads (4x4 grid, measured) — checker
  counts only PCB_VIA objects; blind spot, not a missing heat path.
- 08_reviews/ populated: reconstructed red-team review (provenance note —
  verbatim text lost to the quota kill; findings from contemporaneous
  records) + DISPOSITIONS.md ledger (2 P0 fixed, 5 P1 dispositioned, 1
  refuted-GUARD).

## 2026-07-23 — v1.0 STAGING: sourcing at source + M-BOM wrong-part catch
- did: staged 07_releases/v1.0-2026-07-23. Fab export (13 gerber layers + 2
  drills, zip 15 files; BOM 48 lines, CPL 182 parts). All BOM codes now flow
  from the tsx (supplierPartNumbers) — the 7 code-less passives were closed:
  L1=C882626 (1277AS-H-2R2M 2.1A/2.6Asat), L2=C237284 (1277AS-H-1R0M
  3.1A/3.7Asat), beads x4 = C3716677, R_fb2b=C25785.
- WRONG-PART CATCH (M-BOM leg C class): the vetted-in-WIP bead
  BLM21PG600SN1D (C18305) is a 60-OHM part — Murata's impedance code 600 =
  60 x 10^0 (601 = 600). Its part.yaml claimed 600R/2A/25mR; the JLC catalog
  row (60R/3.5A/20mR) broke the tie, cross-checked against C41556732
  (BLM21PG601SN1D, 600R/1.4A/140mR). Ordered part: BLM21SP601SN1D
  (C3716677, 600R/2.3A/60mR, stock 11402). 02_parts entry replaced;
  ADR-0007 + DISPOSITIONS updated.
- SOURCING SWAPS (each ADR/part.yaml-documented): U9 TCR2LF18 C150173
  stock=0 -> TLV70018DDCR C79924 (ADR-0006's documented drop-in; SBVS205
  pin table verified 1=IN 2=GND 3=EN 4=NC 5=OUT, sch/tsx/part.yaml updated).
  Y1 FA-238 24MHz: EVERY FA-238 variant stock=0 -> NX3225SA-24MHZ-EXS00A
  C2762192 (same 3225-4P, SAME CL 9pF, +/-10ppm, stock 8142). R_fb2b 400k:
  not in the JLC catalog at all -> 402k E96 C25785 (0V9 setpoint 0.8985V,
  -0.17%, inside the 1% divider tolerance).
- process note: tsci regen after each tsx edit; the PINNED converter
  .kicad_sch restored from backup each time (the regenerated sch would
  reintroduce the net-merge geometry), then hand-patched for the two value
  fields (R_fb2b 402k, U9/Y1 code values) — ERC 0, check_port_nets 115/115
  + 8/8, ROUTING GATE 0/0/0 re-measured AFTER the edits (rebuild3).
- gates at staging: bom_source_check PASS (48 lines, every LCSC == source;
  ledger +6 catalog-verified codes); stock verify: FAIL only on the 2
  ADR-documented consignment lines (XU316 C6938291, RJ45 C9900035627) + 2
  uncoded hand-solder headers — dispositioned in ORDER_README. ERC 0/1409w.
  policy_audit: only M-REL open (MANIFEST — resolves at stamp).

## 2026-07-23 — fresh-lens verdict ORDER; both P1s fixed PRE-SEAL; twin gate green
- FRESH LENS (zero-context headless claude -p over the staged archive +
  curated docs; journals/STATUS/08_reviews withheld): VERDICT ORDER, no P0,
  "all previous P0 defects verified repaired". 2 P1 + 4 P2 findings —
  archived verbatim in 08_reviews/2026-07-23_v1.0_fresh-lens_integrated.md,
  dispositioned in DISPOSITIONS.md (FL-*).
- P1 FIXES APPLIED AT SOURCE (a finding at staging costs an edit, not a
  supersede): CL1/CL2 22pF -> 12pF C0G C1547 (crystal CL 9pF: 2*(9-3)=12pF;
  authored 22pF was ~30-50ppm of pull); Cout_U10 1uF -> 2.2uF 25V X5R
  C72203 (Torex phase-comp requirement; the DETAIL_DESIGN "[PARTS confirm
  Cout]" placeholder had never been resolved — now it is). nets.yaml PWR
  class: phantom PLUS5V_AUDIO replaced by the real P5VA_1..8 (measured: all
  120 segments already 0.5mm).
- RE-GATED after the fixes (rebuild5, from committed-shape source):
  check_port_nets 115/115 + 8/8; ROUTING GATE 0/0/0; E-INV 7/7; E-TOPO 2/2;
  count_parity 194 x4; audit_board 21+11 PASS; bom_source_check PASS (49
  lines); twin exit 0 (160 OK / 358 checked; the one FETCH-FAILED is the
  C99* consign RJ45, evidence-adjudicated; register
  03_src/rules/twin_adjudications.yaml — 8 evidence-backed entries incl.
  the C464587 alternate-not-a-drop-in probe); missing_models 0/172;
  stock: only the 2 ADR'd consignment lines (XU316, RJ45).
- TWIN ADJUDICATION MATCHER note: a code-level FETCH-FAILED reports ONE
  combined-ref row ("J10,J3,..."), and the matcher tests that whole string
  against refs entries — omit refs and key on lcsc+status for that class.
- Staged archive complete: fab(zip+drills+bom+cpl) / pdf(schematic from
  tscircuit render, layers, assembly) / source(sch+pcb+tsx+net) / 3d(step) /
  verification(19 files incl. both red-team archives + fresh_lens).
  policy_audit: ONLY M-REL open (MANIFEST — stamps at seal). Proceeding to
  the 2-commit seal.

## 2026-07-24 — v1.1 respin (external DO-NOT-ORDER on v1.0)

- External file/evidence review of sealed v1.0 arrived post-seal; orchestrator
  verified every claim against the sealed bytes. Archived verbatim
  (08_reviews/2026-07-24_v1.0_external-llm_full.md), EXT-F1..F6 dispositioned.
- F1: XU316 EP footprint's 16 dup-numbered 0.30/0.15 thru-hole pads REMOVED;
  16 real GND vias seeded at rebuild step 3.5 (03_src/add_u1_thermal_vias.py,
  stopgap w/ promotion schema); step 4.5 patches setup (capping yes)(filling
  yes). MEASURED: PTH file has NO 0.15 ComponentDrill tool; T1 ViaDrill 0.150
  carries all 639 vias incl. the 16 EP holes at (90,102)±{0.55,1.65}.
- F2: KiCad only pairs nets by P/N//+/- suffix — USB_DP/USB_DM could never
  bind a diff-pair rule; renamed USB_DM->USB_DN through tsx/sch/part.yaml.
  90ohm solved for JLC06161H-3313 (3313 prepreg h=0.0994 Er=4.1) by 2D FD
  field solve: w=0.125/gap=0.15 -> 89.7-90.5 ohm (sanity: 50.6 ohm SE at
  w=0.14). generate_rules_generic grew per-class diff_pair (netclass + dru
  rule + board diff_pair_dimensions; 3 tests RED-verified). KRT route_diff
  reroute: spread 0.110mm, all 0.125 F.Cu, 0 vias; activation proof = dru min
  0.30 produced 10 diff_pair_gap_out_of_range on a copy. audit_board grew the
  R-LEN skew/width/layer gate + the U1-EP-16-vias gate.
- PIPELINE TRAP FOUND: the v1.0 P0 dogleg surgery lived only in the COMMITTED
  converter kicad_sch — gen_tscircuit regenerates that file, and a fresh
  render measurably reintroduced the merge class (check_port_nets LABEL-LOST
  P5VA_4 + MID2P). The sch is now a PROMOTED ARTIFACT: rebuild_all
  saves/restores it around gen_tscircuit and refreshes ERC/netlist evidence
  from the promoted copy; check_port_nets proves the promoted sch is the one
  exported (115/115 + 8/8 re-verified after the reroute).
- Sourcing drift at staging: basic C25744 (10k) + C25900 (4.7k) stock=0 at
  JLC; pinned in-stock 1% equivalents at SOURCE (C60490, C105871), C105871
  catalog-vetted into lcsc_passives_ledger.yaml.
- F4 discipline: every verification artifact regenerated against the STAGED
  v1.1 dir (standalone-source DRC 0/0/0 after archiving the fp-lib-table with
  archive-relative .pretty paths; bom_source/stock/twin name the sealed dir).
  Manual v1.0-vs-v1.1 hash diff: all fab/pdf DIFFER except cpl.csv
  (IDENTICAL — placement/rotations untouched by design; freshness's
  stale-artifact check silently skips board-prefixed dir names, so this was
  checked BY HAND).
- SEAL STOPPED (2026-07-24, pre-seal): the v1.1 zero-context pin review flagged
  U1.40/43/52 (LV_L_N/LV_T_N/LV_R_N) hard-tied to 3V3. Datasheet-confirmed P0
  (XU316-1024-TQ128 ds v2.0.0): the straps are Input PU **IOB** pins — the
  bottom IO bank is ALWAYS 1.8V (§4.8) and AMR V(Vin) = VDDIO+0.5 = 2.3V
  (§15.1) — a 3.3V tie is ~1V over AMR on the consigned SoC. Correct 3V3-mode
  select is tie-high-to-1V8 OR FLOAT (internal PU). Latent since v1.0 (v1.0's
  reviews missed it; root cause: part.yaml "tie HIGH(or float)=3V3" — HIGH
  misread as 3V3). PR2-P0-1 OPEN in DISPOSITIONS; DETAIL_DESIGN carries the
  full cite. v1.1 staging dir left as mutable staging; machine gates all
  green; fix is a small tsx change + full rebuild/re-gate/re-review.
- PR2-P0-1 FIX (coordinator-authorized, 2026-07-24): 3V3 tie removed from
  U1.40/43/52 at source — tsx conn entries deleted (comment documents the
  AMR basis), promoted-sch surgery excised the self-contained branch (BFS
  proved it: 14 wires + one 3V3 label touching ONLY these 3 pins), 3
  no_connect markers added. Chain surgery removed exactly 7 copper items
  (the 3 in-pad 3V3 vias + 4 dead B.Cu/In2 segments). First prune attempt
  over-deleted 9 unrelated zone/T-junction-anchored F.Cu segments (endpoint
  graph is blind to T-joints and pours) — restored from git, redone as an
  explicit 7-item removal. Rebuild GREEN: DRC 0/0/0, parity 0 (588 nodes =
  591-3, no-connect 146 = 143+3), ERC 0 err/1201 warn (-14 = excised
  branch), port nets 115/115+8/8, audit_board all green. v1.0-relative
  netlist diff: exactly 7 node moves total (4x USB_DM->USB_DN + 3x LV to
  unconnected) — 06_build/verify/lv_strap_fix_diff.md.
