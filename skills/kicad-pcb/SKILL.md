---
name: kicad-pcb
description: KiCad PCB/schematic engineering from scripted generation through routing to fab-ready DRC-clean output. Use when generating, routing, reviewing, or repairing KiCad boards/schematics, or scripting pcbnew. Encodes hard-won empirics (autorouter landscape, KRT parser bug, escape geometry, pcbnew gotchas) so agents don't rediscover them.
---

# KiCad PCB engineering

Battle-tested knowledge from taking a 136-part, 4-layer power board from
generator scripts to zero-DRC-violation fab outputs (SPF rover power board,
2026-07). Every empirical claim below was paid for in GPU-hours, cloud
credits, or debugging time — check provenance notes before assuming staleness.

## Golden rules (the 30-second version)

1. **KiCad has no autorouter.** Use KiCadRoutingTools (KRT, clone at
   `~/gits/KiCadRoutingTools`); freerouting is broken across its version
   matrix; DeepPCB routes poorly (~23%) but *places* well.
2. **KRT routes through existing copper** on any pcbnew-saved board that
   contains tracks or filled zones. Only feed it TRACK-FREE AND UNFILLED
   pcbnew boards, or its own output files ("chain files"). Repairs: `--nets` on the KRT-dialect chain file,
   then re-import EVERYTHING in one shot.
3. **Netclasses + ampacity floors BEFORE routing, ever.** Define
   current-tiered netclasses (SWITCH_NODE / PWR_RAIL / VBUS / signal) and
   `.kicad_dru` per-class minimum-width rules as part of board setup —
   BEFORE any router touches the board. Routers have no ampacity concept;
   with floors in place their thin-pass output fails DRC immediately
   instead of shipping 0.15mm switch nodes. Plan power trunks as POURS
   (priority-N over GND), not tracks; sub-floor tap corridors get named
   rule areas. Retrofitting this after routing cost a full repair campaign
   (SPF power board, 2026-07).
3a. **The policy canon is `references/design-policies.md`** — every schematic/
   placement/routing/meta policy with a stable check ID, verified by
   `scripts/policy_audit.py` (machine items) or the review protocols (human
   items). Run the auditor before any release; zero FAIL + evidence-backed
   waivers is the gate. Rules added below are summaries; the canon governs.
3b. **Reference designators PRINT on the board: F.SilkS, visible, always.**
   Generators must place every part's refdes on the silkscreen (run the
   de-collision pass so they stay legible), IN ADDITION to functional
   labels (terminal words, pin maps) and the F.Fab copy for assembly
   drawings. A board shipped with refdes on F.Fab only — perfect
   functional silk, but no U/R/C names anywhere on the physical board for
   probing and debug (2026-07-17). The placement audit enforces this as
   I8 refdes-not-on-silk (audit_template.py; per-project waivers via
   cfg["ref_silk_ok"], e.g. passives too small next to their body).
3c. **Functional silk for anything a human touches** (canon P5): terminals,
   fuses, headers get plain-word labels (function, polarity, voltage);
   policy_audit P-SILK-FN checks a label exists near every J*/F*/TP* ref.
   Three boards shipped with ZERO functional text — one of them a 12.6V
   battery board with unmarked terminals (fleet audit 2026-07-17).
