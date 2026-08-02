#!/usr/bin/env python3
"""T2: fast PCB orchestration, handoff freshness, and timing budgets."""
import importlib.util
import hashlib
import json
import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, SCRIPTS, check, contains, eq, main, must_fail,  # noqa: E402
                     must_pass, not_contains, run, test, tmpdir)

FLOW = SCRIPTS / "pcb_flow.py"


def scratch(*, dirty=False, overlap=False, noflow=False, extra_tool=None):
    root = tmpdir("t2flow_")
    for rel in ("02_parts/X", "03_src/rules", "03_tscircuit/src", "04_kicad",
                "06_build/drc"):
        (root / rel).mkdir(parents=True, exist_ok=True)
    copper = {
        "deterministic": ["stitch.seed_stubs", "route.final"],
        "stochastic": ["route.waves"],
    }
    if overlap:
        copper["stochastic"].append("route.final")
    route = {
        "project": {"name": "fixture", "board": "04_kicad/fixture.kicad_pcb",
                    "build_dir": "06_build/route"},
        "route": {"waves": [{"name": "sig"}],
                  "final": "03_src/route/r1.kicad_pcb"},
        "stitch": {"seed_stubs": {"stubs": []}},
    }
    if not noflow:
        route["flow"] = {
            "owner": {"stage": "routing",
                      "files": ["03_src/route.yaml", "03_src/floorplan.yaml"]},
            "copper": copper,
            "budgets_s": {},
        }
        if extra_tool:
            route["flow"]["inputs"] = {"tools": [str(extra_tool)]}
    (root / "03_src/route.yaml").write_text(yaml.safe_dump(route, sort_keys=False))
    (root / "03_src/floorplan.yaml").write_text("board: fixture\n")
    (root / "03_src/rebuild_all.sh").write_text("#!/bin/bash\nexit 0\n")
    (root / "03_src/rules/rf.yaml").write_text(yaml.safe_dump({
        "schema": 1,
        "rf": {"enabled": False,
               "rationale": "This orchestration fixture has no RF paths."},
    }, sort_keys=False))
    (root / "03_tscircuit/src/fixture.tsx").write_text("export const x = 1\n")
    (root / "03_tscircuit/manifest.yaml").write_text("components: [X1]\n")
    (root / "03_tscircuit/package.json").write_text('{"name":"fixture"}\n')
    (root / "03_tscircuit/net_aliases.txt").write_text("5V=V5\n")
    (root / "02_parts/X/part.yaml").write_text(
        "mpn: X\nescape: {style: passive, pitch: 1.0, "
        "tier_required: jlc_2layer_default, checked: escape_check}\n")
    (root / "04_kicad/fixture.kicad_pcb").write_text("(kicad_pcb fixture)\n")
    (root / "04_kicad/fixture.kicad_sch").write_text("(kicad_sch fixture)\n")
    (root / "04_kicad/fixture.kicad_pro").write_text('{"board":{}}\n')
    (root / "04_kicad/fixture.kicad_dru").write_text("(version 1)\n")
    gate = {"violations": ([{"type": "clearance"}] if dirty else []),
            "unconnected_items": [], "schematic_parity": []}
    # Gate last: a valid gate must post-date the board and DRC semantics.
    (root / "06_build/drc/gate.json").write_text(json.dumps(gate))
    return root


def flow(root, *args):
    return run([KPY, FLOW, *args, root])


