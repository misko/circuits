#!/usr/bin/env python3
"""schema_reader_audit — G-ORPHAN: every schema key a hand-authored source file
declares must NAME the gate that reads it, and that gate must PROVABLY read it.

    python3 schema_reader_audit.py --root REPO_ROOT        # fleet census
    python3 schema_reader_audit.py PROJECT_DIR             # one board
    python3 schema_reader_audit.py --root REPO --families  # the denominator
    python3 schema_reader_audit.py --root REPO --json OUT

WHY THIS EXISTS. A DECLARED FIELD THAT NOTHING READS IS WORSE THAN AN ABSENT
ONE, because it reads as covered. `02_parts/*/part.yaml` may declare
`layout.adjacency:` — a refdes-pair proximity budget — and until 2026-07-29
`policy_audit.py`'s P-ADJ read `keep_short` entries ONLY. So pluto-rx2-8way's
requirement that `U_ESD` sit within ~2.0 mm of `J_USB`, where 6 nH per 10 mm of
loop turns a 17 V clamp into a 305 V spike, was graded by NO GATE AT ALL while
appearing in source as if it were live; a human hand-measured it. Same shape,
same week: `length_match:` did not exist as a schema until the day R-LEN landed,
on two boards whose release artifact IS a length delta; `pins.<N>.tie` — a
net-shaped assertion in 43 dossiers — is read by nothing, and that is the exact
field class the `GND_ISO` ghost that reached shipped silk lived in.

E-NETREF (`net_reference_audit.py`) solved the NARROW version of this: it
enumerated its twelve reference kinds BY READING THE CONSUMERS, and prints each
one with the consumer's name (`--kinds`). Its subject is net-shaped VALUES. This
gate is the same method widened from values to KEYS (canon M-WIDTH): the class
is "a schema key with no reader", and net names are one member of it.

WHERE THE BINDING LIVES, AND WHY IT CANNOT DRIFT.

Not here. A `KEYS = {...}` table in this file would be a REGISTRY — a second
home for the schema, which is precisely the failure the escape-block drift
(2026-07-21) and the cooksense MANIFEST-vs-`assembly.yaml` contradiction were
both instances of. So the binding lives in the ONE artifact that already owns
each schema: the governing contract TEMPLATE under
`skills/pcb-design/templates/contracts/`, which `CLAUDE.md` already makes
mandatory to update in the same change as a schema change, and which
`t1_contracts.py t_skill_contract_sync` already cross-checks. This gate adds no
new home; it makes the existing one EXECUTABLE (ADR-0007).

A declaration is a table under a heading naming the file family it governs:

    ### keys: 03_src/rules/power_tree.yaml

    | key | reader | why |
    |---|---|---|
    | `rails[].vin_min` | `power_topology.py` | E-TOPO envelope |
    | `rails[].name` | ADVISORY | a LABEL: no gate resolves it as a net |
    | `rails[].note` | OWED | free prose; no gate reads it yet |

and the DRIFT is caught in all three directions, which is what makes this
different from a registry:

  * a key appears in real source with NO row  -> ORPHAN, and the gate FAILS.
    Adding a field to a board without saying who reads it is the defect.
  * a row names a reader that does not read it -> UNREAD, and the gate FAILS.
    This is the `layout.adjacency` case and the retired R-LEN predicate's case.
  * a row names a reader that no longer exists, or a file this gate cannot
    parse -> UNPROVABLE, and the gate FAILS. Never a skip (canon M-COVER).

Nothing is restated: the contract holds a CLAIM, and the claim's truth is read
out of the consumer's AST on every run.

WHAT "PROVABLY READS IT" CAN AND CANNOT PROVE. THIS IS THE HARD PART.

R-LEN's whole defect was crediting a WORD's presence: `re.search(r"length|
spread", src)` passed smc0985-cooksense on two comments about a creepage slot
being lengthened. A grep is therefore refused outright. What this gate does
instead, per named consumer:

  PROVES  the key's own name appears as a STRING CONSTANT IN A READ POSITION in
          the consumer's parsed AST — a subscript slice (`d["max_span_mm"]`), a
          `.get`/`.pop`/`.setdefault` first argument, an `==`/`in` comparand, or
          an element of a literal list/tuple/set that code iterates. And it
          proves the same for EVERY literal segment of the key's path, so
          `layout.keep_short[].max_span_mm` requires `layout`, `keep_short` AND
          `max_span_mm` to each be read in the same file. Line numbers are
          printed for each, so a reviewer can check the claim in one jump.

  CANNOT PROVE  (a) that the read is off THIS structure. `"name"` subscripted
          anywhere in `power_topology.py` satisfies `rails[].name`; a same-named
          key on an unrelated dict would too. The path-segment requirement
          raises the bar but does not close this, and it is why the report
          prints the line numbers rather than a bare PASS.
          (b) that the value REACHES A VERDICT. A key read and discarded counts
          as read. That is E-INV's and G-VACUOUS's job, not this gate's.
          (c) a DYNAMICALLY built key (`d[f"{axis}_mm"]`) or one consumed by a
          schema-driven `for k, v in d.items()` loop. Those are invisible here
          and must be declared with an explicit reader that does name the key,
          or as ADVISORY/OWED with a reason.
          (d) anything in a non-Python consumer. A named reader that will not
          `ast.parse` is UNPROVABLE and FAILS, rather than being waved through.

  REFUSES  a MENTION: an exact-match constant that is NOT in a read position —
          a docstring, a message string, a dict literal key. `ast.get_docstring`
          text and `ast.Dict` keys are classified MENTION on purpose, and a
          row whose only evidence is a mention FAILS with that word in the
          finding, because "the gate talks about the key" is the R-LEN error.

ADVISORY IS A DECLARED STATE WITH A REASON, NEVER A SILENT EXEMPTION.

Some keys are legitimately read by nobody, and failing them produces a gate that
gets waived into uselessness. E-NETREF found exactly ONE such kind among twelve;
this gate does not assume the count and asks each contract to name its own. An
`ADVISORY` row REQUIRES a non-empty `why`, and the reasons the fleet actually
has are three distinct mechanisms, not one:

  1. A LABEL THE GRADER NEVER RESOLVES. `power_tree.yaml rails[].name` — the
     E-NETREF precedent. `power_topology.py` grades the rail's NUMBERS and
     never looks the name up, so `name: USB-A` is correct documentation.
  2. INTENT ADDRESSED TO A HUMAN REVIEWER, WHOSE PRESENCE IS ITSELF GRADED.
     `nets.yaml classes.<C>.intent` / `verify`, `layout.notes`, every `why:`.
     No gate resolves the prose; something else (`policy_audit`, `M-WAIV`,
     `contracts_audit`) grades that it EXISTS and is non-empty. Advisory here
     means "the TEXT is not machine-graded", not "the field is unchecked".
  3. A PROVENANCE FACT SPENT OUTSIDE THIS PIPELINE. `datasheet.note`,
     `layout.source`, `land_pattern.*` — read by a person at part-selection
     time. Declaring these OWED would be dishonest: nobody intends a gate.

OWED is the RATCHET, and it is a different claim from ADVISORY: it means a gate
is INTENDED and absent. The two are counted separately for exactly that reason —
`--families` prints both, and a family's OWED count is the debt.

THE RATCHET, AND WHY DAY ONE IS NOT FULL COMPLIANCE.

A gate that reds every contract on day one gets disabled; G-VACUOUS landed 5 of
32 declared with 27 named OWED and its floor pinned so it can only rise, and
this follows it. Two levels:

  * WITHIN a governed family the gate is FULLY hard — every observed key is
    PROVEN, ADVISORY, OWED or ORPHAN, and an ORPHAN fails. There is no partial
    credit inside a family.
  * A file family with NO `### keys:` block anywhere is UNGOVERNED: reported BY
    NAME on every run, and it does not fail. That is the ratchet's only slack,
    it is enumerated rather than silent, and `tests/t1_schema_reader.py`
    `t_governed_family_floor_is_pinned` pins the governed-family count and the
    PROVEN-key count to what the tree achieves, so neither can be lowered to
    buy a green run nor silently lag adoption.

MEASURED ON LANDING (2026-07-29, `--root .` over 6 projects, 176 hand-authored
source files; reproduced every run by `t_real_fleet_denominator`):

  11 governed families, 4 UNGOVERNED and named (`assembly.yaml`, `mates.yaml`,
  `rf.yaml`, `twin_adjudications.yaml`). 420 declared rows include **345
  PROVEN** readers, with 0 ORPHAN. Those rows cover more than 1205 distinct
  schema keys** the fleet's source actually declares, 881 of them under 39 `*`
  SUBTREE claims (`limits.*`, `land_pattern.*`, `stitch.<pass>.*`), which is
  why both numbers are printed: 293/293 alone would overstate it.

FOUR ORPHANS THE FIRST RUN FOUND, each a field that read as covered:

  1. `policy_waivers.yaml [].refs` — **A WAIVER IS APPLIED BY `id` ALONE.**
     `policy_audit.py` builds `waived_ids` from `w["id"]` and never reads
     `refs:`; `waiver_provenance.py` reads `why`/`derived_from` only. So a
     waiver written for `refs: [J1]` silences that check for EVERY ref on the
     board, and `policy_audit.py`'s own docstring documents the `{id, refs,
     why}` shape — a MENTION, the exact R-LEN shape.
  2. `power_tree.yaml linear_rails[]` — five smc0985-cooksense rails with a
     full `vin_min`/`vin_max`/`vout_min`/`vout_max`/`iout_max_A` envelope, and
     `power_topology.py` names `linear_rails` only in a docstring paragraph
     explaining that it ignores it. "Vout IS Vin minus an Rds(on)/ESR drop" is
     checkable arithmetic that nothing checks, and the currents are absent from
     the trunk-current sum too.
  3. `nets.yaml classes.<C>.intent` / `routing` / `verify` — REQUIRED per class
     by the 03_src/rules contract since that folder was created, filled in on
     all 38 fleet classes, read by NOTHING — not even their presence. The
     `current:` field in the same required list got A-AMP and a "silence is not
     a declaration" rule; its three neighbours got neither.
  4. `length_match.<G>.phase` — originally declared "OPTIONAL reporting aid,
     never a gate" while `copper_length_audit.py` printed a different global
     constant. Closed 2026-08-01: the audit consumes the group tuple and, when
     `solver_evidence` is named, cross-checks delay, epsilon, impedance,
     frequency, stackup and cross-section against that artifact.

Plus 21 OWED rows in `02_parts/*/part.yaml`, the file this rule was written
for — among them `pins.<N>.tie` (84 pins, 43 dossiers), `datasheet.sha256` /
`revision` (an M-IMPORT provenance grade nothing recomputes), `sourcing.
do_not_use` (a banned LCSC code no gate refuses) and `escape.checked`.

INDEPENDENCE (canon M1). The claim side is markdown prose in contracts.md; the
proof side is the consumer's Python AST; the denominator side is the boards' own
YAML. Three artifacts, three parsers, no shared method — and in particular this
gate never imports or executes a consumer, so a consumer cannot influence its
own grade.

`pins.<N>.tie` IS NOT CLOSED HERE, DELIBERATELY, AND THE PATCH IS WRITTEN.
`tie:` is a NET NAME (`GND`, `AGND`, `DGND`, `none`) asserting which net a pin
must land on — a reference, which is E-NETREF's subject, not this gate's. It is
declared OWED in the 02_parts contract, and this is the patch its owner should
apply to `net_reference_audit.py` rather than have a second gate resolve nets:

    KINDS["K13"] = ("02_parts/*/part.yaml", "pins.<N>.tie",
                    "electrical_invariants.py pin_on_net (OWED — see below)",
                    True)
    # in collect_parts(), beside the keep_short loop:
    for pin, spec in (d.get("pins") or {}).items():
        if isinstance(spec, dict) and _str(spec.get("tie")) \
                and spec["tie"] not in ("none", "NC", "nc"):
            refs.append(Ref("K13", f"02_parts/{py.parent.name}/part.yaml "
                                   f"pins.{pin}.tie", spec["tie"]))

The `none`/`NC` exclusion is load-bearing: `XU316-1024-TQ128-I24` declares
`tie: none` on four IO-voltage straps that are DELIBERATELY FLOATING, and
failing those would be the false lead that gets K13 waived. Once K13 lands,
the 02_parts row for `pins.<N>.tie` becomes `net_reference_audit.py` and this
gate will hold it there.

NOT WIRED INTO `policy_audit.py`, DELIBERATELY, AND THAT IS A GAP.
This gate lands with its tests, its canon row and its contract sections but is
not called by the policy audit, so no board's `policy_audit.md` reports G-ORPHAN
yet. Two reasons, neither of them doubt. (a) Its subject is the SKILL, not a
board: it grades contract templates against the fleet, so a per-board row would
report the same verdict on every board — the right shape is one repo-level row,
which is `gate_contract_audit.py`'s territory, not `policy_audit.py`'s. (b) At
landing time two boards were mid-rebuild and mid-route, and `policy_audit.py`
was under another agent's edit. **The follow-up is owed:** call it from
`gate_contract_audit.py` beside G-SELFCON (`--root REPO`, exit 0 = PASS, 2 =
UNGRADED not N-A) once that file is quiet. Until then run it by hand; the canon
row, this file and the `### keys:` tables are the authority.

VACUITY: (canon G-VACUOUS. Fixtured by `tests/t1_schema_reader.py`
`t_vacuity_a_family_declared_entirely_OWED_passes`.)

G-ORPHAN PASSES a governed family in which EVERY key is declared `OWED` — a
contract that has named its whole schema and bound none of it to a reader.
The graded fact ("every declared key names a gate that reads it") is then FALSE
for every key in that family, and the exit code is 0. That is the ratchet,
chosen over a day-one wall of red that gets the gate turned off; but it means a
green G-ORPHAN is NOT by itself evidence that any key is bound.

Three things bound it, none of them reachable from inside this audit:
BOUNDED — the slack is exactly the `OWED` set and the ungoverned-family set,
nothing else; every other key is graded in both directions. ENUMERATED — both
sets are printed by name on every run, so the vacuity is never silent, which is
what separates it from the six G-VACUOUS instances of 2026-07-28/29 (each of
those passed with nothing said). MONOTONE — `GOVERNED_FLOOR` and `PROVEN_FLOOR`
are committed integers a reviewer reads, a drop below either is a hard FAIL, and
a test pins them to what the tree measures so they cannot lag adoption either.

Exit 0 when every observed key is PROVEN, ADVISORY or OWED; 1 on any ORPHAN,
UNREAD or UNPROVABLE row, or if either floor is breached; 2 when the audit
itself could not run (unparseable contract, unparseable source, no families
declared, nothing observed) — never a green zero.
"""
import argparse
import ast
import fnmatch
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:                                       # pragma: no cover
    sys.exit("schema_reader_audit needs pyyaml")