3d. **Schematics draw their story** (canon S6): generators must WIRE the
   story-critical paths (power entry -> protection -> regulation; the
   primary signal chain); net-label-only connection is acceptable for
   pullups/decouplers/bulk. The label-blob era is retired: the go-forward
   WIRED path is **tscircuit** — author in TSX, and `circuit_json_to_kicad_sch.py`
   (default `--mode layout`) emits a wired, readable `.kicad_sch` (converter v2,
   ADR-0002 Phase A). The human schematic document is tscircuit's own render
   (`build/schematic.pdf`). For the schwriter2 FALLBACK path (footprints
   tscircuit can't yet express — it still emits label-glue, no drawn wires),
   the render review MUST grade readability.
3e. **NC pins are emitted, not narrated** (canon S4): generate_schematic
   places no_connect flags for every sanctioned float; the rebuild chain
   gates `kicad-cli sch erc --severity-all` at ZERO errors (warnings
   baselined with reasons). Prose-only "intentionally floating" notes let
   13 unflagged floats ship on one board and 9 on another.
3f. **Rules ride INTO the router** (canon R1): the route-input project
   file must contain the netclasses — verify with policy_audit R-RULES.
   Fleet audit: every board's r0.kicad_pro had only Default 0.2mm; floors
   were enforced only by the post-route DRC gate. Emit rules before
   route-prep AND last (pcbnew saves clobber netclasses).
3g. **The final route artifact is PROMOTED, not disposable** (canon M3):
   06_build/ stays throwaway EXCEPT the imported final chain file, which
   moves to 03_src/route/ and is committed (sha in the MANIFEST). A
   released board's only route input was gitignored — unreproducible from
   a fresh clone.
3h. **Thermal-via floors** (canon R6): on >=4-layer boards, EPs and power
   pads above ~4mm2 get >=2 same-net vias in/near the pad (policy_audit
   R-THERM). TPS2557 EPs and a DPAK tab shipped with zero.
3i. **Modules before bare complex ICs** (canon P-MOD): when the brief is
   silent, prefer a proven compute/control, radio, interface, power or sensing
   module that meets the locked requirements. A bare IC needs an evidenced ADR
   showing why considered modules fail a binding requirement; run
   `scripts/module_first_check.py PROJECT` before generation.
3j. **A declared RF via-fence is measured from the saved board.** Lattice
   pitch is only an input; collision rejection and via de-duplication can open
   larger flank apertures. Run `scripts/fence_pitch.py BOARD BAND_MM BOUND_MM`
   after stitching and make its nonzero exit block the rebuild before a field
   solver consumes the claimed maximum pitch.
4. **Fanout before routing, hardest nets first.** Escape lanes are claimed
   by whoever routes first. `bga_fanout.py` on fine-pitch ICs, then a thin
   pass (0.15/0.13, 0.45/0.2 vias) for escape-bound nets, then the standard
   pass, then thin reconciliation.
5. **0.4 mm pitch QFN = no trace between pads at any legal geometry**
   (track + 2×clearance ≥ 0.276 mm > 0.2 mm gap at JLC 4L floors). If escapes saturate,
   the fix is the PACKAGE (SOIC swap), not router tuning.
6. **Never add copper without an exact-collide green check**
   (`GetEffectiveShape().Collide`, both layers, hole + barrel). Circular
   pad approximations and "exemption zones" both produced real crossings.
7. **AI/auto placement is blind to electrical proximity.** Decouplers land
   50+ mm from their ICs. Always run a snap-back pass (decouplers/FB/TVS to
   2–5 mm of anchors), then run `policy_audit.py --phase placement` before
   routing. It is the authoritative P-LAYOUT/P-PREC/P-ADJ subset, not a second
   proximity metric, and writes `06_build/placement_policy_audit.md`.
8. **Classify DRC, don't count it.** Real = different-net below the fab
   floor. Margin (≥ floor) and same-net/design-intent items get scoped
   `.kicad_dru` rules or documented severity policy. Target: a zero-noise
   report where any new violation is real.
9. **GUI DRC is authoritative for zone-fill-dependent checks**
   (starved_thermal is invisible headless). Fix starved thermals with
   per-pad `ZONE_CONNECTION_FULL`, not vias — the check counts only spokes.
10. **pcbnew scripting**: save/reload after `Remove()` (segfaults), `FindNet`
   not `GetNetsByName`, design rules live in `.kicad_pro` (generators must
   never clobber it), absolute paths in background shells.
11. **Verify with fresh eyes at the first judgeable artifact, then again at
    release.** After schematic/netlist generation, PR-REVIEW requires an
    independent exact-hash topology verdict before placement. After placement,
    it requires exact-hash pin/layout/render verdicts plus same-camera A-RENDER
    before routing. Fresh routed-release reviews still repeat those lenses.
    Render schematics/boards to PNG and have a clean-context agent describe
    them back — it catches defects the author is blind to (8 classes on first
    use). Red/green every fix; netlist parity (node-for-node) after any
    schematic regeneration.
12. **Treat successful generation and clean generation as separate facts.**
    `tsci build` can return zero while embedding `*_error` diagnostics in
    `circuit.json`. Run `circuit_json_diagnostics.py` immediately after the
    build/copy boundary; error records block, while warning records are counted
    for review. Freshness, ERC, and parity do not replace this producer-owned
    diagnostic check.
13. **Separate source / generated / build / releases; extract datasheets
    once.** Every fab order freezes into an immutable `releases/<ver>-<date>/`
    with a MANIFEST (git SHA + tool versions) — a single mutable `fab/` dir
    silently mixed KiCad 7 and 10 gerbers and cannot answer "what did we
    send?". Datasheet FACTS (physical pad numbers, polarity, package) go once
    into `parts/<MPN>/part.yaml` with the revision pinned; the PDF is cached
    globally by sha256 and committed into the project only when the part is
    actually used. See `references/project-structure.md`.

## Reference map (open on demand)

| When you need... | Read |
|---|---|
| Folder layout spec→fab, datasheet/parts caching, releases | `references/project-structure.md` |
| The 7-step generate→route→verify pipeline + KRT invocations | `references/routing-pipeline.md` |
| Fast stage orchestration, handoffs, profiling, layout seal, testing | `references/fast-pcb-flow.md` |
| Which routing/placement tool to use, all empirics + traps | `references/autorouter-landscape.md` |
| pcbnew Python API gotchas with workaround patterns | `references/pcbnew-scripting.md` |
| DRC classification, .kicad_dru patterns, JLC capability floors | `references/drc-discipline.md` |
| Placement anchors, snap-back, proximity gates | `references/placement-and-proximity.md` |
| Generator-driven schematics, structure links, section boxes | `references/schematic-generation.md` |
| RF applicability, stackup/impedance/phase obligations | `references/rf-design.md` |
| Independent RF schematic review | `references/rf-schematic-review-protocol.md` |
| Independent RF routed-board review | `references/rf-pcb-review-protocol.md` |
| Exact-Gerber RF fabrication review | `references/rf-fab-review-protocol.md` |
| DeepPCB cloud API (billing traps included) | `references/deeppcb-api.md` |

## Scripts (parameterized, project-agnostic)

| Script | Purpose |
|---|---|
| `scripts/pcb_toolkit.py` | Exact-collide library: verified segments/vias, verified A*, copper-aware ring-search placement |
| `scripts/audit_template.py` | Placement/pad invariant gates (I1–I7): pads-in-outline, mate directions, screw keepouts, classified DRC baseline |
| `scripts/classified_drc.py` | Severity-classified DRC report (real / margin / same-net) |
| `scripts/import_krt.py` | Import KRT-dialect output into a pcbnew board |
| `scripts/fab_tier_util.py` | Resolve a project's declared `fab_tier` into capability floors (`references/fab_tiers.yaml` is the single source) — the generators derive missing via/clearance/silk geometry from it and reject explicit sub-floor values |
| `scripts/route_and_stitch_generic.py` | ONE parameterized route+stitch backend (prep/route/import/taps/quick/stitch) driven by `03_src/route.yaml` — replaces per-board route_prep.py + route_waves.sh + stitch_and_fill.py (+ bespoke tap scripts). `quick` = seconds-fast pre-stitch unconnected + clearance/track_width verdict (the loop tool). See `docs/generic-router-proof.md` |
| `scripts/net_label_survival.py` | S-NETMERGE gate: every schematic global_label survives to the exported netlist (kicad-cli merges touching/collinear wires silently); config = `label_survival:` block of `03_src/rules/electrical_invariants.yaml` |
| `scripts/module_first_check.py` | P-MOD architecture gate: every complex subsystem records module-vs-chip reasoning; bare ICs inventory external support parts and integrations at/above the configured threshold carry an evidenced module trade study; missing policy is UNMIGRATED, never PASS |
| `scripts/pin_map_check.py` | P-PINMAP early identity gate: immediately after board generation, prove every dossier physical pin reaches both the schematic and footprint; intentional fused-land aliases require explicit evidence |
| `scripts/pre_route_review_check.py` | PR-REVIEW fail-closed boundary: binds netlist/parts/board plus adopted design-rule bytes, so a requirements, ratings, or route-contract edit stales the independent review before routing |
| `scripts/early_design_check.py` | D-SPEC/E-PATH/E-SWDRV/E-SURGE fail-closed authoring gate: external-output measurement boundary and complete IR path, controller/MOSFET drive compatibility, and surge coordination before schematic review/layout |
| `scripts/placement_gates.py` | Shared placement gates P-OUT, P-CAP, and non-waivable P-BODYCLR positive same-side courtyard/body-to-foreign-pad clearance — post-placement, pre-routing |
| `scripts/critical_route_check.py` | R-PAIRMAP cross-checks the declared inventory against independent `nets.yaml length_match` intent, engine/seed source, layers and via policy; R-CRITESC grades realized copper. Shared route/prep/import/stitch entry points invoke it, so direct calls do not bypass the gate. |
| `scripts/policy_audit.py --phase placement` | Authoritative early P-LAYOUT/P-PREC/P-ADJ/P-ADJ-PAIR/P-ADJ-UNREACHED gate — after placement, before routing; separate report so the full release audit is not clobbered |
| `scripts/pad_separation.py` | P-PADSEP: separate-footprint copper must clear the fab-tier gap; exact same-net overlap/touch and foreign-pad stencil paste intrusion are fatal; same-footprint composite pads remain legal |
| `scripts/rf_contract_check.py` | RF-CONTRACT: explicit RF applicability, ports/cross-sections/claims/first-article plan, plus exact-artifact RF schematic/PCB/fab reviews with derived nonzero requirement coverage |
| `scripts/tier_preflight.py` | R-PREFLIGHT gate: every routing/stitch/rescue parameter with a DRC-floor twin, including nominal board-thickness/minimum-drill plated-through aspect ratio (`PF-VIA-ASPECT`), proven consistent with the declared fab tier BEFORE any KRT cycle; wired refuse-to-route into `route_and_stitch_generic route`; `--explain` prints derivations + copy-paste fixes |
| `scripts/fence_pitch.py` | Saved-board RF ground-fence gate: reconstructs each RF F.Cu arm, projects GND vias and PTH return posts into each flank band, and fails when any realized interior aperture exceeds the declared bound |
| `scripts/grind_driver.py` | The BOUNDED mechanical DRC grind loop: classify findings, look each class up in `references/grind_fixes.yaml`, auto-apply only conservatively-safe reruns, escalate everything else (`06_build/grind_escalation.md`, distinct exit codes). Hard stops: 0/0/0, novel class, D-BACK 3-cycle stagnation, `--max-cycles`. Journals every cycle (canon M9) |
| `scripts/pcb_flow.py` | Thin process conductor: pre-route escape/tier preflight, timed stages, bounded grind delegation, content-addressed agent handoffs, and fresh-rebuild `layout-seal` (PCB layout only; never substitutes for jlcpcb-fab release gates) |

Fab output + ordering (gerber zip, BOM/CPL, JLC stock checks) moved to the
**`jlcpcb-fab` skill** — use it for everything order-facing. The old
`scripts/export_fab_jlc.py` here is superseded by its
`export_jlc_package.py` (adds the upload zip + version-safe extensions).

Run them with the KiCad-bundled interpreter (`/usr/bin/python3` with
`import pcbnew` working). Each takes `--help`-documented arguments; none
hardcodes a board.

### Fresh-context pin review (scripts/pin_audit.py + references/pin-review-protocol.md)

The gate that breaks the consistently-wrong-together failure mode (a
mirror-numbered footprint passed DRC+parity+polarity twice): per active part,
`pin_map_check.py` first runs immediately after the generated board exists,
before placement review or routing, to catch missing/collapsed artifact pin
identities while fixes are cheap. It does not replace datasheet authority:
`pin_audit.py` extracts a conclusion-free dossier (pad positions/sides,
computed winding, part.yaml functions, actual board nets, alias/fused-land
declarations, datasheet path). When several PDFs are vendored it selects the
one whose bytes match `datasheet.sha256`; directory order is never authority;
the orchestrator then spawns FRESH agents - no session context - who derive
the expected pinout from the datasheet figure and judge every pin's net
electrically, per the protocol. Verdicts land in the release's
verification/pin_review.md; any FAIL blocks the order.

## Companion tools

- **KRT** (`~/gits/KiCadRoutingTools`, github drandyhaas/KiCadRoutingTools):
  routing, fanout, DRC helpers. THE workhorse. Never rely on /tmp clones.
- **kicad-happy** (github aklofas; analysis-only): `analyze_schematic.py` /
  `analyze_pcb.py` — subcircuit detection and design review. Good detector,
  known false-alarm classes (rail sources on label-only captures, pull-ups
  on unused open-drain, 22R USB series advice). Never expect it to route
  or format.
- **kicad-cli** (v7+): `sch export netlist|svg|pdf`, headless plotting.

## The failure museum (mistakes the tooling invites)

- Routing with KRT on a filled-zone or tracked pcbnew board → 400+ silent
  crossings that DRC catches but the router reports as success.
- Adding stubs/vias checked only at the via SITE, not along the stub path.
- Ring-search placement that checks footprints and holes but not the copper
  UNDER the new location → pads on other nets' tracks.
- Trusting a headless-clean DRC when the GUI fill disagrees (starved_thermal).
- A schematic generator that rewrites `.kicad_pro`, silently destroying the
  DRC rule floors and severity policy.
- "Fixing" a nudged via into a new violation — always re-run the green check
  after every micro-edit, including your own fixes.
- Believing an autorouter's "0 fails" without an import + DRC ground truth.
- A generator that SKIPS parts with missing footprints as a console warning —
  a one-line `print` shipped a board without its USB ESD array (D8), and
  every board-internal gate (DRC, audit, routing completeness) passed
  because they never compare board vs schematic. Missing footprint must be
  a HARD ERROR, and `kicad-cli pcb drc --schematic-parity` (KiCad 10+) must
  be in the gate list.
- A hand-rolled collision-cache "optimization" built before `board.Add(fp)`
  made the new part's own pads invisible to probes → routed a track through
  its own GND pad. The toolkit's bbox index now auto-rebuilds on track/pad
  count changes; if you bypass the toolkit, staleness is on you.
- Retrofitting a part into a routed board: route its stubs OUTWARD-FIRST
  (the pin whose escape is most boxed-in goes first) — a carelessly-shaped
  early stub (an L-fence along the pad row) boxed in a later pin on the
  same package and cost three rip-and-reroute rounds.
- The KRT thin pass (0.15/0.13) will happily route a 6A buck switch node —
  NOTHING checks ampacity by default (DRC = clearance, audit = placement).
  Both SPF buck SW nodes shipped as 0.15mm fuses until a manual
  current-path walk caught it. THE DURABLE FIX (do this at project start):
  current-tiered NETCLASSES (e.g. SWITCH_NODE / PWR_RAIL / VBUS) plus
  .kicad_dru per-class minimum-width rules — undersized power copper then
  becomes a hard DRC violation the standard gate catches. Calibration:
  trunk current rides pours/planes (floors are backstops, not the sizing);
  mixed nets with mA sense taps get a moderate floor; sub-floor tap runs
  (gate-drive returns) get NAMED RULE AREAS with a scoped lower floor so
  the exemption lives on the board. Repair pattern for undersized trunks:
  priority-N F.Cu pour patches over the GND pour (fill handles clearance).
  Gotchas paid for: dru width rules compare exact NANOMETERS (249800 nm
  prints as "0.25" and fails a 0.25 min); pours split into islands over a
  crossing trace (gate traces love slicing SW pours — reroute the gate or
  bridge islands on B.Cu; the island-to-island unconnected check is the
  tell); pre-filter rails may have NO inner plane — the F.Cu patch is the
  highway.
- Deleting "redundant" thin tracks after installing a trunk pour: FIRST
  enumerate every pad on the net. The trunk (FET↔inductor) was
  pour-covered, but controller SW-sense pins, bootstrap caps, and ILIM
  taps hung off the same net through those "redundant" segments — deleting
  all 64 disconnected them and triggered an island-reconnection campaign.
  Delete only segments whose endpoints are both inside the pour's fill.
- Git is the geometry undo across sessions: `git show <rev>:<board>` +
  a pcbnew load of that file lets you extract exact ripped segments
  (net, layer, endpoints, width) and re-add them verbatim — far safer
  than re-deriving a route that took days to converge.
- A script that crashes between `Remove()` and `Save()` ships partial
  state, and SWIG iterators can poison mid-session after a Remove (a
  `GetTracks()` call after `Remove(zone)` threw). Batch removals into
  their own load→remove→save script, additions into another.
- Generic 2-pin symbols ("1"/"2") on polarized footprints: KiCad diode/LED
  footprints put the CATHODE on pad 1, and NO electrical check (DRC, ERC,
  parity, netlist) can see a reversed assignment — it's self-consistent. A
  reverse-battery schottky shipped cathode-to-battery (dead always-on rail)
  and an LED reversed. Audit every 2-pad polarized part explicitly: pad 1's
  net must be the cathode/positive per the footprint's marker (verify the
  marker pad from the footprint's own asymmetric graphics if unsure). Fix
  on a routed board = rotate 180 + rebind pad nets (copper untouched).

### 2026-07-16 batch (usb-power-3s bring-up: 266 DRC violations -> 0/0/0)

- `pcbnew` SAVES CLOBBER `.kicad_pro` netclasses — a board regenerated by
  script wipes the classes; DRC then silently uses Default 0.2 mm clearance.
  Run the rules generator (netclasses + dru) LAST in the rebuild chain,
  after every pcbnew save.
- DRC floor constraints come from the BOARD file's setup (ds.m_*) AND the
  `.kicad_pro` `board.design_settings.rules` block — the pro block wins for
  hole/edge/annular floors. Advanced 0.25/0.15 vias need
  min_via_annular_width <= 0.05 and min_through_hole 0.15 in BOTH.
- `via_site_ok` skips same-net copper, so it happily approves a via STACKED
  on an identical via — dedupe by coordinate yourself, and seed the
  dedupe set from the board's existing vias, not just your own.
- Re-importing a KRT output into a board that already has tracks DOUBLES
  everything (`holes_co_located` x69). When a KRT output evolved FROM the
  live board, regenerate the board fresh and import that output once.
- Zone semantics burn-down: same-net same-priority overlapping zones are a
  DRC error (merge into one polygon); a pad inside a HIGHER-priority
  foreign pour is disconnected (rescue via + short track to its plane); a
  pad's own pour "feeds" it only if that pour WINS the point (highest
  priority containing it); the full-board GND pour (prio 0) fills AROUND
  foreign pads and swallows nothing.
