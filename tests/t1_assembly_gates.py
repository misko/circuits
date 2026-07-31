#!/usr/bin/env python3
"""T1: the ASSEMBLY gates — A-POP (`assembly_coverage.py`) and A-STOCK
(`release_freshness_check.py` check (e)).

PCBA is the deliverable, but until 2026-07-25 nothing in `skills/`, `scripts/`
or `tests/` had ever read a `cpl.csv` back. Of policy_audit's 32 check IDs
exactly one touched a fab-order artifact and it graded only `bom.csv`. So both
defect classes below reached a SEALED release and were found by a human
reading bytes:

  A-POP   cooksense v1.1 ships 13 CPL placement rows whose BOM line carries a
          BLANK LCSC (J_TC + the twelve K_* Standex relays). Its MANIFEST
          declares 12 of them not_assembled — JLC was told to PLACE parts the
          order paperwork says are unassembled, and to source a 13th declared
          nowhere. The interposer v1.0 ships the same class with no
          `not_assembled:` line at all. crow-recorder-central-v2 v1.3 declares
          its PLACED, consigned U1 "not_assembled".
  A-STOCK five sealed releases ship stock evidence whose LAST LINE says FAIL.
          crow-recorder-central-v2 v1.0-v1.3 each record their own CPU
          (C6938291, the XU316 SoC) at LOW_STOCK(0). cooksense v1.1 ships a
          raw `--out` CSV report with ZERO verdict lines, so the gate must not
          be silenceable by simply omitting the verdict.

RED-VERIFICATION, two kinds, both performed:

 1. NEW-GATE variant (A-POP). `assembly_coverage.py` did not exist before this
    commit — at HEAD~ there is no such file, so every A-POP case below fails
    with "no such file" and the gate could not exist. What that cannot prove is
    that a finding comes from the check it names, so every A-POP known-bad ALSO
    carries an INLINE red-verify: re-run with the `--_disable-<family>` hook and
    assert the SAME fixture now passes. A finding that survives its own check
    being neutered is a finding from somewhere else.
 2. GIT-SWAP variant (A-STOCK). check (e) is an addition to an existing gate,
    so it was verified the documented way (tests/README step 3). MEASURED
    2026-07-25: with `git show HEAD:.../release_freshness_check.py` swapped
    back in, `--only=A-STOCK` reports **1 passed, 10 failed**; restored, 11
    passed, 0 failed. The one that survives is `t_stock_sourcing_plan_clears`,
    a clean case that asserts the ABSENCE of a finding — vacuously true when
    the check does not exist, which is exactly why a clean case alone proves
    nothing and every teeth-bearing case here is a known_bad.

Sealed releases are IMMUTABLE and are opened READ-ONLY here. Every scratch
tree is built by COPYING the minimal orderable subset out of them; nothing is
ever written back. Assertions are PROPERTIES — exit codes, finding strings,
named refdes sets — never file bytes: a re-export legitimately reorders CSV
rows.

HERMETICITY, learned the hard way the same day (2026-07-25): a sealed release
is immutable, but `discover()` walks OUT of it to
`projects/<b>/03_src/rules/assembly.yaml`, which is LIVE. Within an hour of
this suite landing, the usb-hub-3s-v3 v1.5 agent authored that project's
assembly.yaml and `t_pop_manifest_prose` flipped from pass to fail with no
code change on either side. Reading immutable bytes is not enough — every
input the checker RESOLVES must be pinned. Tests whose premise is "this
release sealed with no assembly.yaml" now pass `no_asm()`, making that
historical fact explicit instead of inheriting today's working tree.
"""
import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (FAB_SCRIPTS, KPY, ROOT, check, contains,  # noqa: E402
                     eq, main, must_fail, must_pass, not_contains, run, test,
                     tmpdir)

COV = FAB_SCRIPTS / "assembly_coverage.py"
FRESH = FAB_SCRIPTS / "release_freshness_check.py"
RELS = ROOT / "projects"

CROW13 = (RELS / "crow-recorder-central-v2" / "07_releases"
          / "crow-recorder-central-v2-v1.3-2026-07-24")
CROW14 = (RELS / "crow-recorder-central-v2" / "07_releases"
          / "crow-recorder-central-v2-v1.4-2026-07-25")
COOK11 = (RELS / "smc0985-cooksense" / "07_releases"
          / "cooksense-v1.1-2026-07-24")
INTERP = (RELS / "smc0985-cooksense" / "07_releases"
          / "interposer-v1.0-2026-07-24")

# A fully-declared assembly.yaml for the crow-rv2 board: J3-J10 are the
# consign-only RJ45s (LCSC C9900035627, permanently stock 0), JP_INJ/J_DBG are
# bring-up headers, H*/TP* are declared exempt.
CLEAN_ASSEMBLY = """
service: standard
sides: [top]
fiducials: none
build_quantity: 5
not_assembled:
  - refs: [J3, J4, J5, J6, J7, J8, J9, J10]
    reason: not_in_catalog
    evidence: "LCSC C9900035627 is a consign-only placeholder, permanently
               stock=0; 8-attempt fetch 2026-07-23 failed for all eight while
               45 other codes in the same run fetched OK."
    disposition: "hand-soldered at integration; ORDER_README section 3"
  - refs: [JP_INJ, J_DBG]
    reason: dnp_by_design
    evidence: "bring-up headers, deliberately unstuffed on production builds
               (board read 2026-07-24)"
    disposition: "n/a"
exempt_prefixes: [H, TP]
"""

CLEAN_MANIFEST = ("board: demo\nversion: v1.0\n"
                  "not_assembled: J3-J10 (RJHSE-5384 consign/hand-solder), "
                  "JP_INJ, J_DBG (bring-up headers)\n")


def rel_tree(src, *, assembly=None, manifest=None, stock=None,
             stock_name="stock_check.txt"):
    """A scratch `projects/<b>/07_releases/<r>/` holding the MINIMAL orderable
    subset copied out of a SEALED release (read-only source, never written).

    Returns (release_dir, project_root)."""
    d = tmpdir("asm_")
    rel = d / "07_releases" / "demo-v1.0-2026-07-25"
    (rel / "fab").mkdir(parents=True)
    (rel / "source").mkdir()
    (rel / "verification").mkdir()
    shutil.copy(next(iter(sorted((src / "source").glob("*.kicad_pcb")))),
                rel / "source")
    for n in ("bom.csv", "cpl.csv"):
        shutil.copy(src / "fab" / n, rel / "fab")
    (rel / "MANIFEST.txt").write_text(
        CLEAN_MANIFEST if manifest is None else manifest)
    if assembly is not None:
        (d / "03_src" / "rules").mkdir(parents=True)
        (d / "03_src" / "rules" / "assembly.yaml").write_text(assembly)
    if stock is not None:
        (rel / "verification" / stock_name).write_text(stock)
    return rel, d


def board_of(rel):
    return next(iter(sorted((rel / "source").glob("*.kicad_pcb"))))


# Sealed releases are immutable, but `discover()` walks OUT of the release to
# projects/<b>/03_src/rules/assembly.yaml — which is LIVE, mutable, and being
# authored right now by the agents adopting this schema. A test that reads a
# sealed release but resolves its assembly.yaml from the working tree is NOT
# hermetic, and it broke exactly that way within an hour of landing: the
# usb-hub-3s-v3 v1.5 agent created that project's assembly.yaml (2026-07-25
# 10:50) and t_pop_manifest_prose flipped from pass to fail with no code
# change. Every test whose PREMISE is "this release sealed with no
# assembly.yaml" — a historical fact about the seal — must pin that fact
# explicitly instead of inheriting today's working tree.
def no_asm():
    """`--assembly <absent path>`: pins the AS-SEALED condition."""
    return ["--assembly", str(tmpdir("noasm_") / "absent.yaml")]