#: the contract templates are the ONE home of the declarations (see docstring).
TEMPLATES = "skills/pcb-design/templates/contracts"

#: where a named reader may live. Basename lookup, because a contract naming
#: `skills/kicad-pcb/scripts/policy_audit.py` in full would break the moment a
#: script moves, and the basename is what every other artifact in this repo
#: (design-policies.md, E-NETREF's consumer column) already uses.
READER_DIRS = ("skills/kicad-pcb/scripts", "skills/jlcpcb-fab/scripts",
               "skills/shopping-list/scripts", "scripts")

#: `### keys: <family glob>` — the family is a project-relative glob, so the
#: heading itself declares which files it governs and no list lives in here.
FAMILY_RE = re.compile(r"^###\s+keys:\s+(\S+)\s*$", re.M)

#: hand-authored YAML this gate expects to be governed. Discovery, not a
#: registry: these are DIRECTORY globs over a project, and any file they find
#: that no declared family matches is reported UNGOVERNED. `06_build`,
#: `04_kicad` and `07_releases` are generated or sealed and are not source.
SOURCE_GLOBS = ("01_docs/*.yaml", "03_src/*.yaml", "03_src/rules/*.yaml",
                "02_parts/*/part.yaml")

#: reader-cell keywords. Anything else is read as a comma-separated script list.
ADVISORY, OWED = "ADVISORY", "OWED"

