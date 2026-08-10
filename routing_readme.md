# routing_readme

Why our routing stage is shaped the way it is, what the literature says, and
how routing actually fails here.

Companion to `skills/kicad-pcb/references/routing-pipeline.md` (the HOW — the
canonical steps, in order) and `design-policies.md` (the RULES — the R-family
check IDs). This document is the WHY. Where the three disagree,
`design-policies.md` governs.

Written 2026-08-02. Measured numbers come from `programmable-usb2-hub` unless
stated; each is reproducible from the artifact named beside it.

Intended home: `skills/kicad-pcb/references/`. It sits at repo root untracked
until it lands, matching the `lipo3s_trace.md` precedent; landing it requires
the folder's kebab-case convention (`routing-readme.md`) and nothing else —
the references contract already allows `*.md`.

---

## 1. What routing is, and why it is hard

A board is a few hundred electrical connections that must become copper.
Copper on the same layer cannot touch unless it is the same net. So the router
plays a maze game: for each connection, find a path from pad A to pad B through
whatever space the already-drawn copper has left. Every path drawn makes the
board harder for the next one.

The asymmetry that governs everything below:

> **Finding a path is cheap. Proving no path exists is brutally expensive.**

Measured on our own board, from `06_build/logs/route-latest.log`:

| | count | A* iterations | median |
|---|---:|---:|---:|
| routes found | 70 | 9,931,847 | 19,031 |
| routes given up | 11 | 14,309,756 | up to 4,637,949 |

A success costs ~19 k search steps. A failure costs up to 4.6 M — **240×** —
because the router exhausts its forward budget, then its backward budget, then
probes, then rips up and retries. **59% of all search effort went into paths
that do not exist.**

This is not a KRT defect. It is the shape of the problem, and it is why the
whole field organizes routing the way it does.

## 2. The two-stage architecture, and where we sit against it

Every mature routing flow — chip, FPGA, and commercial PCB — splits routing in
two:

**Global routing** partitions the board into coarse tiles (GCells), computes
each tile boundary's *capacity* (how many tracks physically fit), assigns every
net a coarse tile-to-tile path (*demand*), and reports where demand exceeds
capacity (*overflow*). It is fast and approximate. It produces two outputs: a
**congestion map** and a set of **routing guides**.

**Detailed routing** then draws real geometry, following those guides.

The purpose of the split is explicitly early failure detection:
congestion awareness "at an early design stage is of great importance to
provide fast feedback and shorten design cycles," and the coarse grid "speeds
up the process of finding the net routing solutions… by reducing the number of
pathways to consider" [1]. Overflow is the primary scored metric in the ISPD
global-routing contests [2]. Intel ships a *Global Router Congestion Hotspot
Summary Report* as a first-class tool output [3]. On the detailed-routing side,
the ISPD-2018/2019 contests define the task as: *given route guides from global
routing*, produce geometry "honoring the route guides as much as possible" —
which is how TritonRoute and every modern detailed router are specified [4][5].

### What we actually have

We do not lack global routing. **We have a manual, unaudited version of it**,
and naming it honestly is the point of this section:

| global routing does | our equivalent | audited? |
|---|---|---|
| tile the board, compute capacity | — | no |
| compute demand, report overflow | — | no |
| produce a congestion map | — | no |
| produce **positive** guides (go this way) | nothing — `--guide-corridor` exists in KRT and is used **nowhere in this repo** | n/a |
| produce **negative** guides (not here) | **18 hand-typed keepout rectangles** in `03_src/route.yaml`, with comments like `# U13.2`, `# C426.2` | no |
| order nets to reduce contention | 29 hand-authored `waves`, ordered by hand | no |

So a human reads the board, guesses where the congestion is, types coordinates
into YAML, and the detailed router discovers the rest by exhaustive search.
That is global routing performed by a person, in the negative, without capacity
or demand accounting — and it is why the failures in §5 are the failures we get.

The gap is not that the idea is unavailable to us. KRT accepts guide polylines
drawn on a User layer (`--guide-corridor`, `--guide-corridor-layer`,
`--guide-corridor-spacing`). We have simply never generated them.

### The concrete algorithms, cheapest first

Global routing is a family, not one algorithm, and the cheap end is very cheap.
In ascending order of cost and fidelity:

| tool | what it needs | what it gives | cost |
|---|---|---|---|
| **RUDY** (Rectangular Uniform wire DensitY) [12] | placement only — net bounding boxes | a congestion *estimate*, renderable directly as an image | very low CPU, no search |
| **Steiner trees** (FLUTE-style, congestion-driven) [13] | placement + a congestion map | coarse per-net topologies | cheap |
| **FastRoute** [13] — OpenROAD's `grt` [14] | the above + tile capacities | guides, congestion report, overflow | moderate |
| **Negotiated congestion** (PathFinder) [11] | full resource graph | a *converged* legal solution | expensive |

RUDY is the one to reach for first, and its properties explain why: it
"depends neither on a bin structure nor on a certain routing model… therefore
RUDY is independent of the router" [12]. That independence is not a
convenience — it satisfies canon M1 directly, because an estimator built on
the router's own model would be grading itself. It also "needs very low CPU
time" and "can be directly represented as images."

Its limitation is stated just as plainly in the same source: it only
*partially* correlates with real congestion. Treat it as an instrument with a
known error bar, never as a verdict.

FastRoute's central result is worth internalising even if we never implement
it: congestion-aware Steiner tree *topologies* remove most of the need for
expensive maze search, so maze routing is applied "to a small percentage of
the two-pin nets" [13]. That is the same economics as §1 — cheap structure
first, expensive search only on the remainder — one level up the hierarchy.

The reference interface to copy, if we ever build the full stage, is
OpenROAD's `grt` [14]: `global_route -guide_file` for guides,
`-congestion_report_file` for the map, and
`set_global_routing_region_adjustment` to reduce capacity in a named region —
which is the principled version of our 18 hand-typed keepout rectangles.

### Why we have a human in the loop, and what they are missing

Every source on PCB routing agrees autorouting is "a niche helper inside a
broader human-led process" [15][16][17]: professionals route critical nets
interactively and automate the leftovers. **We have that human — it is Claude.**
The hand-typed keepouts and hand-ordered waves in §2 are not a hack around
missing automation; they *are* the industry pattern.

What is missing is not the designer. It is the **instrument panel**. A designer
in Altium sees a live ratsnest, a congestion map, and push-and-shove feedback
under the cursor. Our loop sees a text log — one that is block-buffered, so
every wave header arrives *after* all 10,000 lines of router output (F1, and
`fix_routing_to_industry_standards.md` Change 3d).

This is the strongest single argument for building the congestion map: not to
replace the judgement calls, but to stop making them blind.

### The honest scope limit on borrowing this

Almost all of the literature above is VLSI and FPGA, not PCB. Chips have
gridded, uniform routing resources and millions of nets; we have arbitrary
outlines, through-hole parts, mixed trace widths, thermal relief and a few
hundred nets. The concepts transfer; the algorithms do not, unmodified.

The number that should govern how much we trust any congestion estimate:
published ML congestion predictors reach ~90% accuracy against *global* routing
but drop to **~60% against actual detailed-router congestion** [6]. That is
the state of the art, on the domain the state of the art was built for. It is
why anything we build here should prefer a **bound** (provably true, possibly
silent) over a **prediction** (often right, occasionally confidently wrong).
This repo already has the pattern: `R-LEN-OCT` computes the octilinear length
floor from pads alone, with no copper, no stackup and no router.

## 3. Why power is a pour and not a trace

The single most consistent piece of industry guidance we found, and the one
with the clearest local consequence.

Past roughly 5–10 A, or ~2.5 mm of width, you stop drawing traces and start
pouring copper. Altium's routing guidance lists among the things to determine
before routing "the current carrying capacity of traces, as high current boards
can require large traces **or even polygons**" [7]; fab-house PDN guides say
the same, adding the secondary benefits — lower inductance, heat spreading, EMI
shielding, better surge behaviour [8][9].

Our canon already says it. R2:

> Width from current (IPC-2152); **power as POURS with priority over GND fill**;
> documented trunk exceptions allowed with margin math — [M] R-POUR

And `routing-pipeline.md` Step 0 says "Plan >1A trunks as priority-N F.Cu
pours, not tracks."

**It is still the defect we shipped.** See §5, F2 and F3.

## 4. Overview of our routing step

Six stages. The ordering is load-bearing; each deviation reintroduces a failure
that was already paid for once.

