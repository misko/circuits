#!/usr/bin/env python3
"""T1: Pluto RX2 8-way v4 full/reuse legacy-pipeline canaries.

These tests parse declarations and synthetic, source-line-addressed xtrace
records only.  They never invoke either legacy driver or any cataloged command.
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import check, eq, main, test  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PIPELINE = ROOT / "skills" / "pcb-design" / "scripts"
sys.path.insert(0, str(PIPELINE))

from pipeline_catalog import CatalogValidationError, LegacyPipelineCatalog  # noqa: E402
from pipeline_xtrace import parse_xtrace  # noqa: E402


PROJECT = ROOT / "archived_projects" / "pluto-rx2-8way-v4"
SRC = PROJECT / "03_src"
ROUTE = SRC / "route.yaml"
DRIVERS = {
    "reuse": SRC / "rebuild_reuse.sh",
    "full": SRC / "rebuild_all.sh",
}
CATALOGS = {
    mode: SRC / f"pipeline_shadow_{mode}.json" for mode in DRIVERS
}
DIGESTS = {
    "reuse": "a91f6709c4677fcef0c4c5b655eefad760657291664bca26e8401b5264421cb1",
    "full": "dd8125412ec597c6bcdc371b74462115db3ddc01904b1849c75b8e8c2e83f8fe",
}
EXPECTED = {
    "reuse": (
        "PLUTOV4-R-MODULE-FIRST",
        "PLUTOV4-R-RF-CONTRACT",
        "PLUTOV4-R-PINNED-SUBJECT",
        "PLUTOV4-R-ROUTE-MARKER-RESET",
        "PLUTOV4-R-NETLIST",
        "PLUTOV4-R-BOARD",
        "PLUTOV4-R-PAD-SEPARATION",
        "PLUTOV4-R-BOARD-AUDIT-PLACEMENT",
        "PLUTOV4-R-RULES-PRE-IMPORT",
        "PLUTOV4-R-PAD-ESCAPE",
        "PLUTOV4-R-ROUTE-IMPORT",
        "PLUTOV4-R-ROUTE-TAPS",
        "PLUTOV4-R-ROUTE-STITCH",
        "PLUTOV4-R-BOARD-AUDIT-ROUTED",
        "PLUTOV4-R-RULES-POST-STITCH",
        "PLUTOV4-R-PARITY-SCHEMATIC-COPY",
        "PLUTOV4-R-LAYOUT-DRC-REPORT",
        "PLUTOV4-R-LAYOUT-DRC-VERDICT",
        "PLUTOV4-R-RF-SOLVER-PREREQUISITE",
        "PLUTOV4-R-FENCE-PITCH",
        "PLUTOV4-R-CPWG-FIELD-SOLVE",
        "PLUTOV4-R-COPPER-LENGTH-VERDICT",
    ),
    "full": (
        "PLUTOV4-F-MODULE-FIRST",
        "PLUTOV4-F-RF-CONTRACT",
        "PLUTOV4-F-TSX-PREFLIGHT",
        "PLUTOV4-F-BUILD-PROVENANCE-STAMP",
        "PLUTOV4-F-TSCIRCUIT-BUILD",
        "PLUTOV4-F-CIRCUIT-JSON-BRIDGE",
        "PLUTOV4-F-RENDER-INVALIDATION",
        "PLUTOV4-F-SCHEMATIC-SVG-EXPORT",
        "PLUTOV4-F-SCHEMATIC-PDF-RENDER",
        "PLUTOV4-F-BUILD-PROVENANCE-VERIFY",
        "PLUTOV4-F-SCHEMATIC-CONVERT",
        "PLUTOV4-F-NETLIST-EXPORT",
        "PLUTOV4-F-NET-LABEL-SURVIVAL",
        "PLUTOV4-F-ELECTRICAL-INVARIANTS",
        "PLUTOV4-F-ADR-COVERAGE",
        "PLUTOV4-F-POWER-TOPOLOGY",
        "PLUTOV4-F-POWER-MARGIN",
        "PLUTOV4-F-OFF-CONTROL",
        "PLUTOV4-F-COUNT-PARITY",
        "PLUTOV4-F-CIRCUIT-BOM",
        "PLUTOV4-F-ERC-BASELINE",
        "PLUTOV4-F-ERC-ERROR-VERDICT",
        "PLUTOV4-F-LAYOUT-PROVENANCE-BEGIN",
        "PLUTOV4-F-BOARD",
        "PLUTOV4-F-BOARD-AUDIT-PLACEMENT",
        "PLUTOV4-F-CRITICAL-PART-FACTS",
        "PLUTOV4-F-PLACEMENT-GATES",
        "PLUTOV4-F-PAD-SEPARATION",
        "PLUTOV4-F-RULES-PRE-ROUTE",
        "PLUTOV4-F-PAD-ESCAPE",
        "PLUTOV4-F-TIER-PREFLIGHT",
        "PLUTOV4-F-ROUTE-PREP",
        "PLUTOV4-F-ROUTE-IMPORT",
        "PLUTOV4-F-ROUTE-STITCH",
        "PLUTOV4-F-BOARD-AUDIT-ROUTED",
        "PLUTOV4-F-RULES-POST-STITCH",
        "PLUTOV4-F-LAYOUT-DRC-REPORT",
        "PLUTOV4-F-LAYOUT-DRC-VERDICT",
        "PLUTOV4-F-LAYOUT-PROVENANCE-FINISH",
        "PLUTOV4-F-RF-SOLVER-PREREQUISITE",
        "PLUTOV4-F-FENCE-PITCH",
        "PLUTOV4-F-CPWG-FIELD-SOLVE",
        "PLUTOV4-F-COPPER-LENGTH-VERDICT",
        "PLUTOV4-F-TRACE-AUDIT-ADVISORY",
        "PLUTOV4-F-PINNED-SCHEMATIC-PROMOTION",
        "PLUTOV4-F-PROJECT-STATE",
    ),
}


def line_map(mode, groups):
    eq(len(groups), len(EXPECTED[mode]), f"{mode} source-map denominator")
    return {
        line: stage
        for stage, lines in zip(EXPECTED[mode], groups)
        for line in lines
    }


TRACE_STAGE_LINES = {
    "reuse": line_map("reuse", (
        (47,), (49,), (59, 60, 61, 62), (64,), (68,), (72,), (73,),
        (77,), (82,), (86,), (90,), (92,), (95,), (101,), (104,),
        (109,), (110,), (112,), (123, 124), (126, 127), (128,), (129,),
    )),
    "full": line_map("full", (
        (28,), (31,), (36,), (45,), (59,), (60, 61), (82,), (83,),
        (84, 85), (94,), (98,), (100,), (106,), (108,), (110,),
        (112,), (114,), (116,), (118,), (120,), (144,), (145,),
        (150,), (157,), (175, 176), (180,), (185,), (186,), (190,),
        (195,), (201,), (205,), (206,), (207,), (213,), (216,),
        (219,), (221,), (222,), (228, 229), (231, 232), (233,), (234,),
        (262,), (270, 271, 272), (274,),
    )),
}
TRACE_FAILURE_LINES = {
    "reuse": {
        48: EXPECTED["reuse"][0], 50: EXPECTED["reuse"][1],
        74: EXPECTED["reuse"][6], 87: EXPECTED["reuse"][9],
        130: EXPECTED["reuse"][21],
    },
    "full": {
        29: EXPECTED["full"][0], 32: EXPECTED["full"][1],
        37: EXPECTED["full"][2], 46: EXPECTED["full"][3],
        96: EXPECTED["full"][9], 107: EXPECTED["full"][12],
        109: EXPECTED["full"][13], 111: EXPECTED["full"][14],
        113: EXPECTED["full"][15], 115: EXPECTED["full"][16],
        117: EXPECTED["full"][17], 119: EXPECTED["full"][18],
        121: EXPECTED["full"][19], 147: EXPECTED["full"][21],
        187: EXPECTED["full"][27], 196: EXPECTED["full"][29],
        202: EXPECTED["full"][30], 235: EXPECTED["full"][42],
        273: EXPECTED["full"][44],
    },
}
TRACE_IGNORED_LINES = {
    "reuse": (37, 38, 40, 42, 43, 44, 67, 108, 125, 131),
    "full": (6, 7, 10, 11, 14, 16, 17, 18, 19, 20, 23, 24, 58, 81, 230),
}


def load(mode):
    raw = json.loads(CATALOGS[mode].read_text(encoding="utf-8"))
    return raw, LegacyPipelineCatalog.from_mapping(raw)


def rows(mode):
    return {row.legacy_key: row for row in load(mode)[1].bindings}


def trace_key(mode, line):
    return (f"project/03_src/{DRIVERS[mode].name}", line)


@test("Pluto v4 catalogs bind exact JSON declarations and exact driver bytes")
def t_exact_declarations():
    for mode in ("reuse", "full"):
        raw, catalog = load(mode)
        eq(catalog.to_mapping(), raw, f"{mode} exact declaration mapping")
        eq(catalog.project_slug, "pluto-rx2-8way-v4", f"{mode} project")
        eq(catalog.driver_relative_path, f"03_src/{DRIVERS[mode].name}",
           f"{mode} driver path")
        eq(catalog.driver_sha256, DIGESTS[mode], f"{mode} declared digest")
        driver_bytes = DRIVERS[mode].read_bytes()
        eq(hashlib.sha256(driver_bytes).hexdigest(), DIGESTS[mode],
           f"{mode} current digest")
        check(catalog.driver_matches(driver_bytes), f"{mode} exact bytes rejected")
        check(not catalog.driver_matches(driver_bytes + b"\n"),
              f"{mode} mutated bytes accepted")


@test("Pluto v4 full and reuse stage orders are distinct and dependency-complete")
def t_orders_and_dependencies():
    eq((len(EXPECTED["reuse"]), len(EXPECTED["full"])), (22, 46),
       "catalog denominators")
    for mode in ("reuse", "full"):
        _, catalog = load(mode)
        eq(catalog.observed_stage_ids(), EXPECTED[mode], f"{mode} order")
        eq(tuple(row.sequence for row in catalog.bindings),
           tuple(range(1, len(EXPECTED[mode]) + 1)), f"{mode} sequence")
        eq(tuple(stage.id for stage in catalog.stage_registry().resolve()),
           EXPECTED[mode], f"{mode} registry order")
        eq(catalog.bindings[0].dependencies, (), f"{mode} first dependency")
        eq(catalog.bindings[0].spec.requires, (), f"{mode} first input")
        for prior, current in zip(catalog.bindings, catalog.bindings[1:]):
            eq(current.dependencies, (prior.spec.id,),
               f"{mode}:{current.legacy_key} control handoff")
            eq(current.spec.requires, prior.spec.produces,
               f"{mode}:{current.legacy_key} semantic handoff")

    reuse_ids = set(EXPECTED["reuse"])
    full_ids = set(EXPECTED["full"])
    check(reuse_ids.isdisjoint(full_ids), "full and reuse reused stage identities")
    check("PLUTOV4-F-TSCIRCUIT-BUILD" in full_ids,
          "full catalog lost source generation")
    check("PLUTOV4-R-PINNED-SUBJECT" in reuse_ids,
          "reuse catalog lost pinned-schematic selection")
    check("PLUTOV4-R-ROUTE-TAPS" in reuse_ids and
          "PLUTOV4-F-ROUTE-TAPS" not in full_ids,
          "catalogs invented a shared taps behavior")


@test("Pluto v4 catalog evidence is inert, normalized data")
def t_nonexecuting_portable_data():
    for mode in ("reuse", "full"):
        _, catalog = load(mode)
        check(not hasattr(catalog, "run") and not hasattr(catalog, "execute"),
              f"{mode} catalog unexpectedly executable")
        for row in catalog.bindings:
            expected_cwd = (
                "03_tscircuit"
                if mode == "full" and row.legacy_key in {
                    "tscircuit-build", "schematic-svg-export"}
                else "."
            )
            eq(row.cwd, expected_cwd, f"{mode}:{row.legacy_key} cwd")
            check((row.argv is None) != (row.shell_builtin is None),
                  f"{mode}:{row.legacy_key} ambiguous command evidence")
            if row.argv:
                joined = "\0".join(row.argv)
                check("/home/" not in joined and "~" not in joined,
                      f"{mode}:{row.legacy_key} captured host-specific text")
                check("$(" not in joined,
                      f"{mode}:{row.legacy_key} argv captured substitution syntax")
            for path in row.accepted_output_paths:
                check(not path.startswith("/") and ".." not in Path(path).parts,
                      f"{mode}:{row.legacy_key} non-normalized output {path}")
                check(not path.startswith("07_releases/"),
                      f"{mode}:{row.legacy_key} writes sealed releases")


@test("Pluto v4 applicability and promoted-route evidence match project sources")
def t_applicability_and_route():
    route = yaml.safe_load(ROUTE.read_text(encoding="utf-8"))
    eq(route["route"]["import_source"], "promoted", "route import policy")
    eq(route["route"]["final"], "03_src/route/r5.kicad_pcb",
       "promoted route path")
    eq(route["route"]["preflight_critical_pairs"], [],
       "no differential-pair route denominator")
    reason = route["route"]["no_critical_routes"]
    check("eight independent single-ended nets" in reason and
          "copper_length_audit.py" in reason,
          "single-ended RF applicability reason lost its specific owner")
    stubs = route["stitch"]["seed_stubs"]["stubs"]
    non_pin = [row for row in stubs if not row.get("pin")]
    eq(len(non_pin), 26, "non-pin seed-stub evidence denominator")
    eq(sum(not str(row.get("why") or "").strip() for row in non_pin), 0,
       "non-pin seed-stub banks missing explicit ownership")
    eq(route["flow"]["budgets_s"]["rf_field_solver"], 45,
       "RF field solver performance budget")
    eq(route["flow"]["timeouts_s"]["rf_field_solver"], 60,
       "RF field solver hard deadline")
    check("run_stage rf_field_solver \"$KRT_PY\"" in
          DRIVERS["full"].read_text(encoding="utf-8"),
          "full driver bypasses bounded RF field-solver stage")
    check("pcb_flow.py\" run . --stage rf_field_solver -- \"$KRT_PY\"" in
          DRIVERS["reuse"].read_text(encoding="utf-8"),
          "reuse driver bypasses bounded RF field-solver stage")
    for mode in ("reuse", "full"):
        eq(rows(mode)["cpwg-field-solve"].spec.timeout_s, 60,
           f"{mode} catalog RF field-solver deadline")
    check((PROJECT / route["route"]["final"]).is_file(),
          "promoted route artifact missing")
    check((SRC / "audit_board.py").is_file(), "audit_board.py premise missing")

    for mode in ("reuse", "full"):
        _, catalog = load(mode)
        check(all(row.applicability == "APPLIES" for row in catalog.bindings),
              f"{mode} contains false N/A applicability")
        check(all(row.applicability_reason is None for row in catalog.bindings),
              f"{mode} APPLIES stage carries an N/A reason")

    reuse_import = rows("reuse")["route-import"]
    full_import = rows("full")["route-import"]
    check("--route-source" not in reuse_import.argv,
          "reuse catalog invented an absent route-source flag")
    eq(full_import.argv[-2:], ("--route-source", "promoted"),
       "full explicit promoted selector")


@test("Pluto v4 deferred commands retain their actual later authority")
def t_authority():
    reuse = rows("reuse")
    full = rows("full")
    eq((reuse["route-marker-reset"].authority,
        reuse["route-marker-reset"].authority_binding),
       ("ignored_until", "route-import"), "reuse marker authority")
    eq((reuse["layout-drc-report"].authority,
        reuse["layout-drc-report"].authority_binding),
       ("postcheck", "layout-drc-verdict"), "reuse DRC authority")
    for key in ("schematic-svg-export", "schematic-pdf-render"):
        eq((full[key].authority, full[key].authority_binding),
           ("ignored_until", "build-provenance-verify"),
           f"full {key} freshness authority")
    eq((full["layout-drc-report"].authority,
        full["layout-drc-report"].authority_binding),
       ("postcheck", "layout-drc-verdict"), "full DRC authority")
    eq((full["trace-audit-advisory"].authority,
        full["trace-audit-advisory"].authority_binding),
       ("ignored_until", "pinned-schematic-promotion"),
       "advisory trace authority")


@test("Pluto v4 exact source-line maps reproduce both catalogs without execution")
def t_xtrace_maps():
    for mode in ("reuse", "full"):
        source_lines = DRIVERS[mode].read_text(encoding="utf-8").splitlines()
        stage_lines = TRACE_STAGE_LINES[mode]
        failure_lines = TRACE_FAILURE_LINES[mode]
        ignored_lines = TRACE_IGNORED_LINES[mode]
        check(set(stage_lines).isdisjoint(failure_lines),
              f"{mode} stage/failure line overlap")
        check(set(stage_lines).isdisjoint(ignored_lines),
              f"{mode} stage/ignored line overlap")
        check(set(failure_lines).isdisjoint(ignored_lines),
              f"{mode} failure/ignored line overlap")
        declared = set(stage_lines) | set(failure_lines) | set(ignored_lines)
        check(max(declared) <= len(source_lines), f"{mode} map exceeds driver")
        for line in declared:
            text = source_lines[line - 1].strip()
            check(text and not text.startswith("#"),
                  f"{mode} trace line {line} no longer names shell text")

        records = [
            f"+PIPELINE_TRACE:{DRIVERS[mode]}:{line}: opaque line {line}"
            for line in sorted(stage_lines)
        ]
        observed = parse_xtrace(
            "\n".join(records) + "\n",
            {trace_key(mode, line): stage
             for line, stage in stage_lines.items()},
            project_root=PROJECT, repo_root=ROOT,
            expected_driver_sha256=DIGESTS[mode],
            trace_driver_sha256=DIGESTS[mode], trace_complete=True)
        eq(observed.observed_stage_ids, EXPECTED[mode],
           f"{mode} source-line observation order")
        check(observed.fully_mapped, f"{mode} source map retained unmapped lines")


def rejects(mapping, expected, label):
    try:
        LegacyPipelineCatalog.from_mapping(mapping)
    except CatalogValidationError as exc:
        check(expected in str(exc),
              f"{label}: {exc!s} does not contain {expected!r}")
    else:
        raise AssertionError(f"{label} SHOULD HAVE FAILED")


@test("Pluto v4 catalogs refuse identity, dependency, applicability, and authority drift",
      kind="known_bad")
def t_mutations_refused():
    reuse, _ = load("reuse")
    full, _ = load("full")

    wrong_digest = copy.deepcopy(reuse)
    wrong_digest["driver_sha256"] = "F" * 64
    rejects(wrong_digest, "64 lowercase", "uppercase digest")

    severed = copy.deepcopy(full)
    severed["bindings"][10]["dependencies"] = []
    rejects(severed, "missing from dependencies", "severed full chain")

    false_na = copy.deepcopy(reuse)
    false_na["bindings"][7]["applicability"] = "NOT_APPLICABLE"
    false_na["bindings"][7]["applicability_reason"] = "pretend absent"
    rejects(false_na, "cannot accept output", "false audit N/A")

    backward_authority = copy.deepcopy(full)
    backward_authority["bindings"][7]["authority_binding"] = "module-first"
    rejects(backward_authority, "must refer to a later", "backward authority")


if __name__ == "__main__":
    raise SystemExit(main())
