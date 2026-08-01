# contract: 03_src/rules/

**Purpose** — design intent that must be MACHINE-ENFORCED. Intent that only
a human reads belongs in `01_docs/ARCHITECTURE.md`; intent a tool must check
belongs here.

**Mutability** — hand-edited. This is source; `.kicad_dru` and the
`.kicad_pro` netclasses are its OUTPUT.

## Allowed

| File | What |
|---|---|
| `integration.yaml` | P-MOD module-first architecture record. REQUIRED on newly commissioned/adopted projects: every complex subsystem selects a real module or carries an evidenced D-MOD bare-IC exception ADR; absence is UNMIGRATED, never PASS |
| `nets.yaml` | net classes: nets, current, intent, min_width, routing strategy, verify, scoped exemptions; `fab_tier` (capability floors for the generic backend); `scoped_floors` (insideArea width relaxations, `why` REQUIRED); `scoped_clearances` (insideArea ISOLATION relaxations, `nets` + `why` REQUIRED, bounded on BOTH sides of the pair); **`length_match`** (canon R-LEN: REALIZED-COPPER matched groups, the ONE machine-readable home for "these paths must have the same length and here is why" — see `## Structure: nets.yaml length_match` below) |
| `electrical_invariants.yaml` | design-INTENT assertions the netlist must satisfy (canon E-INV): `pin_on_net`, `series_chain`, `net_has_part`, **`part_value`**, **`node_level`**. Each REQUIRES `adr:` (the ADR that emitted it) + `why:`. **`adr:` MUST BE QUOTED — `adr: "0011"`, or unpadded `adr: 11`.** A bare zero-padded reference is a YAML 1.1 OCTAL literal and the loader REJECTS it: `adr: 0011` becomes the integer 9 and re-pads to `"0009"`, `adr: 0012` -> `"0010"`, `adr: 0010` -> `"0008"`, `adr: 0020` -> `"0016"`, while `adr: 0008`/`0009` survive as strings only because 8 and 9 are not octal digits. That is not a SKIP — the invariant silently satisfies the WRONG ADR and E-ADR credits a document that emitted nothing. The rejection is written at the width of the class (canon M-WIDTH): every unquoted zero-padded `adr:` is refused, including the ones that happen to survive, because which are safe is a fact about the digits and not about the schema. It is a REJECTION rather than a coercion because coercion is impossible after the fact — by the time `yaml.safe_load()` returns, `adr: 0011` and `adr: 9` are the same object and the padding is gone; the check runs on the composed NODE, which still carries the scalar's quoting style. Measured 2026-07-27: this template itself and the board seeded from it both wrote `adr: 0011` and both resolved it to `0009`. **`part_value` `{part, min\|max\|equals (+tolerance_pct), adr, why}` pins a PARAMETER, which the other three cannot** — they pin TOPOLOGY, and an invariant that pins a component's EXISTENCE does not pin its VALUE. smc0985-cooksense 2026-07-25: the WD_PET safety fix landed a 100k watchdog pull-down where TI SLVS165O bounds it at 5.2k (I_IL 190uA max x R < V_IL 0.99V), silently disabling the supervisor on a cooking-contactor interlock — and ALL THREE assertions that shipped with that fix (one `net_has_part`, two `pin_on_net`) PASS on the 100k netlist, because the resistor does exist, on the right nets. Values are read from the netlist's own `(comp (value ...))` and decoded as SI, so `1k`/`1kOhm`/`1kΩ`/`4k7`/`0R1` are one number — note `m` is MILLI and `M` is MEGA, and an UNDECODABLE value is a FAIL, never a skip. At least one bound is REQUIRED: an assertion naming a part and bounding nothing is the exact gap this kind closes. **`node_level` `{net, receiver: REF.PIN, driver_state: released\|contended, must_be: logic_high\|logic_low, adr, why}` pins the OUTCOME, which `part_value` still cannot** — a value that is RIGHT can leave the node DEAD. smc0985-cooksense v1.7 2026-07-29: a divider taking `U_EXP.1` off a 5 V node was sized as if `EFUSE_FLT_N` were a stiff 5 V source; it is OPEN-DRAIN behind `R_PG` 100k, so the chain is 100k+10k over 22k and the pin sat at **0.833 V against a 2.640 V threshold** — the fault readback was dead, and **E-INV passed 136/136** because the assertions said the resistors EXISTED at the right values. Resolves the DC path through RESISTORS ONLY (a first run crossed a 220uF cap and printed a confident wrong 2.500 V); needs a top-level `supplies: {NET: volts}` map and an `electrical:` block on the RECEIVER's `02_parts` dossier. **Every net named in `supplies:` MUST EXIST in the netlist and the loader REJECTS one that does not, naming the near-miss.** cooksense 2026-07-29: `supplies: {N3V3: 3.3}` declared the tsx AUTHOR-PREFIX form of a net the netlist calls `3V3`, the grader filters supplies to nets it can see, and so the 3V3 rail was INVISIBLE to every `node_level` grade on the board. A misnamed rail does not announce itself — it either downgrades the verdict to UNREACHED for the WRONG REASON (the pre-fix message read "no supply rail voltages declared — add `supplies:`" on a board that had declared it, sending the author to write a block they had already written), or, when a second rail does resolve, lets that one win the shortest-path search and reports a CONFIDENT WRONG VOLTAGE with nothing in the output to distinguish it from a correct board. Graded whenever `supplies:` is present at all, not only when a grade comes up short (canon M-WIDTH); no path to GND means PULLED TO THE RAIL, no path to a rail is UNREACHED, a receiver with no thresholds is UNREACHED — never a default (M-COVER). Emitted by protection/topology ADRs; graded by `electrical_invariants.py`. OPTIONAL top-level `label_survival:` block (canon S-NETMERGE, graded by `net_label_survival.py` — the schematic net-merge gate; the generic every-global-label-survives-to-the-netlist check is ALWAYS ON with or without this block): `exempt:` labels allowed to be absent, each REQUIRES `why:` evidence (canon M4); `pin_map:` board-specific pin-for-pin net assertions `{refs, n_start, pins: {pin: pattern-with-{n}}, unconnected}` — the crow-recorder net-merge class (P5VA_4→AUDIO4M, MID2P→5V: two DO-NOT-ORDER defects, every self-consistent gate green, 2026-07-23) |
| `power_tree.yaml` | per-rail voltage ENVELOPES + converter selection, graded by `power_topology.py` for E-TOPO / E-MARGIN / E-OFF. REQUIRED per rail: `{name, vin_min, vin_max, vout_min, vout_max, iout_max_A, converter, eff}` — topology DERIVED from Vin-vs-Vout (buck/boost/buck_boost) asserted against the converter part.yaml `type:`, over-capable = over-engineering FAIL (E-TOPO). **THIS FILE IS NOT OPTIONAL WHEN THE BOARD HAS A CONVERTER.** E-TOPO takes its N-A only when `02_parts` declares NO buck/boost/buck_boost/linear part — an independent artifact written by a different stage (canon M1), because until 2026-07-27 the gate asked the power tree whether there was anything to grade and believed it. An ABSENT file, or `rails: []`, with a converter present is `0/N converters graded` and a FAIL; a rails list that omits SOME of `02_parts`' converters is reported as `UNGRADED CONVERTERS: k of N` and fails too. Measured on landing: usb-hub-3s — the board whose IP6559 buck-boost MOTIVATED E-TOPO — had no power_tree.yaml and had never been graded by it. **LINEAR CONVERTERS.** A linear regulator (part.yaml `type:` matching `ldo`/`linear`/`low-dropout`) is NOT a fourth topology; it is one IMPLEMENTATION of a step-down requirement, so the derivation is unchanged: required BUCK is MET, required BOOST or BUCK_BOOST is a cannot-meet FAIL (it cannot step up, and an overlapping Vin envelope means it drops out somewhere in the range). It is then graded on the two failure modes the derivation cannot see — `vin_min - vout_max >= dropout_mv` and `(vin_max - vout_min) * iout_max_A <= pdiss_max_mw`, both REQUIRED from the converter's part.yaml (see the 02_parts contract) or overridden per rail as OPTIONAL `dropout_mv:` / `pdiss_max_mw:`. A linear rail's INPUT CURRENT is `iout`, not `Pout/eff/Vin`: the pass element is in series with the load, so `eff` does not enter the trunk-current sum for it (modelling one as constant-power under-states its trunk current by Vout/Vin — 25% on the first board that declared one). OPTIONAL per rail: `load_uv_threshold` (the load's brownout V — ACTIVATES E-MARGIN), `ir_budget_mohm` (board+connector+cable series R, mΩ), `margin`, `feedback: {vref, vref_tol_pct, r_top_ohm, r_top_tol_pct, r_bottom_ohm, r_bottom_tol_pct}` (the FB-divider tolerance window — all six REQUIRED when present; the checker computes the worst-case vout corners from vout = vref·(1+Rtop/Rbot), FAILS E-TOPO/E-MARGIN when the DECLARED vout window is NARROWER than computed, and grades E-MARGIN headroom from the COMPUTED worst-low — the usb-hub-3s-v3 Vref-only under-stated window, 2026-07-23). OPTIONAL top-level: `source_type` / `off_control` / `quiescent_ua` / `pack_capacity_mah` (E-OFF: a DETECTED battery source must declare its de-energization path + stored draw, an always-on off_control needs an ADR reference), `ir_floor_mohm` (E-MARGIN floor when a load-UV rail declares no ir_budget_mohm, default 100mΩ) |
| `assembly.yaml` | ASSEMBLY intent — the ONE machine-readable home for "who gets placed, and why not" (canon A-POP + A-POS + A-STOCK, and the planned A-ROT, held 2026-07-25; PCBA is the default deliverable). REQUIRED top-level: `service`, `sides`, `fiducials` (`none` is allowed but SILENCE is not), `build_quantity`. `not_assembled:` entries REQUIRE `{refs, reason, evidence, disposition}` where `reason` is the CLOSED vocabulary `not_in_catalog\|consign\|user_supplied\|dnp_by_design\|mechanical\|test_point\|process_incompatible` (`process_incompatible` added 2026-07-25: a part that IS catalogued, stocked and wanted but that the ORDERED process cannot place — the classic case being a true THT part on a `sides: [top]` SMT-only order, whose pads carry no F.Paste so it cannot be intrusive-reflowed. crow-recorder-central-v2 v1.4 shipped exactly that as J1 and the nearest existing reason would have been `not_in_catalog`, which is FALSE: a closed vocabulary with no true option forces a lie into the decision record) and `evidence` is a DATED measurement (the catalog query + its result), not a rationale — every ref listed must ALSO carry `FP_EXCLUDE_FROM_POS_FILES` on the board, and a declared-unpopulated ref still on the CPL is a FAIL. `board_attr_plan:` `{refs, measured_on, plan}` is the ONLY way to defer that board attribute, exactly parallel to `sourcing_plan:` for stock — it exists because the attribute lives in the `.kicad_pcb`, so on a board whose gerbers are sealed and correct the only way to satisfy the check used to be regenerating the board, which churns every UUID (MEASURED 81626 diff lines on a semantically identical rebuild) and turns a data-only CPL fix into a full respin. The DECISION is never deferred: the ref must still be off the shipped CPL, which `DECLARED-BUT-PLACED` enforces and which is NOT deferrable, and the exporter honours `not_assembled:` directly so the declaration is itself a mechanism. `consigned:` parts are POPULATED (they stay ON the CPL): `{refs, lcsc, msl, evidence, disposition}`, `msl` REQUIRED for consigned parts and any exposed-pad package. OPTIONAL per `not_assembled:` entry: `lcsc:` — the code of a catalogued part deliberately not placed, read by `jlc_twin --assembly` so its body still renders and its land pattern is still checked (this replaces hand-typed `--also REF=LCSC`, which was a second home for the population set). `sourcing_plan:` `{lcsc, measured_stock, measured_on, plan}` is the ONLY way to seal past a non-OK stock line (canon A-STOCK, graded by `release_freshness_check.py` check (e); `build_quantity` is the multiplier). `exempt_prefixes:` declares refdes classes whose CPL absence needs no entry — DECLARED, never hardcoded in the checker. The release MANIFEST `not_assembled:` line is GENERATED from this file, never hand-written twice (cooksense v1.1: 13 blank-LCSC CPL rows vs a MANIFEST declaring 12 of them not_assembled — the two drifted because nothing read either) |
| `mates.yaml` | **CONDITIONAL — present ONLY when the board mates to hardware this repo did not design** (canon D-MATE / M-IMPORT, ADR-0005). The machine copy of the BRIEF's `## Mating fact-lock`: `device:` (the `spf/<device>/` folder that holds the facts), `why:`, and `consumes:` entries `{fact, use, where}`. `use` is the CLOSED vocabulary `dimensional\|informational\|owed`; `where` is REQUIRED — a fact spent nowhere in particular cannot be reviewed at the point of USE, which is where M-IMPORT grades it. **IT HOLDS NO NUMBERS.** `value` / `grade` / `method` / `units` / `error_bar` / `quote` inside a `consumes:` entry are M-RESTATE FAILs: the fact's single home is `spf/<device>/facts.yaml` (indexed against the `README.md` record by a VERBATIM quote, so the two cannot drift silently). Same rule, same reason, as `assembly.yaml` being the single home for "who gets placed" — cooksense v1.1 shipped 13 CPL rows contradicting its own MANIFEST because two files held one fact. Graded by `import_provenance_check.py PROJECT_DIR` (also `--root REPO` fleet-wide): **M-EXIST** the id and its quoted line exist in the device record; **M-GRADE** MEASURED/CITED/ESTIMATED/OWED, absent or unknown is a FAIL never a skip; **M-BAR** ESTIMATED + `dimensional` requires a PARSEABLE error bar; **M-PROXY** the grade must match the method (a number off a rendered plot is not MEASURED however reproducibly it was extracted); **M-OWED** a fact nobody has may not be spent dimensionally, and must say how to obtain it; **M-RESTATE**; **D-MATE** every consumption names its site, and a BRIEF declaring a Mating fact-lock must have this file. An EMPTY `consumes:` is an M-COVER FAIL — delete the file rather than ship governance that grades nothing. pluto-cal-switch 2026-07-27: an SMA span extracted from an undimensioned vector assembly plot read 35.60 mm with three independent extractions agreeing to 0.003 mm, and a caliper on two physical units then read 35.04 and 34.72 mm — 10-18x a ±0.05 mm mating window, and no gate in this repo could see it because the number never came from an artifact any gate reads |
| `stackup.yaml` | layer count, what each layer is for, fab tier (optional) |
| `twin_adjudications.yaml` | reviewed jlc_twin findings accepted WITH evidence (see jlcpcb-fab skill) |
| `passives_lcsc.yaml` | passives BOM-comment -> LCSC seed map (bom_seed input; usb-hub-3s) |
| `policy_waivers.yaml` | policy_audit waivers accepted WITH measurement evidence (canon M4/M-WAIV): a YAML list, each entry naming the WAIVED S-/P-/R-/M-/E- policy ID + `why:` + the measurement that justifies it; P-ADJ net-span over-budget dispositions land here with the measured span + why. An entry without evidence is itself a FAIL. **A LOAD-BEARING NUMBER CARRIES A COMMAND, NOT A DIGIT** — see "Structure: `policy_waivers.yaml` — the `evidence:` block" below |
| `policy_audit.json` | OPTIONAL `policy_audit.py` config (`--config 03_src/rules/policy_audit.json`, its default path): thresholds + HUMAN-item verdict pointers (S5/S6/S7) |
| `contracts.md` | this file |