| # | stage | what it does | why it exists |
|---|---|---|---|
| 0 | **rules** | netclasses + IPC-2152 ampacity width floors + via rules written into the routing-input `.kicad_pro`/`.kicad_dru` | canon R1. Without floors first, every later pass is graded against Default 0.2 mm. `generate_rules` also runs **LAST**, because pcbnew saves clobber netclasses |
| 1 | **tier preflight** | proves every routing/stitch parameter agrees with the declared fab tier — 0 FAIL — before a single KRT cycle | canon R8. Four unexamined tool defaults were ~60% of one board's routing stage |
| 2 | **prep** | track-free unfilled board, keepouts, deterministic seed stubs, GND pad rescue | KRT mis-parses filled zones and pcbnew-dialect tracks and will route straight through existing copper. Seeds reserve plane drops before routing consumes the only legal via sites |
| 3 | **waves** | 29 sequential KRT invocations, `r0 → r1 → … → r29`, each routing a named net group | hardest-first; and net ordering is the only contention control we have (see §2) |
| 4 | **stitch** | via stitching, zone fill, island rescue, T-junction splitting, dangling pruning | KRT's tally is not the truth; connectivity is only real after fill |
| 5 | **gate** | `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity` = 0 violations / 0 unconnected / 0 parity | canon R7. **Both halves.** The unconnected half is the one that gets summarised instead of classified |

Two properties of stage 3 that shape everything:

- **KRT is stochastic.** Two runs of the same board differ measurably. This is
  why `race: N` exists (N concurrent chains, keep the measured best, selection
  logged to `race_log.json`) and why any published length number needs
  `R-LEN-PIN` to catch a silent re-route.
- **KiCad has no autorouter.** Nor does anything else usable: freerouting was
  tested exhaustively and rejected, DeepPCB does placement but not routing.
  See `autorouter-landscape.md`. KRT is the only detailed router in the stack,
  which is why its cost model is our cost model.

## 5. Common failure modes

Each entry: the symptom, the real cause, **the question that distinguishes
them**, and a measured instance. These are ordered by how often they have
actually bitten, not by severity.

### F1 — "The router is slow"

**Almost always:** a net that cannot be routed is spending its full iteration
budget proving it. Speed is a *symptom of infeasibility*, not a tuning problem.

**Diagnostic:** does the wave take the *same* time every run? A stochastic
router that produces the identical duration eight times is not searching — it
is exhausting a cap. Compare per-net time against the median success.

**Measured:** `vin_protected_pre` — 1 net, `43 45 46 48 48 50 51 52` s across
eight runs, 0/1 routed, 5 of 26 pads unconnected, and `min clearance used
0.1375 mm` (already below the 0.15 nominal, i.e. no headroom existed to find).
Four wide-power waves were 180 s of a 340 s chain — **53% of routing time on 10
net-slots.**

**Do not:** raise `max_iterations`. Our caps are already 500 k–1.2 M against
KRT's 200 k default, and 80 k probe against its 5 k, while the median
*successful* route takes 19 k iterations and p90 is 465 k. Raising the cap buys
almost no real routes and pays full price on every failure.

### F2 — Fat power routed as a trace

**Symptom:** one power net dominates routing time, or refuses to complete.

**Cause:** the net is past the width where trace routing is the right tool
(§3). A 3.0 mm trace to 26 pads across 29 mm is not a routing problem.

**Diagnostic:** what is the net's declared current, and does it have a zone?

**Measured:** VIN_PROTECTED, declared `current: "10 A fused; 6.4 A calculated
worst-case continuous input at 12 V"`, routed as a 3.0 mm trace.

### F3 — A gate that is blind to its own subject

**The repo's dominant defect shape.** A gate reports PASS because its *input
set was empty*, and nothing prints the denominator.

**Diagnostic — always ask this:** *how many items did the gate actually grade?*
A PASS with no denominator is not evidence.

**Measured:** `| R-POUR | PASS | high-current-class nets all poured (0 nets) |`
on the board in F2. `policy_audit.py:1281` selects high-current nets by
`netclass track_width >= 0.5 mm`; every netclass on that board declares a
0.25 mm **floor** and receives its real width at route time from
`route.yaml`'s `power_nets_widths`. So the gate that exists to require F2's fix
was structurally incapable of seeing it — including on the netclass declaring
10 A.

Related, same shape, elsewhere in the canon: `jlc_twin` exited 0 on 11
unverified parts; R-LEN passed a board for its whole history on the *word*
"length" appearing in a comment about a creepage slot.

### F4 — A placement problem filed as a routing problem

**Symptom:** unconnected nets after a full chain; the instinct is to tune the
router.

**Cause:** the parts are where they are. Routability-driven placement is an
entire research subfield precisely because placement decides whether routing
can succeed [6][10]. (The commonly-quoted "80% of routing success is
placement" is vendor folklore with no study behind it — cite the subfield's
existence, not the number.)

**Diagnostic:** measure net span lengths *before* touching router parameters.
And ask whether a legal geometry exists at all — that is arithmetic, not
search.

