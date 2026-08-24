# The canonical routing pipeline

Proven end-to-end on a 136-part, 100×65 mm, 4-layer board: 0 unconnected,
0 shorts, 0 fab-illegal copper. Order is load-bearing — each deviation below
reintroduces a failure that was already debugged once.

## Contents

1. Source-to-preparation authority
2. Ampacity guardrails
3. Canonical routing steps
4. Repair procedure
5. Package-versus-router decision
6. Measured empirics
7. Candidate transactions and final acceptance
8. Quick-loop economics, escalation and progressive controls

The route-entry capability check includes `PF-VIA-ASPECT`.

## Source-to-preparation authority

Before emitting r0, read `source-to-prep-authority.md`. Compile the authored
stack, independent live source facts, optional migration, and route ownership
into one verified source-preparation receipt. Consume its physical-order,
layer/reference, via-span, wave-owner and conservative stitch outputs; do not
rederive those facts in the route driver. During migration the receipt remains
shadow behind current prep authority until its owning canaries pass. This is
an internal source-to-prep seam, not a new lifecycle stage.

## Step 0 (BEFORE anything routes): ampacity guardrails

Define current-tiered netclasses (SWITCH_NODE / PWR_RAIL / VBUS / signal)
in `.kicad_pro` and per-class `track_width (min ...)` rules in
`.kicad_dru`. Plan >1A trunks as priority-N F.Cu pours, not tracks.
Sub-floor tap corridors (gate-drive returns) get named rule areas with a
scoped lower floor. With this in place, every later routing pass —
including KRT's thin pass — is gated by standard DRC. Retrofit cost when
skipped: a full repair campaign (SPF 2026-07: both 6A switch nodes shipped
as 0.15mm until a manual walk caught them).

## Steps

1. **Start from a TRACK-FREE, UNFILLED pcbnew board.** KRT mis-parses
   filled zones AND pcbnew-dialect tracks, then routes straight through
   existing copper (400+ crossings observed twice). Strip tracks
   (`board.Delete`), `z.UnFill()` every zone, save.
2. **Keepouts.** Draw `gr_poly` squares on `User.2` around mounting holes
   (screw-head radius ~3.35 mm); pass `--keepout --keepout-layer User.2`
   to every KRT invocation. Edge strips only where no connector pads live.
3. **Fanout FIRST.** `bga_fanout.py` each fine-pitch IC (VQFN/BGA) before
   any routing claims the escape lanes:
   ```
   python3 ~/gits/KiCadRoutingTools/bga_fanout.py BOARD --output BOARD \
     --component U1 --layers F.Cu B.Cu --track-width 0.15 --clearance 0.13 \
     --via-size 0.45 --via-drill 0.2 --fab-tier advanced
   ```
   Peripheral 0.4 mm QFNs cannot be fanned out or routed between pads at
   any legal geometry — their nets go in the hardest-first set instead
   (and the durable fix is a larger package).
4. **Hardest-first thin pass.** Route the escape-bound / historically
   failing nets on the empty board at 0.15 track / 0.13 clearance /
   0.45-0.2 vias (`--fab-tier advanced`, `--max-iterations 500000`).
   Don't over-stuff one wave: too many hard nets compete; two waves
   beat one big one.
5. **Main pass.** Everything else at standard geometry. The full
   invocation (THE workhorse command — entry point is `route.py`):
   ```
   python3 ~/gits/KiCadRoutingTools/route.py BOARD.kicad_pcb \
     --output OUT.kicad_pcb --layers F.Cu B.Cu \
     --clearance 0.2 --track-width 0.3 --via-size 0.6 --via-drill 0.3 \
     --fab-tier standard --keepout --keepout-layer User.2 \
     --max-iterations 300000 \
     --power-nets VSW 5V_A 5V_B --power-nets-widths 1.2 1.2 1.2
   ```
   `--power-nets` and `--power-nets-widths` are PARALLEL lists (one width
   per net). The hardest-first/reconcile passes are the same command with
   `--nets ...`, `--track-width 0.15 --clearance 0.13 --via-size 0.45
   --via-drill 0.2 --fab-tier advanced --max-iterations 500000`.
   Each `--output` file is a **chain file**: KRT-dialect, re-parseable by
   KRT, the ONLY safe input for repair passes. Name them sequentially
   (`pb_s1`, `pb_s2`, ...) and keep every one until the board ships.