def load_flow_module():
    spec = importlib.util.spec_from_file_location("pcb_flow_under_test", FLOW)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def reviewed_repo(*, scoped=False):
    root = scratch()
    if scoped:
        (root / "03_src/a").mkdir()
        (root / "03_src/b").mkdir()
        (root / "03_src/a/custom.yaml").write_text("board_input: true\n")
        (root / "03_src/b/unrelated.yaml").write_text("sibling: true\n")
        route_path = root / "03_src/route.yaml"
        route = yaml.safe_load(route_path.read_text())
        route["flow"]["inputs"] = {
            "include": ["03_src/a"],
            "parts": ["02_parts/X"],
        }
        route_path.write_text(yaml.safe_dump(route, sort_keys=False))
    board_hash = hashlib.sha256(
        (root / "04_kicad/fixture.kicad_pcb").read_bytes()).hexdigest()
    schematic_hash = hashlib.sha256(
        (root / "04_kicad/fixture.kicad_sch").read_bytes()).hexdigest()
    reviews = root / "08_reviews"
    reviews.mkdir()
    specs = {
        "x_pin_review.md": ("board_sha256", board_hash),
        "x_render_review.md": ("board_sha256", board_hash),
        "x_redteam_topology.md": ("board_sha256", board_hash),
        "x_redteam_layout.md": ("board_sha256", board_hash),
        "x_rf_schematic.md": ("artifact_sha256", schematic_hash),
        "x_rf_pcb.md": ("artifact_sha256", board_hash),
    }
    for name, (field, digest) in specs.items():
        (reviews / name).write_text(
            "source_commit: COMMIT\n"
            f"{field}: {digest}\n"
            "design_verdict: SOUND\n")
    must_pass(run(["git", "init", "-q"], cwd=root), "fixture git init")
    must_pass(run(["git", "config", "user.email", "test@example.invalid"],
                  cwd=root), "fixture git email")
    must_pass(run(["git", "config", "user.name", "PCB Flow Test"], cwd=root),
              "fixture git name")
    # Reviews must name the commit they are part of; use a fixed-point-free
    # two-commit history where the source commit contains build inputs and the
    # later commit contains exact reviews naming that source commit.
    must_pass(run(["git", "add", "."], cwd=root), "fixture stage source")
    must_pass(run(["git", "commit", "-qm", "source"], cwd=root),
              "fixture source commit")
    source = must_pass(run(["git", "rev-parse", "HEAD"], cwd=root),
                       "fixture source sha").out.strip()
    for path in reviews.iterdir():
        path.write_text(path.read_text().replace("COMMIT", source))
    must_pass(run(["git", "add", "08_reviews"], cwd=root),
              "fixture stage reviews")
    must_pass(run(["git", "commit", "-qm", "reviews"], cwd=root),
              "fixture review commit")
    return root, source


def provenance_fails(module, root, commit, needle):
    try:
        module.reviewed_commit_provenance(module.resolve_context(root), commit)
    except module.FlowError as exc:
        contains(str(exc), needle, "reviewed-commit refusal")
        return
    raise AssertionError(f"reviewed-commit unexpectedly accepted: {needle}")


@test("handoff is compact, binds all evidence, and validates current inputs")
def t_handoff_green():
    root = scratch()
    r = must_pass(flow(root, "handoff"), "clean handoff")
    contains(r.out, "stage routing", "clean DRC without a fresh seal witness")
    handoff = root / "06_build/agent_handoff.yaml"
    check(handoff.stat().st_size < 16 * 1024, "handoff exceeded intake budget")
    doc = yaml.safe_load(handoff.read_text())
    eq(doc["schema"], 2, "hardened handoff schema")
    eq(doc["metrics"]["drc"],
       {"violations": 0, "unconnected": 0, "parity": 0}, "DRC tuple")
    for key in ("source", "board", "tools", "gate"):
        check(doc["inputs"].get(key, "").startswith("sha256:"), f"bound {key}")
    must_pass(flow(root, "validate"), "fresh handoff validation")


@test("a clean but unwitnessed gate cannot claim layout_sealed", kind="known_bad")
def t_kb_clean_unwitnessed_seal():
    root = scratch()
    r = run([KPY, FLOW, "handoff", root, "--stage", "layout_sealed"])
    must_fail(r, "unwitnessed layout seal", "fresh layout-seal witness")


@test("semantic source hash ignores YAML formatting-only rewrites")
def t_semantic_hash():
    root = scratch()
    must_pass(flow(root, "handoff"), "baseline handoff")
    path = root / "03_src/route.yaml"
    data = yaml.safe_load(path.read_text())
    path.write_text(yaml.safe_dump(data, sort_keys=True, width=60))
    must_pass(flow(root, "validate"), "format-only rewrite")


@test("top-level tscircuit controls and KiCad sidecars stale handoffs",
      kind="known_bad")
