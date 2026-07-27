# ADR-0005 — Every fact from outside this repo carries its provenance and a confidence grade

status: accepted — PHASE 1 LANDED 2026-07-27; PHASES 2-4 LANDED 2026-07-27
        (see "Phases 2-4, as built" at the end — the paragraph below is kept
        verbatim as the record of what was true when phase 1 shipped)
date: 2026-07-27

**What actually landed (phase 1 only, and nothing more):** `M-IMPORT` is a row
in the Meta table of `skills/kicad-pcb/references/design-policies.md`, graded
`[H]`, with the adjacent-property corollary co-resident and its known members
enumerated; `S-VER` (S3) is re-parented as its narrow instance and says so in
both rows; the two governing contracts caught up in the same change
(`skills/kicad-pcb/references/contracts.md`,
`skills/pcb-design/templates/contracts/02_parts/contracts.md`).

**What did NOT land, and is therefore not enforced by anything** *(true when
phase 1 shipped; SUPERSEDED the same day by "Phases 2-4, as built" at the end.
Kept verbatim, because a record of what a canon row could and could not do at
the moment it landed is the point of writing it down):* `D-MATE` and
the BRIEF MATING section (phase 2); `import_provenance_check.py` and its RED
fixture (phase 3); `pluto-cal-switch`'s `mates.yaml` backfill (phase 4). The
M-IMPORT row states this absence in its own Verified cell — a canon row whose
Verified column reads like enforcement while nothing runs is the
gate-that-grades-nothing shape M-COVER forbids, and it would be a poor joke to
commit it in the change that widens the import rule.
tags: canon, external-facts, mechanical, mating, meta

## Context

ADR-0004 governs the facts this pipeline **produces**: grade the shipped bytes,
declare coverage, regrade the fleet. Every principle in it compares our own
artifacts to each other or to what ships.

A board does not exist alone. It plugs into things. And **every fact about the
outside world enters this pipeline unexamined**, because the gates only compare
our artifacts to our artifacts.

### The incident

`pluto-cal-switch` is a 5-port adapter that must mate to an ADALM-PlutoPlus SMA
panel. The vendor publishes **no PCB source** — three PDFs, no KiCad/Altium,
no DXF, no STEP, no dimensioned drawing.

The SMA pitch was extracted from an undimensioned vector assembly plot, rendered
at 600 dpi and calibrated against two known packages. It came out **35.60 mm**
across the three-connector span, and three independent extractions agreed to
0.003 mm. **I was ready to build a floorplan on it.**

Then the user put a caliper on two physical units:

| | span | vs the plot |
|---|---|---|
| plot (CAD proxy) | 35.60 mm | — |
| genuine Pluto+ | **35.04 mm** | 1.6 % |
| 2025 clone | **34.72 mm** | 2.5 % |

The mating window for rigid SMA is **±0.05 mm** (MIL-STD-348B thread-start
capture). The error was 10-18x the window, and no gate in this repo could have
seen it, because the number never came from an artifact any gate reads.

Three further facts from the same episode, each its own trap:

- **A proxy measured beautifully and was still wrong.** Three extractions
  agreeing to 0.003 mm measured the PLOT precisely. Precision about a proxy is
  not accuracy about the object.
- **The first photogrammetry measured the wrong feature.** Measuring the
  protruding SMA barrels gave near-uniform spacing, because the barrels stand
  ~11 mm toward the camera and parallax swamped a 3.5 % asymmetry. Re-measured
  on the flat silkscreen boxes, the asymmetry appeared at ~3 sigma. The
  adjacent-property error, in a new costume.
- **A published tolerance meant something other than its label.** JLCPCB's
  `Hole Position Tolerance +-0.05 mm` states NO DATUM. Eurocircuits publishes
  both and shows why it matters: hole-to-hole 0.10 mm, but **Profile/Cut-Out to
  Hole +-0.20 mm** — the profile is a separate machine setup. This board's
  connector positions are referenced to the BOARD EDGE, so the edge-referenced
  term is the one that matters, and it is precisely the one JLCPCB does not
  publish. Using the printed number would have understated the budget 4x.

