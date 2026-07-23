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

Fixtures are SELF-CONTAINED synthetic release trees built in a tmpdir (the
sealed real releases are immutable and never written). Each known-bad fixture
breaks exactly ONE of the three, so the test proves the gate reacts to THAT
defect. RED-VERIFY: every known-bad case is re-run with that one check
neutered (`--_disable-*`) and shown to PASS — proving the finding comes from
the check under test and nothing else. A gate that cannot fail is worthless.
"""
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


if __name__ == "__main__":
    main()