def t_kb_complete_source_classes():
    mutations = {
        "03_tscircuit/manifest.yaml": "components: [X1, X2]\n",
        "03_tscircuit/package.json": '{"name":"fixture","version":"2"}\n',
        "03_tscircuit/net_aliases.txt": "5V=V5\n12V=V12\n",
        "04_kicad/fixture.kicad_sch": "(kicad_sch changed)\n",
        "04_kicad/fixture.kicad_pro": '{"board":{"rules":"changed"}}\n',
        "04_kicad/fixture.kicad_dru": "(version 2)\n",
    }
    for rel, changed in mutations.items():
        root = scratch()
        must_pass(flow(root, "handoff"), f"baseline for {rel}")
        path = root / rel
        path.write_text(changed)
        must_fail(flow(root, "validate"), f"stale {rel}", "source hash changed")


@test("review archive bytes are part of the seal source witness",
      kind="known_bad")
def t_kb_review_mutation_stales_handoff():
    root = scratch()
    reviews = root / "08_reviews"
    reviews.mkdir()
    review = reviews / "rf_pcb.md"
    review.write_text("design_verdict: SOUND\n")
    must_pass(flow(root, "handoff"), "review-bound handoff")
    review.write_text("design_verdict: DEFECTIVE\n")
    must_fail(flow(root, "validate"), "changed review bytes",
              "source hash changed")


@test("shared tool identity is independently content-addressed", kind="known_bad")
def t_kb_tool_stale():
    tool = tmpdir("t2flow_tool_") / "producer.py"
    tool.write_text("VERSION = 1\n")
    root = scratch(extra_tool=tool)
    must_pass(flow(root, "handoff"), "tool-bound baseline")
    tool.write_text("VERSION = 2\n")
    must_fail(flow(root, "validate"), "stale tool handoff", "tool hash changed")


@test("handoff rejects source changes instead of handing stale context onward",
      kind="known_bad")
def t_kb_source_stale():
    root = scratch()
    must_pass(flow(root, "handoff"), "baseline handoff")
    (root / "03_src/floorplan.yaml").write_text("board: changed\n")
    r = must_fail(flow(root, "validate"), "stale source handoff",
                  "source hash changed")
    eq(r.rc, 2, "distinct stale exit")


@test("handoff generation rejects DRC evidence older than its board",
      kind="known_bad")
def t_kb_stale_gate_generation():
    root = scratch()
    board = root / "04_kicad/fixture.kicad_pcb"
    board.write_text("(kicad_pcb newer)\n")
    gate_ns = (root / "06_build/drc/gate.json").stat().st_mtime_ns
    os.utime(board, ns=(gate_ns + 1_000_000_000, gate_ns + 1_000_000_000))
    r = must_fail(flow(root, "handoff"), "stale gate generation",
                  "DRC gate is older")
    check(not (root / "06_build/agent_handoff.yaml").exists(),
          "stale metrics must not be published")


@test("handoff validation binds the exact DRC gate", kind="known_bad")
def t_kb_gate_hash_stale():
    root = scratch()
    must_pass(flow(root, "handoff"), "baseline handoff")
    gate = root / "06_build/drc/gate.json"
    gate.write_text(json.dumps({"violations": [{"type": "clearance"}],
                                "unconnected_items": [],
                                "schematic_parity": []}))
    must_fail(flow(root, "validate"), "changed gate", "gate hash changed")


@test("handoff rejects a changed generated board independently of source",
      kind="known_bad")
def t_kb_board_stale():
    root = scratch()
    must_pass(flow(root, "handoff"), "baseline handoff")
    (root / "04_kicad/fixture.kicad_pcb").write_text("(kicad_pcb changed)\n")
    r = must_fail(flow(root, "validate"), "stale board handoff", "board hash changed")
    eq(r.rc, 2, "distinct stale exit")


@test("dirty DRC cannot be labeled layout_sealed", kind="known_bad")
def t_kb_dirty_seal_stage():
    root = scratch(dirty=True)
    r = run([KPY, FLOW, "handoff", root, "--stage", "layout_sealed"])
    must_fail(r, "dirty layout seal", "requires DRC 0/0/0")
    check(not (root / "06_build/agent_handoff.yaml").exists(),
          "a rejected seal must not leave a handoff")


