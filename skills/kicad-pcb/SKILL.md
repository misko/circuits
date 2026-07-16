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
   2–5 mm of anchors) and gate on a proximity table.
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
11. **Verify with fresh eyes.** Render schematics/boards to PNG and have a
    clean-context agent describe them back — it catches defects the author
    is blind to (8 classes on first use). Red/green every fix; netlist
    parity (node-for-node) after any schematic regeneration.
12. **Separate source / generated / build / releases; extract datasheets
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
| Which routing/placement tool to use, all empirics + traps | `references/autorouter-landscape.md` |
| pcbnew Python API gotchas with workaround patterns | `references/pcbnew-scripting.md` |
| DRC classification, .kicad_dru patterns, JLC capability floors | `references/drc-discipline.md` |
| Placement anchors, snap-back, proximity gates | `references/placement-and-proximity.md` |
| Generator-driven schematics, structure links, section boxes | `references/schematic-generation.md` |
| DeepPCB cloud API (billing traps included) | `references/deeppcb-api.md` |

## Scripts (parameterized, project-agnostic)

| Script | Purpose |
|---|---|
| `scripts/pcb_toolkit.py` | Exact-collide library: verified segments/vias, verified A*, copper-aware ring-search placement |
| `scripts/audit_template.py` | Placement/pad invariant gates (I1–I7): pads-in-outline, mate directions, screw keepouts, classified DRC baseline |
| `scripts/classified_drc.py` | Severity-classified DRC report (real / margin / same-net) |
| `scripts/import_krt.py` | Import KRT-dialect output into a pcbnew board |

Fab output + ordering (gerber zip, BOM/CPL, JLC stock checks) moved to the
**`jlcpcb-fab` skill** — use it for everything order-facing. The old
`scripts/export_fab_jlc.py` here is superseded by its
`export_jlc_package.py` (adds the upload zip + version-safe extensions).

Run them with the KiCad-bundled interpreter (`/usr/bin/python3` with
`import pcbnew` working). Each takes `--help`-documented arguments; none
hardcodes a board.

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
