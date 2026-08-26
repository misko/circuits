#!/usr/bin/env python3
"""T1: executable contract for the forward PCB documentation entry points.

The prose is intentionally checked against machine-owned sources instead of
being snapshotted.  A documentation change may reword explanations freely,
but it may not publish a stale command, omit a lifecycle stage, invent a
semantic dependency, lose an authority route, or point at a missing file.
"""
from __future__ import annotations

import json
import re
import shlex
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (ROOT, check, contains, eq, main, must_pass, run, test,  # noqa: E402
                     tmpdir)


README = ROOT / "README.md"
SKILL = ROOT / "skills/pcb-design/SKILL.md"
GRAPH = ROOT / "skills/pcb-design/references/execution-graph.md"
CATALOG = ROOT / "skills/pcb-design/references/skill-authority-map.json"
DOCS_INDEX = ROOT / "docs/README.md"
IMPROVEMENTS = ROOT / "improvements.md"
CLAUDE = ROOT / "CLAUDE.md"
ROOT_CONTRACT = ROOT / "skills/pcb-design/templates/contracts/ROOT.contracts.md"
KICAD_CONTRACT = ROOT / "skills/pcb-design/templates/contracts/04_kicad/contracts.md"
RELEASE_CONTRACT = ROOT / "skills/pcb-design/templates/contracts/07_releases/contracts.md"
CHECKLIST = ROOT / "skills/pcb-design/templates/01_docs/CHECKLIST.md"
ORCHESTRATION = ROOT / "skills/pcb-design/templates/ORCHESTRATION_STATE.md"
GEN_TSCIRCUIT = ROOT / "skills/kicad-pcb/scripts/gen_tscircuit.sh"
TSX_TO_BOARD = ROOT / "skills/kicad-pcb/scripts/tsx_to_board.sh"
TSCIRCUIT_REFERENCE = ROOT / "skills/kicad-pcb/references/tscircuit-folder.md"
TSCIRCUIT_CONTRACT = ROOT / "skills/pcb-design/templates/contracts/03_tscircuit/contracts.md"

ENTRY_DOCS = (README, SKILL, GRAPH, DOCS_INDEX, IMPROVEMENTS)
CURRENT_ROOT_DOCS = {"CLAUDE.md", "README.md", "contracts.md", "improvements.md"}
LINK_RE = re.compile(
    r"!?\[[^\]]*\]\(\s*(?:<(?P<angle>[^>]+)>|(?P<plain>[^\s)]+))"
)


def markdown_section(text: str, heading: str) -> str:
    """Return an exact Markdown heading through the next peer/parent heading."""
    lines = text.splitlines(keepends=True)
    try:
        start = next(i for i, line in enumerate(lines)
                     if line.rstrip("\r\n") == heading)
    except StopIteration as exc:
        raise AssertionError(f"missing Markdown heading {heading!r}") from exc
    level = len(heading) - len(heading.lstrip("#"))
    end = len(lines)
    for i in range(start + 1, len(lines)):
        match = re.match(r"^(#{1,6})\s", lines[i])
        if match and len(match.group(1)) <= level:
            end = i
            break
    return "".join(lines[start:end])


def commissioning_command(document: Path, heading: str) -> list[str]:
    section = markdown_section(document.read_text(), heading)
    blocks = re.findall(r"```bash[ \t]*\n(.*?)\n```", section, re.DOTALL)
    commands = [block for block in blocks if "commission_project.py" in block]
    eq(len(commands), 1, f"{document.relative_to(ROOT)} commissioning block count")
    command = re.sub(r"\\[ \t]*\r?\n", " ", commands[0]).strip()
    tokens = shlex.split(command)
    check(len(tokens) >= 3, f"short commissioning command in {document}")
    eq(tokens[0], "python3", f"{document.relative_to(ROOT)} interpreter")
    eq(tokens[1], "skills/pcb-design/scripts/commission_project.py",
       f"{document.relative_to(ROOT)} commissioner path")
    check(not any(token in {"&&", "||", ";", "|"} for token in tokens),
          f"quick start is not one parseable command in {document}")
    return tokens


def markdown_links(text: str) -> list[str]:
    return [match.group("angle") or match.group("plain")
            for match in LINK_RE.finditer(text)]