@test("one copper config path cannot have deterministic and stochastic owners",
      kind="known_bad")
def t_kb_copper_ownership_overlap():
    root = scratch(overlap=True)
    marker = root / "06_build/layout_seal.json"
    marker.write_text("old witness\n")
    r = must_fail(run([KPY, FLOW, "layout-seal", root]),
                  "overlapping copper ownership", "both deterministic and stochastic")
    eq(r.rc, 1, "configuration exit")
    eq(marker.read_text(), "old witness\n", "config validates before seal mutation")


@test("ownership may reserve a promoted board before the first route")
def t_future_owned_board():
    root = scratch()
    future = root / "03_src/route/final.kicad_pcb"
    data = yaml.safe_load((root / "03_src/route.yaml").read_text())
    data["flow"]["owner"]["files"].append("03_src/route/final.kicad_pcb")
    (root / "03_src/route.yaml").write_text(yaml.safe_dump(data, sort_keys=False))
    must_pass(flow(root, "handoff"), "reserved future promoted board")
    check(not future.exists(), "validation must not manufacture the output")


@test("missing non-board ownership paths remain configuration errors",
      kind="known_bad")
def t_kb_missing_owned_source():
    root = scratch()
    data = yaml.safe_load((root / "03_src/route.yaml").read_text())
    data["flow"]["owner"]["files"].append("03_src/typo.yaml")
    (root / "03_src/route.yaml").write_text(yaml.safe_dump(data, sort_keys=False))
    must_fail(flow(root, "handoff"), "missing owned source", "does not exist")


@test("legacy projects are explicit rather than mislabeled as routing")
def t_legacy_state():
    root = scratch(noflow=True)
    must_pass(flow(root, "handoff"), "legacy handoff")
    doc = yaml.safe_load((root / "06_build/agent_handoff.yaml").read_text())
    eq(doc["stage"], "legacy_unmigrated", "legacy lifecycle state")


@test("timed run records evidence and returns the distinct budget-regression exit")
def t_budget_timing():
    root = scratch()
    r = run([KPY, FLOW, "run", root, "--stage", "unit_probe", "--budget-s", "0",
             "--", KPY, "-c", "pass"])
    eq(r.rc, 6, "budget exit")
    contains(r.out, "BUDGET EXCEEDED", "budget finding")
    perf = json.loads((root / "06_build/performance.json").read_text())
    row = perf["runs"][-1]
    eq(row["stage"], "unit_probe", "timed stage")
    check(row["over_budget"] is True and row["rc"] == 0,
          "evidence distinguishes a good command from a slow command")


@test("router pass timing composes with the single-board flow log")
def t_router_pass_timing():
    root = scratch()
    must_pass(run([KPY, FLOW, "run", root, "--stage", "outer", "--",
                   KPY, "-c", "pass"]), "outer timing sample")
    router = SCRIPTS / "route_and_stitch_generic.py"
    code = (
        "import importlib.util,pathlib,sys\n"
        "s=importlib.util.spec_from_file_location('router',sys.argv[1])\n"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m)\n"
        "m.record_pass_timing({'_root':pathlib.Path(sys.argv[2])},"
        "'stitch','fill',1.25,counters={'zones':4})\n")
    must_pass(run([KPY, "-c", code, router, root]), "router timing writer")
    rows = json.loads((root / "06_build/performance.json").read_text())["runs"]
    eq(len(rows), 2, "shared timing rows")
    eq(rows[-1]["stage"], "stitch:fill", "pass stage")
    eq(rows[-1]["counters"], {"zones": 4}, "pass counters")


@test("layout-seal dry-run places P-LAND after the canonical rebuild")
def t_layout_seal_dry_run():
    root = scratch()
    r = must_pass(run([KPY, FLOW, "layout-seal", root, "--dry-run"]),
                  "layout seal dry run")
    for needle in ("escape_check.py", "tier_preflight.py", "rebuild_all.sh",
                   "[escape_lands]", "--schematic-parity",
                   "fabrication/PCBA release not sealed"):
        contains(r.out, needle, "layout-seal command plan")
    check(r.out.index("rebuild_all.sh") < r.out.index("[escape_lands]"),
          "fresh-board P-LAND must run after rebuild")
    check(not (root / "06_build/agent_handoff.yaml").exists(),
          "dry-run must not claim a handoff or seal")