#: THE RATCHET (see the docstring). Committed integers; a drop below either is
#: a hard FAIL, and `t_governed_family_floor_is_pinned` refuses a lowering.
GOVERNED_FLOOR = 18
PROVEN_FLOOR = 634
#: `stitch.seed_stubs.*` and `taps.reattempt.*` bound to
#: route_and_stitch_generic.py, which provably reads both. The floor
#: rises in the commit that EARNS it — that is the whole ratchet.
#: 17 -> 18 families and 575 -> 600 PROVEN on 2026-08-16: the first
#: release-target USB-controlled-hub canary populated model-registration
#: authority and exercised exact model-override/corridor/length-router fields.
#: Missing child-key rows were added only where the named implementations read
#: them; duplicate prose fields were removed. Measured `--root .`: 698/698
#: declared, 600 PROVEN, 0 orphan.
#: 600 -> 607 PROVEN on 2026-08-16: E-FAULT's fixed-load evidence and
#: device-specific slew-limited startup fields were promoted from wildcard
#: coverage to exact reader contracts by the USB controlled-hub canary.
#: 607 -> 608 PROVEN on 2026-08-16: native-model registration gained a
#: tuple-bound SMD all-pad-centre datum instead of assuming every critical
#: package has drilled attachments.
#: 608 -> 614 PROVEN on 2026-08-16: realised `pad_bank_faces` placement
#: assertions made the functional/front bank, target ref/bank, rear bank and
#: optional directional margin executable before routing.
#: 614 -> 634 PROVEN on 2026-08-16: the USB controlled-hub canary added
#: realised-width and partial-wave physical-DRC routing controls plus the
#: connector-orientation contract (model/footprint axes, mating plane,
#: keyed pad, mounted side and explicit exemptions). Every row names the
#: shared reader that consumes it; the fleet sweep remains orphan-free.
#: 16 -> 17 families and 514 -> 551 PROVEN on 2026-08-13: the RF contract's
#: exact route/fence geometry and imported mating-fact schema acquired real
#: readers. Measured `--root .`: 648/648 declared, 551 PROVEN, 0 orphan.
#: 508 -> 514 on 2026-08-13: schema-2 control profiles bind profile identity,
#: revision, canonical source and both generated consumer paths to the
#: canonical control-protocol reader. Measured `--root .`: 610/610 declared,
#: 514 PROVEN, 0 orphan.
#: 424 -> 508 on 2026-08-13: assembly, control-protocol and RF contracts became
#: governed families. Their canonical readers prove 84 additional keys while
#: human-only transfer notes remain explicitly ADVISORY. Measured `--root .`:
#: 604/604 declared, 508 PROVEN, 0 orphan.
#: 419 -> 422 on 2026-08-12: P-AUTH binds `datasheet.sha256` to the
#: digest-selected local review PDF, and the formerly malformed combined
#: tap-via contract row is split into the two keys the stitcher actually reads:
#: `taps.connections[].via` and `.via_protection`.
#: 242 -> 246 on 2026-07-30: nets.yaml `scoped_clearances[]`
#: {zone, nets, clearance, why} bound to generate_rules_generic.py
#: (canon R-SCOPE). This constant is the ONLY line the R-SCOPE change
#: touches in this file — the floor is pinned by EQUALITY
#: (t1_schema_reader.t_governed_family_floor_is_pinned), so a commit that
#: adds contract rows and does NOT raise it leaves the suite red.
#: 246 -> 251 on 2026-07-30: `layout_refs` STOPPED BEING OWED and gained a
#: reader (canon P-PREC, `policy_audit.py`), bringing `layout_refs[].tier`,
#: `[].artifact`, `[].reached` and `[].why` with it — 4 new rows plus the one
#: that changed state, all PROVEN. This is the ratchet paying out exactly as
#: designed: the OWED row named a gate that was INTENDED and absent, and the
#: floor rose in the commit that built it. Measured `--root .`: 307/307
#: declared keys graded OK, 251 PROVEN, 0 orphan.
#: 251 -> 254 on 2026-07-30: `floorplan.yaml` `silk.polarity_marks[]`
#: {ref, pad, text} bound to generate_board_generic.py — THE REPO'S LAST
#: ORPHAN, and the one that shows why the DISCRIMINATING SEGMENT is the whole
#: question. `ref`, `pad` and `text` are each already read in that same file
#: for OTHER structures (`asserts.pad_net[].ref`, `asserts.pad_beyond_edge[]
#: .pad`, `silk.captions[].text`), so all three rows would have scored PROVEN
#: on reads that have nothing to do with polarity silk — the "CANNOT PROVE
#: (a)" case in this file's own docstring, arriving for real. The read that
#: makes the claim TRUE is the single `.get("polarity_marks")` at ~L1657, and
#: deleting THAT one call turns all three rows UNREAD while every one of the
#: decoy reads stays put. Red-verified both directions by
#: `t1_schema_reader.t_polarity_marks_row_rests_on_its_own_read`.
#: 254 -> 304 and 7 -> 8 governed families on 2026-07-31: schema-governance
#: repair added the integration family and bound the newly landed v4/hub source
#: keys. Measured `--root .`: 377/377 declared keys graded OK, 304 PROVEN,
#: 1205 observed keys, 0 orphan, and 3 explicitly named ungoverned families.
#: 304 -> 306 on 2026-08-01: `board.via_protection.{capping,filling}`
#: 306 -> 313 on 2026-08-01: the complete solver-bound phase tuple
#: bound to the generic generator's post-save KiCad setup-token emitter.
#: 323 -> 341 and 8 -> 11 governed families on 2026-08-01: adopted the
#: external-power requirements, switching-stage, and surge-path schemas plus
#: critical-pair mapping. Their readers are early_design_check.py and
#: critical_route_check.py; the pipeline runs both before irreversible layout
#: or routing spend and rechecks realized critical copper after stitch.
#: 341 -> 345 on 2026-08-01: bound schema-2 module support threshold,
#: support-ref inventory and decision rationale to module_first_check.py, and
#: cascaded power-rail input_parent to power_topology.py. The new free-form
#: part.yaml configuration block is explicitly ADVISORY; its load-bearing
#: values must be duplicated into a machine-read rule or firmware gate.
#: 313 -> 321 on 2026-08-01: P-PINMAP `pin_aliases` and executable
#: policy-waiver evidence schema readers.
#: 321 -> 323 on 2026-08-01: the USB interface-standard provenance row and
#: `part.yaml` `twin_body.*` installed-product model authority, the latter
#: consumed by jlc_twin for non-CPL same-camera evidence.
#: 345 -> 381 and 11 -> 13 governed families on 2026-08-10: the findings-ledger
#: maturity controls and selective critical-part accepted facts gained explicit
#: readers; route source selection, pre-route pad rescue and newly landed
#: programmable-hub dossier fields were governed in the same sweep. Measured
#: `--root .`: 461/461 declared rows, 381 PROVEN and 0 orphan.
#: 381 -> 384 on 2026-08-10: the pre-artifact rules source phase reads and
#: readability-grades classes.<C>.intent/routing/verify. Its first real run on
#: USB hub v4 found two malformed current declarations before schematic work.
#: Measured `--root .`: 461/461 declared rows, 384 PROVEN and 0 orphan.