def set_attr(board, ref, flag="pcbnew.FP_EXCLUDE_FROM_POS_FILES"):
    """Break a good board in EXACTLY ONE way: set one attribute on one part."""
    code = (f"import pcbnew,sys\nb=pcbnew.LoadBoard(sys.argv[1])\n"
            f"fp=b.FindFootprintByReference({ref!r})\n"
            f"assert fp is not None, 'no such refdes {ref}'\n"
            f"fp.SetAttributes(fp.GetAttributes() | {flag})\n"
            f"b.Save(sys.argv[1])\n")
    return must_pass(run([KPY, "-c", code, str(board)]), f"set_attr({ref})")


# ============================================================ A-POP clean
@test("assembly_coverage PASSES a release whose population set is fully "
      "declared (every unpopulated ref has an evidenced entry or a declared "
      "exempt prefix)")
def t_pop_clean():
    rel, _ = rel_tree(CROW13, assembly=CLEAN_ASSEMBLY)
    # A-POS disabled: this case isolates the POPULATION axis. v1.3 shares
    # v1.4's datum defect (J1/J2 emitted at the footprint anchor), which
    # t_pos_datum_off_real_release pins on the sealed bytes instead.
    r = must_pass(run([KPY, COV, rel, "--_disable-datum", "--_disable-smt"]),
                  "fully-declared release")
    contains(r.out, "A-POP: PASS", "verdict")
    contains(r.out, "placement histogram", "per-side histogram is printed")


@test("assembly_coverage's board reader agrees with pcbnew on a real sealed "
      "board — the independence claim (canon M1) is MEASURED, not asserted")
def t_reader_matches_pcbnew():
    """A-POP must not re-ask the exporter's own oracle, so it parses the
    `.kicad_pcb` s-expression directly instead of importing pcbnew. That is
    only safe if the independent parser is CORRECT — an independent-but-wrong
    reader is worse than no gate. Cross-check every footprint on a sealed
    board: refdes, footprint name, orientation, layer, pad-number count and
    the exclude_* attribute flags must all agree, both directions."""
    sys.path.insert(0, str(FAB_SCRIPTS))
    from assembly_coverage import read_footprints
    board = board_of(COOK11)
    mine = {f["ref"]: (f["fp"], round(f["rot"], 3), f["layer"], len(f["pads"]),
                       tuple(sorted(a for a in f["attrs"]
                                    if a.startswith("exclude"))))
            for f in read_footprints(board)}
    probe = (
        "import pcbnew,sys,json\n"
        "b=pcbnew.LoadBoard(sys.argv[1]); o={}\n"
        "for fp in b.GetFootprints():\n"
        "  a=fp.GetAttributes(); fl=[]\n"
        "  if a & pcbnew.FP_EXCLUDE_FROM_POS_FILES: fl.append('exclude_from_pos_files')\n"
        "  if a & pcbnew.FP_EXCLUDE_FROM_BOM: fl.append('exclude_from_bom')\n"
        "  pads={str(p.GetNumber()) for p in fp.Pads() if str(p.GetNumber())}\n"
        "  o[fp.GetReference()]=[str(fp.GetFPID().GetLibItemName()),\n"
        "    round(fp.GetOrientationDegrees(),3),\n"
        "    'F.Cu' if fp.GetLayer()==pcbnew.F_Cu else 'B.Cu', len(pads),\n"
        "    sorted(fl)]\n"
        "print('@@'+json.dumps(o))\n")
    import json
    got = json.loads(must_pass(run([KPY, "-c", probe, str(board)]),
                               "pcbnew probe").out.split("@@", 1)[1].strip())
    theirs = {k: (v[0], v[1], v[2], v[3], tuple(v[4])) for k, v in got.items()}
    check(len(mine) > 100, f"fixture too small to be evidence: {len(mine)}")
    eq(set(mine), set(theirs), "refdes sets (text parse vs pcbnew)")
    bad = sorted(k for k in mine if mine[k] != theirs[k])
    check(not bad, f"{len(bad)} footprint(s) read differently by the "
                   f"pcbnew-free parser: "
                   + "; ".join(f"{k}: {mine[k]} vs {theirs[k]}"
                               for k in bad[:5]))


# ========================================================= A-POP known-bad
@test("assembly_coverage FAILS cooksense v1.1: 13 blank-LCSC BOM refs are ON "
      "the CPL (JLC told to place parts it has no code to source)",
      kind="known_bad")
def t_pop_cooksense_uncoded_on_cpl():
    """THE INCIDENT (sealed 2026-07-24, found by a reviewer 2026-07-25). The
    BOM's two blank-LCSC lines cover J_TC and the twelve K_* Standex reed
    relays; all 13 appear on fab/cpl.csv. The MANIFEST separately declares 12
    of them not_assembled, so the order package contradicts itself and the
    machine instruction wins. Read-only against the SEALED release."""
    r = must_fail(run([KPY, COV, COOK11, *no_asm()]), "cooksense v1.1 A-POP",
                  "UNCODED-ON-CPL")
    for ref in ("J_TC", "K_D1", "K_D2", "K_D3", "K_D4", "K_PRESS", "K_STOP",
                "K_U1", "K_U2", "K_U3", "K_U4", "K_U5", "K_U6"):
        contains(r.out, ref, f"the finding names {ref}")
    contains(r.out, "13 ref(s)", "all thirteen are counted")
    # The MANIFEST separately "declares" 12 of them not_assembled — but its
    # line is PROSE ("... · 16 test points (bare pads)"), so it is reported as
    # ungradeable rather than cross-checked. Accusing specific refs out of
    # prose is a false-positive generator; see t_pop_manifest_prose.
    contains(r.out, "MANIFEST-PROSE",
             "the ungradeable MANIFEST line is its own finding")
    # INLINE RED-VERIFY: neuter ONLY the uncoded check -> that finding vanishes.
    rr = run([KPY, COV, COOK11, *no_asm(), "--_disable-uncoded"])
    not_contains(rr.out, "UNCODED-ON-CPL",
                 "neutered run emits no uncoded finding")


@test("assembly_coverage FAILS the cooksense interposer v1.0: uncoded refs on "
      "the CPL, no assembly.yaml, and no MANIFEST not_assembled line",
      kind="known_bad")
def t_pop_interposer():
    """Sealed 2026-07-24 with every gate green. Its blank-LCSC BOM row's refs
    (J_CN1_JUMPER, J_MEMBRANE) are on the CPL, 24 board footprints are absent
    from the CPL with nothing declaring them, and the disposition was PROSE in
    the README telling a human to delete rows before uploading."""
    r = must_fail(run([KPY, COV, INTERP, *no_asm()]), "interposer v1.0 A-POP",
                  "UNCODED-ON-CPL")
    contains(r.out, "J_CN1_JUMPER", "names the uncoded placed ref")
    contains(r.out, "J_MEMBRANE", "names the uncoded placed ref")
    contains(r.out, "NO-ASSEMBLY-DECL", "no assembly.yaml is itself a finding")
    contains(r.out, "MANIFEST-UNDECLARED",
             "no MANIFEST not_assembled line is a finding")