6. **Thin reconciliation.** `--nets <fails>` at the thin geometry. Nets
   served by planes/pours (GND to an inner plane, rails with pours) often
   "fail" in KRT but resolve at zone fill — judge by DRC, not KRT's tally.
7. **Import once, then ground truth.** Textual import of segments+vias into
   the pcbnew base (see `scripts/import_krt.py`), `ZONE_FILLER.Fill`, save,
   then classified DRC + audit gates. KRT's JSON summary is NOT the truth;
   the filled board's DRC is.

## Repairing a routed board

Never re-run KRT on the imported pcbnew board. Instead run
`--nets NET1 NET2 --rip-existing-nets NET3` on the **KRT-dialect chain
file** from the previous pass (which it parses perfectly), then re-import
everything into the clean base in one shot.

For last-mile gaps KRT can't close, use the verified micro-tools
(`scripts/pcb_toolkit.py`): blocker listing → rip single track-only
blockers → direct/L/Z join scan → verified A* → re-route ripped nets.
Every added segment/via must pass the exact-collide check; re-run the
green check after every edit including your own fixes.

Constrain A* to the one or two reviewed copper layers that can actually
carry the repair (`astar_fallback.layers`). This reduces the state space and
prevents an apparently convenient layer change from consuming an unrelated
escape corridor. Its transition vias must use the declared fab-tier
size/drill and `hole_to_copper`; the stitcher inherits the latter from a
matching `stitch.via.tiers` entry when it is not repeated in the A* block.

## Decision rule: router ordering vs package swap

When airlines cluster at a fine-pitch part, split them: nets that fail
because escape LANES were consumed are fixed by fanout-first +
hardest-first (free); nets that must pass between pads or need a via where
no legal landing zone exists are fixed only by the package swap or a
human. On the reference board: 14 airlines at the QFN -> ~10 were
ordering-fixable, 4-5 were mathematically stuck -> SOIC swap closed all.
Run the (free) ordering fix first; swap the package if stragglers survive.

## Empirics worth trusting (provenance: SPF power board, 2026-07)

- More layers do NOT fix routing failures that are escape-bound: bare-board
  (all planes removed) and spread-out placements plateaued at the same
  completion. The ceiling is pad-escape geometry + via landing zones.
- Smaller vias (0.45/0.2 advanced tier) did NOT beat 0.6/0.3 at the router
  level either — the stragglers were lane-blocked, not via-blocked.
- Hardest-first ordering closed 21/22 nets that retry-based strategies
  never closed. Fanout-first closed the rest.
- A finished dense board typically carries fab-legal margin items
  (0.10–0.20 mm spacings from thin passes). Classify, don't panic
  (see drc-discipline.md).

## Loop economics: quick vs the full cycle, and when grind_driver escalates

Measured on the v4 usb-hub-3s clean-room canary (112 parts, 2026-07-21):
one FULL cycle — rebuild chain + `kicad-cli` severity-all DRC + a frontier
agent reading the report — runs **~8-10 minutes**, and the whole grind
historically burned **~500k tokens per board**. A routing iteration only
ever changes unconnected + copper clearance/track_width, so paying the
full cycle per iteration is waste.

The cheap loop: `route_and_stitch_generic.py quick` on the post-import,
pre-stitch board — pcbnew ratsnest unconnected (split routed vs
pour-deferred nets) + clearance/track_width from an unfilled-zone DRC.
**Measured 0.65 s** on cook-loadcell; expect seconds-to-a-minute on a
dense 4-layer board. Iterate routing against `quick`; run the full gate
once quick is clean. quick is a loop tool — the severity-all 0/0/0 full
DRC after stitch remains authoritative, but is one predicate inside the
single final-route acceptance receipt rather than an isolated green claim.

### Final-route acceptance boundary