#: how a string constant was used. Ordered weakest-first; only READ and WEAK
#: count as a read.
MENTION, WEAK, READ = "MENTION", "WEAK", "READ"
_RANK = {MENTION: 0, WEAK: 1, READ: 2}

#: a string that is EXACTLY a dotted identifier path — the `get(cfg, "a.b.c")`
#: accessor idiom. Deliberately strict: no spaces, no punctuation, so an English
#: sentence with a full stop in it cannot masquerade as a key path.
DOTTED_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)+$")

#: a bare lower-case identifier — the registry/decorator dispatch key shape.
IDENT_RE = re.compile(r"^[a-z_][a-z0-9_]*$")


class AuditError(Exception):
    """The audit could not run. Exit 2 — never a silent zero (canon M-COVER)."""


# ------------------------------------------------------------------ the claim
class Row:
    """One declared key: its path pattern, its readers, and where it was said."""
    __slots__ = ("family", "key", "readers", "why", "site")

    def __init__(self, family, key, readers, why, site):
        self.family, self.key, self.readers = family, key, readers
        self.why, self.site = why, site

    @property
    def state(self):
        if self.readers == [ADVISORY]:
            return ADVISORY
        if self.readers == [OWED]:
            return OWED
        return "READER"

    def __repr__(self):                                   # pragma: no cover
        return f"<Row {self.family} {self.key} {self.readers}>"


