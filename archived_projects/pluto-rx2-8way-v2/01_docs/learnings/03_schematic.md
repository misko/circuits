# learnings: commission through the schematic gate — pluto-rx2-8way-v2

Harvest source for the canon (design-policies.md / T4), not canon itself.

---

## L1 — A BRIEF THAT TRAVELS BETWEEN AGENTS IS A CLAIM, AND RE-MEASURING IT IS CHEAP

**Issue.** The commissioning brief handed me seven load-bearing facts about v1.
Four re-measured correctly. Three did not: "11 unconnected nets" (v1's own DRC
says 28), "a 0.200 mm floor" (that is v1's declared NETCLASS clearance, not a
fab capability — the tier's `min_space` is 0.09), and an implied claim that the
via-in-pad arithmetic was the module's justification.

**Root cause.** The brief's author measured some things and inherited others,
and the two were not distinguished in the text handed to me.

**How to avoid.** The rule already exists ("MARK EVERY LOAD-BEARING CLAIM AS
MEASURED OR INHERITED") and it worked in the direction that matters — the brief
told me to re-verify, so I did. What is worth adding is the *cost*: re-measuring
all seven took about fifteen minutes of scripting against v1's own artifacts,
against a design decision worth days. **The re-verification pass should be a
NAMED STAGE-0 STEP with a journal entry, not an instruction buried in a rules
section.**

`candidate-canon: yes` — suggested ID **M-REVERIFY**: at commission, every
inherited numeric claim is re-measured against the artifact it came from, and
the result table goes in the journal before any design work starts.

---

## L2 — A GHOST `keep_short` IS THE COST OF COPYING A DOSSIER, AND ONLY ONE GATE SEES IT

**Issue.** I copied five part dossiers from v1 (correctly — they are ledger
hits). Two carried `layout.keep_short` budgets naming nets that do not exist on
v2: `VBUS_F` (v1's ferrite sat on the USB rail; v2 has no VBUS at all) and
`RF_ANT_LAUNCH` (a placeholder that is not a net on v1 either).

**Root cause.** A `keep_short` budget is the ONE field in a dossier that is
board-specific. Everything else — pins, package, limits, gotchas — is a property
of the part and travels correctly. The budget names a NET, and nets are a
property of the board.

**How to avoid.** `net_reference_audit` (E-NETREF) already catches it and did,
which is the system working. The compounding move is at the *copy* step:
**copying a dossier between projects should immediately be followed by
E-NETREF**, because that one field is guaranteed to be stale and nothing else
in the dossier is. It is a two-second gate against a defect that is silent by
construction (a ghost budget makes P-ADJ grade nothing while still counting as
declared).

`candidate-canon: yes` — suggested ID **P-ADJ-PORT**: when a `part.yaml` is
copied into a new project, its `layout.keep_short[].net` entries are re-pointed
or deleted in the same change; E-NETREF is run before the dossier is committed.

Second, smaller learning inside this one: `RF_ANT_LAUNCH` was a **placeholder
name in a shipped dossier**, ghosted on its ORIGINAL board too. A dossier for a
part with N instances (ten SMA jacks) wants N budgets, not one generic one — a
budget on one representative port leaves the other eight ungraded.

---

## L3 — THE FLEET PUBLISHES THREE CONSTANT SETS FOR ONE STACKUP, AND TWO ARE IN ONE FILE

**Issue.** `rf-design.md` 4(d) makes "one stackup, one constant set" a canon rule
after two BOARDS disagreed. Measured today: v1 disagrees with ITSELF — its
`nets.yaml` carries eps_eff 3.350 in the phase block and lambda_g 27.41 mm
(implying 3.3229) in a netclass comment ~300 lines earlier, and the 1.37 mm via
fence in use across this family was computed from the second one. My own
Hammerstad-Jensen derivation from the declared stackup gives 3.3286 and
reproduces NEITHER published value at any w in {0.35, 0.36, 0.37} x t in
{0, 0.035}.

**Root cause.** The numbers were typed, not regenerated. Once typed, a value can
be re-cited indefinitely, and rf-design.md's own opening warns about exactly
this pattern ("later ADRs re-cited that headline as though it had been
measured").

**How to avoid.** ADR-0003 answers it for v2 with a `<!-- bound -->` block whose
`command:` regenerates the value. Notable fleet fact measured while doing it:
**of 68 project ADRs, exactly ONE declares a bound block — this one — while 36
publish an inequality in prose and 35 of those are OWED.** The mechanism exists
and is essentially unused.

`candidate-canon: yes` — this is rf-design.md gate proposal 2 ("one stackup, one
constant set", extend `adr_bound_provenance`) and today's measurement is the
second strike: the defect is now observed WITHIN a board, not only across two.

---

## L4 — A REQUIRED FIELD FILLED WITH A PLAUSIBLE GUESS IS WORSE THAN ONE FILLED WITH "NOBODY KNOWS"

**Issue.** `assembly.yaml`'s `consigned:` schema REQUIRES `msl:`. Waveshare
publishes no MSL rating and no reflow profile for RP2040-Zero — it is a finished
consumer assembly, not a component sold in a moisture-barrier bag.

**Root cause.** The schema was written for consigned SEMICONDUCTORS, where MSL
is a datasheet line. A consigned MODULE has no such line and the schema has no
way to say so.

**How to avoid.** I wrote the field as an explicit OWED statement naming the
mitigation (JEDEC J-STD-033 unknown-MSL bake) and how to close it. **"MSL 3"
would have been indistinguishable from a datasheet read** — and the field exists
precisely because crow-recorder-central v1.0 shipped a consigned MSL-3 part with
no MSL text in its paperwork.

`candidate-canon: maybe` — suggested ID **A-MSL-OWED**: `msl:` accepts a
structured OWED form (`owed: true` + `mitigation:` + `how_to_close:`) so the
difference between "read from the datasheet" and "nobody publishes it" is
machine-visible instead of living in prose the schema cannot grade.

---

## L5 — DECLARING A RAIL WHOSE REGULATOR YOU DO NOT OWN

**Issue.** v2's 3V3 is generated by an RT9013-33 inside a bought module. The
easy path was `rails: []` and a clean E-TOPO N-A.

**Root cause.** E-TOPO takes N-A when `02_parts` declares no converter. A board
whose converter is inside a module trivially satisfies that — and gets a green
verdict for having nothing to grade. `power_topology.py`'s own docstring names
three fleet boards that landed there.

**How to avoid.** Declare the rail, point `converter:` at the module, and put
`dropout_mv`/`pdiss_max_mw` as PER-RAIL overrides rather than inventing a
dossier for a part you never order. Two honest notes go in the file: the
`iout_max_A` is the WHOLE rail's (most of which never crosses our copper, so the
IR model is ~500x conservative), and the dissipation budget is the MODULE
VENDOR'S with our ambient assumption named and the corner where it fails stated.

`candidate-canon: maybe` — the general shape is "a rail whose converter is
inside a bought assembly", which the pipeline will meet again the moment anyone
uses a second module. Suggested: `converter: <module refdes>` + per-rail
electrical overrides becomes a documented pattern rather than something each
board re-invents.

---

## L6 — A GATE THAT REJECTS A SCHEMA ERROR LOUDLY IS WORTH MORE THAN ONE THAT SKIPS IT

**Issue.** My first `electrical_invariants.yaml` used `kind:` where the schema is
`assert:`, and wrote `series_chain` as a list of PARTS where it is an
alternating list of NETS and PARTS.

**Root cause.** I modelled the file on the SKILL's prose summary rather than on
a working example.

**How to avoid — and this is the learning, not the mistake.** The gate returned
`E-INV LOAD ERROR ... unknown or missing assert kind None` and **exit 2**, not a
silent zero-invariant pass. Had it skipped unparseable entries, the board would
have shipped with 20 declared invariants and 0 graded — a `rails: []` in a
different costume. Re-authoring against a real example also produced a BETTER
file: `series_chain` pins POSITION where the `net_has_part` I first reached for
only pins existence, and position is the failure mode for both the ferrite and
the pickoff.

`candidate-canon: no` — the behaviour is already correct. Recorded as evidence
FOR the existing design, which is worth keeping: most learnings are about gates
that failed to fire.
