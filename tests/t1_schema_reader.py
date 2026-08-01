#!/usr/bin/env python3
"""T1: the SCHEMA-READER gate (canon G-ORPHAN) — schema_reader_audit.py.

Motivating measurement: **a declared field that nothing reads is worse than an
absent one, because it reads as covered.** `02_parts/*/part.yaml` may declare
`layout.adjacency:` and until 2026-07-29 P-ADJ read `keep_short` entries ONLY,
so pluto-rx2-8way's requirement that `U_ESD` sit within ~2.0 mm of `J_USB` —
where 6 nH per 10 mm of loop turns a 17 V clamp into a 305 V spike — was graded
by NO GATE AT ALL while sitting in source as if it were live. A human had to
hand-measure it. Same week, same class: `length_match:` did not exist as a
schema until R-LEN landed, on two boards whose release artifact IS a length
delta; `pins.<N>.tie` names a net on 84 pins across 43 dossiers and nothing
reads it, which is the field class the `GND_ISO` ghost that reached shipped silk
lived in.

The first run of this gate found four more (all four are asserted below, against
REAL project and REAL script bytes, in `t_real_findings_*`):

  1. `policy_waivers.yaml [].refs` — a waiver is applied by `id` ALONE.
  2. `power_tree.yaml linear_rails[]` — five cooksense rails, full envelopes,
     read only by a docstring paragraph explaining they are ignored.
  3. `nets.yaml classes.<C>.intent`/`routing`/`verify` — REQUIRED per class,
     filled in on 38 fleet classes, read by nothing, not even their presence.
  4. `length_match.<G>.phase` — "a reporting aid" that does not reach the report.

RED-VERIFICATION (new-gate variant, per tests/README "Adding a regression").
`schema_reader_audit.py` did not exist before this commit, so there is no
pre-fix code to swap in: MEASURED pre-fix output for every case here is
`/usr/bin/python3: can't open file '.../schema_reader_audit.py': [Errno 2] No
such file or directory`, exit 2 — no gate, no verdict. Where a stronger red is
available it is taken instead of leaning on an absent file:

  * `t_mention_in_a_docstring_is_not_a_read` reproduces THE DEFECT ALGORITHM
    inline — `re.search(key, source_text)`, which is exactly the retired R-LEN
    predicate that passed smc0985-cooksense on two comments about a creepage
    slot being lengthened — and asserts it credits the reader while this gate
    FAILS it. That is a real RED against the wrong algorithm.
  * `t_advisory_declared_passes_undeclared_fails` is the both-halves
    discrimination on ONE input: the same key, same tree, one line of contract
    changed, opposite verdicts.
  * `t_real_findings_*` and `t_real_fleet_denominator` read REAL bytes
    read-only, so the incidents are pinned rather than modelled.

Every known-bad fixture here is a PASSING fixture broken in exactly ONE way.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, ROOT, SCRIPTS, check, contains, eq,  # noqa: E402
                     main, must_fail, must_pass, not_contains, run, test,
                     tmpdir)

SRA = SCRIPTS / "schema_reader_audit.py"

#: a reader that genuinely READS every key the clean fixture declares.
GOOD_READER = '''#!/usr/bin/env python3
"""A gate. Its docstring mentions ghost_key and nothing else does."""
import sys


def grade(cfg):
    tier = cfg["fab_tier"]
    out = []
    for name, c in (cfg.get("classes") or {}).items():
        out.append((name, c["min_width"], c.get("current")))
    return tier, out


print("PASS" if grade({}) else "FAIL")
'''

#: the SAME reader with `min_width` demoted to a MENTION: the exact string is
#: still in the file, as a plain assignment and in a message, and it is no
#: longer used to reach a value. A grep predicate cannot tell the two apart.
MENTION_READER = GOOD_READER.replace(
    'c["min_width"]', 'c["clearance"]').replace(
    "import sys", 'import sys\n\nLABEL = "min_width"   # a caption, not a read')


def repo(d, contract, readers=None, source=None, project="bd"):
    """Build a scratch REPO ROOT: contract templates + readers + one project."""
    d = Path(d)
    cdir = d / "skills" / "pcb-design" / "templates" / "contracts" / "03_src" \
        / "rules"
    cdir.mkdir(parents=True, exist_ok=True)
    (cdir / "contracts.md").write_text(contract, encoding="utf-8")
    sdir = d / "skills" / "kicad-pcb" / "scripts"
    sdir.mkdir(parents=True, exist_ok=True)
    for name, body in (readers or {"reader.py": GOOD_READER}).items():
        (sdir / name).write_text(body, encoding="utf-8")
    pdir = d / "projects" / project / "03_src" / "rules"
    pdir.mkdir(parents=True, exist_ok=True)
    (pdir / "nets.yaml").write_text(source if source is not None else SRC,
                                    encoding="utf-8")
    return d


#: the clean source: three keys, each with a row below.
SRC = """\
fab_tier: JLC04161H
classes:
  PWR:
    min_width: 0.5
    current: "2 A"
"""

CLEAN = """\
# contract: 03_src/rules/

### keys: 03_src/rules/nets.yaml