**Measured, pluto-rx2-8way:** 28 unconnected were summarised as "MCU-field
congestion." Classified, they were four unrelated problems, and **18 of the 28
were two config lines** — a `mounting_holes` keepout with no refdes filter
stamping over a connector's own alignment pegs, and a keepout rect containing
the switch endpoints. Only 8 were at the MCU, and those were arithmetic: at
0.400 mm pitch a 0.250 mm via leaves 0.175 mm against a 0.200 mm floor, so no
legal via-in-pad exists. Not congestion at all.

### F5 — Counting instead of classifying

**DRC violations AND unconnected items are CLASSIFIED, never counted.** The
unconnected half is the one that gets summarised. In F4 that summary travelled
through three agent briefs and a user report over several hours before anyone
classified the 28.

### F6 — The retry ladder that only grows

**Symptom:** the wave list keeps getting longer; each new failure adds a
`_recover` / `_cleanup` / `_tail` wave.

**Cause:** we route nets one at a time in a fixed order and give up on the
losers, then add a pass to mop up. The field's answer is **negotiated
congestion** (PathFinder [11]): route everything, allow illegal overlap, then
make contested resources progressively more expensive with a *historical* cost
term until the solution is legal. It converges; a hand-grown ladder does not.

**Measured:** **17 of 29 waves** on this board are recover/cleanup/tail/reconcile
passes. Every chain replay pays for all of them from `r0`, because
`cmd_route` hardcodes its start at `prep.out` and cannot resume.

### F7 — Tool config disagreeing with the declared fab tier

**Cause:** an unexamined tool default is config. A default that disagrees with
the tier is the same defect as an explicit wrong value, only harder to see.

**Measured:** four unexamined defaults on crow-recorder-central-v2 = ~60% of
that board's routing stage. And a green preflight is not enough on its own —
`PF-ROUTE-CLR` read `route.common.clearance` and never `route.waves[]`, so a
wave overriding to 0.14 under a 0.2 mm floor printed *"0 FAIL — config is
tier-consistent"* and then routed 49 clearance findings.

**Diagnostic:** a gate must read **every** place its value can be set. Ask
which keys the checker actually opened.

### F8 — Rules present, silently unenforced

**Cause:** a `.kicad_dru` rule conditioning on a netclass the `.kicad_pro` does
not define, or an `insideArea()` not on the board, enforces nothing while
reading as enforcement — and DRC still reports 0.

**Measured:** crow-mic-pod-v2 v1.0 — 2 of 4 DRU rules dead; the board carried 3
tracks 0.0002 mm under the floor the dead rule named, at DRC 0/0/0. Fleet
sweep: 3 boards affected.

### F9 — Re-running KRT on an imported pcbnew board

KRT mis-parses filled zones and pcbnew-dialect tracks and routes straight
through existing copper — 400+ crossings observed twice. Repair passes run on
the **KRT-dialect chain file**, never the imported board.

### F10 — Escape geometry that no router can satisfy

A 0.4 mm-pitch peripheral QFN cannot be fanned out or routed between pads at
any legal geometry. This is a **package** problem checked at part selection
(P-ESC / P-TIER), not a router problem. Tuning will not fix it; a larger
package will.

### F11 — A re-route silently invalidates a published number

KRT is stochastic, so any artifact that publishes a measured copper property
(a length delta, a phase) becomes fiction the moment the board is re-routed.
`R-LEN-PIN` exists to fail exactly this.

### F12 — Serial replays instead of concurrent ones

**Symptom:** "we ran it eight times and picked the best."

**Cause:** `race` unset → 1 lane. Measured: 8–9 sequential chain replays,
2745 s of recorded stage time in an 87-minute window, on a **32-core** host.

**But fix F1/F2 first.** Racing a deterministic failure discovers the same wall
N times in parallel. Concurrency multiplies whatever the chain does.

### The two questions worth asking first

1. **What is the denominator?** (F3 — before believing any PASS.)
2. **Is this time being spent finding something, or proving something isn't
   there?** (F1 — before touching any router parameter.)

## 6. Sources

Industry / vendor guidance:

- [7] [Altium — PCB Routing](https://resources.altium.com/p/pcb-routing) — current capacity, "large traces or even polygons"; [Altium — Situs Topological Autorouter](https://resources.altium.com/p/automated-pcb-routing-with-situs-topological-autorouter) — pre-route and lock critical nets
- [8] [JLCPCB — Power Distribution Network Design Guidelines](https://jlcpcb.com/blog/power-distribution-network-design-guidelines); [JLCPCB — Track Width vs Current Capacity](https://jlcpcb.com/blog/track-width-vs-current-capacity-pcb-layout-tips)
- [9] [PCBWay — PCB Layout Design Guidelines: Placement and Routing](https://www.pcbway.com/blog/PCB_Design_Layout/PCB_Layout_Design_Guidelines_Placement_and_Routing_e5aad1e8.html)
- [3] [Intel — Global Router Congestion Hotspot Summary Report](https://www.intel.com/content/www/us/en/docs/programmable/683236/23-4/global-router-congestion-hotspot-summary.html)
- [Sierra Circuits — Autorouting in KiCad using FreeRouting](https://www.protoexpress.com/blog/how-to-autoroute-pcb-layout-in-kicad-using-freerouting-plugin/)

Academic:

- [1] [Chen & Chang — Global and Detailed Routing (EDA textbook chapter)](https://cc.ee.ntu.edu.tw/~ywchang/Courses/PD_Source/EDA_routing.pdf); [ScienceDirect — Routing Congestion overview](https://www.sciencedirect.com/topics/computer-science/routing-congestion)
- [2] [ISPD 2008 Global Routing Contest](http://www.ispd.cc/contests/08/ispd08rc.html); [ISPD24 Contest — GPU/ML-Enhanced Large Scale Global Routing](https://liangrj2014.github.io/ISPD24_contest/)
- [4] [Kahng, Wang et al. — TritonRoute: An Initial Detailed Router for Advanced VLSI Technologies](https://dl.acm.org/doi/10.1145/3240765.3240766)
- [5] [ISPD 2019 Initial Detailed Routing Contest and Benchmark with Advanced Routing Rules](https://dl.acm.org/doi/10.1145/3299902.3311067)
- [6] [ACM TRETS — Novel Congestion-estimation and Routability-prediction Methods based on Machine Learning](https://dl.acm.org/doi/fullHtml/10.1145/3337930)
- [10] [arXiv — Generalizable Cross-Graph Embedding for GNN-based Congestion Prediction](https://arxiv.org/pdf/2111.05941)
- [11] [McMurchie & Ebeling — PathFinder: A Negotiation-Based Performance-Driven Router for FPGAs](https://dl.acm.org/doi/10.1145/201310.201328)
- [12] [Spindler & Johannes — Fast and Accurate Routing Demand Estimation for Efficient Routability-driven Placement (RUDY)](https://past.date-conference.com/proceedings-archive/2007/DATE07/PDFFILES/08.7_1.PDF)
- [13] [Pan, Xu & Chu — FastRoute: An Efficient and High-Quality Global Router](https://onlinelibrary.wiley.com/doi/10.1155/2012/608362)
- [14] [OpenROAD `grt` — global routing module (FastRoute-based)](https://github.com/The-OpenROAD-Project/OpenROAD/blob/master/src/grt/README.md)
- [Shojaei, Davoodi & Linderoth — Planning for Local Net Congestion in Global Routing](https://jlinderoth.github.io/papers/Shojaei-Davoodi-Linderoth-13-PP.pdf)

On human-led routing (the framing in §2):

- [15] [Altium — Hand Routing vs Using an Automated Router](https://resources.altium.com/p/hand-routing-vs-using-an-automated-router-why-auto-interactive-routing-is-the-ideal-pcb-design-solution); [Altium — Routing the PCB](https://www.altium.com/documentation/altium-designer/pcb/routing?version=22) (power nets first, then critical signals)
- [16] [911EDA — Pros & Cons of Autorouters](https://www.911eda.com/solutions/pros-cons-of-autorouters-in-pcb-design-explained/); [Autocuro — Why PCB Autorouting Remains Broken](https://autocuro.com/blog/why-pcb-autorouting-remains-broken)
- [17] [KiCad forum — Why industry prefers manual routing](https://forum.kicad.info/t/why-product-design-industry-prefer-manual-routing-over-autoroute-for-designing-pcb-layout/23660); [Proto-Electronics — Manual or interactive routing](https://www.proto-electronics.com/blog/manual-or-interactive-routing)

Internal (primary sources, and they override the above where they conflict):

- `skills/kicad-pcb/references/design-policies.md` — the R-family canon
- `skills/kicad-pcb/references/routing-pipeline.md` — the canonical steps
- `skills/kicad-pcb/references/autorouter-landscape.md` — why KRT, why not freerouting/DeepPCB
- `fix_routing_to_industry_standards.md` — the open plan derived from this document
