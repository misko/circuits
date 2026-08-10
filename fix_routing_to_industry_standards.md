# fix_routing_to_industry_standards

Bring the routing stage in line with what the literature has settled on: make
one blind gate see its subject, add one provable pre-route bound, and stop
letting a single net's failure cost an unbounded search.

Written 2026-08-02 from measurements on `projects/programmable-usb2-hub`.
**Revision 4** — audited by five independent lenses with adversarial
verification (83 findings survived, 2 refuted) and by a five-angle literature
sweep. Numbers below are post-audit; several in revisions 1–3 were wrong and
are corrected in place with a note.

Status: PROPOSED. Nothing here is landed.

> ### Revision 4 headline: the diagnostic tool had the defect it was built to diagnose
>
> Revision 3 demoted Change 2b (global routing) because a RUDY spike measured
> this board at median tile utilisation 0.11 / p90 0.36 and ρ=+0.264 against
> wave cost — "not congested."
>
> **The spike was broken.** `rudy_spike.py` resolved every net's width inside a
> `try:` whose first statement (`board.FindNet(n).GetNetClass()`) throws on this
> KiCad build, so the `except` assigned `DEFAULT_W + DEFAULT_CLR = 0.18 + 0.15
> = 0.330 mm` to **all 208 nets** — including the 17 that route at 0.5–3.0 mm.
> It measured a board on which every wire is the same thin default.
>
> That is **the same defect as R-POUR**: a tool reading a nominal width instead
> of the real one. Committed inside the instrument built to diagnose it.
>
> Re-run with route-time widths overlaid from `route.yaml`:
>
> | | broken spike | corrected |
> |---|---:|---:|
> | median tile utilisation | 0.11 | **0.39** |
> | p90 | 0.36 | **0.98** |
> | max | 1.09 | **2.20** |
> | tiles over capacity | 12 / 3036 | **282 / 3036** |
> | Spearman ρ (max-RUDY vs wave seconds) | +0.264 | **+0.471** |
> | mean-RUDY on the expensive waves | *lowest* on the board (0.24) | **highest** (1.00–1.37) |
>
> **Change 2b is UN-DEMOTED.** The board is at capacity, RUDY does correlate,
> and the "geometry not congestion" framing of revision 3 was an artifact of my
> own arithmetic. What survives untouched: VIN_PROTECTED still fails the same
> five pads on an empty board, so *that net* is geometry-limited. The board-level
> claim was wrong; the single-net claim was not.
>
> **The transferable lesson is the plan's own thesis, self-inflicted:** before
> believing any measurement, ask what width/denominator the measuring tool
> actually read. A `try/except` that swallows an API mismatch into a plausible
> default is the silent version of a zero denominator.

---

## 0. The finding that organizes everything

The canon **already requires** what the literature recommends. R2 says:

> Width from current (IPC-2152); **power as POURS with priority over GND fill**;
> documented trunk exceptions allowed with margin math — [M] R-POUR

And on the USB hub, R-POUR reads:

```
| R-POUR | PASS | high-current-class nets all poured (0 nets) |
```

**Zero nets.** On a board whose input trunk declares 10 A fused / 6.4 A
continuous. `policy_audit.py:1281` selects high-current nets by
`netclass track_width >= 0.5 mm`, and every power netclass here declares a
0.25 mm **floor**, taking its real width at route time from `route.yaml`'s
`power_nets_widths` (0.5 / 1.0 / 1.5 / 2.5 / 3.0 mm). The gate reads the floor,
finds nothing at or above 0.5, and passes on an empty set.

| netclass | declared `current:` | `required_width_mm` | netclass floor | routed at | R-POUR sees it? |
|---|---|---:|---:|---:|---|
| PWR_IN | 10 A fused / 6.4 A cont. | 7.194 mm @10 A (3.887 @6.4) | 0.25 mm | 3.0 mm | no |
| PWR_5V | 4 A per rail | 2.033 mm | 0.25 mm | 2.5 mm | no |
| SWITCH_POWER | up to 4 A | 2.033 mm | 0.25 mm | **1.0 mm** | no |
| PWR_PORT | 2.0 A | 0.781 mm | 0.25 mm | 1.5 mm | no |

**A second gate already sees this and is already RED.** `rules_audit.py`
(A-AMP) parses the prose `current:` correctly — `parse_amps(...)` returns
`(10.0, 'number')` — and FAILS on PWR_IN. It is simply **non-blocking** and not
wired into the route preflight. So the honest diagnosis is not "no gate sees
it"; it is *one gate is blind and the gate that isn't cannot stop anything.*

Note also **SWITCH_POWER routes at 1.0 mm against a 2.033 mm ampacity floor** —
the largest relative ampacity gap on this board, and nothing in this plan
touches it. Recorded here so it is not silently inherited.

### The consequence, measured

VIN_PROTECTED is routed as a 3.0 mm **trace** to 26 pads. On `r7`:

```
Single-ended:  0/1 routed
Multi-point:   21/26 pads connected (5 FAILED)
Min clearance used: 0.1375 mm (below nominal 0.15)
WALL 45.63 s
```