@test("assembly_coverage FAILS crow-recorder-central-v2 v1.3: its MANIFEST "
      "declares the PLACED, consigned U1 'not_assembled' (consigned means "
      "PLACED — a sourcing class, not a population class)", kind="known_bad")
def t_pop_consigned_declared_unpopulated():
    r = must_fail(run([KPY, COV, CROW13, *no_asm()]), "crow-rv2 v1.3 A-POP",
                  "DECLARED-BUT-PLACED")
    contains(r.out, "U1", "names the consigned part the MANIFEST mis-declares")


@test("assembly_coverage reports a PROSE not_assembled: line as ungradeable "
      "and accuses NO ref from it — prose is a false-positive generator",
      kind="known_bad")
def t_pop_manifest_prose():
    """MEASURED REGRESSION (found 2026-07-25 on usb-hub-3s-v3 v1.4, against
    the FIRST cut of this checker, before it shipped in anger).

    That release's `not_assembled:` line is three numbered prose clauses. A
    naive refdes scrape yields 50 whitespace tokens of which 44 are English
    words ('must', 'be', 'the', 'blade'), and its four REAL refdes —
    C53/C54/R34/R35 — sit in clause (3), which says the OPPOSITE of
    unpopulated: 'remain POPULATE-BY-DEFAULT on BOM/CPL'. The first cut
    accused all four, i.e. the gate would have blocked an in-flight release
    with a finding that was exactly backwards.

    The fix is structural, not another prose heuristic: a GENERATED line
    contains ONLY refdes, so a line carrying any non-refdes token is reported
    as ungradeable and cross-checked against nothing. That is why the contract
    now REQUIRES the line to be generated from assembly.yaml.

    RED-VERIFIED inline below: the four wrongly-accused refs must NOT appear,
    and a machine-readable line on the same board's sibling release still
    produces its DECLARED-BUT-PLACED finding (t_pop_consigned_declared_
    unpopulated), so this did not simply switch the check off."""
    usb = RELS / "usb-hub-3s-v3" / "07_releases" / "v1.4-2026-07-23"
    r = must_fail(run([KPY, COV, usb, *no_asm()]), "prose MANIFEST line", "MANIFEST-PROSE")
    not_contains(r.out, "DECLARED-BUT-PLACED",
                 "no ref may be accused from a prose line")
    for ref in ("C53", "C54", "R34", "R35"):
        not_contains(r.out, ref,
                     f"{ref} is POPULATE-BY-DEFAULT per the same line — "
                     f"accusing it is exactly backwards")
    # the genuinely-unpopulated refs are still caught, by the board-vs-CPL
    # set identity, which needs no prose at all
    contains(r.out, "F1", "the real unpopulated refs are still named")
    contains(r.out, "SW1", "the real unpopulated refs are still named")


@test("assembly_coverage FAILS a declared-but-placed ref from a STRUCTURED "
      "assembly.yaml (the machine-readable path keeps full teeth)",
      kind="known_bad")
def t_pop_declared_but_placed_structured():
    """The MANIFEST path only grades a line that is pure refdes, so the
    structured path is where this class must be pinned unconditionally:
    assembly.yaml declares a ref not_assembled while the CPL places it."""
    rel, _ = rel_tree(CROW13, assembly=CLEAN_ASSEMBLY.replace(
        "  - refs: [JP_INJ, J_DBG]",
        "  - refs: [JP_INJ, J_DBG, U5]"),
        manifest="board: demo\nnot_assembled: J3 J4 J5 J6 J7 J8 J9 J10 "
                 "JP_INJ J_DBG U5\n")
    r = must_fail(run([KPY, COV, rel, "--_disable-datum", "--_disable-smt"]),
                  "declared not_assembled but on CPL", "DECLARED-BUT-PLACED")
    contains(r.out, "U5", "names the placed-yet-declared ref")


@test("assembly_coverage reads a WRAPPED MANIFEST not_assembled: value, so a "
      "continuation line is not silently under-read")
def t_pop_manifest_continuation():
    """crow-recorder-central-v2 v1.3 wraps its value: `JP_INJ + J_DBG` sits on
    the second line. Reading only the first line under-reads the declaration
    and surfaces as a bogus MANIFEST-DRIFT against a correct assembly.yaml."""
    sys.path.insert(0, str(FAB_SCRIPTS))
    from assembly_coverage import manifest_not_assembled
    refs, _raw = manifest_not_assembled(CROW13 / "MANIFEST.txt")
    for ref in ("J3", "J10", "U1", "JP_INJ", "J_DBG"):
        check(ref in refs, f"{ref} missing from the parsed MANIFEST value "
                           f"(continuation line dropped?): {sorted(refs)}")


@test("assembly_coverage FAILS a board broken in EXACTLY ONE way: one extra "
      "part marked exclude_from_pos_files while the shipped CPL still places "
      "it — and names only that ref", kind="known_bad")
def t_pop_synthetic_one_part():
    """Built by breaking the PASSING fixture above in exactly one way
    (harness `edit_board` idiom), so the finding provably reacts to THAT
    defect and not to some unrelated malformation. This is the stale-CPL
    class: the board changed, the CPL did not."""
    rel, _ = rel_tree(CROW13, assembly=CLEAN_ASSEMBLY)
    # A-POS disabled throughout: this case isolates the set-identity axis, and
    # v1.3 carries v1.4's datum defect (J1/J2 at the anchor) independently of
    # the one break introduced below.
    iso = ["--_disable-datum", "--_disable-smt"]
    must_pass(run([KPY, COV, rel, *iso]),
              "the fixture passes BEFORE the break")
    set_attr(board_of(rel), "U5")
    r = must_fail(run([KPY, COV, rel, *iso]), "one extra excluded part",
                  "POS-ATTR-VS-CPL")
    contains(r.out, "U5", "names the broken ref")
    contains(r.out, "1 ref(s)", "exactly one ref is accused")
    for other in ("U1", "U2", "U7", "R1"):
        not_contains(r.out.split("POS-ATTR-VS-CPL")[1], other,
                     f"{other} must not be dragged into the finding")
    # INLINE RED-VERIFY: neuter ONLY the set-identity family -> passes again.
    rr = run([KPY, COV, rel, *iso, "--_disable-setid"])
    check(rr.rc == 0, f"red-verify: with the set-identity checks neutered the "
                      f"one-part fixture must pass, got rc={rr.rc}\n{rr.out}")
    not_contains(rr.out, "POS-ATTR-VS-CPL", "neutered run emits no finding")


@test("assembly_coverage FAILS a not_assembled entry with a reason but NO "
      "evidence (a waiver needs the measurement, not the rationale)",
      kind="known_bad")
def t_pop_entry_needs_evidence():
    """Mirrors t1_release_freshness `t_exception_needs_reason`: canon M4 is
    the same rule wherever an exception is recorded. 'hand-solder' must be a
    sourcing wall you PROVE you hit — the catalog query and its result."""
    asm = CLEAN_ASSEMBLY.replace(
        '''    evidence: "LCSC C9900035627 is a consign-only placeholder, permanently
               stock=0; 8-attempt fetch 2026-07-23 failed for all eight while
               45 other codes in the same run fetched OK."''',
        '    evidence: ""')
    rel, _ = rel_tree(CROW13, assembly=asm)
    r = must_fail(run([KPY, COV, rel]), "evidence-less not_assembled entry",
                  "NO-EVIDENCE")
    contains(r.out, "J3", "names the entry's refs")


@test("assembly_coverage FAILS a reason outside the closed vocabulary",
      kind="known_bad")