@test("reviewed-commit seal plan does not rebuild signed bytes")
def t_reviewed_commit_seal_dry_run():
    root = scratch()
    r = must_pass(run([KPY, FLOW, "layout-seal", root,
                       "--reviewed-commit", "0" * 40, "--dry-run"]),
                  "reviewed commit seal dry run")
    not_contains(r.out, "[rebuild]", "signed artifact must not be rebuilt")
    contains(r.out, "[escape_lands]", "landability is revalidated")
    contains(r.out, "[placement_clearance]", "P-BODYCLR is revalidated")
    contains(r.out, "[critical_pair_map]", "R-PAIRMAP is revalidated")
    contains(r.out, "[critical_route_connected]", "R-CRITESC is revalidated")
    contains(r.out, "[pre_route_placement]", "placement review is revalidated")
    contains(r.out, "[rf_reviews]", "exact RF reviews are revalidated")
    contains(r.out, "--schematic-parity", "exact DRC is revalidated")


@test("reviewed-commit recovery is commit-, input-, and review-bound")
def t_reviewed_commit_provenance():
    module = load_flow_module()

    root, source = reviewed_repo()
    proof = module.reviewed_commit_provenance(module.resolve_context(root), source)
    eq(proof["method"], "reviewed_commit", "witness method")
    eq(proof["source_commit"], source, "explicit source commit")

    dirty, dirty_source = reviewed_repo()
    (dirty / "03_src/floorplan.yaml").write_text("board: changed\n")
    provenance_fails(module, dirty, dirty_source, "byte mismatch")

    deleted, deleted_source = reviewed_repo()
    (deleted / "03_tscircuit/net_aliases.txt").unlink()
    provenance_fails(module, deleted, deleted_source, "build-input set differs")

    scoped, scoped_source = reviewed_repo(scoped=True)
    (scoped / "03_src/a/custom.yaml").unlink()
    provenance_fails(module, scoped, scoped_source, "build-input set differs")

    isolated, isolated_source = reviewed_repo(scoped=True)
    (isolated / "03_src/b/unrelated.yaml").write_text("sibling: changed\n")
    module.reviewed_commit_provenance(
        module.resolve_context(isolated), isolated_source)

    board, board_source = reviewed_repo()
    (board / "04_kicad/fixture.kicad_pcb").write_text("(kicad_pcb edited)\n")
    provenance_fails(module, board, board_source, "byte mismatch")

    review, review_source = reviewed_repo()
    pin = review / "08_reviews/x_pin_review.md"
    pin.write_text(pin.read_text().replace(review_source, "0" * 40))
    provenance_fails(module, review, review_source, "pin review coverage")

    other, other_source = reviewed_repo()
    orphan = must_pass(
        run(["git", "commit-tree", "HEAD^{tree}", "-m", "orphan"], cwd=other),
        "fixture orphan commit").out.strip()
    provenance_fails(module, other, orphan, "not an ancestor")


@test("reviewed-commit witness revalidates provenance, not only file hashes",
      kind="known_bad")
def t_kb_reviewed_commit_history_rewrite():
    module = load_flow_module()
    root, source = reviewed_repo()
    ctx = module.resolve_context(root)
    provenance = module.reviewed_commit_provenance(ctx, source)
    ctx.seal.write_text(json.dumps(module.seal_witness_document(
        ctx, provenance)))
    check(module.seal_witness_valid(ctx), "baseline reviewed witness")
    orphan = must_pass(
        run(["git", "commit-tree", "HEAD^{tree}", "-m", "replacement"], cwd=root),
        "replacement history commit").out.strip()
    must_pass(run(["git", "update-ref", "HEAD", orphan], cwd=root),
              "replace fixture history without changing files")
    check(not module.seal_witness_valid(ctx),
          "history rewrite must stale reviewed-commit provenance")