| key | reader | why |
|---|---|---|
| `fab_tier` | `reader.py` | capability floors |
| `classes.<C>.min_width` | `reader.py` | the enforced width floor |
| `classes.<C>.current` | `reader.py` | ampacity obligation |
"""


def sweep(d, extra=()):
    return run([KPY, str(SRA), "--root", str(d)] + list(extra))


# ------------------------------------------------------------------ clean
@test("G-ORPHAN passes a tree where every declared key names a reader that "
      "PROVABLY reads it, and prints both denominators")
def t_clean_passes():
    d = tmpdir()
    r = sweep(repo(d, CLEAN))
    must_pass(r, "G-ORPHAN on a fully bound tree")
    contains(r.out, "G-ORPHAN: PASS")
    contains(r.out, "3 PROVEN")
    # M-COVER: the CLAIM count and the OBSERVED count are both printed, and
    # they are different numbers with different jobs.
    contains(r.out, "3/3 declared key(s) graded OK")
    contains(r.out, "distinct schema key(s) under those rows")
    # the proof NAMES its evidence, so a reviewer can check it in one jump
    contains(r.out, "1 governed famil")


@test("--families prints the declared denominator and every row's reader")
def t_families_names_a_reader():
    d = tmpdir()
    r = sweep(repo(d, CLEAN), ["--families"])
    must_pass(r, "--families")
    contains(r.out, "03_src/rules/nets.yaml  (3 declared key(s))")
    for k in ("fab_tier", "classes.<C>.min_width", "classes.<C>.current"):
        contains(r.out, k)
    # every row names a consumer: the column IS the argument that a miss
    # costs something (the E-NETREF --kinds precedent).
    eq(r.out.count("reader.py"), 3, "rows naming a reader")


# --------------------------------------------------------------- known-bad
@test("G-ORPHAN FAILS a key that appears in real source with NO row in the "
      "governing contract — the `layout.adjacency` class", kind="known_bad")
def t_orphan_key_fails():
    d = tmpdir()
    src = SRC + "    routing: pour\n"          # ONE new key, undeclared
    r = sweep(repo(d, CLEAN, source=src))
    must_fail(r, "G-ORPHAN on an undeclared key", "ORPHAN")
    contains(r.out, "classes.<C>.routing")
    contains(r.out, "named by NO row in the governing contract")
    # and it must NOT be reported as a reader problem: the contract is silent
    not_contains(r.out, "UNREAD 03_src/rules/nets.yaml `classes.<C>.routing")


@test("G-ORPHAN reports ONE finding for a whole undeclared BLOCK, at its "
      "topmost level — a wall of findings is a verdict nobody acts on")
def t_orphan_reported_once_at_the_top():
    d = tmpdir()
    src = SRC + """\
length_match:
  ARMS:
    adr: "0004"
    intent: "matched"
    members: {a: [N1], b: [N2]}
"""
    r = sweep(repo(d, CLEAN, source=src))
    must_fail(r, "G-ORPHAN on an undeclared block", "ORPHAN")
    eq(r.out.count("G-ORPHAN ORPHAN"), 1, "orphan findings for one block")
    contains(r.out, "`length_match`")
    for buried in ("max_spread_mm", "`length_match.<G>.adr`"):
        not_contains(r.out, buried)


@test("G-ORPHAN FAILS a row whose NAMED reader does not read the key — the "
      "field is graded by nothing while reading as covered", kind="known_bad")
def t_unread_row_fails():
    d = tmpdir()
    r = sweep(repo(d, CLEAN, readers={"reader.py": MENTION_READER}))
    must_fail(r, "G-ORPHAN on a reader that dropped the key", "UNREAD")
    contains(r.out, "`classes.<C>.min_width`")
    contains(r.out, "declared read by reader.py")


@test("a key MENTIONED in the reader's docstring and read nowhere is refused, "
      "and the finding SAYS 'MENTION' — the retired R-LEN predicate credited "
      "exactly this and passed cooksense on a creepage comment",
      kind="known_bad")
def t_mention_in_a_docstring_is_not_a_read():
    d = tmpdir()
    d = repo(d, CLEAN, readers={"reader.py": MENTION_READER})
    r = sweep(d)
    must_fail(r, "G-ORPHAN on a docstring mention", "MENTION")
    contains(r.out, "not a read")

    # RED AGAINST THE WRONG ALGORITHM, not against an absent file. This is
    # the R-LEN predicate: a regex over the raw source text. It credits the
    # reader, so a gate built this way would report the field covered.
    text = (d / "skills" / "kicad-pcb" / "scripts"
            / "reader.py").read_text()
    check(re.search(r"min_width", text) is not None,
          "the pre-fix (grep) predicate must CREDIT this reader — if it "
          "does not, the fixture is not reproducing the R-LEN defect")


@test("G-ORPHAN FAILS a row naming a reader that does not exist, and one that "
      "is not Python — UNPROVABLE is a FAIL, never a skip (M-COVER)",
      kind="known_bad")
def t_unprovable_reader_fails():
    d = tmpdir()
    c = CLEAN.replace("| `fab_tier` | `reader.py` |",
                      "| `fab_tier` | `moved_away.py` |")
    r = sweep(repo(d, c))
    must_fail(r, "G-ORPHAN on a missing reader", "UNPROVABLE")
    contains(r.out, "no such script")
    d = tmpdir()
    c = CLEAN.replace("| `fab_tier` | `reader.py` |",
                      "| `fab_tier` | `rebuild_all.sh` |")
    dd = repo(d, c)
    (dd / "skills" / "kicad-pcb" / "scripts"
     / "rebuild_all.sh").write_text("# fab_tier\n", encoding="utf-8")
    r = sweep(dd)
    must_fail(r, "G-ORPHAN on a shell reader", "UNPROVABLE")
    contains(r.out, "is not Python")


@test("an ADVISORY or OWED row with no reason is UNGRADED at exit 2 — a "
      "declared state without evidence is canon M4 failing", kind="known_bad")
def t_state_without_a_reason_is_ungraded():
    for state in ("ADVISORY", "OWED"):
        d = tmpdir()
        c = CLEAN.replace("| `fab_tier` | `reader.py` | capability floors |",
                          f"| `fab_tier` | {state} |  |")
        r = sweep(repo(d, c))
        eq(r.rc, 2, f"{state} with no reason")
        contains(r.out, "G-ORPHAN: UNGRADED")
        contains(r.out, "with no reason")


@test("a row naming NO reader at all is UNGRADED at exit 2", kind="known_bad")
def t_empty_reader_cell_is_ungraded():
    d = tmpdir()
    c = CLEAN.replace("| `fab_tier` | `reader.py` | capability floors |",
                      "| `fab_tier` |  | capability floors |")
    r = sweep(repo(d, c))
    eq(r.rc, 2, "empty reader cell")
    contains(r.out, "names no reader at all")


@test("the same key declared TWICE is UNGRADED at exit 2 — two homes for one "
      "claim is the drift this gate exists to prevent", kind="known_bad")
def t_duplicate_row_is_ungraded():
    d = tmpdir()
    c = CLEAN + "\n| `fab_tier` | `reader.py` | again |\n"
    r = sweep(repo(d, c))
    eq(r.rc, 2, "duplicate row")
    contains(r.out, "twice")


@test("a tree with NO `### keys:` declaration anywhere is UNGRADED at exit 2, "
      "never a green zero over zero (M-COVER)", kind="known_bad")
def t_no_declarations_is_ungraded():
    d = tmpdir()
    r = sweep(repo(d, "# contract: 03_src/rules/\n\nnothing declared.\n"))
    eq(r.rc, 2, "no declarations")
    contains(r.out, "G-ORPHAN: UNGRADED")
    contains(r.out, "would grade 0 keys against 0 claims")


@test("a declared family that matches NO source file is UNGRADED at exit 2 — "
      "0 keys over 0 files is not a pass", kind="known_bad")
def t_no_source_is_ungraded():
    d = tmpdir()
    dd = repo(d, CLEAN)
    (dd / "projects" / "bd" / "03_src" / "rules" / "nets.yaml").unlink()
    r = sweep(dd)
    eq(r.rc, 2, "no source file")
    contains(r.out, "no source file matched any declared family")


# ------------------------------------------- the both-halves discrimination
@test("ADVISORY with a reason PASSES while the SAME key UNDECLARED FAILS — one "
      "line of contract, one tree, opposite verdicts")
def t_advisory_declared_passes_undeclared_fails():
    src = SRC + "    intent: 'the 2 A trunk'\n"
    d = tmpdir()
    c = CLEAN + ("| `classes.<C>.intent` | ADVISORY | prose for a "
                 "reviewer; the enforced numbers beside it are graded |\n")
    r = sweep(repo(d, c, source=src))
    must_pass(r, "G-ORPHAN with the key declared ADVISORY")
    contains(r.out, "ADVISORY — declared read by nobody, with a reason")
    contains(r.out, "`classes.<C>.intent`")
    d = tmpdir()
    r = sweep(repo(d, CLEAN, source=src))         # the row REMOVED
    must_fail(r, "G-ORPHAN with the same key undeclared", "ORPHAN")
    contains(r.out, "`classes.<C>.intent`")


@test("a `*` SUBTREE row covers a whole fact bag, and the report says HOW MANY "
      "keys it swallowed — 293/293 alone would overstate the coverage")
def t_subtree_row_is_counted_as_a_blanket():
    src = SRC + """\