## The rule that makes this folder worth existing

**`intent` and `min_width` come from the same file, so they cannot drift.**
When they lived apart — classes in `.kicad_pro`, intent in a human's head —
both 6A switch nodes got routed at 0.15mm and DRC had no basis to object.

Corollary: **define classes and floors BEFORE routing, never after.** With
floors in place a router's thin-pass output fails DRC immediately.
Retrofitting them cost a full repair campaign.

## Structure: `nets.yaml`

Each class requires: `intent` (prose, why this net is special), `nets` (list
or patterns), `min_width`, `routing` (pour vs track, and the strategy),
`verify` (how to prove it). `exemptions` are scoped to NAMED RULE AREAS that
exist on the board — never a blanket carve-out.

**`current:` is REQUIRED on every class, and silence is not a declaration.**
A class with no ampacity obligation says so — `signal`, `none`, `return
(planes)` — and that is graded as an explicit exemption. A magnitude may carry
a qualifier (`7 A worst case`, `<50 mA`, `~1.5A pulsed`, `6 A / 5 A`); the
first figure followed by an amp unit is taken, so write the BINDING figure
first in a range. **A value the gate cannot read is a FAIL, never an
exemption.**

WHY THIS IS SPELLED OUT: `parse_amps` used to return a bare `None` for both
"absent" and "present but unreadable", and `rules_audit` filed it under OKS as
"n/a (no current: declared)". Measured 2026-07-27 — **A-AMP graded 10 of 57
declared currents fleet-wide**, that message was wrong 100% of the times it
fired (ZERO classes declare no current), and usb-hub-3s-v3 shipped `PWR_IN`
7 A, `PWR_RAIL` 6 A and `SWITCH_NODE` 7 A all silenced while the single class
it did grade FAILED. After the fix: 53 of 57, with the remainder failing
loudly as unreadable.