**Correction to revisions 1–2:** this wave is *not* "zero copper." Measured
`r7 → r8`: VIN_PROTECTED goes 9.8 mm / 2 vias → 111.4 mm / 15 vias. The wave
lays **101.6 mm (93.9 mm of it at 3.0 mm) and 13 vias in those 45.6 s**, and
the last five pads close later at wave 21 `cleanup_input_power`. The net is
expensive and incomplete, not useless. Any claim that deleting the wave is free
must specify what replaces the copper.

**It fails identically on an empty board.** Routed first on track-free `r0`:
the same five pads fail. Two conclusions, the second corrected in revision 4:

1. **For this net the failure is geometry** — zero competing copper, same five
   pads. A static bound computable on the bare board would have caught it. This
   survives revision 4's correction; it is a claim about one net, measured
   directly, not about the board.
2. **Wave ordering is not the cause — and the "7×" was a units error.**
   Revisions 1–3 compared `Total time: 6.30s` on `r0` against `WALL 45.63 s` at
   wave 8. `Total time:` is **KRT's own search counter**
   (`route.py:1467`), not wall clock; the same counter reads **6.20 s** for the
   same net at wave 8 in-chain. Same-clock wall from the artifacts' own mtimes:
   **41.2 s on r0 vs 45.5 s at wave 8 — about 9%, not 7×.** Reordering is
   defensible practice, but it buys far less than claimed.

**And the net is not ultimately unrouted.** At `r24` VIN_PROTECTED carries
145.0 mm and 20 vias and appears in **none** of the 18 unconnected items the
canon DRC gate reports — the last five pads close at wave 21
`cleanup_input_power`. The retry ladder *works*; it is expensive, not broken.
Any claim that deleting `vin_protected_pre` is free must show the replacement
carries all 26 pads.

From `06_build/logs/route-latest.log` (one full chain):

| | count | A* iterations | median |
|---|---:|---:|---:|
| routes found | 70 | 9,931,847 | 19,031 (p90 465,252) |
| routes given up | **42** | **29,641,605** | up to 4,637,949 |

**75% of all search effort is spent failing.** *(Revisions 1–2 said 59% from 11
give-ups — that regex matched only the `(both directions)` subset. The correct
figure is 74.9% over 42 events.)*

Chain total 341.0 s of per-stage medians. The four wide-power waves
(`rail_power` 66.0, `vin_protected_pre` 48.0, `input_recover` 39.7,
`input_power` 23.4) are **177.1 s = 51.9%** on 10 net-slots. `route:signal` is
a further 33.0 s median / 194.9 s max that no change here addresses.

---

## 1. Measured baseline

| quantity | measured |
|---|---|
| recorded stage time, one session | 2745 s over an 87 min wall window; 341.0 s of per-stage medians per chain |
| chain replays | 8–9 for early waves; n falls to 5 across the eight `cleanup_*`, 3 at `final_signal_reconcile`; the five `tail_*` waves have no records (added this session) |
| waves | 29 chained (30 groups defined — `preseeded_usb` is chained by nothing); **12 primary, 17 recover/cleanup/tail** |
| `vin_protected_pre` | 43–52 s, fails every run, lays 101.6 mm + 13 vias, 21/26 pads |
| median / p90 successful route | 19,031 / 465,252 iterations |
| configured `max_iterations` | 500 k – 1.2 M (KRT default 200 k); probe 80 k (default 5 k) |
| per-invocation KRT overhead | 0.77 s — not the bottleneck |
| `route.race` | unset → 1 lane on a 32-core / 188 GB host |
| chain resume | none — `cmd_route` hardcodes `cur = build / prep.out` (:846) |
| board now | 218 footprints, 0 segments; **r24 = 18 unconnected under the canon gate** (`kicad-cli pcb drc --severity-all --refill-zones`), 189 raw pcbnew ratsnest of which 171 are unfilled-GND |
| `route.yaml` | 731 lines, 29 waves, 17 keepout rects (**1 region + 16 per-pad; 6 of the 16 stale**) |

*(Revisions 1–2 reported "189 unconnected" as the board's state. Under the
canon gate — which refills zones — it is **18**. The 189 is a pre-fill artifact.
This materially overstated how far from done the board is.)*

---

## 2. What the literature says

A five-angle sweep (pin accessibility, PCB package escape, global↔detailed
iteration, pre-route predictors, repo archaeology) produced three results that
reshape this plan.

### (a) Per-component difficulty has a name: pin accessibility

The formal per-component notion of "hard to route" is **pin accessibility** —
with published definitions (hit point, access point, access pattern, hit-point
combination), a per-cell criticality predicate, and a production implementation:
OpenROAD's `drt` runs **pin access analysis as its FIRST stage**, exposes a
standalone `pin_access` command, and enforces a floor of **3 access points per
pin**.

