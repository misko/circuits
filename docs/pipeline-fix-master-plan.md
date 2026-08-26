# Pipeline fix — master plan

One plan for the whole pipeline, merged from three working documents and two
adversarial audits. Written 2026-08-02.

**Supersedes and absorbs:**

| source | scope | disposition |
|---|---|---|
| `fix_pcb_design.md` (862 lines, untracked) | parts + schematic, defects D1–D4, fixes F1–F11 | absorbed here; delete after this lands |
| `fix_routing_to_industry_standards.md` (rev 4, untracked) | routing, Changes 0–5 | absorbed here; delete after this lands |
| `routing_readme.md` (untracked) | the WHY document | **not a plan** — lands separately at `skills/kicad-pcb/references/routing-readme.md` after its 5 P0s close (§9) |
| process-fix judge panel (8 agents, 3 judges) | the instruments themselves | absorbed as Stage-X |
| plan-corpus audit (56 findings, 0 refuted) | document hygiene | absorbed as §9 |
| routing-plan audit (83 findings, 2 refuted) | corrections | folded into the numbers throughout |

Status: **PROPOSED. Nothing here is landed.**

> ### Merge coverage — measured, and the first draft failed it
>
> A completeness audit enumerated **133 numbered items** across the four
> sources. The first draft of this merge carried **43**, transformed **14**, and
> **silently dropped 76 (57%)** — with no "deliberately not carried" list.
>
> That is this plan's own §4-X2 defect (an instrument that does not report its
> miss population) committed by the merge itself. Revision 2 restores the P0
> losses below and states the remainder explicitly rather than hiding it.
>
> | source group | items | carried | dropped, now stated |
> |---|---:|---:|---|
> | `fix_pcb_design` D1–D4 | 4 | 4 | — |
> | `fix_pcb_design` F1–F11 (16 sub-items) | 16 | 6 → **9** | F8.1/F8.2/F8.3 restored (§6, §7) |
> | its "deliberately deferred" table | 4 | 0 → **4** | §11b |
> | its open questions | 4 | 1 → **3** | §12 |
> | `fix_routing` Changes 0–5 | 11 | 7 | 4 thinned, named in §7 |
> | its Change-5 deletion table | 5 | 1 → **5** | §7 R5 |
> | its §4 testing corrections | 3 | 0 → **3** | §13a |
> | its §4.3 acceptance table | 9 | 1 → **9** | §13b |
> | its §6 board-level consequence | 1 | 0 → **1** | §7 R1 |
> | judge-panel proposals | 5 | 5 | — |
> | plan-corpus audit findings | 56 | 8 | **48 have no disposition — owed, see §9** |
> | routing-plan audit findings | 83 | "folded in" | **not enumerated — owed** |
>
> The last two rows are still open. They are stated here rather than left
> silent, which is the minimum this plan's own rules require.

Home: `docs/` — its `## Allowed` table permits `*.md`, but the *What* column
reads "proof documents". Widen that cell to "proof documents and repo-level
plans" in the same commit (CLAUDE.md: a change is not done until its contract
catches up). This document deliberately does **not** sit at repo root, because
`contracts_audit.py --present` already exits 1 with `FAIL C-ALLOW` on all three
predecessors.

---

## 1. The organizing finding

Everything below is one defect shape with five measured instances:

> **An instrument reads a nominal, partial, or defaulted input, produces a
> plausible number, and nothing ever asks what it actually read.**

| # | instance | what it read | what it should have read |
|---|---|---|---|
| 1 | **R-POUR** grades 0 nets on a 6.4 A board | netclass floor 0.25 mm | route-time width 3.0 mm |
| 2 | **P-CAP** has graded every 4-layer board on 2 layers, for its whole life | `cap.get("layers", 2)` | `board.GetCopperLayerCount()` |
| 3 | The **RUDY spike** measured this board as uncongested | a swallowed `except` → 0.330 mm for all 208 nets | per-net route-time widths |
| 4 | The **give-up count** was reported as 11, then 42 | two different regex subsets | 19 (`FAILED: Could not find route`) |
| 5 | **`gate_contract_audit.py:12-16`** asserts `parse_amps` returns `None` on qualifiers | a claim true before 2026-07-27 | the parser, which returns `(7.0,'number')` |

Instances 3 and 4 were committed *by an agent diagnosing instance 1*. Instance
5 is why: the repo stores negative capability claims with no expiry, and an
agent read one and repeated it.

The canon already has the right principle — **M-COVER**: every checker emits
`N graded / M total`. It is applied to *populations* and never to *inputs*.
That is the gap this plan closes, and it is why Stage X comes first.

---

## 2. Measured baseline (post-audit, corrected)

Every number below traces to a command. Figures marked **corrected** were wrong
in a predecessor document.

### Fleet

| quantity | measured | source |
|---|---:|---|
| board generations | **28** (10 active + 18 archived) — *corrected from 29* | `ls projects/ archived_projects/` |
| commits | 945 | `git rev-list --count HEAD` |
| part dossiers | 614, of which **309 distinct MPNs** | `find */02_parts/*/part.yaml` |
| dossiers with no PDF | 300 | script over all 614 |
| …of those, recording a sha256 for a missing file | **8** — *corrected from 190 (substring artifact)* | hash-match over 314 |
| superseded releases | 47; **17** are byte-identical boards by sha256, 33 *say so in prose*, 16 carry no `.kicad_pcb` at all — *corrected: the prose figure and the gate's own criterion are different methods* | `find -name SUPERSEDED.md` |
| boards carrying a disposition ledger | **10 of 28** — so fleet rates over review findings are conditioned, not absolute | `find 08_reviews -name DISPOSITIONS.md` |
| D-BACK entries in journals | **39 total**: routing 25, board 7, placement 5, verify 1, schematic 1, parts 0 — *corrected from 24/5/1/0* | `grep -o D-BACK` |

### Routing (programmable-usb2-hub)

| quantity | measured |
|---|---|
| chain | 24 executed waves (`r0→r24`) from **29 authored**; five `tail_*` never ran |
| chain wall | 341.0 s of per-stage medians; 2745 s recorded over an 87-min window |
| routes found | 70; **median 16,444** iterations (n is even: middles 13,857 / 19,031 — an earlier 19,031 was the upper-middle, not the median), p90 465,252 |
| **routes given up** | **19 events** (`FAILED: Could not find route`). **Do not use 11 or 42** — 11 is the `(both directions)` subset; 42 double-counts, because a `(both directions)` total already contains its `(forward)` half |
| give-up iteration share | ≥59% (14,309,756 attributable across the 11 complete two-direction searches) |
| four wide-power waves | 177.1 s of 341.0 s = **51.9%** on 10 net-slots |
| `route:signal` | 33.0 s median, 194.9 s max — addressed by nothing here |
| unconnected at `r24` | **18** under the canon gate (`--refill-zones`); the raw pcbnew ratsnest 189 is a pre-fill artifact |
| congestion (route-time widths) | median 0.39, **p90 0.98**, 282 of 3036 tiles over capacity, Spearman ρ **+0.471** vs wave cost |
| `route.yaml` | 731 lines, 29 waves, **17** keepout rects = 1 region-level + 16 per-pad; **6 of the 16 are stale** |
| VIN_PROTECTED | fails 5 of 26 pads at wave 8, lays 101.6 mm + 13 vias there, **fully connected at r24** (145.0 mm, 20 vias) |

### Ampacity (IPC-2221A as implemented, `rules_audit.py:78-84`)

| current | required width (external) |
|---|---:|
| 1.5 A | 0.525 mm |
| 3.0 A | 1.367 mm |
| 4.5 A | 2.391 mm |
| 6.4 A | 3.887 mm |
| 10 A | 7.194 mm |

**Note the standards mismatch:** canon R2 cites **IPC-2152**; the only
implementation in the tree is **IPC-2221A**. Correct the citation or adopt
IPC-2152 with new constants — do not leave them disagreeing.

---

## 3. Literature basis

What the field does, and which stage it lands in.