OPTIONAL per class: **`pour_fed: "<evidence>"`** — A-AMP measures the narrowest
enforced TRACK width, but a plane-fed net does not conduct through a track, so
on such a class the metric is ADJACENT to the property (the same error shape as
measuring island positions instead of island shapes). Declare the pour geometry
that carries the current — layer, area/width, and the measurement. A bare
`pour_fed: true` is REFUSED: canon M4 wants evidence, not rationale.

Optional per-class `diff_pair:` `{width, gap, via_gap?, max_uncoupled?}` (mm)
declares SOLVED controlled-impedance geometry for a differential-pair class
(2026-07-24, crow-recorder-central-v2 v1.1 / external-review F2: USB-HS 90ohm
was neither constrained nor demonstrated — `diff_pair_dimensions` sat `[]`).
The emitter writes it three ways so it is ACTIVE, not documentation: netclass
`diff_pair_width/gap/via_gap`, a `.kicad_dru` `<CLASS>_diffpair` rule
(`diff_pair_gap` min/opt + optional `diff_pair_uncoupled` max), and the board
`design_settings.diff_pair_dimensions` entry. `gap` is REQUIRED once the key
exists; width/gap must clear the tier's `min_track`/`min_space`. NB: KiCad
pairs nets only by name suffix (P/N, +/-, _P/_N) — a diff_pair class whose
net names cannot pair silently gates NOTHING (rename the nets, e.g.
USB_DM -> USB_DN). Cite the stackup + solve (which fab stackup, Er, h, the
computed Zdiff) in the class `intent` or DETAIL_DESIGN.

Top-level `scoped_floors:` (canon M8 promotion of the hand-appended
insideArea rules) is the machine-enforced form of a scoped exemption:
`{zone, nets, min_width, why}` — the generic emitter writes it as a
last-match `.kicad_dru` rule after the netclass floors. `why` is REQUIRED
(canon M4); `min_width` must still clear the declared tier's `min_track`.