def t_pop_bad_reason():
    rel, _ = rel_tree(CROW13, assembly=CLEAN_ASSEMBLY.replace(
        "reason: dnp_by_design", "reason: too_expensive"))
    r = must_fail(run([KPY, COV, rel]), "reason outside the vocabulary",
                  "BAD-REASON")
    contains(r.out, "too_expensive", "names the invented reason")


@test("assembly_coverage FAILS a CONSIGNED part listed as not_assembled "
      "(consigned parts are POPULATED and stay ON the CPL)", kind="known_bad")
def t_pop_consign_as_unpopulated():
    """The crow-recorder-central-v2 v1.3 class, reproduced in the schema: a
    sourcing class written into the population set. Both spellings must
    bite — `reason: consign`, and the same refs appearing in `consigned:`."""
    rel, _ = rel_tree(CROW13, assembly=CLEAN_ASSEMBLY.replace(
        "reason: not_in_catalog", "reason: consign"))
    r = must_fail(run([KPY, COV, rel]), "reason: consign in not_assembled",
                  "CONSIGN-AS-UNPOPULATED")
    rel2, _ = rel_tree(CROW13, assembly=CLEAN_ASSEMBLY + """
consigned:
  - refs: [J3]
    lcsc: C9900035627
    msl: "MSL 1 (THT jack, not moisture sensitive)"
    evidence: "supplied from stock on hand, 8 pcs, 2026-07-24"
    disposition: "ship with the order; JLC places"
""")
    r2 = must_fail(run([KPY, COV, rel2]), "ref in BOTH consigned and "
                                          "not_assembled",
                   "CONSIGN-AS-UNPOPULATED")
    contains(r2.out, "J3", "names the doubly-classed ref")


@test("assembly_coverage FAILS a declared-unpopulated ref that does NOT carry "
      "exclude_from_pos_files on the board (the next export puts it back)",
      kind="known_bad")
def t_pop_declared_not_excluded():
    rel, _ = rel_tree(CROW13, assembly=CLEAN_ASSEMBLY.replace(
        "exempt_prefixes: [H, TP]",
        """  - refs: [U5]
    reason: dnp_by_design
    evidence: "declared unpopulated on 2026-07-25 for this fixture, but the
               board footprint was never marked exclude_from_pos_files"
    disposition: "n/a"
exempt_prefixes: [H, TP]"""))
    r = must_fail(run([KPY, COV, rel]), "declared but not excluded",
                  "DECLARED-NOT-EXCLUDED")
    contains(r.out, "U5", "names the ref")


@test("assembly_coverage FAILS when the MANIFEST not_assembled set disagrees "
      "with assembly.yaml (the MANIFEST line is GENERATED, never re-typed)",
      kind="known_bad")
def t_pop_manifest_drift():
    """The cooksense v1.1 root cause: two hand-written homes for the same
    fact, which drifted and shipped."""
    rel, _ = rel_tree(CROW13, assembly=CLEAN_ASSEMBLY,
                      manifest="board: demo\nnot_assembled: J3-J10 (RJ45)\n")
    r = must_fail(run([KPY, COV, rel]), "MANIFEST/assembly.yaml drift",
                  "MANIFEST-DRIFT")
    contains(r.out, "JP_INJ", "names what the MANIFEST forgot")


# ============================================================ A-POS cases
# The known-bad fixture is a REAL SEALED RELEASE, not a synthetic one:
# crow-recorder-central-v2 v1.4 shipped its only USB-C 1.3025mm off its own
# pads. Every gate that release ran was green — DRC 0/0/0, schematic parity 0,
# A-POP, A-ROT, two red-team lenses — because nothing in the fleet had ever
# compared a CPL COORDINATE to anything at all. These bytes are immutable, so
# this fixture cannot rot.

@test("A-POS catches the v1.4 USB-C blocker: a CPL row emitted at KiCad's "
      "footprint ANCHOR instead of JLC's pad-array placement datum")
def t_pos_datum_off_real_release():
    r = must_fail(run([KPY, COV, CROW14, *no_asm()]), "v1.4 A-POS",
                  "CPL-DATUM-OFF")
    contains(r.out, "J2", "names the USB-C — the part that cannot seat")
    contains(r.out, "1.3025", "reports the MEASURED offset, not a verdict")
    contains(r.out, "FOOTPRINT ANCHOR",
             "diagnoses WHICH wrong datum was used, so the fix is obvious")
    # INLINE RED-VERIFY: neuter only this family; the same bytes must pass it.
    # A finding that survives its own check being disabled came from elsewhere.
    rr = run([KPY, COV, CROW14, *no_asm(), "--_disable-datum"])
    check("CPL-DATUM-OFF" not in rr.out,
          "red-verify: --_disable-datum must silence exactly this finding")


@test("A-POS grades EVERY placed row's coordinate, and reports the worst "
      "residual — a datum gate that only prints failures cannot be trusted "
      "when it prints nothing")
def t_pos_datum_reports_worst():
    r = run([KPY, COV, CROW14, *no_asm()])
    contains(r.out, "A-POS datum:", "the measurement is always printed")
    contains(r.out, "177 CPL row(s) graded",
             "all 177 shipped rows were graded, not a sampled subset")


@test("A-POS catches a true THT part on the CPL of an SMT-only order (v1.4 "
      "J1, the board's ONLY power inlet), and does NOT flag pin-in-paste")
def t_pos_not_smt_placeable():
    rel, _ = rel_tree(CROW14, assembly=CLEAN_ASSEMBLY)
    r = must_fail(run([KPY, COV, rel, "--_disable-datum"]),
                  "v1.4 J1 process class", "CPL-NOT-SMT-PLACEABLE")
    contains(r.out, "J1", "names the barrel jack")
    # J2 also has 4 DRILLED pads — but they carry F.Paste, so it is legitimate
    # intrusive reflow. The discriminator must be PASTE, never the
    # `through_hole` attribute, or this check would condemn every pin-in-paste
    # connector on the fleet.
    smt = [ln for ln in r.out.splitlines() if "CPL-NOT-SMT-PLACEABLE" in ln]
    check(not any(" J2 " in ln for ln in smt),
          "J2 (pin-in-paste, F.Paste on all 4 drilled pads) must NOT be flagged")
    rr = run([KPY, COV, rel, "--_disable-smt"])
    check("CPL-NOT-SMT-PLACEABLE" not in rr.out,
          "red-verify: --_disable-smt must silence exactly this finding")


@test("A-POS: a DECLARED-AND-EVIDENCED bought THT process exempts the refs it "
      "NAMES — because taking a paid-for connector off the CPL is the wrong fix")
def t_pos_tht_declared_process_exempts():
    """usb-hub-3s-v3 v1.6: the board PAYS for JLC's through-hole line, so J1-J4
    belong ON the CPL. Before this, `service:` was interpolated into the message
    and never decided on, so the only way to pass was to remove the part — which
    would have hand-soldered a connector the customer had already bought."""
    asm = CLEAN_ASSEMBLY.replace("service: standard",
                                 "service: standard SMT + THROUGH-HOLE assembly") + """
through_hole:
  process: "JLCPCB through-hole assembly, ORDERED"
  refs: [J1]
  evidence: "measured hole census 2026-07-26: J1 has 4 plated holes, none pasted"
"""
    rel, _ = rel_tree(CROW14, assembly=asm)
    r = run([KPY, COV, rel, "--_disable-datum"])
    smt = [ln for ln in r.out.splitlines() if "CPL-NOT-SMT-PLACEABLE" in ln]
    check(not any(" J1 " in ln for ln in smt),
          "J1 is NAMED in an evidenced through_hole declaration -> exempt, "
          f"got: {smt}")


