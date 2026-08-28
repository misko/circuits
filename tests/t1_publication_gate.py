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


@test("publication CI watches both active and frozen project collections")
def t_workflow_watches_project_collections():
    workflow = (ROOT / ".github" / "workflows" /
                "pcb-publication-gate.yml").read_text(encoding="utf-8")
    check(workflow.count('- "projects/**"') == 2,
          "publication workflow must watch active projects on PR and push")
    check(workflow.count('- "archived_projects/**"') == 2,
          "publication workflow must watch frozen archives on PR and push")


@test("publication diff selection separates enclosure work while grading PCB "
      "source, release, and review claims")
def t_diff_selection_is_semantic():
    paths = [
        "projects/demo/03_src/route.py",
        "projects/demo/03_src/mechanical/case.scad",
        "projects/demo/07_enclosure_releases/v2/meshes/base.stl",
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
    for enclosure in (
            "projects/x/03_src/mechanical/case.scad",
            "projects/x/03_src/mechanical/reference/board.step",
            "projects/x/07_enclosure_releases/contracts.md",
            "projects/x/07_enclosure_releases/v2/MANIFEST.json"):
        check(pg.classify_project_path(enclosure) == pg.PATH_ENCLOSURE_ONLY,
              f"enclosure path was not isolated from PCB grading: {enclosure}")
        check(not pg.is_material_project_path(enclosure),
              f"enclosure path incorrectly triggered PCB grading: {enclosure}")
    check(pg.enclosure_only_projects(paths) == ["projects/demo"],
          f"wrong enclosure-project set: {pg.enclosure_only_projects(paths)}")


@test("enclosure exemption is exact and electrical, PCB, fab-release, and "
      "review paths remain material")
def t_enclosure_classifier_is_fail_closed():
    for material in (
            "projects/x/03_src/mechanical-electrical/route.yaml",
            "projects/x/03_src/contracts.md",
            "projects/x/03_src/route.yaml",
            "projects/x/03_src/rules/connector_assemblies.yaml",
            "projects/x/03_src/rules/contracts.md",
            "projects/x/03_src/rules/nets.yaml",
            "projects/x/03_src/rules/rf.yaml",
            "projects/x/03_src/rules/connector_assemblies.yaml.bak",
            "projects/x/03_src/rules/connector_assemblies/nets.yaml",
            "projects/x/03_src/lib/rf.pretty/J1.kicad_mod",
            "projects/x/04_kicad/x.kicad_pcb",
            "projects/x/07_releases/v2/MANIFEST.txt",
            "projects/x/08_reviews/DISPOSITIONS.md",
            "projects/x/08_reviews/2026-08-27_connector-service_first-article.md.bak",
            "projects/x/08_reviews/2026-08-27_connector-service_first-article-and-routing.md",
            "projects/x/08_reviews/redteam_layout.md"):
        check(pg.classify_project_path(material) == pg.PATH_PCB_MATERIAL,
              f"material near/mixed path escaped PCB grading: {material}")


@test("release-only and review-only diffs cannot earn a zero-project pass",
      kind="known_bad")
def t_claim_only_diff_selects_project():
    for path in ("projects/release-only/07_releases/v2/MANIFEST.txt",
                 "projects/review-only/08_reviews/layout.md"):
        selected = pg.affected_projects([path])
        check(len(selected) == 1,
              f"claim-only path escaped the publication denominator: {path}")


def _commit(repo, message):
    must_pass(run(["git", "add", "-A"], cwd=repo), f"stage {message}")
    must_pass(run(["git", "commit", "-q", "-m", message], cwd=repo),
              f"commit {message}")
    return must_pass(run(["git", "rev-parse", "HEAD"], cwd=repo),
                     f"resolve {message}").out.strip()


def _enclosure_diff_repo(*, add_electrical=False):
    root = tmpdir("pub_enclosure_")
    must_pass(run(["git", "init", "-q"], cwd=root), "init enclosure fixture")
    must_pass(run(["git", "config", "user.email", "tests@example.invalid"],
                  cwd=root), "configure fixture email")
    must_pass(run(["git", "config", "user.name", "Publication Gate Tests"],
                  cwd=root), "configure fixture name")
    project = root / "projects" / "demo"
    (project / "README.md").parent.mkdir(parents=True)
    (project / "README.md").write_text("# demo\n")
    base = _commit(root, "base")

    mechanical = project / "03_src" / "mechanical"
    mechanical.mkdir(parents=True)
    (mechanical / "case.scad").write_text("cube([1, 1, 1]);\n")
    release = project / "07_enclosure_releases" / "v1.0-2026-08-26"
    release.mkdir(parents=True)
    (release / "MANIFEST.json").write_text("{}\n")
    if add_electrical:
        rules = project / "03_src" / "rules"
        rules.mkdir(parents=True)
        (rules / "rf.yaml").write_text("impedance_ohms: 50\n")
    head = _commit(root, "candidate")
    return root, base, head


def _connector_bundle_repo(*, missing_contract=False, extra_contract=False,
                           near_prefix=False, mixed_material=False,
                           preexisting_authority=False, contract_mode_drift=False):
    root = tmpdir("pub_connector_bundle_")
    must_pass(run(["git", "init", "-q"], cwd=root),
              "init connector bundle fixture")
    must_pass(run(["git", "config", "user.email", "tests@example.invalid"],
                  cwd=root), "configure fixture email")
    must_pass(run(["git", "config", "user.name", "Publication Gate Tests"],
                  cwd=root), "configure fixture name")
    project = root / "projects" / "demo"
    rules = project / "03_src" / "rules"
    rules.mkdir(parents=True)
    contract = rules / "contracts.md"
    contract.write_text(
        "# child contract\n\n| File | What |\n|---|---|\n"
        "| `contracts.md` | this file |\n")
    connector = rules / "connector_assemblies.yaml"
    if preexisting_authority:
        connector.write_text("schema: 1\nassemblies: [old]\n")
    base = _commit(root, "base connector child contract")

    connector.write_text("schema: 1\nassemblies: []\n")
    if not missing_contract:
        canonical = sorted(pg.CANONICAL_CONNECTOR_CONTRACT_ROWS)[0]
        contract.write_text(contract.read_text().replace(
            "| `contracts.md` | this file |\n",
            canonical + "\n| `contracts.md` | this file |\n"))
        if extra_contract:
            contract.write_text(contract.read_text() +
                                "electrical policy changed too\n")
        if contract_mode_drift:
            contract.chmod(0o755)
    if near_prefix:
        (rules / "connector_assemblies.yaml.bak").write_text(
            "electrical: true\n")
    if mixed_material:
        (project / "03_src" / "route.yaml").write_text("schema: 1\n")
        (rules / "nets.yaml").write_text("classes: []\n")
        reviews = project / "08_reviews"
        reviews.mkdir()
        (reviews / "DISPOSITIONS.md").write_text("# generic ledger\n")
    head = _commit(root, "connector bundle candidate")
    return root, base, head


def _cross_domain_rename_repo(*, commit=True):
    root = tmpdir("pub_enclosure_rename_")
    must_pass(run(["git", "init", "-q"], cwd=root), "init rename fixture")
    must_pass(run(["git", "config", "user.email", "tests@example.invalid"],
                  cwd=root), "configure fixture email")
    must_pass(run(["git", "config", "user.name", "Publication Gate Tests"],
                  cwd=root), "configure fixture name")
    project = root / "projects" / "demo"
    electrical = project / "03_src" / "rules" / "rf.yaml"
    electrical.parent.mkdir(parents=True)
    electrical.write_text("impedance_ohms: 50\n")
    base = _commit(root, "base")

    mechanical = project / "03_src" / "mechanical"
    mechanical.mkdir(parents=True)
    shutil.move(electrical, mechanical / electrical.name)
    head = (_commit(root, "move electrical source into mechanical")
            if commit else None)
    return root, base, head


@test("an exact enclosure-only diff does not require PCB reseal or RF build")
def t_enclosure_only_diff_bypasses_pcb_denominator():
    root, base, head = _enclosure_diff_repo()
    drift = pg._material_changes_since(
        base, head, "projects/demo", root)
    check(not drift,
          f"enclosure-only source incorrectly made PCB release stale: {drift}")
    r = must_pass(run([sys.executable, PUB, "--root", root,
                       "--base", base, "--head", head]),
                  "enclosure-only publication classification")
    contains(r.out, "2 enclosure-only path(s) across 1 project(s)",
             "explicit enclosure coverage")
    contains(r.out, "outside the PCB reseal/RF-build denominator",
             "independent release-stream diagnosis")


@test("an enclosure diff cannot launder a simultaneous electrical change",
      kind="known_bad")
def t_enclosure_diff_does_not_launder_electrical_change():
    root, base, head = _enclosure_diff_repo(add_electrical=True)
    drift = pg._material_changes_since(
        base, head, "projects/demo", root)
    check(drift == ["projects/demo/03_src/rules/rf.yaml"],
          f"mixed drift classifier lost the electrical source: {drift}")
    r = must_fail(run([sys.executable, PUB, "--root", root,
                       "--base", base, "--head", head]),
                  "mixed enclosure/electrical publication", "BOARD-COVERAGE")
    contains(r.out, "1 material project(s)", "PCB coverage denominator")
    contains(r.out, "2 enclosure-only path(s) across 1 project(s)",
             "independent enclosure accounting")


@test("an exact connector authority plus canonical child-contract row is "
      "enclosure governance only")
def t_exact_connector_contract_bundle_is_enclosure_only():
    root, base, head = _connector_bundle_repo()
    r = must_pass(run([sys.executable, PUB, "--root", root,
                       "--base", base, "--head", head]),
                  "exact connector governance bundle")
    contains(r.out, "2 enclosure-only path(s) across 1 project(s)",
             "paired connector bundle accounting")
    contains(r.out, "0 PCB project(s), 0 board(s) graded",
             "connector bundle stays outside PCB denominator")


@test("mechanical connector bundle cannot launder simultaneous electrical "
      "source or generic review changes", kind="known_bad")
def t_connector_contract_diff_does_not_launder_material_changes():
    root, base, head = _connector_bundle_repo(mixed_material=True)
    r = must_fail(run([sys.executable, PUB, "--root", root,
                       "--base", base, "--head", head]),
                  "mixed connector/electrical publication", "BOARD-COVERAGE")
    contains(r.out, "1 material project(s)", "PCB coverage denominator")
    contains(r.out, "2 enclosure-only path(s) across 1 project(s)",
             "mechanical connector accounting")


@test("connector allowance rejects missing siblings, extra contract bytes, "
      "and near-prefix paths", kind="known_bad")
def t_connector_contract_bundle_is_exact_and_fail_closed():
    fixtures = (
        ("missing child-contract delta", {"missing_contract": True}),
        ("extra child-contract byte", {"extra_contract": True}),
        ("near-prefix sibling", {"near_prefix": True}),
        ("pre-existing authority mutation", {"preexisting_authority": True}),
        ("child-contract mode drift", {"contract_mode_drift": True}),
    )
    for label, kwargs in fixtures:
        root, base, head = _connector_bundle_repo(**kwargs)
        r = must_fail(run([sys.executable, PUB, "--root", root,
                           "--base", base, "--head", head]),
                      label, "BOARD-COVERAGE")
        contains(r.out, "1 material project(s)", f"{label} PCB selection")


@test("moving electrical source into the enclosure subtree cannot launder its "
      "deletion", kind="known_bad")
def t_cross_domain_rename_is_fail_closed():
    root, base, head = _cross_domain_rename_repo()
    drift = pg._material_changes_since(base, head, "projects/demo", root)
    check(drift == ["projects/demo/03_src/rules/rf.yaml"],
          f"rename lost the deleted electrical source: {drift}")
    r = must_fail(run([sys.executable, PUB, "--root", root,
                       "--base", base, "--head", head]),
                  "cross-domain committed rename", "BOARD-COVERAGE")
    contains(r.out, "1 material project(s)", "PCB coverage denominator")
    contains(r.out, "1 enclosure-only path(s) across 1 project(s)",
             "renamed enclosure destination accounting")


@test("an uncommitted cross-domain rename remains dirty PCB material")
def t_worktree_cross_domain_rename_is_material():
    root, _, _ = _cross_domain_rename_repo(commit=False)
    changed = pg._working_material_changes("projects/demo", root)
    check(changed == ["projects/demo/03_src/rules/rf.yaml"],
          f"worktree rename lost deleted electrical source: {changed}")


@test("mutable rehearsal ignores only its exact candidate release tree")
def t_rehearsal_worktree_exception_is_exact():
    root = tmpdir("pub_rehearsal_worktree_")
    must_pass(run(["git", "init", "-q"], cwd=root),
              "init rehearsal worktree fixture")
    must_pass(run(["git", "config", "user.email", "tests@example.invalid"],
                  cwd=root), "configure fixture email")
    must_pass(run(["git", "config", "user.name", "Publication Gate Tests"],
                  cwd=root), "configure fixture name")
    project = root / "projects" / "demo"
    source = project / "03_src" / "rules" / "rf.yaml"
    predecessor = project / "07_releases" / "v1.0-2026-08-25"
    source.parent.mkdir(parents=True)
    predecessor.mkdir(parents=True)
    source.write_text("impedance_ohms: 50\n")
    (predecessor / "MANIFEST.txt").write_text("version: v1.0\n")
    _commit(root, "base")

    candidate_rel = "projects/demo/07_releases/v1.1-2026-08-26"
    candidate = root / candidate_rel
    candidate.mkdir()
    (candidate / "MANIFEST.txt").write_text("version: v1.1\n")
    # All three near/sibling paths must remain visible beside the one exact
    # output tree: predecessor metadata, a lexical near-prefix, and live RF.
    (predecessor / "SUPERSEDED.md").write_text("superseded\n")
    near = project / "07_releases" / "v1.1-2026-08-260"
    near.mkdir()
    (near / "MANIFEST.txt").write_text("near prefix\n")
    source.write_text("impedance_ohms: 55\n")

    changed = pg._working_material_changes(
        "projects/demo", root, ignored_new_prefixes=(candidate_rel,))
    check(candidate_rel + "/MANIFEST.txt" not in changed,
          f"exact candidate was not excluded: {changed}")
    expected = {
        "projects/demo/03_src/rules/rf.yaml",
        "projects/demo/07_releases/v1.0-2026-08-25/SUPERSEDED.md",
        "projects/demo/07_releases/v1.1-2026-08-260/MANIFEST.txt",
    }
    check(set(changed) == expected,
          f"candidate exception escaped its exact tree: {changed}")

    check(pg._mutable_release_output_prefix(
        "projects/demo", candidate, "HEAD", root) == candidate_rel,
        "new direct release candidate did not earn its exact output prefix")
    check(pg._mutable_release_output_prefix(
        "projects/demo", predecessor, "HEAD", root) is None,
        "tracked immutable predecessor incorrectly earned an output prefix")

    # Staged additive bytes remain the same pre-seal candidate output. A byte
    # modified again after staging is AM, not additive-only, and must surface.
    must_pass(run(["git", "add", candidate], cwd=root),
              "stage exact rehearsal candidate")
    staged = pg._working_material_changes(
        "projects/demo", root, ignored_new_prefixes=(candidate_rel,))
    check(candidate_rel + "/MANIFEST.txt" not in staged,
          f"staged additive candidate was not excluded: {staged}")
    (candidate / "MANIFEST.txt").write_text("version: v1.1-drift\n")
    modified_after_stage = pg._working_material_changes(
        "projects/demo", root, ignored_new_prefixes=(candidate_rel,))
    check(candidate_rel + "/MANIFEST.txt" in modified_after_stage,
          "modified-after-stage candidate byte escaped rehearsal dirt")


def _archive_repo(*, preexisting_archive=False, names=("demo",),
                  frozen_control=False):
    root = tmpdir("pub_archive_")
    must_pass(run(["git", "init", "-q"], cwd=root), "init archive fixture")
    must_pass(run(["git", "config", "user.email", "tests@example.invalid"],
                  cwd=root), "configure fixture email")
    must_pass(run(["git", "config", "user.name", "Publication Gate Tests"],
                  cwd=root), "configure fixture name")
    for name in names:
        active = root / "projects" / name
        (active / "03_src").mkdir(parents=True)
        (active / "03_src" / "route.yaml").write_text("schema: 1\n")
        rebuild = active / "03_src" / "rebuild.sh"
        rebuild.write_text("#!/bin/sh\nexit 0\n")
        rebuild.chmod(0o755)
        (active / "01_docs").mkdir()
        (active / "01_docs" / "STATUS.md").write_text("state: scaffold\n")
    active = root / "projects" / names[0]
    archived = root / "archived_projects" / names[0]
    if preexisting_archive:
        archived.mkdir(parents=True)
        (archived / "prior.txt").write_text("already reserved\n")
    if frozen_control:
        frozen = root / "archived_projects" / "frozen-control"
        frozen.mkdir(parents=True)
        (frozen / "receipt.txt").write_text("immutable\n")
    base = _commit(root, "base")
    if preexisting_archive:
        shutil.rmtree(archived)
    for name in names:
        source = root / "projects" / name
        destination = root / "archived_projects" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(source, destination)
    return root, base, active, archived


@test("an exact tracked project-tree relocation into the archive is allowed")
def t_exact_archive_relocation_is_allowed():
    root, base, _, _ = _archive_repo()
    head = _commit(root, "archive exact tree")
    r = must_pass(run([sys.executable, PUB, "--root", root,
                       "--base", base, "--head", head]),
                  "exact archive relocation")
    contains(r.out, "1 exact archive relocation(s)",
             "archive coverage denominator")
    contains(r.out, "tracked tree byte/mode identity proven",
             "archive identity evidence")


@test("multiple exact project-tree relocations are independently counted")
def t_multiple_exact_archive_relocations_are_allowed():
    root, base, _, _ = _archive_repo(names=("alpha", "beta"))
    head = _commit(root, "archive two exact trees")
    r = must_pass(run([sys.executable, PUB, "--root", root,
                       "--base", base, "--head", head]),
                  "two exact archive relocations")
    contains(r.out, "2 exact archive relocation(s)",
             "multi-archive coverage denominator")
    contains(r.out, "ARCHIVE projects/alpha -> archived_projects/alpha",
             "first independently proven move")
    contains(r.out, "ARCHIVE projects/beta -> archived_projects/beta",
             "second independently proven move")


@test("archive allowance rejects plain deletion, byte/mode drift, retained "
      "active trees, and overwritten destinations", kind="known_bad")
def t_inexact_archive_relocations_are_refused():
    fixtures = []

    root, base, _, archived = _archive_repo()
    (archived / "03_src" / "route.yaml").write_text("schema: 2\n")
    fixtures.append(("byte drift", root, base))

    root, base, _, archived = _archive_repo()
    (archived / "03_src" / "rebuild.sh").chmod(0o644)
    fixtures.append(("mode drift", root, base))

    root, base, active, _ = _archive_repo()
    (active / "03_src").mkdir(parents=True)
    (active / "03_src" / "residual.yaml").write_text("left: true\n")
    fixtures.append(("retained active tree", root, base))

    root, base, _, _ = _archive_repo(preexisting_archive=True)
    fixtures.append(("overwritten archive", root, base))

    root, base, _, archived = _archive_repo()
    shutil.rmtree(archived)
    fixtures.append(("plain deletion", root, base))

    for label, root, base in fixtures:
        head = _commit(root, f"hostile {label}")
        r = must_fail(run([sys.executable, PUB, "--root", root,
                           "--base", base, "--head", head]), label)
        check("1 exact archive relocation(s)" not in r.out,
              f"{label} incorrectly earned the archive allowance:\n{r.out}")
        contains(r.out, "ARCHIVE-", f"{label} archive diagnosis")


def _frozen_archive_repo():
    root = tmpdir("pub_frozen_archive_")
    must_pass(run(["git", "init", "-q"], cwd=root),
              "init frozen archive fixture")
    must_pass(run(["git", "config", "user.email", "tests@example.invalid"],
                  cwd=root), "configure fixture email")
    must_pass(run(["git", "config", "user.name", "Publication Gate Tests"],
                  cwd=root), "configure fixture name")
    frozen = root / "archived_projects" / "frozen"
    frozen.mkdir(parents=True)
    (frozen / "receipt.txt").write_text("immutable\n")
    replay = frozen / "replay.sh"
    replay.write_text("#!/bin/sh\nexit 0\n")
    replay.chmod(0o755)
    base = _commit(root, "frozen archive base")
    return root, base, frozen


@test("pre-existing archive mutation, deletion, and addition are refused",
      kind="known_bad")
def t_preexisting_archive_is_immutable():
    fixtures = []

    root, base, frozen = _frozen_archive_repo()
    (frozen / "receipt.txt").write_text("mutated\n")
    fixtures.append(("byte mutation", root, base))

    root, base, frozen = _frozen_archive_repo()
    (frozen / "replay.sh").chmod(0o644)
    fixtures.append(("mode mutation", root, base))

    root, base, frozen = _frozen_archive_repo()
    (frozen / "late.txt").write_text("not in the frozen tree\n")
    fixtures.append(("path addition", root, base))

    root, base, frozen = _frozen_archive_repo()
    shutil.rmtree(frozen)
    fixtures.append(("archive deletion", root, base))

    for label, root, base in fixtures:
        head = _commit(root, label)
        r = must_fail(run([sys.executable, PUB, "--root", root,
                           "--base", base, "--head", head]), label,
                      "ARCHIVE-IMMUTABILITY")
        contains(r.out, "archived_projects/frozen", f"{label} subject")


@test("an archive-only addition and a copy retaining the active tree are "
      "refused", kind="known_bad")
def t_unpaired_archive_additions_are_refused():
    root, base, _ = _frozen_archive_repo()
    orphan = root / "archived_projects" / "orphan" / "03_src"
    orphan.mkdir(parents=True)
    (orphan / "route.yaml").write_text("schema: 1\n")
    head = _commit(root, "archive-only addition")
    r = must_fail(run([sys.executable, PUB, "--root", root,
                       "--base", base, "--head", head]),
                  "archive-only addition", "ARCHIVE-IMMUTABILITY")
    contains(r.out, "archived_projects/orphan", "unpaired archive subject")

    root, base, active, archived = _archive_repo()
    shutil.copytree(archived, active)
    head = _commit(root, "copy while retaining active tree")
    r = must_fail(run([sys.executable, PUB, "--root", root,
                       "--base", base, "--head", head]),
                  "retained active copy", "ARCHIVE-IMMUTABILITY")
    contains(r.out, "0 exact archive relocation(s)",
             "retained active copy earns no relocation credit")


@test("an exact archive move cannot launder a frozen archive mutation",
      kind="known_bad")
def t_exact_move_does_not_launder_archive_mutation():
    root, base, _, _ = _archive_repo(frozen_control=True)
    frozen = root / "archived_projects" / "frozen-control" / "receipt.txt"
    frozen.write_text("mutated beside a valid move\n")
    head = _commit(root, "exact move plus frozen archive mutation")
    r = must_fail(run([sys.executable, PUB, "--root", root,
                       "--base", base, "--head", head]),
                  "mixed exact move and archive mutation",
                  "ARCHIVE-IMMUTABILITY")
    contains(r.out, "1 exact archive relocation(s)",
             "valid move remains counted")
    contains(r.out, "archived_projects/frozen-control",
             "independent frozen mutation subject")


@test("an exact archive move cannot hide another material project mutation",
      kind="known_bad")
def t_archive_relocation_does_not_launder_other_project_changes():
    root, base, _, _ = _archive_repo()
    other = root / "projects" / "other" / "03_src"
    other.mkdir(parents=True)
    (other / "route.yaml").write_text("schema: 1\n")
    head = _commit(root, "archive plus unrelated project mutation")
    r = must_fail(run([sys.executable, PUB, "--root", root,
                       "--base", base, "--head", head]),
                  "archive plus unrelated project mutation",
                  "BOARD-COVERAGE")
    contains(r.out, "1 exact archive relocation(s)",
             "valid archive move remains independently accounted")
    contains(r.out, "projects/other", "unlaundered project finding")


@test("an archived RX2 v4 project cannot be audited as a live project",
      kind="known_bad")
def t_archived_project_cannot_enter_live_audit():
    r = must_fail(run([sys.executable, PUB, "--project",
                       "projects/pluto-rx2-8way-v4"]),
                  "archived RX2 explicit publication", "PROJECT:")
    contains(r.out, "selected project directory is absent",
             "live-tree boundary diagnosis")


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


@test("publication replays a declared representation-only predecessor")
def t_representation_freshness_mode_is_composed():
    d = tmpdir("pub_representation_")
    releases = d / "07_releases"
    prior = releases / "v1.0-2026-08-01"
    current = releases / "v1.1-2026-08-02"
    prior.mkdir(parents=True)
    current.mkdir()
    errors, args = pg._freshness_args(
        {"release_mode": "representation-only", "supersedes": prior.name},
        current)
    check(not errors, f"valid representation declaration refused: {errors}")
    check(args[:3] == ["--claim", "design",
                       "--representation-supersede"],
          f"wrong representation freshness argv: {args}")
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