limits:
  vin_abs_max: 6.5
  t_j_max: 150
  esd_hbm_kv: 2
"""
    d = tmpdir()
    c = CLEAN + ("| `limits.*` | ADVISORY | the open per-part datasheet "
                 "fact bag; the executable channel is an assert |\n")
    r = sweep(repo(d, c, source=src))
    must_pass(r, "G-ORPHAN with a blanket subtree row")
    contains(r.out, "1 row(s) are `*` SUBTREE claims covering 4 of them")


# ----------------------------------------------------------------- vacuity
@test("G-ORPHAN PASSES a family whose EVERY key is declared OWED — the "
      "ratchet's blind spot, bounded, enumerated and floored",
      kind="vacuity", gate="schema_reader_audit.py")
def t_vacuity_a_family_declared_entirely_OWED_passes():
    """VACUITY (canon G-VACUOUS). The graded fact is "every declared key names
    a gate that reads it". A contract may declare its whole schema OWED — a
    gate is intended for each key and absent — and G-ORPHAN exits 0 over it,
    with the fact FALSE for every key in that family. Chosen over a day-one
    wall of red that gets the gate disabled, exactly as G-VACUOUS itself did.

    THE CONTRAST (asserted at the end, after the must_pass) is what
    distinguishes a blind spot from a fact the gate cannot represent: the SAME
    tree with ONE row moved from `OWED` to a NAMED reader — a reader that does
    not read the key — FAILS. So the gate is not blind to unread keys in
    general; it is blind exactly where a contract declares the debt, which is
    the bound. The other two bounds are outside this fixture: the OWED set is
    enumerated in the output (asserted here), and `GOVERNED_FLOOR` /
    `PROVEN_FLOOR` are committed integers pinned by
    `t_governed_family_floor_is_pinned` and made to bite by
    `t_floors_bite_when_the_tree_falls_short`."""
    owed = """\
# contract: 03_src/rules/

### keys: 03_src/rules/nets.yaml