@test("A-POS: through_hole exempts ONLY the refs it names, and an incomplete "
      "declaration exempts NOTHING — prose cannot buy a process")
def t_pos_tht_declaration_is_scoped_and_complete():
    """The known-bad half. Three ways a declaration must fail to help:
    (a) a ref left OFF the list is still caught — that IS the
        crow-recorder-central-v2 v1.4 case, whose assembly.yaml asserted in prose
        that its THT parts were off the CPL while J1 sat on it;
    (b) `refs:` with no `process:`/`evidence:` is an assertion, not a purchase;
    (c) an EMPTY declaration exempts nothing at all."""
    # (a) declaration names a DIFFERENT ref -> J1 still fails
    asm_other = CLEAN_ASSEMBLY + """
through_hole:
  process: "JLCPCB through-hole assembly, ORDERED"
  refs: [J99]
  evidence: "measured 2026-07-26"
"""
    rel_a, _ = rel_tree(CROW14, assembly=asm_other)
    must_fail(run([KPY, COV, rel_a, "--_disable-datum"]),
              "a bought process must not exempt a ref it does not name",
              "CPL-NOT-SMT-PLACEABLE")
    # (b) refs but no process/evidence -> exempts nothing AND is called out
    asm_bare = CLEAN_ASSEMBLY + """
through_hole:
  refs: [J1]
"""
    rel_b, _ = rel_tree(CROW14, assembly=asm_bare)
    rb = must_fail(run([KPY, COV, rel_b, "--_disable-datum"]),
                   "an unevidenced through_hole declaration",
                   "CPL-NOT-SMT-PLACEABLE")
    contains(rb.out, "THT-DECL-INCOMPLETE",
             "the incomplete declaration is named, not silently ignored")
    contains(rb.out, "process", "says WHICH keys are missing")
    # (c) empty declaration -> exempts nothing
    rel_c, _ = rel_tree(CROW14, assembly=CLEAN_ASSEMBLY + "\nthrough_hole: {}\n")
    must_fail(run([KPY, COV, rel_c, "--_disable-datum"]),
              "an empty through_hole block", "CPL-NOT-SMT-PLACEABLE")


@test("A-POS passes a CPL whose coordinates ARE the pad-array datum — the "
      "gate has to be satisfiable, and 175 of v1.4's 177 rows already were")
def t_pos_datum_clean_rows():
    r = run([KPY, COV, CROW14, *no_asm()])
    offenders = [ln for ln in r.out.splitlines() if "CPL-DATUM-OFF" in ln]
    check(len(offenders) == 2,
          f"exactly 2 of 177 rows are off-datum (J1, J2); got {len(offenders)}")
    check(all(" J1 " in ln or " J2 " in ln for ln in offenders),
          "the two offenders are the two connectors, not a systematic shift")


@test("the exporter's assembly.yaml path removes a declared ref from the CPL "
      "— the mechanism that lets a SEALED board drop a placement")
def t_declared_refs_leave_the_cpl():
    """crow-recorder-central-v2 v1.5's whole architecture rests on this: the
    board is sealed and its gerbers are byte-identical to v1.4, so
    `exclude_from_pos_files` could not be set without regenerating (81626
    diff lines of UUID churn). The DECLARATION had to become a mechanism."""
    import re as _re
    src = (FAB_SCRIPTS / "export_jlc_package.py").read_text()
    check("declared_unpopulated" in src,
          "the exporter reads 03_src/rules/assembly.yaml")
    check(_re.search(r"if ref in _declared_np:\s*\n\s*_dropped_by_decl",
                     src) is not None,
          "a declared ref is dropped BEFORE the CPL row is built")
    # It must only ever REMOVE. A path that could ADD a row would make
    # assembly.yaml able to place parts that are not on the board.
    check(src.count("_declared_np") == 3,
          "the declaration is consulted exactly once, on the drop path")


@test("`on_bom: false` drops a ref from the ASSEMBLY BOM, and is NOT inferred "
      "from `reason:` — two boards say user_supplied and want opposite answers")
def t_on_bom_false_is_its_own_key():
    """crow-mic-pod-v2 v1.1 removed MK1 and J1 from its BOM because both carry
    an unmatchable code and neither is on the CPL — "the upload stalls at JLC's
    BOM/CPL matcher". That removal was made by EDITING `fab/bom.csv`, so the
    sealed v1.1/v1.2 BOM was NOT reproducible from source (canon M3):
    re-running the exporter on the same board puts both rows straight back,
    which is exactly what happened while staging v1.3 (2026-07-27). `on_bom:
    false` gives the decision a machine-readable home in the file that already
    owns "who gets placed, and why not".

    THE KEY EXISTS BECAUSE `reason:` CANNOT CARRY IT. usb-hub-3s-v3 declares F1
    `user_supplied` and F1 IS on its BOM — the fuse HOLDER (C5249699, stock
    1213) ships with the order and only the fuse ELEMENT is bought locally.
    crow-mic-pod-v2 declares MK1 and J1 `user_supplied` and both must LEAVE the
    BOM. Same reason code, opposite answer, so a rule inferred from `reason:`
    would have silently dropped a real fuse holder from a real order.

    Asserted here as a SOURCE property (the drop happens before the row is
    built, it can only ever REMOVE, and a contradiction with the CPL BLOCKS)
    plus the two live declarations, in the same shape as
    t_declared_refs_leave_the_cpl above. The end-to-end proof that the
    regenerated BOM equals the sealed row set is crow-mic-pod-v2 v1.3's own
    verification/replot_identity.txt.

    RED-VERIFIED 2026-07-27: with `git show HEAD:...export_jlc_package.py`
    swapped back in, every check below fails — the exporter has no
    `declared_off_bom` at all and mic-pod's BOM comes out 17 rows, not 15."""
    import re as _re
    import yaml as _yaml
    src = (FAB_SCRIPTS / "export_jlc_package.py").read_text()
    check("declared_off_bom" in src,
          "the exporter reads the `on_bom:` declaration")
    check(_re.search(r"if ref in _off_bom:\s*\n\s*_dropped_off_bom",
                     src) is not None,
          "an off-BOM ref is dropped BEFORE its group row is built")
    check("A-POP BLOCKED" in src and "_contradiction" in src,
          "a ref that is both `on_bom: false` and ON THE CPL must BLOCK — "
          "that is the dangerous inversion, JLC placing a part with no line "
          "to source it from")

    def off_bom(proj):
        d = _yaml.safe_load(
            (ROOT / "projects" / proj / "03_src/rules/assembly.yaml").read_text())
        return {r for e in (d.get("not_assembled") or [])
                if e.get("on_bom") is False for r in (e.get("refs") or [])}

    eq(off_bom("crow-mic-pod-v2"), {"MK1", "J1"},
       "crow-mic-pod-v2 declares exactly the two rows v1.1 removed by hand")
    eq(off_bom("usb-hub-3s-v3"), set(),
       "usb-hub-3s-v3's F1 is user_supplied AND stays on the BOM — if this "
       "set is ever non-empty, a fuse holder is being dropped from an order")


@test("A-POP's DECLARED-NOT-EXCLUDED still FAILS an undeferred ref, and is "
      "cleared ONLY by a dated board_attr_plan: entry")
