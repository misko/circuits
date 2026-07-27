#!/usr/bin/env python3
"""T1: the RELEASE-ARTIFACT FRESHNESS gate
(`skills/jlcpcb-fab/scripts/release_freshness_check.py`).

Motivating incident (usb-hub-3s-v3 v1.2, 2026-07-23): a REDESIGNED board
sealed and shipped DO-NOT-ORDER because three independent defects all slipped
past every existing gate:

  (a) STALE ARTIFACT — pdf/assembly_{front,back}.pdf + pdf/pcb_layers.pdf were
      byte-identical (sha256-confirmed) to the PRIOR release v1.1's same-named
      files: the redesigned board shipped the OLD board's fab drawings.
  (b) AUDIT / MANIFEST DISAGREEMENT — verification/policy_audit.md said
      "M-BOM FAIL" / "Summary: FAIL=1" while the MANIFEST claimed
      "policy_audit: 0 FAIL" / "M-BOM ... PASS".
  (c) DRAFT README — the shipped ORDER_README.md was a working draft.

Second motivating incident (crow-recorder-central-v2 v1.0, sealed 2026-07-23,
found 2026-07-24) — check (d) MANIFEST SELF-CONSISTENCY: the manifest's
human-readable gate summary disagreed with the machine evidence it SHIPS and
no gate caught it: MANIFEST "ERC 0 errors (1409 baselined warnings)" vs
policy_audit.md "S-ERC PASS 0 errors (1215 warnings)" (erc.json measures
1409); MANIFEST "bom_source_check PASS (48 lines...)" vs fab/bom.csv's 49
actual data rows; and verification/bom_source_check.txt naming
"07_releases/v1.0-2026-07-23/fab/bom.csv" — not the sealed directory name
(crow-recorder-central-v2-v1.0-2026-07-23). The section-(d) fixtures below
use those EXACT mismatches. RED-VERIFIED (git-swap, 2026-07-24): with git
HEAD's pre-change release_freshness_check.py swapped back in, every
known-bad case in section (d) FAILS (the old gate passes the broken
releases, and `--_disable-manifest-consistency` is an unknown argument),
then the fixed script restored and all pass — see the git-swap note at the
section header.

Fixtures are SELF-CONTAINED synthetic release trees built in a tmpdir (the
sealed real releases are immutable and never written). Each known-bad fixture
breaks exactly ONE of the three, so the test proves the gate reacts to THAT
defect. RED-VERIFY: every known-bad case is re-run with that one check
neutered (`--_disable-*`) and shown to PASS — proving the finding comes from
the check under test and nothing else. A gate that cannot fail is worthless.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (ROOT, KPY, check, contains, main, must_fail,  # noqa: E402
                     must_pass, not_contains, run, test, tmpdir)

GATE = ROOT / "skills" / "jlcpcb-fab" / "scripts" / "release_freshness_check.py"

# A distinct little PDF-ish blob keyed by a tag, so "same tag => identical
# bytes" and "different tag => different bytes" is exact and obvious.
def _blob(tag):
    return (b"%PDF-1.5\n% generated artifact for " + tag.encode() +
            b"\n" + (b"\x00\x11\x22" * 40) + b"\n%%EOF\n")


_AUDIT_PASS = """# Policy audit — demo

| ID | Grade | Detail |
|---|---|---|
| S-ERC | PASS | 0 errors |
| M-BOM | PASS | every BOM LCSC == source |
| M-REL | PASS | provenance + hashes verify |

Summary: FAIL=0, HUMAN=6, N-A=2, PASS=27, WAIVED=2
"""

_AUDIT_FAIL = """# Policy audit — demo

| ID | Grade | Detail |
|---|---|---|
| S-ERC | PASS | 0 errors |
| M-BOM | FAIL | 15 BOM-vs-source defect(s): SUBSTITUTED code ... |
| M-REL | PASS | provenance + hashes verify |

Summary: FAIL=1, HUMAN=6, N-A=2, PASS=27, WAIVED=2
"""

_MANIFEST_PASS = """# MANIFEST — demo v{ver}

board:        demo_board
version:      v{ver}
git_dirty:    false
gates (MEASURED this release):
  policy_audit:              0 FAIL (PASS=27, WAIVED=2)
  M-BOM (bom_source_check):  PASS -- every fab/bom.csv LCSC == source
"""

_README_FINAL = """# ORDER README — demo v{ver}

Final order document. Board 100 x 80 mm, 4 layer, 42 parts.
Hand-solder: J4, J5. First-power ritual: bench 12 V, confirm 5.0 V rails.
"""

_README_DRAFT = """# ORDER README — demo v{ver}

> DRAFT for the v{ver} seal (staged in `06_build/verification/`). At seal
time this moves to the release root.

