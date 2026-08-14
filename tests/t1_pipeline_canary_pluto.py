#!/usr/bin/env python3
"""T1: Pluto RX2 reuse driver declaration is exact and non-executing."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import check, eq, main, test  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PIPELINE = ROOT / "skills" / "pcb-design" / "scripts"
sys.path.insert(0, str(PIPELINE))

from pipeline_catalog import CatalogValidationError, LegacyPipelineCatalog  # noqa: E402
from pipeline_xtrace import parse_xtrace  # noqa: E402


PROJECT = ROOT / "projects" / "pluto-rx2-8way"
CANARY = PROJECT / "03_src" / "pipeline_shadow_reuse.json"
DRIVER = PROJECT / "03_src" / "rebuild_reuse.sh"
ROUTE = PROJECT / "03_src" / "route.yaml"
DRIVER_SHA256 = "ff2c79b35beade80787b0f8bbebd6b2946a04163ad372075d905f57b7e49ead0"
EXPECTED_ORDER = (
    "PLUTO-RX2-REUSE-PREPARE",
    "PLUTO-RX2-REUSE-NETLIST",
    "PLUTO-RX2-REUSE-BOARD",
    "PLUTO-RX2-REUSE-AUDIT",
    "PLUTO-RX2-REUSE-RULES-PRE",
    "PLUTO-RX2-REUSE-IMPORT",
    "PLUTO-RX2-REUSE-TAPS",
    "PLUTO-RX2-REUSE-STITCH",
    "PLUTO-RX2-REUSE-RULES-POST",
    "PLUTO-RX2-REUSE-SCHEMATIC-COPY",
    "PLUTO-RX2-REUSE-DRC",
    "PLUTO-RX2-REUSE-VERDICT",
)
TRACE_STAGE_LINES = {
    53: EXPECTED_ORDER[0], 54: EXPECTED_ORDER[0],
    55: EXPECTED_ORDER[0], 56: EXPECTED_ORDER[0],
    58: EXPECTED_ORDER[0], 62: EXPECTED_ORDER[1],
    66: EXPECTED_ORDER[2], 69: EXPECTED_ORDER[3],
    74: EXPECTED_ORDER[4], 77: EXPECTED_ORDER[5],
    79: EXPECTED_ORDER[6], 82: EXPECTED_ORDER[7],
    85: EXPECTED_ORDER[8], 90: EXPECTED_ORDER[9],
    91: EXPECTED_ORDER[10], 100: EXPECTED_ORDER[11],
}
TRACE_IGNORED_LINES = (37, 38, 40, 42, 43, 44, 61, 89, 101)


def load():
    raw = CANARY.read_text(encoding="utf-8")
    return json.loads(raw), LegacyPipelineCatalog.from_json(raw)


def by_key(catalog):
    return {row.legacy_key: row for row in catalog.bindings}


def trace_key(line):
    return ("project/03_src/rebuild_reuse.sh", line)


@test("Pluto reuse canary parses the exact catalog file and pinned driver bytes")
def t_exact_files():
    raw, catalog = load()
    eq(catalog.to_mapping(), raw, "exact declaration mapping")
    eq(catalog.project_slug, "pluto-rx2-8way", "project slug")
    eq(catalog.driver_relative_path, "03_src/rebuild_reuse.sh", "driver path")
    eq(catalog.driver_sha256, DRIVER_SHA256, "declared driver digest")
    driver_bytes = DRIVER.read_bytes()
    eq(hashlib.sha256(driver_bytes).hexdigest(), DRIVER_SHA256,
       "current driver digest")
    check(catalog.driver_matches(driver_bytes), "catalog rejected exact driver bytes")


@test("Pluto reuse observation has exactly twelve stable stages")
def t_order_denominator():
    _, catalog = load()
    eq(len(catalog.bindings), 12, "stage denominator")
    eq(catalog.observed_stage_ids(), EXPECTED_ORDER, "observed legacy order")
    eq(tuple(row.sequence for row in catalog.bindings), tuple(range(1, 13)),
       "contiguous sequence")
    eq(tuple(stage.id for stage in catalog.stage_registry().resolve()),
       EXPECTED_ORDER, "registry dependency order")


@test("Pluto reuse stages form the actual strict one-fact shell chain")
def t_one_fact_chain():
    _, catalog = load()
    first = catalog.bindings[0]
    eq(first.dependencies, (), "first dependency")
    eq(first.spec.requires, (), "first fact input")
    for prior, current in zip(catalog.bindings, catalog.bindings[1:]):
        eq(current.dependencies, (prior.spec.id,),
           f"{current.legacy_key} control dependency")
        eq(current.spec.requires, prior.spec.produces,
           f"{current.legacy_key} one-fact data dependency")
        eq(len(current.spec.requires), 1,
           f"{current.legacy_key} fact denominator")


@test("argv evidence is portable data and every cwd/output path is relative")
def t_portable_evidence():
    _, catalog = load()
    for row in catalog.bindings:
        eq(row.cwd, ".", f"{row.legacy_key} cwd")
        for path in row.accepted_output_paths:
            check(not path.startswith("/") and ".." not in Path(path).parts,
                  f"{row.legacy_key} non-relative output {path}")
        if row.argv is None:
            check(row.shell_builtin is not None,
                  f"{row.legacy_key} missing explicit shell token")
            continue
        joined = "\n".join(row.argv)
        check("/home/" not in joined and "~" not in joined,
              f"{row.legacy_key} captured a host path")
        for arg in row.argv:
            if "/skills/" in arg:
                check(arg.startswith("{repo}/"),
                      f"{row.legacy_key} skill path lacks repo placeholder")
            if any(part in arg for part in ("03_src/", "03_tscircuit/",
                                             "04_kicad/", "06_build/")):
                check(arg.startswith("{project}/"),
                      f"{row.legacy_key} project path lacks project placeholder")


@test("existing board audit and no-op taps remain explicitly APPLIES")
def t_applicability():
    _, catalog = load()
    rows = by_key(catalog)
    audit = rows["board-audit"]
    taps = rows["route-taps"]
    check((PROJECT / "03_src" / "audit_board.py").is_file(),
          "audit applicability premise disappeared")
    eq(audit.applicability, "APPLIES", "audit applicability")
    eq(audit.argv,
       ("/usr/bin/python3", "{project}/03_src/audit_board.py"),
       "audit argv")
    eq(taps.applicability, "APPLIES", "taps applicability")
    eq(taps.argv[2:], ("taps", "{project}/03_src/route.yaml"), "taps argv")
    eq(taps.accepted_output_paths, (), "no-op taps file outputs")
    eq(taps.accepted_output_symbols, ("reuse_taps_complete",),
       "no-op taps explicit completion fact")


@test("pre-import and post-stitch rule applications remain distinct stages")
def t_repeated_rules():
    _, catalog = load()
    rows = by_key(catalog)
    before = rows["rules-pre-import"]
    after = rows["rules-post-stitch"]
    check(before.spec.id != after.spec.id, "repeated rules stage ids collapsed")
    check(before.legacy_key != after.legacy_key, "repeated rules keys collapsed")
    eq(before.argv, after.argv, "same legacy rules command")
    eq(before.spec.produces, ("reuse_rules_pre",), "pre-import rules fact")
    eq(after.spec.produces, ("reuse_rules_post",), "post-stitch rules fact")
    check(before.sequence < rows["promoted-route-import"].sequence,
          "pre-import rules moved after import")
    check(after.sequence > rows["route-stitch"].sequence,
          "post-stitch rules moved before stitch")


@test("promoted import truthfully depends on deleting build-route precedence")
def t_promoted_route_provenance():
    _, catalog = load()
    rows = by_key(catalog)
    prepare = rows["prepare-promoted-reuse"]
    imported = rows["promoted-route-import"]
    driver_bytes = DRIVER.read_bytes()
    route_text = ROUTE.read_text(encoding="utf-8")

    eq(prepare.shell_builtin, "derive_verify_remove_build_final",
       "marker invalidation evidence")
    eq(prepare.spec.produces, ("promoted_route_selection_forced",),
       "promoted-selection fact")
    check(b"rm -f 06_build/route/FINAL" in driver_bytes,
          "driver no longer removes build-route precedence")
    check("final: 03_src/route/r6.kicad_pcb" in route_text,
          "promoted route declaration disappeared")
    check((PROJECT / "03_src" / "route" / "r6.kicad_pcb").is_file(),
          "promoted route artifact disappeared")
    eq(imported.argv[2:], ("import", "{project}/03_src/route.yaml"),
       "import retains truthful auto-selection argv")
    check("--route-source" not in imported.argv,
          "canary invented an explicit promoted selector")
    check("06_build/route/import_provenance.json" in
          imported.accepted_output_paths, "import provenance not accepted")


@test("DRC report remains non-authoritative until the count postcheck")
def t_postcheck_authority():
    _, catalog = load()
    rows = by_key(catalog)
    drc = rows["pcb-drc-report"]
    verdict = rows["routing-count-verdict"]
    eq(drc.authority, "postcheck", "DRC authority semantics")
    eq(drc.authority_binding, verdict.legacy_key, "DRC postcheck link")
    eq(verdict.shell_builtin, "python_heredoc_postcheck", "heredoc evidence")
    eq(verdict.authority, "exit", "final verdict authority")


@test("canary declaration is inspection-only and exposes no executor")
def t_non_executing():
    _, catalog = load()
    check(not hasattr(catalog, "run"), "catalog unexpectedly exposes run()")
    check(not hasattr(catalog, "execute"), "catalog unexpectedly exposes execute()")
    check(all(not hasattr(row, "run") for row in catalog.bindings),
          "binding unexpectedly executable")


@test("Pluto reuse xtrace line map covers the exact catalog without executing it")
def t_xtrace_map():
    source_lines = DRIVER.read_text(encoding="utf-8").splitlines()
    all_declared = set(TRACE_STAGE_LINES) | set(TRACE_IGNORED_LINES)
    check(max(all_declared) <= len(source_lines), "trace line exceeds driver")
    for line in all_declared:
        text = source_lines[line - 1].strip()
        check(text and not text.startswith("#"),
              f"trace line {line} no longer names executable shell text")

    records = [
        f"+PIPELINE_TRACE:{DRIVER}:{line}: opaque line {line}"
        for line in sorted(TRACE_STAGE_LINES)
    ]
    observed = parse_xtrace(
        "\n".join(records) + "\n",
        {trace_key(line): stage for line, stage in TRACE_STAGE_LINES.items()},
        project_root=PROJECT, repo_root=ROOT,
        expected_driver_sha256=DRIVER_SHA256,
        trace_driver_sha256=DRIVER_SHA256, trace_complete=True)
    eq(observed.observed_stage_ids, EXPECTED_ORDER,
       "source-line observation order")
    check(observed.fully_mapped, "declared Pluto trace retained unmapped commands")


@test("Pluto canary REFUSES catalog drift mutations", kind="known_bad")
def t_mutation_failures():
    raw, _ = load()
    mutations = []

    wrong_digest = copy.deepcopy(raw)
    wrong_digest["driver_sha256"] = "F" * 64
    mutations.append((wrong_digest, "64 lowercase"))

    broken_chain = copy.deepcopy(raw)
    broken_chain["bindings"][5]["dependencies"] = []
    mutations.append((broken_chain, "internal producer"))

    escaped_output = copy.deepcopy(raw)
    escaped_output["bindings"][10]["accepted_output_paths"] = ["../gate.json"]
    mutations.append((escaped_output, "non-escaping"))

    false_na = copy.deepcopy(raw)
    false_na["bindings"][3]["applicability"] = "NOT_APPLICABLE"
    false_na["bindings"][3]["applicability_reason"] = "file ignored"
    mutations.append((false_na, "cannot accept output"))

    for changed, diagnosis in mutations:
        try:
            LegacyPipelineCatalog.from_mapping(changed)
        except CatalogValidationError as exc:
            check(diagnosis in str(exc),
                  f"mutation diagnosis {exc!s} lacks {diagnosis!r}")
        else:
            raise AssertionError(f"catalog mutation was accepted: {diagnosis}")


if __name__ == "__main__":
    raise SystemExit(main())