def t_pop_board_attr_plan_defer():
    asm = CLEAN_ASSEMBLY.replace("exempt_prefixes: [H, TP]", """\
  - refs: [R_bg1]
    reason: dnp_by_design
    evidence: "declared 2026-07-25 for this test fixture, no board attribute"
    disposition: "n/a"
exempt_prefixes: [H, TP]""")
    rel, _ = rel_tree(CROW13, assembly=asm)
    must_fail(run([KPY, COV, rel, "--_disable-datum", "--_disable-smt"]),
              "declared ref with no board attribute", "DECLARED-NOT-EXCLUDED")
    # Now defer it the ONLY sanctioned way. The decision is not weakened: the
    # ref must still be off the CPL, which DECLARED-BUT-PLACED enforces and
    # which is NOT deferrable.
    deferred = asm + """
board_attr_plan:
  - refs: [R_bg1]
    measured_on: 2026-07-25
    plan: "floorplan.yaml carries the pattern; lands at the next board revision"
"""
    rel2, _ = rel_tree(CROW13, assembly=deferred)
    r = run([KPY, COV, rel2, "--_disable-datum", "--_disable-smt"])
    check("DECLARED-NOT-EXCLUDED" not in r.out,
          "a dated board_attr_plan clears the finding")
    contains(r.out, "DEFERRED-BOARD-ATTR", "and says so out loud, as a note")
    # A defer with no measurement is not a defer.
    bare = asm + "\nboard_attr_plan:\n  - refs: [R_bg1]\n    plan: soon\n"
    rel3, _ = rel_tree(CROW13, assembly=bare)
    must_fail(run([KPY, COV, rel3, "--_disable-datum", "--_disable-smt"]),
              "undated/unevidenced defer", "DECLARED-NOT-EXCLUDED")


# ========================================================== A-STOCK cases
PASS_STOCK = """49 BOM lines: 47 with LCSC, 2 without

  OK               C6938291   x1   XU316-1024                     expand stock=900
  OK               C9900035627 x8   RJHSE-5384                     expand stock=800

PASS: 0 coded lines with problems; 2 lines still uncoded
"""


def stock_all_ok(rel_src, *, verdict="PASS", stock=99999):
    """Synthesize evidence covering EVERY coded+placed line of a real release
    so the A-STOCK clean cases isolate one axis at a time."""
    placed = {r["Designator"].strip()
              for r in csv.DictReader((rel_src / "fab" / "cpl.csv").open())}
    lines = ["49 BOM lines: 47 with LCSC, 2 without", ""]
    seen = set()
    for row in csv.DictReader((rel_src / "fab" / "bom.csv").open()):
        code = (row.get("LCSC") or "").strip()
        if not code or code in seen:
            continue
        if not any(d.strip() in placed for d in row["Designator"].split(",")):
            continue
        seen.add(code)
        lines.append(f"  OK               {code:10} x1   part "
                     f"                          expand stock={stock}")
    lines += ["", f"{verdict}: 0 coded lines with problems; 2 lines still "
                  f"uncoded", ""]
    return "\n".join(lines)


@test("release_freshness A-STOCK: a release with no fab BOM/CPL says so out "
      "loud rather than silently skipping")
def t_stock_nothing_to_grade():
    """A gate that quietly grades nothing is the NO-CAD bug again. The
    synthetic releases in t1_release_freshness carry no BOM/CPL at all, and
    that must be a VISIBLE note, not an invisible pass."""
    d = tmpdir("stk_")
    rel = d / "07_releases" / "v1.0-2026-07-25"
    (rel / "fab").mkdir(parents=True)
    (rel / "verification").mkdir()
    (rel / "fab" / "demo_gerbers.zip").write_bytes(b"gerber")
    (rel / "MANIFEST.txt").write_text("board: demo\n")
    (rel / "ORDER_README.md").write_text("# ORDER README\n\nFinal.\n")
    (rel / "verification" / "policy_audit.md").write_text(
        "| ID | Grade |\n|---|---|\n| M-BOM | PASS |\n\nSummary: FAIL=0\n")
    r = must_pass(run([KPY, FRESH, rel]), "release with nothing to source")
    contains(r.out, "no coded, placed line to grade",
             "the empty case is announced, not silent")


@test("release_freshness A-STOCK PASSES stock evidence with a parseable PASS "
      "verdict covering every coded, placed line")
def t_stock_clean():
    rel, _ = rel_tree(CROW13, assembly=CLEAN_ASSEMBLY,
                      stock=stock_all_ok(CROW13))
    (rel / "ORDER_README.md").write_text("# ORDER README\n\nFinal.\n")
    (rel / "verification" / "policy_audit.md").write_text(
        "| ID | Grade |\n|---|---|\n| M-BOM | PASS |\n\nSummary: FAIL=0\n")
    r = run([KPY, FRESH, rel])
    not_contains(r.out, "STOCK-", "clean stock evidence raises no finding")
    contains(r.out, "verdict=PASS", "the verdict was actually parsed")


@test("release_freshness A-STOCK: a sourcing_plan entry with the MEASURED "
      "stock, its date AND its order_status clears an otherwise-blocking line")
def t_stock_sourcing_plan_clears():
    """The ONE legitimate way past a non-OK line — and it costs a number, a
    date and a CLASSIFICATION, not a sentence.

    CHANGED 2026-07-30 (canon A-BUY — NOT `A-ORDER`, which has meant
    `rules_audit`'s generate-rules-runs-LAST check since 2026-07-17; the new
    check was renamed before landing and this docstring carried the pre-rename
    name). This fixture used to omit `order_status:` and still pass, because a
    plan entry SILENTLY CLEARED its line whatever its own measured number said.
    That silence is the defect A-BUY closes: a plan measuring 0 against a need
    of 5 now has to say which of PLANNED (the catalog is irrelevant to this
    line — consignment, as here) or BLOCKED (it cannot be bought as sealed) it
    means.

    NB this case asserts the ABSENCE of a finding, so its teeth live in the
    known-bads: `t_stock_plan_incomplete` (no measurement) and
    `t_stock_verdict_fail` (no plan at all) here, plus A-BUY's own 11
    known-bads in `tests/t1_release_freshness.py` — of which
    `t_order_plan_unclassified` is exactly this tree minus the
    `order_status:` line.

    RED-VERIFIED on REAL BYTES, 2026-07-30, in the direction that matters:
    `projects/crow-recorder-central-v2/03_src/rules/assembly.yaml` is the live
    source for the sealed v1.7 release and carries the same consigned C6938291
    shortfall. Graded WITH `order_status: PLANNED` it prints
    `SOURCING: PLANNED-1`; with that ONE line reverted to its pre-change form
    it prints `SOURCING: UNGRADED + FAIL (1 finding(s))` and
    `ORDER-PLAN-UNCLASSIFIED: ... measures stock 0 against 1 x 5 = 5`."""
    asm = CLEAN_ASSEMBLY + """
sourcing_plan:
  - lcsc: C6938291
    measured_stock: 0
    measured_on: 2026-07-24
    order_status: PLANNED
    plan: "consigned from stock on hand (5 pcs); JLC stock irrelevant here"
"""
    rel, _ = rel_tree(CROW13, assembly=asm,
                      stock=stock_all_ok(CROW13, verdict="FAIL").replace(
                          "  OK               C6938291   x1",
                          "  LOW_STOCK(0)     C6938291   x1"))
    (rel / "ORDER_README.md").write_text("# ORDER README\n\nFinal.\n")
    (rel / "verification" / "policy_audit.md").write_text(
        "| ID | Grade |\n|---|---|\n| M-BOM | PASS |\n\nSummary: FAIL=0\n")
    r = run([KPY, FRESH, rel])
    not_contains(r.out, "STOCK-VERDICT-FAIL",
                 "a planned line does not accuse the release")
    not_contains(r.out, "STOCK-INSUFFICIENT", "the plan covers the line")
    contains(r.out, "SOURCING: PLANNED-1",
             "a consigned shortfall is PLANNED, and it is stated out loud "
             "rather than vanishing into the YAML")