- Gate traces slice FET-source pour bands into islands invisible until
  fill+DRC — bond islands with a B.Cu patch + via ladders sized for the
  current, and add a post-fill pass that drops a via into any pad-bearing
  island that has none.
- Sense/tap pads of pour-fed power nets (FB dividers, BST/ILIM taps, VIN
  pins) are NOT routed by anything unless you route them: pours can't
  reach across the board and the router only sees its own ratsnest. Either
  extend pours/planes, add rescue vias (only where the net has a plane
  under the site!), or route them — a KRT pass restricted via temp-net
  renamed pads (tap pads + one pour-fed anchor pad -> TAPX, route --nets
  TAPX, rename back in the output) beats hand-threading a dense bus.
- KiCad python SWIG traps: instantiating a PCB_IO corrupts the module-level
  `pcbnew.FootprintLoad`, and `FootprintSave` corrupts every OTHER live
  footprint wrapper — do footprint library writes ONE PER SUBPROCESS.
- Schematic parity zero requires: full `lib:name` FPIDs on generated
  footprints + an fp-lib-table covering every referenced lib; symbol pin
  numbers matching footprint pad names EXACTLY (merged drain pads, "SH"
  shield pads); FP_BOARD_ONLY|FP_EXCLUDE_FROM_BOM on mounting holes; and
  vendored variants (e.g. edge-trimmed connector silk) in the project lib
  instead of runtime edits to board copies (lib_footprint_mismatch).