Board 100 x 80 mm, 4 layer, 42 parts.
"""


def make_release(root, ver, *, pdf_tags, audit=_AUDIT_PASS,
                 manifest=_MANIFEST_PASS, readme=_README_FINAL,
                 exceptions=None):
    """Build one synthetic release tree 07_releases/v<ver>-2026-07-23/.

    `pdf_tags` maps a pdf/ filename -> blob tag (same tag across two releases
    => byte-identical file). Everything else is a knob for one known-bad case.
    """
    d = root / f"v{ver}-2026-07-23"
    (d / "pdf").mkdir(parents=True, exist_ok=True)
    (d / "fab").mkdir(parents=True, exist_ok=True)
    (d / "verification").mkdir(parents=True, exist_ok=True)
    for name, tag in pdf_tags.items():
        (d / "pdf" / name).write_bytes(_blob(tag))
    # a fab artifact keyed to the version so it is naturally fresh
    (d / "fab" / "demo_gerbers.zip").write_bytes(_blob(f"gerber-{ver}"))
    (d / "verification" / "policy_audit.md").write_text(audit)
    (d / "MANIFEST.txt").write_text(manifest.format(ver=ver))
    (d / "ORDER_README.md").write_text(readme.format(ver=ver))
    if exceptions is not None:
        (d / "verification" / "freshness_exceptions.txt").write_text(exceptions)
    return d


def gate(release_dir, *extra):
    return run([KPY, GATE, str(release_dir), *extra])


def two_release_root(*, v2_pdf_tags, **v2_kw):
    """A 07_releases/ root with a clean prior v1.1 and a v1.2 under test."""
    root = tmpdir("relfresh_")
    make_release(root, "1.1",
                 pdf_tags={"assembly_front.pdf": "front-v1.1",
                           "assembly_back.pdf": "back-v1.1",
                           "pcb_layers.pdf": "layers-v1.1"})
    d2 = make_release(root, "1.2", pdf_tags=v2_pdf_tags, **v2_kw)
    return root, d2


# --------------------------------------------------------------- clean case
@test("release_freshness: fresh artifacts + consistent audit/manifest + final "
      "README = PASS")
def t_pass():
    _, d2 = two_release_root(
        v2_pdf_tags={"assembly_front.pdf": "front-v1.2",
                     "assembly_back.pdf": "back-v1.2",
                     "pcb_layers.pdf": "layers-v1.2"})
    r = must_pass(gate(d2), "the all-fresh release")
    contains(r.out, "FRESHNESS: PASS", "verdict")


@test("release_freshness: the very FIRST release (no predecessor) can't be "
      "stale — PASS")
def t_first_release_ok():
    root = tmpdir("relfresh_first_")
    d = make_release(root, "1.0",
                     pdf_tags={"assembly_front.pdf": "front-v1.0"})
    r = must_pass(gate(d), "first release has nothing to be stale against")
    contains(r.out, "FRESHNESS: PASS", "verdict")


# -------------------------------------------------- (a) STALE ARTIFACT
@test("release_freshness FAILS when a PDF is byte-identical to a prior "
      "release's same-named file (the v1.2 shipped-old-drawings defect)",
      kind="known_bad")
def t_stale_pdf():
    # assembly_front reuses the v1.1 tag => byte-identical; the rest are fresh
    _, d2 = two_release_root(
        v2_pdf_tags={"assembly_front.pdf": "front-v1.1",   # STALE
                     "assembly_back.pdf": "back-v1.2",
                     "pcb_layers.pdf": "layers-v1.2"})
    r = must_fail(gate(d2), "stale PDF must block the seal", "STALE")
    contains(r.out, "assembly_front.pdf", "names the stale file")
    contains(r.out, "FRESHNESS: FAIL", "verdict")
    # RED-VERIFY: neuter ONLY the stale check -> the same fixture passes,
    # proving the finding came from the stale check and nothing else.
    rr = gate(d2, "--_disable-stale")
    check(rr.rc == 0,
          f"red-verify: with the stale check neutered the stale fixture must "
          f"pass, got rc={rr.rc}\n{rr.out}")
    not_contains(rr.out, "STALE", "neutered run emits no stale finding")


@test("release_freshness FAILS on stale FAB output too (gerber zip identical "
      "to a prior release)", kind="known_bad")
def t_stale_fab():
    root = tmpdir("relfresh_fab_")
    make_release(root, "1.1", pdf_tags={"assembly_front.pdf": "front-v1.1"})
    d2 = make_release(root, "1.2",
                      pdf_tags={"assembly_front.pdf": "front-v1.2"})
    # overwrite v1.2's gerber with v1.1's exact bytes -> stale fab artifact
    (d2 / "fab" / "demo_gerbers.zip").write_bytes(_blob("gerber-1.1"))
    r = must_fail(gate(d2), "stale gerber must block", "STALE")
    contains(r.out, "fab/demo_gerbers.zip", "names the stale fab file")


@test("release_freshness: a documented exception (reason given) waives one "
      "identical file — and the waiver itself needs a reason")
def t_exception_mechanism():
    # v1.2 legitimately reuses schematic-shaped file; waive it WITH a reason.
    root, d2 = two_release_root(
        v2_pdf_tags={"assembly_front.pdf": "front-v1.1",   # identical
                     "assembly_back.pdf": "back-v1.2",
                     "pcb_layers.pdf": "layers-v1.2"},
        exceptions="pdf/assembly_front.pdf   doc-only re-release, drawing unchanged\n")
    r = must_pass(gate(d2), "documented exception waives the identical file")
    contains(r.out, "WAIVED", "notes the waiver")
    contains(r.out, "FRESHNESS: PASS", "verdict")


@test("release_freshness FAILS a bare-path exception with NO reason "
      "(a waiver needs evidence)", kind="known_bad")
def t_exception_needs_reason():
    root, d2 = two_release_root(
        v2_pdf_tags={"assembly_front.pdf": "front-v1.1",   # identical
                     "assembly_back.pdf": "back-v1.2",
                     "pcb_layers.pdf": "layers-v1.2"},
        exceptions="assembly_front.pdf\n")   # path, no reason
    r = must_fail(gate(d2), "reasonless exception is rejected", "BAD EXCEPTION")
    # and the underlying stale file is still flagged, not silently waived
    contains(r.out, "STALE", "the file is still stale without a valid waiver")


# ------------------------------------------- (b) AUDIT / MANIFEST DISAGREEMENT
@test("release_freshness FAILS when policy_audit.md says FAIL but the MANIFEST "
      "claims 0-FAIL/PASS (the shipped-audit-contradicts-manifest defect)",
      kind="known_bad")
def t_audit_manifest_disagree():
    _, d2 = two_release_root(
        v2_pdf_tags={"assembly_front.pdf": "front-v1.2",
                     "assembly_back.pdf": "back-v1.2",
                     "pcb_layers.pdf": "layers-v1.2"},
        audit=_AUDIT_FAIL,            # audit: FAIL=1 (M-BOM)
        manifest=_MANIFEST_PASS)      # manifest: policy_audit 0 FAIL
    r = must_fail(gate(d2), "audit/manifest disagreement must block",
                  "AUDIT/MANIFEST DISAGREEMENT")
    contains(r.out, "M-BOM", "names the disagreeing check")
    contains(r.out, "FRESHNESS: FAIL", "verdict")
    # RED-VERIFY: neuter ONLY the audit/manifest check -> passes.
    rr = gate(d2, "--_disable-audit-manifest")
    check(rr.rc == 0,
          f"red-verify: with the audit/manifest check neutered this fixture "
          f"must pass, got rc={rr.rc}\n{rr.out}")
    not_contains(rr.out, "DISAGREEMENT", "neutered run emits no disagreement")


@test("release_freshness: a manifest that HONESTLY reports the audit's FAIL "
      "count does not trip the disagreement check (only under-reporting does)")
def t_audit_manifest_honest():
    # both audit and manifest say FAIL=1: no *disagreement*. (Make the rest of
    # the release clean so this isolates the audit/manifest axis.)
    honest_manifest = (
        "# MANIFEST — demo v{ver}\n\nversion: v{ver}\n"
        "gates:\n  policy_audit:  1 FAIL (known open item)\n")
    _, d2 = two_release_root(
        v2_pdf_tags={"assembly_front.pdf": "front-v1.2",
                     "assembly_back.pdf": "back-v1.2",
                     "pcb_layers.pdf": "layers-v1.2"},
        audit=_AUDIT_FAIL, manifest=honest_manifest)
    r = gate(d2)
    not_contains(r.out, "DISAGREEMENT",
                 "matching FAIL counts are not a disagreement")


# ------------------------------------------------------- (c) DRAFT README
@test("release_freshness FAILS when the shipped README carries a draft marker",
      kind="known_bad")
def t_draft_readme():
    _, d2 = two_release_root(
        v2_pdf_tags={"assembly_front.pdf": "front-v1.2",
                     "assembly_back.pdf": "back-v1.2",
                     "pcb_layers.pdf": "layers-v1.2"},
        readme=_README_DRAFT)
    r = must_fail(gate(d2), "draft README must block the seal", "DRAFT README")
    contains(r.out, "FRESHNESS: FAIL", "verdict")
    # RED-VERIFY: neuter ONLY the readme check -> passes.
    rr = gate(d2, "--_disable-readme")
    check(rr.rc == 0,
          f"red-verify: with the readme check neutered the draft-README "
          f"fixture must pass, got rc={rr.rc}\n{rr.out}")
    not_contains(rr.out, "DRAFT README", "neutered run emits no readme finding")


@test("release_freshness: a TODO/placeholder marker in the README also blocks",
      kind="known_bad")
def t_todo_readme():
    _, d2 = two_release_root(
        v2_pdf_tags={"assembly_front.pdf": "front-v1.2",
                     "assembly_back.pdf": "back-v1.2",
                     "pcb_layers.pdf": "layers-v1.2"},
        readme="# ORDER README v{ver}\n\nHand-solder list: TODO fill in.\n")
    must_fail(gate(d2), "TODO placeholder must block", "DRAFT README")


# ---------------------------------------- docs-only supersede mode
# usb-hub-3s-v3 v1.4 (2026-07-23): a documentation-only supersede release
# INTENTIONALLY ships fab/ byte-identical to its predecessor — the board did
# not change, only the docs did. The default stale check flags exactly that
# identity as a defect; `--docs-only-supersede <prior>` ASSERTS the declared
# identity instead: fab/source/3d MUST match the prior byte-for-byte (any
# deviation FAILs — a "docs-only" release that changes fab is lying),
# identical pdf/ is allowed, and ORDER_README + MANIFEST MUST differ.
# RED-VERIFIED (git-swap, 2026-07-23): against pre-change
# release_freshness_check.py the flag is an unrecognized argument (argparse
# exit 2 carrying none of the asserted findings), so every docs-only case
# below goes RED — verified by swapping git HEAD's script back in (all four
# docs-only tests failed), then restoring the fixed script (all pass). The
# default mode is byte-for-byte untouched: t_stale_pdf / t_stale_fab above
# still prove the normal-mode identical-artifact teeth.
def docs_only_root():
    """A prior v1.3 and a docs-only v1.4 whose fab/ + pdf/ are byte-identical
    to it (docs differ automatically: MANIFEST/README embed the version)."""
    root = tmpdir("relfresh_docsonly_")
    tags = {"assembly_front.pdf": "front-v1.3",
            "assembly_back.pdf": "back-v1.3"}
    d1 = make_release(root, "1.3", pdf_tags=tags)
    d2 = make_release(root, "1.4", pdf_tags=tags)
    # fab must be byte-identical to the prior (make_release keys it by ver)
    (d2 / "fab" / "demo_gerbers.zip").write_bytes(_blob("gerber-1.3"))
    return root, d1, d2


def dgate(d2, d1, *extra):
    return gate(d2, "--docs-only-supersede", str(d1), *extra)


@test("release_freshness --docs-only-supersede PASSES a true docs-only "
      "release: identical fab+pdf ASSERTED, changed README+MANIFEST")
def t_docs_only_pass():
    """The v1.4 shape: fab/ and pdf/ byte-identical to v1.3, ORDER_README and
    MANIFEST rewritten. The identity that the default mode would flag as
    STALE is asserted, not flagged."""
    _, d1, d2 = docs_only_root()
    r = must_pass(dgate(d2, d1), "a true docs-only supersede")
    contains(r.out, "byte-identical", "notes the asserted identity")
    contains(r.out, "FRESHNESS: PASS", "verdict")
    not_contains(r.out, "STALE", "identical artifacts are not flagged stale")
    # and the SAME tree in DEFAULT mode still fails (its pdf+fab are
    # identical to a lower-version sibling): the mode is opt-in, the
    # default gate's teeth are intact.
    rd = must_fail(gate(d2), "default mode still flags the identity", "STALE")
    contains(rd.out, "FRESHNESS: FAIL", "default-mode verdict")


@test("release_freshness --docs-only-supersede FAILS when ONE fab file "
      "differs from the prior (a 'docs-only' release that changes fab is "
      "lying)", kind="known_bad")
def t_docs_only_fab_differs():
    """Break the clean case in exactly one way: v1.4's gerber zip gets fresh
    bytes. Docs-only mode must FAIL naming the file — a fab deviation means
    this is NOT a docs-only release and needs a full seal."""
    _, d1, d2 = docs_only_root()
    (d2 / "fab" / "demo_gerbers.zip").write_bytes(_blob("gerber-1.4-tweak"))
    r = must_fail(dgate(d2, d1), "a differing fab file must block",
                  "DOCS-ONLY DEVIATION")
    contains(r.out, "fab/demo_gerbers.zip", "names the deviating file")
    contains(r.out, "lying", "says what a fab change means here")
    contains(r.out, "FRESHNESS: FAIL", "verdict")


@test("release_freshness --docs-only-supersede FAILS an UNCHANGED "
      "ORDER_README (a supersede that changes no docs supersedes nothing)",
      kind="known_bad")
def t_docs_only_readme_unchanged():
    """Break the clean case the other way: v1.4 ships v1.3's ORDER_README
    byte-for-byte. The release's entire point is the changed documentation,
    so an identical README is a FAIL."""
    _, d1, d2 = docs_only_root()
    (d2 / "ORDER_README.md").write_bytes(
        (d1 / "ORDER_README.md").read_bytes())
    r = must_fail(dgate(d2, d1), "an unchanged README must block",
                  "DOCS-ONLY UNCHANGED")
    contains(r.out, "order README", "names the unchanged document")
    contains(r.out, "supersedes nothing", "explains why it blocks")


@test("release_freshness --docs-only-supersede FAILS an unchanged MANIFEST "
      "(the new release must re-state what it measured)", kind="known_bad")
def t_docs_only_manifest_unchanged():
    """Same axis, other document: an identical MANIFEST means the release
    never re-declared its own identity/gates — FAIL."""
    _, d1, d2 = docs_only_root()
    (d2 / "MANIFEST.txt").write_bytes((d1 / "MANIFEST.txt").read_bytes())
    r = must_fail(dgate(d2, d1), "an unchanged MANIFEST must block",
                  "DOCS-ONLY UNCHANGED")
    contains(r.out, "MANIFEST.txt", "names the unchanged document")


@test("release_freshness --docs-only-supersede still runs the draft-README "
      "check (b/c gates keep their teeth in this mode)", kind="known_bad")
def t_docs_only_draft_readme_still_bites():
    """Docs-only mode replaces ONLY the stale check. A draft-marker
    ORDER_README (which also differs from the prior, so the changed-docs
    assertion passes) must still block via check (c)."""
    _, d1, d2 = docs_only_root()
    (d2 / "ORDER_README.md").write_text(_README_DRAFT.format(ver="1.4"))
    r = must_fail(dgate(d2, d1), "a draft README must still block",
                  "DRAFT README")
    not_contains(r.out, "DOCS-ONLY UNCHANGED",
                 "the draft README did change vs the prior — only (c) fires")


# ------------------------------------------- BOM-only supersede mode
# The case docs-only mode CORRECTLY refuses, and which therefore had nowhere
# to go: crow-mic-pod-v2 v1.1 (2026-07-25). v1.0's fab/bom.csv carried MK1
# with its MPN *and* LCSC columns both EMPTY and J1 at live stock 0, neither
# designator on the CPL — so the upload stalls at JLC's BOM/CPL matcher.
# Removing those rows changes fab/, so `--docs-only-supersede` fails it ("a
# docs-only release that changes fab is lying" — correctly). But no copper
# moved. `--bom-only-supersede` asserts something STRONGER than identity for
# that one file: the delta must be whole rows REMOVED for designators that
# are NOT on the CPL (canon A-POP: an unplaced part must leave the BOM).
_BOM_HDR = "Comment,Designator,Footprint,MPN,LCSC\n"
_BOM_PRIOR = (_BOM_HDR + "100nF,\"C1,C2\",C_0603,,C14663\n"
              "10k,R1,R_0603,,C25804\n"
              "electret,MK1,MIC_THT,,\n"
              "rj45,J1,RJ45_THT,,C9900035627\n")
_BOM_FIXED = (_BOM_HDR + "100nF,\"C1,C2\",C_0603,,C14663\n"
              "10k,R1,R_0603,,C25804\n")
_CPL = ("Designator,Val,Package,Mid X,Mid Y,Layer,Rotation\n"
        "C1,100nF,C_0603,10,-10,top,0.0\n"
        "C2,100nF,C_0603,12,-10,top,0.0\n"
        "R1,10k,R_0603,14,-10,top,0.0\n")


def bom_only_root():
    """A prior release whose BOM carries two rows that are NOT on the CPL,
    and a successor that removed exactly those rows. Everything else in fab/
    is byte-identical."""
    root, d1, d2 = docs_only_root()
    (d1 / "fab" / "bom.csv").write_text(_BOM_PRIOR)
    (d2 / "fab" / "bom.csv").write_text(_BOM_FIXED)
    for d in (d1, d2):
        (d / "fab" / "cpl.csv").write_text(_CPL)
        # a CPL activates A-STOCK, which is a DIFFERENT check with its own
        # teeth (t_stock_* below). Satisfy it here so these fixtures isolate
        # the bom-delta assertion and nothing else.
        (d / "verification" / "stock_check.json").write_text(json.dumps({
            "tool": "jlc_stock_check.py", "bom": "fab/bom.csv",
            "min_stock_per_board": 5, "verdict": "PASS",
            "failures": [], "uncoded_lines": [],
            "lines": [{"lcsc": "C14663", "designators": "C1,C2", "qty": 2,
                       "status": "OK", "stock": 101938374},
                      {"lcsc": "C25804", "designators": "R1", "qty": 1,
                       "status": "OK", "stock": 5672413}]}))
    return root, d1, d2


# ------------------------------------------------- cpl-only supersede (A-POS)
# RED-VERIFIED 2026-07-25 (tests/README step 3, GIT-SWAP variant): with
# `git show HEAD:.../release_freshness_check.py` swapped back in, this file
# reports **30 passed, 4 failed** — every cpl-only case dies on
# "unrecognized arguments: --cpl-only-supersede". Restored: 34 passed, 0
# failed. The mode cannot pass vacuously because it did not exist.
# The crow-recorder-central-v2 v1.5 shape. A wrong CPL COORDINATE is the one
# defect that is 100% assembly data and 0% copper: v1.4 shipped its only USB-C
# 1.3025mm off its own pads because the exporter emitted KiCad's footprint
# ANCHOR instead of JLC's pad-array datum. Fixing it changes fab/cpl.csv and
# nothing else, so docs-only refuses it and bom-only does not cover it.
_CPL_MOVED = ("Designator,Val,Package,Mid X,Mid Y,Layer,Rotation\n"
              "C1,100nF,C_0603,10,-8.6975,top,0.0\n"     # the datum fix
              "C2,100nF,C_0603,12,-10,top,0.0\n")        # R1 dropped (DNP)


def cpl_only_root(cur_cpl=None):
    root, d1, d2 = bom_only_root()
    for d in (d1, d2):
        (d / "fab" / "bom.csv").write_text(_BOM_PRIOR)
    (d1 / "fab" / "cpl.csv").write_text(_CPL)
    (d2 / "fab" / "cpl.csv").write_text(cur_cpl or _CPL_MOVED)
    return root, d1, d2


def cgate(d2, d1, *extra):
    return gate(d2, "--cpl-only-supersede", str(d1), *extra)


@test("release_freshness --cpl-only-supersede PASSES a coordinate fix plus a "
      "row dropped for a part that is no longer populated")
def t_cpl_only_pass():
    _, d1, d2 = cpl_only_root()
    r = must_pass(cgate(d2, d1), "a true cpl-only supersede")
    contains(r.out, "cpl-only supersede", "the mode should be announced")
    contains(r.out, "1 coordinate move(s)", "the delta shape should be explicit")
    contains(r.out, "0 rotation/layer/identity changes",
             "the assertion that separates this from a rotation fix")
    contains(r.out, "FRESHNESS: PASS", "verdict")
    # the stricter mode must still refuse the same tree
    rd = must_fail(dgate(d2, d1), "docs-only must still refuse a fab change",
                   "DOCS-ONLY DEVIATION")
    contains(rd.out, "fab/cpl.csv", "names the file docs-only refuses")


@test("release_freshness --cpl-only-supersede FAILS a ROTATION change — a "
      "coordinate fix and a rotation fix are different claims",
      kind="known_bad")
def t_kb_cpl_only_rotation_change():
    """The v1.3 -> v1.4 supersede WAS a CPL-only change and it moved seven
    ROTATIONS. If a release could smuggle a rotation into a 'coordinate fix',
    the two defect classes would share one unaccountable channel."""
    rot = ("Designator,Val,Package,Mid X,Mid Y,Layer,Rotation\n"
           "C1,100nF,C_0603,10,-8.6975,top,0.0\n"
           "C2,100nF,C_0603,12,-10,top,180.0\n")
    _, d1, d2 = cpl_only_root(rot)
    r = must_fail(cgate(d2, d1), "a smuggled rotation change",
                  "CPL-ONLY DEVIATION")
    contains(r.out, "Rotation changed", "names the column that moved")
    contains(r.out, "C2", "names the offending ref")
    contains(r.out, "A-ROT", "points at the evidence such a claim would need")


@test("release_freshness --cpl-only-supersede FAILS an ADDED CPL row — "
      "placing a new part is a population change, not a coordinate fix",
      kind="known_bad")
def t_kb_cpl_only_added_row():
    add = (_CPL + "R2,10k,R_0603,16,-10,top,0.0\n")
    _, d1, d2 = cpl_only_root(add)
    r = must_fail(cgate(d2, d1), "an added placement", "CPL-ONLY DEVIATION")
    contains(r.out, "R2", "names the newly-placed ref")
    contains(r.out, "ADDED", "says what happened")


@test("release_freshness --cpl-only-supersede FAILS when the CPL did not "
      "change at all — a supersede that moves nothing supersedes nothing",
      kind="known_bad")
def t_kb_cpl_only_no_change():
    _, d1, d2 = cpl_only_root(_CPL)
    r = must_fail(cgate(d2, d1), "an empty cpl-only supersede", "CPL-ONLY")
    contains(r.out, "supersedes nothing", "says why it is refused")
    contains(r.out, "docs-only", "names the mode that WOULD be correct")


def bgate(d2, d1, *extra):
    return gate(d2, "--bom-only-supersede", str(d1), *extra)


@test("release_freshness --bom-only-supersede PASSES removing BOM rows for "
      "designators that are not on the CPL")
def t_bom_only_pass():
    """The crow-mic-pod-v2 v1.1 shape. Everything but bom.csv is asserted
    byte-identical; bom.csv's delta is asserted to be removals only, and only
    of unplaced designators."""
    _, d1, d2 = bom_only_root()
    r = must_pass(bgate(d2, d1), "a true bom-only supersede")
    contains(r.out, "bom-only supersede", "the mode should be announced")
    contains(r.out, "2 whole row(s) REMOVED", "the delta should be stated")
    contains(r.out, "0 added", "the delta shape should be explicit")
    contains(r.out, "FRESHNESS: PASS", "verdict")
    # the SAME tree under docs-only must still FAIL — the modes are distinct
    # and the stricter one keeps its teeth
    rd = must_fail(dgate(d2, d1), "docs-only must still refuse a fab change",
                   "DOCS-ONLY DEVIATION")
    contains(rd.out, "fab/bom.csv", "names the file docs-only refuses")


@test("release_freshness --bom-only-supersede FAILS a removal for a "
      "designator that is STILL ON THE CPL", kind="known_bad")
def t_kb_bom_only_removed_but_placed():
    """The dangerous inversion: dropping a BOM line for a part JLC is still
    told to place leaves the machine sourcing nothing for a populated
    position. Break the clean case in exactly one way — put R1 on the CPL and
    remove its BOM row."""
    _, d1, d2 = bom_only_root()
    (d2 / "fab" / "bom.csv").write_text(
        _BOM_HDR + "100nF,\"C1,C2\",C_0603,,C14663\n")   # R1 row gone
    r = must_fail(bgate(d2, d1), "removing a placed part's BOM row must block",
                  "BOM-ONLY DEVIATION")
    contains(r.out, "STILL ON THE CPL", "must say why it is dangerous")
    contains(r.out, "R1", "must name the designator")


@test("release_freshness --bom-only-supersede FAILS an EDITED BOM row (a "
      "changed LCSC is a different board, not paperwork)", kind="known_bad")
def t_kb_bom_only_edited_row():
    """The mode permits removals, not substitutions. Swapping a code past a
    'bom-only' claim is exactly the usb-hub-3s-v3 v1.1 corruption class."""
    _, d1, d2 = bom_only_root()
    (d2 / "fab" / "bom.csv").write_text(
        _BOM_HDR + "100nF,\"C1,C2\",C_0603,,C14663\n"
        "10k,R1,R_0603,,C99999999\n")                     # code substituted
    r = must_fail(bgate(d2, d1), "an edited BOM row must block",
                  "BOM-ONLY DEVIATION")
    contains(r.out, "EDITED", "must say the row was edited")


@test("release_freshness --bom-only-supersede FAILS an ADDED BOM row",
      kind="known_bad")
def t_kb_bom_only_added_row():
    _, d1, d2 = bom_only_root()
    (d2 / "fab" / "bom.csv").write_text(
        _BOM_FIXED + "1uF,C9,C_0603,,C15849\n")
    r = must_fail(bgate(d2, d1), "an added BOM row must block",
                  "BOM-ONLY DEVIATION")
    contains(r.out, "ADDED", "must say the row was added")


@test("release_freshness --bom-only-supersede still refuses a NON-BOM fab "
      "change (the exemption is exactly one file)", kind="known_bad")
def t_kb_bom_only_other_fab_file():
    """The relaxation must not become a blanket fab waiver: bom-only exempts
    fab/bom.csv and nothing else. A changed gerber zip is still a respin."""
    _, d1, d2 = bom_only_root()
    (d2 / "fab" / "demo_gerbers.zip").write_bytes(_blob("gerber-tweaked"))
    r = must_fail(bgate(d2, d1), "a changed gerber must block even here",
                  "DOCS-ONLY DEVIATION")
    contains(r.out, "demo_gerbers.zip", "names the deviating file")


# ------------------------------------ legible-bom supersede mode (F-LEGIBLE)
# RED-VERIFIED 2026-07-27 (tests/README step 3, GIT-SWAP variant): with
# `git show HEAD:skills/jlcpcb-fab/scripts/release_freshness_check.py` swapped
# back in, every test below dies on "unrecognized arguments:
# --legible-bom-supersede" — the mode cannot pass vacuously, because it did not
# exist. Restored and re-run green.
#
# The case the three modes above ALL correctly refuse. Canon F-LEGIBLE
# (ADR-0006): crow-recorder-central-v2 v1.5's BOM was uploaded to JLCPCB and
# its parts "were not being picked up by their web processing". Fixing that
# EDITS every row — MPN filled from the part's own dossier, a Comment that
# stops being an LCSC code — while board, gerbers, drills, CPL, STEP and PDFs
# stay byte-identical. docs-only refuses (fab/ changed); bom-only refuses too,
# and RIGHTLY, because it FAILs on any EDITED row for the A-POP defect it
# guards. So the edit needs its own mode with its own assertion.
_BOM_ILLEGIBLE = (_BOM_HDR + "100nF,\"C1,C2\",C_0603,,C14663\n"
                  "C25804,R1,R_0603,,C25804\n")
_BOM_LEGIBLE = (_BOM_HDR
                + "100nF,\"C1,C2\",C_0603,CC0603KRX7R9BB104,C14663\n"
                "10k,R1,R_0603,0603WAF1002T5E,C25804\n")


def legible_bom_root(cur_bom=None, prior_bom=None):
    """A prior release whose BOM ships blank MPNs and an LCSC code in the
    Comment column, and a successor that fixed exactly that. Everything else in
    fab/ is byte-identical. Both codes resolve from the vetted passives ledger,
    so the fixture needs no 02_parts tree."""
    root, d1, d2 = bom_only_root()
    (d1 / "fab" / "bom.csv").write_text(prior_bom or _BOM_ILLEGIBLE)
    (d2 / "fab" / "bom.csv").write_text(cur_bom or _BOM_LEGIBLE)
    return root, d1, d2


def lgate(d2, d1, *extra):
    return gate(d2, "--legible-bom-supersede", str(d1), *extra)


@test("release_freshness --legible-bom-supersede PASSES a BOM whose Comment "
      "and MPN columns were made legible and NOTHING else moved")
def t_legible_bom_pass():
    _, d1, d2 = legible_bom_root()
    r = must_pass(lgate(d2, d1), "a true legible-bom supersede")
    contains(r.out, "legible-bom supersede", "the mode should be announced")
    contains(r.out, "0 added, 0 removed, 0 Footprint/LCSC changes",
             "the assertion that separates this from a sourcing change")
    contains(r.out, "F-LEGIBLE on this release", "the verdict is quoted")
    contains(r.out, "FRESHNESS: PASS", "verdict")
    # the two stricter modes must still refuse the same tree
    rd = must_fail(dgate(d2, d1), "docs-only must still refuse a fab change",
                   "DOCS-ONLY DEVIATION")
    contains(rd.out, "fab/bom.csv", "names the file docs-only refuses")
    rb = must_fail(bgate(d2, d1), "bom-only must still refuse an EDITED row",
                   "BOM-ONLY DEVIATION")
    contains(rb.out, "EDITED", "bom-only refuses it for its own good reason")


@test("release_freshness --legible-bom-supersede FAILS a changed LCSC — a "
      "legibility pass rewrites how a row READS, never WHICH PART it is",
      kind="known_bad")
def t_kb_legible_bom_substitution():
    """The C82317 -> C131025 class, smuggled in as paperwork. A mode that only
    asked "did the file become legible?" would wave this through: the
    substituted row is perfectly readable."""
    sub = (_BOM_HDR + "100nF,\"C1,C2\",C_0603,CC0603KRX7R9BB104,C14663\n"
           "10k,R1,R_0603,0603WAF1002T5E,C25803\n")     # code substituted
    _, d1, d2 = legible_bom_root(sub)
    r = must_fail(lgate(d2, d1), "a smuggled substitution must block",
                  "LEGIBLE-BOM DEVIATION")
    contains(r.out, "LCSC changed", "names the column that moved")
    contains(r.out, "C131025", "points at the incident class")


@test("release_freshness --legible-bom-supersede FAILS a REMOVED row — that "
      "is an A-POP fix and belongs in --bom-only-supersede", kind="known_bad")
def t_kb_legible_bom_removed_row():
    _, d1, d2 = legible_bom_root(
        _BOM_HDR + "100nF,\"C1,C2\",C_0603,CC0603KRX7R9BB104,C14663\n")
    r = must_fail(lgate(d2, d1), "a removed row must block",
                  "LEGIBLE-BOM DEVIATION")
    contains(r.out, "REMOVED", "says what happened")
    contains(r.out, "--bom-only-supersede", "names the mode that WOULD apply")


@test("release_freshness --legible-bom-supersede FAILS a BOM that is STILL "
      "ILLEGIBLE — the release must ship what it claims", kind="known_bad")
def t_kb_legible_bom_still_illegible():
    """The vacuous-pass shape: rewrite one Comment, leave every MPN blank, and
    call it a legibility release. The verdict comes from the F-LEGIBLE gate
    itself, not from this file's own opinion (ONE grader, canon M1)."""
    half = (_BOM_HDR + "100nF,\"C1,C2\",C_0603,,C14663\n"
            "10k,R1,R_0603,,C25804\n")          # Comments fixed, MPNs blank
    _, d1, d2 = legible_bom_root(half)
    r = must_fail(lgate(d2, d1), "an illegible 'legibility' release must block",
                  "still FAILS F-LEGIBLE")
    contains(r.out, "must SHIP a legible BOM", "says what is required")