def local_link_findings(
    document: Path,
    *,
    text: str | None = None,
    resolution_base: Path | None = None,
) -> list[str]:
    """Report missing local link targets; fragments and remote URIs are exempt."""
    findings: list[str] = []
    body = document.read_text() if text is None else text
    base = document.parent if resolution_base is None else resolution_base
    for raw_target in markdown_links(body):
        target = raw_target.strip()
        if target.startswith("#"):
            continue
        split = urlsplit(target)
        if split.scheme or split.netloc:
            continue
        path_text = unquote(split.path)
        if not path_text:
            continue
        candidate = Path(path_text)
        if not candidate.is_absolute():
            candidate = base / candidate
        if not candidate.exists():
            findings.append(
                f"{document.name}: missing local link {raw_target!r} -> {candidate}"
            )
    return findings


def semantic_roles(cell: str) -> tuple[str, ...]:
    value = cell.strip()
    if value == "—":
        return ()
    return tuple(item.strip().strip("`") for item in value.split(","))


def stage_table(text: str) -> list[tuple[int, str, str, str,
                                         tuple[str, ...], tuple[str, ...]]]:
    section = markdown_section(text, "## Stage catalog")
    rows = []
    for line in section.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 6 or not cells[0].isdigit():
            continue
        rows.append((
            int(cells[0]),
            cells[1].strip("`"),
            cells[2].strip("`"),
            cells[3].strip("`"),
            semantic_roles(cells[4]),
            semantic_roles(cells[5]),
        ))
    return rows


def selection_label(selects: dict) -> str:
    """Canonical human label for every closed schema-1 selector shape."""
    target_release_or_later = [
        "first_article", "production", "publication", "release"
    ]
    labels = {
        json.dumps({"always": True}, sort_keys=True): "always",
        json.dumps({"signal_integrity": ["rf"]}, sort_keys=True): "RF",
        json.dumps({"foreign_mating": [True]}, sort_keys=True): "foreign mating",
        json.dumps({"targets": target_release_or_later},
                   sort_keys=True): "release or later",
        json.dumps({"signal_integrity": ["rf"],
                    "targets": target_release_or_later},
                   sort_keys=True): "RF release or later",
        json.dumps({"targets": ["publication"]},
                   sort_keys=True): "publication",
        json.dumps({"targets": ["first_article", "production"]},
                   sort_keys=True): "first article or production",
        json.dumps({"targets": ["production"]},
                   sort_keys=True): "production",
    }
    key = json.dumps(selects, sort_keys=True)
    check(key in labels, f"stage selector has no documentation label: {selects!r}")
    return labels[key]


def catalog_stage_table(catalog: dict) -> list[tuple[int, str, str, str,
                                                     tuple[str, ...],
                                                     tuple[str, ...]]]:
    rows = []
    for ordinal, row in enumerate(catalog["stages"], 1):
        spec = row["spec"]
        selects = row.get("selects", row.get("applies"))
        check(selects is not None, f"{spec['id']} has no selector")
        rows.append((
            ordinal,
            spec["id"],
            spec["owner"],
            selection_label(selects),
            tuple(spec["requires"]),
            tuple(spec["produces"]),
        ))
    return rows


def stage_table_findings(graph: Path, catalog: dict) -> list[str]:
    actual = stage_table(graph.read_text())
    expected = catalog_stage_table(catalog)
    if actual == expected:
        return []
    actual_ids = [row[1] for row in actual]
    expected_ids = [row[1] for row in expected]
    missing = [stage_id for stage_id in expected_ids if stage_id not in actual_ids]
    extra = [stage_id for stage_id in actual_ids if stage_id not in expected_ids]
    details = [f"stage table differs: documented={actual_ids!r} catalog={expected_ids!r}"]
    if missing:
        details.append(f"missing stages: {missing!r}")
    if extra:
        details.append(f"extra stages: {extra!r}")
    if not missing and not extra:
        for documented, canonical in zip(actual, expected):
            if documented != canonical:
                details.append(
                    f"stage {canonical[1]} row differs: "
                    f"documented={documented!r} catalog={canonical!r}"
                )
    return details


