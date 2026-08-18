#!/usr/bin/env python3
"""T1: publication cannot bypass sealing and exact-artifact reviews."""
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (ROOT, check, contains, main, must_fail, must_pass, run,
                     test, tmpdir)  # noqa: E402

PUB = ROOT / "skills" / "pcb-design" / "scripts" / "pcb_publication_gate.py"
sys.path.insert(0, str(PUB.parent))
import pcb_publication_gate as pg  # noqa: E402

HEAD_SHA = subprocess.check_output(
    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


@test("publication diff selection grades source, release, and review claims "
      "while ignoring status bookkeeping")
def t_diff_selection_is_semantic():
    paths = [
        "projects/demo/03_src/route.py",
        "projects/demo/01_docs/STATUS.md",
        "projects/demo/08_reviews/redteam.md",
        "projects/demo/07_releases/v1.0/MANIFEST.txt",
        "projects/other/02_parts/U1/part.yaml",
        "skills/pcb-design/SKILL.md",
    ]
    check(pg.affected_projects(paths) ==
          ["projects/demo", "projects/other"],
          f"wrong affected-project set: {pg.affected_projects(paths)}")
    for material in (
            "projects/x/01_docs/BRIEF.md",
            "projects/x/01_docs/decisions/0001.md",
            "projects/x/03_tscircuit/src/board.tsx",
            "projects/x/04_kicad/x.kicad_pcb",
            "projects/x/07_releases/v1.0/MANIFEST.txt",
            "projects/x/08_reviews/redteam_layout.md"):
        check(pg.is_material_project_path(material),
              f"material path escaped selection: {material}")
    check(not pg.is_material_project_path("projects/x/01_docs/STATUS.md"),
          "STATUS bookkeeping incorrectly triggered publication")


@test("release-only and review-only diffs cannot earn a zero-project pass",
      kind="known_bad")
def t_claim_only_diff_selects_project():
    for path in ("projects/release-only/07_releases/v2/MANIFEST.txt",
                 "projects/review-only/08_reviews/layout.md"):
        selected = pg.affected_projects([path])
        check(len(selected) == 1,
              f"claim-only path escaped the publication denominator: {path}")


@test("the real RX2 v4 release is explicitly stale after material pipeline "
      "source changed", kind="known_bad")
def t_real_release_stales_after_pipeline_adoption():
    r = must_fail(run([sys.executable, PUB, "--project",
                       "projects/pluto-rx2-8way-v4"]),
                  "stale reviewed RX2 publication", "STALE-RELEASE")
    contains(r.out, "1 project(s), 1 board(s) graded", "coverage denominator")
    contains(r.out, "03_src/route.yaml", "material source diagnosis")


@test("an unsealed board cannot be published even when DRC/parity are green",
      kind="known_bad")
def t_unsealed_hub_is_refused():
    # The real programmable hub eventually seals; pin this property to a
    # deliberately release-less project so success cannot make the regression
    # fixture stale. The gate exits at NO-RELEASE before invoking child tools.
    d = tmpdir("pub_unsealed_")
    (d / ".git").mkdir()
    board_dir = d / "projects" / "unsealed-demo" / "04_kicad"
    board_dir.mkdir(parents=True)
    (board_dir / "unsealed_demo.kicad_pcb").write_text("(kicad_pcb)\n")
    r = must_fail(run([sys.executable, PUB, "--root", d, "--project",
                       "projects/unsealed-demo"]),
                  "deliberately unsealed board", expect="NO-RELEASE")
    contains(r.out, "1 project(s), 1 board(s) graded", "coverage denominator")


@test("mutable rehearsal cannot borrow a release from another project",
      kind="known_bad")
def t_staging_release_scope_is_refused():
    root = tmpdir("pub_release_scope_")
    project = root / "projects/demo"
    board = project / "04_kicad/demo.kicad_pcb"
    board.parent.mkdir(parents=True)
    board.write_text("(kicad_pcb)\n")
    foreign = root / "projects/other/06_build/release_staging/v1"
    foreign.mkdir(parents=True)
    errors, selected = pg.grade_board(
        project, board, "HEAD", root, False, foreign)
    check(selected == foreign.resolve(), "scope refusal lost the supplied subject")
    contains("\n".join(errors), "RELEASE-SCOPE", "cross-project diagnosis")


def _review_text(project, board_hash):
    return (f"subject: {project}\n"
            "design_verdict: SOUND\n"
            f"source_commit: {HEAD_SHA}\n"
            f"board_sha256: {board_hash}\n")


@test("all four publication reviews bind the exact board and are archived")
def t_review_binding_clean():
    d = tmpdir("pubreview_")
    project = d / "projects" / "demo-board"
    release = project / "07_releases" / "v1.0-2026-08-01"
    (release / "verification").mkdir(parents=True)
    (project / "08_reviews").mkdir(parents=True)
    board_hash = "a" * 64
    for name in pg.REQUIRED_REVIEWS:
        text = _review_text(project.name, board_hash)
        (release / "verification" / name).write_text(text)
        shutil.copy2(release / "verification" / name,
                     project / "08_reviews" / name)
    errors = pg.review_binding_errors(
        project, release, board_hash, "HEAD", ROOT)
    check(not errors, f"clean exact-artifact reviews were refused: {errors}")


@test("a review of adjacent board bytes or an unarchived review is refused",
      kind="known_bad")
def t_review_binding_mismatch_is_refused():
    d = tmpdir("pubreview_bad_")
    project = d / "projects" / "demo-board"
    release = project / "07_releases" / "v1.0-2026-08-01"
    (release / "verification").mkdir(parents=True)
    (project / "08_reviews").mkdir(parents=True)
    board_hash = "a" * 64
    for name in pg.REQUIRED_REVIEWS:
        text = _review_text(project.name, board_hash)
        (release / "verification" / name).write_text(text)
        shutil.copy2(release / "verification" / name,
                     project / "08_reviews" / name)
    bad = release / "verification" / "redteam_layout.md"
    bad.write_text(_review_text(project.name, "b" * 64))
    errors = pg.review_binding_errors(
        project, release, board_hash, "HEAD", ROOT)
    joined = "\n".join(errors)
    contains(joined, "REVIEW-BINDING", "wrong-artifact finding")
    contains(joined, "REVIEW-ARCHIVE", "unarchived-review finding")


@test("publication replays a declared docs-only predecessor through the "
      "strong freshness mode")
def t_docs_only_freshness_mode_is_composed():
    d = tmpdir("pub_docs_only_")
    releases = d / "07_releases"
    prior = releases / "v1.0-2026-08-01"
    current = releases / "v1.1-2026-08-02"
    prior.mkdir(parents=True)
    current.mkdir()
    errors, args = pg._freshness_args(
        {"release_mode": "docs-only", "supersedes": prior.name}, current)
    check(not errors, f"valid docs-only declaration refused: {errors}")
    check(args[:3] == ["--claim", "design", "--docs-only-supersede"],
          f"wrong freshness mode argv: {args}")
    check(Path(args[3]) == prior, f"wrong predecessor path: {args[3]}")


@test("publication fails closed on a docs-only declaration with no existing "
      "predecessor", kind="known_bad")
def t_docs_only_missing_predecessor_is_refused():
    d = tmpdir("pub_docs_only_bad_")
    current = d / "07_releases" / "v1.1-2026-08-02"
    current.mkdir(parents=True)
    errors, args = pg._freshness_args(
        {"release_mode": "docs-only", "supersedes": "v1.0-2026-08-01"},
        current)
    check(not args, f"bad declaration still produced gate argv: {args}")
    contains("\n".join(errors), "FRESHNESS-PREDECESSOR",
             "missing predecessor diagnosis")


if __name__ == "__main__":
    sys.exit(main())