@test("release_freshness --legible-bom-supersede FAILS when the PRIOR BOM was "
      "already legible — there was no defect to supersede", kind="known_bad")
def t_kb_legible_bom_no_defect():
    _, d1, d2 = legible_bom_root(_BOM_LEGIBLE, prior_bom=_BOM_LEGIBLE)
    r = must_fail(lgate(d2, d1), "a supersede of a clean BOM must block",
                  "LEGIBLE-BOM")
    contains(r.out, "supersedes nothing", "says why it is refused")


@test("release_freshness --legible-bom-supersede still refuses a NON-BOM fab "
      "change (the exemption is exactly one file)", kind="known_bad")
def t_kb_legible_bom_other_fab_file():
    _, d1, d2 = legible_bom_root()
    (d2 / "fab" / "demo_gerbers.zip").write_bytes(_blob("gerber-tweaked"))
    r = must_fail(lgate(d2, d1), "a changed gerber must block even here",
                  "DOCS-ONLY DEVIATION")
    contains(r.out, "demo_gerbers.zip", "names the deviating file")


# ----------------- board-prefixed release names (the _version_key silent skip)
# Found 2026-07-24: _version_key matched only names STARTING with 'v', so
# every board-prefixed release (cooksense-v1.1-…, crow-mic-pod-v2-v1.0-…,
# crow-recorder-central-v2-v1.0-…, interposer-v1.0-…) had NO predecessors and
# the stale-artifact check (a) silently never ran on it — the same
# silent-skip class as the M-REL glob bug. RED-VERIFIED (pre-fix run,
# 2026-07-24): against the pre-fix script, the t_prefixed_stale fixture
# below (board-prefixed v1.1 shipping v1.0's exact pdf bytes) exited 0 /
# "FRESHNESS: PASS"; after the _version_key fix it FAILS with the STALE
# finding. A gate that cannot fail is worthless.
def prefixed_release(root, name, *, pdf_tag, gerber_tag=None):
    d = root / name
    for sub in ("pdf", "fab", "verification"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    (d / "pdf" / "assembly.pdf").write_bytes(_blob(pdf_tag))
    (d / "fab" / "demo_gerbers.zip").write_bytes(
        _blob(gerber_tag or f"gerber-{name}"))
    (d / "verification" / "policy_audit.md").write_text(_AUDIT_PASS)
    (d / "MANIFEST.txt").write_text(_MANIFEST_PASS.format(ver=name))
    (d / "ORDER_README.md").write_text(_README_FINAL.format(ver=name))
    return d


@test("_version_key: a BOARD-PREFIXED release shipping a prior release's "
      "exact pdf bytes now FAILS check (a) — pre-fix it silently passed "
      "(dir names not starting with 'v' had no predecessors)",
      kind="known_bad")
def t_prefixed_stale():
    root = tmpdir("relfresh_prefix_")
    prefixed_release(root, "demoboard-v1.0-2026-07-23", pdf_tag="asm-1.0")
    d2 = prefixed_release(root, "demoboard-v1.1-2026-07-24",
                          pdf_tag="asm-1.0")   # STALE: v1.0's exact bytes
    r = must_fail(gate(d2), "board-prefixed stale pdf must block", "STALE")
    contains(r.out, "assembly.pdf", "names the stale file")
    contains(r.out, "demoboard-v1.0-2026-07-23", "names the predecessor")
    # RED-VERIFY (i): neuter only the stale check -> passes.
    rr = gate(d2, "--_disable-stale")
    check(rr.rc == 0,
          f"red-verify: with the stale check neutered the prefixed-stale "
          f"fixture must pass, got rc={rr.rc}\n{rr.out}")


@test("_version_key: a board whose NAME ends in -v2 "
      "(crow-recorder-central-v2-v1.0 shape) parses the LAST v-token as the "
      "release version — its prefixed v1.1 still catches a stale artifact",
      kind="known_bad")
def t_prefixed_vN_board_name():
    root = tmpdir("relfresh_v2name_")
    prefixed_release(root, "demo-central-v2-v1.0-2026-07-23", pdf_tag="a")
    d2 = prefixed_release(root, "demo-central-v2-v1.1-2026-07-24",
                          pdf_tag="a")         # STALE
    r = must_fail(gate(d2), "v2-suffixed board name must still compare",
                  "STALE")
    contains(r.out, "demo-central-v2-v1.0-2026-07-23", "right predecessor")


@test("_version_key: two DIFFERENT boards sharing one 07_releases/ root "
      "(cooksense-* + interposer-*) are never cross-compared — an "
      "interposer file identical to a cooksense file is not stale")
def t_prefixed_no_cross_board():
    root = tmpdir("relfresh_xboard_")
    prefixed_release(root, "cooksense-v1.0-2026-07-23", pdf_tag="shared")
    d2 = prefixed_release(root, "interposer-v1.0-2026-07-24",
                          pdf_tag="shared")    # same bytes, DIFFERENT board
    r = must_pass(gate(d2), "different board prefix is not a predecessor")
    not_contains(r.out, "STALE", "no cross-board stale finding")


# --------------------------- (d) MANIFEST SELF-CONSISTENCY
# crow-recorder-central-v2 v1.0 (2026-07-23): the MANIFEST's prose gate
# summary disagreed with its OWN shipped evidence three ways (ERC warning
# count, BOM line count, embedded release path) and nothing caught it —
# check (b) compares only the policy_audit RESULT and the stale check only
# bytes. Each fixture below reproduces exactly ONE of the three, with the
# incident's real numbers. RED-VERIFY is double: (i) per-case, the fixture
# passes when ONLY the new check is neutered (--_disable-manifest-consistency)
# — the finding comes from this check and nothing else; (ii) git-swap
# (2026-07-24): with `git show HEAD:.../release_freshness_check.py` swapped
# back in, t_mc_erc_mismatch / t_mc_bom_mismatch / t_mc_path_mismatch all
# went RED (the old gate PASSES each broken release), then the fixed script
# was restored and all pass.
def consistency_release(root, *, dirname="demoboard-v1.0-2026-07-23",
                        manifest_erc="ERC 0 errors (1409 baselined warnings)",
                        audit_erc="0 errors (1409 warnings)",
                        erc_json_warnings=1409,
                        erc_included=("error", "warning", "exclusion"),
                        manifest_bom_lines=49, bom_rows=49,
                        bom_source_dir=None):
    """One release tree shaped like the crow-rv2 v1.0 seal: a MANIFEST whose
    gate summary states ERC + BOM counts, plus the machine evidence those
    claims must match (policy_audit S-ERC row, erc.json, fab/bom.csv,
    bom_source_check.txt with an embedded 07_releases/<dir>/ path). Defaults
    are fully self-consistent; each knob breaks exactly one axis."""
    import json
    d = root / dirname
    for sub in ("pdf", "fab", "verification"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    (d / "pdf" / "assembly.pdf").write_bytes(_blob(f"asm-{dirname}"))
    (d / "fab" / "demo_gerbers.zip").write_bytes(_blob(f"gerber-{dirname}"))
    (d / "verification" / "policy_audit.md").write_text(
        "# Policy audit — demo\n\n| ID | Grade | Detail |\n|---|---|---|\n"
        f"| S-ERC | PASS | {audit_erc} |\n"
        "| M-BOM | PASS | every BOM LCSC == source |\n\n"
        "Summary: FAIL=0, PASS=30\n")
    (d / "verification" / "erc.json").write_text(json.dumps({
        "included_severities": list(erc_included),
        "sheets": [{"violations":
                    [{"severity": "warning"}] * erc_json_warnings}]}))
    (d / "fab" / "bom.csv").write_text(
        "Comment,Designator,Footprint,MPN,LCSC\n" +
        "".join(f'100k,"R{i}a,R{i}b",R_0402,,C{25741+i}\n'
                for i in range(bom_rows)))
    (d / "verification" / "bom_source_check.txt").write_text(
        f"BOM-vs-source: 07_releases/{bom_source_dir or dirname}/fab/bom.csv\n"
        "BOM SOURCE CHECK: PASS (every BOM LCSC == source)\n")
    (d / "MANIFEST.txt").write_text(
        f"board: demo\nversion: v1.0\ngit_dirty: false\n"
        f"gates:  DRC 0/0/0 · {manifest_erc} ·\n"
        f"        policy_audit 0 FAIL ·\n"
        f"        bom_source_check PASS ({manifest_bom_lines} lines, "
        f"every LCSC == source)\n")
    (d / "ORDER_README.md").write_text(_README_FINAL.format(ver="1.0"))
    return d


@test("manifest-consistency: a release whose MANIFEST counts MATCH its "
      "shipped evidence (and whose evidence paths name its real dir) PASSES")
def t_mc_clean():
    d = consistency_release(tmpdir("relmc_clean_"))
    r = must_pass(gate(d), "self-consistent manifest")
    contains(r.out, "FRESHNESS: PASS", "verdict")
    not_contains(r.out, "MISMATCH", "no consistency finding on a clean bundle")


@test("manifest-consistency FAILS when the MANIFEST's ERC warning count "
      "disagrees with the shipped policy_audit S-ERC row (crow-rv2 v1.0: "
      "MANIFEST 1409 vs audit 1215)", kind="known_bad")
def t_mc_erc_mismatch():
    """The incident verbatim: MANIFEST says 1409 baselined warnings, the
    bundled policy_audit.md says 1215, the bundled erc.json measures 1409.
    The bundle disagrees with itself -> FAIL naming all three values."""
    d = consistency_release(tmpdir("relmc_erc_"),
                            audit_erc="0 errors (1215 warnings)")
    r = must_fail(gate(d), "ERC count disagreement must block",
                  "MANIFEST/EVIDENCE MISMATCH")
    contains(r.out, "ERC warning count", "names the disagreeing field")
    contains(r.out, "1409", "reports the MANIFEST/erc.json value")
    contains(r.out, "1215", "reports the audit's value")
    # RED-VERIFY (i): neuter ONLY the manifest-consistency check -> passes.
    rr = gate(d, "--_disable-manifest-consistency")
    check(rr.rc == 0,
          f"red-verify: with manifest-consistency neutered the ERC-mismatch "
          f"fixture must pass, got rc={rr.rc}\n{rr.out}")
    not_contains(rr.out, "MISMATCH", "neutered run emits no finding")


@test("manifest-consistency FAILS when the MANIFEST's bom_source_check line "
      "count disagrees with fab/bom.csv's actual data rows (crow-rv2 v1.0: "
      "claimed 48, shipped 49)", kind="known_bad")
def t_mc_bom_mismatch():
    """The incident verbatim: MANIFEST 'bom_source_check PASS (48 lines...)'
    while the shipped fab/bom.csv carries 49 data rows (csv-parsed, so
    quoted multi-refdes cells count as one row)."""
    d = consistency_release(tmpdir("relmc_bom_"),
                            manifest_bom_lines=48, bom_rows=49)
    r = must_fail(gate(d), "BOM count disagreement must block",
                  "MANIFEST/EVIDENCE MISMATCH")
    contains(r.out, "48 lines", "reports the claim")
    contains(r.out, "49 data row", "reports the measured rows")
    rr = gate(d, "--_disable-manifest-consistency")
    check(rr.rc == 0, f"red-verify: neutered BOM-mismatch fixture must pass, "
                      f"got rc={rr.rc}\n{rr.out}")


@test("manifest-consistency FAILS when verification evidence embeds a "
      "07_releases/ path that is NOT this release's directory (crow-rv2 "
      "v1.0: 'v1.0-2026-07-23' inside crow-recorder-central-v2-v1.0-...)",
      kind="known_bad")
def t_mc_path_mismatch():
    """The incident verbatim: bom_source_check.txt names
    07_releases/v1.0-2026-07-23/fab/bom.csv — a shortened/staging directory
    name, not the sealed dir — proving the evidence was produced against a
    path that is not this archive."""
    d = consistency_release(tmpdir("relmc_path_"),
                            dirname="demoboard-v1.0-2026-07-23",
                            bom_source_dir="v1.0-2026-07-23")
    r = must_fail(gate(d), "foreign evidence path must block",
                  "EVIDENCE PATH MISMATCH")
    contains(r.out, "bom_source_check.txt", "names the evidence file")
    contains(r.out, "v1.0-2026-07-23", "names the wrong dir")
    contains(r.out, "demoboard-v1.0-2026-07-23", "names the real dir")
    rr = gate(d, "--_disable-manifest-consistency")
    check(rr.rc == 0, f"red-verify: neutered path-mismatch fixture must "
                      f"pass, got rc={rr.rc}\n{rr.out}")


@test("manifest-consistency: a MANIFEST that states NO counts is not checked "
      "against them — absence != mismatch")
def t_mc_absence_not_mismatch():
    """Robustness: evidence present (bom.csv, erc.json, audit) but the
    MANIFEST prose states neither an ERC warning count nor a BOM line
    count. Nothing to compare against the manifest -> no finding. (The
    evidence itself stays self-consistent — audit 1409 == erc.json 1409 —
    because evidence-vs-evidence disagreement is checked too, by design.)"""
    d = consistency_release(tmpdir("relmc_absent_"),
                            manifest_erc="ERC clean")
    # strip the bom line-count claim too
    mt = (d / "MANIFEST.txt").read_text().replace(
        "bom_source_check PASS (49 lines, every LCSC == source)",
        "bom_source_check PASS (every LCSC == source)")
    (d / "MANIFEST.txt").write_text(mt)
    r = must_pass(gate(d), "unstated counts are not checked")
    not_contains(r.out, "MISMATCH", "no finding without a stated count")


@test("manifest-consistency: an errors-only erc.json (included_severities "
      "without 'warning') is NO evidence about warnings — cooksense-v1.0 "
      "shape must not false-positive")
def t_mc_errors_only_ercjson():
    """cooksense v1.0 ships erc.json run with --severity-error: 0 recorded
    warnings there is an artifact of the run scope, not a measurement. The
    audit's 978-warning statement must not be 'contradicted' by it."""
    d = consistency_release(tmpdir("relmc_erronly_"),
                            manifest_erc="ERC 0 errors",
                            audit_erc="0 errors (978 warnings)",
                            erc_json_warnings=0, erc_included=("error",))
    r = must_pass(gate(d), "errors-only erc.json is not warning evidence")
    not_contains(r.out, "MISMATCH", "no false mismatch")


@test("manifest-consistency: evidence referencing an EXISTING sibling "
      "release (diff vs a real predecessor) is legitimate, not flagged")
def t_mc_sibling_reference_ok():
    """cooksense v1.1's semantic_battery diffs its netlist against the
    sealed v1.0 by path. A reference to a release dir that EXISTS is a
    legitimate cross-release measurement, not a staging-path defect."""
    root = tmpdir("relmc_sib_")
    (root / "demoboard-v0.9-2026-07-20").mkdir(parents=True)
    d = consistency_release(root)
    (d / "verification" / "semantic_battery.txt").write_text(
        "netlist diff vs 07_releases/demoboard-v0.9-2026-07-20/source/"
        "demo.net: IDENTICAL\n")
    r = must_pass(gate(d), "existing-sibling reference is legitimate")
    not_contains(r.out, "PATH MISMATCH", "no finding for a real sibling")


if __name__ == "__main__":
    main()