Read `route-candidate-contract.md` for the sole workspace, evidence, native-DRC,
admission, and verification contract. Its content-addressed accepted-bundle
publisher is experimental and currently refuses promotion. This flow only owns
the order: run quick grading after a candidate mutation, and full grading before
the existing driver may promote a route, seal layout, start release review, or
export fabrication data. A failed, incomplete, stale, or timed-out transaction
cannot authorize that legacy progression; the existing driver and mutable
`FINAL` path retain promotion and rollback authority. `route-exploration.md`
alone owns retry, stagnation, Pareto, and typed-backtrack decisions.

Two stitch passes earn a special note here. Put **`fresh_reload`** after the
last `fill`: it unconditionally saves and re-execs in a fresh pcbnew process,
rebuilding connectivity before any island decision. A long-lived pcbnew
process can otherwise retain a pre-fill view and report fewer zone groups
than the later `kicad-cli pcb drc --refill-zones` gate. This is distinct from
`reload`, which only fires after destructive passes poison SWIG iterators.

Then run **`heal_islands`**. A same-net pour that fills as two or more disconnected
islands is the DRC unconnected class "Zone [X] <-> Zone [X]" — 4 of the v4
usb-hub-3s canary's last 7 findings (LX1/LX2/VIN_S/VBUSA3, priority-2 F.Cu
converter hot-loop pours sliced by escape tracks, 2026-07-21), previously
bridged by hand at frontier-agent cost. The pass detects island groups
with pcbnew's own connectivity on the filled board, bridges the narrowest
collision-clear gap (net-class-width track, or a via through a shared
same-net plane; every emitted segment/via pcb_toolkit-verified), then
refills and re-verifies — a heal that does not reduce the island count is
a hard error, a healed board re-runs as a no-op, and different nets are
never bridged. The grind table's `unconnected_zone_islands` auto entry
maps the DRC class to a stitch rerun with this pass.

`heal_islands.min_bbox` is a performance filter, not a correctness waiver.
KiCad DRC reports very small pad-bearing fragments too; dense QFN/eFuse
boards should use a measured small floor (0.1 mm on the programmable USB hub)
or prove that skipped fragments are padless. The release gate remains the
fresh, refilled CLI DRC, never the in-process group count alone.

`scripts/grind_driver.py` mechanizes the loop between those two levels,
with `references/grind_fixes.yaml` as the class table. It AUTO-applies
only conservatively-safe generator reruns (the v4 batch classes:
track_width wave/class alignment, silk floor normalization,
fp-lib-table emission, refdes de-collision) and ESCALATES everything else
into `06_build/grind_escalation.md` — clearance clusters and opens are
design work, and the D-BACK ladder maps them to the owning stage. Hard
stops (exit codes): 0 = full 0/0/0; 2 = table-escalate; 3 = novel class;
4 = D-BACK (3 consecutive cycles without total-count improvement) or the
--max-cycles cap. The driver is deliberately UNABLE to loop forever; when
it exits nonzero, the expensive agent is summoned ONCE, with counts and
samples, instead of once per cycle.

### Widening the auto-fix vocabulary (canon M8 two-strike promotions)

The grind cost falls each time a class that was hand-fixed board-after-board
becomes a bounded mechanical fix. Three more promotions (2026-07-22, from the
usb-hub-3s v1.1 respin, each already hand-fixed on >= 2 boards):

- **`zones_intersect_same_net`** (auto). Two pours of the SAME net overlapping
  at the SAME priority — KiCad reports "Copper zones intersect (intersecting
  zones must have distinct priorities)". The stitch `unify_zone_priorities`
  pass bumps the smaller zone to a distinct priority so the union NESTS
  legally (same net => identical copper, only the priority integer changes),
  refills, and re-verifies. A CROSS-net overlap is a SHORT and is REFUSED
  (escalate to `shorting_items`). classify_gate splits the DRC `zones_intersect`
  type by whether both items name one net. Provenance: v1.0 "P3-union", v1.1
  re-learn.