- A `script | grep | tail && next` chain masks the script's exit code and
  the next stage runs on a STALE artifact (we diagnosed a phantom DRC state
  twice). One `set -euo pipefail` rebuild script; every failing checker
  exits BEFORE saving.

## Circuit-as-code landscape + adoption policy (2026-07-18)

Boards-as-code tools: CircuitScript (Python-ish DSL, SVG schematics, KiCad
NETLIST export, MIT, young), google/pcbdl, tscircuit (React), SKiDL,
atopile, JITX. Our position: the LAYERING RULE (canon S-DSL) — declaration
ergonomics may evolve; native artifacts + gates never move. We do NOT
adopt external DSLs into the gate chain: CircuitScript's netlist-only
export would disconnect ERC, schematic-parity, and S-OCCL (all keyed to
native .kicad_sch), replacing our least-problematic layer while breaking
the most valuable ones; young single-maintainer projects also lack our
incident-hardened invariants (one-label-per-wire, T-junction spans,
envelope collision-freedom). What we DO take: API ergonomics into
schwriter2 — path syntax for series chains, first-class parameterized
Subcircuits with net prefixing, net OBJECTS instead of strings (typo ->
NameError, closing an S2 hazard). Additive-only; regenerating every
schwriter2 board with netlist parity 0 is the proof any sugar is pure.