@test("root and skill quick-start commissioning commands execute in scratch roots")
def t_documented_commissioning_commands():
    base = tmpdir("pcb-doc-command-")
    brief = base / "brief.txt"
    brief.write_text("Build a small ordinary board from this exact brief.\n")

    for ordinal, (document, heading) in enumerate((
        (README, "## Manual commissioning"),
        (SKILL, "## Quick start"),
    ), 1):
        projects_root = base / f"projects-{ordinal}"
        projects_root.mkdir()
        tokens = commissioning_command(document, heading)
        brief_index = tokens.index("--brief-file") + 1
        tokens[brief_index] = str(brief)
        tokens.extend(("--projects-root", str(projects_root)))
        result = must_pass(
            run(tokens, cwd=ROOT),
            f"{document.relative_to(ROOT)} quick-start commission",
        )
        contains(result.out, "PCB-SCAFFOLD OK", "scaffold success marker")
        contains(result.out, "stage=PCB-COMMISSION status=INCOMPLETE",
                 "commission remains an explicit hold")
        project = projects_root / "my-board"
        check((project / "01_docs/BRIEF.md").is_file(),
              f"{document} command did not write the brief record")
        profile = json.loads(
            (project / "01_docs/capability-profile.json").read_text())
        eq(profile["target"], "design", "documented default lifecycle target")
        eq(profile["signal_integrity"], "ordinary",
           "documented ordinary signal-integrity profile")


@test("root quick start installs and invokes pcb-design with a brief-only prompt")
def t_root_brief_only_skill_quick_start():
    section = markdown_section(README.read_text(), "## Quick start")
    contains(section, "$skill-installer Install skills/pcb-design",
             "skill installation prompt")
    contains(section, "/skills", "Codex slash selector")
    contains(section, "$pcb-design 3S LiPo input", "direct skill invocation")
    contains(section, "4× USB-A outputs at 5 V / 1.5 A each",
             "brief-only USB-A requirement")
    contains(section, "1× USB-C output at 5 V / 5 A",
             "brief-only USB-C requirement")
    contains(section, "v1.12-2026-07-28", "fabricated example release")
    contains(section, "twin_iso_nw.png", "fabricated example hero render")


@test("execution graph stage table exactly mirrors the ordered catalog")
def t_execution_graph_matches_catalog():
    catalog = json.loads(CATALOG.read_text())
    findings = stage_table_findings(GRAPH, catalog)
    check(not findings, "\n".join(findings))
    eq(len(stage_table(GRAPH.read_text())), 19, "closed lifecycle stage census")


@test("every routed authority reference exists and is linked directly by the skill")
def t_routed_references_exist_and_are_direct():
    catalog = json.loads(CATALOG.read_text())
    routed = [reference
              for domain in catalog["domains"]
              for reference in domain.get("references", [])]
    eq(len(routed), len(set(routed)), "routed reference uniqueness")
    linked = {
        (SKILL.parent / unquote(urlsplit(target).path)).resolve()
        for target in markdown_links(SKILL.read_text())
        if not urlsplit(target).scheme and urlsplit(target).path
    }
    for reference in routed:
        path = (ROOT / reference).resolve()
        check(path.is_file(), f"routed reference does not exist: {reference}")
        check(path in linked,
              f"routed reference is not linked directly from SKILL.md: {reference}")


@test("documentation index classifies every non-current root document as history")
def t_root_history_is_classified():
    root_markdown = {path.name for path in ROOT.glob("*.md")}
    historical = root_markdown - CURRENT_ROOT_DOCS
    history_section = markdown_section(
        DOCS_INDEX.read_text(), "## Historical plans and snapshots")
    indexed = set()
    for target in markdown_links(history_section):
        split = urlsplit(target)
        if split.scheme or not split.path:
            continue
        resolved = (DOCS_INDEX.parent / unquote(split.path)).resolve()
        if resolved.parent == ROOT and resolved.suffix == ".md":
            indexed.add(resolved.name)
    eq(indexed, historical, "root historical document classification")
    for name in sorted(historical):
        opening = "\n".join((ROOT / name).read_text().splitlines()[:12])
        contains(opening, "Historical", f"{name} historical banner")


@test("all local links in the forward PCB entry documents resolve")
def t_entry_document_links_resolve():
    findings = [finding
                for document in ENTRY_DOCS
                for finding in local_link_findings(document)]
    check(not findings, "\n".join(findings))