@test("adopted pcb-flow preflight runs P-MOD first; legacy remains explicit")
def t_module_first_preflight():
    root = scratch()
    legacy = must_pass(run([KPY, FLOW, "preflight", root, "--dry-run"]),
                       "legacy preflight plan")
    not_contains(legacy.out, "module_first_check.py", "unmigrated compatibility")
    (root / "03_src/rules").mkdir(parents=True, exist_ok=True)
    (root / "03_src/rules/integration.yaml").write_text(
        "schema: 1\ndefault: prefer_module\nselections: []\n"
        "no_applicable_functions: This fixture has no complex subsystem in scope.\n")
    adopted = must_pass(run([KPY, FLOW, "preflight", root, "--dry-run"]),
                        "adopted preflight plan")
    contains(adopted.out, "[module_first]", "P-MOD stage")
    check(adopted.out.index("module_first_check.py") <
          adopted.out.index("escape_check.py"), "P-MOD must run first")


@test("pcb-flow preflight places the authoritative P-ADJ policy phase before "
      "router spend")
def t_placement_policy_preflight():
    root = scratch()
    plan = must_pass(run([KPY, FLOW, "preflight", root, "--dry-run"]),
                     "preflight plan")
    contains(plan.out, "[placement_policy]", "placement policy stage")
    contains(plan.out, "--phase placement", "authoritative policy subset")
    check(plan.out.index("[placement_policy]") < plan.out.index("[tier_preflight]"),
          "P-ADJ must run before routing preflight/spend")


@test("adopted pcb-flow runs early electrical design before every schematic, "
      "placement, and routing gate")
def t_early_design_preflight():
    root = scratch()
    rules = root / "03_src/rules"
    rules.mkdir(parents=True, exist_ok=True)
    (rules / "requirements.yaml").write_text(
        "schema: 1\npower_claims: []\n"
        "no_external_power_outputs: Fixture has no external power output.\n")
    plan = must_pass(run([KPY, FLOW, "preflight", root, "--dry-run"]),
                     "adopted preflight plan")
    contains(plan.out, "[early_design]", "early electrical stage")
    check(plan.out.index("[early_design]") <
          plan.out.index("[pre_route_schematic]") <
          plan.out.index("[pin_map]") <
          plan.out.index("[critical_pair_map]") <
          plan.out.index("[tier_preflight]"),
          "early electrical and critical-pair gates must follow stage ownership")
    for stage in ("build_freshness", "net_label_survival",
                  "electrical_invariants", "adr_coverage", "power_topology",
                  "power_margin", "off_control", "count_parity", "circuit_bom"):
        contains(plan.out, f"[{stage}]", "complete authoring semantic battery")


@test("pcb-flow preflight runs P-PINMAP as its first board-artifact gate")
def t_pin_map_preflight():
    root = scratch()
    plan = must_pass(run([KPY, FLOW, "preflight", root, "--dry-run"]),
                     "preflight plan")
    contains(plan.out, "[pin_map]", "pin-map stage")
    contains(plan.out, "pin_map_check.py", "shared pin-map checker")
    check(plan.out.index("[pin_map]") < plan.out.index("[escape_lands]")
          < plan.out.index("[placement_policy]")
          < plan.out.index("[tier_preflight]"),
          "P-PINMAP must precede land, placement, and routing checks")


@test("pcb-flow preflight makes both exact-artifact review boundaries blocking")
def t_pre_route_review_preflight():
    root = scratch()
    plan = must_pass(run([KPY, FLOW, "preflight", root, "--dry-run"]),
                     "preflight plan")
    contains(plan.out, "[pre_route_schematic]", "schematic review stage")
    contains(plan.out, "[pre_route_placement]", "placement review stage")
    check(plan.out.count("pre_route_review_check.py") == 2,
          "preflight must run each PR-REVIEW phase exactly once")
    check(plan.out.index("[pre_route_schematic]") <
          plan.out.index("[pre_route_placement]") <
          plan.out.index("[tier_preflight]"),
          "both independent review phases must precede routing preflight")


@test("pcb-flow direct preflight cannot bypass either exact pre-route review "
      "boundary")
