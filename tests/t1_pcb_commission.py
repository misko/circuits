#!/usr/bin/env python3
"""T1: executable, no-merge commissioning for the pcb-design skill."""
from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (ROOT, KPY, check, contains, eq, main, must_fail,  # noqa: E402
                     must_pass, run, test, tmpdir)


COMMISSION = ROOT / "skills/pcb-design/scripts/commission_project.py"
TEMPLATES = ROOT / "skills/pcb-design/templates"
ENCLOSURE_ASSETS = ROOT / "skills/pcb-enclosure/assets"
BRIEF_BEGIN = "<!-- prompt-verbatim-begin -->"
BRIEF_END = "<!-- prompt-verbatim-end -->"


def invoke(
    projects_root: Path,
    brief: Path,
    *,
    name: str = "fresh-board",
    extra: tuple[str, ...] = (),
):
    return run([
        KPY,
        COMMISSION,
        "--projects-root", projects_root,
        "--name", name,
        "--brief-file", brief,
        *extra,
    ], cwd=ROOT, env={"SOURCE_DATE_EPOCH": "1787713200", "TZ": "UTC"})


def paths_below(root: Path) -> set[str]:
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() or path.is_symlink()
    }


def file_snapshot(root: Path) -> dict[str, tuple[bytes, int]]:
    return {
        path.relative_to(root).as_posix(): (
            path.read_bytes(), stat.S_IMODE(path.lstat().st_mode))
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def expected_paths(*, foreign_mating: bool, enclosure: bool) -> set[str]:
    expected: set[str] = set()
    contract_root = TEMPLATES / "contracts"
    for source in contract_root.rglob("*"):
        if not source.is_file():
            continue
        relative = source.relative_to(contract_root)
        if relative == Path("03_src/mechanical/contracts.md") and not enclosure:
            continue
        destination = "contracts.md" if relative == Path("ROOT.contracts.md") else relative.as_posix()
        expected.add(destination)
    for template_root, destination_root in (
        (TEMPLATES / "01_docs", Path("01_docs")),
        (TEMPLATES / "03_src", Path("03_src")),
    ):
        for source in template_root.rglob("*"):
            if not source.is_file():
                continue
            relative = source.relative_to(template_root)
            if (template_root.name == "03_src" and
                    relative == Path("rules/mates.yaml") and not foreign_mating):
                continue
            expected.add((destination_root / relative).as_posix())
    expected.update({
        ".gitignore",
        "README.md",
        "01_docs/capability-profile.json",
        "01_docs/COMMISSIONING-HOLD.md",
    })
    if enclosure:
        expected.update({
            "03_src/mechanical/mechanical-intent-v2.yaml",
            "07_enclosure_releases/contracts.md",
        })
    return expected


def write_brief(directory: Path, data: bytes) -> Path:
    brief = directory / "commission.txt"
    brief.write_bytes(data)
    return brief


@test("ordinary commission preserves UTF-8 prompt bytes, hash, and deterministic tree")
def t_ordinary_deterministic():
    base = tmpdir("pcb-commission-clean-")
    brief_bytes = "Build a café sensor.\r\nKeep ΔT visible.\r\n".encode("utf-8")
    brief = write_brief(base, brief_bytes)
    roots = [base / "projects-a", base / "projects-b"]
    for root in roots:
        root.mkdir()

    first = must_pass(invoke(roots[0], brief), "first ordinary commission")
    second = must_pass(invoke(roots[1], brief), "repeat ordinary commission")
    eq(first.out, second.out, "deterministic command output")
    contains(first.out, "PCB-SCAFFOLD OK name=fresh-board", "success output")
    contains(first.out, "stage=PCB-COMMISSION status=INCOMPLETE",
             "honest scaffold boundary")
    contains(first.out, "target=KICAD-LAYOUT-SEAL", "resolved router target")

    project_a = roots[0] / "fresh-board"
    project_b = roots[1] / "fresh-board"
    eq(file_snapshot(project_a), file_snapshot(project_b),
       "deterministic scaffold bytes and modes")
    eq(paths_below(project_a), expected_paths(foreign_mating=False, enclosure=False),
       "ordinary template census")
    check(not (project_a / "03_src/rules/mates.yaml").exists(),
          "ordinary project received a foreign-mating declaration")
    check(not (project_a / "03_src/mechanical").exists(),
          "ordinary project received enclosure source")

    profile = {
        "schema": 1,
        "signal_integrity": "ordinary",
        "assembly": "jlcpcb",
        "firmware": "forbidden",
        "foreign_mating": False,
        "target": "design",
    }
    eq((project_a / "01_docs/capability-profile.json").read_bytes(),
       (json.dumps(profile, indent=2) + "\n").encode(),
       "exact schema-1 capability profile")

    rendered = (project_a / "01_docs/BRIEF.md").read_bytes()
    opener = (BRIEF_BEGIN + "\n").encode()
    closer = ("\n" + BRIEF_END).encode()
    check(rendered.count(opener) == 1 and rendered.count(closer) == 1,
          "rendered BRIEF marker pair is not unique")
    preserved = rendered.split(opener, 1)[1].split(closer, 1)[0]
    eq(preserved, brief_bytes, "verbatim commissioning prompt bytes")
    digest = hashlib.sha256(brief_bytes).hexdigest().encode()
    check(b"prompt_sha256: " + digest in rendered, "BRIEF prompt hash is wrong")

    hold = project_a / "01_docs/COMMISSIONING-HOLD.md"
    contains(hold.read_text(), "schema examples—not adopted product facts",
             "commission hold explains seeded values")
    contains(hold.read_text(), "conductor-enforced stop marker",
             "commission hold names its actual enforcement mechanism")
    contains(hold.read_text(),
             "PCB-COMMISSION` → `PCB-ARCHITECTURE` → `PCB-SOURCING",
             "commission hold names its combined early admission span")
    status = (project_a / "01_docs/STATUS.md").read_text()
    contains(status, "state:   blocked", "commission status is held")
    contains(status, "PCB-COMMISSION INCOMPLETE", "commission status is honest")
    contains(status, "updated: 2026-08-26T03:00:00",
             "commission status has a reproducible real timestamp")
    for driver in ("rebuild_all.sh", "rebuild_reuse.sh"):
        check((project_a / "03_src" / driver).stat().st_mode & stat.S_IXUSR,
              f"{driver} is not executable in the commissioned scaffold")
        driver_text = (project_a / "03_src" / driver).read_text()
        contains(driver_text,
                 "${CIRCUITS_ROOT:-}",
                 f"{driver} honors the documented external-checkout override")
        check(".claude/skills" not in driver_text,
              f"{driver} silently falls back from the selected circuits checkout")
        blocked = must_fail(
            run(["bash", f"03_src/{driver}"], cwd=project_a),
            f"{driver} commission hold",
            expect="GATE INCOMPLETE [PCB-COMMISSION]",
        )
        eq(blocked.rc, 2, f"{driver} hold exit")

    # Once commission is admitted, an explicit checkout path remains
    # authoritative. A bad value must fail before any seeded board producer;
    # silently substituting an installed/global skill would make the same
    # scaffold execute different code on two machines.
    (project_b / "01_docs/COMMISSIONING-HOLD.md").unlink()
    invalid_root = base / "not-circuits"
    invalid_root.mkdir()
    for driver in ("rebuild_all.sh", "rebuild_reuse.sh"):
        refused = must_fail(
            run(["bash", f"03_src/{driver}"], cwd=project_b,
                env={"CIRCUITS_ROOT": str(invalid_root)}),
            f"{driver} invalid explicit circuits checkout",
            expect="does not contain skills/kicad-pcb",
        )
        eq(refused.rc, 2, f"{driver} invalid CIRCUITS_ROOT exit")

    for path in project_a.rglob("*"):
        check(not path.is_symlink(), f"scaffold contains a symlink: {path}")
        check(path.is_dir() or path.is_file(), f"scaffold contains a special path: {path}")


@test("RF enclosure and foreign mating seed their exact conditional authorities")
def t_rf_enclosure_mating():
    base = tmpdir("pcb-commission-rf-")
    projects = base / "projects"
    projects.mkdir()
    brief = write_brief(base, b"Make an RF board with a derived enclosure.")
    result = must_pass(invoke(projects, brief, extra=(
        "--signal-integrity", "rf",
        "--assembly", "jlcpcb",
        "--firmware", "requested",
        "--target", "release",
        "--foreign-mating",
        "--enclosure",
    )), "RF enclosure commission")
    contains(result.out, "target=PCB-RELEASE-SEAL", "resolved release target")
    project = projects / "fresh-board"
    eq(paths_below(project), expected_paths(foreign_mating=True, enclosure=True),
       "conditional template census")
    eq((project / "03_src/rules/mates.yaml").read_bytes(),
       (TEMPLATES / "03_src/rules/mates.yaml").read_bytes(), "mates schema seed")
    eq((project / "03_src/mechanical/contracts.md").read_bytes(),
       (TEMPLATES / "contracts/03_src/mechanical/contracts.md").read_bytes(),
       "mechanical source contract")
    eq((project / "03_src/mechanical/mechanical-intent-v2.yaml").read_bytes(),
       (ENCLOSURE_ASSETS / "mechanical-intent.template.yaml").read_bytes(),
       "mechanical intent authority")
    eq((project / "07_enclosure_releases/contracts.md").read_bytes(),
       (ENCLOSURE_ASSETS / "enclosure-release.contracts.md").read_bytes(),
       "independent enclosure release contract")
    eq(json.loads((project / "01_docs/capability-profile.json").read_text()), {
        "schema": 1,
        "signal_integrity": "rf",
        "assembly": "jlcpcb",
        "firmware": "requested",
        "foreign_mating": True,
        "target": "release",
    }, "RF capability profile")


@test("unsupported non-JLC profile creates nothing", kind="known_bad")
def t_invalid_profile():
    base = tmpdir("pcb-commission-profile-bad-")
    projects = base / "projects"
    projects.mkdir()
    brief = write_brief(base, b"Release this board.")
    must_fail(invoke(projects, brief, extra=("--assembly", "none")),
              "non-JLC executable scaffold", expect="invalid choice")
    check(not (projects / "fresh-board").exists(),
          "mismatched conductor profile left a destination")


@test("enclosure authority mode is never accepted then discarded", kind="known_bad")
def t_enclosure_mode_not_silently_discarded():
    base = tmpdir("pcb-commission-enclosure-mode-bad-")
    projects = base / "projects"
    projects.mkdir()
    brief = write_brief(base, b"A board with a future enclosure.")
    must_fail(invoke(projects, brief, extra=("--enclosure", "derived")),
              "premature enclosure authority mode",
              expect="provide the project slug positionally or with --name")
    check(not (projects / "fresh-board").exists(),
          "discarded enclosure mode left a destination")


@test("existing destination is never merged or overwritten", kind="known_bad")
def t_existing_destination():
    base = tmpdir("pcb-commission-existing-")
    projects = base / "projects"
    destination = projects / "fresh-board"
    destination.mkdir(parents=True)
    sentinel = destination / "user-data.txt"
    sentinel.write_bytes(b"do not touch\n")
    brief = write_brief(base, b"A board.")
    must_fail(invoke(projects, brief), "existing project commission",
              expect="destination already exists")
    eq(paths_below(destination), {"user-data.txt"}, "existing destination census")
    eq(sentinel.read_bytes(), b"do not touch\n", "existing destination content")


@test("symlink projects roots and destinations fail closed", kind="known_bad")
def t_symlink_boundaries():
    base = tmpdir("pcb-commission-symlink-")
    real_projects = base / "real-projects"
    real_projects.mkdir()
    linked_projects = base / "linked-projects"
    linked_projects.symlink_to(real_projects, target_is_directory=True)
    brief = write_brief(base, b"A board.")
    must_fail(invoke(linked_projects, brief), "symlink projects root",
              expect="symlink path component is forbidden")
    check(not (real_projects / "fresh-board").exists(),
          "symlink root was followed")

    outside = base / "outside"
    outside.mkdir()
    sentinel = outside / "sentinel"
    sentinel.write_bytes(b"outside\n")
    (real_projects / "fresh-board").symlink_to(outside, target_is_directory=True)
    must_fail(invoke(real_projects, brief), "symlink destination",
              expect="destination already exists")
    eq(paths_below(outside), {"sentinel"}, "symlink destination target census")
    eq(sentinel.read_bytes(), b"outside\n", "symlink destination target content")


@test("template census excludes only declared conditional and coordinator files")
def t_template_census():
    base = tmpdir("pcb-commission-census-")
    brief = write_brief(base, b"Census board.")
    ordinary_root = base / "ordinary"
    complete_root = base / "complete"
    ordinary_root.mkdir()
    complete_root.mkdir()
    must_pass(invoke(ordinary_root, brief, name="census-board"), "ordinary census")
    must_pass(invoke(complete_root, brief, name="census-board",
                     extra=("--foreign-mating", "--enclosure")), "full census")
    ordinary = paths_below(ordinary_root / "census-board")
    complete = paths_below(complete_root / "census-board")
    eq(ordinary, expected_paths(foreign_mating=False, enclosure=False),
       "ordinary current-template census")
    eq(complete, expected_paths(foreign_mating=True, enclosure=True),
       "full current-template census")
    eq(complete - ordinary, {
        "03_src/rules/mates.yaml",
        "03_src/mechanical/contracts.md",
        "03_src/mechanical/mechanical-intent-v2.yaml",
        "07_enclosure_releases/contracts.md",
    }, "conditional-only scaffold paths")
    readme = (complete_root / "census-board/README.md").read_text()
    contains(readme, "PCB commissioning scaffold", "honest project heading")
    contains(readme, "01_docs/capability-profile.json", "project navigation README")
    contains(readme, "--at-stage PCB-COMMISSION", "stage-local router command")
    contains(readme, "export CIRCUITS_ROOT=", "persistent external-checkout authority")
    contains(readme, "--resume-after-schematic-review",
             "truthful full-conductor resume path")
    check("+  --profile" not in readme, "patch marker leaked into router command")
    check("bash 03_src/rebuild_all.sh\n```" not in readme,
          "generated README tells a scaffold to rebuild immediately")
    start_block = readme.split("```bash\n", 1)[1].split("\n```", 1)[0]
    routed = must_pass(
        run(["bash", "-c", start_block],
            cwd=complete_root / "census-board",
            env={"CIRCUITS_ROOT": str(ROOT)}),
        "generated project README router command",
    )
    contains(routed.out, '"authority": "DISCLOSURE_ONLY"',
             "generated README router authority")
    check("ORCHESTRATION_STATE.md" not in complete,
          "campaign coordinator state leaked into one board")


if __name__ == "__main__":
    sys.exit(main())
