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


if __name__ == "__main__":
    sys.exit(main())