- **`seed_stubs`** (config-driven build-step pass). Deterministic pour-fed
  chip-pin stubs — the connections KRT excludes and taps are too short to
  thread. The `seed_stubs` stitch pass (runs BEFORE fill) places EXPLICIT
  geometry from `stitch.seed_stubs`, verified against live copper with
  collision REFUSAL, proves each declared `pin` is reached, and is idempotent.
  The same emitter is available as `prep.seed_stubs` when reviewed copper
  must be present on r0 so every KRT wave routes around it (for example,
  coupled high-speed banks assigned to different copper layers).
  Generalises usb-hub-3s `plan_seed_stubs.py` + `add_seed_stubs.py`.
- **`tap_reattempt`** (bounded retry in `cmd_taps`). A long pour-net pin tap's
  corridor is order-fragile; on a failure the whole tap set is re-routed
  LONGEST-first (most-constrained-first) on a fresh board, BOUNDED by
  `taps.reattempt.max_retries` and progress-gated (a retry that does not beat
  the best failure count stops). Then it escalates, pointing at `seed_stubs`.

Every auto entry carries a `safety:` block naming its four invariants —
**reduce** (re-measure proves the target class dropped), **no new
violations**, **idempotent** (second run is a no-op), **refuse** (escalate,
never guess when it cannot apply safely) — the D-BACK lesson: an unbounded
auto-fixer is worse than none.

The escalation report **self-harvests** the next promotion: when the driver
escalates a class whose grind_fixes provenance already names >= 2 boards, it
prints `class X escalated on boards A,B — two-strike, promotion candidate`, so
the loop flags what to mechanize next (auto classes are excluded — already
done).

### Deliberate wave checkpoints

When a board benefits from a real review boundary between critical/high-speed,
power and control routing, run a deterministic prefix without editing the route
contract:

```bash
python3 route_and_stitch_generic.py route 03_src/route.yaml \
  --through-wave <last-wave-in-stage>
```

The command authenticates every completed wave in `route_progress.json` and
writes no `FINAL` marker while configured waves remain. Continue the exact
chain with `route --resume` (optionally with another `--through-wave`). This is
intentionally incompatible with route races: a partial stochastic candidate
set is neither comparable nor promotable.

If a costly critical prefix has passed review and must become a reproducible
source artifact, promote it explicitly instead of trusting a loose `rN` file:

```yaml
route:
  prefix:
    board: 03_src/route/critical_prefix.kicad_pcb
    through_wave: usb_upstream
    r0_sha256: <exact prepared r0 SHA-256>
    board_sha256: <exact reviewed checkpoint SHA-256>
```

This is a fail-closed continuation seam, not a DRC waiver. Before skipping a
wave, the route command rematerializes the checkpoint, proves P-ROUTEBASE
inheritance from the exact `r0`, runs partial-board physical DRC, and requires
every adopted critical pair to be connected. It records the prefix provenance
in `route_progress.json`; `--resume` reauthenticates it. Prefix continuation is
single-chain only because racing an already-reviewed prefix adds no diversity
to the critical copper and complicates provenance.

### Progressive route controls (new projects)

The public lifecycle stage remains `KICAD-ROUTING`; these are internal seams,
not new orchestration stages. Existing project configs retain their old
behavior until their canaries explicitly promote each predicate.

Read `route-ownership.md` before adding topology/corridor declarations,
`route-candidate-contract.md` before promotion or manual grading, and
`route-exploration.md` before retaining or retrying a failed candidate.

The order is load-bearing:

```text
ownership preflight -> KRT wave -> legacy fast wave gates
                    -> immutable candidate workspace -> verified receipt
                    -> semantic objective/progress receipt
       unresolved -> Pareto + novelty budget -> retry or typed D-BACK
```

Shadow diagnostics record an incompatibility without changing verdict, stage
identity, accepted pointer, or runtime behavior. No live dual mode may tighten
or loosen admission. Authority moves only in a separate promotion change after
its canaries agree, and that change removes the replaced duplicate predicate.
Exact mode defaults, receipt schemas, semantic objectives, attempt budgets, and
retention rules live only in the three linked owner references above.
