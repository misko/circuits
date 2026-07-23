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