**Power belongs in a pour, not a trace** — unanimous vendor/fab guidance;
threshold ~5–10 A or ~2.5 mm. Altium: high-current boards "can require large
traces **or even polygons**." → Stage 4–6, Change R1.
[Altium — PCB Routing](https://resources.altium.com/p/pcb-routing) ·
[JLCPCB — PDN guidelines](https://jlcpcb.com/blog/power-distribution-network-design-guidelines)

**Power routes first** — Altium documents the order: "First route or fan out
the power nets. After the power nets, consider the critical signals."
→ Stage 4–6, Change R0.
[Altium — Routing the PCB](https://www.altium.com/documentation/altium-designer/pcb/routing?version=22)

**Autorouting is a helper inside a human-led process** — professionals route
critical nets interactively. We have the human (Claude); what it lacks is an
instrument panel. → Stage 4–6, Changes R3d and R6.
[Altium — Hand vs automated routing](https://resources.altium.com/p/hand-routing-vs-using-an-automated-router-why-auto-interactive-routing-is-the-ideal-pcb-design-solution) ·
[911EDA](https://www.911eda.com/solutions/pros-cons-of-autorouters-in-pcb-design-explained/)

**Global → detailed is one-directional and traversed once** — OpenROAD's `grt`
writes guides, `drt` reads them; ORFS never calls `global_route` after
`detail_route`, and `FlexDR` follows the guide in only 3 of 65 iterations.
Guides are explicitly soft. The loop that *does* run 2–3× per flow is **global
routing ↔ placement**. → Stage 4–6, Change R6 (map only, no feedback loop).
[OpenROAD grt](https://github.com/The-OpenROAD-Project/OpenROAD/blob/master/src/grt/README.md) ·
[FastRoute](https://onlinelibrary.wiley.com/doi/10.1155/2012/608362) ·
[ISPD 2019 detailed-routing contest](https://dl.acm.org/doi/10.1145/3299902.3311067)

**Production routers never fail a net** — Cadence NanoRoute: *"The detailed
router creates shorts or spacing violations rather than leave unconnected
nets."* SPECCTRA: "Conflicts are allowed… until the last fanout pass." A
failure is never terminal, so it never costs an unbounded search.
→ Stage 4–6, Change R2c. **This is the single highest-value item in the plan.**

**Rip-up should negotiate, not accumulate rungs** — PathFinder's historical
congestion cost converges; a hand-grown ladder does not. → Stage 4–6, Change R4
(measure first, do not reimplement).
[McMurchie & Ebeling, PathFinder](https://dl.acm.org/doi/10.1145/201310.201328)

**Width infeasibility has a theorem** — Ó'Dúnlaing & Yap (1985): a disc of
radius *r* moves between two points among polygonal obstacles **iff** a path
exists along the generalized Voronoi diagram with clearance ≥ *r*, O(n log n).
A trace of width *w* and clearance *c* is a disc of radius *w/2 + c*.
→ Stage 4–6, Change R2a.

**Multi-wire feasibility has a cut condition** — Leiserson & Maley (STOC'85;
MIT Press 1990): a sketch is routable iff no cut's flow exceeds its capacity.
Implementable on Delaunay edges as `capacity = |edge| − (r₁+r₂)` vs
`Σ(width + clearance)` — Su & Dai (ICCAD'97, the SURF board/MCM system),
productised and patented (US 5,880,969), and extended by Liu et al.
(TCAD 28(2), 2009). → Stage 4–6, Change R2a phase 2.

**RUDY is a density model with no wire-width term, and is documented as a
flawed proxy for PCB specifically** — Cypress, ISPD'25 (Cornell/NVIDIA).
Feeding it route-time widths is what made it informative here.
→ Stage 4–6, Change R6.
[RUDY — Spindler & Johannes, DATE'07](https://past.date-conference.com/proceedings-archive/2007/DATE07/PDFFILES/08.7_1.PDF)

**Per-component difficulty is called pin accessibility, and congestion metrics
are documented blind to it** — Taghavi et al. (ICCAD'10). OpenROAD's `drt` runs
pin-access analysis as its **first** stage with a floor of 3 access points per
pin. The formal hardest-first key is `order(n) = HPWL·(1 + α·min(hp_s, hp_t))`
— access-point scarcity, not length. Baek et al. treat pin-access and
congestion DRVs as **distinct mechanisms needing different models**.
→ Stage 1–3 (P-ESC upgrade) and Stage 4–6 (Change R0).
[Xu/Cline/Yeric/Pan, SPIE 2016](https://www.cerc.utexas.edu/utda/publications/C187.pdf) ·
[Kahng/Wang/Xu, Tao of PAO, DAC'20](https://vlsicad.ucsd.edu/Publications/Conferences/377/c377.pdf)

**Placement is where corridor failures are fixed — with a number** — Cheng, Ho
& Holtz (UCSD, arXiv:2210.14259): PCB placement by margin maximization,
measured across 14 real PCB designs routed with FreeRouting and checked in
KiCad — **79% DRV reduction from placement alone**. CLAUDE.md's "a routing
failure is usually a PLACEMENT problem" now has a citation.

**Escape feasibility is closed-form arithmetic** — Altera AN-114:
`g = pitch − via_pad_diameter`, then *n* traces fit iff `g ≥ n·w + (n+1)·s`.
→ Stage 1–3, Change P4.

---

## 4. Stage X (cross-cutting) — fix the instruments first

*Nothing else in this plan can be trusted until these land. All three winners
of the judge panel; none adds a new gate.*

### X1 — Land the denominator census as its own oracle *(panel score 8.8)*

`docs/denominator-census.md` already exists and already names exactly four check
IDs (`M-REPRO`, `R-POUR`, `P-KEEP`, `P-POL`) with per-board measured `|pop| = 0`.
It is enforced by nothing — one reference repo-wide, in `contracts_audit.py`,
which governs the file's *existence*, not its content.

> **Correction (rev 2): the cost basis in rev 1 was false.** Rev 1 said the
> conversions were "already written and commented out" and the cost was "mostly
> uncommenting." **No such commented block exists.** `policy_audit.py` carries
> exactly one commented `rows.append` — `:1436-1442`, which is *R-LEN's* OWED
> replacement, not a census conversion. Four `grade()` sites must be converted
> **by hand**.
>
> **And the census's own line numbers are stale.** It was measured at
> `7f5e48cd`; HEAD is `809b38af`. It cites M-REPRO :1542, R-POUR :1262,
> P-KEEP :1050, P-POL :1024; the actual sites are **:1584, :1304, :1092,
> :1066**. Re-measure and re-anchor by `grade("<ID>"` rather than by line
> number, in the same commit — the drift is the reason.

**Ordering hazard with R1:** X1's equality test is calibrated against R-POUR's
population *under the old selector* (census:74 records `pwr` = nets with
`track_width >= 0.5`). R1 replaces that selector. **R1 must re-run the census
for R-POUR and update `docs/denominator-census.md` in the same commit**, or X1's
oracle grades a population that no longer exists.

Implement exactly those four conversions and add a test asserting the
implemented set **equals** the census set — so a fifth conversion fails. The
census itself says any unnamed conversion "is a regression, not an improvement."

**Known-bad:** a fifth conversion added to `policy_audit.py` → test fails.
**Cost:** mostly uncommenting. **Closes:** instance 1, defect D5.

### X2 — MISS-CENSUS: amend M-COVER so the complement is part of the denominator *(8.7)*

An instrument that resolves per-item facts or extracts matches must report its
**miss population**: how many items took a default/exception path, and how many
candidates its pattern did *not* match. A 100% fallback rate is a hard FAIL —
a resolver that defaults for every member is broken, not permissive.

This **amends** M-COVER rather than minting an ID. ~65 lines: a `census()` /
`extract()` pair plus one AST check as a fourth sibling of the existing
`G-COVER` / `G-INPUT` / `G-RED` `--enforce` list in `gate_contract_audit.py`.

**Measured scope:** 14 silent-fallback sites across `skills/*/scripts/`,
including `generate_rules_generic.py:255-257` (clearance 0.2, via_diameter 0.6,
via_drill 0.3 — three *geometry* numbers), `placement_gates.py:322`
(`layers, 2`) and `tier_preflight.py:291` (`or 2`, with 3 of 11 floorplans
carrying no `layers:` key).

**Known-bad:** a 20-line gate whose resolver raises unconditionally → prints
`N/N defaulted`, exits 1; the same gate with one net resolving → exits 0. Both
are required, or it is a ban on fallbacks rather than a census.
**Closes:** instances 2, 3, 4.

### X3 — Close the check-ID and grade vocabularies, bound both ways *(8.5)*

Every check ID a gate emits or a document cites has a canon row; every canon row
has an emitter; every grade cell is a member of `GRADES`. Lifted from code, not
hand-listed. The test already exists and needs widening.

`policy_audit.py:86` reads `GRADES = ("PASS","FAIL","WAIVED","HUMAN","N-A")`.
Any new grade (`UNGRADED`) is added to that tuple in the same commit, because
`parse_report` counts only rows whose grade cell is in `GRADES`, and
`report_inconsistencies` then flags the rest as malformed.

> **Correction (rev 2): "there is no UNREACHED" was wrong, and scoped too
> widely.** `UNREACHED` is a **live emitted verdict** in at least five scripts —
> `copper_length_audit.py:1054/1158/1170/1180`, `escape_check.py:716`,
> `electrical_invariants.py:841/854/886/911`, `build_provenance.py:569/580`.
> The true statement is narrow: it is not a member of *`policy_audit.py`'s
> `GRADES` tuple*. X3 must decide explicitly — add it alongside `UNGRADED`, or
> rule it out of scope and name which emitters are exempt. Implementing rev 1's
> sentence as written would silently drop those rows or fail five gates.

**Self-application hazard:** X3 closes IDs that "a document cites", and is
sequenced first. This document cites **17 unminted IDs**. `t1_contracts.py:425-437`
exempts a citation only when *every* citation line matches
`candidate|proposed|future|todo|planned` — a **per-line** regex, so a header
`Status: PROPOSED` does not cover them. Either tag each new-ID line with a
forward-reference token, or state that X3's docs/ widening excludes
PROPOSED-status documents. Otherwise this plan fails X3 on landing.

**Closes:** the invented-vocabulary class.

### X4 — G-STALE-NEG: a negative capability claim carries its probe

Any assertion that something **cannot** be parsed, is **not** read, **never**
runs, or returns **zero** — in a live document or a module docstring — carries
the re-runnable command whose output supports it.

**The root cause, measured:** `gate_contract_audit.py:12-16` asserts that any
qualifier makes `parse_amps` return `None`. Executed today, `'7 A worst case'`
→ `(7.0, 'number')`. The parser was fixed 2026-07-27; the claim above it was
never re-run — and an agent read it and built a contract obligation on it.

**Closes:** instance 5.

### X5 — CFG-SUBJECT: a config is graded against the board it configures

Every refdes or coordinate a config names must resolve to a real footprint at
approximately the position implied, and any gate accepting a config file prints
whether it ran on a config or on defaults.

**Measured:** 6 of 16 per-pad keepout rects name a refdes that is absent
(`C432`, `C207`, `C211`) or 17.7 / 27.8 / 30.2 mm away (`C32`, `C422`, `C201`).
And `find -name placement_gates.json` returns **zero results repo-wide**.

**Closes:** instance 2's config half, and a live board defect.

---

## 5. Stage 0 — Commission

No changes. The commission record and D-SPEC tension check are working: Q2's
2 A revision on the USB hub was captured, dated, and drove ADR-0007 correctly.

**One note carried forward:** commission answers must be re-read before every
architecture decision. ADR-0006 restored 3 A without a user directive and was
invalidated — the process caught it, at the cost of a full redesign.

---

## 6. Stage 1–3 — Design docs, parts, rules

*The stage where the most expensive decisions are made and the fewest gates run.
The organizing insight from `fix_pcb_design.md`, and it survives audit:*

> **The pipeline's instruments are ordered by when an ARTIFACT EXISTS, not by
> when a DECISION IS MADE.**

### P0 — F5: call the machinery at the stage that decides *(the enabler)*

`policy_audit.py` already produces **9–12 gradeable rows on a parts-only tree in
0.45–0.87 s** (measured across three boards; *corrected from "10 rows in
0.89 s"* — it is board-dependent, and the run exits 1 on E-INV). Nothing invokes
it until the release audit. Add `--phase parts` and a `parts-gate` verb.

**Every other Stage 1–3 fix lands into this.** Do it first.

### P1 — F1: promote parts to a fleet library *(closes D1)*

614 dossiers → 309 distinct MPNs. One dossier per MPN makes the 94 measured
contradictions structurally unrepresentable. New IDs: `M-PART1`, `M-PARTREF`,
`M-REUSE`.

Scope correction from audit: `USBLC6-2SC6` has `escape:` in **6** of 12 (not 7),
and **6** dossiers carry none of the four keys (not 4).

### P2 — F2: reference design as a fetched artifact *(closes D2)*

Replace self-asserted `reached: true` with a vendored file whose sha256
verifies, plus a prior-art census as an *input* to selection. New IDs:
`P-PREC-FETCH`, `P-PRIOR`.

Scope: 300 folders need a download. **Not 490** — the 190 figure was a substring
artifact.

### P3 — F3 + F9: application-circuit conformance and `E-ACCOUNT` *(closes D3)*

Give the required-companion set a machine home outside the schematic author's
own declaration, with a printed coverage denominator; then make the netlist the
denominator. New IDs: `E-APPCKT`, `E-ACCOUNT`.

Fix the worked example: the part is `XU316-1024-TQ128-I24`, the citation is
`XM-014532-PC-2.0.0 §14 Integration, p.29` — there is no "Figure 14.3", and
`XU316-1024-QF60` exists nowhere in the fleet.

### P4 — upgrade P-ESC from a boolean to a number

Today `escape_check.py` answers "can this package be escaped at tier T" from
four scalars, and `escapes_worst_side` is **human-declared and never measured**.

Two upgrades, both cheap and both literature-backed:
- **Emit the number**, not a verdict: `g = pitch − via_pad`, then traces-per-
  channel from `g ≥ n·w + (n+1)·s` (Altera AN-114).
- **Split on package topology, not pitch**: area-array (BGA/LGA/CSP) gets the
  channel test; peripheral (QFN/QFP/SOIC) gets a pad-width test and no via
  fan-out budget — the escape-routing literature is defined over pin *arrays*,
  and applying it to peripheral packages draws the wrong conclusion.

**This is also where a per-component difficulty score belongs.** Canon R4 says
"hardest nets first" and is graded **`HUMAN`** — `policy_audit.py:1391`. There
is no machine definition of "hardest" anywhere in the tree. The literature's key
is access-point scarcity at the endpoints; `escapes_worst_side` is already a
hand-entered version of exactly that number.

### P5 — F7: sourcing for build AND bench *(closes the Q-2SOURCE gap)*

One flat "two pools, stock > 10" rule serving two different jobs. Split: a reel
that must build 5 boards (`Q-BUILD`), and a bench spare in hand next week
(`Q-WEST`), with a machine-decidable exemption class and an ADR path
(`Q-WEST-WAIVE`).

Restate the scope denominator: there are **68 release directories / 2615 BOM
rows**, or **41 distinct BOMs / 1629 rows** deduplicated — the plan's "40
releases / 1758 lines" reproduces by neither method and must be restated with
its own method.

### P6 — F11 + F6: `P-DOSSIER` and reuse promotion *(closes D1's second half)*

Does every part the design names *have* a dossier? Then promote reuse.
`M-REUSE` belongs **here**, not in P1 — its input (`requires:` models) does not
exist until P1 lands. Report-only at first, deliberately.

### P7 — F8.1 and F8.2: two live gate defects *(restored in rev 2, and they go FIRST)*

Both are crashes or self-certifications, not improvements. `fix_pcb_design`
placed them in Phase 0a/0b as the opening move; rev 1 lost them.

**P7a — multi-board `route.yaml` path resolution.**
`pre_route_review_check.py:82-84` does an unguarded
`(project/"03_src/route.yaml").read_text()`. `smc0985-cooksense` has no such
file — only `03_src/cooksense/route.yaml` and `03_src/interposer/route.yaml` —
so the gate raises `FileNotFoundError`. **PR-REVIEW currently passes on 0 of 10
boards.** Budget note: making it grade reveals ten boards' worth of findings.
Needs a `t_no_route_yaml` fixture.

**P7b — `E-INV` self-certifies at 100%.** `electrical_invariants.py:1178`
prints `f"E-INV OK: {len(invs)}/{len(invs)} invariants hold"` — numerator and
denominator are the same variable. **This is another instance of §1's shape**,
and it was sitting in the tree the whole time. Land the real coverage line
**report-only**; do **not** ratchet the fraction in the same change.

---

## 7. Stage 4–6 — Generate, place, route

### PLACEMENT — restored in rev 2, and rev 1 erased it by mismeasurement

> **Rev 1 deleted the placement half of the loop, and did it with the plan's own
> defect.** `fix_pcb_design` §6 Q4 classified D-BACK entries **by TARGET**
> — placement ~10, parts 2, schematic 1, pipeline-config 2 — and concluded:
> *"a plan aimed only at parts and schematic is aimed at the wrong half of the
> loop. Placement, and the pipeline's own constants, are unaddressed here and
> should be the next investigation."*
>
> Rev 1 replaced that with a count **by JOURNAL** (routing 25, board 7,
> placement 5 …) and labelled it *"corrected"*. **It is not a correction — it is
> a different question.** Where a backtrack was *written* is not what it
> *targeted*. The conclusion vanished with the measurement, and with it the only
> placement fix in either predecessor.
>
> Both tables are now stated in §2, and the by-TARGET one governs the scope
> decision.

**PL1 — `P-DRIFT` (was F8.3).** Diff regenerated placement against the last
promoted board for every refdes named by coordinate in `route.yaml`; FAIL on any
move over threshold or any ref that no longer exists. ~20-line port of the
existing `bbox_override` guard at `generate_board_generic.py:1278-1282`.

Carry its recorded caveat: **this is a symptom fix.** The real repair is making
the legalizer locally stable, which is not in this plan.

**PL2 — the placement hand-off is `R-FEAS-NARROW`.** R2a's finding IDs are the
one place routing hands a failure back to placement, with a citable payoff:
79% DRV reduction from placement alone (Cheng/Ho/Holtz, 14 real PCB designs).
See R2a for the ranked remedy.

**Note on that citation:** their boards were routed with **FreeRouting**, which
`autorouter-landscape.md:32-38` calls a dead end for *our* KiCad DSN path. The
result is admissible as evidence about *placement*, not about routers — say so
wherever it is cited.

### R0 — power routes first, and "hardest" gets a definition

Move power waves ahead of USB. Altium documents the order; our own
`routing-pipeline.md` says "hardest-first"; the board does neither — **34** USB
net-slots route before the widest net on it.

**Honestly scoped:** measured same-clock at **~9%** (41.2 s on `r0` vs 45.5 s at
wave 8), not the 7× claimed in two predecessor drafts — that compared KRT's
internal search counter against wall time. And it is not a *fix*:
VIN_PROTECTED fails the same five pads first or eighth.

Pair it with P4's difficulty number so R4's `HUMAN` grade can become machine.

### R1 — R-POUR grades declared current, not netclass width

Replace the `track_width >= 0.5 mm` selector (`policy_audit.py:1295`; the
comment is at `:1281` and the grade call at `:1304` — cite the span, the offset
has already drifted once) with the netclass's `current:`, converted by
`rules_audit.py:84 required_width_mm`.

**Three corrections from the predecessor:**
1. The prose **is** machine-readable — `parse_amps` returns `(10.0,'number')`.
   The "not machine-readable" premise was false (see X4 for why it was believed).
2. `current:` is **already required** and already bound to A-AMP. Nothing gains it.
3. It is **IPC-2221A**, not IPC-2152.

The real gaps are narrower: R-POUR doesn't read `current:` though A-AMP does;
and the prose form makes a parser take the **fuse rating (10 A)** rather than the
**design current (6.4 A)** — hence a typed `current_a:` companion.

**State the threshold.** At ~2.5 mm the in-scope set here is **PWR_IN alone**
(4 nets → 4 zones); PWR_5V and SWITCH_POWER at 2.033 mm fall outside.

**Companion, not optional:** nothing in the repo grades a **zone's** ampacity.
Converting a trace to a pour trades a computed FAIL for an ungraded assumption.
Either add the check or say so in §11.

**And A-AMP is already RED and non-blocking** — wire it into the route preflight.

### R2a — R-FEAS: the widest-corridor bound, with a theorem

Per net per layer, compute **w\*** — the widest trace that can reach — by the
disc-motion retraction theorem plus max-bottleneck path. Sound (fails only where
no corridor exists), deliberately incomplete (passing promises nothing).

**Bound it to the declared neckdown floor, not the netclass width.** Every power
wave sets `neckdown_length: 0.5` and PWR_IN's `routing:` explicitly permits
0.5 mm taps — a gate firing at netclass width would fire on legal, intended
geometry.

Phase 2, only if phase 1 earns it: the Delaunay cut condition for the
multi-wire case.

### R2c — bounded failure: a net must never be a terminal outcome

**The highest-value item in this plan.** Three mechanisms, ascending cost:

1. **Window-bounded search** — bound A* by a bounding box, not an iteration
   count; grow the box on failure. Failure cost becomes O(window).
2. **Escalation schedule instead of a flat cap** — TritonRoute's readable ladder
   is `mazeEndIter` 3→8→16→32→64 with DRC cost 1×→64×. Our caps are 500 k–1.2 M
   against a 200 k default while median success is 16.4 k.
3. **Bounded deferral** — cap effort, defer, retry ≤ N (deferring cycle = 3;
   routability *saturates* with more cycles while runtime grows). This is the
   principled replacement for the 17-rung retry ladder.

**Risk, stated:** unlike everything else here, R2c changes routing *output* —
committing a recorded conflict instead of leaving a net unrouted. The
unconnected-vs-violations trade must be measured, and DRC findings stay
CLASSIFIED, never counted.

### R3 — economics: resume, race, buffering

- **R3a** `--from rN`: `cmd_route` hardcodes `cur = build / prep.out` (:846).
  Measured saving on this session's event: 24 of 29 waves.
- **R3b** `race`: unset → 1 lane on 32 cores. Worthless until R1/R2a/R2c land.
  Note `route.race` is **already bound** in the contract (`03_src/contracts.md:435`)
  — this sets a value, not a schema.
- **R3d** `flush=True`: 24 wave headers land at log lines 10,087–10,156 of a
  10,159-line file. Not hygiene — it restores the only live feedback channel the
  human in this loop has.

*(R3c, deriving iteration caps, is subsumed by R2c.)*

### R4 — R-LADDER: name the retry ladder under a dated ceiling

17 of 29 waves are recover/cleanup/tail. Report it with a grade cell drawn from
`GRADES` and the ratio in Detail — a bare number in the Grade cell is invisible
to `parse_report`. **The ceiling and its date ARE the policy.**

### R5 — delete what the fixes make dead

Including the **6 stale keepout rects** — a live board defect, one join between
`route.yaml` comments and pcbnew pad positions, no new theory. The 10 correct
per-pad reservations should be **generated from `seed_stubs`**, not hand-typed,
which removes the staleness class rather than six instances of it.

> **Success criterion: `route.yaml` must get SHORTER.** Baseline 731 lines /
> 29 waves / 17 rects.

### R6 — the congestion map (un-demoted)

Corrected: median 0.39, **p90 0.98**, 282/3036 tiles over capacity, ρ **+0.471**.
The board *is* at capacity. Build step i (`congestion_triage.py`, 188 lines,
0.21 s) as the instrument panel.

Steps ii and iii remain gated: the specified `correlation` gate (two boards,
where nets *failed*, threshold agreed beforehand) has still not been run, and
step ii's premise was wrong anyway — a capacity map calls a 0.4 mm² pad
reservation "slack to spare" by construction.

**Free cross-check:** configure **P-CAP** and compare. Two independent methods
(canon M1) for almost nothing.

---

## 8. Stage 7 — Verify and release

### V1 — F4: split the copper release from the evidence revision *(closes D4)*

A release whose board sha256 equals its predecessor's is an evidence revision,
not a supersede. New IDs: `M-REL-KIND`, `F-EARLY`.

**State both methods:** 33 of 47 `SUPERSEDED.md` *say in prose* the payload is
byte-identical; by board sha256 — the criterion the gate actually applies —
**17 qualify, 13 changed, and 16 release dirs carry no `.kicad_pcb` at all**.
Specify the gate's behaviour on a board-less release (normalised gerber hash, or
FAIL as ungradeable — never a silent pass).

### V2 — F8.4 only: name the fleet runner

> **Rev 2 correction: rev 1 compressed F8's four sub-items into the words "Four
> process fixes" and moved them from FIRST to LAST.** Three of the four are live
> defects and none is stage-7 work. They are re-split to their own stages:
> **F8.1 and F8.2 → Stage 1–3 (P7 below)**, **F8.3 → PL1 (placement)**, and only
> F8.4 stays here.

`fleet_regrade.py` already runs four **release** gates
(F-PAYLOAD, F-LEGIBLE, A-EVID, A-POP) over `07_releases/` and never invokes
`policy_audit` — so `t1_fleet_regrade.py` is **not** a policy sweep and cannot be
reused as one. Whoever builds `fleet_gates.sh` owns the R-POUR fleet table.

### V3 — F10: bounded gate migration, then pin

A board commissioned after date D runs gate set D. **Add the missing scope
sentence:** the pin covers the gate *set wired into a board's driver*; it does
**not** exempt a board from (i) corrections to gates already wired, or (ii)
refuse-to-route preflights inside `cmd_route`. Without that, R1 and R2a are
ambiguous on the only board either plan touches.

---

## 9. Document hygiene (from the corpus audit)

| action | why |
|---|---|
| Correct the give-up number to **19 events** in both routing documents | currently wrong in the document that "corrected" it |
| **Do not promote `routing_readme.md`** until its 5 P0s close | it would make four wrong numbers canonical |
| Delete `lipo3s_trace.md` + `.gitignore:5` | dead since 2026-07-21; and it is the false precedent `routing_readme.md` leans on |
| **DONE 2026-08-26:** Archive `pluto-rx2-8way-v3` | Moved intact to `archived_projects/`: 28 tracked files vs v2's 109, no BRIEF.md, no KiCad design or release, and `STATUS.md` still literal `YYYY-MM-DDTHH:MM:SS` |
| Rewrite or delete `resume_state.md` | tracked and actively wrong: cooksense v1.7 sealed, v4 shipped twice, 6 of 10 boards listed |
| Delete or RESOLVED-banner both stale `RESUME.md` files | usb-hub-3s-v3 is sealed through v1.12 |
| Create `examples/routing-economics-2026-08/` | C-ISO: skills may not cite `projects/` paths |
| Instantiate `docs/ORCHESTRATION_STATE.md` | the corpus has **no index** — this document was found by listing a directory |

---

## 9b. Testing corrections and acceptance criteria *(restored in rev 2)*

### 9b-i — three testing-plan corrections rev 1 dropped

1. **`vacuity` runs the other way.** `tests/README.md:36`: *"the checker
   **PASSES** input whose graded fact is FALSE — a declared blind spot (canon
   G-VACUOUS)."* `gate_contract_audit.py:599-607` FAILS a fixture declared
   `kind="vacuity"` whose first assertion is `must_fail`. Rows asserting "must
   not pass" are `known_bad`, not vacuity.
2. **RED-first is scoped to existing gates.** CLAUDE.md ties it to *fixing a
   bug in a gate*. It applies to R1 (`git show HEAD:…policy_audit.py`;
   `known_bad_floor` must PASS against it). R2a, R2c, X4 and X5 are new code
   with no pre-fix bytes — each fixture instead states inline what it would
   have caught.
3. **Fixtures must name their oracle.** `tests/README.md:290-338` allows three:
   a pinned `git show <sha>:<path>`, a sealed `07_releases/<rel>/source/…`, or a
   live board only where the assertion tolerates re-routing. Never live
   `04_kicad/`.

**Every new gate needs a known-bad, or `G-RED` blocks it on landing**
(`gate_contract_audit.py:197-198`). Rev 1 specified one for X1 and X2 only —
X3, X4, X5, PL1 and the R-family still owe theirs.

### 9b-ii — performance acceptance *(the governing rule rev 1 deleted)*

| metric | baseline | target | how measured |
|---|---:|---:|---|
| give-up events | **19** | < 5 | `grep -c 'FAILED: Could not find route'` |
| give-up share of iterations | ≥59% | < 20% | log parse, method stated |
| cost of one give-up | up to 4,637,949 iters | ≤ 10× median success (164 k) | R2c |
| `vin_protected_pre` | 48.0 s, 21/26 pads at wave 8 | replaced by a pour **whose copper is specified** | `performance.json` |
| full chain, race:1 | 341.0 s | state the lever or drop the target | `performance.json` |
| **unconnected at chain end** | **18** (canon gate, refilled) | **0** | `kicad-cli … --refill-zones` |
| congestion p90 | 0.98 | falling | `congestion_triage.py` |
| ladder ratio | 17/29 | under a dated ceiling | `R-LADDER` |
| `route.yaml` | 731 lines / 29 waves / 17 rects | strictly smaller | `recipe_shrinks` |

> **None of these may buy speed with connectivity. The unconnected row
> governs.** This applies above all to **R2c**, which is the one change that
> alters router *output* — committing a recorded conflict instead of leaving a
> net unrouted. Rev 1 shipped R2c with no pass/fail bar and no connectivity
> floor; that was the most dangerous single omission in the merge.

## 10. Sequencing

```
Stage X  (instruments)         ── X1, X3 first: both are mostly repairing
                                  machinery already on disk. Then X2, X4, X5.
                                  NOTHING ELSE IS TRUSTWORTHY UNTIL THESE LAND.
R5-stale (6 dead keepouts)     ── a live board defect; standalone, today
R3a / R3d (resume, buffering)  ── cheap; R3d restores live feedback
P0 (F5 --phase parts)          ── the Stage 1-3 enabler; everything lands into it
R2c (bounded failure)          ── largest single routing payoff
R1 + R2a                       ── both before R3b
P1..P6                         ── parts/schematic, in F-number order
R0, R3b, R4, R6-i              ── after the deterministic failures are gone
V1..V3                         ── release
R5 (delete what died)          ── after EACH of the above
R6-ii/iii                      ── only if the specified correlation gate passes
```

**Why Stage X is first:** four of this plan's own headline numbers were wrong
when first measured. A plan that acts on unverified instruments repeats the
defect it exists to fix.

---

## 11. What this plan explicitly does NOT do

- **Not replacing the router.** But *not* on the grounds
  `fix_pcb_design.md` gave: its "first-pass routing completes in 1–4 hours on
  every board measured" matches **no artifact** (the repo's own driver comment
  says "cooksense routing D-BACK ~13h", and cooksense's journal heading is
  `## STUCK`). The honest grounds are that R2c and R2a fix the measured cost
  without a rewrite.
- **Not acting on the Freerouting benchmark.** `fix_pcb_design.md` cites KRT
  falling 0.74→0.20 while Freerouting holds 0.78 — **uncited**, and directly
  contradicting `autorouter-landscape.md:32-38` ("dead end (tested
  exhaustively)… Don't sink time here again"). Either name the benchmark and
  reconcile it against that canon in one edit, or drop it. **It is an open
  question, not a plan item** — see §12.
- **Not reimplementing PathFinder.** R4 measures first.
- **Not adding a review lens.** Lenses already dominate detection.
- **Not backfilling `land_pattern:` across 614 dossiers.** After P1, over 309.
- **Not adding a fleet ratchet that forces every new check onto all 10 boards.**
  V3 replaces it with a bounded migration.

---

## 12. Open questions

1. **The Freerouting benchmark.** If real, it undercuts a load-bearing canon
   assumption on a board that fought its router all session. Needs a source, a
   board set, and a definition of "clean-pass" before it is anything.
2. **Zone ampacity.** Nothing grades it. R1 creates the need.
3. **Whether R2c's conflict-commit is acceptable here.** Production PCB routers
   do it; our DRC gate is 0-violations. These may be incompatible, and if so R2c
   reduces to mechanisms 1 and 3.
4. **`route:signal`** — 33.0 s median / 194.9 s max, addressed by nothing.

---

## 13. Appendix — files touched, with collision map

**Collisions between the two predecessor plans (neither cross-referenced the
other):**

| file | routing plan | pcb-design plan |
|---|---|---|
| `skills/kicad-pcb/scripts/policy_audit.py` | R-POUR selector, `GRADES`, R-LADDER | `--phase parts` (F5) |
| `skills/kicad-pcb/references/design-policies.md` | 4 row edits | **14 new rows** |
| `skills/pcb-design/SKILL.md` | resume verb, feasibility stage | parts-gate |
| `tests/run_tests.sh` | 5 new suites | unspecified |
| `templates/contracts/03_src/rules/contracts.md` | `current_a` | F1/F7 keys |

**New:** `route_feasibility.py`, `congestion_triage.py`, `global_route.py`
(deferred), `fleet_gates.sh`, `docs/ORCHESTRATION_STATE.md`,
`examples/routing-economics-2026-08/`.

**Suites:** `t1_policy_pour.py`, `t1_route_feasibility.py`, `t1_route_budget.py`,
`t1_route_economics.py`, `t1_route_deletion.py`, plus X1–X5 fixtures.
`t4_regressions.t_every_suite_propagates_and_is_wired_in` asserts registration.

**Contract catch-up required in the same commits:** `docs/contracts.md` (widen
the *What* cell), the `03_src/rules` and `03_src` templates, and
`skills/kicad-pcb/scripts/contracts.md`'s `## Audit` obligations (that folder has
no per-script allow-list — patterns only).

---

## 14. Provenance

Fleet numbers measured against `809b38af` and the 2026-08-02 working tree.
Routing numbers from `06_build/performance.json` and
`06_build/logs/route-latest.log` on `programmable-usb2-hub`. Corrections marked
*corrected* were produced by two adversarial audits (83 findings / 2 refuted,
and 56 findings / 0 refuted) plus a five-framing, three-judge proposal panel.

**Four of this document's own headline numbers were wrong in a predecessor and
are corrected here.** That is the strongest single argument for Stage X.

---

## 9a. Corpus-audit disposition — all 56 findings

*The audit filed 56 findings / 0 refuted across 8 target documents. §9 carries 8
rows; this section disposes of every finding against them. Rule applied:*

- **FOLDED** is available only for findings against `fix_pcb_design.md` and
  `fix_routing_to_industry_standards.md` — the two documents this plan deletes
  after landing (header table). A correction carried in the plan's numbers is
  the whole remedy, because the source dies.
- **`routing_readme.md` is *promoted*, not deleted**, so nothing against it can
  be folded. Every one of its 23 findings needs an action or it becomes canon.
  §9-r2 gates promotion on 5 P0s and leaves the other 18 undisposed.
- **ACTION-HERE** = executing an existing §9 row *literally* closes the finding.
  Where the row exists but its text closes nothing as written, it is still
  ACTION-HERE and the amendment is listed under "row-text amendments".

### The five P0s §9-r2 gates on and never names

They are **5 findings but 3 distinct defects**, and **2 of the 5 file a FIX that
is itself wrong**.

**P0-a — `routing_readme.md:38` and `:42-43`** *(findings #1, #4, #5 — one row,
three filings)*
Claim: `| routes given up | 11 | 14,309,756 | up to 4,637,949 |` and
"**59% of all search effort went into paths that do not exist.**"
Fix: `| routes given up | 19 events | most expensive single search 4,637,949 |`.
`grep -c 'FAILED: Could not find route' projects/programmable-usb2-hub/06_build/logs/route-latest.log` → **19**.
⚠ Findings #4 and #5 both prescribe **42 / 29,641,605 / 74.9–75%**. Both are the
double-count artifact (a `(both directions)` total contains its `(forward)`
half). **Closing them as filed lands a wrong number in canon.**

**P0-b — `routing_readme.md:102` and `:107-116`** *(finding #2)*
Claim: the RUDY row's *what it needs* cell reads "placement only — net bounding
boxes", and ":107 RUDY is the one to reach for first." The document carries no
spike result at all:
`grep -cin 'spike\|spearman\|0\.471\|3036\|282 of' routing_readme.md` → **0**.
→ owed row **H1**.

**P0-c — `routing_readme.md:225-229`, `:238`, `:245-246`** *(finding #3)*
Claim: F1 Measured "0/1 routed, 5 of 26 pads unconnected"; F2 Symptom "one power
net dominates routing time, **or refuses to complete**." Under the canon gate on
`r24`: 18 unconnected, and VIN_PROTECTED is **not among them** (145.0 mm /
20 vias, fully connected). The exemplar is expensive, not unroutable.
→ owed row **H2**.

*§9-r2's why-column says promotion "would make four wrong numbers canonical."
It is **at least twelve**: :38 (11), :42 (59%), :83/:128 (18 rects → 17),
:195 (r0→r29 → 24 executed), :228 (180/340 s, 53% → 177.1/341.1, 51.9%),
:257 (0.25 mm floor → 4 of 8 netclasses are below it), :192 (IPC-2152 →
IPC-2221A), :141 ("all 10,000 lines" → headers at 10,087–10,156 of 10,159),
:225 (wave-8 snapshot presented as final state), :226 (0.1375 mm attributed to
a log that has no such string), :102 (RUDY needs route-time widths), :221
(identical duration → 42.7–52.3 s).*

### Disposition table

#### `routing_readme.md` — 23 findings (P0 5 / P1 10 / P2 8)

| # | lines — claim | P | disposition |
|---|---|---|---|
| RR1 | :37-43 — give-up row `11` / "59%" | P0 | **ACTION-HERE** §9-r1 |
| RR2 | :102,107-116 — RUDY "placement only"; no spike result | P0 | **ACTION-OWED** H1 |
| RR3 | :225-229,238,245-246 — F1 "0/1 routed, 5 of 26"; F2 "or refuses to complete" | P0 | **ACTION-OWED** H2 |
| RR4 | :38,42 — same row; **its FIX prescribes 42 / 74.9%** | P0 | **ACTION-HERE** §9-r1 — adopt 19, reject the filed FIX |
| RR5 | :37-38,42-43 — same row; **its FIX prescribes 42 / 75%** | P0 | **ACTION-HERE** §9-r1 — adopt 19, reject the filed FIX |
| RR6 | :221-223 — F1 diagnostic "identical duration eight times" | P1 | **ACTION-OWED** H7 |
| RR7 | :83,86-89 — keepouts framed as human congestion guesses | P1 | **ACTION-OWED** H3 |
| RR8 | :14-17 — `lipo3s_trace.md` precedent + "kebab-case and nothing else" | P1 | **ACTION-HERE** §9-r3 *(amend a)* |
| RR9 | :33,83,259 — board-specific evidence paths (C-ISO landing blocker) | P1 | **ACTION-HERE** §9-r7 *(amend c)* |
| RR10 | :195 — "29 sequential KRT invocations, r0 → r29" | P1 | **ACTION-OWED** H4 |
| RR11 | :13-18 — same precedent paragraph (dup of RR8) | P1 | **ACTION-HERE** §9-r3 |
| RR12 | :16,107 — promotion precondition; RUDY unmeasured on this board | P1 | **ACTION-OWED** H1 |
| RR13 | :83,86-89,128 — "18 hand-typed keepout rectangles" | P1 | **ACTION-OWED** H3 |
| RR14 | :192 — stage-0 "IPC-2152 ampacity width floors" | P1 | **ACTION-OWED** H5 |
| RR15 | :183,218-229,236-246 — "It is still the defect we shipped" | P1 | **ACTION-OWED** H2 |
| RR16 | :83,128 — 18 → 17 (dup of RR13, severity-corrected) | P2 | **ACTION-OWED** H3 |
| RR17 | :228-229 — "180 s of a 340 s chain — 53%" | P2 | **ACTION-OWED** H6 |
| RR18 | :257-259 — "every netclass declares a 0.25 mm floor" | P2 | **ACTION-OWED** H6 |
| RR19 | :226-227 — "0.1375 mm" sourced to `route-latest.log` | P2 | **ACTION-OWED** H6 |
| RR20 | :141-142 — buffering evidence + wrong F1 pointer | P2 | **ACTION-OWED** H6 |
| RR21 | :160-161 — R-LEN-OCT "and no router" | P2 | **ACTION-OWED** H6 |
| RR22 | :265-266 — "R-LEN passed on the *word* 'length'" | P2 | **ACTION-OWED** H6 |
| RR23 | :14-17 — same precedent paragraph (dup of RR8) | P2 | **ACTION-HERE** §9-r3 |

#### `fix_pcb_design.md` — 20 findings (P0 2 / P1 5 / P2 13) — *document deleted after this lands*

| # | lines — claim | P | disposition |
|---|---|---|---|
| FP1 | :338-339 — "190 record a sha256 for a missing file" | P0 | **FOLDED** §2 fleet row (**8**, corrected from 190) |
| FP2 | :775-776 — "first-pass routing completes in 1–4 hours" | P0 | **FOLDED** §11 bullet 1 ("matches no artifact") |
| FP3 | :775-777 — same clause, no artifact repo-wide | P1 | **FOLDED** §11 bullet 1 |
| FP4 | :777-779 — uncited Freerouting 0.78 benchmark | P1 | **FOLDED** §11 bullet 2 + §12 Q1 |
| FP5 | :179-186 + whole file — 14 new IDs, no files-touched appendix | P1 | **FOLDED** §13 appendix + collision map + contract catch-up |
| FP6 | :361-364,370 — `M-REL-KIND` "33 of 47", method mismatch | P1 | **FOLDED** §2 supersede row + §8 V1 (17/13/16) |
| FP7 | :42-44,775-776,859-862 — "35 of 210 / 4.2%" unconditioned | P1 | **FOLDED** §2 "10 of 28 carry a disposition ledger" |
| FP8 | :1-10,849-862 — no disposition/target-path paragraph | P2 | **NO-ACTION** — source document is deleted after this lands |
| FP9 | :506-517 — `P-DRIFT` vs the route.yaml↔pad join, no cross-ref | P2 | **FOLDED** §7 PL1 + §7 R5 + §10 (R5-stale standalone, today) |
| FP10 | :585-618,790-793 — F10 pin scope unstated | P2 | **FOLDED** §8 V3 ("Add the missing scope sentence") |
| FP11 | :384-385 — both plans edit `policy_audit.py`, no cross-ref | P2 | **FOLDED** §13 collision map + §4 X3 (`GRADES`) |
| FP12 | :529-537 — `fleet_gates.sh` ignores `fleet_regrade.py` | P2 | **FOLDED** §8 V2 (names the 4 release gates) |
| FP13 | :287 — `XU316-1024-QF60` / "Figure 14.3" | P2 | **FOLDED** §6 P3 (`XU316-1024-TQ128-I24`, `XM-014532-PC-2.0.0 §14`) |
| FP14 | :423,427-431 — "40 releases / 1758 BOM lines" | P2 | **FOLDED** §6 P5 (68/2615 or 41/1629, restate the method) |
| FP15 | :5 — "29 board generations" | P2 | **FOLDED** §2 fleet row (**28**) |
| FP16 | :45-47 — D-BACK 24/5/1/0 | P2 | **FOLDED** §2 D-BACK row (39 total) + §7 by-TARGET box |
| FP17 | :30-34,384-385 — "10 rows in 0.89 s"; R-LEN/P-PREC PASS on an empty subject | P2 | **ACTION-OWED** H10 *(the count is folded at §6 P0; the vacuity is not)* |
| FP18 | :70,73 — USBLC6-2SC6 "`escape:` in 7 of 12", "worst four" | P2 | **FOLDED** §6 P1 (6 of 12; 6 carry none) |
| FP19 | :267-268 — `P-PREC` is RED; two failures of different shape | P2 | **ACTION-OWED** H9 |
| FP20 | :777-779 — Freerouting benchmark (dup of FP4) | P2 | **FOLDED** §11 bullet 2 + §12 Q1 |

#### `resume_state.md` — 5 findings (P0 1 / P1 3 / P2 1)

| # | lines — claim | P | disposition |
|---|---|---|---|
| RS1 | :66,103-104,110-127 — cooksense "blocked, v1.7 candidate", §3A | P0 | **ACTION-HERE** §9-r5 |
| RS2 | :67,177-247,302 — "pluto-rx2-8way-v2 THE NEW BOARD", floorplan "UNAUTHORED" | P1 | **ACTION-HERE** §9-r5 |
| RS3 | :62-71 — 6-row board table presented as the fleet | P1 | **ACTION-HERE** §9-r5 |
| RS4 | :124 — `owed_skill_patches.md` at a path that does not exist | P1 | **ACTION-HERE** §9-r5 *(amend b)* |
| RS5 | :161,291,342 — §3C items already landed; wrong skill set | P2 | **ACTION-HERE** §9-r5 |

#### `fix_routing_to_industry_standards.md` — 3 findings (P2 3) — *document deleted after this lands*

| # | lines — claim | P | disposition |
|---|---|---|---|
| FR1 | :68 — "`policy_audit.py:1281` selects high-current nets" | P2 | **FOLDED** §7 R1 (cite the span `:1281-1305`; `:1295` selector, `:1304` grade) |
| FR2 | :718,723 — revision-3 residue the rev-4 body reverses | P2 | **FOLDED** §7 R6 (un-demoted) + §2 congestion row + §13 (`global_route.py` deferred) |
| FR3 | :543-546 — `C422`/`C32` distances transposed | P2 | **FOLDED** §4 X5 (C32 17.7 / C422 27.8 / C201 30.2, correct order) |

#### root `contracts.md` — 2 · `RESUME.md` — 1 · `pluto-rx2-8way-v3` — 1 resolved · `lipo3s_trace.md` — 1

| # | lines — claim | P | disposition |
|---|---|---|---|
| CM1 | :14-24,30-46 — coverage rule scopes to `git ls-files`; 3 root plans FAIL C-ALLOW | P1 | **FOLDED** — plan "Home:" ¶ (:47-52) names exactly this and widens `docs/contracts.md` *(addendum below)* |
| CM2 | :30-46 — the corpus has no index | P2 | **ACTION-HERE** §9-r8 |
| RM1 | `projects/usb-hub-3s-v3/RESUME.md:1-12` — "no currently-orderable release" | P1 | **ACTION-HERE** §9-r6 |
| PV1 | `pluto-rx2-8way-v3` — scaffold-only board in `projects/` | P1 | **RESOLVED 2026-08-26** — moved intact to `archived_projects/pluto-rx2-8way-v3/` |
| LT1 | `lipo3s_trace.md:1-8,155-169` — dead pre-run trace, gitignored | P2 | **ACTION-HERE** §9-r3 |

### New §9 rows owed (paste into the §9 table)

| action | why |
|---|---|
| **H1 — routing-readme congestion (closes P0-b).** Rewrite :102's *what it needs* cell to "placement + per-net route-time widths"; fold §2's corrected table (median 0.39 / **p90 0.98** / 282 of 3036 tiles over capacity / ρ **+0.471**) into :102-115; add the broken first spike (a swallowed `except` → 0.330 mm for all 208 nets) to §5; amend :16 to state the spike-result precondition | `grep -cin 'spike\|spearman\|0\.471\|3036' routing_readme.md` = **0** — the plan has the numbers, the document that becomes canon does not |
| **H2 — routing-readme F1/F2 exemplar (closes P0-c).** Qualify :225's "0/1 routed, 5 of 26 pads" as the **wave-8 snapshot**, add "(101.6 mm + 13 vias laid there; fully connected at r24 — 145.0 mm, 20 vias)"; delete ":238 or refuses to complete"; rewrite :183 "It is still the defect we shipped" | the canon gate on `r24` lists 18 unconnected and VIN_PROTECTED is not among them — the exemplar is *expensive*, not infeasible, and F1's whole thesis rests on it |
| **H3 — routing-readme keepouts.** 18 → **17** at :83 and :128; split into "1 region-level exclusion rect (a corridor guess)" + "16 per-pad via reservations (deliberate, load-bearing, 6 provably stale)"; scope :128's "principled version" remedy to the region rect alone | `python3 -c "import yaml;print(len(yaml.safe_load(open('projects/programmable-usb2-hub/03_src/route.yaml'))['prep']['keepouts']['rects']))"` = **17**. Calling 16 deliberate reservations "a human guessing at congestion" mis-aims R5 and §7's global-routing argument |
| **H4 — routing-readme wave count.** :195 "29 sequential KRT invocations, `r0 → … → r29`" → "**24 executed**, `r0 → r24`, from **29 authored**"; :84 "29 hand-authored waves" → "29 authored, 24 executed" | `grep -c '=== wave' …/route-latest.log` = **24**; `06_build/route/` holds r0–r24 (25 files) and no r25–r29 |
| **H5 — routing-readme standards citation.** :192 IPC-2152 → **IPC-2221A**, and decide `design-policies.md:64` (R2, "Width from current (IPC-2152)") in the same commit | `grep -n 'IPC-215\|IPC-2221' skills/kicad-pcb/references/design-policies.md` → :58, :64 still cite IPC-2152 while `rules_audit.py:78-84` implements IPC-2221A. §2:125-127 flags the mismatch and does not resolve it |
| **H6 — routing-readme measured-number sweep (6 P2s, one edit pass).** :228-229 → "177.1 s of a 341.1 s chain — **51.9%**" plus `route:signal` 33.0 s median / 194.9 s max; :257-259 → 4 of 8 netclasses are **below** 0.25 mm, the load-bearing fact is that none reaches the 0.5 mm selector; :226-227 → cite the r7 artifact, not `route-latest.log`; :141-142 → "24 headers at lines 10,087-10,156 of a 10,159-line log", drop the F1 pointer; :160-161 → "no router **RUN**"; :265-266 → the substring `length` inside "lengthens"/"slot-lengthened", drop "for its whole history" | `grep -c '0.1375' …/route-latest.log` = **0**; `wc -l` = 10,159 with first/last wave headers at 10,087/10,156. Each becomes canon on promotion, and §9-r2 gates only the P0s |
| **H7 — routing-readme F1 diagnostic.** :221-223's "a router that produces the identical duration eight times is exhausting a cap" is refuted by its own next line (`43 45 46 48 48 50 51 52` s — 22% spread). Replace the discriminator with the `Total time:` vs wall gap (35.6 s across 35 KRT summaries vs 341.1 s of route stages) and do **not** write "`Total time:` is a search counter" — `route.py:1467` prints seconds | applying the doc's stated diagnostic to the doc's stated data yields the opposite of F1's conclusion; this is the reasoning defect, not a number |
| **H8 — widen §9-r2's gate.** Promotion of `routing-readme.md` blocks on **all 23 corpus findings**, not 5; and the give-up FIX text filed with P0-d/P0-e (42 / 29,641,605 / 74.9–75%) is **rejected** — the number is **19** | 2 of the 5 P0s prescribe the double-count artifact; the 5 P0s are 3 distinct defects; and the why-column's "four wrong numbers" is itself an undercount (≥12, enumerated above) |
| **H9 — `P-PREC` is RED before §6 P2 extends it.** `/usr/bin/python3 tests/t1_layout_precedent.py` → **10 passed, 2 failed**. The two are different shapes: `PREC_GRADED_FLOOR` 14 → 17 (the fleet improved; raise it — the designed workflow) and `programmable-usb2-hub` `PREC_OWED_CEILING` **got 10, want 6** (the redesign added un-graded in-scope parts — a real regression). Fix both before `P-PREC-FETCH` lands | §6 P2 extends `P-PREC` and the plan never mentions its test is red; the two failures need opposite responses |
| **H10 — `--phase parts` must name its row set and refuse vacuous passes.** §6 P0's enabler runs `R-LEN` and `P-PREC` over an **empty subject** and they PASS. List the IDs `--phase parts` selects and grade a no-copper subject `N-A`, never `PASS` | canon G-VACUOUS at the stage the plan says decides everything; §6 P0 folds the count correction (9–12 rows, 0.45–0.87 s, exit 1) and drops the vacuity |

### Row-text amendments (existing §9 rows close nothing as written)

- **amend a — §9-r3.** "Delete `lipo3s_trace.md` + `.gitignore:5`" leaves
  `routing_readme.md:13-18` citing a deleted file. Add: *rewrite :13-18 with
  `fix_routing_to_industry_standards.md:726-729`'s wording and drop the
  "kebab-case … and nothing else" clause.* The convention is real but is not the
  gate: `find skills/kicad-pcb/references -name '*.md'` → **19** files, **0**
  non-kebab (the finding says 21), and `references/contracts.md:10` allows `*.md`.
- **amend b — §9-r5.** Deleting `resume_state.md` orphans the owed-skill-patch
  ledger: `find . -name owed_skill_patches.md -not -path './.claude/*'` returns
  **two** paths, both under cooksense v1.7 (`07_releases/…` sealed/IMMUTABLE and
  `06_build/staging/…` build output). Copy it to `docs/owed-skill-patches.md`
  (`docs/contracts.md:14` allows `*.md`) **before** the delete.
- **amend c — §9-r7.** Creating `examples/routing-economics-2026-08/` closes
  nothing until :33, :83 and :259 are re-pointed at it. `grep -c 'projects/'
  routing_readme.md` = **0** — the paths are project-relative
  (`06_build/logs/route-latest.log`, `03_src/route.yaml`), so `ISO_RE`
  (`scripts/contracts_audit.py:109`, applied at :476 only to `skills/` paths)
  passes the file. C-ISO is violated in substance, not in syntax; widening
  `ISO_RE` is an owed follow-up with its own known-bad, not a blocker here.
- **addendum — the "Home:" ¶ (CM1).** The plan's own file is untracked and moved
  the stray ratchet: `contracts_audit.py --present` now reports **126** stray
  files in **4** units (was 125 / 3) — the new unit is `docs`. Landing this plan
  must commit `docs/pipeline-fix-master-plan.md` in the same change, or it
  reproduces the C-ALLOW/stray condition it cites as its reason for not sitting
  at root.

### Census

> **56 findings → 33 action (15 ACTION-HERE, 18 ACTION-OWED), 21 folded, 1 no-action, 1 resolved.**
> By document: `routing_readme.md` 7 here / 16 owed; `fix_pcb_design.md` 18
> folded / 1 owed / 1 no-action; `resume_state.md` 5 here;
> `fix_routing_to_industry_standards.md` 3 folded; root `contracts.md` 1 folded /
> 1 here; `RESUME.md` and `lipo3s_trace.md` 1 here each;
> `pluto-rx2-8way-v3` 1 resolved.
> §9 grows from 8 rows to **18**.

### Commands run for this disposition (all read-only, HEAD `809b38af` + working tree)

```
grep -c 'FAILED: Could not find route' projects/programmable-usb2-hub/06_build/logs/route-latest.log   # 19
grep -cin 'spike\|spearman\|0\.471\|3036\|282 of' routing_readme.md                                     # 0
grep -c 'projects/' routing_readme.md                                                                   # 0
python3 -c "import yaml;print(len(yaml.safe_load(open('.../03_src/route.yaml'))['prep']['keepouts']['rects']))"  # 17
grep -c '=== wave' .../route-latest.log ; ls .../06_build/route | grep -cE '^r[0-9]+\.kicad_pcb$'       # 24 ; 25
wc -l .../route-latest.log ; grep -n '=== wave' … | head -1 | tail -1                                   # 10159 ; 10087 ; 10156
grep -c '0.1375' .../route-latest.log                                                                   # 0
grep -n 'GRADES = ' skills/kicad-pcb/scripts/policy_audit.py                                            # :86 PASS/FAIL/WAIVED/HUMAN/N-A
grep -n 'IPC-215\|IPC-2221' skills/kicad-pcb/references/design-policies.md                              # :58, :64 (IPC-2152)
find skills/kicad-pcb/references -name '*.md' | wc -l                                                   # 19, 0 non-kebab
find . -name owed_skill_patches.md -not -path './.claude/*'                                             # 2 (both cooksense v1.7)
find . -name ORCHESTRATION_STATE.md -not -path './.git/*' -not -path './.claude/*'                      # template only
ls examples/                                                                                            # no routing-economics-2026-08
/usr/bin/python3 tests/t1_layout_precedent.py                                                           # 10 passed, 2 failed
/usr/bin/python3 scripts/contracts_audit.py --present                                                   # exit 1; 3x FAIL C-ALLOW; stray 126 / 4 units
git ls-files docs/pipeline-fix-master-plan.md                                                           # (empty — untracked)
```
---

## 9c. Routing-plan audit — the 83 findings, enumerated

*Closes the `**not enumerated — owed**` cell at line 42. The audit ran against
`fix_routing_to_industry_standards.md` rev 4; this table records where each
finding landed in **this** document.*

**Method.** Disposition verified per row against this file:
`grep -n '<corrected value>' docs/pipeline-fix-master-plan.md`. Legend —
**FOLDED §x:L** the corrected value is present at that line; **+owed** the
row's residue is not; **OWED** nothing of it is present; **SUPERSEDED** a later
correction overrode it; **NO-ACTION** the host sentence did not survive the
merge, so there is nothing to correct.

| id | sev | claim (against rev 4) | disposition |
|---|---|---|---|
| F01 | P0 | "18 hand-typed keepout rects" is 1 region rect + 16 per-pad seed_stub reservations; 6 of the 16 are stale | FOLDED §2:112 + X5:322-323 (`C432`,`C207`,`C211`,`30.2`) |
| F02 | P0 | `vin_protected_pre` is not "zero copper" — it lays 101.6 mm and joins 21/26 pads | FOLDED §2:113 (`101.6`) |
| F03 | P1 | `required_width_mm` is IPC-2221A, not the IPC-2152 the plan and R2 cite | FOLDED §2:115,125-127; R1:506 |
| F04 | P1 | five rows labelled `vacuity` assert `must_fail`, which `gate_contract_audit` rejects | FOLDED §9b-i:652-657 |
| F05 | P1 | §5/§7/appendix still schedule Change 2b after §3 demoted it | SUPERSEDED — R6 un-demoted (:582) by F69 |
| F06 | P1 | "42 USB net-slots"; and Change 0 contradicts `routing-pipeline.md`, it does not restore it | FOLDED R0:486 (`**34**`) **+owed**: :485 still reads "the board does neither" |
| F07 | P1 | the `soundness` fixture's "four real routed boards" is 8 (9 `.kicad_pcb`) | OWED — no routed-board denominator anywhere (`grep 'eight boards'`→0) |
| F08 | P1 | 29 waves authored, 24 timed; the 5 `tail_*` never completed a run | FOLDED §2:103-104 (`24 executed`, `29 authored`) |
| F09 | P2 | 18 keepout rects → 17 | FOLDED §2:112, R5:580, §9b-ii:684 |
| F10 | P2 | `power_nets_widths` are {0.5,1.0,1.5,2.5,3.0}, no 2.0; PWR_PORT declares 2.0 mm and routes 1.5 mm | NO-ACTION on the list (claim dropped) **+owed**: the nets.yaml-vs-route.yaml disagreement is absent |
| F11 | P2 | "Every netclass declares a 0.25 mm floor" is false (4 of 8 are 0.18/0.249) | NO-ACTION — sentence not carried |
| F12 | P2 | VIN_PROTECTED spans 64.5 mm (bbox 64.1×32.8), not 29 mm | OWED — `grep '64.5\|64.1'`→0, and it is R2a's corridor input and R1's pour-area input |
| F13 | P2 | the "reproduced on r7" block quotes 0.1375 mm, a line from `archived_projects/cook-hub` | NO-ACTION — repro block not carried (`grep '0.1375\|0.135'`→0) |
| F14 | P2 | "all 29 wave headers" is 24; replay n is 3–9, not 8–9 | FOLDED R3d:561 (`24 wave headers`); replay-n row NO-ACTION |
| F15 | P2 | `--guide-corridor` does appear in the repo (`autorouter-landscape.md:28`); it is never *passed* | NO-ACTION — claim not carried (`grep guide-corridor`→0) |
| F16 | P2 | "Four changes" is seven; the appendix omits `t1_route_deletion.py` | FOLDED §13:769; the change-count half NO-ACTION (restructured) |
| F17 | P2 | `lipo3s_trace.md` is gitignored, so it is not the "untracked at root" precedent | FOLDED §9:640 + header:47-52 (plan moved to `docs/`) |
| F18 | P2 | `R-FEAS-POUR` and `R-POUR-TRACE` fire on the same predicate (board has one zone net, GND) | FOLDED — `R-FEAS-POUR` absent (`grep`→0; survives only in the superseded predecessor) |
| F19 | P1 | §5 sequencing + "Why Change 2b comes last" still live against the demotion | SUPERSEDED — R6 un-demoted |
| F20 | P1 | §4.1/appendix commission `global_route.py` and `t1_global_route.py` with no deferral marker | FOLDED §13:764 (`global_route.py` "(deferred)") |
| F21 | P1 | Change 5's keepout removal test depends on `R-GLOBAL-KEEPOUT-DEAD`, which will never be emitted | FOLDED §7 R5:572-577 (stale-rect join, "no new theory") + §9b-ii:689 (unconnected governs) |
| F22 | P2 | "do not start 2b before 1/2a/3" is stale against the demotion | SUPERSEDED — R6 un-demoted |
| F23 | P2 | the §4.1 `correlation` gate (2 boards, pre-agreed threshold) did not fire | FOLDED R6:588-591 ("has still not been run") |
| F24 | P1 | the spike script is "kept" nowhere — it lives in a session scratchpad | FOLDED R6:585 + §13:764 (`congestion_triage.py`, 3 hits) |
| F25 | P2 | appendix "register the four" omits `t1_route_deletion.py` | FOLDED §13:768-769 |
| F26 | P2 | §3 has seven `### Change` headings, not four | NO-ACTION — section restructured |
| F27 | P2 | bare "Change 2" references survive the 2a/2b split | NO-ACTION — renamed R2a/R2c |
| F28 | P2 | 18 → 17 rects (the 18th `x0:` is `stitch.stitch_grid.avoid`) | FOLDED §2:112 |
| F29 | P2 | "Changes 1–4 add two scripts, five test files" miscounts | NO-ACTION — sentence gone |
| F30 | P2 | "every wave shows n=8/n=9" false for 14 of 24 | NO-ACTION — row not carried into §2 or §9b-ii |
| F31 | P2 | dup of F15 (`--guide-corridor` "appears nowhere") | NO-ACTION |
| F32 | P2 | dup of F11/F10 (netclass floors + widths) | NO-ACTION |
| F33 | P2 | Change 0 lands before `t1_route_economics.py`, i.e. before its own `wave_order` fixture | OWED — §10 schedules R0 with no suite (`grep wave_order`→0) |
| F34 | P2 | three more passages treat 2b as live, incl. the §7 risk row | SUPERSEDED — R6 un-demoted |
| F35 | P2 | header "one blind gate and one bound" undercounts by five | NO-ACTION — header gone |
| F36 | P2 | promoting `routing_readme.md` verbatim exports a pre-spike RUDY recommendation | FOLDED §9:639 ("do not promote until its 5 P0s close") |
| F37 | P0 | `UNREACHED` is not in `policy_audit.py:86 GRADES`, so such rows are counted by the writer and dropped by the reader | FOLDED X3:279-291 (tuple quoted verbatim; `UNGRADED`/`UNREACHED` both present) |
| F38 | P0 | `denominator-census.md` bounds the conversion to exactly 4 check IDs; "every row that can produce an empty set" is the opposite instruction | FOLDED X1:218-249 (four IDs named; stale-anchor correction; re-anchor by `grade("<ID>"`) |
| F39 | P0 | three `vacuity` rows are mislabelled known-bads; no new gate ships a declared blind spot | FOLDED §9b-i:652-657 |
| F40 | P0 | `t1_fleet_regrade.py` is a release-gate suite, not a policy sweep; it never invokes `policy_audit` | FOLDED V2:620-622 |
| F41 | P1 | `current:` is already REQUIRED and bound; `classes.<C>.routing` is the OWED key that already owns pour-vs-track | FOLDED R1:505 **+owed**: the `routing:` OWED-key retirement is absent (`grep 'classes.<C>'`→0) |
| F42 | P1 | an unregistered fifth suite is a hard failure of `t_every_suite_propagates_and_is_wired_in` | FOLDED §13:768-770 |
| F43 | P1 | three fixtures name a live `04_kicad/` board and no oracle | FOLDED §9b-i:663-666 (three legal oracles, never live `04_kicad/`) |
| F44 | P1 | `skills/kicad-pcb/scripts/contracts.md` has no per-script registry — only 16 of 51 scripts are named | FOLDED §13:774-775 ("patterns only") |
| F45 | P1 | an `R-LADDER` row with a number in the Grade cell is invisible to `parse_report` | FOLDED R4:566-570 (grade cell from `GRADES`, ratio in Detail) |
| F46 | P1 | the spike has no in-tree existence; its output `rudy.png` violates the board contract's *Forbidden at root* | FOLDED R6:585 (script) **+owed**: `rudy.png` unmentioned (`grep rudy`→0) |
| F47 | P1 | `routing_readme.md`'s citations resolve only against a live board (C-ISO / clean-room) | FOLDED §9:644 (`examples/routing-economics-2026-08/`) |
| F48 | P1 | RED-first is scoped by CLAUDE.md to fixing an existing gate; new gates need an adjacent-property re-verify | FOLDED §9b-i:658-662 |
| F49 | P2 | dup of F03 (IPC-2221A) | FOLDED §2:115,125-127 |
| F50 | P2 | 17 rects; and `prep.waves.groups` defines 30 groups while `route.waves` chains 29 — `preseeded_usb` is dead | FOLDED §2:112 **+owed**: the dead group is missing from R5's deletion inventory (`grep preseeded`→0) |
| F51 | P2 | `route.race` is already bound at `03_src/contracts.md:435`; only the derived caps are owed | FOLDED R3b:559-560 |
| F52 | P2 | the real root-`contracts.md` precedent is `resume_state.md`, not gitignored `lipo3s_trace.md` | FOLDED §9:640,642 + header:47-52 |
| F53 | P0 | dup of F02 ("45.6 s, zero copper") | FOLDED §2:113 |
| F54 | P1 | 189 unconnected is the un-refilled ratsnest; the canon gate reports 18 | FOLDED §2:110 + §9b-ii:681 |
| F55 | P1 | A-AMP already sees the ampacity and is RED — nothing in the route path calls it | FOLDED R1:519 |
| F56 | P0 | the prose IS machine-read (`parse_amps`→`(10.0,'number')`); `pour_fed:` already exists | FOLDED R1:504-505 + §1 instance 5 **+owed**: `pour_fed:` reuse absent (`grep`→0) |
| F57 | P0 | `rail_power` is not removable (2.5 mm > 2.033 mm floor); and the pour has no layer/region/priority | FOLDED §9b-ii:679 ("pour **whose copper is specified**"), 112 s claim dropped **+owed**: no layer/region/priority or In1-USB-reference note (`grep 'In1\|priority'`→0) |
| F58 | P1 | R-FEAS at netclass width fires on legal `neckdown_length: 0.5` geometry, so `soundness` is unachievable | FOLDED R2a:528-530 ("bound it to the declared neckdown floor") |
| F59 | P1 | Change 1 never states a numeric threshold; PWR_IN is 4 nets → 4 zones | FOLDED R1:512-513 |
| F60 | P1 | nothing in the repo grades a zone's ampacity, so the pour trades a computed FAIL for a declaration | FOLDED R1:515-517 + §12 Q2 |
| F61 | P2 | `current_a:` needs a `### keys` row or G-ORPHAN fails it | OWED — §13 names the template file only (`grep 'G-ORPHAN\|schema_reader_audit'`→0) |
| F62 | P2 | dup of F03 | FOLDED §2:115,125-127 |
| F63 | P2 | give-ups are 42 / 74.9%, not 11 / 59% | SUPERSEDED — 19 events; §2:106 bans both 11 and 42 by name |
| F64 | P2 | 42 → 34 USB net-slots | FOLDED R0:486 |
| F65 | P2 | widths list wrong; SWITCH_POWER is the board's largest *relative* ampacity gap (1.0 vs 2.033 mm) | FOLDED R1:513 (out of R-POUR scope) **+owed**: the 2.03× shortfall is named nowhere as a live gap |
| F66 | P2 | `< 200 s` is unreachable by the named mechanisms; `route:signal` is the largest stage and is unmentioned | FOLDED §9b-ii:680 ("state the lever or drop the target") + §2:109 + §12 Q4 |
| F67 | P0 | the 7× is KRT's internal `Total time:` counter vs wall; same-clock it is 1.1× | FOLDED R0:488-490 ("~9% … not the 7× claimed") |
| F68 | P1 | `r0` is not track-free — 150 segments + 171 vias, and the wave-8 blocker is that seed copper | NO-ACTION — "track-free"/"zero competing copper" not carried; verdict unchanged per the finding's own refutation |
| F69 | P0 | the RUDY spike read the 0.25 mm netclass floor; at route-time widths p90 0.36→0.98 and ρ +0.264→+0.471 | FOLDED §1 instance 3:67 + §2:111 + R6:582-584 |
| F70 | P1 | the spike is one board / wave-seconds proxy — not the §4.1 two-board tiles-vs-failed-nets gate | FOLDED R6:588-591 |
| F71 | P1 | `current:` is parsed and already graded by A-AMP; the real defect is that `parse_amps` takes the 10 A fuse rating | FOLDED R1:504-510 + X4:303-314 |
| F72 | P1 | dup of F03 | FOLDED §2:115,125-127 |
| F73 | P1 | state the threshold X; switch nodes need a graded `pour_exempt:` because nets.yaml declares 1.0 mm islands | FOLDED R1:512-513 **+owed**: no `pour_exempt:` key (`grep`→0) |
| F74 | P1 | the guided/unguided A/B is not free — `_race_candidate` gives every lane identical cfg | OWED — R6 ii/iii still gated with no per-lane-config prerequisite (`grep per-lane`→0) |
| F75 | P1 | KRT guides are documented best-effort and one polyline set per invocation, not per-net | OWED — no guide-granularity note survives |
| F76 | P1 | the give-up denominator omits the multipoint MST router entirely (62% of logged iterations) | FOLDED §2:106-107 (19 events, attribution stated) **+owed**: `grep 'MST\|multipoint'`→0; §9b-ii:677 books "method stated" as an obligation, not a value |
| F77 | P2 | `19,031` is `sorted[n//2]`, not the median; `statistics.median` = 16,444, and max/median is 282×, not 240× | **OWED — FLAG.** §2:105 still prints `median **19,031**`, and §9b-ii:678's target `≤ 10× median success (190 k)` is derived from it |
| F78 | P2 | 18 → 17, so the keepout third of the success criterion is already met without deleting anything | FOLDED §2:112 + §9b-ii:684 |
| F79 | P2 | replays are 3–9 per wave, distribution {9:6, 8:6, 7:3, 5:8, 3:1} | NO-ACTION — row not carried |
| F80 | P2 | the 8 replays were config *iterations*; `race` re-rolls one fixed recipe and cannot substitute | OWED — R3b:557-558 keeps `race` without the distinction |
| F81 | P2 | 112 s → 114.3 s; and the 341 s baseline excludes the 5 `tail_*` waves | FOLDED §2:103-104; the 112 s claim was dropped |
| F82 | P2 | dup of F12 (span) + F13 (clearance) | OWED (span, per F12); clearance NO-ACTION |
| F83 | P2 | the 10 over-capacity tiles are the MGMT_P/MGMT_N pair, and the spike prints no per-net attribution | SUPERSEDED on the tile count (282 tiles at route widths, :111) **+owed**: `congestion_triage.py` still has no attribution print (`grep 'MGMT\|attribution'`→0) |

**Census (83 = 44 + 13 + 9 + 5 + 12).** FOLDED clean **44**; FOLDED with a
named residue still owed **13** (F06, F10, F14, F16, F41, F46, F50, F56, F57,
F65, F73, F76, F83); OWED entire **9** (F07, F12, F33, F61, F74, F75, F77, F80,
F82); SUPERSEDED **5** (F05, F19, F22, F34 by the R6 un-demotion; F63 by the
19-event count); NO-ACTION **12** (F11, F13, F15, F26, F27, F29, F30, F31, F32,
F35, F68, F79 — host sentence did not survive the merge). By severity of the
22 not-fully-folded rows: P0 **2** (F56, F57 — both residues), P1 **8**, P2 **12**.

**Flag — one finding is not merely unfolded, it is contradicted.** F77:
`§2:105` carries `median **19,031** iterations`, which the audit measured as
`sorted(v)[len(v)//2]`, not the median. Re-measured on the file §14 names:

```
/usr/bin/python3 -c "import re,statistics;t=open('projects/programmable-usb2-hub/06_build/logs/route-latest.log',errors='ignore').read();
v=[int(x.replace(',','')) for x in re.findall(r'Route found in ([\d,]+) iterations',t)];
print(len(v), statistics.median(v), sorted(v)[len(v)//2], 4637949/statistics.median(v))"
→ 70  16444.0  19031  282.0
```

so `§9b-ii:678`'s target `≤ 10× median success (190 k)` should read **164 k**,
and the `240×` this document dropped was really **282×**. This is the same
upper-middle-vs-median error class as §1, committed inside §1's own table.

**Second flag — scope.** Line 15's `folded into the numbers throughout` is true
for 44 of 83 and partly true for 13 more; 27 rows are unfolded, unsuperseded, or
actively wrong. Replace that cell with `44 folded / 13 partial / 9 owed /
5 superseded / 12 no-action — enumerated in §9c` and delete the
`**not enumerated — owed**` cell at line 42.

---

## 9b-iii — The six owed known-bads, specified

*Rev 1 specified known-bads for X1 and X2 only. `gate_contract_audit.py:197-198`
blocks any new gate without one, so these are landing conditions, not polish.*

### The mechanics every row below must satisfy

`has_red_fixture` (`gate_contract_audit.py:133-160`) is a proxy with two exact
requirements: some `tests/t*.py` must contain a **quoted** `"<stem>.py"` literal
**and** the token `must_fail`. A bare name in a docstring does not count (that
hole shipped once). New suites additionally need `sys.exit(main())` and a
`run_tests.sh` row — `t4_regressions.t_every_suite_propagates_and_is_wired_in`
measures both.

**Two of the six have no G-RED host at all, measured:**

```
/usr/bin/python3 -c "import sys;sys.path.insert(0,'skills/kicad-pcb/scripts');
import gate_contract_audit as g; print(sorted(g.SKIP_BASENAMES))"
```

`generate_board_generic.py` and `route_and_stitch_generic.py` are both in
`SKIP_BASENAMES`, so they are **not in the 46-gate inventory** and G-RED never
asks them for a fixture:

| host | in inventory | in SKIP |
|---|---|---|
| `placement_gates.py` | yes | no |
| `policy_audit.py` | yes | no |
| `rules_audit.py` | yes | no |
| `generate_board_generic.py` | **no** | **yes** |
| `route_and_stitch_generic.py` | **no** | **yes** |

So **PL1 must not land inside `generate_board_generic.py`** and **R2c's graded
half must not land inside `route_and_stitch_generic.py`** — in either place the
gate is invisible to the gate-on-gates and its fixture is voluntary. Hosts
below are chosen accordingly.

### Vacuity is both or neither

`check_vacuity` (`gate_contract_audit.py:559-649`) fails **a declaration with no
fixture** (:581), **a fixture with no declaration** (:589), a fixture whose
*first* assertion is `must_fail` (:598), and a fixture whose `gate=` basename is
**not in the verdict-printing inventory** (:623). Consequence for R2c: a
`kind="vacuity"` fixture naming `route_and_stitch_generic.py` is a hard FAIL —
another reason the graded half needs its own script.

`VACUITY_FLOOR = 13` (`:483`) and only ratchets up. Measured at `809b38af`:

```
/usr/bin/python3 skills/kicad-pcb/scripts/gate_contract_audit.py
  coverage: 46/46 verdict-printing scripts audited (69 scanned, 16 skipped)
  G-VACUOUS: 13/46 gate(s) declare a vacuity condition WITH a fixture (floor 13); 33 OWED
```

All six items below earn a vacuity, so **`VACUITY_FLOOR` goes 13 → 19**, raised
in the same commits that earn it, never ahead of one.

---

### X3 — closed vocabularies

**Host problem first.** X3 as written widens `tests/t1_contracts.py:425-437`, and
a test cannot carry a `VACUITY:` docstring block that `gate_contract_audit`
reads. Give the closure a verdict-printing home — fold it into
`schema_reader_audit.py` (already grades the SKILL, canon G-ORPHAN) or mint
`vocabulary_audit.py` — or X3 forfeits its vacuity declaration entirely.

| fixture | input that FAILS | oracle |
|---|---|---|
| `t_kb_emitted_id_has_no_canon_row` | scratch copy of `design-policies.md` with the `R-POUR` row deleted, against a `policy_audit.py` still emitting `grade("R-POUR"` at `:1304` | **constructed** (scratch canon) + a live read of `skills/`, which is the subject — the `t1_schema_reader` precedent (grades the SKILL, not a board) |
| `t_kb_canon_row_has_no_emitter` | scratch canon carrying `\| R-BOGUS \|` that no `skills/*/scripts/*.py` emits → FAIL naming `R-BOGUS`. **This direction does not exist today** — `t1_contracts.py:425` runs emitted→canon only; the reverse exists solely for `GG-*` (`t1_trace_audit.py:866`) | **constructed** |
| `t_kb_grade_cell_outside_GRADES` | a synthetic rendered `policy_audit.md` with one Grade cell `UNGRADED` while `policy_audit.py:86` still reads `GRADES = ("PASS","FAIL","WAIVED","HUMAN","N-A")` → `parse_report` drops the row, `report_inconsistencies` must report the shortfall, not a silent count | **constructed** |
| `t_kb_UNREACHED_is_a_decided_case` | a report row graded `UNREACHED` → the gate must FAIL until X3 has explicitly *decided*: admit it to `GRADES`, or name the exempt emitters. Measured: **57 occurrences across 7 scripts** — `grep -c UNREACHED skills/kicad-pcb/scripts/*.py` → `build_provenance.py`, `copper_length_audit.py`, `electrical_invariants.py`, `escape_check.py`, `net_reference_audit.py`, `policy_audit.py`, `waiver_provenance.py`. Implementing rev 1's sentence silently drops those rows | **constructed** + live `skills/` read |

**Vacuity: YES.** `emitted()` is
`re.findall(r'(?:grade\(|rows\.append\(\()"([A-Z][A-Z0-9-]+)"', txt)` — a
**string literal** matcher. A gate emitting `grade(f"R-{fam}", …)` passes X3
with the graded fact false. `t_vac_x3_runtime_built_id_is_invisible`: assert
`must_pass` on a scratch gate emitting an f-string ID with no canon row, then
the contrast — the same ID written as a literal FAILS.

---

### X4 — G-STALE-NEG

New gate `skills/kicad-pcb/scripts/negative_claim_audit.py` (inventory: yes).

**The headline known-bad is the root cause, and it pins by two shas 15 minutes
apart.** Measured:

```
git show 555a97d0:skills/kicad-pcb/scripts/gate_contract_audit.py | sed -n '11,17p' | md5sum
git show 809b38af:skills/kicad-pcb/scripts/gate_contract_audit.py | sed -n '11,17p' | md5sum
   both 098e3a84a51f8ac9248a088df3f66646     # the claim is BYTE-IDENTICAL at HEAD
```

```
git show 555a97d0:skills/kicad-pcb/scripts/rules_audit.py  -> parse_amps('7 A worst case') = None
                  (claim TRUE; and note the bare '7 A' already returned 7.0)
        HEAD      -> parse_amps('7 A worst case') = (7.0, 'number')   # claim FALSE
```

`555a97d0` (07:xx) wrote the claim; `a98fabc9` (07:55:13, **2 commits later**,
*"A-AMP graded 10/57 → 53/57, because a qualifier silenced it"*) falsified it.
Nobody re-ran it, and the claim reached `809b38af`.

| fixture | input that FAILS | oracle |
|---|---|---|
| `t_kb_stale_negative_claim_is_caught_on_the_real_bytes` | `git show 555a97d0:…/gate_contract_audit.py` as the claim-bearing document, probed against `git show a98fabc9:…/rules_audit.py` → FAIL naming the claim and printing the measured `(7.0, 'number')` | **pinned git sha ×2** (oracle #1, strongest) |
| `t_kb_negative_claim_with_no_probe` | the same docstring with the `PROBE:` line removed → FAIL. A negative claim with no re-runnable command is the whole defect class | **pinned sha** |
| `t_kb_probe_output_recorded_but_never_rerun` | a claim whose `PROBE:` records `None` while executing it yields `(7.0, 'number')` → FAIL on the *disagreement*, not on the absence | **pinned sha** |
| `t_probe_that_still_holds_passes` *(clean, not known-bad, but required)* | the same claim probed against `git show 555a97d0:…/rules_audit.py` → PASS. Without it the gate is "ban negative claims", not "date them" | **pinned sha** |

**Vacuity: YES.** Detection is by pattern (`cannot`, `never`, `returns None`,
`zero`). The identical falsifiable content written affirmatively — *"`parse_amps`
handles bare numbers only"* — carries no trigger word and is invisible.
`t_vac_g_stale_neg_affirmative_phrasing_is_invisible`: `must_pass` on the
affirmative sentence, then the contrast — the same sentence rewritten as
*"cannot parse a qualifier"* FAILS.

---

### X5 — CFG-SUBJECT

New gate `skills/kicad-pcb/scripts/config_subject_check.py` (inventory: yes).

**The threshold is measured, not chosen.** Every per-pad keepout rect in
`03_src/route.yaml` names a refdes-and-pad in its trailing comment. Distance from
rect centre to the named footprint's origin, over all 16 (footprint origin is a
pcbnew-free proxy for the pad; the pad-centre method collapses the low group
further and widens the gap):

```
C34 0.775 · C426 0.780 · U9/U10/U11/U12 1.455 · U13/U14/U15 2.875 · U6 5.130
                        ── empty ──
C32 18.292 · C422 27.561 · C201 29.541 · C207 ABSENT · C211 ABSENT · C432 ABSENT
```

Ten correct reservations span 0.775–5.130 mm; then **nothing until 18.292 mm**.
The threshold sits in that empty gap (the `t1_converter` plate-collision idiom:
`0.0008 → 0.0677 mm`). And this reproduces the plan's *"6 of the 16 are stale"*
by an independent method: **{3 ABSENT} ∪ {3 over 18 mm}**.

`grep -c '"C432"' projects/programmable-usb2-hub/04_kicad/programmable_usb2_hub.kicad_pcb` → `0`
(same for `C207`, `C211`; `C32`/`C422`/`C201` → `2` each, i.e. present but far).

| fixture | input that FAILS | oracle |
|---|---|---|
| `t_kb_config_names_an_absent_refdes` | a `route.yaml` rect commented `# C432.2` against a board carrying no `C432` → FAIL naming `C432` and the config line number | **pinned git sha** — `git show 809b38af:` on **both** `03_src/route.yaml` **and** `04_kicad/programmable_usb2_hub.kicad_pcb` (both tracked; verified). Live reads are illegal here: R5 deletes these six rects, and a live fixture would break on the fix — `tests/README.md:315-328`, third instance |
| `t_kb_config_coordinate_has_drifted` | rect commented `# C32.2` whose centre is **18.292 mm** from `C32` → FAIL naming the ref and the distance | **pinned sha ×2** |
| `t_kb_gate_on_defaults_does_not_report_a_pass` | invoke a config-accepting gate with the config **absent** → must print `ran on DEFAULTS`, never a bare PASS. Measured: `git ls-files \| grep -c placement_gates.json` → **0**, and `find . -name placement_gates.json -not -path './.git/*'` → **0**. `placement_gates.py` has graded every board on defaults, always | **constructed** |
| `t_correct_reservation_is_kept` *(the over-broad-fix control)* | the ten rects at 0.775–5.130 mm must all PASS. Without this the gate is "route.yaml has rects", and it deletes correct work | **pinned sha ×2** |

**Vacuity: YES.** CFG-SUBJECT resolves refdes named in a **trailing comment**.
A rect with no comment names no subject and is ungraded — the denominator is the
*annotated* rects, not the rects. `t_vac_cfg_subject_uncommented_rect_is_ungraded`:
`must_pass` on a rect with the `# C432.2` comment stripped (identical geometry,
same wrongness, zero findings), then the contrast — restore the comment, FAIL.

---

### PL1 — P-DRIFT

**Host: `placement_gates.py` (inventory: yes), or a new `placement_drift_check.py`
— never `generate_board_generic.py`** (SKIP_BASENAMES). The ~20-line port of the
`bbox_override` guard (`generate_board_generic.py:1276-1282`) is the *logic*; the
*grading* has to live where G-RED can see it.

| fixture | input that FAILS | oracle |
|---|---|---|
| `t_kb_pdrift_named_refdes_moved` | baseline = the last promoted board; candidate = the same board with one `route.yaml`-named refdes moved past threshold via `edit_board()` → FAIL naming the ref and the delta | **sealed release** (oracle #2) — `projects/usb-hub-3s-v3/07_releases/v1.11-2026-07-27/source/usb_hub_3s_v2.kicad_pcb`. Verified present; a sealed `source/` carries `.kicad_pcb`, `.kicad_pro`, `.kicad_dru`, `.kicad_sch`, `.net`, `.tsx`. "Last promoted board" **is** a sealed release, so this is the natural oracle, not a workaround |
| `t_kb_pdrift_named_refdes_vanished` | candidate with `C432` deleted while `route.yaml` still names it → FAIL. Assert inline that **X5's verdict on the same input DISAGREES** (X5 grades config→board, PL1 grades board→board): distinct denominators, so the overlap is not a duplicate — the `P-ADJ-UNREACHED` idiom |
| `t_pdrift_sub_threshold_move_is_kept` | a named refdes nudged *within* threshold must PASS. **Required, not optional**: without it P-DRIFT fires on every legal legalizer nudge and gets deleted — the `PREC_OWED_CEILING` failure (`policy_audit.py:111-132`), which this plan cites twice | **sealed release** |

**Vacuity: YES, and it is the caveat PL1 already records** ("this is a symptom
fix"). P-DRIFT's denominator is *refdes named by coordinate in `route.yaml`* — 16
on this board — not the board's parts. A wholesale placement change passes as
long as those 16 held still. `t_vac_pdrift_unnamed_part_may_move_freely`:
`must_pass` on a board where an unnamed part moved 20 mm, then the contrast — add
that ref to `route.yaml` and the identical board FAILS.

---

### R1 — R-POUR reads declared current

Host `policy_audit.py` (inventory: yes; already has red fixtures). Suite
`t1_policy_pour.py` per §13.

**The known-bad is a REAL configuration and the RED side is measured every run**
(§9b-i item 2: RED-first applies here because R1 fixes an existing gate).

Sealed `v1.11/source/usb_hub_3s_v2.kicad_pro` netclass widths:

```
Default 0.2 · SWITCH_NODE 0.6 · PWR_IN 0.6 · PWR_RAIL 0.4 · VBUS 0.8 · GATE 0.3 · GND_RET 0.25
```

`03_src/rules/nets.yaml:192` → `current: "6 A / 5 A"`. Measured:

```
parse_amps("6 A / 5 A")        -> (6.0, 'number')
required_width_mm(6.0)         -> 3.5561 mm      # rules_audit.py:84, IPC-2221A
```

`PWR_RAIL` sits at **0.4 mm**, *below* the `track_width >= 0.5` selector
(`policy_audit.py:1295`), so the pre-fix R-POUR **never sees it** while the net
declares 6 A and needs 3.556 mm. That is the defect in one row.

| fixture | input that FAILS | oracle |
|---|---|---|
| `t_kb_rpour_grades_declared_current_not_class_width` | the config above → post-fix FAIL naming `PWR_RAIL`, 6.0 A, 3.5561 mm; **`git show HEAD:skills/kicad-pcb/scripts/policy_audit.py` PASSES the identical input**, asserted inline, so the red side is measured rather than claimed | **sealed release** for board/`.kicad_pro` (oracle #2) + **pinned sha** for `nets.yaml` (oracle #1 — R1 itself adds `current_a:` to that live file, so a live read would rot) |
| `t_kb_fuse_rating_is_not_design_current` | `current: "10 A fuse"` → measured `parse_amps` = `(10.0,'number')` → `required_width_mm(10.0)` = **7.1941 mm**. A typed `current_a: 6.4` companion (→ 3.8872 mm) must WIN, and a disagreement must FAIL loudly, never silently pick one. This is the E-TOPO `AO3401A`-read-as-3401 A class one level up | **constructed** + pinned sha |
| `t_neckdown_tap_is_kept` | a net at its declared `neckdown_length: 0.5` floor must PASS — the plan's own R2a warning applied to R1: a bound at netclass width fires on legal, intended geometry | **pinned sha** |

**Vacuity: YES — and it is forced by the plan's own §11/§12.** *"Nothing in the
repo grades a **zone's** ampacity."* After R1, R-POUR passes any net that touches
a zone, with no area or width term: a 0.2 mm pour clears a 6 A net.
`t_vac_rpour_zone_ampacity_is_ungraded`: `must_pass` on a board whose 6 A net is
carried by a hairline pour, then the contrast — the same net on a trace FAILS.
Declaring it is cheaper than answering open question #2 and stops the pour
conversion from laundering a computed FAIL into an ungraded assumption.

**Ordering (already flagged in X1):** R1 changes R-POUR's population, so it must
re-run and re-anchor `docs/denominator-census.md` in the **same commit**, by
`grade("<ID>"` and not by line number — the census's own numbers are already
stale (`R-POUR :1262` recorded; actual `:1304`).

---

### R2a — R-FEAS

New `skills/kicad-pcb/scripts/route_feasibility.py` (inventory: yes). Suite
`t1_route_feasibility.py`.

| fixture | input that FAILS | oracle |
|---|---|---|
| `t_kb_rfeas_corridor_narrower_than_the_disc` | 2-layer board, two pads either side of a corridor of clear width `g`; net declares floor `w`, clearance `c`, with `w/2 + c > g/2` → **w\* < w** → FAIL naming net, layer, `w*` **to a number**, and the bottleneck edge coordinates. Ó'Dúnlaing–Yap gives `w*` in closed form here, so the assertion is on the number, not the verdict | **constructed** — the only input where `w*` is independently known. Canon M1: a checker graded against its own output proves nothing |
| `t_rfeas_widened_corridor_passes` | the identical board with the corridor widened 0.05 mm must PASS. Without it the gate is "narrow boards fail", not `w* < floor` | **constructed** |
| `t_kb_rfeas_bound_is_the_neckdown_floor_not_the_class_width` | netclass 3.0 mm, `routing:` permits 0.5 mm taps, `neckdown_length: 0.5`. **Both verdicts asserted on one input**: bound-to-class-width FAILS (wrongly), bound-to-declared-floor PASSES — so a later "simplification" of the bound cannot land silently | **constructed** |
| `t_rfeas_prints_a_denominator_on_real_bytes` | run against `v1.11/source/usb_hub_3s_v2.kicad_pcb` and assert **only** `N nets × M layers graded` — an M-COVER assertion that cannot go stale under a re-route | **sealed release** |

**Vacuity: YES — the plan already states it** ("sound, deliberately incomplete;
passing promises nothing"). `w*` is a **single-wire, per-net-per-layer** bound, so
a board where every net individually clears while a *cut* is over capacity
(Leiserson–Maley; R2a phase 2) passes with the fact false.
`t_vac_rfeas_multiwire_cut_is_ungraded`: two nets, each with `w* ≥ w`, whose
`Σ(width + clearance)` exceeds the Delaunay edge capacity → `must_pass`; contrast
— widen one net past its own `w*` → FAIL.

---

### R2c — bounded failure

**Split the change.** The mechanism (window-bounded A\*, escalation schedule,
bounded deferral) lands in `route_and_stitch_generic.py`, which is in
`SKIP_BASENAMES` and therefore **has no G-RED obligation and cannot host a
vacuity declaration**. The *graded* half must be its own script —
`skills/kicad-pcb/scripts/route_budget_check.py` — reading the run's recorded
census. Suite `t1_route_budget.py` per §13.

**Oracle problem, and it is hard-measured.** The baseline numbers (19 give-ups,
18 unconnected, 19,031 median, 4,637,949 worst, 341.0 s, p90 0.98) live in
`06_build/`, which is **ignored on this board**:

```
git check-ignore -v projects/programmable-usb2-hub/06_build/logs/route-latest.log
   projects/programmable-usb2-hub/.gitignore:1:06_build/*
git show HEAD:projects/.../06_build/logs/route-latest.log
   fatal: … exists on disk, but not in 'HEAD'
```

So **none of the three legal oracles reaches them.** They must be snapshotted into
`tests/fixtures/route_econ/` with a `PROVENANCE.md`, exactly as
`tests/fixtures/beacons/` pins the four drifted beacons verbatim at `98f4c3a`.
Fixtures reading `06_build/` directly are not admissible and would be the fourth
instance of the `tests/README.md:315-338` class.

| fixture | input that FAILS | oracle |
|---|---|---|
| `t_kb_speed_may_not_be_bought_with_connectivity` | two recorded outcomes over one board — baseline (19 give-ups / 18 unconnected) vs candidate (4 / **22**) → FAIL naming the 4 nets. **This is §9b-ii's governing rule and rev 1 shipped R2c without it** | **constructed** from the pinned fixture snapshot |
| `t_kb_search_exceeds_its_bound_without_deferring` | a wave consuming > `10 × median success` = **190,310** iterations with no deferral → FAIL naming wave and count. Baseline context: worst give-up 4,637,949 = **244× the 19,031 median** | fixture snapshot |
| `t_kb_deferral_is_bounded` | a net deferred > N (N = 3, the documented saturation point) → FAIL naming the net, never a silent re-queue. Otherwise "never terminal" becomes "never terminates" | **constructed** |
| `t_kb_committed_conflict_must_be_classified` | a committed recorded conflict with no classified disposition → FAIL. DRC findings stay CLASSIFIED, never counted (CLAUDE.md); this is open question #3 made gradeable instead of argued | **constructed** |

**Vacuity: YES, and it is the sharpest one here.** The give-up count is
`grep -c 'FAILED: Could not find route'` — a **string in a foreign tool's log**.
Reword KRT's message and the count goes to 0 and R2c reports a perfect run. Same
class as R-LEN's `length|spread` and E-TOPO's unanchored `([\d.]+)\s*A`.
`t_vac_r2c_reworded_router_message_reads_as_zero_giveups`: `must_pass` on a log
with the phrase reworded (gate reports 0 give-ups); contrast — the same log
carrying a structured `routed:` / `deferred:` census line makes the two channels
**disagree** and the gate FAILS. That contrast is X2/MISS-CENSUS applied to R2c
and is the reason R2c must read a census, not only a grep.

---

## 8 V1a — M-REL-KIND as a dated floor

### The pattern to copy, with lines

`scripts/contracts_audit.py`:

| element | lines | what it buys |
|---|---|---|
| `DEBT_CEILING` — per-unit committed map | `:135-157` | a bound that is data a reviewer reads |
| `unit_of()` — the unit is a board, never the fleet | `:356-371` | *"a FLEET-WIDE integer ceiling **breaks on a correct action**"* |
| `check_ratchet()` — **EQUALITY**, not `<=` | `:374-402` | slack cannot be banked; an improvement must be recorded in the same commit |
| coverage guard — every measured unit needs a row | `:384-389` | a map satisfiable by deleting rows is not a bound |
| staleness guard — a row the sweep no longer sees FAILS | `:390-393` | *"a bound nothing measures is not a bound"* |
| scoped to `root == default_root` | `:498`, `:534` | a fixture tree is a different inventory; the count says nothing about it |
| verdict prints the ratchet with its denominator | `:535-538` | BOUNDED / ENUMERATED / MONOTONE (`gate_contract_audit.py:58-76`) |

Sibling precedent and its recorded failure: `PREC_OWED_CEILING`
(`policy_audit.py:146-156`), whose docstring at `:111-132` is the post-mortem of
the fleet-aggregate version — *"a bound that a correct action breaks is not a
ratchet; it is a tax on commissioning."*

### What V1 would actually grade — measured at `809b38af`

```
git ls-files | grep -c 'SUPERSEDED\.md$'                         ->  47   (all under 07_releases/)
git ls-files | grep 'SUPERSEDED\.md$' | xargs grep -lni '^\s*kind\s*:' | wc -l  ->   0
```

**Zero of 47 carry a `kind:` declaration, and `07_releases/` is immutable.** A
V1 M-REL-KIND that *demands the declaration* fails all 47 with no legal remedy —
worse than the plan's "~30".

But the **derivation** needs no writes at all. Classifying each superseded
release against its immediate in-series successor:

| verdict | count | method |
|---|---:|---|
| EVIDENCE-REVISION | 17 | board `sha256` |
| COPPER-CHANGE | 13 | board `sha256` |
| EVIDENCE-REVISION | 12 | normalised gerber `sha256` (fallback) |
| COPPER-CHANGE | 4 | normalised gerber `sha256` (fallback) |
| UNGRADEABLE | 1 | `cooksense-v1.7-2026-07-30` — superseded, **no successor release exists yet** |
| **total** | **47** | |

The 17/13/16 split in §2 reproduces exactly on the board-`sha256` arm
(17 identical + 13 changed + **16 release dirs with no `.kicad_pcb`**), and the
47th is the no-successor row §2 does not name. **All 16 board-less releases carry
a gerber zip**, and the normalised hash resolves every one — so §8's
*"specify the gate's behaviour on a board-less release"* has a real answer, not
an aspirational one: hash the zip with `G04`/`;`/`CreationDate`/
`GenerationSoftware` lines stripped, via `fab_payload_census.py`, which already
parses GERBER TEXT (canon M-SHIP). Worked example, `esp32-laser-timing`:
v1.0 → v1.1 **DIFFERS**, then v1.1 = v1.2 = v1.3 = v1.4 = v1.5 = v1.6 — five
consecutive evidence revisions that no board hash could ever have seen.

**Derivable: 46 of 47.** The one exception self-resolves when cooksense v1.8
seals. Report it as `UNGRADEABLE (no successor)` with its reason — never a
silent pass (canon M-COVER).

### The specification

```python
# skills/kicad-pcb/scripts/policy_audit.py — beside M-REL (:1630, :1723)
#
# M-REL-KIND grades the SUPERSEDE KIND. Two halves, scoped differently, and the
# asymmetry is the whole point (the PREC_OWED_CEILING lesson, :111-132).
#
# DERIVED — runs on ALL 47 rows, every run, needs no write anywhere:
#   board sha256(R) vs sha256(successor)      -> EVIDENCE-REVISION | COPPER-CHANGE
#   no .kicad_pcb    -> normalised gerber sha256 from fab/*_gerbers.zip
#   no successor     -> UNGRADEABLE, with the reason, counted in the denominator
#
# DECLARED — a SUPERSEDED.md carrying `kind:` must AGREE with the derivation.
#   A disagreement is a FAIL. A file with NO `kind:` is DEBT, not a failure.
#
# THE FLOOR IS THE UNDECLARED SET, PER BOARD. Measured 2026-08-02 at 809b38af.
# It moves ONLY DOWN, and only when someone writes `kind:` into an existing
# SUPERSEDED.md — which CLAUDE.md already sanctions as the one legal write into
# a sealed release. A CORRECT NEW RELEASE MOVES NO ROW: the SUPERSEDED.md it
# writes is authored today, declares `kind:`, and is graded — never counted here.
# A NEW BOARD gets no row (rows exist only for a NONZERO count) and cannot
# breach another board's.
MREL_KIND_UNDECLARED = {
    "archived_projects/ble-bus-bar":           1,
    "archived_projects/crow-array-pod":        1,
    "archived_projects/crowsync-recorder":     2,
    "archived_projects/esp32-laser-timing":    7,
    "archived_projects/usb-power-3s":          3,
    "archived_projects/xt60-usb-supply-rerun": 2,
    "projects/crow-mic-pod-v2":                3,
    "projects/crow-recorder-central-v2":       7,
    "projects/pluto-rx2-8way-v4":              1,
    "projects/smc0985-cooksense":              8,
    "projects/usb-hub-3s-v3":                 12,
}                                        # sum = 47, and 47 = the whole population
```

**Baseline count: 47** — every tracked `SUPERSEDED.md` in the repo, distributed
over 11 units as above. Reproduce with:

```sh
git ls-files | grep 'SUPERSEDED\.md$' | xargs grep -Lni '^\s*kind\s*:' \
  | awk -F/ '{print $1"/"$2}' | sort | uniq -c
```

Reuse `check_ratchet()` verbatim (equality + both vacuity guards) and scope
enforcement to the default root, exactly as `contracts_audit.py:498`.

**Why the epoch is a property of the file, not a date lookup.** Keying on the
superseding release's seal date breaks on a correct action: when cooksense v1.8
lands, v1.7's *existing* SUPERSEDED.md would have to be amended, moving
cooksense's row 8 → 7 for doing the right thing. Keying on *"does this file carry
`kind:`"* has no such edge — the row falls only when someone chooses to amend,
and the equality pawl then forces the map edit into the same commit.

**Print it, and name the debt.** Following `gate_contract_audit.py:937-945`:

```
M-REL-KIND: 46/47 supersedes derived (30 evidence-revision, 16 copper-change,
            1 UNGRADEABLE: no successor); 0/47 declare `kind:`;
            undeclared debt 47 over 11 unit(s) vs 47 recorded — held
OWED M-REL-KIND archived_projects/esp32-laser-timing: 7 undeclared
… one line per unit …
```

An adoption ratchet whose remainder is a bare count is how a partial rollout
becomes permanent. The 47 are enumerated on every run, so the gap is never
silent — which is the only thing that separates a declared floor from the free
gap `contracts_audit.py:62` was written to close: *"this repo has ratchet FLOORS
and no CEILINGS, so an honestly declared gap is free."*

### Two corrections to §2 and §8 that fall out

1. **The "33 say so in prose" figure does not reproduce by any single method.**
   Four defensible patterns over the same 47 files:
   `/byte-identical/i` → **25**, the plan's likelier phrasing set → **26**,
   `/identical/i` → **38**, `/identical|unchanged/i` → **41**. State the method
   or drop the number — and note that the spread *is* the argument for grading
   `sha256`, not prose.
2. **§2's superseded row should read**: 47 files; by board `sha256` 17 identical
   / 13 changed / 16 with no `.kicad_pcb`, **+1 with no successor**; with the
   normalised-gerber fallback **46 of 47 derivable, 30 evidence-revision and 16
   copper-change**. `17 + 13 + 16 = 46`, not 47 — the missing row was
   `cooksense-v1.7`.

---

### X5 — CFG-SUBJECT: a config is graded against the board it configures

Every refdes or coordinate a config names must resolve to a real footprint at
approximately the position implied; the naming must be in a **field**, not a
comment; and any gate accepting a config file prints whether it ran on a config
or on defaults.

#### Why rev 2 is unimplementable as written

The refdes attribution rev 2 proposes to grade **does not survive the parser**.
`projects/programmable-usb2-hub/03_src/route.yaml:51-66` are bare
`{x0,y0,x1,y1}` maps with a trailing `# C432.2`:

```
$ /usr/bin/python3 -c "import yaml;c=yaml.safe_load(open('projects/programmable-usb2-hub/03_src/route.yaml'));\
r=c['prep']['keepouts']['rects'];print(len(r), sorted(r[1]))"
17 ['x0', 'x1', 'y0', 'y1']
```

Every consumer — `route_and_stitch_generic.py`, `policy_audit.py` P-KEEP,
`schema_reader_audit.py` — sees four floats. There is nothing to grade. The
fix is a schema field first, a checker second.

#### Measured, on this board

Rect-centre vs. the named pad, resolved with `pcbnew` against
`04_kicad/programmable_usb2_hub.kicad_pcb`:

| rect | line | named | nearest pad to rect centre | verdict |
|---|---|---|---|---|
| `# U13.2` `# U14.2` `# U15.2` | 51, 55, 60 | GND pad | itself, 0.735 mm | OK |
| `# U9.8` `# U10.8` `# U11.8` `# U12.8` | 53, 56, 61, 64 | GND pad | itself, 0.535 mm | OK |
| `# C426.2` `# C34.2` `# U6.42` | 52, 58, 59 | GND pad | itself, 0.005 / 0.000 / 0.662 mm | OK |
| `# C32.2` | 57 | exists | **Q8.3 (RUN_B), 1.154 mm** — C32.2 is **17.671 mm** away | WRONG |
| `# C422.2` | 54 | exists | **U14.5, 2.100 mm** — C422.2 is **27.824 mm** away | WRONG |
| `# C201.2` | 63 | exists | **C108.1 (5V_B), 1.129 mm** — C201.2 is **30.161 mm** away | WRONG |
| `# C432.2` `# C207.2` `# C211.2` | 62, 65, 66 | **no such refdes on the board** | C464.2 / C105.2 / Q5.8 | WRONG |

Discriminator that separates the two groups cleanly, with a 24× margin: **the
named pad is the nearest pad of any footprint to the rect centre** (true for
all 10 OK, false for all 3 far ones), **and** the offset is ≤ 1.5 mm
(max OK = 0.735 mm; the three far ones are 17.7 / 27.8 / 30.2 mm).

Two further defects the comment hid, both measured from the same config:

1. **The 10 "correct" rects are the wrong size.** 7 of them correspond to a
   `prep.seed_stubs` GND stub. Recomputing each reservation as
   `bbox(segments ⊕ w/2, vias ⊕ via_size/2) ⊕ route.common.clearance ⊕
   widest_netclass_half` — `via 0.30/2 + 0.15 + 0.25/2 = 0.425`, so 0.850 mm
   square around a bare via — **0 of 7 hand-typed boxes cover the computed
   box**: `C34.2` is 0.64×0.65 against 0.850×0.850; `U9.8/U10.8/U11.8/U12.8`
   are 0.57×0.64 against **1.305**×0.850 and miss the stub segment's west end
   entirely (`x0 51.15` vs `50.500`); `U6.42` is 1.55×0.60 against
   1.963×0.850. This is the identical arithmetic already written down as an
   incident on another board —
   `projects/smc0985-cooksense/03_src/cooksense/route.yaml:282`: *"at ±0.35 the
   box does not cover via_r 0.125 + gap 0.155 + track_half 0.125 = 0.405 and
   KRT enforces rects on the track CENTRELINE, so this site REFUSED on the
   race-3 chain."*
2. **17 of the 24 GND seed stubs have no reservation at all**, and the
   hand-typed set is 3-of-4 on a symmetric structure: `U13.2 U14.2 U15.2` are
   reserved, **`U16.2` (GND, 133.9, 37.5 — same row, same y) is not**.

And the gate over all of this passes:

```
$ grep -n 'P-KEEP' projects/programmable-usb2-hub/06_build/policy_audit.md
30:| P-KEEP | PASS | ... route.yaml prep.keepouts x3 |
```

`policy_audit.py:1072-1092` counts *non-empty subkeys of `prep.keepouts`* (3:
`mounting_holes`, `edge_band`, `rects`). It never opens a rect. **tests/README
`vacuity`: the checker PASSES input whose graded fact is FALSE.**

The second half of X5 stands as written and is confirmed:

```
$ find . -name 'placement_gates.json' | wc -l
0
```

`pcb_flow.py:673-674` and `skills/pcb-design/templates/03_src/rebuild_reuse.sh:87`
**always** pass `--config 03_src/placement_gates.json`; `placement_gates.py:504-506`
sets `cfg = {}` when that path is absent and prints nothing. Every board's
placement gate has run on defaults while the flow reads as configured.

---

#### X5a — the schema field

On `prep.keepouts.rects[]`, **exactly one of** these is REQUIRED:

| field | value | resolution |
|---|---|---|
| `ref:` | `REF` or `REF.PAD` (`U13.2`) | `REF` must be a footprint on the board; with `.PAD`, that pad must be the NEAREST pad of any footprint to the rect centre and within `subject_tol` (default **1.5 mm**); bare `REF`, the footprint bbox must intersect the rect |
| `why:` | one non-empty sentence | the rect is not a part reservation (the island rect at `route.yaml:46`, an RF fan, an edge band) |

`subject_tol:` is a sibling of `layers:` under `prep.keepouts`.

**Name it `ref:`, not `pin:` — and that choice is the gate's own blind spot,
not a preference.** `schema_reader_audit.py` proves a contract row by finding
each literal segment in a READ position (`read_positions`, L492-560; `prove`,
L637-670). Measured over `route_and_stitch_generic.py`'s AST:

```
$ /usr/bin/python3 - <<'EOF'
import ast; t=ast.parse(open('skills/kicad-pcb/scripts/route_and_stitch_generic.py').read())
h={}
for n in ast.walk(t):
    if isinstance(n,ast.Subscript) and isinstance(n.slice,ast.Constant): h.setdefault(n.slice.value,[]).append(n.slice.lineno)
    elif isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('get','pop','setdefault') and n.args and isinstance(n.args[0],ast.Constant): h.setdefault(n.args[0].value,[]).append(n.args[0].lineno)
print({k:h.get(k) for k in ('pin','ref','why','rects','reserve')})
EOF
{'pin': [3393], 'ref': None, 'why': None, 'rects': [451], 'reserve': None}
```

A row `prep.keepouts.rects[].pin` would score **PROVEN off `stub.get("pin")` at
line 3393** — the seed-stub pass, an unrelated structure — so G-ORPHAN would
certify the row even if the keepout emitter never read it. This is exactly the
discrimination hazard the same contract already documents for `ref`/`pad`/`text`
at `skills/pcb-design/templates/contracts/03_src/contracts.md:401-411`.
`ref`, `why` and `reserve` appear in **zero** read positions today, so deleting
their reads makes the rows go UNREAD — the read is provable.

Backward compatible: the only keys any rect has ever carried fleet-wide are
`{x0,y0,x1,y1,layer}` (census below), so no board changes meaning.

#### X5b — the contract row, and where

**File:** `skills/pcb-design/templates/contracts/03_src/contracts.md`.
**Block:** `### keys: 03_src/route.yaml`, heading at **line 412**, table header
at **419**, rows **421-463**. `| `prep.keepouts.*` | ... |` is **line 431**.
Insert **immediately after 431**, before `prep.waves.*` (432), four rows:

```markdown
| `prep.keepouts.subject_tol` | `route_and_stitch_generic.py` | max mm between a rect centre and the pad its `ref:` names before R-KOSUBJ fails (default 1.5; measured separation on programmable-usb2-hub is 0.735 mm good vs 17.7 mm bad) |
| `prep.keepouts.rects[].ref` | `route_and_stitch_generic.py` | R-KOSUBJ subject: `REF` or `REF.PAD` this rect reserves, resolved against the live board at prep. Was a YAML COMMENT on 71 rects across 4 boards and therefore graded by nothing — 6 of 16 on programmable-usb2-hub named an absent or 17.7-30.2 mm-distant part |
| `prep.keepouts.rects[].why` | `route_and_stitch_generic.py` | the explicit NOT-A-PART declaration for an island/fan/band rect; an empty string does not satisfy it (canon M-COVER) |
| `prep.seed_stubs.stubs[].reserve` | `route_and_stitch_generic.py` | emit this stub's router reservation from its own geometry instead of hand-typing a rect (X5d) |
```

The project copies carry the same table; `prep.keepouts.*` sits at
`projects/programmable-usb2-hub/03_src/contracts.md:431`,
`projects/pluto-rx2-8way-v4/03_src/contracts.md:400`,
`archived_projects/pluto-rx2-8way-v3/03_src/contracts.md:398`,
`projects/pluto-rx2-8way-v2/03_src/contracts.md:303`. Template is the source of
truth; copies re-sync on their next revision (CLAUDE.md structure governance),
and `t1_contracts.py t_skill_contract_sync` is the backstop.

Acceptance: `/usr/bin/python3 skills/kicad-pcb/scripts/schema_reader_audit.py
projects/programmable-usb2-hub` reports the four new keys **PROVEN**, and the
PROVEN floor rises by 4 (today: `420/420 declared keys graded OK (345 with a
PROVEN reader, floor 345), 6 orphan`).

#### X5c — migration

**This board, 17 rects** (`prep.keepouts.rects`, `route.yaml:46` + `51-66`):

| action | rects |
|---|---|
| `why:` added | 1 — line 46, the USB-only exclusion over the three switching-power islands |
| **deleted**, replaced by `reserve: true` on the corresponding `prep.seed_stubs.stubs[]` | 7 — `C426.2 U9.8 U10.8 C34.2 U6.42 U11.8 U12.8` (all 7 are undersized today; 0 of 7 cover the computed box) |
| `ref:` added, kept as an explicit rect **or** promoted to a seed stub | 3 — `U13.2 U14.2 U15.2`, which have **no** `prep.seed_stubs` entry. Promoting them adds the missing `U16.2` and closes the 3-of-4 asymmetry; this is the preferred form |
| **deleted** — reserve empty board | 3 — `C432.2 C207.2 C211.2`, refdes absent from the board |
| **deleted or re-derived** — the site they meant is 17.7-30.2 mm away | 3 — `C32.2 C422.2 C201.2`. Do **not** re-point the comment; re-derive from the stub that actually needs the site, or drop |

Net: 17 hand-typed rects → 1 `why:` rect + up to 3 `ref:` rects, plus **24
generated reservations** (one per GND seed stub, up from the 7 currently
covered).

**Other projects — the class swept, not one instance** (memory: *class-width:
sweep the references*):

```
$ /usr/bin/python3 -c "
import yaml,glob
for f in sorted(glob.glob('projects/*/03_src/route.yaml')+glob.glob('projects/*/03_src/*/route.yaml')):
    r=(((yaml.safe_load(open(f)) or {}).get('prep') or {}).get('keepouts') or {}).get('rects') or []
    k=set().union(*[set(x) for x in r]) if r else set()
    print(f'{len(r):4d}  {f}  keys={sorted(k)}')"
```

| project | rects | with a `# REF.PAD` comment | resolve correctly today |
|---|---|---|---|
| smc0985-cooksense (cooksense) | 108 | 43 | **43/43** |
| pluto-cal-switch | 21 | 0 (comments are NET names) | — |
| programmable-usb2-hub | 17 | 16 | **10/16** |
| pluto-rx2-8way-v2 | 15 | 6 | 6/6 |
| pluto-rx2-8way-v4 | 15 | 6 | 6/6 |
| pluto-rx2-8way | 11 | 0 | — |
| crow-mic-pod-v2 / pluto-rx2-8way-v3 | 2 / 2 | 0 | — |
| crow-recorder-central-v2, usb-hub-3s-v3, cooksense interposer | 0 | — | — |
| **fleet total** | **191** | **71** | **65/71** |

Every rect fleet-wide carries only `{x0,y0,x1,y1,layer}`. **55 of the 71
comment-attributed rects are right today and unverifiable by construction** —
they are the same defect that has not fired yet. Migration is one line per rect,
191 lines; `03_src/` is not sealed, but cooksense is released at v1.7 and
pluto-rx2-8way-v4 at v1.1, so those migrate on their next revision, not
retro-edited (CLAUDE.md immutability). **A migrated board must re-run prep and
compare the emitted rect set** — `route.yaml:451-457` prints the count.

#### X5d — the generator change: reservations EMITTED, not typed

**Where.** `skills/kicad-pcb/scripts/route_and_stitch_generic.py`:
- `_keepout_rect(pcbnew, b, x0, y0, x1, y1, layer)` — **L305-315**, the drawer.
- `ko = get(cfg, "prep.keepouts", {})` — **L401**; `mounting_holes` L405-421,
  `npth_pads` L423-438, `edge_band` L441-449, the literal rects loop
  **L451-456**, the count print **L457**, `b.Save(str(out))` **L459**.
- `preseed = get(cfg, "prep.seed_stubs")` … `p_seed_stubs(ctx, preseed)` —
  **L469-479**, and the pass itself `@stitch_pass("seed_stubs") def
  p_seed_stubs` — **L3340-3462**.

**Ordering constraint (load-bearing).** Keepouts are drawn and the board saved
at L451-459, **before** `p_seed_stubs` runs at L469-479. The reservation
emitter therefore reads `prep.seed_stubs.stubs[]` **geometry from the config**,
not placed copper, and must run inside the keepout section so its rects are on
`r0` and counted at L457.

**New block, between L449 and L451:**

```python
    seed = get(cfg, "prep.seed_stubs") or {}
    if seed.get("stubs"):
        vr = float((seed.get("via") or {}).get("size", 0.25)) / 2
        gap = float(get(cfg, "route.common.clearance", 0.15))
        half = widest_netclass_half(cfg, b)          # KRT enforces rects on the
        n_res = 0                                    # track CENTRELINE
        for s in seed["stubs"]:
            if not s.get("reserve"):
                continue
            xs, ys = [], []
            for sg in s.get("segments", []) or []:
                h = float(sg["width"]) / 2 + gap + half
                for (x, y) in sg["pts"]:
                    xs += [x - h, x + h]; ys += [y - h, y + h]
            for (x, y) in s.get("vias", []) or []:
                h = vr + gap + half
                xs += [x - h, x + h]; ys += [y - h, y + h]
            if not xs:
                die(f"prep.seed_stubs.stubs[{s.get('pin')}]: reserve: true on a "
                    f"stub with no segments and no vias — nothing to reserve")
            for lay in layers:
                _keepout_rect(pcbnew, b, min(xs), min(ys), max(xs), max(ys), lay)
            n_res += 1
        n_ko += n_res
```

and the literal-rect loop at L451 gains the subject check:

```python
    for i, r in enumerate(ko.get("rects", []) or []):
        _keepout_subject(pcbnew, b, r, i, float(ko.get("subject_tol", 1.5)))
```

where `_keepout_subject` `die()`s on: neither `ref` nor `why`; both; an empty
`why`; a `ref` whose refdes is not on the board; a `REF.PAD` whose pad is not
the nearest pad to the rect centre, **naming the pad that is**; a `REF.PAD`
farther than `subject_tol`, **printing the measured mm**.

**Print the denominator** (canon M-COVER) — extend L457:

```
keepouts: 28 rects (24 reserved from prep.seed_stubs, 4 literal: 1 why + 3 ref) on ['User.2', 'User.3']
```

**Second half — F-CFGDEF.** `placement_gates.py:497-506`: a `--config PATH`
whose file is absent becomes an **invocation error (exit 2)**, not silent
defaults; a run with no `--config` prints `config: DEFAULTS (no --config
given)`; a run with one prints `config: <path> (N keys, M waivers)`. Then
either commit a `03_src/placement_gates.json` per board or drop the flag from
`pcb_flow.py:673-674` and `rebuild_reuse.sh:87` — today all 10 boards silently
take the `{}` branch.

#### X5e — known-bad fixtures

`tests/t2_route_stitch.py`, built on `scratch(mutate)` (L46-60) — *"a project
tree with 03_src/route.yaml + 04_kicad/<board>; known-bad fixtures are this
GOOD tree broken in exactly one way"* — alongside `t_prep_keepout_layers`
(L125) and `t_prep_seed_stubs` (L143). Each `must_fail(prep(p))` and asserts
the message NAMES the subject:

| fixture | the one break | must say |
|---|---|---|
| `t_kb_keepout_rect_names_no_subject` | a rect with neither `ref:` nor `why:` | refuses, names the index — **this is the fixture that reproduces today's 191-rect fleet state** |
| `t_kb_keepout_rect_names_an_absent_refdes` | `ref: C432.2` (real fixture-board refdes changed one letter) | `no footprint 'C432'` — the `C432/C207/C211` case |
| `t_kb_keepout_rect_far_from_its_subject` | a good rect's `ref:` kept, rect translated +18 mm | prints the measured mm **and the pad that IS nearest** — the `C32.2` case (17.671 mm, nearest was `Q8.3`) |
| `t_kb_keepout_why_is_empty` | `why: ""` | an empty declaration satisfies nothing (M-COVER) |
| `t_kb_seed_reserve_with_no_geometry` | `reserve: true` on a stub with no `segments` and no `vias` | refuses rather than emitting a zero-area rect |
| `t_prep_seed_reservations_are_emitted` *(clean)* | `reserve: true` on the existing `E_PLUS U1.3` stub | stdout carries `reserved from prep.seed_stubs`, and the drawn rect's half-extent **equals** `via/2 + route.common.clearance + widest netclass half` recomputed in the test from the config — the property, never bytes (`tests/README`: assert PROPERTIES; KRT is stochastic) |

Two more, outside t2:
- `tests/t1_schema_reader.py` — the four new rows must be **PROVEN**; and one
  fixture must show `prep.keepouts.rects[].pin` scoring PROVEN off L3393 while
  the keepout emitter reads nothing, which is the reason the field is `ref:`.
- `tests/t1_placement_gates.py` — `--config /nonexistent.json` is exit 2 with a
  named path, not exit 0 on defaults.

**RED-verify each against pre-fix code** (swap the old `route_and_stitch_generic.py`
back in, confirm green-when-it-should-be-red, restore) and say so in the test —
`tests/README.md` §Adding a regression. The pre-fix binary is already known: all
five known-bads PASS today, because `yaml.safe_load` returns four floats.

#### New IDs (PROPOSED, not yet minted — forward-reference for X3)

- **`R-KOSUBJ`** (PROPOSED): every `prep.keepouts.rects[]` names its subject in
  a field and that subject resolves on the live board.
- **`F-CFGDEF`** (PROPOSED): a gate offered a config path says which it used,
  and a named-but-absent config is an invocation error, never defaults.

Neither collides: `grep -rl -- R-KOSUBJ skills/ tests/ docs/ | wc -l` → `0`,
same for `F-CFGDEF` (canon A-ORDER: check a new ID against `skills/` **and**
`tests/` before minting). Both prefixes are already inside
`t1_contracts.py:454` `ID_RE = [ASPRMEDFGQ]-`, so the sync backstop reaches
them the day they land.

**Closes:** instance 2's config half; a live board defect (6 rects reserving
empty board, 7 reserving too little, 17 GND stub sites reserving nothing); and
the 55 fleet rects that are correct today only by luck.

---

## Citation fix for §3 — "Production routers never fail a net"

**What was wrong.** `docs/pipeline-fix-master-plan.md:161-165` carries two verbatim vendor quotes with zero links, while §11 (`:722-727`) rejects the Freerouting benchmark *specifically for being uncited*. Same document, two standards. Both quotes are **real and now sourced** — but one of them is scoped wrong, and the bullet's headline claim is **contradicted by its own sources**.

### All four sources located

| # | claim | source | grade |
|---|---|---|---|
| a | "creates shorts or spacing violations rather than leave unconnected nets" | **EDI System User Guide 14.17**, ch. *Using the NanoRoute Router*, § **Detailed Routing** — verbatim | **vendor tool documentation**, mirror-only |
| b | "Conflicts are allowed … until the last fanout pass" | **SPECCTRA V8.0 command reference**, `fanout` command, `<passes>` option — verbatim | **tool documentation**, third-party reproduction |
| c | 65-entry schedule, `followGuide` true only for 0–2, `mazeEndIter` 3→8→16→32→64 | **OpenROAD `FlexDR.cpp` `strategy()`**, lines 1742-1813 — parsed, not read | **primary source (executable code)** |
| d | routing guides are a SOFT rule | **ISPD-2018 contest FAQ Q5**, official site — verbatim | **contest documentation** (organizers = Cadence); companion paper is peer-reviewed |

Verification commands:

```bash
# (a) live host 503s; Internet Archive snapshot 2017-12-02 is intact
curl -sS 'https://web.archive.org/web/20171202094422id_/http://free-online-ebooks.appspot.com/enc/14.17/soceUG/Using_the_NanoRoute_Router.html' \
  | sed 's/<[^>]*>/ /g' | grep -o 'The detailed router creates[^.]*\.'
# -> The detailed router creates shorts or spacing violations rather than leave unconnected nets.

# (c) parse the schedule rather than trust prose
curl -sS https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD/master/src/drt/src/dr/FlexDR.cpp \
  | python3 -c "$(cat <<'PY'
import re,sys
s=sys.stdin.read(); i=s.find('SearchRepairArgs> strategy'); j=s.find('// clang-format on',i)
r=re.findall(r'^\s*\{(.+?)\}[,]?\s*//\s*(\d+)\s*$', s[i:j], re.M)
print('entries', len(r), 'followGuide true at',[int(n) for c,n in r if c.split(',')[-1].strip()=='true'])
PY
)"
# -> entries 65 followGuide true at [0, 1, 2]
```

### Two defects found while sourcing (both must be fixed in the same edit)

1. **(b) is scoped wrong.** "Conflicts are allowed … until the last fanout pass" is the description of the **`fanout` command's `<passes>` argument** — it governs *escape wires only*, not general routing. Using it to support a general claim is a misquote by omission. The same document carries the *correct* general-routing evidence, which is stronger: SPECCTRA's default on a failed reroute is to **keep the conflicting wire**, and unrouting is an opt-in flag — `-remove`: *"When the autorouter tries to reroute a wire and can't find a new path, it restores the wire to its original position. If you specify remove, the autorouter does not restore the wire, but instead creates an unroute."* Conflicts are also a *budgeted* quantity: `limit cross <n>` = *"The maximum number of crossing conflicts allowed when routing a connection."*

2. **The headline claim "Production routers never fail a net" is false, and both sources say so.** NanoRoute: *"Detailed routing stops automatically if it cannot make further progress on routing the design."* SPECCTRA's routing-history table has a dedicated **`Unrte`** column and a `Fail` column. The defensible claim — and the one R2c actually needs — is **bounded, non-terminal failure**: a conflict is the *default committed* outcome, an unroute is *opt-in*, and effort *stops* rather than growing.

**Bonus: this closes §12 open question 3** ("whether R2c's conflict-commit is acceptable under our 0-violation gate"). It is: the committed conflict is a **transient**, never a shipped state. SPECCTRA's own documented status file (`Demoa.dsn`, 681 nets / 2718 connections) shows unconnections cleared *first* by tolerating conflicts, then conflicts negotiated to zero — exit state is 100.00% complete, 0 unconnections, 0 conflicts:

| pass | Cross | Clear | Fail | Unrte |
|---|---:|---:|---:|---:|
| Fanout 1 | 0 | 0 | 68 | 878 |
| Route 2 | 1242 | 196 | 5 | 5 |
| Route 5 | 451 | 82 | 1 | 1 |
| Route 9 | 27 | 4 | 2 | **0** |
| Route 13 | **0** | 4 | 0 | 0 |
| Clean 20 | **0** | **0** | **0** | **0** |

Connectivity first, DRC second, **both zero at exit** — exactly compatible with `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity` = 0/0/0.

---

## PASTE-READY — replaces `docs/pipeline-fix-master-plan.md:161-165`

```markdown
**Failure is bounded and non-terminal — a conflict is the committed default, an
unroute is opt-in, and effort stops rather than grows.** Cadence NanoRoute:
*"The detailed router creates shorts or spacing violations rather than leave
unconnected nets… Detailed routing stops automatically if it cannot make
further progress."* SPECCTRA's default on a failed reroute is to KEEP the
conflicting wire — unrouting requires the explicit `-remove` option (*"does not
restore the wire, but instead creates an unroute"*) — and conflicts are a
budgeted quantity (`limit cross <n>`), not an error. Neither router "never
fails a net"; both refuse to pay unbounded search for one. The committed
conflict is a TRANSIENT: SPECCTRA's own status file goes 1242 crossing + 196
clearance conflicts at pass 2 → 0 by pass 13, with unconnections at 0 from pass
9 — connectivity first, DRC second, **both zero at exit**, which is our 0/0/0
gate. Ours inverts this: **19** give-ups against caps of **500 k–1.2 M**
iterations, when **40 of 70** successful searches finish inside 50 k.
→ Stage 4–6, Change R2c. **This is the single highest-value item in the plan.**
[EDI System UG 14.17 — Using the NanoRoute Router, §Detailed Routing](https://web.archive.org/web/20171202094422/http://free-online-ebooks.appspot.com/enc/14.17/soceUG/Using_the_NanoRoute_Router.html)
(vendor tool documentation; live host 503s, Internet Archive 2017-12-02) ·
[SPECCTRA V8.0 command reference — `route -remove`, `limit cross`, `fanout <passes>`](http://ohm.bu.edu/~pbohn/__Engineering_Reference/pcb_layout/PADS/PADS-PowerPCB_Training_Manual_4.0/PADS-PowerPCB%20Training%20Manual%204.0/8%20Cct.doc)
(tool documentation, reproduced in PADS-PowerPCB Training Manual 4.0 ch. 8 —
note "conflicts are allowed until the last fanout pass" is the `fanout`
command's escape wires ONLY, not general routing) ·
[OpenROAD FlexDR `strategy()`](https://github.com/The-OpenROAD-Project/OpenROAD/blob/98251dfc5ffe48d408558b9e8ed159681cdc9540/src/drt/src/dr/FlexDR.cpp#L1742-L1813)
(primary source: 65 search-repair entries, `followGuide` true only for 0–2) ·
[ISPD-2018 contest FAQ Q5](http://www.ispd.cc/contests/18/#faq): *"Routing guide
is a soft rule while violation is a harder rule"*
([ISPD'18 paper](https://dl.acm.org/doi/10.1145/3177540.3177562), peer-reviewed).

*Own numbers, reproducible from `projects/programmable-usb2-hub`:*
`grep -c 'FAILED: Could not find route' 06_build/logs/route-latest.log` → **19**;
`grep -c 'Route found' …` → **70**;
`grep -oP '(?<=max_iterations: )\d+' 03_src/route.yaml | sort -n | uniq -c` →
2×500 k, 1×600 k, 3×700 k, 3×900 k, 20×1.2 M;
`grep -oP '(?<=Route found in )\d+' … | awk '$1<=50000' | wc -l` → **40**.
```

### Two precision corrections this sourcing forces elsewhere

**R2c mechanism 2 (`:541-542`) — `mazeEndIter 3→8→16→32→64` is not a monotone ladder.** Parsed from the schedule (65 entries, indices 0–64):

| `mazeEndIter` | entries |
|---|---|
| 3 | 0–2 |
| 8 | 3–41, **49**, **57** |
| 16 | 42–48 |
| 32 | 50–56 |
| 64 | 58–64 |

It **drops back to 8** at entries 49 and 57. Likewise `workerDRCCost` is not a clean `1×→64×`: it oscillates back to `shapeCost` 12 times; only the *envelope* rises 1→2→4→8→16→32→64 (first appearance at entries 0/10/18/26/34/50/59). Suggested wording: *"`mazeEndIter` rises 3→8→16→32→64 across 65 entries, with two deliberate drops back to 8 (entries 49, 57) and a DRC-cost envelope of 1×→64× that resets to 1× twelve times — the ladder alternates cheap-broad and expensive-narrow, it does not just climb."* The struct is `FlexDR.h:83-94` (`size, offset, mazeEndIter, workerDRCCost, workerMarkerCost, workerFixedShapeCost, workerMarkerDecay, ripupMode, followGuide`); `RipUpMode` cycles `ALL → DRC → NEARDRC` on the same non-monotone pattern.

**§3 "Global → detailed" bullet (`:150-159`)** asserts "Guides are explicitly soft" and "FlexDR follows the guide in only 3 of 65 iterations" but cites neither. Both are now first-hand: append `· [ISPD-2018 FAQ Q5](http://www.ispd.cc/contests/18/#faq) · [FlexDR strategy()](https://github.com/The-OpenROAD-Project/OpenROAD/blob/98251dfc5ffe48d408558b9e8ed159681cdc9540/src/drt/src/dr/FlexDR.cpp#L1742-L1813)`. The 3-of-65 claim **verifies exactly**.

**§11's Freerouting bullet needs no change** — it is now consistent, because §3's highest-value bullet meets the standard §11 enforces.