**tscircuit is ADOPTED as the design front-end (ADR-0001 + ADR-0002).**
The governing model: **tscircuit = design environment (dev loop); KiCad
backend = CI + fabrication; the converter is the compiler between them.**
`tsci export` emits circuit.json; our `scripts/circuit_json_to_kicad_sch.py`
(the AUTHORITATIVE bridge — NOT `tsci export -f kicad_sch`, which truncates
custom-footprint chips) compiles it to a native, annotated, backend-ready
`.kicad_sch` that flows into the unchanged gate stack (proven: the lipo3s-tsc
capstone, 100 parts, node-for-node = the hand-KiCad original). What tscircuit
owns: authoring, schematic layout (its render IS the human schematic PDF —
`build/schematic.pdf`), placement-as-code (`circuit_json_to_kicad_pcb.py` at
authored `pcbX/pcbY`, never auto-place), module reuse. **Two permanent hard
lines stay KiCad** because the authoring tool must never self-grade them:
**routing physics** (KRT — tscircuit has no ampacity concept, shorts congested
corners) and **jlc_twin** (checker-independence M1 — caught 4 wrong-footprint
boards). Generator: `scripts/gen_tscircuit.sh <project>`; the full mechanics,
converter modes, placement + module details: `references/tscircuit-folder.md`
and `docs/decisions/0002-tscircuit-native-pipeline.md`. Runtime is `bun`
(`~/.bun/bin`) + `tsci` (`npm i -g tscircuit`), persistent per-user. schwriter2
remains the fallback for footprints tscircuit can't yet express.