def _cell(s):
    """A markdown table cell -> plain text.

    Only a code span WRAPPING THE WHOLE CELL is unwrapped, and only when the
    cell holds exactly one pair of backticks: a `why` sentence that ENDS with a
    code span (`... as \\`vin_min\\``) otherwise loses its final backtick and
    then its last word, which is how a reason silently truncates in the report.
    """
    s = s.replace("\\|", "|").replace("**", "").strip()
    if s.startswith("`") and s.endswith("`") and s.count("`") == 2:
        s = s[1:-1]
    return s.strip()


def _split_row(line):
    """Split a markdown table row on UNESCAPED pipes.

    `\\|` inside a cell is a literal pipe — the `design:` row's `\\|` block-scalar
    marker is one, and splitting naively tore that cell in three (the same
    markdown-pipe class `contracts_audit.py` was fixed for on 2026-07-25).
    """
    out, cur, esc = [], "", False
    for ch in line:
        if esc:
            cur += "\\" + ch
            esc = False
        elif ch == "\\":
            esc = True
        elif ch == "|":
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur + ("\\" if esc else ""))
    return out[1:-1] if len(out) > 2 else out


def parse_declarations(text, site):
    """-> {family: [Row]} from the `### keys:` tables in one contracts.md.

    The table is read positionally (key | reader | why) rather than by header
    name, because a contract that renames a column has changed the schema of
    the declaration and should fail loudly, not be guessed at.
    """
    out = {}
    marks = list(FAMILY_RE.finditer(text))
    for i, m in enumerate(marks):
        fam = m.group(1)
        body = text[m.end():marks[i + 1].start() if i + 1 < len(marks)
                    else len(text)]
        rows = []
        for line in body.splitlines():
            line = line.strip()
            if not line.startswith("|"):
                if rows and not line:
                    continue
                if rows and not line.startswith("|"):
                    break            # the table ended; ignore trailing prose
                continue
            cells = _split_row(line)
            if len(cells) < 2:
                continue
            key, reader = _cell(cells[0]), _cell(cells[1])
            why = _cell(cells[2]) if len(cells) > 2 else ""
            if not key or set(key) <= set("-: ") or key.lower() == "key":
                continue             # header or separator row
            if reader in (ADVISORY, OWED):
                if not why:
                    raise AuditError(
                        f"{site}: `{fam}` key `{key}` is declared {reader} with "
                        f"no reason. {reader} is a DECLARED state and canon M4 "
                        f"wants evidence, not silence — say what reads it "
                        f"instead, or who is going to")
                readers = [reader]
            else:
                readers = [r.strip() for r in reader.split(",") if r.strip()]
                if not readers:
                    raise AuditError(
                        f"{site}: `{fam}` key `{key}` names no reader at all. "
                        f"Write the script that reads it, or {ADVISORY}/{OWED} "
                        f"with a reason")
            rows.append(Row(fam, key, readers, why, site))
        if rows:
            out.setdefault(fam, []).extend(rows)
    return out


def load_declarations(root):
    """-> {family: [Row]} over every contract TEMPLATE. Raises AuditError."""
    tdir = Path(root) / TEMPLATES
    if not tdir.is_dir():
        raise AuditError(f"{tdir} does not exist — G-ORPHAN reads its "
                         f"declarations from the contract templates and has "
                         f"no second home to fall back on")
    fams = {}
    for c in sorted(tdir.rglob("contracts.md")):
        for fam, rows in parse_declarations(
                c.read_text(encoding="utf-8-sig"),
                str(c.relative_to(root))).items():
            fams.setdefault(fam, []).extend(rows)
    if not fams:
        raise AuditError(
            f"no `### keys: <family>` declaration found under {TEMPLATES} — "
            f"G-ORPHAN would grade 0 keys against 0 claims and report OK, "
            f"which is the vacuous pass it exists to prevent (canon M-COVER)")
    for fam, rows in fams.items():
        seen = {}
        for r in rows:
            if r.key in seen:
                raise AuditError(
                    f"{r.site}: `{fam}` declares key `{r.key}` twice (also "
                    f"{seen[r.key]}) — two homes for one claim is the drift "
                    f"this gate exists to prevent")
            seen[r.key] = r.site
    return fams


# ------------------------------------------------------------------ the proof
def read_positions(tree):
    """{string constant: (strongest use, [line numbers])} for one module AST.

    A constant counts as a READ only where the code uses it to REACH a value.
    Everything else — a docstring, a message, a dict literal's key — is a
    MENTION, and a MENTION is refused: crediting the presence of a word is
    exactly the retired R-LEN predicate's defect.
    """
    seen = {}

    def note(s, kind, lineno):
        if not isinstance(s, str):
            return
        cur = seen.get(s)
        if cur is None or _RANK[kind] > _RANK[cur[0]]:
            seen[s] = (kind, sorted(set((cur[1] if cur else []) + [lineno])))
        else:
            cur[1].append(lineno)
            seen[s] = (cur[0], sorted(set(cur[1])))

    strong, weak = set(), set()
    for node in ast.walk(tree):
        # d["k"] — the canonical read.
        if isinstance(node, ast.Subscript) and \
                isinstance(node.slice, ast.Constant):
            strong.add(id(node.slice))
            note(node.slice.value, READ, node.slice.lineno)
        # d.get("k") / d.pop("k") / d.setdefault("k")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr in ("get", "pop", "setdefault") \
                and node.args and isinstance(node.args[0], ast.Constant):
            strong.add(id(node.args[0]))
            note(node.args[0].value, READ, node.args[0].lineno)
        # k == "x" / k in ("x", ...) — a dispatch on the key name.
        elif isinstance(node, ast.Compare):
            for c in [node.left] + list(node.comparators):
                if isinstance(c, ast.Constant):
                    weak.add(id(c))
                    note(c.value, WEAK, c.lineno)
        # for f in ("a", "b"): d[f]  — a literal collection of key names.
        elif isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            for e in node.elts:
                if isinstance(e, ast.Constant):
                    weak.add(id(e))
                    note(e.value, WEAK, e.lineno)
        # A TABLE-DRIVEN READ: {"track_min_width": "m_TrackMinWidth", ...} then
        # `vals.update(cfg["design_rules"]); for k in vals: setattr(ds,
        # DS_KEYS[k], ...)`. The subscript is DYNAMIC, so the literal dict key
        # is the only place the schema key appears — and it is genuinely the
        # read. Counting it a MENTION rejected all eight of
        # `floorplan.yaml design_rules.*` in generate_board_generic.py, which is
        # the adjacent-property error this repo keeps paying for (a proxy that
        # refuses the tool doing the thing properly). MENTION therefore stays
        # reserved for docstrings, messages and plain assignments — the shapes
        # the retired R-LEN predicate actually credited.
        elif isinstance(node, ast.Dict):
            for k in node.keys:
                if isinstance(k, ast.Constant):
                    weak.add(id(k))
                    note(k.value, WEAK, k.lineno)

    # A DOTTED-PATH ACCESSOR: `get(cfg, "route.common.track_width")`. The whole
    # key path is ONE string constant, so none of its segments is a subscript
    # anywhere. `route_and_stitch_generic.py` reads its entire config this way —
    # 100+ of `route.yaml`'s keys — and refusing the idiom would have declared
    # the router blind to its own config file. Only a string that is EXACTLY a
    # dotted identifier path and sits in a call argument qualifies, and the
    # credit is WEAK, never READ.
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            for arg in list(node.args) + [k.value for k in node.keywords]:
                if isinstance(arg, ast.Constant) \
                        and isinstance(arg.value, str) \
                        and DOTTED_RE.match(arg.value):
                    weak.add(id(arg))
                    for seg in arg.value.split("."):
                        note(seg, WEAK, arg.lineno)
            # A REGISTRY / DECORATOR DISPATCH KEY: `@stitch_pass("drop_dangling")`
            # binds the handler for the `stitch.drop_dangling` config block, and
            # that is the only place the block's name appears in the router.
            # Restricted to a SOLE positional argument that is a bare lower-case
            # identifier, so a prose message cannot qualify — and WEAK, never
            # READ. Without it eighteen `route.yaml` keys read as orphans on a
            # router that demonstrably dispatches on them.
            if len(node.args) == 1 and not node.keywords \
                    and isinstance(node.args[0], ast.Constant) \
                    and isinstance(node.args[0].value, str) \
                    and IDENT_RE.match(node.args[0].value):
                weak.add(id(node.args[0]))
                note(node.args[0].value, WEAK, node.args[0].lineno)

    # everything else that is a bare string constant is a MENTION, recorded so
    # the finding can SAY "mentions but does not read" rather than "absent".
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                and id(node) not in strong and id(node) not in weak:
            note(node.value, MENTION, getattr(node, "lineno", 0))
    return seen