@test("release_freshness A-STOCK FAILS crow-recorder-central-v2 v1.3: its "
      "shipped stock evidence ends in FAIL with the board's own CPU at "
      "stock 0", kind="known_bad")
def t_stock_verdict_fail():
    """THE INCIDENT. verification/stock_check.txt's last line reads
    'FAIL: 2 coded lines with problems' and line 41 reads
    'LOW_STOCK(0) C6938291' — the XU316 SoC this board is built around, and
    the part it cannot be assembled without. Four sealed releases of this
    board ship that same evidence. Read-only against the SEALED release."""
    r = must_fail(run([KPY, FRESH, CROW13, *no_asm()]), "crow-rv2 v1.3 A-STOCK",
                  "STOCK-VERDICT-FAIL")
    contains(r.out, "C6938291", "names the board's own CPU")
    contains(r.out, "STOCK-INSUFFICIENT",
             "the per-line grade fires independently of the verdict line")
    # RED-VERIFY: neuter ONLY check (e) -> this release passes freshness,
    # proving the finding came from A-STOCK and from nothing else.
    rr = run([KPY, FRESH, CROW13, *no_asm(), "--_disable-stock"])
    check(rr.rc == 0,
          f"red-verify: with check (e) neutered crow-rv2 v1.3 must pass "
          f"freshness, got rc={rr.rc}\n{rr.out[-1500:]}")
    not_contains(rr.out, "STOCK-", "neutered run emits no stock finding")


@test("release_freshness A-STOCK FAILS cooksense v1.1 with a DISTINCT "
      "no-parseable-verdict finding (evidence with the verdict missing is "
      "unverified sourcing, never a pass)", kind="known_bad")
def t_stock_no_verdict():
    """cooksense v1.1 ships jlc_stock_check's `--out` CSV REPORT as
    verification/stock_check.txt: 50 graded rows and ZERO PASS:/FAIL: lines.
    The finding must be its own class — if 'no verdict' collapsed into 'not
    checked' or, worse, into silence, the gate could be silenced by deleting
    one line."""
    r = must_fail(run([KPY, FRESH, COOK11, *no_asm()]), "cooksense v1.1 A-STOCK",
                  "STOCK-NO-VERDICT")
    not_contains(r.out, "STOCK-VERDICT-FAIL",
                 "a missing verdict is NOT the same finding as a FAIL verdict")
    rr = run([KPY, FRESH, COOK11, *no_asm(), "--_disable-stock"])
    not_contains(rr.out, "STOCK-", "neutered run emits no stock finding")


@test("release_freshness A-STOCK: DELETING the verdict line from PASSING "
      "evidence FAILS — the gate cannot be silenced by omission",
      kind="known_bad")
def t_stock_verdict_deleted_still_fails():
    """The adversarial case, built by breaking the passing fixture in exactly
    one way: take evidence the gate accepts and remove ONLY its verdict line.
    'Missing verdict' must be a FAIL, not a skip — otherwise every gate above
    is optional."""
    ev = stock_all_ok(CROW13)
    rel, _ = rel_tree(CROW13, assembly=CLEAN_ASSEMBLY, stock=ev)
    (rel / "ORDER_README.md").write_text("# ORDER README\n\nFinal.\n")
    (rel / "verification" / "policy_audit.md").write_text(
        "| ID | Grade |\n|---|---|\n| M-BOM | PASS |\n\nSummary: FAIL=0\n")
    must_pass(run([KPY, FRESH, rel]), "the fixture passes BEFORE the break")
    stripped = "\n".join(l for l in ev.splitlines()
                         if not l.startswith(("PASS:", "FAIL:")))
    (rel / "verification" / "stock_check.txt").write_text(stripped)
    r = must_fail(run([KPY, FRESH, rel]), "evidence with the verdict deleted",
                  "STOCK-NO-VERDICT")
    rr = run([KPY, FRESH, rel, "--_disable-stock"])
    check(rr.rc == 0, f"red-verify: with check (e) neutered the "
                      f"verdict-deleted fixture must pass, got rc={rr.rc}")


@test("release_freshness A-STOCK FAILS a coded, PLACED line with no stock "
      "evidence line at all (assumed, never sourced)", kind="known_bad")
def t_stock_ungraded_line():
    ev = "\n".join(l for l in stock_all_ok(CROW13).splitlines()
                   if "C6938291" not in l)
    rel, _ = rel_tree(CROW13, assembly=CLEAN_ASSEMBLY, stock=ev)
    (rel / "ORDER_README.md").write_text("# ORDER README\n\nFinal.\n")
    (rel / "verification" / "policy_audit.md").write_text(
        "| ID | Grade |\n|---|---|\n| M-BOM | PASS |\n\nSummary: FAIL=0\n")
    r = must_fail(run([KPY, FRESH, rel]), "coded placed line with no evidence",
                  "STOCK-UNGRADED")
    contains(r.out, "C6938291", "names the ungraded line")


@test("release_freshness A-STOCK FAILS when a release ships NO stock evidence "
      "file at all", kind="known_bad")
def t_stock_no_evidence():
    rel, _ = rel_tree(CROW13, assembly=CLEAN_ASSEMBLY)
    (rel / "ORDER_README.md").write_text("# ORDER README\n\nFinal.\n")
    (rel / "verification" / "policy_audit.md").write_text(
        "| ID | Grade |\n|---|---|\n| M-BOM | PASS |\n\nSummary: FAIL=0\n")
    must_fail(run([KPY, FRESH, rel]), "release with no stock evidence",
              "STOCK-NO-EVIDENCE")


@test("release_freshness A-STOCK reads the jlc_stock_check --json sidecar and "
      "honours its EXPLICIT verdict field")
def t_stock_json_sidecar():
    """The fleet ships three incompatible text formats; `--json` is the one
    shape with a verdict that never has to be inferred from the absence of a
    FAIL line."""
    import json
    placed = {r["Designator"].strip()
              for r in csv.DictReader((CROW13 / "fab" / "cpl.csv").open())}
    lines, seen = [], set()
    for row in csv.DictReader((CROW13 / "fab" / "bom.csv").open()):
        code = (row.get("LCSC") or "").strip()
        if code and code not in seen and any(
                d.strip() in placed for d in row["Designator"].split(",")):
            seen.add(code)
            lines.append({"lcsc": code, "qty": 1, "status": "OK",
                          "stock": 50000})
    rel, _ = rel_tree(CROW13, assembly=CLEAN_ASSEMBLY)
    (rel / "verification" / "stock_check.json").write_text(json.dumps(
        {"verdict": "PASS", "failures": 0, "lines": lines}))
    (rel / "ORDER_README.md").write_text("# ORDER README\n\nFinal.\n")
    (rel / "verification" / "policy_audit.md").write_text(
        "| ID | Grade |\n|---|---|\n| M-BOM | PASS |\n\nSummary: FAIL=0\n")
    r = run([KPY, FRESH, rel])
    contains(r.out, "stock_check.json", "the sidecar is preferred")
    not_contains(r.out, "STOCK-", "a clean sidecar raises no finding")


