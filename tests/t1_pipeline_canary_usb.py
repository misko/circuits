#!/usr/bin/env python3
"""T1: USB Hub v4 deterministic-reuse shadow catalog canary.

The canary parses declarations and exact legacy bytes only.  It never invokes
the recorded commands or changes their authority.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import check, eq, main, test  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "projects" / "usb-hub-3s-v4"
CATALOG_PATH = PROJECT / "03_src" / "pipeline_shadow_reuse.json"
DRIVER_PATH = PROJECT / "03_src" / "rebuild_reuse.sh"
ROUTE_PATH = PROJECT / "03_src" / "route.yaml"

sys.path.insert(0, str(ROOT / "skills" / "pcb-design" / "scripts"))
from pipeline_catalog import CatalogValidationError, LegacyPipelineCatalog  # noqa: E402
from pipeline_xtrace import parse_xtrace  # noqa: E402


EXPECTED_DRIVER_SHA256 = (
    "bfe2630390266b0b442c52a94d734e568ae6cb89a3acf1de480aad4ca6a7f317"
)
EXPECTED_STAGE_IDS = (
    "USBV4-R-MODULE-FIRST-VALID",
    "USBV4-R-DESIGN-SCHEMA-VALID",
    "USBV4-R-SOURCE-RULES-VALID",
    "USBV4-R-PINNED-SUBJECT-RESOLVED",
    "USBV4-R-BUILD-ROUTE-MARKER-INVALIDATED",
    "USBV4-R-NETLIST-PRODUCED",
    "USBV4-R-SCHEMATIC-REVIEWS-ADMISSIBLE",
    "USBV4-R-BOARD-PRODUCED",
    "USBV4-R-PARITY-SCHEMATIC-COPIED",
    "USBV4-R-PIN-MAP-VALID",
    "USBV4-R-BOARD-AUDIT-DISPOSITION",
    "USBV4-R-PLACEMENT-GATES-VALID",
    "USBV4-R-PAD-SEPARATION-VALID",
    "USBV4-R-CRITICAL-PAIR-MAP-VALID",
    "USBV4-R-PLACEMENT-POLICY-VALID",
    "USBV4-R-RULES-PRE-PLACEMENT-DRC",
    "USBV4-R-PLACEMENT-DRC-REPORT",
    "USBV4-R-PLACEMENT-DRC-CLEAN",
    "USBV4-R-RULES-PRE-ROUTE-PREP",
    "USBV4-R-PAD-ESCAPE-VALID",
    "USBV4-R-TIER-PREFLIGHT-VALID",
    "USBV4-R-ROUTE-PREP-PRODUCED",
    "USBV4-R-PLACEMENT-REVIEWS-ADMISSIBLE",
    "USBV4-R-PROMOTED-ROUTE-IMPORTED",
    "USBV4-R-ROUTE-TAPS-PRODUCED",
    "USBV4-R-STITCH-PRODUCED",
    "USBV4-R-CRITICAL-ROUTES-CONNECTED",
    "USBV4-R-RULES-POST-STITCH",
    "USBV4-R-REALIZED-RULES-VALID",
    "USBV4-R-VIA-AMPACITY-VALID",
    "USBV4-R-LAYOUT-DRC-REPORT",
    "USBV4-R-LAYOUT-DRC-CLEAN",
)

# Exact source-line dispositions for the hash-pinned driver.  Repeated lines
# within one shell stage collapse only while consecutive; the three rules
# invocations therefore remain three distinct observed stages.
TRACE_STAGE_LINES = {
    48: EXPECTED_STAGE_IDS[0], 50: EXPECTED_STAGE_IDS[1],
    52: EXPECTED_STAGE_IDS[2], 62: EXPECTED_STAGE_IDS[3],
    63: EXPECTED_STAGE_IDS[3], 64: EXPECTED_STAGE_IDS[3],
    65: EXPECTED_STAGE_IDS[3], 67: EXPECTED_STAGE_IDS[4],
    71: EXPECTED_STAGE_IDS[5], 74: EXPECTED_STAGE_IDS[6],
    79: EXPECTED_STAGE_IDS[7], 82: EXPECTED_STAGE_IDS[8],
    86: EXPECTED_STAGE_IDS[9], 91: EXPECTED_STAGE_IDS[10],
    92: EXPECTED_STAGE_IDS[11], 93: EXPECTED_STAGE_IDS[12],
    95: EXPECTED_STAGE_IDS[13], 100: EXPECTED_STAGE_IDS[14],
    103: EXPECTED_STAGE_IDS[15], 104: EXPECTED_STAGE_IDS[16],
    106: EXPECTED_STAGE_IDS[17], 112: EXPECTED_STAGE_IDS[18],
    116: EXPECTED_STAGE_IDS[19], 119: EXPECTED_STAGE_IDS[20],
    121: EXPECTED_STAGE_IDS[21], 123: EXPECTED_STAGE_IDS[22],
    128: EXPECTED_STAGE_IDS[23], 130: EXPECTED_STAGE_IDS[24],
    133: EXPECTED_STAGE_IDS[25], 134: EXPECTED_STAGE_IDS[26],
    138: EXPECTED_STAGE_IDS[27], 139: EXPECTED_STAGE_IDS[28],
    141: EXPECTED_STAGE_IDS[29], 148: EXPECTED_STAGE_IDS[30],
    157: EXPECTED_STAGE_IDS[31],
}
TRACE_FAILURE_LINES = {
    49: EXPECTED_STAGE_IDS[0], 51: EXPECTED_STAGE_IDS[1],
    53: EXPECTED_STAGE_IDS[2], 76: EXPECTED_STAGE_IDS[6],
    88: EXPECTED_STAGE_IDS[9], 94: EXPECTED_STAGE_IDS[12],
    96: EXPECTED_STAGE_IDS[13], 101: EXPECTED_STAGE_IDS[14],
    107: EXPECTED_STAGE_IDS[17], 117: EXPECTED_STAGE_IDS[19],
    120: EXPECTED_STAGE_IDS[20], 125: EXPECTED_STAGE_IDS[22],
    135: EXPECTED_STAGE_IDS[26], 140: EXPECTED_STAGE_IDS[28],
    143: EXPECTED_STAGE_IDS[29],
}
TRACE_IGNORED_LINES = (37, 38, 40, 42, 43, 44, 70, 147, 158)


def source_mapping():
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def catalog():
    return LegacyPipelineCatalog.from_json(
        CATALOG_PATH.read_text(encoding="utf-8"))


def by_key(value, key):
    return next(row for row in value.bindings if row.legacy_key == key)


def trace_key(line):
    return ("project/03_src/rebuild_reuse.sh", line)


@test("USB reuse catalog binds the exact declaration and current driver bytes")
def t_exact_files_and_driver():
    value = catalog()
    eq(value.project_slug, "usb-hub-3s-v4", "project identity")
    eq(value.driver_relative_path, "03_src/rebuild_reuse.sh", "driver path")
    eq(value.driver_sha256, EXPECTED_DRIVER_SHA256, "catalog driver digest")
    driver = DRIVER_PATH.read_bytes()
    check(value.driver_matches(driver), "current rebuild_reuse.sh bytes drifted")
    check(not value.driver_matches(driver + b"\n"),
          "mutated driver bytes matched the catalog")


@test("USB reuse catalog preserves all 32 observed stages in exact order")
def t_order_and_denominator():
    value = catalog()
    eq(len(value.bindings), 32, "catalog denominator")
    eq(value.observed_stage_ids(), EXPECTED_STAGE_IDS, "legacy order")
    plan = value.stage_registry().resolve(
        available=("usbv4_reuse_source_tree",))
    eq(tuple(stage.id for stage in plan), EXPECTED_STAGE_IDS,
       "strict one-fact dependency order")
    for prior, current in zip(value.bindings, value.bindings[1:]):
        eq(current.dependencies, (prior.spec.id,),
           f"{current.legacy_key} direct dependency")
        eq(tuple(current.spec.requires), tuple(prior.spec.produces),
           f"{current.legacy_key} semantic handoff")


@test("USB reuse commands remain portable inert argv data")
def t_portable_nonexecuting_commands():
    value = catalog()
    check(not hasattr(value, "execute"), "catalog unexpectedly exposes execution")
    for row in value.bindings:
        eq(row.cwd, ".", f"{row.legacy_key} cwd")
        if row.argv is not None:
            joined = "\0".join(row.argv)
            check("/home/" not in joined, f"{row.legacy_key} captured a host path")
            check("$(" not in joined and ";" not in joined,
                  f"{row.legacy_key} argv became shell syntax")
        for path in row.accepted_output_paths:
            check(not path.startswith("/") and ".." not in Path(path).parts,
                  f"{row.legacy_key} output path is not normalized: {path}")
    python_rows = [row for row in value.bindings
                   if row.argv and row.argv[0] == "/usr/bin/python3"]
    check(python_rows, "no Python command evidence was cataloged")
    check(all("{repo}/" in row.argv[1] for row in python_rows),
          "Python tool paths are not portable {repo} literals")


@test("USB reuse keeps all three rule rewrites as distinct stages")
def t_repeated_rules_distinct():
    value = catalog()
    rows = tuple(by_key(value, key) for key in (
        "rules-pre-placement-drc", "rules-pre-route-prep", "rules-post-stitch"))
    eq(tuple(row.sequence for row in rows), (16, 19, 28), "rule positions")
    eq(tuple(row.spec.id for row in rows), (
        "USBV4-R-RULES-PRE-PLACEMENT-DRC",
        "USBV4-R-RULES-PRE-ROUTE-PREP",
        "USBV4-R-RULES-POST-STITCH",
    ), "distinct rule stage identities")
    check(rows[0].argv == rows[1].argv == rows[2].argv,
          "repeated rule producer argv drifted")
    check(len({tuple(row.spec.produces) for row in rows}) == 3,
          "repeated rules reused one semantic output")


@test("USB reuse records the current generic-board audit as explicit N/A")
def t_board_audit_na():
    value = catalog()
    row = by_key(value, "board-audit-na")
    eq(row.sequence, 11, "N/A position")
    eq(row.applicability, "NOT_APPLICABLE", "N/A applicability")
    eq(row.applicability_reason,
       "generic-backend board has no 03_src/audit_board.py", "N/A reason")
    eq(row.shell_builtin, "not_applicable", "N/A command token")
    eq(row.accepted_output_symbols, (), "N/A accepted symbols")
    eq(row.accepted_output_paths, (), "N/A accepted paths")
    check(not (PROJECT / "03_src" / "audit_board.py").exists(),
          "catalog says N/A but audit_board.py now exists")


@test("USB reuse import evidence agrees with promoted-route configuration")
def t_promoted_import():
    value = catalog()
    route = yaml.safe_load(ROUTE_PATH.read_text(encoding="utf-8"))
    eq(route["route"]["import_source"], "promoted", "route import policy")
    eq(route["route"]["final"], "03_src/route/r8.kicad_pcb",
       "promoted route subject")
    row = by_key(value, "route-import")
    eq(row.sequence, 24, "route import position")
    eq(row.argv, (
        "/usr/bin/python3",
        "{repo}/skills/kicad-pcb/scripts/route_and_stitch_generic.py",
        "import",
        "03_src/route.yaml",
    ), "reuse import argv")
    check("--route-source" not in row.argv,
          "catalog invented a flag absent from rebuild_reuse.sh")
    marker = by_key(value, "route-marker-reset")
    eq((marker.authority, marker.authority_binding),
       ("ignored_until", "route-import"), "ignored marker-reset authority")


@test("USB reuse producer reports retain their later postcheck authority")
def t_postcheck_authority():
    value = catalog()
    placement = by_key(value, "placement-drc-report")
    layout = by_key(value, "layout-drc-report")
    eq((placement.authority, placement.authority_binding),
       ("postcheck", "placement-drc-verdict"), "placement DRC authority")
    eq((layout.authority, layout.authority_binding),
       ("postcheck", "layout-drc-verdict"), "layout DRC authority")


@test("USB reuse xtrace line map covers the exact catalog without executing it")
def t_xtrace_map():
    source_lines = DRIVER_PATH.read_text(encoding="utf-8").splitlines()
    all_declared = (set(TRACE_STAGE_LINES) | set(TRACE_FAILURE_LINES) |
                    set(TRACE_IGNORED_LINES))
    check(max(all_declared) <= len(source_lines), "trace line exceeds driver")
    for line in all_declared:
        text = source_lines[line - 1].strip()
        check(text and not text.startswith("#"),
              f"trace line {line} no longer names executable shell text")

    records = [
        f"+PIPELINE_TRACE:{DRIVER_PATH}:{line}: opaque line {line}"
        for line in sorted(TRACE_STAGE_LINES)
    ]
    observed = parse_xtrace(
        "\n".join(records) + "\n",
        {trace_key(line): stage for line, stage in TRACE_STAGE_LINES.items()},
        project_root=PROJECT, repo_root=ROOT,
        expected_driver_sha256=EXPECTED_DRIVER_SHA256,
        trace_driver_sha256=EXPECTED_DRIVER_SHA256, trace_complete=True)
    eq(observed.observed_stage_ids, EXPECTED_STAGE_IDS,
       "source-line observation order")
    check(observed.fully_mapped, "declared USB trace retained unmapped commands")


@test("USB reuse catalog REFUSES a severed semantic chain",
      kind="known_bad")
def t_mutated_catalog_refused():
    clean = source_mapping()
    LegacyPipelineCatalog.from_mapping(copy.deepcopy(clean))
    broken = copy.deepcopy(clean)
    broken["bindings"][18]["dependencies"] = []
    try:
        LegacyPipelineCatalog.from_mapping(broken)
    except CatalogValidationError as exc:
        check("missing from dependencies" in str(exc),
              f"severed-chain diagnosis: {exc}")
    else:
        raise AssertionError("catalog with a severed dependency SHOULD HAVE FAILED")


if __name__ == "__main__":
    raise SystemExit(main())