Critically, Taghavi et al. (ICCAD'10) state that congestion analysis based on
global routing **does not model pin-access effects at all**. Baek et al.
(ICCAD'22 / TCAD'24) treat pin-accessibility DRVs and congestion DRVs as two
*distinct mechanisms needing two different model classes*. And UCSD (Kahng et
al.) call density-based accessibility estimation "inaccurate, if not
misleading."

**Revision 3 used this to argue our board was pin-access-bound rather than
congested. Revision 4 retracts that.** The corrected spike measures p90 0.98
and 282 tiles over capacity — the board *is* congested. Pin accessibility
remains the right name for the **VIN_PROTECTED** failure (five pads with no
3.0 mm approach on an empty board) and the right frame for a per-component
difficulty score, but it is no longer an explanation for the board as a whole.

Both mechanisms are present, which is what the literature expects: Baek et al.
treat pin-access DRVs and congestion DRVs as **distinct mechanisms needing
different model classes** — so the correct response is to measure both and
classify each failure, not to pick one.

Cypress (ISPD'25, Cornell/NVIDIA) does say RUDY is a flawed proxy **for PCB**,
noting it has **no wire-width term** — which is precisely why feeding it
route-time widths (rather than a netclass floor, or a swallowed default) is
what made it informative here.

### (b) There are provably-correct, cheap, non-density feasibility tests

Two, both PCB-native, both polynomial:

**Single-wire width feasibility.** Ó'Dúnlaing & Yap (1985): a disc of radius
*r* can move between two points among polygonal obstacles **iff** a path exists
along the generalized Voronoi diagram whose clearance is ≥ *r* throughout —
O(n log n). Combined with the widest-path / max-bottleneck result (the
bottleneck path lies on the maximum spanning tree; Camerini 1978, linear time),
this gives per net per layer an exact **w\* = the widest trace that can reach
the target**. A trace of width *w* with clearance *c* is a disc of radius
*w/2 + c*. If w\* < required width, the net is **provably unroutable** and A*
must not be run.

**This is R-FEAS, and it turns out to have a theorem and an algorithm.** It is
not our invention after all — which is better.

**Multi-wire feasibility.** Leiserson & Maley (STOC'85; Maley, MIT Press 1990):
a sketch is routable **iff** it contains no unsafe cut — flow (Σ wire widths +
spacings crossing a cut) must not exceed capacity (gap length minus terminal
radii). Su & Dai (ICCAD'97, the SURF board/MCM system) give the implementable
form on Delaunay edges: `capacity = |edge| − (r₁ + r₂)`, `flow = Σ(width +
clearance)`. Productised and patented (US 5,880,969), stated over *terminals on
a printed-circuit board*. Liu et al. (TCAD 28(2), 2009) build the same over a
constrained Delaunay triangulation with η = Σ(wᵢ+sᵢ)/C.

### (c) Nobody alternates global and detailed routing — and production routers never fail a net

Direct answer to the alternation question: **no**. OpenROAD's `grt` writes
`odb::dbGuide`, `drt` reads it, and ORFS never calls `global_route` after
`detail_route`. The interface is one-directional and traversed once. Guides are
explicitly **soft** (ISPD-2018 FAQ: "Routing guide is a soft rule while
violation is a harder rule"), and OpenROAD's `FlexDR` follows the guide in only
**3 of its 65** scheduled iterations.

Three things *do* alternate, none of them global↔detailed:

1. **Inside detailed routing** — a fixed 65-entry rip-up-and-reroute schedule
   escalating cost and window size (`mazeEndIter` 3→8→16→32→64; DRC cost
   1×→64×).
2. **Global routing ↔ PLACEMENT** — ORFS runs `global_route -start_incremental`
   / `detailed_placement` / `global_route -end_incremental` **2–3× per run**.
   *This* is the real outer loop.
3. **Batch ECO on a deliberately deleted subset** (`editDeleteViolations` then
   `globalDetailRoute`) — never an automatic repair loop.

And the single most important sentence in the whole sweep, Cadence
NanoRoute, verbatim:

> **"The detailed router creates shorts or spacing violations rather than leave
> unconnected nets."**

SPECCTRA/Allegro agrees: "Conflicts are allowed in the escape wire until the
last fanout pass." **Production detailed routers do not return "unroutable" for
a net.** A failure is never a terminal state, so it never costs an unbounded
search. Ours does — which is the direct cause of the 75%.

Global congestion, meanwhile, is a **hard gate that stops the flow** (Cadence:
"If you see congested areas after global routing, your design is unroutable";
OpenROAD errors `GRT-0116`). Nobody asks the detailed router to fix it.

### (d) Placement is where corridor failures are fixed — now with a number

Cheng, Ho & Holtz (UCSD, arXiv:2210.14259) formulate PCB placement as
maximizing margin between net convex hulls. Measured across **14 real PCB
designs routed with FreeRouting and checked in KiCad** — our exact toolchain
family — **79% reduction in DRVs from placement alone.** CLAUDE.md's "a routing
failure is usually a PLACEMENT problem" now has a citable measured number
instead of an assertion.

### What our repo already has (archaeology)

Three per-component routability notions exist, **all at part-selection or
placement, none at routing, none a cost model**:

- **P-ESC/P-TIER** (row P7) — per-package feasibility from four scalars
  (style, pitch, `escapes_worst_side`, npins) against a fab-tier table.
  Deliberately board-blind: no placement, no neighbours, no netlist.
  `escapes_worst_side` is **human-declared in part.yaml and never measured**.
- **P-LAND** (row P8) — per-**pad** launch-width on the placed board (0.03 mm
  grid × 48 directions × 1.0 mm reach). The closest existing thing to "this pad
  has no legal corridor," but it is a 1.0 mm *launch* measure and never rolled
  up per component.
- **P-CAP** (row P10) — a global cut-line demand/capacity sweep. **The repo
  already had a congestion gate**, structurally the same class as the RUDY
  spike, and it would also call this board healthy. Note: `find -name
  placement_gates.json` returns **zero results repo-wide**, so P-CAP has always
  run on defaults — including `layers: 2` on 4-layer boards.

And the hole that matters: **R4's "hardest nets first" is graded `HUMAN`**
(`policy_audit.py:1391`). There is no machine definition of "hardest" anywhere
in the tree, and no per-net cost model — our 19k-vs-4.6M measurement has
nowhere to live.

---

## 3. The plan

**Seven changes** (0, 1, 2a, 2c, 3 with four sub-fixes, 4, 5) plus one measured
and demoted (2b). Each names its owner file, check ID, contract obligation, and
the failure it prevents.

### Change 0 — power routes first (one reordering, measured)

**Where** — `03_src/route.yaml` wave order; principle into `routing-pipeline.md`.

**What** — move power waves ahead of USB. Altium documents it: *"First route or
fan out the power nets. After the power nets, consider the critical signals."*
Our order puts **34 USB net-slots** ahead of the widest net on the board.
*(Revisions 1–2 said 42; the 8 `preseeded_usb` nets are seed-stub sourced and
not part of the chain.)*

**Honestly scoped, twice corrected:** revisions 1–3 claimed a 7× discount on
discovering a failure. Measured same-clock, it is **~9%** (41.2 s on `r0` vs
45.5 s at wave 8) — the 7× compared KRT's internal search counter against wall
time. It is **not a fix** either: VIN_PROTECTED fails the same five pads first
or eighth. Fanout-first is documented tool behaviour in two independent
commercial tools; *"route hard components first"* has no documented backing —
label it an empirical repo rule, not industry practice.

**Gate** — the `wave_order` fixture must ship **with** this change; see §5.

### Change 1 — R-POUR grades DECLARED CURRENT, not netclass width

**Where** — `policy_audit.py:1281-1304`.

**What** — replace the `track_width >= 0.5 mm` selector with the netclass's
`current:`, converted by the calculator already in the tree:
`rules_audit.py:84 required_width_mm(...)`.

**Corrections from revisions 1–2, all three material:**

1. **The prose IS machine-readable.** `parse_amps("10 A fused; 6.4 A calculated
   worst-case…")` → `(10.0, 'number')`. All four hub power classes parse. The
   "not machine-readable" premise was wrong.
2. **`current:` is already REQUIRED** and already bound
   (`templates/contracts/03_src/rules/contracts.md:61` and `:451` → `A-AMP`).
   Nothing "gains" it.
3. **It is IPC-2221A, not IPC-2152.** `rules_audit.py:78` implements
   IPC-2221A (k=0.048 external, b=0.44, c=0.725). R2's row mislabels it and
   must be corrected in the same change.

**The real gaps** are therefore narrower and sharper: (a) R-POUR does not read
`current:` at all, though A-AMP does; (b) the prose form makes a parser take
the **fuse rating (10 A)** rather than the **design current (6.4 A)** — hence
`current_a:` as a typed companion field, with the prose retained as rationale.

**State the numeric threshold.** Revisions 1–2 never did, which left the
selector and the board-level prediction contradicting each other. At §2's
~2.5 mm the in-scope set on this board is **PWR_IN alone (4 nets → 4 zones)**;
PWR_5V and SWITCH_POWER at 2.033 mm fall outside it. Either state 2.5 mm and
drop the 5V prediction, or lower the threshold and accept both — but do not
leave them inconsistent.

**Grades.** `policy_audit.py:86` is `GRADES = ("PASS","FAIL","WAIVED","HUMAN",
"N-A")` — there is no `UNREACHED`. Revisions 1–2 invented one in six places.
The fix: add **`UNGRADED`** to `GRADES` **in the same commit**, because
`parse_report` (:185) counts only rows whose grade cell is in `GRADES` and
`report_inconsistencies` then flags the rest as malformed.

**Zero-denominator conversion is BOUNDED.** `docs/denominator-census.md:5-8`
states that such a change "must produce EXACTLY the conversions listed here and
no others. A conversion this document does not name is a regression." It names
**4 check IDs**: `M-REPRO`, `R-POUR`, `P-KEEP`, `P-POL`. Revisions 1–2 proposed
applying it to "every row that can produce an empty set" — that is a regression
by the census's own rule. Scope to those four.

**Contract obligation** — the `### keys` block for `03_src/rules/nets.yaml`
gains `classes.<C>.current_a → rules_audit.py, policy_audit.py (R-POUR)`;
`current:` is re-worded as rationale, not added. Re-run `schema_reader_audit.py`
(G-ORPHAN). R2's row updated for IPC-2221A.

**Companion, and it is not optional:** nothing in the repo grades a **zone's**
ampacity — `grep -rl 'required_width_mm\|IPC-2221'` returns two files, both
grading *track* widths. Converting a trace to a pour therefore trades a
computed FAIL for an ungraded assumption. Either add a zone-ampacity check
(narrowest neck of the filled polygon per layer, summed across layers, against
`required_width_mm`) or say plainly in §7 that we accept the trade and why.

### Change 2a — R-FEAS: the widest-corridor bound, with a proof

**Where** — new `skills/kicad-pcb/scripts/route_feasibility.py`, called from
`cmd_route` after the R8 tier preflight, same refuse-to-route discipline.

**What** — per net per layer, compute **w\*, the widest trace that can reach**,
via the disc-motion retraction theorem: obstacles = other pads/vias/copper +
keepouts + board outline; a trace of width *w* and clearance *c* is a disc of
radius *w/2 + c*; the answer is the max-bottleneck path on the generalized
Voronoi diagram. A distance transform on a ~0.05 mm raster (130×90 mm =
2600×1800 cells) is adequate and cheap. **Sound** — it fails only where no
corridor exists — and **deliberately incomplete**: passing does not promise the
net routes, and the doc must say so in those words.

**Correction: the soundness contract in revisions 1–2 was unachievable.** Every
power wave sets `neckdown_length: 0.5` (15 occurrences), and PWR_IN's `routing:`
explicitly permits "0.50 mm minimum taps and no more than 0.5 mm of unavoidable
local neckdown." A gate that fires whenever the corridor is narrower than the
*netclass* width would fire on legal, intended geometry. **Bound the gate to the
declared neckdown floor instead**: fire only when w\* is below the neckdown
floor (0.5 mm here), or below the full width for more than the declared neckdown
*length*.

**Findings** — `R-FEAS-NARROW` (names **placement**), `R-FEAS-POUR`,
`R-FEAS-UNREACHED`.

**Ranked remedy printed with the finding**, extending R-SCOPE's precedent:
**pour → re-place → scoped clearance → neck-down with margin math.** Re-placing
now carries a measured number: 79% DRV reduction from placement alone.

**Later, if it earns it:** the multi-wire generalisation — Delaunay cut
capacity `|edge| − (r₁+r₂)` versus `Σ(width + clearance)`. Answers "this board
is not congested but three wide nets want the same gap." Build after the
single-net test, which is cheaper and already catches what we measured.

### Change 2c — bounded failure: a net must never be a terminal outcome

*New in revision 3, and on the evidence the highest-value item here.*

**The finding:** production detailed routers do not fail a net. Cadence:
*"The detailed router creates shorts or spacing violations rather than leave
unconnected nets."* Ours treats "no legal corridor" as terminal and grinds a
flat `max_iterations` budget to exhaustion — **42 give-ups, 29.6 M iterations,
75% of all search effort.**

**Three mechanisms, in ascending cost:**

1. **Window-bounded search.** Bound each net's A* by a *bounding box*, not an
   iteration count. On failure, grow the box by a fixed increment and retry.
   Failure cost becomes O(window) with a bounded growth ladder, instead of a
   flat 900 k–1.2 M every time. TritonRoute does exactly this (7×7 GCell clips,
   adaptive growth when the clip edge is the constraint).
2. **Escalation schedule instead of a flat cap.** Per-pass maze budget and
   violation cost that both escalate — OpenROAD's readable ladder is
   `mazeEndIter` 3→8→16→32→64 with DRC cost 1×→64×. Our 19k-median /
   465k-p90 success distribution says an early pass should cap far below
   today's 900 k.
3. **Bounded deferral.** Cap per-net effort at a small multiple of observed
   success cost, then **defer** the net and retry at most N times (Xu et al.:
   deferring cycle = 3; routability *saturates* with more cycles while runtime
   grows quasi-linearly). This is the principled replacement for our 17-rung
   retry ladder.

**Relationship to Change 3c:** 3c lowers a flat cap; 2c replaces the flat cap
with a schedule. If both land, 2c subsumes 3c — sequence accordingly.

**Prevents** — the 75%. This is the only change that attacks it directly;
Changes 0/1/2a each remove *particular* failures, while 2c bounds the cost of
*any* failure, including ones we have not met yet.

### Change 2b — the congestion map — **UN-DEMOTED in revision 4**

Corrected measurement on this board (route-time widths, 0.21 s):

```
congestion  max=2.20  p99=1.71  p90=0.98  median=0.39
tiles over capacity (>1.0): 282 of 3036
Spearman rho (max-RUDY vs measured wave seconds, n=24) = +0.471
mean-RUDY now ranks the expensive waves TOP:
  input_power 1.37 | input_recover 1.08 | cleanup_input_power 1.06 | vin_protected_pre 1.00
```

p90 of **0.98** against a capacity of 1.0 is a board routing at its limit, and
ρ=+0.471 on n=24 is a real signal. Revision 3's demotion was an artifact of the
spike's own width bug (see the revision-4 headline).

**Step i is therefore justified and cheap** — 188 lines, 0.21 s, router-
independent, renders as an image. Build it as `congestion_triage.py`.

**Steps ii and iii remain gated**, on two grounds that the audit sharpened:

- The `correlation` gate as *specified* in §4.1 (two real boards; tiles the map
  calls congested must contain the nets that actually **failed**; threshold
  agreed beforehand) still **has not been run**. What we have is n=1 against
  wave *cost*. Revision 3 claimed the gate "fired exactly as designed" — it did
  not, and the corrected numbers show how much rode on that.
- Step ii's premise was wrong anyway. See Change 5: 16 of the 17 rects are
  per-pad via reservations ~0.6 × 0.65 mm, and a capacity map calls a 0.4 mm²
  pad-site reservation "slack to spare" **by construction**. `R-GLOBAL-KEEPOUT-
  DEAD` would have deleted correct reservations.

**Cross-check available for free:** the repo's own **P-CAP** (row P10) is a
global cut-line demand/capacity sweep — the same class of measure. It has never
been configured (`find -name placement_gates.json` → zero results repo-wide, so
it has always run on defaults including `layers: 2` on a 4-layer board).
Configuring P-CAP and comparing it against the corrected RUDY map is a
two-independent-methods check (canon M1) that costs almost nothing.

### Change 3 — routing economics: resume, race, caps, buffering

**3a. Chain resume.** `cmd_route` hardcodes `cur = build / prep.out` (:846).
Add `--from rN`. Measured saving on this session's exact event: 24 of 29 waves.

**3b. `race` from measurement, not from 1.** Mechanism exists and is auditable
(`race_log.json`). Unset → one lane on 32 cores. **Worthless until Changes 1
and 2a remove the deterministic failures.** Note: `route.race` is **already
bound** in the contract (`03_src/contracts.md:435`) — 3b sets a *value*, not a
schema.

**3c. Iteration caps derived, not chosen** — superseded by 2c if 2c lands.

**3d. Line-buffer the orchestrator.** All 29 wave headers land at the *end* of
the log (wave 1's router output at line 46, its header at 10087). `flush=True`.
Not log hygiene — it restores the only real-time feedback channel the human in
this loop has.

**Contract obligation** — the `### keys` block gains the derived-cap keys only;
`skills/pcb-design/SKILL.md` §4-6 gains the resume verb.

### Change 4 — name the retry ladder, then shrink it

Census of primary vs `recover`/`cleanup`/`tail`/`reconcile` waves — **17 of 29**
here. **Correction:** report it with a grade cell drawn from `GRADES` (`N-A`
when no ladder waves exist, `PASS` under a declared ceiling, `FAIL` above it)
and the ratio in the Detail cell. A bare number in the Grade cell is invisible
to `parse_report` — the same defect as Change 1's `UNREACHED`.

**The ceiling and its date ARE the policy.** The repo has ratchet floors and no
ceilings; a declared-but-uncapped number costs nothing and drifts forever.

### Change 5 — delete what the fixes make dead

**Correction:** revisions 1–2 keyed keepout removal on `R-GLOBAL-KEEPOUT-DEAD`,
emitted by step ii of the **demoted** Change 2b — a dangling dependency. Use the
empirical test instead.

**The keepouts are two different things, and revisions 1–3 treated them as one.**
`route.yaml:44-66` holds **1 region-level exclusion rect** (25,79)-(147,106) on
User.3, "USB-only exclusion over all three switching-power islands" — plus
**16 per-pad seed-stub via reservations**, each ~0.6 × 0.65 mm, each naming one
pad, reserving "the only legal 0.25/0.15 mm via sites" for GND escapes. Only the
first is a corridor guess; the other 16 are deliberate and load-bearing.

**Measured, and this is a live board defect rather than a documentation one:
6 of the 16 are stale.** `C432`, `C207` and `C211` are **not on the board at
all**; `C422.2`, `C32.2` and `C201.2` sit **17.7 / 27.8 / 30.2 mm** from the pad
they name (C201 pad 2 is at 115.40, 71.72; its rect centre is 133.30, 96.00).
Six reservations are protecting empty space while six real pads are unprotected.

**That audit needs no congestion map and no new theory** — it is a join between
`route.yaml`'s rect comments and `pcbnew`'s pad positions. It is the highest
value-per-line item the audit surfaced, and it should be its own small gate.

| target | removal test |
|---|---|
| retry/cleanup/tail waves | remove, re-run, keep the removal if unconnected does not rise |
| the 6 stale pad reservations | the refdes is absent, or the rect centre is > 1 mm from the pad it names — delete or re-derive |
| the 1 region-level rect | empirical test; may be graded by the congestion map once step ii is earned |
| per-wave iteration caps | subsumed by 2c's schedule |
| dead wave definitions | any wave whose net set is empty on every board |

**The 10 correct pad reservations are not deletion targets.** They should be
*generated* from `seed_stubs` rather than hand-typed, which removes the whole
staleness class instead of fixing six instances of it.

> **This plan is not done until `route.yaml` is SHORTER.** Baseline: **731
> lines, 29 chained waves (30 groups defined), 17 keepout rects.**

---

## 4. Testing plan

Per `tests/README.md` — and **corrected**: revisions 1–2 used `vacuity`
backwards. The contract reads: *"`vacuity` | the checker **PASSES** input whose
graded fact is FALSE — a declared blind spot (canon G-VACUOUS)."* Three rows
labelled `vacuity` asserted the gate must **not** pass; those are `known_bad`
rows. Every suite needs a real vacuity row naming a genuine blind spot.

**RED-first is scoped.** CLAUDE.md ties it to fixing a bug in an *existing*
gate. It applies to **Change 1 only** (`git show HEAD:…policy_audit.py`;
`known_bad_floor` must PASS against it). R-FEAS and 2c are new code with no
pre-fix bytes; each fixture instead carries an inline statement of what it
would have caught.

**Fixtures must name their oracle.** `tests/README.md` (:290-338) lists three
legal oracles — pinned commit `git show <sha>:<path>`, sealed release
`07_releases/<rel>/source/…`, or a live board only where the assertion
tolerates re-routing. Revisions 1–2 named real boards and no oracle in three
rows; all three now read from sealed releases or pinned shas, never live
`04_kicad/`.

| suite | change | load-bearing fixture |
|---|---|---|
| `t1_policy_pour.py` | 1 | `known_bad_floor` — the exact hub shape (`current_a: 6.4`, `min_width: 0.25`) must **FAIL**, and must **PASS** against `HEAD`'s policy_audit |
| `t1_route_feasibility.py` | 2a | `soundness` — zero false positives over four routed boards read from **sealed releases**, graded against the **neckdown floor**, not the netclass width |
| `t1_route_budget.py` | 2c | `failure_is_bounded` — a provably unroutable net costs ≤ K× the median success, and the router still **commits** a recorded conflict rather than returning unrouted |
| `t1_route_economics.py` | 0, 3 | `wave_order`, `resume_stale`, `race_audit`, `buffering` |
| `t1_route_deletion.py` | 5 | `recipe_shrinks` — machine-checks §4.3's own success criterion |
| `t1_global_route.py` | 2b | **DEFERRED** — written only if a board earns 2b |

`t4_regressions.t_every_suite_propagates_and_is_wired_in` asserts every `t*.py`
is registered in `run_tests.sh` — five suites now, not four.

**Contract note:** `skills/kicad-pcb/scripts/contracts.md` has no per-script
allow-list (patterns only: `*.py`, `*.sh`), so "gains a script entry" is not the
obligation. The real obligation is that folder's `## Audit`: docstring purpose +
usage, clean and known-bad fixtures, G-INPUT (name the artifact), G-COVER
(`N/M` denominator).

### 4.2 Fleet regrade

**Correction:** `tests/t1_fleet_regrade.py` is the suite for
`skills/kicad-pcb/scripts/fleet_regrade.py`, which runs **four release gates**
(F-PAYLOAD, F-LEGIBLE, A-EVID, A-POP) over `projects/*/07_releases/*/` and never
invokes `policy_audit`. It is **not** a policy sweep and cannot be reused as
one as written. Either extend it or write the sweep; do not assume it exists.

Change 1 will turn R-POUR red on boards passing vacuously — that is the change
working. Publish the per-board table into `docs/denominator-census.md` (which
already governs exactly this conversion) **before** landing.

### 4.3 Performance acceptance

| metric | baseline | target | how measured |
|---|---:|---:|---|
| give-up share of iterations | **74.9%** | < 20% | `route-latest.log` parse |
| cost of one give-up | up to 4,637,949 iters | ≤ 10× median success (190 k) | 2c |
| `vin_protected_pre` | 48.0 s median, 21/26 pads | replaced by a pour **whose copper is specified** | `performance.json` |
| full chain, race:1 | 341.0 s | state the lever or drop the target | `performance.json` |
| unconnected at chain end | **18** (canon gate, refilled) | 0 | `kicad-cli … --refill-zones` |
| congestion p90 (route-time widths) | **0.98**, 282/3036 tiles over capacity | falling | `congestion_triage.py` |
| ladder ratio | 17/29 | reported under a dated ceiling | `R-LADDER` |
| `route.yaml` | 731 lines / 29 waves / 17 rects | strictly smaller | `t1_route_deletion.recipe_shrinks` |

**None of these may buy speed with connectivity.** The unconnected row governs.

---

## 5. Sequencing

```
Change 5-stale (6 dead keepout rects)  ── a live board defect; today, standalone
Change 3a/3d (resume, buffer)         ── cheap; 3d restores live feedback
Change 2b-i (congestion map)          ── 188 lines, 0.21 s, now justified (rho +0.471)
Change 2c (bounded failure)           ── attacks the 75% directly; supersedes 3c
Change 1  (R-POUR reads current)      ┐
Change 2a (R-FEAS bound)              ┴─ both before 3b
Change 0  (power first)               ── ~9% not 7x; ships WITH its wave_order fixture
Change 3b (race)                      ── only after the deterministic failures are gone
Change 4  (R-LADDER + ceiling)        ── after 2c, to measure the effect
Change 5  (delete what died)          ── after EACH of the above
Change 2b-ii/iii (keepout grading, guides) ── still gated on the SPECIFIED
                                             correlation gate (two boards,
                                             failures not wave-cost)
```

**Why the stale keepouts jumped to the front:** they are the only item that is a
defect in the *board* rather than in a gate or a document, they cost one join to
find, and six of them are currently protecting empty space.

**Why Change 0 dropped:** measured at ~9%, not 7×. Still correct practice, no
longer urgent.

**Why 2c moved up:** it is the only change that bounds the cost of failures we
have not met yet. Changes 0/1/2a each delete one known failure; 2c makes the
*next* one cheap. On the measured evidence (75% of effort, 42 events) it has the
largest single payoff.

**Why 1 and 2a precede 3b:** parallelism multiplies whatever the chain does,
including failing identically eight times.

---

## 6. Board-level consequence

**Corrected.** Revisions 1–2 claimed Change 1 removes `vin_protected_pre` *and*
`rail_power`, "112 s of the ~340 s chain." Measured: 5V_A/5V_B route at 2.5 mm
against a 2.033 mm ampacity floor — **already compliant**, and outside a 2.5 mm
pour threshold. `rail_power`'s 66.0 s is **not** removable on this argument.

The honest figure is **48.0 s of the 341.0 s chain**, and only if the
replacement pour is specified: which layer, what region, what priority against
the GND zone, and what it does to the declared-unbroken In1 USB reference. A
pour that breaks the USB reference plane trades an R-POUR finding for an R3 one.

---

## 7. Risks

- **R-POUR turning red across the fleet.** Mitigated by §4.2 before landing.
- **Zone ampacity is ungraded.** Change 1 converts a computed A-AMP FAIL into an
  ungraded assumption unless the companion check lands. Stated, not hidden.
- **R-FEAS false positives.** Mitigated by grading against the neckdown floor
  and by `soundness` over sealed releases. If it ever cries wolf, revert — do
  not add a tolerance knob.
- **2c changing what the router produces.** Unlike every other change here, 2c
  alters routing *output*: committing a recorded conflict instead of leaving a
  net unrouted. The unconnected-vs-violations trade must be measured, and DRC
  findings stay CLASSIFIED, never counted.
- **`current_a:` churn** across every project's `nets.yaml`. Real, unavoidable.
- **Change 2b decorating — REALISED and acted on.** The spike produced a
  plausible picture at ρ=+0.264; it was demoted rather than tuned. Kept here as
  the worked example, not a prospective risk.
- **P-CAP has never been configured.** No `placement_gates.json` exists
  repo-wide, so it has always run on defaults including `layers: 2` on 4-layer
  boards. Out of scope here, but it means the repo's existing congestion gate is
  uncalibrated — do not cite it as corroboration without fixing that first.

---

## Appendix: files touched

| file | change |
|---|---|
| `skills/kicad-pcb/scripts/policy_audit.py` | R-POUR selector; `UNGRADED` added to `GRADES` (:86); R-LADDER row with a legal grade cell |
| `skills/kicad-pcb/scripts/route_feasibility.py` | new — R-FEAS (disc-motion / widest-path) |
| `skills/kicad-pcb/scripts/congestion_triage.py` | new — the 188-line RUDY spike as a triage tool, not a gate |
| `skills/kicad-pcb/scripts/route_and_stitch_generic.py` | `--from`, R-FEAS call, `flush=True`, 2c window/escalation/deferral |
| `skills/kicad-pcb/references/design-policies.md` | R2 → IPC-2221A; R4's `[H]` → a machine key if Change 0 gains one; new R-FEAS row; R-LADDER + ceiling |
| `skills/kicad-pcb/references/routing-readme.md` | new — the WHY document; **must carry the SPIKE RESULT before promotion** (it currently still says "RUDY is the one to reach for first") |
| `examples/routing-economics-2026-08/` | new — PROVENANCE.md + the log excerpt and `route.yaml` waves the WHY document cites (C-ISO: skills may not cite `projects/` paths) |
| `skills/pcb-design/templates/contracts/03_src/rules/contracts.md` | `### keys` gains `classes.<C>.current_a` |
| `skills/pcb-design/SKILL.md` §4-6 | resume verb, feasibility stage |
| `tests/t1_policy_pour.py`, `t1_route_feasibility.py`, `t1_route_budget.py`, `t1_route_economics.py`, `t1_route_deletion.py` | new — register all five |
| `tests/t1_global_route.py` | deferred (2b demoted) |
| `docs/denominator-census.md` | R-POUR fleet table, bounded to the 4 named check IDs |

This file is untracked at repo root. **`lipo3s_trace.md` is not a precedent** —
it is gitignored (`.gitignore:5`) and therefore outside the audit's universe.
The precedent is `resume_state.md`: tracked, with its own row in the root
`contracts.md` `## Allowed` table (canon M7).