@test("jlc_stock_check --json WRITES a sidecar that release_freshness READS: "
      "the writer and the reader agree on the shape")
def t_stock_json_roundtrip():
    """The reader tests above hand-build the sidecar, which would keep passing
    if the WRITER emitted a different shape — checker and checked sharing a
    method by accident (canon M1). Round-trip it through the real writer.

    Hermetic: a BOM whose lines are all UNCODED makes zero `query()` calls, so
    the network is never touched (`--search-missing` is deliberately off).

    UPDATED 2026-07-27 (G-COVER). This used to assert the all-uncoded BOM
    exited 0 with `"verdict": "PASS"`. That was the defect: every line lacking
    an LCSC means stock was queried for NONE of them, so the sidecar declared
    PASS over a ZERO denominator — and release_freshness A-STOCK READS that
    field, so a zero-coverage run could clear the release gate. The round-trip
    property this test exists for is unchanged and still asserted; what moved
    is the verdict such a run is entitled to."""
    import json
    d = tmpdir("stkw_")
    bom = d / "bom_jlc.csv"
    bom.write_text("Comment,Designator,Footprint,MPN,LCSC\n"
                   "10k,R1,R_0402_1005Metric,,\n")
    out = d / "stock_check.json"
    r = must_fail(run([KPY, FAB_SCRIPTS / "jlc_stock_check.py", bom,
                       "--json", out]),
                  "jlc_stock_check --json (all-uncoded BOM grades NOTHING)",
                  "0/1 BOM lines graded")
    contains(r.out, "FAIL:", "the writer still prints its verdict line")
    doc = json.loads(out.read_text())
    # the SIDECAR and the EXIT CODE must not disagree — the sidecar is what the
    # release gate reads, so a PASS here beside an exit 1 would be the worse
    # half of the defect
    check(doc.get("verdict") == "FAIL",
          f"the sidecar must agree with the exit code, got "
          f"{doc.get('verdict')!r} beside rc={r.rc}")
    check(doc.get("graded_lines") == 0 and doc.get("total_lines") == 1,
          f"the sidecar must carry the DENOMINATOR so a reader of the JSON "
          f"alone can see a zero-coverage run: got graded_lines="
          f"{doc.get('graded_lines')!r} total_lines={doc.get('total_lines')!r}")
    check(doc.get("zero_coverage"),
          "the sidecar must SAY why nothing was graded, not leave it inferable")
    check("lines" in doc, "the sidecar must carry a per-line list")
    # and the READER must accept exactly what the WRITER produced
    rel, _ = rel_tree(CROW13, assembly=CLEAN_ASSEMBLY)
    shutil.copy(out, rel / "verification" / "stock_check.json")
    (rel / "ORDER_README.md").write_text("# ORDER README\n\nFinal.\n")
    (rel / "verification" / "policy_audit.md").write_text(
        "| ID | Grade |\n|---|---|\n| M-BOM | PASS |\n\nSummary: FAIL=0\n")
    rr = run([KPY, FRESH, rel])
    not_contains(rr.out, "STOCK-NO-VERDICT",
                 "the reader rejected the real writer's own verdict field — "
                 "writer and reader disagree on the sidecar shape")


@test("release_freshness A-STOCK FAILS a --json sidecar whose verdict field "
      "is absent (the sidecar gets no easier ride than the text)",
      kind="known_bad")
def t_stock_json_no_verdict():
    import json
    rel, _ = rel_tree(CROW13, assembly=CLEAN_ASSEMBLY)
    (rel / "verification" / "stock_check.json").write_text(
        json.dumps({"failures": 0, "lines": []}))
    (rel / "ORDER_README.md").write_text("# ORDER README\n\nFinal.\n")
    (rel / "verification" / "policy_audit.md").write_text(
        "| ID | Grade |\n|---|---|\n| M-BOM | PASS |\n\nSummary: FAIL=0\n")
    must_fail(run([KPY, FRESH, rel]), "verdict-less json sidecar",
              "STOCK-NO-VERDICT")


@test("release_freshness A-STOCK FAILS a sourcing_plan entry missing its "
      "measured number or date (a plan without the measurement is a hope)",
      kind="known_bad")
def t_stock_plan_incomplete():
    asm = CLEAN_ASSEMBLY + """
sourcing_plan:
  - lcsc: C6938291
    plan: "we'll sort it out at order time"
"""
    rel, _ = rel_tree(CROW13, assembly=asm, stock=stock_all_ok(CROW13))
    (rel / "ORDER_README.md").write_text("# ORDER README\n\nFinal.\n")
    (rel / "verification" / "policy_audit.md").write_text(
        "| ID | Grade |\n|---|---|\n| M-BOM | PASS |\n\nSummary: FAIL=0\n")
    r = must_fail(run([KPY, FRESH, rel]), "incomplete sourcing plan",
                  "STOCK-PLAN-INCOMPLETE")
    contains(r.out, "C6938291", "names the incomplete entry")


# --------------------------------------------------------------- A-STOCK scope
@test("the stock sidecar states what its PASS does NOT cover")
def t_stock_sidecar_declares_its_own_limit():
    """Canon M-QUOTE, added 2026-07-27 after a measured miss.

    `jlc_stock_check.py` grades `stockCount`, which is LCSC CATALOG stock. JLC's
    assembly uploader allocates from a DIFFERENT pool. usb-hub v1.11's
    predecessor shipped this very sidecar reading

        C25744 ... "status": "OK", "stock": 291      "verdict": "PASS"

    and JLC refused that exact line the same day with "10 shortfall", because
    LCSC held 291 and JLC's assembly warehouse held none. The gate was not
    wrong about the number it measured; it was silent about which number that
    was, and `release_freshness` A-STOCK READS this file.

    So the PROPERTY is not "the verdict is correct" -- it is that the verdict
    CARRIES ITS OWN SCOPE, because a downstream reader has no other way to know.
    A gate that reports a true fact about the wrong pool, without saying which
    pool, is the adjacent-property error with a machine-readable interface.

    Runs OFFLINE: the sidecar is written before the zero-coverage exit, so an
    all-uncoded BOM exercises the writer with no network at all.
    """
    with tmpdir() as d:
        bom = Path(str(d)) / "bom.csv"
        bom.write_text("Comment,Designator,Footprint,LCSC\n"
                       "10k,R1,R_0402_1005Metric,\n"
                       "100nF,C1,C_0402_1005Metric,\n")
        out = Path(str(d)) / "stock.json"
        run([KPY, FAB_SCRIPTS / "jlc_stock_check.py", str(bom),
             "--json", str(out)])
        check(out.is_file(), "the sidecar must be written even on a run that "
                             "grades nothing -- that is the zero-coverage case "
                             "a reader most needs to see")
        j = json.loads(out.read_text())
        eq(j.get("stock_source"), "lcsc_catalog_stockCount",
           "the sidecar must name WHICH stock pool it read")
        eq(j.get("predicts_jlc_assembly_allocation"), False,
           "the sidecar must state that it does NOT predict JLC allocation")
        check("F-ECHO" in (j.get("pass_means") or ""),
              f"pass_means must point at the instrument that DOES answer it: "
              f"{j.get('pass_means')!r}")
        # and the limit is not json-only: a human reading the terminal sees it
        r = run([KPY, FAB_SCRIPTS / "jlc_stock_check.py", str(bom)])
        contains(r.out, "necessary and not sufficient",
                 "the printed verdict states its own limit")


if __name__ == "__main__":
    sys.exit(main())