And a fact nobody would have thought to check: **two units both sold as
"PlutoPlus" measure 0.32 mm apart.** The thing being mated to is not a single
fixed object.

### Why the existing canon did not prevent this

`S-VER` already requires a `part.yaml` `verified:` line to cite a datasheet
**figure and page**. That IS an imported-fact rule. It is scoped to pin maps,
because a pin-map error is the incident that taught it.

**This is an M-WIDTH instance — and M-WIDTH is the canon landed in ADR-0004.**
S-VER is the incident. The class is *every fact imported from outside*. The
campaign gets to apply its own newest rule to its own canon.

## Options

- **Fix the pluto board's numbers and move on.** REJECTED — it leaves the class
  open, and the next board that mates to anything re-pays the whole lesson.
- **Require a physical measurement for every external fact.** REJECTED as
  unworkable: a datasheet figure is a legitimate source, and demanding a caliper
  for every imported number would stop work for no gain. The problem is not that
  proxies are used; it is that their status is invisible.
- **Grade the provenance, and make the grade visible and machine-checked.**
  CHOSEN.

## Decision

### M-IMPORT, into `design-policies.md`

> **M-IMPORT — every fact from outside this repo carries its provenance and a
> confidence grade.**
>
> | grade | meaning |
> |---|---|
> | **MEASURED** | someone touched the physical object, or read a machine-readable source (a `.kicad_pcb`, a drill file, a STEP) |
> | **CITED** | read from a vendor document, with figure / page / section |
> | **ESTIMATED** | derived, photogrammetric, inferred — **MUST carry an error bar** |
>
> - A fact used in copper is MEASURED or CITED, never ESTIMATED without its bar.
> - Where grades disagree, **the object beats its drawing.** A drawing is a
>   proxy for the thing; precision about a proxy is not accuracy about the
>   object.
> - **A published number whose DATUM is unstated is ESTIMATED, not CITED.**
> - Where multiple physical units of nominally the same device DISAGREE, that
>   disagreement is the headline, not a footnote.
>
> `S-VER` is the narrow instance of this rule scoped to part pin maps and
> remains in force unchanged.

The existing adjacent-property canon gains one corollary from this incident:
**measure the feature whose position you need, not one adjacent to it** — the
barrel is not the feature whose spacing you want.

### D-MATE — mating geometry is a fact-lock row

When a board mates to hardware this repo did not design, the commission
fact-lock (BRIEF.md) gains a MATING section, and every dimension consumed by the
floorplan appears there with its grade.

### One home, referenced not restated

`spf/<device>/` holds the facts **once**; its contract already demands the
method-per-number discipline. A board declares `03_src/rules/mates.yaml` naming
the device folder and the specific facts it consumes. **Boards reference; they
never restate.**

Same shape, and the same reason, as `assembly.yaml` being the single home for
"who gets placed": cooksense v1.1 shipped 13 CPL rows contradicting its own
MANIFEST because two files held the same fact and drifted.

### One gate

`import_provenance_check.py` — for every fact referenced by a board's
`mates.yaml`: it exists in `spf/<device>/`, it carries a grade, and any
ESTIMATED fact used dimensionally carries an error bar.

**The RED fixture is free and already written**: the PlutoPlus geometry as it
stood BEFORE the caliper — ESTIMATED at +-1.5 %, about to be used as if
MEASURED. The same property ADR-0004 relied on, where usb-hub v1.8's zip was the
known-bad. The defects keep supplying their own fixtures.

## Consequences

### Sequencing

**Phase 0 — DONE, measured 2026-07-27.** ADR-0004 required this of itself and
it paid off here, because the first cut was misleading.

Raw count: 110 of 193 `verified:` lines cite a figure/page/table/section, 83 do
not — which reads alarming. **But 86 of the 193 are 2-TERMINAL PASSIVES, where
there is no pin map to verify.** Counting them was the adjacent-property error
again: the property is "a pin-map claim backed by a figure", not "a dossier with
a citation".

Scoped to MULTI-PIN parts, where a pin map is a real claim:

| | |
|---|---|
| cite a figure/page/table/section | **89 / 107 (83 %)** |
| do not | **18** |
| 2-terminal passives, correctly out of scope | 86 |

**S-VER is in far better shape than feared, and the 18 are a bounded backfill,
not a campaign.** But several sit in paths where the pin map decides behaviour:
`LTV-817S-TA1` (the optocoupler ON THE ISOLATION BARRIER), `MAX31856MUD+T` (the
thermocouple front end on a cooking interlock), `SN74HC595DR` and `SN74HC14DR`
(the keypad shift chain), `USB4105-GF-A`, `RJHSE-5384`.

The other two counts:
- **P-FACT `asserts:` — 16 / 193 (8.3 %).** Executable part facts remain rare.
- **`mates.yaml` — 0 boards.** `spf/` holds 1 device record. This ADR's own
  mechanism has exactly one consumer, which is the honest reason the
  mating-feasibility checker is NOT promoted below.

Conclusion: the design stands, but **Phase 1-3 should be sized as a small gate
plus an 18-part backfill**, not a fleet-wide overhaul.

**Phase 1 — DONE 2026-07-27.** M-IMPORT into the canon, S-VER re-parented as
its instance, both contracts updated in the same change.

**Phase 2** — D-MATE into the commission stage + the BRIEF template.

**Phase 3** — `import_provenance_check.py` with the RED fixture, wired into
`run_tests.sh` and given a semantic Audit row (a bare `*.py` wildcard is not a
contract — ADR-0004).

**Phase 4** — backfill `pluto-cal-switch`'s `mates.yaml` from
`spf/plutoplus_hardware/`, which is the first and currently only consumer.

### NOT promoted, and why — with their triggers

**A mating-feasibility checker** (two boards' fab tolerances + a connector's
published float -> PASS/FAIL). Mechanical enough to automate, and it would have
condemned rigid SMA here in one line. But it has been run **once, by hand, on
one interface**. Canon M8 says the SECOND board needing the same bespoke thing
triggers mandatory promotion. **Trigger: the next board that mates to foreign
hardware.**

**The research fan-out heuristic.** It earned its cost on this board — six
concurrent sourcing agents plus adversarial refutation surfaced a 37-piece stock
ceiling, a 1.64 dB chain tilt that makes "30 dB total" ambiguous, and a switch
whose truth table already matches the required control polarity. But it is a
process judgement, not a property a gate can measure. It belongs in `SKILL.md`
prose with its trigger — **a `proven-parts.yaml` miss on a whole part class**
(the ledger held 31 entries and zero RF) — not as a check ID.

Promoting either now would be writing a rule wider than its evidence, which is
M-WIDTH's failure mode in reverse.

### The flake, named rather than excused

`t4_regressions`'s `classified_drc` SUB-FLOOR case has failed twice and passed
on re-run twice during this campaign, and each time it was excused as "the known
temp-path flake, commit 2de4b2a". **That habit trains a reader to ignore red**,
which is the same disease as a gate that cannot fail. Fix it, or quarantine it
with a dated reason and an owner. A third excuse is worse than the flake.

**RESOLVED 2026-07-27 — FIXED, not quarantined.** Measured rate before the fix:
**3/65 = 4.6%** (2/25 in one serial loop, 1/40 in another), all SERIAL, no
concurrency — which refutes the temp-path theory outright, and 2de4b2a was a fix
for a real but different bug. The nondeterminism was in the FIXTURE, not the
checker: the injected track pair sat on top of the sealed board's existing
copper, KiCad emits ONE violation class per neighbourhood, and pcbnew's `Save()`
does not order Python-added tracks stably — good and bad boards were a
byte-identical multiset of lines differing only in where the injected segment
landed. The pair moved to the board's maximum-clearance site and the fixture now
ASSERTS its own isolation. The `REAL=1` assertion was NOT touched. 60/60 green
after. Details in the `t4_regressions.py` INCIDENT 8 header.

### What this does not do

It does not make imported facts correct. It makes their **status visible**, so
that a number carrying +-1.5 % cannot be silently spent against a +-0.05 mm
budget. The caliper still has to be picked up; this only guarantees that
everyone can see when it has not been.