| key | reader | why |
|---|---|---|
| `fab_tier` | OWED | a tier gate is intended and absent |
| `classes.<C>.min_width` | OWED | an ampacity gate is intended and absent |
| `classes.<C>.current` | OWED | an ampacity gate is intended and absent |
"""
    d = tmpdir()
    r = sweep(repo(d, owed))
    must_pass(r, "G-ORPHAN over a wholly-OWED family")
    contains(r.out, "G-ORPHAN: PASS")
    contains(r.out, "0 with a PROVEN reader")
    # ENUMERATED: the vacuity is never silent.
    contains(r.out, "OWED — a gate is INTENDED and absent (3)")
    for k in ("fab_tier", "classes.<C>.min_width", "classes.<C>.current"):
        contains(r.out, k)

    # THE CONTRAST — one row changed, same tree, opposite verdict.
    bound = owed.replace("| `fab_tier` | OWED |", "| `fab_tier` | `reader.py` |")
    d2 = tmpdir()
    r2 = sweep(repo(d2, bound, readers={"reader.py": "X = 1\nprint('PASS')\n"}))
    must_fail(r2, "the same tree with one key BOUND to a reader that does not "
                  "read it", "UNREAD")


@test("the floors BITE: a tree short of the committed counts FAILS, naming "
      "both numbers — the MONOTONE half of the vacuity bound", kind="known_bad")
def t_floors_bite_when_the_tree_falls_short():
    r = run([KPY, "-c",
             "import sys;sys.argv=['x','--root',%r];"
             "sys.path.insert(0,%r);import schema_reader_audit as g;"
             "g.GOVERNED_FLOOR=99;g.PROVEN_FLOOR=9999;sys.exit(g.main())"
             % (str(ROOT), str(SCRIPTS))])
    must_fail(r, "G-ORPHAN with the floors raised above the tree",
              "below the committed floor")
    contains(r.out, "Do not lower the number")
    contains(r.out, "may only RISE")


# ------------------------------------------------------------- the ratchet
@test("the floors are PINNED to what this tree measures — they may not be "
      "lowered to buy a green run, nor silently lag adoption")
def t_governed_family_floor_is_pinned():
    """G-VACUOUS's `VACUITY_FLOOR` precedent. The floor is data a human edits
    in a file a reviewer reads, and this test measures the tree so the number
    cannot drift in either direction."""
    src = SRA.read_text(encoding="utf-8")
    gov = int(re.search(r"^GOVERNED_FLOOR = (\d+)", src, re.M).group(1))
    prov = int(re.search(r"^PROVEN_FLOOR = (\d+)", src, re.M).group(1))
    r = run([KPY, str(SRA), "--root", str(ROOT)])
    must_pass(r, "G-ORPHAN on this repo")
    m = re.search(r"(\d+) PROVEN,", r.out)
    f = re.search(r"across (\d+) governed famil", r.out)
    check(m and f, f"could not read the measured counts back:\n{r.out[:800]}")
    eq(int(f.group(1)), gov, "governed families measured vs GOVERNED_FLOOR")
    eq(int(m.group(1)), prov, "PROVEN rows measured vs PROVEN_FLOOR")


@test("an UNGOVERNED file family is reported BY NAME and does not fail — the "
      "ratchet's only slack, and it is never silent")
def t_ungoverned_family_is_named_not_failed():
    d = tmpdir()
    dd = repo(d, CLEAN)
    (dd / "projects" / "bd" / "03_src" / "rules"
     / "assembly.yaml").write_text("service: pcba\n", encoding="utf-8")
    r = sweep(dd)
    must_pass(r, "G-ORPHAN with an ungoverned family present")
    contains(r.out, "UNGOVERNED file famil")
    contains(r.out, "03_src/rules/assembly.yaml")


# --------------------------------------------------------------- real bytes
@test("the REAL fleet denominator: 8 governed families over the real projects, "
      "with the observed-key count and the blanket count both printed")
def t_real_fleet_denominator():
    r = run([KPY, str(SRA), "--root", str(ROOT)])
    must_pass(r, "G-ORPHAN on the real repo")
    contains(r.out, "8 governed famil")
    contains(r.out, "0 ORPHAN key(s) in source with no row")
    m = re.search(r"declares (\d+) distinct schema key\(s\) under those rows; "
                  r"(\d+) row\(s\) are", r.out)
    check(m, "the observed denominator is missing from the verdict")
    check(int(m.group(1)) > 900,
          f"the fleet's observed schema shrank to {m.group(1)} keys — if that "
          f"is real, re-measure; if not, the walker stopped covering something")
    # the three families with no `### keys:` block are named, not silent
    for fam in ("assembly.yaml", "mates.yaml", "twin_adjudications.yaml"):
        contains(r.out, fam)


@test("REAL FINDING — a policy waiver is applied by `id` ALONE: policy_audit.py "
      "reads no `refs:`, so a waiver written for one refdes silences the check "
      "for every ref — and `refs:` is OVERLOADED, which is why it survived")
def t_real_finding_waiver_refs_is_not_a_scope():
    """NARROWED 2026-07-29, and the narrowing is the interesting part.

    This fixture first asserted that NEITHER `policy_audit.py` nor
    `waiver_provenance.py` reads `refs:`. Within the hour the M4 evidence work
    landed `W-REFS`, which resolves path-shaped `refs:` and validates that a
    cited line span exists — so `waiver_provenance.py` now genuinely reads it and
    the fixture correctly refused to keep claiming otherwise.

    What survives is sharper: **`refs:` is OVERLOADED.** Most fleet entries use
    it as an EVIDENCE POINTER (file paths, now validated by W-REFS); three use it
    as a SCOPE (refdes lists), and `policy_audit.py` — the only consumer that
    could honour a scope — still builds `waived_ids` from `w["id"]` alone. So
    cooksense's `P-SILK-FN` waiver names 22 refdes and silences that check
    BOARD-WIDE; a 23rd failing refdes is silent, on the board carrying a 30 V
    NOT-SELV terminal where connector labelling is the safety story.

    The ambiguity is the reason nobody noticed: a reader who checks whether
    `refs:` is read finds that it is, and stops. The fixture therefore pins the
    CONSUMER, not the key."""
    # the CLAIM side: the contract now says OWED and says why
    c = (ROOT / "skills/pcb-design/templates/contracts/03_src/rules"
         / "contracts.md").read_text(encoding="utf-8")
    contains(c, "A WAIVER IS APPLIED BY `id` ALONE", "the rules contract")
    # the PROOF side, measured here rather than trusted: `refs` reaches no read
    # position in either named gate, while `id` and `why` do.
    sys.path.insert(0, str(SCRIPTS))
    import ast
    import schema_reader_audit as g
    # policy_audit is the ONLY consumer that could honour a scope, and it is the
    # one pinned. waiver_provenance DOES read `refs:` now (W-REFS validates
    # path-shaped citations) — that is the evidence-pointer use, not the scope
    # use, so it is asserted separately below rather than folded in.
    for name in ("policy_audit.py",):
        uses = g.read_positions(ast.parse(
            (SCRIPTS / name).read_text(encoding="utf-8-sig")))
        kind = uses.get("refs", (None,))[0]
        check(kind in (None, g.MENTION),
              f"{name} now READS 'refs' ({kind}) — if it reads it as a SCOPE the "
              f"finding is closed: move the contract row from OWED to name this "
              f"gate and retire this fixture. If it reads it as an evidence "
              f"POINTER the finding stands and this assertion needs re-narrowing, "
              f"not deleting")
        check(uses.get("id", (None,))[0] == g.READ,
              f"{name} must read 'id' — if it does not, the fixture is not "
              f"reproducing the asymmetry that IS the finding")


@test("REAL FINDING — power_topology.py names `linear_rails` only in a "
      "DOCSTRING: five cooksense rails carry a full Vin/Vout/Iout envelope "
      "that no gate reads")
def t_real_finding_linear_rails_envelope_is_unread():
    sys.path.insert(0, str(SCRIPTS))
    import ast
    import schema_reader_audit as g
    text = (SCRIPTS / "power_topology.py").read_text(encoding="utf-8-sig")
    uses = g.read_positions(ast.parse(text))
    check(uses.get("linear_rails", (None,))[0] is None,
          f"power_topology.py now reaches 'linear_rails' in a read position "
          f"({uses.get('linear_rails')}) — the finding is closed; move the "
          f"power_tree rows off OWED")
    eq(uses.get("rails", (None,))[0], g.READ,
       "'rails' in power_topology.py (the contrast: the sibling key IS read)")
    # RED AGAINST THE WRONG ALGORITHM: the word IS in the file, twice, inside
    # a docstring paragraph explaining that the checker ignores the key. A grep
    # predicate — the retired R-LEN shape — would report this field covered.
    check(text.count("linear_rails") >= 1,
          "the fixture is not reproducing the defect: 'linear_rails' must "
          "APPEAR in power_topology.py for the grep-vs-AST contrast to mean "
          "anything")
    r = run([KPY, str(SRA), "--root", str(ROOT)])
    contains(r.out, "`linear_rails[].vin_min`")
    contains(r.out, "OWED — a gate is INTENDED and absent")


@test("REAL FINDING — `nets.yaml` classes.<C>.intent/routing/verify are "
      "REQUIRED per class by this folder's own contract, filled in fleet-wide, "
      "and read by nothing — not even their presence")
def t_real_finding_class_intent_is_unread():
    sys.path.insert(0, str(SCRIPTS))
    import ast
    import schema_reader_audit as g
    uses = g.read_positions(ast.parse(
        (SCRIPTS / "rules_audit.py").read_text(encoding="utf-8-sig")))
    for k in ("intent", "routing", "verify"):
        check(uses.get(k, (None,))[0] in (None, g.MENTION),
              f"rules_audit.py now reads {k!r} — close the OWED row")
    # the contrast: the fourth member of the same REQUIRED list DID get a gate
    eq(uses.get("current", (None,))[0], g.READ, "'current' in rules_audit.py")
    r = run([KPY, str(SRA), "--root", str(ROOT)])
    for k in ("classes.<C>.intent", "classes.<C>.routing",
              "classes.<C>.verify"):
        contains(r.out, k)


@test("REAL FINDING — `pins.<N>.tie` names a net on 84 pins across 43 real "
      "dossiers and NOTHING reads it; the E-NETREF K13 patch is written out "
      "rather than a second net resolver being built")
def t_real_finding_pins_tie_is_owed_with_its_patch():
    import ast
    sys.path.insert(0, str(SCRIPTS))
    import schema_reader_audit as g
    for name in ("pin_audit.py", "electrical_invariants.py",
                 "net_reference_audit.py", "policy_audit.py"):
        uses = g.read_positions(ast.parse(
            (SCRIPTS / name).read_text(encoding="utf-8-sig")))
        check(uses.get("tie", (None,))[0] in (None, g.MENTION),
              f"{name} now reads 'tie' — if that is E-NETREF K13 landing, move "
              f"the 02_parts row off OWED and retire this assertion")
    # the OWED row and the patch both exist, in ONE place each
    doc = SRA.read_text(encoding="utf-8")
    contains(doc, 'KINDS["K13"]', "the K13 patch in the gate's docstring")
    contains(doc, 'spec["tie"] not in ("none", "NC", "nc")',
             "the tie: none exclusion — four XU316 straps float deliberately")
    parts_c = (ROOT / "skills/pcb-design/templates/contracts/02_parts"
               / "contracts.md").read_text(encoding="utf-8")
    contains(parts_c, "| `pins.<N>.tie` | OWED |", "the 02_parts OWED row")
    # and the measurement: 43 dossiers, read straight off the tree
    n = len([p for p in (ROOT / "projects").glob("*/02_parts/*/part.yaml")
             if re.search(r"^\s*\S+:\s*\{[^}]*\btie:", p.read_text(
                 encoding="utf-8-sig"), re.M)])
    check(n >= 40, f"only {n} dossiers declare a pins.<N>.tie — re-measure the "
                   f"claim in the 02_parts contract before trusting it")


# ----------------------------------------- the module 3D envelope (2026-07-30)
REAL_02PARTS = (ROOT / "skills/pcb-design/templates/contracts/02_parts"
                / "contracts.md")

#: a gate that genuinely reads `mpn`, so the fixture family has a PROVEN row and
#: the only thing under test is the `mechanical` block.
MPN_READER = '''#!/usr/bin/env python3
"""A gate that reads the MPN."""


def grade(d):
    return d["mpn"]
'''

#: the defect CONSTRUCTED, not borrowed from a live dossier (tests/README, the
#: third-instance rule): a part.yaml carrying a module 3D envelope, shaped after
#: pluto-rx2-8way-v2's RP2040-Zero — four stack scalars plus the open per-feature
#: bag, including the two facts the contract calls out as unchecked arithmetic.
ENVELOPE_PART = """\
mpn: RP2040-Zero
mechanical:
  pcb_thickness_mm: 1.091
  top_side_max_height_mm: 3.250
  bottom_side_max_protrusion_mm: 1.000
  total_thickness_mm: 5.341
  crystal: {side: bottom, protrusion_mm: 1.000,
            extent_mm: [[6.975, 10.925], [3.320, 6.420]]}
  usb_c:
    mating_face_y_mm: 24.816
    z_mm: [-0.910, 3.250]