def find_reader(root, name):
    """basename -> Path, searched in the declared script homes."""
    for d in READER_DIRS:
        p = Path(root) / d / name
        if p.is_file():
            return p
    return None


class ReaderCache:
    def __init__(self, root):
        self.root, self._c = Path(root), {}

    def uses(self, name):
        """-> (uses|None, error|None). None+error means UNPROVABLE."""
        if name not in self._c:
            p = find_reader(self.root, name)
            if p is None:
                self._c[name] = (None, f"no such script in {'/'.join(READER_DIRS)}")
            elif p.suffix != ".py":
                self._c[name] = (None, f"{p.name} is not Python — G-ORPHAN "
                                       f"proves a read from a parsed AST and "
                                       f"cannot prove one here")
            else:
                try:
                    self._c[name] = (read_positions(
                        ast.parse(p.read_text(encoding="utf-8-sig"))), None)
                except (SyntaxError, OSError) as e:
                    self._c[name] = (None, f"{p.name} will not parse ({e})")
        return self._c[name]


#: `<NAME>` is a name slot (a user-chosen mapping key); `[]` is a list; a
#: trailing `*` covers a whole subtree. Only the LITERAL segments are proved.
SLOT_RE = re.compile(r"^<[^>]*>$")


def segments(key):
    """`layout.keep_short[].max_span_mm` -> the literal names to prove."""
    out = []
    for seg in key.replace("[]", "").split("."):
        if not seg or seg == "*" or SLOT_RE.match(seg):
            continue
        out.append(seg)
    return out


def prove(row, cache):
    """-> (verdict, detail). verdict in PROVEN / UNREAD / UNPROVABLE."""
    segs = segments(row.key)
    if not segs:
        return "UNPROVABLE", (f"key `{row.key}` has no literal segment to "
                              f"prove — it is all name slots")
    best = {}
    for name in row.readers:
        uses, err = cache.uses(name)
        if uses is None:
            return "UNPROVABLE", f"reader {name}: {err}"
        for s in segs:
            kind, lines = uses.get(s, (None, []))
            if kind is None:
                continue
            cur = best.get(s)
            if cur is None or _RANK[kind] > _RANK[cur[0]]:
                best[s] = (kind, name, lines[:4])
    missing = [s for s in segs
               if s not in best or best[s][0] == MENTION]
    if missing:
        detail = []
        for s in missing:
            if s in best:
                detail.append(f"{s!r} appears in {best[s][1]} only as a MENTION "
                              f"(line{'s' if len(best[s][2]) > 1 else ''} "
                              f"{', '.join(str(n) for n in best[s][2])}) — a "
                              f"docstring/message/dict-literal key, not a read")
            else:
                detail.append(f"{s!r} does not appear in any read position at "
                              f"all")
        return "UNREAD", "; ".join(detail)
    proof = ", ".join(f"{s}={best[s][0]}@{best[s][1]}:"
                      f"{','.join(str(n) for n in best[s][2])}" for s in segs)
    return "PROVEN", proof


# -------------------------------------------------------------- the observed
def load_yaml(path):
    try:
        return yaml.safe_load(Path(path).read_text(encoding="utf-8-sig"))
    except Exception as e:                                # noqa: BLE001
        raise AuditError(f"{path}: unparseable YAML ({e})")