---

## Phases 2-4, as built — 2026-07-27

**Phase 2 — D-MATE.** The BRIEF template gains `## Mating fact-lock` (grade,
error bar, where it is spent, and the budget it is spent against), the 01_docs
contract gains its structure section + a Validate line, and `SKILL.md` stage 0
gains the D-MATE bullet with the incident in it. `none — this board does not
mate to hardware this repo did not design` closes the section; SILENCE DOES
NOT, and the gate enforces exactly that asymmetry.

**Phase 3 — `skills/kicad-pcb/scripts/import_provenance_check.py`**, wired into
`tests/run_tests.sh` as `t1_import_provenance.py` and given a SEMANTIC Audit
entry in `skills/kicad-pcb/scripts/contracts.md` (a bare `*.py` wildcard is not
a contract — ADR-0004). It grades `03_src/rules/mates.yaml` against
`spf/<device>/{README.md,facts.yaml}`:

| finding | what it refuses |
|---|---|
| M-EXIST | an id the record does not hold, or a `quote:` no longer in the record VERBATIM — the machine index drifted from the human record |
| M-GRADE | absent or invented grade. Absent is a FAIL, never a promotion to ESTIMATED |
| M-BAR | ESTIMATED + `use: dimensional` with no bar, or a bar that does not PARSE |
| M-PROXY | the grade contradicting the METHOD — a plot number graded MEASURED |
| M-OWED | a number nobody has, spent on a dimension; or OWED with no route to obtaining it |
| M-RESTATE | the board writing a value/grade/method that has a home in `spf/` |
| M-COVER | a `mates.yaml` consuming NOTHING |
| D-MATE | a consumption with no site; a BRIEF lock with no yaml |

Two additions beyond the three properties this ADR specified, each earned by
the same incident rather than invented: **M-PROXY**, because the plot number's
danger was that it read as measured (three extractions, 0.003 mm apart), and
**M-EXIST's verbatim-quote half**, because splitting the record into a human
file and a machine index creates exactly the two-homes drift that
`assembly.yaml` exists to prevent. The M-PROXY keyword list deliberately
excludes "derived": subtracting two caliper readings is still a measurement,
and the PlutoPlus D-free pitches are computed that way.

**The RED fixture was free, as predicted.** `t1_import_provenance.py` carries
the PlutoPlus record AS IT STOOD BEFORE THE CALIPER, twice: 35.60 mm ESTIMATED
with no bar, spent dimensionally (M-BAR), and the same number graded MEASURED
on the strength of its reproducibility (M-PROXY). Both RED-verified by
neutering the checks: M-BAR disabled -> 18 passed / 2 failed; M-PROXY disabled
-> 19 passed / 1 failed; restored byte-identical -> **20 passed, 15 known-bad**.

**Phase 4 — `projects/pluto-cal-switch/03_src/rules/mates.yaml`**, referencing
15 facts in `spf/plutoplus_hardware/facts.yaml` (the new machine index of the
README): 9 MEASURED, 3 ESTIMATED (one dimensional, with its ±1.5 % bar), 2
OWED, 1 superseded plot number kept visible with its grade attached. **15/15
graded, 0 fails.** The two OWED entries are the RF-axis height above the
Pluto's PCB and the mounting-hole positions — declared rather than invented,
which is what the grade is for.

**NOT built, still, and for the reason already given:** the mating-feasibility
checker. It would have compared `connector_outline_width`'s ±0.12 mm against
SMP's ±0.254 mm float automatically, and the temptation to add it while the
data was right there was real. One interface, one hand run; M8 triggers on the
SECOND board. Writing a rule wider than its evidence is M-WIDTH's failure mode
in reverse.

**One thing this pass could NOT do.** `spf/plutoplus_hardware/photos/` is
empty: the four photographs the README names were pasted into a chat and never
written to disk. They are the evidence behind the field-ID tells (shield can,
silk labels, U.FL count) and behind `port_order`'s silkscreen half. Nothing was
fabricated to fill the gap; the README already names the four expected files,
and the folder stays empty until someone saves them.
