# Generic router + stitcher — validation proof

`skills/kicad-pcb/scripts/route_and_stitch_generic.py` — ONE parameterized
backend for the stage after board generation: route-prep, KRT waves, import,
and stitch/fill, driven by a small per-board `03_src/route.yaml`. It replaces
the hand-written `route_prep.py` + `route_waves.sh` + `stitch_and_fill.py`
that every project carried. Sealed `04_kicad`/`07_releases` were not touched;
every artifact went to a scratch tree.

## config-lines vs bespoke-lines

| board | bespoke (prep + waves + stitch) | route.yaml | ratio |
|---|---|---|---|
| cook-loadcell  | 86 + 36 + 278 = **400** | 96 (66 non-comment) | **4.2x** |
| crow-array-pod | 79 + 37 + 493 = **609** | 90 (66 non-comment) | **6.8x** |

(Across the fleet the bespoke stitchers alone run 215–537 lines each; the
generic backend is 1180 lines shared by all boards.)

## DRC numbers actually measured

Full pipeline from a freshly generated board — `prep` → **real KRT** waves →
`import` → `stitch` → `generate_rules` LAST → `kicad-cli pcb drc
--severity-all --refill-zones --schematic-parity`:

| board | KRT waves | violations | unconnected | parity | node parity vs sealed |
|---|---|---|---|---|---|
| cook-loadcell  | 3/3, 100% | **0** | **0** | **0** | **0 — 77 nodes identical** |
| crow-array-pod | 3/3, 100% | **0** | **0** | **0** | (routing only — placement parity is the generator proof) |

cook-loadcell was run through the from-scratch stochastic route **4 times**;
all four reached 0/0/0. These are the real DRC counts, not KRT's self-report.

Reproduce (from a scratch project tree — never the sealed one):

    /usr/bin/python3 skills/kicad-pcb/scripts/route_and_stitch_generic.py prep   03_src/route.yaml
    ~/gits/KiCadRoutingTools/.venv/bin/python  .../route_and_stitch_generic.py route  03_src/route.yaml
    /usr/bin/python3 .../route_and_stitch_generic.py import 03_src/route.yaml
    /usr/bin/python3 .../route_and_stitch_generic.py stitch 03_src/route.yaml
    python3 03_src/generate_rules.py        # LAST — pcbnew saves clobber netclasses

The T2 suite (`tests/t2_route_stitch.py`) runs the last two boards end-to-end
in `--slow` and asserts 0/0/0 as a permanent regression.

## What the generic backend expresses

Route-prep: track-free/unfilled enforcement, canon-R1 rules-ride-along (refuses
a netclass-less `.kicad_pro`), keepouts (mounting-hole squares, NPTH-barrel
fences, edge band, per-layer explicit rects for analog guards / corner cuts),
wave grouping (named groups + a `rest` bucket + glob excludes).

Route: chained KRT waves with a per-wave flag override map; hardest-first
ordering is just the wave list order. Hard errors on a net a board lacks, a
nonzero KRT exit, a silent no-output KRT, an unknown flag name.

Import: one-shot import into the track-free base; refuses a board that already
has tracks (the doubling trap).

Stitch: the pass list is the config's **ordering axis** (the survey found the
grid running first/middle/last across boards). Passes implemented: dedupe
vias/tracks, normalize via size, drop micro-fragments, drop dangling tails,
**split T-junctions** (KRT emits mid-body joins that DRC flags as
`track_dangling` — split, never delete), width-floor lift (optionally
region-gated), hole-to-hole repair (nudge or shrink), GND/plane pad rescue
(via-in-pad or adjacent-via+stub), stub fallback, verified-A* fallback (with
pinned via geometry), power/plane-island stitch, via janitor, fill, post-fill
island rescue (with barrel-credit and track-credit), and the gate. The
SWIG-after-`Remove()` poisoning is handled automatically: any pass that
removes copper triggers a fresh-interpreter re-exec, with counters/pending
pads carried across in a sidecar state file.

## What it still CANNOT express (honest list)

These stayed bespoke in the survey and are **not** in the generic backend.
Boards needing them keep a thin per-board script for that one step.

1. **Hand-listed coordinate via ladders** (usb-power-3s `EXPLICIT`, 20 entries;
   `JOBS`, 11 sites; `FORCE_RESCUE`, 6 ref/pad pairs). The schema is trivial
   (`net → [sites]`) and `power_stitch.sites` accepts it — but the *values*
   were derived by a human mapping actual fill islands on a filled board, and
   several encode negative knowledge ("B.Cu under U1 EP is solid gate routing,
   no via fits") that only a comment can hold.
2. **Net-specific deterministic reroutes** (cook-hub COIL_EN: "if the router
   dropped this net, A* U9.4→R24.1 with these two tuned parameter sets").
   That is a per-net router-failure workaround, not stitching.
3. **One-shot coordinate patches** (usb-power-3s ILIM1 endpoint retarget
   `(121.2,62.0)→(121.49,63.5)`). Pure literal→literal geometry edits.
4. **Geographic gates that encode where a wave happened to route**
   (usb-power-3s width floor applies only at `min(x) > 93.5mm`). `width_floor`
   has a `region` box, but a board-independent meaning for 93.5 does not exist.
5. **ble-bus-bar's KRT-import repair engine** (joint patcher, endpoint-to-body
   patcher, 3-pass fixpoint orphan sweep, cross-layer solder vias, cross-layer
   endpoint-pair vias — ~230 lines). Algorithmically generic but semantically
   a *different tool* (netlist repair), deliberately kept out so "the generic
   stitcher" does not also own route repair. `split_t_junctions` +
   `drop_dangling` cover the subset the other five boards needed.
6. **Region ALGEBRA** (cook-hub `IN2_POUR` uses `not in_nogo(x,y)` — a negated
   region; ble-bus-bar's grid bound `95.5` is decoupled from the board
   outline). Config takes rect lists and `avoid` boxes, not arbitrary
   union/negation of regions, and cannot know a bound is *intentionally* not
   the outline.
7. **Arbitrary concave outlines for the stitch keep-in.** `keepin` supports a
   rect + uniform `corner_cut` radius (enough for crow-array-pod's four
   R6.25 cuts); a general non-convex board polygon is not expressible.
8. **usb-power-3s's temp-net-rename tap-routing round-trip** (`route_taps_krt.py
   prep|finish`: rename pour-fed tap pads onto a temp net, route only those,
   textual `s.replace` the net back in the output). This is a whole routing
   *strategy* for pour-fed nets that KRT cannot see, not a stitch pass. Its
   actual KRT command lines were never checked in, so that board cannot be
   re-routed through any generic driver — only its promoted chain re-imported.
9. **usb-power-3s's `over_plane()`-returns-True-for-planeless-nets semantics**
   (a pour-to-pour bond mode). Would require per-net "bond mode" config; not
   modeled.

Of the six surveyed boards, **two (cook-loadcell, crow-array-pod) route and
stitch fully through the generic path to 0/0/0** with zero bespoke code. The
4-layer power boards (usb-power-3s, cook-hub) exercise items 1–5 and 8–9 and
would still need a per-board tail for those steps; ble-bus-bar needs item 5.