"""


def _shipped_mechanical_rows():
    """The five `mechanical.` rows LIFTED VERBATIM out of the shipped contract.

    Not a transcription: the fixture below grades the rows this repo actually
    ships, so deleting or weakening them in the template shows up HERE rather
    than in a copy that drifted. `mechanical_pads.<NAME>.*` does not match — the
    character after `mechanical` is `_`, not `.`.
    """
    rows = [ln for ln in REAL_02PARTS.read_text(encoding="utf-8").splitlines()
            if ln.startswith("| `mechanical.")]
    eq(len(rows), 5, "`mechanical.` rows lifted from the shipped 02_parts "
                     "contract (4 enumerated scalars + 1 `*` bag)")
    return rows


def _parts_repo(d, rows):
    """A scratch repo whose 02_parts contract carries `rows` and nothing else."""
    d = Path(d)
    cdir = d / "skills/pcb-design/templates/contracts/02_parts"
    cdir.mkdir(parents=True, exist_ok=True)
    (cdir / "contracts.md").write_text(
        "# contract: 02_parts/\n\n### keys: 02_parts/*/part.yaml\n\n"
        "| key | reader | why |\n|---|---|---|\n"
        "| `mpn` | `reader.py` | the MPN authority |\n"
        + "".join(r + "\n" for r in rows), encoding="utf-8")
    sdir = d / "skills/kicad-pcb/scripts"
    sdir.mkdir(parents=True, exist_ok=True)
    (sdir / "reader.py").write_text(MPN_READER, encoding="utf-8")
    pdir = d / "projects/bd/02_parts/RP2040-Zero"
    pdir.mkdir(parents=True, exist_ok=True)
    (pdir / "part.yaml").write_text(ENVELOPE_PART, encoding="utf-8")
    return d


@test("G-ORPHAN FAILS a part.yaml module 3D ENVELOPE whose contract rows are "
      "absent — the 2026-07-30 defect, with the shipped rows lifted VERBATIM so "
      "the red side is re-measured every run instead of asserted in a docstring",
      kind="known_bad")
def t_known_bad_module_envelope_with_no_contract_row():
    """THE INCIDENT, and it is the whole reason this suite was red at 217ea175.

    pluto-rx2-8way-v2's RP2040-Zero dossier grew a `mechanical:` block — the
    module's 3D envelope, every number MEASURED off the vendor Creo STEP —
    because the module is NOT flat-backed: 23 components sit on the
    carrier-facing face, the 12 MHz crystal 1.000 mm proud, so the joint plane
    and the collision plane are the same plane and the part cannot sit down.
    That number is why the board's `assembly.yaml` refuses to have `U_MCU`
    machine-placed. It arrived with NO row in the governing contract, and
    G-ORPHAN failed 2 of this file's assertions naming it.

    RED-VERIFY, BOTH DIRECTIONS, ON ONE TREE — the `t_advisory_declared_passes_
    undeclared_fails` shape applied to real shipped bytes. Removing the rows is
    exactly `git show HEAD~:...contracts.md`, so the pre-fix contract is what
    the red half grades; the green half then restores them and re-measures. If
    the rows are ever deleted from the template the lift asserts 5 and this
    fixture goes red on the CLAIM side before it ever reaches the gate.

    GIT-SWAP RED-VERIFIED 2026-07-30, and BOTH new fixtures were confirmed to
    bite rather than riding the two pre-existing failures. The pre-fix contract
    restored over the fixed one (`git show HEAD:...02_parts/contracts.md`), this
    file measured **22 passed / 4 failed / 10 known-bad**: the two the defect was
    reported as (`t_governed_family_floor_is_pinned`,
    `t_real_fleet_denominator`) PLUS this fixture and its REAL-FINDING sibling.
    Restored, **26 / 0 / 11**, exit 0. The pre-fix G-ORPHAN run itself measured
    `307/307 declared keys graded OK (251 PROVEN, floor 251), 1 orphan` — a
    ratchet floor MET and a genuinely new schema key with no contract home,
    which is why this landed as a contract row and not as a floor edit."""
    rows = _shipped_mechanical_rows()

    # RED — the pre-fix contract: the `mpn` row alone, envelope ungoverned.
    r = sweep(_parts_repo(tmpdir(), []))
    must_fail(r, "G-ORPHAN on an ungoverned module envelope", "ORPHAN")
    contains(r.out, "`mechanical`")
    # ONE finding for the whole block, at its topmost level — not eight
    not_contains(r.out, "`mechanical.pcb_thickness_mm`: declared in")

    # GREEN, the ADJACENT-PROPERTY re-verify: same tree, same source bytes,
    # the shipped rows restored and nothing else changed.
    d2 = _parts_repo(tmpdir(), rows)
    r2 = sweep(d2)
    must_pass(r2, "G-ORPHAN with the shipped `mechanical.` rows in place")
    contains(r2.out, "0 ORPHAN key(s) in source with no row")

    # and the ENUMERATION is real, not a blanket wearing four hats: the four
    # stack scalars are credited to their OWN rows, the open feature bag to the
    # `*` row. A single `mechanical.*` would have passed the gate too, and would
    # have governed nothing (the contract's own "enumerating a key out of a
    # subtree is always the stronger move").
    import json
    out = Path(d2) / "rep.json"
    must_pass(sweep(d2, ["--json", str(out)]), "the JSON report")
    cov = {x["key"]: x["covers"] for x in json.loads(
        out.read_text(encoding="utf-8"))["rows"]}
    eq(cov.get("mechanical.bottom_side_max_protrusion_mm"),
       ["mechanical.bottom_side_max_protrusion_mm"],
       "the SEATABILITY scalar is credited to its own row")
    eq(sorted(cov.get("mechanical.*", [])),
       ["mechanical", "mechanical.crystal", "mechanical.usb_c"],
       "the `*` row covers the open feature bag and NOT the four scalars")


@test("REAL FINDING — the module 3D ENVELOPE is read by NOTHING, and the "
      "obvious candidate reader is a NAME COLLISION that would score PROVEN "
      "while grading a different file's field")
def t_real_finding_module_envelope_has_no_reader_and_the_obvious_one_collides():
    """The finding is not "nobody reads it" — it is that the fix which makes
    the finding go quiet costs ONE WORD and is FALSE.

    `assembly_coverage.py` contains `"mechanical"` in a READ position (a set
    literal, line 84), so naming it in the 02_parts contract would score PROVEN.
    That occurrence is the closed `reason:` vocabulary of
    `03_src/rules/assembly.yaml` — a different file, a different structure —
    and is limitation (a) of `schema_reader_audit.py`'s own docstring ("cannot
    prove the read is off THIS structure") arriving as a live temptation rather
    than a caveat. The DISCRIMINATOR is the block's own fields: the key NAME is
    read somewhere in the fleet, and `bottom_side_max_protrusion_mm` is read
    nowhere at all. Same word, different structure, opposite conclusions.

    MEASURED 2026-07-30 across nine candidate consumers: the key reaches a read
    position in exactly one, and that one is the collision.

    RATCHET: this FAILS LOUDLY when the finding is closed, naming the rows to
    move off OWED — that breakage is the fix landing, not a regression."""
    import ast
    sys.path.insert(0, str(SCRIPTS))
    import schema_reader_audit as g

    # (1) the eight candidates that could plausibly own a part's 3D envelope
    for name in ("import_provenance_check.py", "policy_audit.py",
                 "escape_check.py", "part_facts_check.py", "pin_audit.py",
                 "generate_board_generic.py", "export_jlc_package.py",
                 "placement_gates.py"):
        p = g.find_reader(ROOT, name)
        check(p is not None, f"{name} is not in {g.READER_DIRS}")
        uses = g.read_positions(ast.parse(p.read_text(encoding="utf-8-sig")))
        check(uses.get("mechanical", (None,))[0] in (None, g.MENTION),
              f"{name} now reads 'mechanical' — if that is M-IMPORT's machine "
              f"half reaching 02_parts, move the five `mechanical.` rows off "
              f"OWED to name this gate and retire this assertion")

    # (2) the COLLISION, asserted rather than avoided — and its discriminator
    ac = g.read_positions(ast.parse(g.find_reader(ROOT, "assembly_coverage.py")
                                    .read_text(encoding="utf-8-sig")))
    check(ac.get("mechanical", (None,))[0] not in (None, g.MENTION),
          "assembly_coverage.py no longer reads the word 'mechanical' — the "
          "collision this fixture pins has moved; re-read the 02_parts G-ORPHAN "
          "section before trusting its warning")
    check(ac.get("bottom_side_max_protrusion_mm") is None,
          "assembly_coverage.py now reads the envelope's own field, so the "
          "occurrence is no longer a collision — re-grade the contract rows")

    # (3) the CLAIM side: the rows exist, say OWED, and name the settlement
    c = REAL_02PARTS.read_text(encoding="utf-8")
    contains(c, "| `mechanical.bottom_side_max_protrusion_mm` | OWED |",
             "the 02_parts seatability row")
    contains(c, "| `mechanical.*` | OWED |", "the 02_parts feature-bag row")
    contains(c, "would score PROVEN and grade NOTHING",
             "the 02_parts G-ORPHAN section's collision warning")


# -------------------------------------- silk.polarity_marks (2026-07-30)
REAL_03SRC = (ROOT / "skills/pcb-design/templates/contracts/03_src"
              / "contracts.md")
REAL_GBG = SCRIPTS / "generate_board_generic.py"

#: the ONE call that makes the three rows true. Everything else the rows name
#: (`ref`, `pad`, `text`) is read in that same file for OTHER structures.
_POLARITY_READ = 'self.silk_cfg.get("polarity_marks")'

#: a floorplan declaring the block and NOTHING else, so the only thing the
#: fixture can be measuring is these three rows.
POLARITY_FLOORPLAN = """\
silk:
  polarity_marks:
    - {ref: LED_ST, pad: 1, text: "K"}