class Trie:
    """The declared key patterns of one family, as a walkable tree.

    Built from the contract rows ONLY. The name-slot positions therefore come
    from the declaration too — nothing in this file knows that `classes` is
    keyed by class name, which is what keeps the schema single-homed.
    """

    def __init__(self):
        self.kids = {}
        self.row = None          # a row terminating exactly here
        self.subtree = None      # a row whose pattern ended in `*`

    @classmethod
    def build(cls, rows):
        root = cls()
        for r in rows:
            node, parts = root, cls.split(r.key)
            star = parts and parts[-1] == "*"
            if star:
                parts = parts[:-1]
            for p in parts:
                node = node.kids.setdefault(p, cls())
            if star:
                node.subtree = r
            else:
                node.row = r
        return root

    @staticmethod
    def split(key):
        """`a.b[].c` -> ['a', 'b', '[]', 'c']; `<X>` and `*` stay as tokens."""
        out = []
        for seg in key.split("."):
            while seg.endswith("[]"):
                seg, tail = seg[:-2], "[]"
                if seg:
                    out.append(seg)
                out.append(tail)
                seg = ""
            if seg:
                out.append(seg)
        return out

    def child(self, name):
        """Resolve one observed mapping key -> (node, canonical token, matched?).

        Precedence: an exact literal beats a name slot beats an inherited
        subtree. Most-specific-wins, so a contract can enumerate two keys of a
        blanket-declared subtree without ambiguity. The canonical token is the
        DECLARED spelling — `<REF>` where the declaration has a name slot — so
        the observed denominator counts schema keys, not refdes instances.
        """
        if name in self.kids:
            return self.kids[name], name, True
        for k, v in self.kids.items():
            if SLOT_RE.match(k):
                return v, k, True
        return None, None, False


def observe(family, path, trie, rel):
    """-> (counted, orphans) for one source file, walked against the trie.

    A key with no row is reported ONCE at its topmost undeclared level and the
    walk stops there: a new block of ten fields is ONE finding, not ten, which
    is the difference between a verdict an author acts on and a wall.
    """
    counted, orphans = {}, []
    data = load_yaml(path)

    def walk(node, value, path_s, inherited):
        if isinstance(value, dict):
            for k, v in value.items():
                k = str(k)
                kid, tok, matched = node.child(k) if node else (None, None,
                                                               False)
                if not matched:
                    here = f"{path_s}.{k}" if path_s else k
                    if inherited is not None:
                        counted.setdefault(inherited.key, []).append(here)
                        continue           # covered by a `*` subtree row
                    orphans.append(here)
                    continue
                here = f"{path_s}.{tok}" if path_s else tok
                sub = kid.subtree or inherited
                if kid.row is not None:
                    counted.setdefault(kid.row.key, []).append(here)
                elif kid.subtree is not None:
                    counted.setdefault(kid.subtree.key, []).append(here)
                elif not kid.kids and sub is None:
                    orphans.append(here)
                    continue
                walk(kid, v, here, sub)
        elif isinstance(value, list):
            kid = node.kids.get("[]") if node else None
            for v in value:
                if kid is None:
                    walk(node, v, path_s + "[]", inherited)
                else:
                    walk(kid, v, path_s + "[]", kid.subtree or inherited)

    walk(trie, data, "", trie.subtree)
    return counted, orphans, rel


# --------------------------------------------------------------- the verdict
def grade(root, projects):
    """-> report dict. Raises AuditError when it cannot run at all."""
    root = Path(root)
    fams = load_declarations(root)
    cache = ReaderCache(root)
    tries = {f: Trie.build(rows) for f, rows in fams.items()}

    # (1) the CLAIM side: every row proved against its named reader.
    rows_out, fails = [], []
    for fam in sorted(fams):
        for r in sorted(fams[fam], key=lambda x: x.key):
            if r.state == "READER":
                verdict, detail = prove(r, cache)
            else:
                verdict, detail = r.state, r.why
            rows_out.append({"family": fam, "key": r.key, "state": verdict,
                             "readers": r.readers, "detail": detail,
                             "site": r.site, "seen": 0, "files": 0,
                             "covers": set()})
            if verdict == "UNREAD":
                fails.append(
                    f"G-ORPHAN UNREAD {fam} `{r.key}`: declared read by "
                    f"{', '.join(r.readers)} ({r.site}), and that gate does "
                    f"NOT read it — {detail}. Either the reader moved, or the "
                    f"field is graded by nothing while reading as covered")
            elif verdict == "UNPROVABLE":
                fails.append(
                    f"G-ORPHAN UNPROVABLE {fam} `{r.key}`: {detail} "
                    f"({r.site}). A reader this gate cannot parse is a FAIL, "
                    f"never a skip (canon M-COVER)")
    by_key = {(x["family"], x["key"]): x for x in rows_out}

    # (2) the OBSERVED side: every key in real hand-authored source.
    ungoverned, orphans, files_seen = {}, [], 0
    for proj in projects:
        proj = Path(proj)
        for g in SOURCE_GLOBS:
            for p in sorted(proj.glob(g)):
                rel = str(p.relative_to(proj))
                fam = next((f for f in sorted(fams)
                            if fnmatch.fnmatch(rel, f)), None)
                if fam is None:
                    ungoverned.setdefault(rel, []).append(proj.name)
                    continue
                files_seen += 1
                counted, orph, _ = observe(fam, p, tries[fam], rel)
                for key, sites in counted.items():
                    row = by_key.get((fam, key))
                    if row is not None:
                        row["seen"] += len(sites)
                        row["files"] += 1
                        row["covers"].update(sites)
                for o in orph:
                    orphans.append((fam, o, f"{proj.name}/{rel}"))
    if not files_seen:
        raise AuditError(
            f"no source file matched any declared family across "
            f"{len(projects)} project(s) — 0 keys over 0 files is not a pass")

    seen_orphans = {}
    for fam, key, site in orphans:
        seen_orphans.setdefault((fam, key), []).append(site)
    for (fam, key), sites in sorted(seen_orphans.items()):
        fails.append(
            f"G-ORPHAN ORPHAN {fam} `{key}`: declared in {len(sites)} source "
            f"file(s) ({', '.join(sorted(sites)[:3])}"
            f"{', ...' if len(sites) > 3 else ''}) and named by NO row in the "
            f"governing contract template. Nothing states which gate reads it, "
            f"so it may be graded by nothing while reading as covered — add a "
            f"row naming the reader, or {ADVISORY}/{OWED} with a reason")

    # (3) the RATCHET. The floors are counts of THIS repo's contracts, so they
    # apply only when the tree under grade is the one this script lives in —
    # `gate_contract_audit.py`'s `own_tree` precedent. A scratch fixture tree
    # legitimately declares three keys and must not be told it is 236 short.
    proven = sum(1 for x in rows_out if x["state"] == "PROVEN")
    own_tree = (Path(__file__).resolve().parents[3] == root.resolve())
    if own_tree:
        if len(fams) < GOVERNED_FLOOR:
            fails.append(
                f"G-ORPHAN: {len(fams)} governed file famil(ies), below the "
                f"committed floor of {GOVERNED_FLOOR}. The floor may only "
                f"RISE — a family losing its `### keys:` block is a coverage "
                f"regression")
        if proven < PROVEN_FLOOR:
            fails.append(
                f"G-ORPHAN: {proven} key(s) with a PROVEN reader, below the "
                f"committed floor of {PROVEN_FLOOR}. Do not lower the number "
                f"to buy a green run")

    counts = {s: sum(1 for x in rows_out if x["state"] == s)
              for s in ("PROVEN", ADVISORY, OWED, "UNREAD", "UNPROVABLE")}
    # THE OBSERVED DENOMINATOR (canon M-COVER). A row ending in `*` is a claim
    # about a whole SUBTREE, so "293 rows all graded" would overstate the
    # coverage of a family whose fact bags are blanket-declared. Both numbers
    # are printed: how many DECLARED rows there are, and how many distinct
    # schema keys the fleet's source actually contains under them.
    for x in rows_out:
        x["covers"] = sorted(x["covers"])
    blanket = [x for x in rows_out if x["key"].endswith("*")]
    observed = len({(x["family"], k) for x in rows_out for k in x["covers"]})
    return {"root": str(root), "families": sorted(fams), "rows": rows_out,
            "observed_keys": observed,
            "blanket": {"rows": len(blanket),
                        "covers": sum(len(x["covers"]) for x in blanket)},
            "counts": counts, "orphans": sorted(seen_orphans),
            "ungoverned": sorted(ungoverned), "files": files_seen,
            "fails": fails, "own_tree": own_tree,
            "floors": {"governed": GOVERNED_FLOOR, "proven": PROVEN_FLOOR}}