def t_pre_route_reviews_in_preflight():
    root = scratch()
    plan = must_pass(run([KPY, FLOW, "preflight", root, "--dry-run"]),
                     "preflight plan")
    contains(plan.out, "[pre_route_schematic]", "schematic review stage")
    contains(plan.out, "[pre_route_placement]", "placement review stage")
    check(plan.out.index("[pre_route_schematic]") <
          plan.out.index("[placement_policy]") <
          plan.out.index("[pre_route_placement]") <
          plan.out.index("[tier_preflight]"),
          "topology review must precede placement policy, whose exact board "
          "must then be reviewed before the router preflight")


@test("successful seal is transactional and every bound class can stale it")
def t_executable_seal_and_tamper():
    module = load_flow_module()
    root = scratch()
    ctx = module.resolve_context(root)
    original = module.run_timed

    def fake_run(_ctx, stage, _command, _budget=None):
        if stage == "layout_drc":
            _ctx.gate.parent.mkdir(parents=True, exist_ok=True)
            _ctx.gate.write_text(json.dumps({"violations": [],
                                             "unconnected_items": [],
                                             "schematic_parity": []}))
        return 0

    module.run_timed = fake_run
    try:
        eq(module.cmd_layout_seal(ctx, False), 0, "executable seal")
        check(ctx.seal.is_file() and ctx.handoff.is_file(), "seal artifacts")
        eq(module.validate_handoff(ctx), 0, "fresh sealed handoff")
        ctx.board.with_suffix(".kicad_dru").write_text("(version 2)\n")
        eq(module.validate_handoff(ctx), 2, "rule tamper stales seal")
    finally:
        module.run_timed = original


@test("handoff preparation failure cannot leave a layout witness", kind="known_bad")
def t_kb_seal_failure_atomicity():
    module = load_flow_module()
    root = scratch()
    ctx = module.resolve_context(root)
    original_run, original_text = module.run_timed, module.handoff_text

    def fake_run(_ctx, stage, _command, _budget=None):
        if stage == "layout_drc":
            _ctx.gate.write_text(json.dumps({"violations": [],
                                             "unconnected_items": [],
                                             "schematic_parity": []}))
        return 0

    def fail_handoff(*_args, **_kwargs):
        raise module.FlowError("synthetic handoff failure")

    module.run_timed, module.handoff_text = fake_run, fail_handoff
    try:
        failed = False
        try:
            module.cmd_layout_seal(ctx, False)
        except module.FlowError as exc:
            failed = "synthetic handoff failure" in str(exc)
        check(failed, "synthetic handoff failure must propagate")
        check(not ctx.seal.exists(), "failed handoff must not leave witness")
    finally:
        module.run_timed, module.handoff_text = original_run, original_text


def multi_scratch():
    root = tmpdir("t2flow_multi_")
    for board in ("a", "b"):
        for rel in (f"02_parts/{board.upper()}", f"03_src/{board}",
                    "03_tscircuit/src", "04_kicad", f"06_build/{board}/drc"):
            (root / rel).mkdir(parents=True, exist_ok=True)
        route = {
            "project": {"name": board, "board": f"04_kicad/{board}.kicad_pcb"},
            "flow": {
                "owner": {"stage": "routing",
                          "files": [f"03_src/{board}/route.yaml"]},
                "copper": {"deterministic": ["route.final"],
                           "stochastic": ["route.waves"]},
                "inputs": {
                    "include": [f"03_src/{board}",
                                f"03_tscircuit/src/{board}.tsx"],
                    "parts": [f"02_parts/{board.upper()}"],
                },
            },
            "route": {"waves": [], "final": f"03_src/{board}/final.kicad_pcb"},
        }
        (root / f"03_src/{board}/route.yaml").write_text(
            yaml.safe_dump(route, sort_keys=False))
        (root / f"03_src/{board}/rebuild_all.sh").write_text("#!/bin/bash\nexit 0\n")
        (root / f"03_tscircuit/src/{board}.tsx").write_text(f"export const {board}=1\n")
        (root / f"02_parts/{board.upper()}/part.yaml").write_text(
            f"mpn: {board.upper()}\nescape: {{style: passive, pitch: 1.0}}\n")
        (root / f"04_kicad/{board}.kicad_pcb").write_text(f"(kicad_pcb {board})\n")
        (root / f"06_build/{board}/drc/gate.json").write_text(
            json.dumps({"violations": [], "unconnected_items": [],
                        "schematic_parity": []}))
    return root