"""


def _shipped_polarity_rows():
    """The three `silk.polarity_marks` rows LIFTED VERBATIM from the shipped
    03_src contract — not transcribed, so weakening them in the template goes
    red HERE rather than in a copy that drifted."""
    rows = [ln for ln in REAL_03SRC.read_text(encoding="utf-8").splitlines()
            if ln.startswith("| `silk.polarity_marks")]
    eq(len(rows), 3, "`silk.polarity_marks` rows lifted from the shipped "
                     "03_src contract (ref + pad + text)")
    return rows


def _floorplan_repo(d, rows, reader_src):
    """A scratch repo: `rows` as the whole floorplan contract, `reader_src` as
    `generate_board_generic.py`, and one board declaring the block."""
    d = Path(d)
    cdir = d / "skills/pcb-design/templates/contracts/03_src"
    cdir.mkdir(parents=True, exist_ok=True)
    (cdir / "contracts.md").write_text(
        "# contract: 03_src/\n\n### keys: 03_src/floorplan.yaml\n\n"
        "| key | reader | why |\n|---|---|---|\n"
        + "".join(r + "\n" for r in rows), encoding="utf-8")
    sdir = d / "skills/kicad-pcb/scripts"
    sdir.mkdir(parents=True, exist_ok=True)
    (sdir / "generate_board_generic.py").write_text(reader_src,
                                                    encoding="utf-8")
    pdir = d / "projects/bd/03_src"
    pdir.mkdir(parents=True, exist_ok=True)
    (pdir / "floorplan.yaml").write_text(POLARITY_FLOORPLAN, encoding="utf-8")
    return d


@test("REAL FINDING CLOSED — `silk.polarity_marks` rows rest on ONE read, and "
      "deleting it turns all three UNREAD while `ref`/`pad`/`text` stay proven "
      "off DECOY structures in the very same file",
      kind="known_bad")
def t_polarity_marks_row_rests_on_its_own_read():
    """THE REPO'S LAST G-ORPHAN, and the trap it walked into on the way out.

    pluto-rx2-8way-v2's floorplan declares `silk.polarity_marks` — an F.SilkS
    glyph anchored at a named PAD, required on any 2-pad polarized part whose
    reversal no electrical gate can see (the D1 reverse-polarity class, where
    DRC/ERC/parity/netlist are all consistently wrong together). It was a real
    generator key with NO row in the governing contract, and G-ORPHAN failed on
    it: `1 orphan`, exit 1.

    THE TRAP, WHICH IS WHY THIS FIXTURE EXISTS RATHER THAN A BARE PASS.
    `generate_board_generic.py` already reads `"ref"` (`asserts.pad_net[].ref`),
    `"pad"` (`asserts.pad_beyond_edge[].pad`) and `"text"`
    (`silk.captions[].text`) — three DIFFERENT structures in the SAME file. So
    all three new rows score PROVEN whether or not the polarity code exists at
    all: limitation (a) of `schema_reader_audit.py`'s own docstring ("cannot
    prove the read is off THIS structure") arriving as a live temptation, the
    same shape as the `mechanical`/`assembly_coverage.py` collision above. The
    DISCRIMINATING segment is `polarity_marks`, and it occurs exactly once.

    RED-VERIFY, BOTH DIRECTIONS, ON ONE TREE, WITH REAL SHIPPED BYTES — the
    reader is the actual `generate_board_generic.py`, not a model of it.
    Removing the one `.get("polarity_marks")` call is the pre-fix generator as
    far as these rows are concerned.

    MEASURED 2026-07-30 against the LIVE repo, by neutering that call in place:
    `312/315 graded OK, 251 PROVEN, 3 UNREAD`, all three findings reading
    `'polarity_marks' does not appear in any read position at all`, plus the
    floor breach `251 ... below the committed floor of 254` — and NOT ONE of
    them named `ref`, `pad` or `text`, which is the decoy reads doing exactly
    what this fixture claims. Restored: `315/315, 254 PROVEN, 0 orphan`."""
    rows = _shipped_polarity_rows()
    good = REAL_GBG.read_text(encoding="utf-8")
    check(good.count(_POLARITY_READ) == 1,
          f"expected exactly ONE {_POLARITY_READ} in generate_board_generic.py "
          f"— the discriminating read this fixture is built on has moved; "
          f"re-derive it before trusting either half")
    # the pre-fix generator, as far as these three rows are concerned: the one
    # discriminating read gone, every decoy read untouched.
    blind = good.replace(_POLARITY_READ,
                         'self.silk_cfg.get("polarity_marks_ABSENT")')

    # RED — three UNREAD rows, and the finding names the segment that carries
    # the claim rather than the three that do not.
    r = sweep(_floorplan_repo(tmpdir(), rows, blind))
    must_fail(r, "G-ORPHAN against a generator that does not read the block",
              "UNREAD")
    contains(r.out, "'polarity_marks' does not appear in any read position")
    eq(r.out.count("G-ORPHAN UNREAD"), 3, "all three rows go UNREAD together")
    # THE TRAP, ASSERTED: the decoys carried `ref`/`pad`/`text` right through
    # the red run. If any of these ever appears, the discrimination is gone and
    # the rows would be passing on an unrelated structure's read.
    for seg in ("'ref' does not appear", "'pad' does not appear",
                "'text' does not appear"):
        not_contains(r.out, seg)

    # GREEN, the ADJACENT-PROPERTY re-verify: same tree, same source bytes,
    # same rows, the one call restored and nothing else changed.
    r2 = sweep(_floorplan_repo(tmpdir(), rows, good))
    must_pass(r2, "G-ORPHAN with the real generator in place")
    contains(r2.out, "3 PROVEN")
    contains(r2.out, "0 ORPHAN key(s) in source with no row")


@test("the gate obeys its own contract: it names its input and prints an N/M "
      "denominator on every path, including the UNGRADED one")
def t_obeys_its_own_gate_contract():
    r = run([KPY, str(SRA), "--root", str(ROOT)])
    contains(r.out, "input:")
    contains(r.out, "hand-authored source file(s) (denominator)")
    d = tmpdir()
    r2 = sweep(repo(d, "# nothing\n"))
    eq(r2.rc, 2, "the UNGRADED path")
    not_contains(r2.out, "PASS")


if __name__ == "__main__":
    sys.exit(main())