Top-level `scoped_clearances:` is its CLEARANCE twin (2026-07-30, added because
pluto-rx2-8way sat routed and promoted on 49 DRC findings that were ONE missing
capability): `{zone, nets, clearance, why}`, emitted as a last-match
`.kicad_dru` `clearance` constraint. **A SEPARATE LIST, NOT A FIELD ON
`scoped_floors`** — the two validate against different tier floors (`min_track`
vs `min_space`), emit different constraints, and mean different things, and
merging them would make every required key conditional ("`min_width` required
unless `clearance` is present"), which is how a required key stops being
required. **BOUNDED ON BOTH SIDES**: the emitted condition requires
`A.insideArea(zone) && B.insideArea(zone)`, because a one-sided condition
licenses a pair whose second item is anywhere on the board; the net clause is
symmetric (`A.NetName` or `B.NetName`) since the relaxed net can be either
member of the pair (the pluto case is an RF arm against an SMA **PTH ground
post**). **CAVEAT before drawing the area**: KiCad's `insideArea` is true for an
item that OVERLAPS the area, not only one contained by it, so the bound is on
the ITEMS and not on their point of closest approach — draw it tightly. `nets`
and `why` are both REQUIRED (see the key table below for why each is stricter
than its `scoped_floors` counterpart), and `clearance` must still clear the
tier's `min_space`. **THE VALUE MUST NOT SIT ABOVE THE ROUTER'S OWN BUDGET** in
`03_src/route.yaml` (`route.common.clearance` or the overriding
`route.waves[].clearance`): a DRC floor above what KRT was allowed to pack to
re-creates the mismatch `tier_preflight` PF-ROUTE-CLR exists to catch, one
level down.

Top-level `fab_tier:` is also the SINGLE SOURCE of capability floors for
the generic backend (`fab_tier_util.py`): class widths, route/stitch/tap
via geometry and silk text heights are floored/derived from it, and
explicit sub-floor values are generation errors naming the tier.

Floors are BACKSTOPS, not sizing: trunk current rides pours and planes. The
floor's job is to make "silently thin" impossible, not to carry the amps.

## Every net name in this folder is a REFERENCE, and it is MACHINE-CHECKED

**Canon E-NETREF, `net_reference_audit.py PROJECT_DIR`** (`--root REPO` sweeps
the fleet; `--kinds` prints the denominator). A net name written here is not a
label — some gate or generator will LOOK IT UP, and when the lookup misses
almost nothing says so: the reference silently grades, generates or prints
NOTHING and the surrounding verdict stays green. This folder contributes SEVEN of
the twelve graded reference kinds — `nets.yaml` `classes.<C>.nets[]` (a
`.kicad_pro` netclass PATTERN: matching zero nets leaves the class with no
members, so its `min_width`/`clearance` floor is enforced on nothing while
`rules_audit.py`'s class-reaches-the-project check still finds the class present
in the `.kicad_pro` — the two agree and both are content) and
`scoped_floors[].nets[]`; **`length_match.<G>.members.<M>[]` (K12, added
2026-07-29 with canon R-LEN — a phase tolerance addressed to a net the board
does not have grades nothing while READING as a matched pair, and the first
fleet sweep found 64 of 908 references absent, 39 of them written against a
DATASHEET reference design's pin function rather than any net the board has)**;
`electrical_invariants.yaml` `supplies.<NET>`, `invariants[].net` and
`invariants[].chain[]`; `power_tree.yaml` `rails[]/linear_rails[].name`. The
remaining five live in `02_parts/*/part.yaml` (`layout.keep_short[].net`) and
`03_src/floorplan.yaml` (`zones[].net`, `asserts.pad_net[].net`,
`placement.patterns[].pad_overrides[].on_net`, and net-shaped tokens in
`silk.captions[].text`).

Matching is EXACT; only `nets:` entries honour `*`/`?`, because KiCad netclass
patterns are globs. **Substring matching is forbidden and is how the incident
survived** — cooksense's silk printed `GND_ISO ONLY`, a net with 0 occurrences
in the netlist whose only ISO-bearing neighbour is `SPI_MISO`.

A miss is classified, and all three classes are printed. GHOST (absent AND a
named consumer was going to use it) FAILS. UNREACHED is REPORTED and does not
fail, and exactly one kind is there by construction: `power_tree.yaml` rail
`name:` is a LABEL — `power_topology.py` grades the rail's numbers and never
resolves the name — so `name: USB-A` and `name: 3V3_SW_A / 3V3_SW_B / ...` are
legitimate. A board with no exported netlist yet is UNREACHED as a WHOLE, named,
never a wall of ghosts; an empty or non-netlist oracle is UNGRADED at exit 2,
never a green zero. Every unresolved name carries a NEAR-MISS with its counted
denominator (case-fold; the tsx AUTHOR-PREFIX `N`, both directions; difflib; the
underscore family) because `N3V3` -> `3V3` is one edit away and a verdict that
names the candidate turns a hunt into a fix.

**`supplies:` is still owned by `electrical_invariants.py`, not by this audit** —
it can REFUSE at load time, before grading, which a separate audit cannot; E-NETREF
grades it too, and the overlap is deliberate. The `nets.yaml` line under
**Validate** below had said "every net in nets.yaml exists in the netlist" since
this folder was created; it was a sentence a human was supposed to check, and for
its whole history nothing did.

## Structure: `nets.yaml` `length_match:` — canon R-LEN

**A MATCHED SET IS AN INTENT, AND UNTIL 2026-07-29 IT LIVED ONLY IN ADR PROSE.**
`policy_audit.py`'s `R-LEN` row was `re.search(r"length|spread", audit_src)` over
the project's `audit_board.py`, so a COMMENT satisfied it: smc0985-cooksense
PASSED on two remarks about a creepage slot being lengthened, and
**pluto-cal-switch — the board whose release artifact IS a published length
delta — graded N-A, "no timing-critical nets declared"**, while its own `A-SYM`
printed *"the D4 delta is a placement property, not a routing outcome"* over a
comparison of footprint positions. Phase is a property of COPPER; two
mirror-perfect placements joined by two differently-meandered traces have
identical A-SYM and different phase.

Graded by `copper_length_audit.py PROJECT_DIR` (`--census` measures EVERY net
without needing a declaration; `--strict` makes UNREACHED exit 1; `--schema`
prints the authoritative field list; `--root REPO` sweeps the fleet).

Per group, REQUIRED: `adr:` (the ADR that emitted the intent — a tolerance
nobody can re-derive is not evidence, canon M4), `intent:`, and `members:` as a
mapping of >= 2 names to **ORDERED NET CHAINS**. A member is a chain because
series parts split one run into several nets — pluto-cal-switch's matched arm is
`[LOOP_ARM1, PAD_A2A_1, LOOP_ARM1_SW]` across two attenuator chips, and
declaring only the first net is the same authoring defect this fleet already
shipped once in a netclass. A group of ONE member is rejected: it has no spread.

OPTIONAL: `topology:` (`chain`, the default, is VERIFIED from the copper —
zero branch vertices and zero cycles, which makes `total_mm` the path length
exactly; `tree` opts into grading the total on a branching net);
`congruent_pads: true` (the claim that the UNMEASURED pad-entry copper is equal
across members and cancels in the delta — without it the spread is printed and
UNREACHED, because comparing two lower bounds with different unmeasured offsets
is not a measurement); `no_vias: true`; `stackup_mm:` (dielectric thickness
between consecutive copper layers — required ONLY to price via barrels, because
the generated boards carry no `(stackup)` block and assuming equal spacing on
`JLC04161H-7628` prices an F->In1 hop 2.5x too long); `pin:`; `phase:`.

**THE TWO NUMBERS HAVE DIFFERENT JOBS. Getting this right matters more than the
code.** `max_spread_mm:` is a **DRIFT ceiling**, derived: the static delta is
calibrated out in software, but `dtau = TC*dT*dL*t_pd` is not, and at FR-4's
ESTIMATED +100 +-100 ppm/degC over 40 degC a 1 mm spread drifts 0.05 deg at
6 GHz while 20 mm drifts 1.05 deg. **1.0 mm** is the defensible ceiling;
`report` (publish the number, no ceiling) is a legal, stated value. `pin:`
`{spread_mm, tol_mm, measured_on}` is the **REPRODUCIBILITY** check and it is
the one that guards a release — it records the spread the published artifact
CLAIMS and FAILS when the copper moves off it, because KRT is stochastic and a
re-route silently turns every published picosecond into fiction.

**DO NOT WRITE A TOLERANCE TIGHTER THAN ~0.5 mm AND CALL IT PHYSICS.** At
13.19 deg/mm (t_pd 6.105 ps/mm, re-derived from the ordered stackup: eps_eff
3.350 at h 0.2104 mm, Dk 4.4, w 0.36 mm) the switch's OWN published
relative-insertion-phase window is 13.2 deg = 1.00 mm of copper part to part;
mounting-inductance asymmetry adds ~2 deg per fillet per unit. JLC etch
tolerance perturbs trace WIDTH (impedance), not centreline length, and the fab
LENGTH terms are common-mode across two arms on one panel. A ceiling nobody can
hold gets waived into uselessness inside a week; the requirement is that the
delta be **KNOWN, STABLE and REPRODUCIBLE**, not that it be zero.

`no_vias: true` is the ONLY place a per-net via ban is graded ANYWHERE.
Measured 2026-07-29: `route_and_stitch_generic.py` and the pluto `route.yaml`
files carry no such concept — the only mechanism is a per-WAVE
`layers: [F.Cu]`, which is not per-net and is re-checked by nothing. One via on
one arm is a pure DIFFERENTIAL error on a published delta.

## Structure: `policy_waivers.yaml` — the `evidence:` block

**A LOAD-BEARING NUMBER IS A COMMAND AND ITS OUTPUT, NOT A DIGIT.** Canon M4
asks a waiver to carry the measurement that justifies it, and for this file's
whole history "carry" meant *type it into `why:`*. Measured 2026-07-29 by
`waiver_provenance.py` over the fleet: **22 entries across 5 boards, 22 with a
hand-typed measurement and 0 with a re-runnable command.** The failure mode is
not "slightly off" — pluto-rx2-8way's `P-ADJ-UNREACHED` typed *"C_SW1 pad 1 to
U_SW pin 8 = 2.62 mm, inside the 3 mm the datasheet sentence means"* where the
pair measured **3.085 mm** centre-to-centre, the measure `policy_audit.py:412`
itself defines. **The waiver's own conclusion reverses,** and it survived a full
revision cycle past `policy_audit`'s length test on `why` and past
`waiver_provenance`'s prose-similarity checks.

So an entry MAY (and at the next revision of any waiver, SHOULD) carry:

```yaml
- id: P-ADJ-UNREACHED
  refs: [PE42482A-X]
  why: >-
    Pin 8 sits on the global 3V3 net, so no keep_short budget can address it;
    measured against the datasheet's 3 mm by hand instead.
  evidence:
    - claim: C_SW1.1 -> U_SW.8, pad centre to pad centre (P-ADJ's own measure)
      command: |-                      # `|-` — a plain scalar containing ": "
        /usr/bin/python3 -c "import pcbnew, math; ..."
      output: "2.873"                  # EXACTLY ONE number, or it is prose
      budget: "<= 3.0"                 # the CONCLUSION the number carries
      requires: [pcbnew, projects/<board>/04_kicad/<board>.kicad_pcb]
      tolerance: 0.02                  # optional, units of `output`
      tolerance_why: >-                # MANDATORY whenever tolerance is present
        Pad centres move only when the legalizer moves a part, so the only
        legitimate drift is the nanometre-quantised import rounding.
```

Graded by `waiver_provenance.py PROJECTS_ROOT`, which RE-RUNS `command` from the
repo root and DIFFS its last stdout line against `output`:

- **W-SCHEMA** `evidence:` is a non-empty list of mappings; keys are drawn from
  `claim command output budget tolerance tolerance_why grade requires
  why_not_rerunnable note` — an unknown key (a misspelled `commmand:`) is a FAIL,
  because the alternative is the schema silently rotting back into prose. `output`
  carries EXACTLY ONE number; two numbers is prose again.
- **W-GRADE** `grade:` is `CITED` or `ESTIMATED`. CITED requires
  `command`+`output` — a citation claim with nothing cited is a FAIL. ESTIMATED
  requires `why_not_rerunnable:`.
- **W-CMD** the command must be READ-ONLY. The gate EXECUTES what this file says.
- **W-REGEN** the regenerated number disagrees with `output` beyond `tolerance`.
- **W-FLIP** the regenerated number does not satisfy the declared `budget` that
  the typed one did. **THE CONCLUSION REVERSED** — reported separately and never
  excused by a tolerance.
- **W-ARITH** the TYPED `output` fails its own declared `budget`. Costs nothing:
  pure arithmetic on two numbers the author wrote side by side.
- **W-TOL** `tolerance` without `tolerance_why`, or a tolerance `>=` the margin
  `|budget - output|`. **A tolerance that cannot distinguish pass from fail is
  not a tolerance — it is the next typed number**, and this is the check that
  stops the fix from recreating the defect.
- **W-REFS** a `refs:` entry shaped like a repo path must resolve, and a
  `path:LO-HI` span must be inside the file. A line range is a typed number too:
  crow-mic-pod-v2's R-RULES cites `04_kicad/….kicad_dru:8-10`.

THE LADDER, for a number that cannot be regenerated here and now (canon
M-IMPORT — **ESTIMATED, not CITED**, reported with its denominator):
`CITED` (ran, agreed) → `UNVERIFIED` (a declared `requires:` is absent, or the
command timed out or exited non-zero: named on every run, credited to nobody,
and deliberately NOT a fail — a gate whose verdict depends on whether a sibling
agent is mid-rebuild is a gate that gets disabled) → `ESTIMATED` (no command is
possible, and `why_not_rerunnable:` says why) → `OWED` (no `evidence:` block).
OWED entries are printed BY NAME on every run and held under a committed
ceiling, so the existing debt is a list and the NEXT typed number is a hard fail.

## `04_kicad/refdes_waiver.json` is NOT a substitute for an entry here

`generate_board_generic.py` writes that file for ITSELF when its silk placer
finds no slot for a refdes, and `policy_audit.py:793` then reads it and SKIPS
every refdes in it while grading P-SILK-REF. Checker and checked share a method
(canon M1) and the machine is its own witness. **W-MACHINE** requires every
refdes in it to be named in some `refs:` in this file. Measured 2026-07-29:
**2 of 11 fleet-wide** (pluto-rx2-8way's `C_MCU7` + `R_CC1`, under a P-SILK-REF
entry that asked for this check in writing); the other 9 are named debt under a
committed ceiling, and `--strict-machine` fails them.

## Validate

- every net in `nets.yaml` exists in the netlist (else the class is a no-op) —
  now MACHINE-CHECKED as E-NETREF above, at the width of the whole class
- every net carrying >1A per `01_docs/ARCHITECTURE.md`'s power tree appears in
  some class here — an unclassed high-current net is a BUG
- regenerating produces byte-identical `.kicad_dru` + `.kicad_pro`
  netclasses (drift = someone hand-edited the output)
- every `exemptions[].area` names a rule area that exists on the board
- every `policy_waivers.yaml` entry parses, names a real policy ID, and carries
  `why:` + measurement evidence (canon M-WAIV)
- `waiver_provenance.py <repo>/projects` reports every OWED entry BY NAME, no
  W-REGEN / W-FLIP / W-ARITH / W-TOL / W-SCHEMA / W-GRADE / W-CMD / W-REFS
  finding, and no rise in the OWED or machine-waiver ceilings. Every `evidence:`
  `command:` must be re-runnable BY A FRESH SHELL FROM THE REPO ROOT — a command
  that only works in the author's terminal is not a citation
- if `nets.yaml` declares `length_match:`: `copper_length_audit.py <project>
  --strict` exits 0, every member net RESOLVES (E-NETREF K12), and the coverage
  line's `N/M` group and member denominators are non-zero. On an UNROUTED board
  it exits 1 under `--strict` and names every net with no copper — that is the
  correct state, not a pass, and it is what both pluto boards report today
- if `mates.yaml` exists: `import_provenance_check.py <project>` exits 0, and
  the coverage line's `N/M` denominator equals the number of facts the file
  consumes. If it does NOT exist, the BRIEF's `## Mating fact-lock` says the
  board mates to nothing foreign — silence there is not a declaration
- DRC width comparisons are EXACT NANOMETERS: a track at 249800nm prints as
  "0.25" and fails a 0.25mm floor. Round emitted values.

## Repair

- Net in `nets.yaml` but not the netlist → stale; remove it or fix the name.
- High-current net with no class → add it; do not lower the floor to match
  the copper.
- Hand-edit found in `.kicad_dru` → port to `nets.yaml`, regenerate.
- `R-LEN` spread over the ceiling → re-route to equalise; do NOT raise the
  ceiling without re-doing the drift arithmetic in the ADR. KRT cannot do this
  for you: its meander machinery is DIFF-PAIR shaped (intra-pair and inter-pair
  P/N equalisation) and the matched paths here are single-ended nets that must
  match EACH OTHER, which is inter-net skew — a human, iterative task that
  `--census` is the instrument for.
- `R-LEN-PIN` red after a re-route → the published artifact is now fiction.
  RE-MEASURE and RE-PUBLISH, then move the pin. Never move the pin first.
- `R-LEN` UNREACHED on a via → declare `stackup_mm:`, or remove the via if the
  ADR forbade one. Do not treat the barrel as zero.
- Number about a mating target found inline in `mates.yaml`, a floorplan
  comment, or an ADR body → it has a second home now. Move it to
  `spf/<device>/facts.yaml` with its method and grade, and reference the id.

## Every schema key here NAMES THE GATE THAT READS IT — canon G-ORPHAN

**`schema_reader_audit.py --root REPO`** (`--families` prints the denominator).
E-NETREF above grades every net-shaped VALUE in this folder; G-ORPHAN grades
every KEY, in the same method widened from values to the schema itself (canon
M-WIDTH). The reason is the same: a field nothing reads READS AS COVERED. A key
in a board's source with no row below is an ORPHAN and FAILS; `ADVISORY`
(nobody reads it, and that is correct) and `OWED` (a gate is intended and
absent) are DECLARED states and both REQUIRE a reason.

TWO ORPHANS THIS FOLDER'S OWN PROSE HAD HIDDEN, both found by the first run:

* **`nets.yaml` `classes.<C>.intent` / `routing` / `verify` are read by NOTHING
  — not even their PRESENCE.** "Each class requires: `intent`, `nets`,
  `min_width`, `routing`, `verify`" has been in the *Structure: `nets.yaml`*
  section since this folder was created, and 38 classes fleet-wide fill all
  three in; `rules_audit.py` names `intent` only in its own module docstring.
  This is the `current:` lesson repeated one column over — that field got a
  gate (A-AMP) and a "silence is not a declaration" rule, and its three
  neighbours in the same required list got neither. They are declared OWED.
* **`power_tree.yaml` `linear_rails[]` numeric envelopes are read by NOTHING**
  — five rails on smc0985-cooksense with `vin_min`/`vin_max`/`vout_min`/
  `vout_max`/`iout_max_A` filled in, and `power_topology.py` names
  `linear_rails` only in a docstring paragraph explaining that it ignores it.
  The 2026-07-27 LINEAR fix moved cooksense's one true LDO rail INTO `rails:`
  and left five pass-through/load-switch rails behind, where "Vout IS Vin minus
  an Rds(on)/ESR drop" is checkable arithmetic that nothing checks. `name:` IS
  graded (E-NETREF K6, advisory); the numbers are OWED.

### keys: 03_src/rules/integration.yaml

| key | reader | why |
|---|---|---|
| `schema` | `module_first_check.py` | contract version; only schema 1 is accepted |
| `default` | `module_first_check.py` | must state `prefer_module`, making silence deterministic |
| `selections` | `module_first_check.py` | complete denominator of selected complex subsystems |
| `selections[].function` | `module_first_check.py` | names the subsystem being implemented |
| `selections[].part` | `module_first_check.py` | resolves to exactly one used part dossier |
| `selections[].implementation` | `module_first_check.py` | closed choice: `module` or `bare_ic` |
| `selections[].rationale` | `module_first_check.py` | total-complexity fit of the selected implementation |
| `selections[].exception` | `module_first_check.py` | required evidence bundle for every bare-IC choice |
| `selections[].exception.binding_requirement` | `module_first_check.py` | locked requirement no considered module meets |
| `selections[].exception.evidence` | `module_first_check.py` | measured/cited top-level comparison evidence |
| `selections[].exception.modules_considered` | `module_first_check.py` | non-empty module comparison set |
| `selections[].exception.modules_considered[].part` | `module_first_check.py` | considered module identity |
| `selections[].exception.modules_considered[].rejected_because` | `module_first_check.py` | specific binding mismatch |
| `selections[].exception.modules_considered[].evidence` | `module_first_check.py` | vendor artifact, measurement, or dated sourcing result |
| `selections[].exception.adr` | `module_first_check.py` | existing exception ADR under `01_docs/decisions/` |
| `no_applicable_functions` | `module_first_check.py` | explicit, explanatory zero-denominator declaration; refused when scoped parts exist |

### keys: 03_src/rules/nets.yaml

| key | reader | why |
|---|---|---|
| `length_match.<G>.elongation` | `copper_length_audit.py` | opts a group out of the OCTILINEAR FLOOR (`R-LEN-OCT`) by declaring the router may lengthen a short member. **Cross-checked against a real `length_match_group` in `03_src/route.yaml`** — an elongation claim is worth the recipe behind it, and without that link it is a declaration graded by nothing. MEASURED on pluto-rx2-8way: elongation recovered the ENTIRE 1.4966 mm octilinear penalty, landing at 0.3236 mm — the 0.3238 mm Euclidean pad residue, i.e. the floor was never a bound on the ACHIEVABLE spread |
| `length_match.<G>.phase.t_pd_ps_per_mm` | `copper_length_audit.py` | group-specific delay; with `solver_evidence`, cross-checked against both `epsilon_eff` and the solver result |
| `length_match.<G>.phase.f_ghz` | `copper_length_audit.py` | frequency used for degrees/mm; cross-checked against the solver model |
| `length_match.<G>.phase.stackup` | `copper_length_audit.py` | exact stack identity cross-checked against the solver model |
| `length_match.<G>.phase.cross_section` | `copper_length_audit.py` | solver-bound geometry class; a masked/via-fenced artifact cannot be declared bare |
| `length_match.<G>.phase.epsilon_eff` | `copper_length_audit.py` | derives delay and must match the solver result within 0.2% |
| `length_match.<G>.phase.z0_ohm` | `copper_length_audit.py` | controlled-impedance result cross-checked against solver evidence within 0.2% |
| `length_match.<G>.phase.solver_evidence` | `copper_length_audit.py` | machine-readable field-solver artifact; absence or disagreement is a hard R-LEN error |
| `fab_tier` | `fab_tier_util.py, policy_audit.py` | the SINGLE source of capability floors (P-TIER) |
| `default_track_width` | `generate_rules_generic.py` | project-wide default |
| `default_clearance` | `generate_rules_generic.py, tier_preflight.py` | project-wide default |
| `classes.<C>.nets` | `generate_rules_generic.py, rules_audit.py, net_reference_audit.py` | the netclass PATTERN list (E-NETREF K1) |
| `classes.<C>.min_width` | `generate_rules_generic.py, rules_audit.py` | the enforced width floor (A-AMP) |
| `classes.<C>.clearance` | `generate_rules_generic.py, tier_preflight.py` | the enforced clearance floor |
| `classes.<C>.via_diameter` | `generate_rules_generic.py` | netclass via diameter emitted into KiCad board setup |
| `classes.<C>.via_drill` | `generate_rules_generic.py` | netclass via drill emitted into KiCad board setup |
| `classes.<C>.current` | `rules_audit.py` | A-AMP ampacity obligation; silence is not a declaration |
| `classes.<C>.pour_fed` | `rules_audit.py` | A-AMP plane-fed evidence |
| `classes.<C>.diff_pair.width` | `generate_rules_generic.py` | controlled-impedance geometry |
| `classes.<C>.diff_pair.gap` | `generate_rules_generic.py` | controlled-impedance geometry |
| `classes.<C>.diff_pair.via_gap` | `generate_rules_generic.py` | controlled-impedance geometry |
| `classes.<C>.diff_pair.max_uncoupled` | `generate_rules_generic.py` | `.kicad_dru` uncoupled-length max |
| `classes.<C>.intent` | OWED | the *Structure* section above makes it REQUIRED per class and NOTHING reads it — not the text, not its presence. `rules_audit.py` names `intent` only in its own docstring. Owed: the same presence-plus-readability gate `current:` got as A-AMP |
| `classes.<C>.routing` | OWED | REQUIRED per class ("pour vs track, and the strategy") and read by nothing, though it states which conductor actually carries the current that A-AMP grades as a track width |
| `classes.<C>.verify` | OWED | REQUIRED per class ("how to prove it") and read by nothing; a declared verification method that no gate resolves is the R-LEN shape |
| `classes.<C>.exemptions` | OWED | *Validate* above says "every `exemptions[].area` names a rule area that exists on the board" — a sentence a human was supposed to check, and nothing does. Not declared by any board today |
| `scoped_floors[].zone` | `generate_rules_generic.py` | the named rule area the relaxation is scoped to |
| `scoped_floors[].nets` | `generate_rules_generic.py, net_reference_audit.py` | insideArea clause nets (E-NETREF K2) |
| `scoped_floors[].min_width` | `generate_rules_generic.py` | the relaxed floor |
| `scoped_floors[].why` | `generate_rules_generic.py` | REQUIRED evidence (canon M4); the emitter refuses a floor without it |
| `scoped_clearances[].zone` | `generate_rules_generic.py` | the named rule area the ISOLATION relaxation is bounded to; REQUIRED (an unbounded clearance relaxation is a board-wide one) |
| `scoped_clearances[].nets` | `generate_rules_generic.py` | the nets whose isolation is reduced — REQUIRED here though optional for `scoped_floors`, because clearance is a property of a PAIR and "every pair inside this box" is not an isolation argument. NOT yet an E-NETREF kind: an absent net name here still emits a rule that matches nothing (OWED, the K2 twin) |
| `scoped_clearances[].clearance` | `generate_rules_generic.py` | the relaxed gap; must still clear the tier's `min_space` |
| `scoped_clearances[].why` | `generate_rules_generic.py` | REQUIRED evidence (canon M4) — for a STRONGER reason than the width case: a width relaxation is bounded below by ampacity, which A-AMP grades independently from `current:`, while an isolation relaxation has NO downstream grader at all (DRC simply stops reporting what the rule permits) |
| `length_match.<G>.adr` | `copper_length_audit.py` | R-LEN: the ADR that emitted the intent |
| `length_match.<G>.intent` | `copper_length_audit.py` | R-LEN group intent |
| `length_match.<G>.members.<M>` | `copper_length_audit.py, net_reference_audit.py` | the ORDERED net chain measured (E-NETREF K12) |
| `length_match.<G>.max_spread_mm` | `copper_length_audit.py` | R-LEN drift ceiling |
| `length_match.<G>.topology` | `copper_length_audit.py` | chain vs tree |
| `length_match.<G>.congruent_pads` | `copper_length_audit.py` | the unmeasured-pad-copper claim |
| `length_match.<G>.no_vias` | `copper_length_audit.py` | the ONLY place a per-net via ban is graded |
| `length_match.<G>.stackup_mm` | `copper_length_audit.py` | via-barrel pricing |
| `length_match.<G>.pin.spread_mm` | `copper_length_audit.py` | R-LEN-PIN reproducibility |
| `length_match.<G>.pin.tol_mm` | `copper_length_audit.py` | R-LEN-PIN tolerance |
| `length_match.<G>.pin.measured_on` | `copper_length_audit.py` | R-LEN-PIN provenance |
| `length_match.<G>.phase` | OWED | the block's own comment calls it "OPTIONAL reporting aid, never a gate" — and it does not reach the report either: `copper_length_audit.py` prints its phase conversion from constants it re-derives itself (6.105 ps/mm, 13.19 deg/mm), never from this declaration. A board writing `t_pd_ps_per_mm: 6.0` beside a gate using 6.105 has two homes for one number and nothing reconciles them |

### keys: 03_src/rules/electrical_invariants.yaml

| key | reader | why |
|---|---|---|
| `supplies.<NET>` | `electrical_invariants.py, net_reference_audit.py` | `node_level` rail map; the loader REFUSES a net the netlist lacks (E-NETREF K3) |
| `invariants[].assert` | `electrical_invariants.py` | which kind this is |
| `invariants[].net` | `electrical_invariants.py, net_reference_audit.py` | the subject net (E-NETREF K4) |
| `invariants[].pin` | `electrical_invariants.py` | `pin_on_net` subject pin |
| `invariants[].part` | `electrical_invariants.py` | `net_has_part` / `part_value` subject |
| `invariants[].part_type` | `electrical_invariants.py` | `net_has_part` type filter |
| `invariants[].chain` | `electrical_invariants.py, net_reference_audit.py` | `series_chain` elements (E-NETREF K5) |
| `invariants[].through.<REF>` | `electrical_invariants.py` | `series_chain` intermediate parts, keyed by refdes -> the pin pair the current passes through |
| `invariants[].min` | `electrical_invariants.py` | `part_value` lower bound |
| `invariants[].max` | `electrical_invariants.py` | `part_value` upper bound |
| `invariants[].equals` | `electrical_invariants.py` | `part_value` exact value |
| `invariants[].tolerance_pct` | `electrical_invariants.py` | `part_value` tolerance window |
| `invariants[].receiver` | `electrical_invariants.py` | `node_level` REF.PIN |
| `invariants[].driver_state` | `electrical_invariants.py` | `node_level` released/contended |
| `invariants[].must_be` | `electrical_invariants.py` | `node_level` expected logic level |
| `invariants[].aggressor` | `electrical_invariants.py` | cross-domain subject |
| `invariants[].defender` | `electrical_invariants.py` | cross-domain subject |
| `invariants[].adr` | `electrical_invariants.py` | E-ADR: the ADR that emitted it; must be QUOTED |
| `invariants[].why` | `electrical_invariants.py` | REQUIRED evidence (canon M4) |
| `label_survival.exempt` | `net_label_survival.py` | S-NETMERGE exemptions, each needing `why:` |
| `label_survival.pin_map` | `net_label_survival.py` | S-NETMERGE per-pin net assertions |
| `label_survival.pin_map[].refs` | `net_label_survival.py` | references whose indexed pins are checked |
| `label_survival.pin_map[].pins` | `net_label_survival.py` | index-to-expected-net map |
| `label_survival.pin_map[].pins.<N>` | `net_label_survival.py` | expected net pattern for an arbitrary physical pin number |
| `label_survival.pin_map[].n_start` | `net_label_survival.py` | starting index used when expanding the reference list |
| `label_survival.pin_map[].unconnected` | `net_label_survival.py` | pins expected to remain unconnected |

### keys: 03_src/rules/power_tree.yaml

| key | reader | why |
|---|---|---|
| `input_trunk_class` | `power_topology.py` | which netclass carries the trunk current |
| `source_type` | `power_topology.py` | E-OFF: battery vs mains-derived |
| `off_control` | `power_topology.py` | E-OFF: the de-energization path |
| `quiescent_ua` | `power_topology.py` | E-OFF: stored draw when off |
| `pack_capacity_mah` | `power_topology.py` | E-OFF: shelf life arithmetic |
| `ir_floor_mohm` | `power_topology.py` | E-MARGIN default series resistance |
| `rails[].name` | `power_topology.py, net_reference_audit.py` | the rail LABEL (E-NETREF K6 — advisory THERE because no gate resolves it as a net; the KEY is read) |
| `rails[].converter` | `power_topology.py` | E-TOPO: the part whose `type:` is asserted |
| `rails[].vin_min` | `power_topology.py` | E-TOPO envelope + dropout headroom |
| `rails[].vin_max` | `power_topology.py` | E-TOPO envelope + dissipation |
| `rails[].vout_min` | `power_topology.py` | E-TOPO envelope + dissipation |
| `rails[].vout_max` | `power_topology.py` | E-TOPO envelope + dropout headroom |
| `rails[].iout_max_A` | `power_topology.py` | trunk current + dissipation |
| `rails[].eff` | `power_topology.py` | trunk current for a switching rail |
| `rails[].dropout_mv` | `power_topology.py` | per-rail override of the part's dropout |
| `rails[].pdiss_max_mw` | `power_topology.py` | per-rail override of the package rating |
| `rails[].load_uv_threshold` | `power_topology.py` | E-MARGIN: the load's brownout voltage |
| `rails[].ir_budget_mohm` | `power_topology.py` | E-MARGIN: board+connector+cable series R |
| `rails[].margin` | `power_topology.py` | E-MARGIN declared headroom |
| `rails[].feedback` | `power_topology.py` | the FB-divider tolerance window |
| `rails[].feedback.vref` | `power_topology.py` | nominal feedback-reference voltage used in the worst-case output window |
| `rails[].feedback.vref_tol_pct` | `power_topology.py` | feedback-reference tolerance used in both worst-case bounds |
| `rails[].feedback.r_top_ohm` | `power_topology.py` | upper divider resistance used in the worst-case output window |
| `rails[].feedback.r_top_tol_pct` | `power_topology.py` | upper-divider tolerance used in both worst-case bounds |
| `rails[].feedback.r_bottom_ohm` | `power_topology.py` | lower divider resistance used in the worst-case output window |
| `rails[].feedback.r_bottom_tol_pct` | `power_topology.py` | lower-divider tolerance used in both worst-case bounds |
| `rails[].note` | ADVISORY | per-rail prose for a reviewer; the graded facts are the numbers beside it, and no gate resolves the sentence |
| `linear_rails[].name` | `net_reference_audit.py` | E-NETREF K6 resolves it (and reports it UNREACHED by construction) |
| `linear_rails[].kind` | OWED | the closed-ish vocabulary (`protection_pass`, load switch, link) that would decide WHICH bound applies, read by nothing |
| `linear_rails[].element` | OWED | the pass element's refdes — the part whose Rds(on)/ESR sets the drop the envelope claims |
| `linear_rails[].vin_min` | OWED | see the note above: `power_topology.py` names `linear_rails` only in a docstring. Five cooksense rails carry a full envelope no gate reads |
| `linear_rails[].vin_max` | OWED | as `vin_min` |
| `linear_rails[].vout_min` | OWED | as `vin_min`; this is the number the Rds(on)/ESR drop arithmetic would be checked against |
| `linear_rails[].vout_max` | OWED | as `vin_min` |
| `linear_rails[].iout_max_A` | OWED | as `vin_min`; also absent from the trunk-current sum `rails[]` feeds |
| `linear_rails[].ovlo_trip_V` | OWED | an over-voltage trip point, declared once and graded nowhere |
| `linear_rails[].note` | ADVISORY | per-rail prose, as `rails[].note` |

### keys: 03_src/rules/policy_waivers.yaml

| key | reader | why |
|---|---|---|
| `[].id` | `policy_audit.py, waiver_provenance.py` | the WAIVED check-ID; must be a real one |
| `[].refs` | OWED | **A WAIVER IS APPLIED BY `id` ALONE.** `policy_audit.py` builds `waived_ids` from `w["id"]` and never reads `refs:`, and `waiver_provenance.py` reads `why`/`derived_from` only — so a waiver written for `refs: [J1]` silences that check for EVERY ref on the board, and the list reads as a scope it does not have. `policy_audit.py`'s own docstring documents the `{id, refs, why}` shape, which is a MENTION and exactly the R-LEN shape. Owed: honour `refs:` as the waiver's scope, or state in the schema that it is documentation |
| `[].why` | `policy_audit.py, waiver_provenance.py` | M-WAIV: the measurement; an entry without it is a FAIL |
| `[].derived_from` | `waiver_provenance.py` | W-COPY/W-FOREIGN: which board this rationale was inherited from |