@test("multi-board selection isolates inputs, packages, and state")
def t_multi_board_isolation():
    root = multi_scratch()
    must_fail(run([KPY, FLOW, "handoff", root]), "ambiguous multi-board root",
              "choose --board")
    must_pass(run([KPY, FLOW, "handoff", root, "--board", "a"]), "board a handoff")
    check((root / "06_build/a/agent_handoff.yaml").is_file(), "board a state path")
    check(not (root / "06_build/b/agent_handoff.yaml").exists(),
          "board b state must not be overwritten")
    dry = must_pass(run([KPY, FLOW, "preflight", root, "--board", "a", "--dry-run"]),
                    "board a preflight")
    contains(dry.out, "02_parts/A/part.yaml", "selected package")
    not_contains(dry.out, "02_parts/B/part.yaml", "sibling package")
    (root / "03_tscircuit/src/b.tsx").write_text("export const b=2\n")
    must_pass(run([KPY, FLOW, "validate", root, "--board", "a"]),
              "sibling edit does not stale board a")
    (root / "03_tscircuit/src/a.tsx").write_text("export const a=2\n")
    must_fail(run([KPY, FLOW, "validate", root, "--board", "a"]),
              "selected-board edit", "source hash changed")


@test("multi-board router timing and grind evidence use the selected state path")
def t_multi_board_worker_state():
    root = multi_scratch()
    router = SCRIPTS / "route_and_stitch_generic.py"
    config = root / "03_src/a/route.yaml"
    code = (
        "import importlib.util,sys\n"
        "s=importlib.util.spec_from_file_location('router',sys.argv[1])\n"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m)\n"
        "c=m.load_cfg(sys.argv[2]);m.record_pass_timing(c,'route','a',1.0)\n")
    must_pass(run([KPY, "-c", code, router, config]), "nested router timing")
    check((root / "06_build/a/performance.json").is_file(),
          "router timing must use board a state")
    check(not (root / "06_build/performance.json").exists(),
          "router timing must not use the project-global state")

    stub = root / "clean_gate.py"
    stub.write_text(
        "import json,pathlib,sys\n"
        "pathlib.Path(sys.argv[1]).write_text(json.dumps({"
        "'violations':[],'unconnected_items':[],'schematic_parity':[]}))\n")
    grind = SCRIPTS / "grind_driver.py"
    must_pass(run([KPY, grind, root, "--config", "03_src/a/route.yaml",
                   "--check-cmd", f"{KPY} {stub} {{out}}", "--max-cycles", "1"]),
              "nested grind")
    check((root / "06_build/a/grind/check.json").is_file(),
          "grind scratch must use board a state")
    check((root / "01_docs/journal/routing_a.md").is_file(),
          "grind journal must be board-qualified")


@test("multi-board configs must declare source and part scope", kind="known_bad")
def t_kb_multi_board_scope_required():
    root = multi_scratch()
    route = root / "03_src/a/route.yaml"
    data = yaml.safe_load(route.read_text())
    del data["flow"]["inputs"]
    route.write_text(yaml.safe_dump(data, sort_keys=False))
    must_fail(run([KPY, FLOW, "handoff", root, "--board", "a"]),
              "unscoped multi-board flow", "requires explicit board-scoped")


@test("oversized handoff is rejected before publication", kind="known_bad")
def t_kb_handoff_ceiling():
    root = scratch()
    r = must_fail(run([KPY, FLOW, "handoff", root, "--blocker", "x" * 20000]),
                  "oversized handoff", "ceiling")
    check(not (root / "06_build/agent_handoff.yaml").exists(),
          "oversized handoff must not be published")


@test("grind dry-run delegates to the bounded driver with an explicit cap")
def t_grind_delegation():
    root = scratch(dirty=True)
    r = must_pass(run([KPY, FLOW, "grind", root, "--max-cycles", "7", "--dry-run"]),
                  "grind dry run")
    contains(r.out, "grind_driver.py", "bounded driver")
    contains(r.out, "--max-cycles 7", "explicit grind bound")


if __name__ == "__main__":
    sys.exit(main())