## Version scoping

Everything here is verified on **KiCad 7.0.x**, re-validated on **10.0.4**
(SPF power board, 2026-07): DRC/ERC/audit/netlist/renders all reproduce.
Known deltas: KiCad 8+ adds `kicad-cli pcb drc` (7 lacks it); KRT emits
KiCad-9 dialect (unopenable in 7, hence the textual import — on KiCad 9+
direct open may work, re-verify). KiCad ≥ 9 API breaks (both fixed in the
scripts with fallbacks): `EDA_UNITS_MILLIMETRES` renamed to `EDA_UNITS_MM`,
and `pcbnew.WriteDRCReport` SEGFAULTS headless (needs the GUI `Pgm()`
instance) — use `kicad-cli pcb drc --severity-all --refill-zones` instead
(same `[type]`-tagged report format). `--refill-zones` makes headless DRC
authoritative for zone-fill checks on 10.x (starved_thermal reproduced the
GUI result); golden rule 8's GUI-only caveat applies to KiCad 7/8. KiCad 10's
`--schematic-parity` catches sch↔pcb BOM gaps nothing in 7 could (found a
real missing footprint on a "clean" board); its noise classes: lib-prefix
footprint_symbol_mismatch, merged-pad multi-pin net_conflict, mounting-hole
extra_footprint. KiCad 10 netlist export is pretty-printed (multi-line
s-exprs) — same-line regex parsers silently match nothing.

## Maintenance

New learnings land in the active project's docs first; graduate them here
when they generalize, with a one-line provenance note. This skill is
KiCad-scoped — do not add unrelated domains.