@test("PCB documentation overhaul remains tracked as IMP-229")
def t_documentation_improvement_marker():
    text = IMPROVEMENTS.read_text()
    match = re.search(
        r"^## IMP-229\b(?P<body>.*?)(?=^## (?:IMP-|Index\b)|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    check(match is not None, "improvements.md has no IMP-229 tracking entry")
    body = match.group(0)
    check(re.search(r"document|graph", body, re.IGNORECASE),
          "IMP-229 does not identify the PCB documentation/graph overhaul")
    check(re.search(r"^- status: (?:accepted|implementing|completed)$",
                    body, re.MULTILINE),
          "IMP-229 has no active/closed forward status")
    contains(body, "completion evidence", "IMP-229 completion contract")


@test("forward DRC examples name the subject and fail on violations")
def t_forward_drc_examples_are_executable():
    board_gate = (
        "kicad-cli pcb drc --severity-all --refill-zones "
        "--schematic-parity --exit-code-violations "
        "04_kicad/<board>.kicad_pcb"
    )
    for document in (CLAUDE, CHECKLIST, KICAD_CONTRACT):
        contains(document.read_text(), board_gate,
                 f"{document.relative_to(ROOT)} exact DRC gate")
    contains(
        ORCHESTRATION.read_text(),
        board_gate.replace("04_kicad/", "projects/<name>/04_kicad/"),
        "coordinator exact DRC gate",
    )
    contains(
        RELEASE_CONTRACT.read_text(),
        board_gate.replace("04_kicad/", "source/"),
        "sealed-source exact DRC gate",
    )


@test("commissioned project contract describes stop, adoption, and resume")
def t_project_contract_has_truthful_resume_path():
    text = ROOT_CONTRACT.read_text()
    contains(text, "bash 03_src/rebuild_all.sh`", "initial full-conductor start")
    contains(text, "operator checkpoints", "intentional stop semantics")
    contains(text, "--resume-after-schematic-review", "exact resume invocation")
    check(text.index("bash 03_src/rebuild_all.sh`") <
          text.index("--resume-after-schematic-review"),
          "project contract presents resume before the initial run")


@test("release contract separates mutable staging from immutable sealing")
def t_release_staging_boundary_is_explicit():
    text = RELEASE_CONTRACT.read_text()
    contains(text, "candidate path is mutable only during", "staging mutability")
    contains(text, "The seal commit is the transition", "seal transition")
    contains(text, "immutability begins the moment the seal commit exists",
             "normative seal boundary")
    check("written once, at\nseal time" not in text,
          "release opening still claims staged bytes appear only at seal time")
    contains(text, 'release_git_dirty.py "$PWD"',
             "project-root release dirt invocation")
    check("release_git_dirty.py <board>" not in text,
          "release contract retains an ambiguous board-name invocation")


@test("forward TSX surfaces use exact-reference and project-local terminology")
def t_forward_tsx_language_and_authority():
    for document in (GEN_TSCIRCUIT, TSX_TO_BOARD, TSCIRCUIT_REFERENCE,
                     TSCIRCUIT_CONTRACT):
        text = document.read_text()
        check("sealed 04_kicad" not in text,
              f"{document.relative_to(ROOT)} calls mutable current KiCad sealed")
        check("sealed_ref.txt" not in text,
              f"{document.relative_to(ROOT)} retains the stale reference name")
    for script in (GEN_TSCIRCUIT, TSX_TO_BOARD):
        text = script.read_text()
        contains(text, "./node_modules/.bin/tsci",
                 f"{script.relative_to(ROOT)} local producer")
        check("TSCI=tsci" not in text,
              f"{script.relative_to(ROOT)} has an ambient tsci fallback")


@test("graph checker rejects a temporarily omitted catalog stage", kind="known_bad")
def t_omitted_stage_is_rejected():
    text = GRAPH.read_text()
    mutated, count = re.subn(
        r"^\|\s*8\s*\|\s*`KICAD-MATING-IMPORT`.*\n",
        "",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    eq(count, 1, "omitted-stage mutation target")
    directory = tmpdir("pcb-doc-omitted-stage-")
    altered = directory / "execution-graph.md"
    altered.write_text(mutated)
    findings = stage_table_findings(altered, json.loads(CATALOG.read_text()))
    check(findings, "stage checker accepted a graph with one catalog stage omitted")
    contains("\n".join(findings), "KICAD-MATING-IMPORT",
             "omitted-stage rejection")


@test("link checker rejects a temporary broken local target", kind="known_bad")
def t_broken_link_is_rejected():
    directory = tmpdir("pcb-doc-broken-link-")
    altered = directory / "README.md"
    broken = "definitely-missing-pcb-documentation-target.md"
    altered.write_text(README.read_text() + f"\n[broken fixture]({broken})\n")
    findings = local_link_findings(
        altered,
        resolution_base=ROOT,
    )
    check(findings, "link checker accepted a missing local target")
    contains("\n".join(findings), broken, "broken-link rejection")


if __name__ == "__main__":
    sys.exit(main())