def report(rep, out=print):
    n = len(rep["rows"])
    c = rep["counts"]
    graded = c["PROVEN"] + c[ADVISORY] + c[OWED]
    out(f"G-ORPHAN schema-reader audit — input: {rep['root']}/{TEMPLATES} "
        f"(claims) x {rep['files']} hand-authored source file(s) (denominator)")
    out(f"  {graded}/{n} declared key(s) graded OK across "
        f"{len(rep['families'])} governed famil(ies): "
        f"{c['PROVEN']} PROVEN, {c[ADVISORY]} advisory, {c[OWED]} OWED, "
        f"{c['UNREAD']} UNREAD, {c['UNPROVABLE']} UNPROVABLE; "
        f"{len(rep['orphans'])} ORPHAN key(s) in source with no row")
    out(f"  the fleet's source declares {rep['observed_keys']} distinct schema "
        f"key(s) under those rows; {rep['blanket']['rows']} row(s) are `*` "
        f"SUBTREE claims covering {rep['blanket']['covers']} of them")
    out(f"  {'family':<40} {'rows':>4} {'obsv':>4} {'prov':>4} {'advi':>4} "
        f"{'owed':>4} {'bad':>4}")
    for fam in rep["families"]:
        rs = [x for x in rep["rows"] if x["family"] == fam]
        out(f"  {fam:<40} {len(rs):>4} "
            f"{len({k for x in rs for k in x['covers']}):>4} "
            f"{sum(1 for x in rs if x['state'] == 'PROVEN'):>4} "
            f"{sum(1 for x in rs if x['state'] == ADVISORY):>4} "
            f"{sum(1 for x in rs if x['state'] == OWED):>4} "
            f"{sum(1 for x in rs if x['state'] in ('UNREAD', 'UNPROVABLE')):>4}")
    owed = [x for x in rep["rows"] if x["state"] == OWED]
    if owed:
        out(f"  OWED — a gate is INTENDED and absent ({len(owed)}):")
        for x in owed:
            out(f"    {x['family']} `{x['key']}`: {x['detail']}")
    adv = [x for x in rep["rows"] if x["state"] == ADVISORY]
    if adv:
        out(f"  ADVISORY — declared read by nobody, with a reason ({len(adv)}):")
        for x in adv:
            out(f"    {x['family']} `{x['key']}`: {x['detail']}")
    if rep["ungoverned"]:
        out(f"  UNGOVERNED file famil(ies) — no `### keys:` block anywhere, "
            f"reported not failed ({len(rep['ungoverned'])}):")
        for f in rep["ungoverned"]:
            out(f"    {f}")
    if rep["fails"]:
        out(f"  FINDINGS ({len(rep['fails'])}):")
        for f in rep["fails"]:
            out(f"    {f}")
    out(f"G-ORPHAN: {'FAIL' if rep['fails'] else 'PASS'} — {graded}/{n} "
        f"declared keys graded OK ({c['PROVEN']} with a PROVEN reader, floor "
        f"{rep['floors']['proven']}"
        f"{'' if rep['own_tree'] else ' NOT APPLIED: not this script’s repo'}"
        f"), {len(rep['orphans'])} orphan, "
        f"{len(rep['ungoverned'])} ungoverned famil(ies)")
    return len(rep["fails"])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("project", nargs="?", help="one PROJECT_DIR to grade")
    ap.add_argument("--root", help="repo root; grades every projects/* board")
    ap.add_argument("--repo", help="repo root when PROJECT_DIR is outside it")
    ap.add_argument("--families", action="store_true",
                    help="print the declared families + their rows and exit")
    ap.add_argument("--json", help="write the full report here")
    a = ap.parse_args(argv)

    if not a.root and not a.project:
        ap.error("give a PROJECT_DIR or --root")
    repo = Path(a.repo or a.root or Path(a.project).resolve().parent.parent)
    if a.families:
        try:
            fams = load_declarations(repo)
        except AuditError as e:
            print(f"G-ORPHAN: UNGRADED — {e}")
            return 2
        for fam in sorted(fams):
            print(f"{fam}  ({len(fams[fam])} declared key(s))")
            for r in sorted(fams[fam], key=lambda x: x.key):
                print(f"    {r.key:<44} {', '.join(r.readers)}")
        return 0

    projects = ([p for p in sorted((Path(a.root) / "projects").glob("*"))
                 if p.is_dir()] if a.root else [Path(a.project)])
    try:
        rep = grade(repo, projects)
    except AuditError as e:
        print(f"G-ORPHAN: UNGRADED — {e}")
        return 2
    n = report(rep)
    if a.json:
        Path(a.json).write_text(json.dumps(rep, indent=1), encoding="utf-8")
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main())
