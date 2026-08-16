#!/usr/bin/env python3
"""T1: independent native-model registration and project orchestration.

The regression fixture starts from the exact Pluto v5 board and exact native
Amphenol model, then changes only J2's internal model offset by 5 mm.  This is
the failure the gate exists to catch: model pixels can remain self-consistent
with their own mesh while missing F.Fab, F.CrtYd, and drilled attachment
datums.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (FAB_SCRIPTS, KPY, ROOT, contains, main, must_fail,  # noqa: E402
                     must_pass, run, test, tmpdir, check, eq)

sys.path.insert(0, str(ROOT / "skills/pcb-design/scripts"))
from pipeline_contract import StageResult  # noqa: E402
from pipeline_readiness import evaluate  # noqa: E402

ENGINE = FAB_SCRIPTS / "native_model_registration.py"
GATE = FAB_SCRIPTS / "model_registration_gate.py"
SOURCE_PROJECT = ROOT / "projects/pluto-rx2-8way-v5"
SOURCE_BOARD = SOURCE_PROJECT / "04_kicad/pluto_rx2_8way_v5.kicad_pcb"
SOURCE_MODEL = (SOURCE_PROJECT /
                "03_src/lib/3dmodels/Amphenol_901_143_6RFX-JLC-C429844.step")


def project_fixture(*, shifted=False, kept_refs=("J2",)):
    project = tmpdir("model_registration_") / "pluto"
    board_dir = project / "04_kicad"
    model_dir = project / "03_src/lib/3dmodels"
    rules_dir = project / "03_src/rules"
    for directory in (board_dir, model_dir, rules_dir):
        directory.mkdir(parents=True, exist_ok=True)
    board = board_dir / SOURCE_BOARD.name
    model = model_dir / SOURCE_MODEL.name
    shutil.copy2(SOURCE_BOARD, board)
    shutil.copy2(SOURCE_MODEL, model)

    # Keep the exact J2 footprint and exact native model.  The optional fault
    # changes only the footprint-local model transform, preserving model bytes.
    mutate = (
        "import pcbnew,sys\n"
        f"p=sys.argv[1]; b=pcbnew.LoadBoard(p); keep=set({tuple(sorted(kept_refs))!r})\n"
        "for fp in b.GetFootprints():\n"
        "  if fp.GetReference() not in keep: fp.Models().clear()\n"
        "  elif fp.GetReference() == 'J2':\n"
        "    models=fp.Models(); model=models[0]\n"
        f"    model.m_Offset.x={5.0 if shifted else 0.0}; models[0]=model\n"
        "b.Save(p)\n"
    )
    must_pass(run([KPY, "-c", mutate, board]), "inject 5 mm model offset")
    model_sha = hashlib.sha256(model.read_bytes()).hexdigest()
    config = {
        "schema": 1,
        "groups": [{
            "id": "shifted_sma",
            "refs": ["J2"],
            "model_sha256": model_sha,
            "fit_tolerance_mm": 1.0,
            "courtyard_containment_tolerance_mm": 0.25,
            "search_margin_mm": 8.0,
            "render_width": 1200,
            "render_height": 800,
        }],
    }
    (rules_dir / "model_registration.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return project, board, model_sha


def broken_project():
    return project_fixture(shifted=True)


def accepted_bytes(path):
    return {
        item.relative_to(path).as_posix(): item.read_bytes()
        for item in path.rglob("*") if item.is_file()
    }


def gate_command(project, board, out="06_build/pre_route/model_registration.md"):
    return [
        KPY, GATE, project, "--board", f"04_kicad/{board.name}",
        "--out", out,
    ]


def readiness_result(project, stage):
    receipts = project / "06_build/receipts"
    receipts.mkdir(parents=True, exist_ok=True)
    shutil.copy2(project / "06_build/pre_route/model_registration.stage.json",
                 receipts / "P-MODEL-REG.json")
    registry = {
        "schema": 1,
        "profile": "model-registration-test",
        "target": "DESIGN_CLEAN",
        "subject": stage.subject.to_mapping(),
        "receipts_dir": "06_build/receipts",
        "stages": [{
            "stage_id": "P-MODEL-REG",
            "required_for": "DESIGN_CLEAN",
            "applicability": "APPLIES",
            "minimum_total": 1,
            "bundles": {
                "model_registration_bundle":
                    "06_build/pre_route/model_registration_bundle/bundle.json",
            },
        }],
    }
    path = project / "03_src/rules/receipt_readiness.yaml"
    path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
    return evaluate(project, path)


@test("model registration publishes a strict tuple receipt and StageResult")
def t_clean_receipt_bundle_and_stage_result():
    project, board, _model_sha = project_fixture()
    first = must_pass(run(gate_command(project, board)),
                      "model registration clean fixture")
    contains(first.out, "P-MODEL-REG PASS: 1/1 group(s) graded",
             "clean aggregate denominator")
    aggregate = (project / "06_build/pre_route/model_registration.md").read_text()
    contains(aggregate, "a-render_verdict: PASS",
             "legacy aggregate verdict remains machine-readable")
    contains(aggregate, f"board_sha256: {hashlib.sha256(board.read_bytes()).hexdigest()}",
             "legacy aggregate board binding remains machine-readable")

    bundle = project / "06_build/pre_route/native_registration/shifted_sma"
    manifest = json.loads((bundle / "bundle.json").read_text())
    receipt = json.loads(
        (bundle / "model_registration_receipt.json").read_text())
    stage = StageResult.from_json(
        (project / "06_build/pre_route/model_registration.stage.json").read_text())
    aggregate_bundle = project / "06_build/pre_route/model_registration_bundle"
    aggregate_manifest = json.loads((aggregate_bundle / "bundle.json").read_text())
    aggregate_index = json.loads(
        (aggregate_bundle / "model_registration_index.json").read_text())
    eq(stage.stage_id, "P-MODEL-REG", "stage id")
    eq(stage.status, "PASS", "outer verdict")
    eq(stage.outputs, ("model_registration_bundle",), "outer output symbol")
    eq(stage.graded, 1, "outer graded groups")
    eq(stage.total, 1, "outer total groups")
    eq(aggregate_manifest["run_id"], stage.run_id,
       "aggregate bundle run matches stage")
    eq(aggregate_manifest["subject"], stage.subject.to_mapping(),
       "aggregate bundle subject matches stage")
    eq(aggregate_index["subject"], stage.subject.to_mapping(),
       "aggregate index subject matches stage")
    eq(aggregate_index["groups"][0]["manifest"],
       "06_build/pre_route/native_registration/shifted_sma/bundle.json",
       "aggregate index points to exact group manifest")
    eq(readiness_result(project, stage)["status"], "PASS",
       "StageResult output reopens through readiness")
    eq(receipt["kind"], "model-registration-receipt-v1", "domain receipt kind")
    eq(set(receipt["tuple"]), {
        "footprint_sha256", "model_sha256", "transform_sha256",
        "contract_sha256", "tool_identity",
    }, "exact tuple fields")
    check("status" not in receipt and "verdict" not in receipt,
          "domain receipt duplicated outer verdict")
    eq(receipt["refs"], ["J2"], "receipt ref denominator")
    eq(receipt["measurements"][0]["attachment_centres_graded"], 5,
       "graded drilled attachment centres")
    eq(receipt["evidence"], sorted(set(receipt["evidence"])),
       "deterministic evidence ordering")
    check((bundle / "native_coupon.kicad_pcb").is_file(),
          "origin-centred coupon persisted")
    for name, record in manifest["outputs"].items():
        artifact = bundle / name
        eq(hashlib.sha256(artifact.read_bytes()).hexdigest(), record["sha256"],
           f"manifest binds {name}")

    before = accepted_bytes(bundle)
    second = must_pass(run(gate_command(project, board)),
                       "model registration tuple cache fixture")
    contains(second.out, "P-MODEL-REG CACHE-HIT: shifted_sma",
             "unchanged tuple is reused")
    eq(accepted_bytes(bundle), before, "cache hit leaves accepted bundle immutable")

    custom_out = "06_build/custom/model_registration.md"
    must_pass(run(gate_command(project, board, custom_out)),
              "custom aggregate output location")
    custom = project / custom_out
    contains(custom.read_text(),
             "accepted_bundle: 06_build/custom/model_registration_bundle/bundle.json",
             "custom output derives its aggregate bundle path")
    check((project / "06_build/custom/model_registration_bundle/bundle.json").is_file(),
          "custom aggregate bundle was published beside its report")


@test("aggregate index is deterministic and readiness-safe for multiple groups")
def t_multi_group_aggregate_index():
    project, board, _model_sha = project_fixture(kept_refs=("J2", "J3"))
    config_path = project / "03_src/rules/model_registration.yaml"
    config = yaml.safe_load(config_path.read_text())
    base = config["groups"][0]
    config["groups"] = [
        {**base, "id": "zeta_group", "refs": ["J2"]},
        {**base, "id": "alpha_group", "refs": ["J3"]},
    ]
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    must_pass(run(gate_command(project, board)), "multi-group model registration")
    stage = StageResult.from_json(
        (project / "06_build/pre_route/model_registration.stage.json").read_text())
    bundle = project / "06_build/pre_route/model_registration_bundle"
    manifest = json.loads((bundle / "bundle.json").read_text())
    index = json.loads((bundle / "model_registration_index.json").read_text())
    eq([group["id"] for group in index["groups"]],
       ["alpha_group", "zeta_group"], "deterministic group index order")
    eq((stage.graded, stage.total), (2, 2), "multi-group denominator")
    eq(manifest["run_id"], stage.run_id, "multi-group aggregate run binding")
    eq(manifest["subject"], stage.subject.to_mapping(),
       "multi-group aggregate subject binding")
    eq(index["run_id"], stage.run_id, "multi-group index run binding")
    eq(index["subject"], stage.subject.to_mapping(),
       "multi-group index subject binding")
    eq(readiness_result(project, stage)["status"], "PASS",
       "multi-group aggregate passes readiness bundle audit")


@test("one physical ref cannot inflate more than one group denominator",
      kind="known_bad")
def t_duplicate_group_ref_is_rejected():
    project, board, _model_sha = project_fixture()
    config_path = project / "03_src/rules/model_registration.yaml"
    config = yaml.safe_load(config_path.read_text())
    base = config["groups"][0]
    config["groups"] = [
        {**base, "id": "alpha_group"},
        {**base, "id": "zeta_group"},
    ]
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    failed = must_fail(run(gate_command(project, board)),
                       "duplicate registration ref denominator")
    contains(failed.out, "ref J2 appears in both alpha_group and zeta_group",
             "duplicate ref diagnosis")


@test("model-transform change invalidates cache and preserves prior PASS",
      kind="known_bad")
def t_transform_change_invalidates_without_clobbering_accepted_bundle():
    project, board, _model_sha = project_fixture()
    must_pass(run(gate_command(project, board)), "seed accepted model receipt")
    bundle = project / "06_build/pre_route/native_registration/shifted_sma"
    before = accepted_bytes(bundle)
    mutate = (
        "import pcbnew,sys\n"
        "p=sys.argv[1]; b=pcbnew.LoadBoard(p); fp=b.FindFootprintByReference('J2')\n"
        "models=fp.Models(); model=models[0]; model.m_Offset.x=5.0; "
        "models[0]=model; b.Save(p)\n"
    )
    must_pass(run([KPY, "-c", mutate, board]), "change native model transform")
    failed = must_fail(run(gate_command(project, board)),
                       "changed tuple registration", expect="P-MODEL-REG FAIL")
    check("CACHE-HIT" not in failed.out, "changed transform reused old tuple")
    eq(accepted_bytes(bundle), before, "failed tuple preserves prior PASS bundle")
    diagnostics = project / "06_build/pre_route/native_registration/failed_attempts"
    check(any(path.name == "invocation.log" for path in diagnostics.rglob("*")),
          "failed attempt diagnostics were retained")
    stage = StageResult.from_json(
        (project / "06_build/pre_route/model_registration.stage.json").read_text())
    eq(stage.status, "FAIL", "outer receipt owns failed verdict")
    eq(stage.outputs, (), "failed receipt does not name prior accepted output")
    eq((stage.graded, stage.total), (0, 1), "failed group denominator")


@test("native registration rejects a provenance-correct model shifted 5 mm",
      kind="known_bad")
def t_native_engine_and_project_gate_reject_shifted_model():
    project, board, model_sha = broken_project()
    direct = must_fail(run([
        KPY, ENGINE, board, project / "direct", "--refs", "J2",
        "--model-sha256", model_sha, "--fit-tol-mm", "1.0",
        "--courtyard-tol-mm", "0.25", "--search-margin-mm", "8.0",
        "--width", "1200", "--height", "800",
    ]), "native_model_registration.py shifted-model fixture",
        expect="P-MODEL-REG FAIL")
    contains(direct.out, "body exceeds F.CrtYd",
             "direct gate identifies physical courtyard excursion")

    aggregate = must_fail(run(gate_command(project, board)),
        "model_registration_gate.py shifted-model fixture",
        expect="P-MODEL-REG FAIL")
    contains(aggregate.out, "0/1 group(s) graded",
             "project gate reports its complete group denominator")


if __name__ == "__main__":
    sys.exit(main())
