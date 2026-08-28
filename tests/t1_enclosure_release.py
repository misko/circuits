#!/usr/bin/env python3
"""Enclosure-release transaction gates over sanitized synthetic projects."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

import yaml

import harness as _harness

# Reuse the strict schema-v2 fixture without registering its test cases here.
_original_test = _harness.test
_harness.test = lambda *args, **kwargs: lambda function: function
try:
    import t1_pcb_enclosure_v2 as _v2base
finally:
    _harness.test = _original_test

from harness import (check, contains, eq, main, must_fail, must_pass, run,
                     test, tmpdir)


ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "pcb-enclosure" / "scripts"
STAGE = SCRIPTS / "stage_enclosure_release.py"
VERIFY = SCRIPTS / "verify_enclosure_release.py"
KPY = "/usr/bin/python3"


def _load_stage_module():
    spec = importlib.util.spec_from_file_location(
        "_enclosure_release_stage_for_test", STAGE)
    check(spec is not None and spec.loader is not None,
          "could not load release-stage module")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(SCRIPTS))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def _load_verify_module():
    spec = importlib.util.spec_from_file_location(
        "_enclosure_release_verify_for_test", VERIFY)
    check(spec is not None and spec.loader is not None,
          "could not load release-verifier module")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(SCRIPTS))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def _parsed_stage_args(module, fixture: dict[str, Path], **kwargs):
    return module._parse_args([str(item) for item in _args(fixture, **kwargs)[2:]])


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture() -> dict[str, Path]:
    source_fixture = _v2base._fresh_fixture()
    root = tmpdir("enclosure_release_")
    project = root / "project"
    pcb_release = project / "07_releases" / "v1.2.3-2026-08-20"
    enclosure_stream = project / "07_enclosure_releases"
    workspace = root / "prepared"
    (pcb_release / "source").mkdir(parents=True)
    (pcb_release / "3d").mkdir()
    (workspace / "source").mkdir(parents=True)
    (workspace / "tooling").mkdir()
    (workspace / "meshes").mkdir()
    (workspace / "verification").mkdir()
    enclosure_stream.mkdir(parents=True)
    (enclosure_stream / "contracts.md").write_text(
        "# Synthetic enclosure release contract\n\nImmutable candidates only.\n")
    pcb = pcb_release / "source" / "array.kicad_pcb"
    step = pcb_release / "3d" / "array.step"
    source_root = source_fixture["root"]
    source_pcb = source_root / "subject" / "board.kicad_pcb"
    source_step = source_root / "subject" / "board.step"
    pcb.write_bytes(source_pcb.read_bytes())
    step.write_bytes(source_step.read_bytes())
    parent_manifest = pcb_release / "MANIFEST.txt"
    parent_manifest.write_text(
        "MANIFEST — synthetic PCB release\nsha256:\n"
        f"  source/array.kicad_pcb  {_sha(pcb)}\n"
        f"  3d/array.step  {_sha(step)}\n")
    (workspace / "README.md").write_text(
        "# Synthetic enclosure release\n\nNot an order authorization.\n")
    interface = workspace / "source" / "board-interface.json"
    antenna = workspace / "source" / "antenna-measurements.yaml"
    intent = workspace / "source" / "mechanical-intent.yaml"
    cad_design_path = workspace / "source" / "enclosure-v1.yaml"
    config_path = workspace / "source" / "enclosure-v2.yaml"
    interface.write_bytes((source_root / "subject" /
                           "board-interface.json").read_bytes())
    antenna.write_bytes(source_fixture["antenna"].read_bytes())
    intent.write_bytes(source_fixture["intent"].read_bytes())

    def binding(relative: str, path: Path) -> dict[str, object]:
        return {"path": relative, "sha256": _sha(path),
                "size": path.stat().st_size}

    release_subject = {
        "release": "v1.2.3-2026-08-20",
        "release_manifest": binding(
            "authorities/pcb-release/MANIFEST.txt", parent_manifest),
        "pcb": binding(
            "authorities/pcb-release/source/array.kicad_pcb", pcb),
        "step": binding("authorities/pcb-release/3d/array.step", step),
        "interface": binding("source/board-interface.json", interface),
    }
    cad_design = yaml.safe_load(source_fixture["cad_design"].read_text())
    cad_design["subject"] = release_subject
    cad_design_path.write_text(
        yaml.safe_dump(cad_design, sort_keys=False), encoding="utf-8")

    replay_config = yaml.safe_load(source_fixture["config"].read_text())
    replay_config["subject"] = {
        **release_subject,
        "mechanical_intent": binding("source/mechanical-intent.yaml", intent),
        "cad_design": binding("source/enclosure-v1.yaml", cad_design_path),
    }
    replay_config["external_subjects"][0]["source"] = binding(
        "source/antenna-measurements.yaml", antenna)
    config_path.write_text(
        yaml.safe_dump(replay_config, sort_keys=False), encoding="utf-8")
    (workspace / "tooling" / "replay.py").write_text(
        "#!/usr/bin/env python3\nprint('synthetic replay')\n")
    (workspace / "meshes" / "base.stl").write_text(
        "solid base\nendsolid base\n")
    (workspace / "verification" / "verification.json").write_text(
        json.dumps({"kind": "synthetic-verification", "status": "INCOMPLETE"})
        + "\n")
    return {
        "root": root, "project": project, "pcb_release": pcb_release,
        "workspace": workspace, "pcb": pcb, "step": step,
        "parent_manifest": parent_manifest,
        "source_fixture": source_fixture,
    }


def _add_shared_connector_replay_closure(fixture: dict[str, Path]) -> None:
    """Mirror one exact shared receipt and every receipt-owned replay input."""
    source_fixture = fixture["source_fixture"]
    _v2base._add_shared_connector_contract(source_fixture)
    source_root = source_fixture["root"]
    workspace = fixture["workspace"]
    source_config = yaml.safe_load(source_fixture["config"].read_text())
    receipt_source = source_fixture["connector_receipt"]
    receipt = json.loads(receipt_source.read_text())

    receipt_target = (workspace / "verification" /
                      "connector_assembly_contract.json")
    receipt_target.write_bytes(receipt_source.read_bytes())
    mirror_root = workspace / "source" / "connector-assembly"
    copied_inputs: list[Path] = []
    nested = [receipt["inputs"]["contract"], *receipt["inputs"]["evidence_files"]]
    for record in nested:
        source = source_root / record["path"]
        target = mirror_root / record["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        eq(_sha(target), record["sha256"], "mirrored connector input hash")
        eq(target.stat().st_size, record["size"],
           "mirrored connector input size")
        copied_inputs.append(target)

    compiler_target = workspace / "tooling" / "connector_assembly_contract.py"
    compiler_target.write_bytes(_v2base.CONNECTOR_COMPILER.read_bytes())
    eq(_sha(compiler_target), receipt["inputs"]["compiler"]["sha256"],
       "mirrored connector compiler hash")

    config_path = workspace / "source" / "enclosure-v2.yaml"
    config = yaml.safe_load(config_path.read_text())
    config.pop("service_envelopes", None)
    config["interface_assemblies"] = copy.deepcopy(
        source_config["interface_assemblies"])
    config["interface_assemblies"]["receipt"] = {
        "path": "verification/connector_assembly_contract.json",
        "sha256": _sha(receipt_target),
        "size": receipt_target.stat().st_size,
    }
    config_path.write_text(yaml.safe_dump(config, sort_keys=False),
                           encoding="utf-8")
    fixture["connector_receipt"] = receipt_target
    fixture["connector_contract"] = copied_inputs[0]
    fixture["connector_evidence"] = copied_inputs[1]
    fixture["connector_compiler"] = compiler_target
    fixture["connector_mirror_root"] = mirror_root


def _rewrite_prepared_connector_receipt(
        fixture: dict[str, Path], receipt: dict) -> None:
    path = fixture["connector_receipt"]
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    config_path = fixture["workspace"] / "source" / "enclosure-v2.yaml"
    config = yaml.safe_load(config_path.read_text())
    config["interface_assemblies"]["receipt"] = {
        "path": "verification/connector_assembly_contract.json",
        "sha256": _sha(path), "size": path.stat().st_size,
    }
    config_path.write_text(yaml.safe_dump(config, sort_keys=False),
                           encoding="utf-8")


def _reseal_manifest_payload(manifest: dict, release: Path,
                             relative: str) -> None:
    path = release / relative
    replacement = {"sha256": _sha(path), "size": path.stat().st_size}
    for row in manifest["payloads"]:
        if row["path"] == relative:
            row.update(replacement)
            break
    else:
        manifest["payloads"].append({"path": relative, **replacement})
        manifest["payloads"].sort(key=lambda row: row["path"])
        manifest["payload_count"] = len(manifest["payloads"])
    if manifest["replay"]["config"]["path"] == relative:
        manifest["replay"]["config"].update(replacement)
    for row in manifest["replay"]["tools"]:
        if row["path"] == relative:
            row.update(replacement)


def _args(fixture: dict[str, Path], *, version: str = "v0.1.0",
          status: str = "INCOMPLETE", scopes: tuple[str, ...] = (
              "shell=INCOMPLETE", "board_retention=INCOMPLETE",
              "antenna_accessory=INCOMPLETE", "thermal=INCOMPLETE"),
          candidate: bool = True, order_ready: bool = False,
          predecessor: str | None = None) -> list[object]:
    result: list[object] = [
        KPY, STAGE, fixture["workspace"], "--project-root", fixture["project"],
        "--artifact-id", "synthetic-array-enclosure", "--version", version,
        "--date", "2026-08-25", "--pcb-release", "v1.2.3-2026-08-20",
        "--pcb-manifest", "MANIFEST.txt", "--pcb", "source/array.kicad_pcb",
        "--step", "3d/array.step", "--status", status,
        "--status-reason", "Exact synthetic status with open physical work.",
        "--replay-config", "source/enclosure-v2.yaml", "--replay-tool",
        "regrade=tooling/replay.py",
    ]
    connector_compiler = (fixture["workspace"] / "tooling" /
                          "connector_assembly_contract.py")
    if connector_compiler.is_file():
        result.extend((
            "--replay-tool",
            "connector_assembly_contract="
            "tooling/connector_assembly_contract.py",
        ))
    for scope in scopes:
        result.extend(("--scope", scope))
    if candidate:
        result.append("--immutable-candidate")
    if order_ready:
        result.append("--order-ready")
    if predecessor:
        result.extend(("--predecessor", predecessor))
    return result


def _release(fixture: dict[str, Path], version: str = "v0.1.0") -> Path:
    return (fixture["project"] / "07_enclosure_releases" /
            f"{version}-2026-08-25")


def _parent_snapshot(fixture: dict[str, Path]) -> dict[str, str]:
    return {
        path.relative_to(fixture["pcb_release"]).as_posix(): _sha(path)
        for path in fixture["pcb_release"].rglob("*") if path.is_file()
    }


def _release_tree_census(root: Path) -> dict[str, object]:
    """Capture every directory plus the identity of every release file."""
    return {
        "directories": sorted(
            path.relative_to(root).as_posix()
            for path in root.rglob("*") if path.is_dir()),
        "files": {
            path.relative_to(root).as_posix(): {
                "sha256": _sha(path), "size": path.stat().st_size,
            }
            for path in sorted(root.rglob("*")) if path.is_file()
        },
    }


def _add_release_local_verifier(fixture: dict[str, Path]) -> None:
    """Install the verifier's exact import closure in synthetic tooling/."""
    workspace_tooling = fixture["workspace"] / "tooling"
    sources = {
        "verify_enclosure_release.py": VERIFY,
        "enclosure_v2.py": SCRIPTS / "enclosure_v2.py",
        "enclosure_common.py": SCRIPTS / "enclosure_common.py",
        "process_runner.py": (
            ROOT / "skills" / "kicad-pcb" / "scripts" / "process_runner.py"),
        "pipeline_runtime.py": (
            ROOT / "skills" / "pcb-design" / "scripts" /
            "pipeline_runtime.py"),
    }
    for name, source in sources.items():
        (workspace_tooling / name).write_bytes(source.read_bytes())


@test("release publisher parses standard sha256sum parent manifests")
def t_sha256sum_parent_manifest_clean():
    module = _load_stage_module()
    root = tmpdir("enclosure_sha256sum_manifest_")
    manifest = root / "MANIFEST.txt"
    pcb_hash = "1" * 64
    step_hash = "2" * 64
    manifest.write_text(
        f"{pcb_hash}  source/array.kicad_pcb\n"
        f"{step_hash} *3d/array.step\n", encoding="utf-8")
    eq(module.release_verify._declared_subject_hashes(manifest), {
        "source/array.kicad_pcb": pcb_hash,
        "3d/array.step": step_hash,
    }, "sha256sum parent-manifest path/hash census")


@test("release publisher atomically publishes a self-contained INCOMPLETE candidate")
def t_publish_incomplete_candidate_clean():
    fixture = _fixture()
    before = _parent_snapshot(fixture)
    result = must_pass(run(_args(fixture)), "stage enclosure candidate")
    contains(result.out, "ENCLOSURE RELEASE PUBLISHED", "publisher output")
    release = _release(fixture)
    check(release.is_dir(), "release destination was not published")
    manifest = json.loads((release / "MANIFEST.json").read_text())
    eq(manifest["status"], "INCOMPLETE", "overall status")
    eq(manifest["scopes"], {
        "antenna_accessory": "INCOMPLETE",
        "board_retention": "INCOMPLETE",
        "shell": "INCOMPLETE",
        "thermal": "INCOMPLETE",
    }, "scoped statuses")
    eq(manifest["publication"], {
        "immutable_candidate": True, "order_ready": False, "release": True,
    }, "candidate publication state")
    eq(manifest["payload_count"], len(manifest["payloads"]), "payload census")
    eq(_parent_snapshot(fixture), before, "PCB release stream bytes")
    check(not list((fixture["project"] / "07_enclosure_releases").glob(
        ".*.staging-*")), "publisher left a staging directory")
    must_pass(run([KPY, VERIFY, release]), "release-local reopen")
    must_pass(run([KPY, VERIFY, release, "--project-root", fixture["project"]]),
              "release reopen against external parent")


@test("publisher seals and verifier regrades a release-local connector closure")
def t_shared_connector_release_replay_clean():
    fixture = _fixture()
    _add_shared_connector_replay_closure(fixture)
    must_pass(run(_args(fixture)), "publish shared connector release")
    release = _release(fixture)
    result = must_pass(run([KPY, VERIFY, release]),
                       "release-local connector replay")
    contains(result.out, "status=INCOMPLETE", "connector release status")
    # Remove every mutable project-side connector source. Reopening must still
    # use the exact contract/evidence/compiler bytes inside the release.
    shutil.rmtree(fixture["source_fixture"]["root"])
    must_pass(run([KPY, VERIFY, release]), "offline connector replay")
    module = _load_verify_module()
    original_loader = module.composition._connector_compiler_module
    executed_from: list[str] = []

    def capture_release_compiler(expected, **kwargs):
        compiler, binding = original_loader(expected, **kwargs)
        executed_from.append(compiler.__file__)
        return compiler, binding

    module.composition._connector_compiler_module = capture_release_compiler
    try:
        reopened = module.verify_release(release)
    finally:
        module.composition._connector_compiler_module = original_loader
    eq(executed_from, [str(release / "tooling" /
                           "connector_assembly_contract.py")],
       "executed connector compiler source")
    eq(reopened["replay"]["connector_assembly"], {
        "receipt": "verification/connector_assembly_contract.json",
        "compiler_role": "connector_assembly_contract",
        "compiler": "tooling/connector_assembly_contract.py",
        "virtual_project_root": "source/connector-assembly",
        "contract": "03_src/rules/connector_assemblies.yaml",
        "evidence_files": ["02_parts/synthetic-connector/part.yaml"],
    }, "release-local connector replay closure")


@test("release-local connector verification is read-only across repeated reopens")
def t_release_local_connector_replay_preserves_exact_census_clean():
    fixture = _fixture()
    _add_shared_connector_replay_closure(fixture)
    _add_release_local_verifier(fixture)
    must_pass(run(_args(fixture)), "publish self-verifying connector release")
    release = _release(fixture)
    local_verifier = release / "tooling" / "verify_enclosure_release.py"
    before = _release_tree_census(release)

    # Simulate an embedding caller that explicitly re-enables bytecode after
    # interpreter startup.  The release verifier itself must remain read-only;
    # relying only on the caller's environment or ``python -B`` is insufficient.
    invoke = (
        "import runpy,sys\n"
        "sys.dont_write_bytecode=False\n"
        "script=sys.argv[1]\n"
        "sys.argv=sys.argv[1:]\n"
        "runpy.run_path(script, run_name='__main__')\n"
    )
    for attempt in ("first", "second"):
        must_pass(run([KPY, "-c", invoke, local_verifier, release]),
                  f"{attempt} release-local connector verify")
        eq(_release_tree_census(release), before,
           f"release tree after {attempt} release-local verify")


@test("release verifier independently requires the exact connector tool role",
      kind="known_bad", gate="verify_enclosure_release.py")
def t_shared_connector_release_wrong_role_bites():
    fixture = _fixture()
    _add_shared_connector_replay_closure(fixture)
    must_pass(run(_args(fixture)), "publish connector fixture")
    release = _release(fixture)
    manifest_path = release / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    connector_tool = next(
        row for row in manifest["replay"]["tools"]
        if row["role"] == "connector_assembly_contract")
    connector_tool["role"] = "connector_compiler"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    must_fail(run([KPY, VERIFY, release]), "reopen wrong connector tool role",
              "requires manifest tool role 'connector_assembly_contract'")


@test("connector release requires its exact compiler role and canonical tool path",
      kind="known_bad", gate="stage_enclosure_release.py")
def t_shared_connector_release_compiler_selection_bites():
    for mutation, expected in (
            ("missing", "requires manifest tool role"),
            ("wrong_path", "must bind exact path"),
            ("substituted", "differs from the exact compiler identity")):
        fixture = _fixture()
        _add_shared_connector_replay_closure(fixture)
        arguments = _args(fixture)
        compiler = fixture["connector_compiler"]
        if mutation == "missing":
            compiler.unlink()
            arguments = _args(fixture)
        elif mutation == "wrong_path":
            renamed = fixture["workspace"] / "tooling" / "renamed.py"
            renamed.write_bytes(compiler.read_bytes())
            compiler.unlink()
            arguments = _args(fixture)
            arguments.extend((
                "--replay-tool",
                "connector_assembly_contract=tooling/renamed.py",
            ))
        else:
            compiler.write_bytes(compiler.read_bytes() + b"\n# substituted\n")
        must_fail(run(arguments), f"connector compiler {mutation}", expected)
        check(not _release(fixture).exists(),
              f"{mutation} connector compiler was published")


@test("connector release binds contract and every evidence byte",
      kind="known_bad", gate="stage_enclosure_release.py")
def t_shared_connector_release_input_drift_bites():
    for field, expected in (
            ("connector_contract", "connector contract does not match"),
            ("connector_evidence", "connector evidence file 0 does not match")):
        fixture = _fixture()
        _add_shared_connector_replay_closure(fixture)
        path = fixture[field]
        path.write_bytes(path.read_bytes() + b"\n# drift\n")
        must_fail(run(_args(fixture)), f"drifted {field}", expected)
        check(not _release(fixture).exists(),
              f"drifted {field} release was published")


@test("connector release closure has an exact receipt-derived file census",
      kind="known_bad", gate="stage_enclosure_release.py")
def t_shared_connector_release_extra_closure_file_bites():
    fixture = _fixture()
    _add_shared_connector_replay_closure(fixture)
    extra = fixture["connector_mirror_root"] / "unclaimed-evidence.yaml"
    extra.write_text("claim: absent from receipt\n", encoding="utf-8")
    must_fail(run(_args(fixture)), "extra connector closure input",
              "connector replay closure census differs")
    check(not _release(fixture).exists(),
          "connector release with extra closure file was published")


@test("connector receipt source path identities cannot be virtualized twice",
      kind="known_bad", gate="stage_enclosure_release.py")
def t_shared_connector_release_recorded_paths_bite():
    cases = (
        ("compiler", "skills/pcb-design/scripts/renamed.py",
         "compiler path differs from the canonical source identity"),
        ("contract", "03_src/rules/alternate.yaml",
         "receipt-selected authority"),
        ("evidence", "02_parts/synthetic-connector/alternate.yaml",
         "receipt source reopen failed"),
    )
    for field, replacement, expected in cases:
        fixture = _fixture()
        _add_shared_connector_replay_closure(fixture)
        receipt = json.loads(fixture["connector_receipt"].read_text())
        if field == "compiler":
            receipt["inputs"]["compiler"]["path"] = replacement
        elif field == "contract":
            old = fixture["connector_contract"]
            new = fixture["connector_mirror_root"] / replacement
            new.parent.mkdir(parents=True, exist_ok=True)
            new.write_bytes(old.read_bytes())
            old.unlink()
            receipt["inputs"]["contract"]["path"] = replacement
        else:
            old = fixture["connector_evidence"]
            new = fixture["connector_mirror_root"] / replacement
            new.parent.mkdir(parents=True, exist_ok=True)
            new.write_bytes(old.read_bytes())
            old.unlink()
            receipt["inputs"]["evidence_files"][0]["path"] = replacement
        _rewrite_prepared_connector_receipt(fixture, receipt)
        must_fail(run(_args(fixture)), f"forged connector {field} path",
                  expected)
        check(not _release(fixture).exists(),
              f"forged connector {field} path was published")


@test("connector receipt nested hash and size bindings are load-bearing",
      kind="known_bad", gate="stage_enclosure_release.py")
def t_shared_connector_release_nested_identity_bites():
    for field, replacement in (("sha256", "0" * 64), ("size", 1)):
        fixture = _fixture()
        _add_shared_connector_replay_closure(fixture)
        receipt = json.loads(fixture["connector_receipt"].read_text())
        receipt["inputs"]["evidence_files"][0][field] = replacement
        _rewrite_prepared_connector_receipt(fixture, receipt)
        must_fail(run(_args(fixture)), f"forged evidence {field}",
                  "connector evidence file 0 does not match")
        check(not _release(fixture).exists(),
              f"forged evidence {field} was published")


@test("connector receipt inputs cannot alias one release-local source",
      kind="known_bad", gate="stage_enclosure_release.py")
def t_shared_connector_release_nested_alias_bites():
    fixture = _fixture()
    _add_shared_connector_replay_closure(fixture)
    receipt = json.loads(fixture["connector_receipt"].read_text())
    contract = receipt["inputs"]["contract"]
    evidence = receipt["inputs"]["evidence_files"][0]
    evidence.update({key: contract[key] for key in ("path", "sha256", "size")})
    _rewrite_prepared_connector_receipt(fixture, receipt)
    must_fail(run(_args(fixture)), "aliased connector input",
              "connector replay inputs alias one source path")
    check(not _release(fixture).exists(),
          "aliased connector closure was published")


@test("connector release recompiles rather than trusting a resealed receipt",
      kind="known_bad", gate="stage_enclosure_release.py")
def t_shared_connector_release_forged_receipt_bites():
    fixture = _fixture()
    _add_shared_connector_replay_closure(fixture)
    receipt = json.loads(fixture["connector_receipt"].read_text())
    receipt["semantic_sha256"] = "f" * 64
    _rewrite_prepared_connector_receipt(fixture, receipt)
    must_fail(run(_args(fixture)), "forged connector receipt",
              "shared connector regrade failed")
    check(not _release(fixture).exists(),
          "forged connector receipt was published")


@test("connector replay config cannot point back into a live build tree",
      kind="known_bad", gate="stage_enclosure_release.py")
def t_shared_connector_release_live_path_bites():
    fixture = _fixture()
    _add_shared_connector_replay_closure(fixture)
    config_path = fixture["workspace"] / "source" / "enclosure-v2.yaml"
    config = yaml.safe_load(config_path.read_text())
    config["interface_assemblies"]["receipt"]["path"] = (
        "06_build/verification/connector_assembly_contract.json")
    config_path.write_text(yaml.safe_dump(config, sort_keys=False),
                           encoding="utf-8")
    must_fail(run(_args(fixture)), "live connector receipt path",
              "shared connector receipt must be release-local below verification/")
    check(not _release(fixture).exists(),
          "live-path connector release was published")


@test("release verifier reopens nested connector bytes after manifest reseal",
      kind="known_bad", gate="verify_enclosure_release.py")
def t_shared_connector_release_reopen_nested_drift_bites():
    fixture = _fixture()
    _add_shared_connector_replay_closure(fixture)
    must_pass(run(_args(fixture)), "publish connector fixture before drift")
    release = _release(fixture)
    relative = ("source/connector-assembly/03_src/rules/"
                "connector_assemblies.yaml")
    path = release / relative
    path.write_bytes(path.read_bytes() + b"\n# post-release drift\n")
    manifest_path = release / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    _reseal_manifest_payload(manifest, release, relative)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    must_fail(run([KPY, VERIFY, release]), "resealed connector contract drift",
              "connector contract does not match")


@test("release verifier rejects manifested extras inside connector closure",
      kind="known_bad", gate="verify_enclosure_release.py")
def t_shared_connector_release_reopen_extra_bites():
    fixture = _fixture()
    _add_shared_connector_replay_closure(fixture)
    must_pass(run(_args(fixture)), "publish connector fixture before extra")
    release = _release(fixture)
    relative = "source/connector-assembly/extra.yaml"
    extra = release / relative
    extra.write_text("claim: not in receipt\n", encoding="utf-8")
    manifest_path = release / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    _reseal_manifest_payload(manifest, release, relative)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    must_fail(run([KPY, VERIFY, release]), "manifested connector extra",
              "connector replay closure census differs")


@test("release verifier controls a non-mapping replay before membership",
      kind="known_bad", gate="verify_enclosure_release.py")
def t_non_mapping_replay_membership_bites():
    fixture = _fixture()
    must_pass(run(_args(fixture)), "publish clean non-mapping fixture")
    module = _load_verify_module()
    original = module.composition.load_yaml
    module.composition.load_yaml = lambda _path: []
    try:
        try:
            module.verify_release(_release(fixture))
        except module.ReleaseError as exc:
            contains(str(exc),
                     "must contain a YAML/JSON object before shared connector "
                     "membership is inspected",
                     "controlled non-mapping replay error")
        except TypeError as exc:
            raise AssertionError(
                "non-mapping replay escaped as an uncontrolled TypeError"
            ) from exc
        else:
            raise AssertionError("non-mapping replay unexpectedly verified")
    finally:
        module.composition.load_yaml = original


@test("release publisher binds an exact optional predecessor and remains locally replayable")
def t_exact_predecessor_clean():
    fixture = _fixture()
    must_pass(run(_args(
        fixture, version="v0.1.0")), "publish predecessor")
    predecessor = _release(fixture)
    predecessor_hash = _sha(predecessor / "MANIFEST.json")
    must_pass(run(_args(
        fixture, version="v0.2.0",
        predecessor=predecessor.name)), "publish successor")
    successor = _release(fixture, "v0.2.0")
    manifest = json.loads((successor / "MANIFEST.json").read_text())
    eq(manifest["predecessor"]["manifest"]["sha256"], predecessor_hash,
       "predecessor manifest identity")
    eq(_sha(successor / "authorities" / "enclosure-predecessor" /
            "MANIFEST.json"), predecessor_hash, "release-local predecessor copy")
    must_pass(run([KPY, VERIFY, successor]), "successor local reopen")
    # Local reopening deliberately does not depend on mutable outside paths.
    (predecessor / "MANIFEST.json").write_text("{}\n")
    must_pass(run([KPY, VERIFY, successor]), "offline successor reopen")
    must_fail(run([KPY, VERIFY, successor, "--project-root", fixture["project"]]),
              "external predecessor drift", "external predecessor manifest")


@test("INCOMPLETE publication requires explicit immutable-candidate state",
      kind="known_bad", gate="stage_enclosure_release.py")
def t_incomplete_without_candidate_bites():
    fixture = _fixture()
    must_fail(run(_args(fixture, candidate=False)), "unmarked incomplete release",
              "INCOMPLETE may publish only")
    check(not _release(fixture).exists(), "invalid candidate was published")


@test("INCOMPLETE publication can never become order-ready",
      kind="known_bad", gate="stage_enclosure_release.py")
def t_incomplete_order_ready_bites():
    fixture = _fixture()
    must_fail(run(_args(fixture, order_ready=True)), "order-ready incomplete release",
              "INCOMPLETE may publish only")
    check(not _release(fixture).exists(), "order-ready incomplete release was published")


@test("overall release status is the conservative aggregate of all scopes",
      kind="known_bad", gate="stage_enclosure_release.py")
def t_scope_aggregate_bites():
    fixture = _fixture()
    must_fail(run(_args(
        fixture, status="CAD_READY",
        scopes=("shell=CAD_READY", "antenna_accessory=INCOMPLETE"),
        candidate=False)), "inflated aggregate status", "scope aggregate INCOMPLETE")
    check(not _release(fixture).exists(), "inflated status release was published")


@test("manual CAD_READY publication is disabled without governing regrade evidence",
      kind="known_bad", gate="stage_enclosure_release.py")
def t_manual_ready_publication_bites():
    fixture = _fixture()
    must_fail(run(_args(
        fixture, status="CAD_READY", scopes=("shell=CAD_READY",),
        candidate=False)), "manual CAD_READY release",
        "publication is disabled until the release publisher can reopen")
    check(not _release(fixture).exists(), "manual CAD_READY release was published")


@test("candidate publication cannot carry an ungraded component-ready scope",
      kind="known_bad", gate="stage_enclosure_release.py")
def t_component_ready_candidate_bites():
    fixture = _fixture()
    must_fail(run(_args(
        fixture, scopes=(
            "shell=CAD_READY", "board_retention=INCOMPLETE",
            "antenna_accessory=INCOMPLETE", "thermal=INCOMPLETE",
        ))), "ungraded component-ready candidate",
        "requires every declared scope to be INCOMPLETE")
    check(not _release(fixture).exists(), "component-ready candidate was published")


@test("release scope census comes from the exact schema-v2 config",
      kind="known_bad", gate="stage_enclosure_release.py")
def t_required_scope_census_bites():
    fixture = _fixture()
    must_fail(run(_args(fixture, scopes=("shell=INCOMPLETE",))),
              "partial release scope census", "required scope census")
    check(not _release(fixture).exists(), "partial-scope candidate was published")


@test("publication refuses an existing destination without changing its bytes",
      kind="known_bad", gate="stage_enclosure_release.py")
def t_no_clobber_bites():
    fixture = _fixture()
    must_pass(run(_args(fixture)), "initial candidate publication")
    release = _release(fixture)
    before = _sha(release / "MANIFEST.json")
    (fixture["workspace"] / "README.md").write_text("changed candidate\n")
    must_fail(run(_args(fixture)), "duplicate publication", "already exists")
    eq(_sha(release / "MANIFEST.json"), before, "published manifest bytes")


@test("publication requires an explicit enclosure-stream contract",
      kind="known_bad", gate="stage_enclosure_release.py")
def t_missing_stream_contract_bites():
    fixture = _fixture()
    (fixture["project"] / "07_enclosure_releases" / "contracts.md").unlink()
    must_fail(run(_args(fixture)), "contractless enclosure stream",
              "enclosure release stream contract")
    check(not _release(fixture).exists(), "contractless release was published")


@test("prepared workspace identity is rechecked before publication",
      kind="known_bad", gate="stage_enclosure_release.py")
def t_workspace_changes_during_stage_bite():
    fixture = _fixture()
    module = _load_stage_module()
    real_copy = module._copy_regular
    changed = False

    def mutate_after_copy(source, destination, where):
        nonlocal changed
        result = real_copy(source, destination, where)
        if source == fixture["workspace"] / "README.md" and not changed:
            changed = True
            source.write_text(source.read_text() + "changed during stage\n")
        return result

    module._copy_regular = mutate_after_copy
    try:
        try:
            module.stage_release(_parsed_stage_args(module, fixture))
        except module.release_verify.ReleaseError as exc:
            contains(str(exc), "prepared workspace changed")
        else:
            check(False, "changed prepared workspace was published")
    finally:
        module._copy_regular = real_copy
    check(not _release(fixture).exists(), "workspace-race release was published")


@test("final canonical destination check runs inside the stream lock",
      kind="known_bad", gate="stage_enclosure_release.py")
def t_late_casefold_destination_bites():
    fixture = _fixture()
    module = _load_stage_module()
    real_verify = module.release_verify.verify_release
    alias = fixture["project"] / "07_enclosure_releases" / \
        "V0.1.0-2026-08-25"
    injected = False

    def add_alias_before_publication(*args, **kwargs):
        nonlocal injected
        result = real_verify(*args, **kwargs)
        if not injected:
            alias.mkdir()
            injected = True
        return result

    module.release_verify.verify_release = add_alias_before_publication
    try:
        try:
            module.stage_release(_parsed_stage_args(module, fixture))
        except module.release_verify.ReleaseError as exc:
            contains(str(exc), "case/Unicode path collision")
        else:
            check(False, "late case-fold alias was ignored")
    finally:
        module.release_verify.verify_release = real_verify
        alias.rmdir()
    check(not _release(fixture).exists(), "casefold-race release was published")


@test("parent authority paths are reopened without following late links",
      kind="known_bad", gate="stage_enclosure_release.py")
def t_late_parent_link_bites():
    fixture = _fixture()
    module = _load_stage_module()
    real_verify = module.release_verify.verify_release
    outside = fixture["root"] / "outside-parent-copy.kicad_pcb"
    outside.write_bytes(fixture["pcb"].read_bytes())
    injected = False

    def replace_parent_before_reopen(*args, **kwargs):
        nonlocal injected
        if not injected:
            fixture["pcb"].unlink()
            fixture["pcb"].symlink_to(outside)
            injected = True
        return real_verify(*args, **kwargs)

    module.release_verify.verify_release = replace_parent_before_reopen
    try:
        try:
            module.stage_release(_parsed_stage_args(module, fixture))
        except module.release_verify.ReleaseError as exc:
            contains(str(exc), "symlink paths are not accepted")
        else:
            check(False, "late linked parent authority was accepted")
    finally:
        module.release_verify.verify_release = real_verify
    check(not _release(fixture).exists(), "linked-parent release was published")


@test("prepared workspaces cannot smuggle symlinked payloads",
      kind="known_bad", gate="stage_enclosure_release.py")
def t_workspace_symlink_bites():
    fixture = _fixture()
    os.symlink(fixture["workspace"] / "README.md",
               fixture["workspace"] / "source" / "linked.yaml")
    must_fail(run(_args(fixture)), "symlinked workspace", "linked/special file")
    check(not _release(fixture).exists(), "symlinked release was published")


@test("prepared workspaces cannot smuggle hard-linked payloads",
      kind="known_bad", gate="stage_enclosure_release.py")
def t_workspace_hardlink_bites():
    fixture = _fixture()
    os.link(fixture["workspace"] / "README.md",
            fixture["workspace"] / "source" / "alias.md")
    must_fail(run(_args(fixture)), "hard-linked workspace", "hard-linked file")
    check(not _release(fixture).exists(), "hard-linked release was published")


@test("case-folded release path aliases are rejected before publication",
      kind="known_bad", gate="stage_enclosure_release.py")
def t_workspace_path_collision_bites():
    fixture = _fixture()
    (fixture["workspace"] / "source" / "Case.yaml").write_text("case: upper\n")
    (fixture["workspace"] / "source" / "case.yaml").write_text("case: lower\n")
    must_fail(run(_args(fixture)), "case-fold path collision", "path collision")
    check(not _release(fixture).exists(), "colliding release was published")


@test("parent PCB manifest must bind the selected PCB and STEP bytes",
      kind="known_bad", gate="stage_enclosure_release.py")
def t_parent_manifest_binding_bites():
    fixture = _fixture()
    text = fixture["parent_manifest"].read_text()
    fixture["parent_manifest"].write_text(
        text.replace(_sha(fixture["pcb"]), "0" * 64))
    must_fail(run(_args(fixture)), "stale parent binding",
              "does not bind selected PCB")
    check(not _release(fixture).exists(), "stale-parent release was published")


@test("replay config cannot retain live project subject paths",
      kind="known_bad", gate="stage_enclosure_release.py")
def t_live_replay_binding_bites():
    fixture = _fixture()
    config_path = fixture["workspace"] / "source" / "enclosure-v2.yaml"
    config = yaml.safe_load(config_path.read_text())
    config["subject"]["pcb"]["path"] = (
        "07_releases/v1.2.3-2026-08-20/source/array.kicad_pcb")
    config_path.write_text(yaml.safe_dump(config, sort_keys=False))
    must_fail(run(_args(fixture)), "live-path replay config",
              "cannot inspect")
    check(not _release(fixture).exists(), "live-path replay release was published")


@test("release verifier rejects every unmanifested regular file",
      kind="known_bad", gate="verify_enclosure_release.py")
def t_release_extra_file_bites():
    fixture = _fixture()
    must_pass(run(_args(fixture)), "candidate publication before extra")
    release = _release(fixture)
    (release / "renders").mkdir()
    (release / "renders" / "unmanifested.png").write_bytes(b"not evidence")
    must_fail(run([KPY, VERIFY, release]), "release extra file", "extras=")


@test("release verifier rejects hard links introduced after publication",
      kind="known_bad", gate="verify_enclosure_release.py")
def t_release_hardlink_bites():
    fixture = _fixture()
    must_pass(run(_args(fixture)), "candidate publication before hard link")
    release = _release(fixture)
    os.link(release / "README.md", release / "source" / "post-publish-alias.md")
    must_fail(run([KPY, VERIFY, release]), "release hard link", "hard-linked file")


@test("release verifier recomputes the conservative scoped status",
      kind="known_bad", gate="verify_enclosure_release.py")
def t_release_scope_reopen_bites():
    fixture = _fixture()
    must_pass(run(_args(fixture)), "candidate publication before status tamper")
    release = _release(fixture)
    manifest_path = release / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["status"] = "CAD_READY"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    must_fail(run([KPY, VERIFY, release]), "inflated released status",
              "conservative scope aggregate INCOMPLETE")


@test("release verifier mirrors the INCOMPLETE-only rollout boundary",
      kind="known_bad", gate="verify_enclosure_release.py")
def t_release_ready_policy_reopen_bites():
    fixture = _fixture()
    must_pass(run(_args(fixture)), "candidate publication before ready tamper")
    release = _release(fixture)
    manifest_path = release / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["status"] = "THERMALLY_VERIFIED"
    manifest["scopes"] = {
        name: "THERMALLY_VERIFIED" for name in manifest["scopes"]
    }
    manifest["lifecycle"] = "immutable_release"
    manifest["publication"] = {
        "release": True, "immutable_candidate": False, "order_ready": True,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    must_fail(run([KPY, VERIFY, release]), "ready-policy manifest tamper",
              "accepts only INCOMPLETE overall and per-scope")


@test("release verifier requires at least one manifest-bound printable mesh",
      kind="known_bad", gate="verify_enclosure_release.py")
def t_release_mesh_denominator_bites():
    fixture = _fixture()
    must_pass(run(_args(fixture)), "candidate publication before mesh removal")
    release = _release(fixture)
    mesh = release / "meshes" / "base.stl"
    mesh.unlink()
    mesh.parent.rmdir()
    manifest_path = release / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["payloads"] = [
        row for row in manifest["payloads"] if row["path"] != "meshes/base.stl"
    ]
    manifest["payload_count"] = len(manifest["payloads"])
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    must_fail(run([KPY, VERIFY, release]), "zero-mesh release",
              "lacks at least one meshes/*.stl")


@test("predecessors stay within one exact enclosure artifact stream",
      kind="known_bad", gate="stage_enclosure_release.py")
def t_predecessor_artifact_stream_bites():
    fixture = _fixture()
    must_pass(run(_args(fixture)), "publish predecessor for stream test")
    predecessor = _release(fixture)
    manifest_path = predecessor / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["artifact_id"] = "different-enclosure"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    must_fail(run(_args(
        fixture, version="v0.2.0", predecessor=predecessor.name)),
        "cross-artifact predecessor", "different artifact stream")


@test("release verifier reopens every copied PCB authority byte",
      kind="known_bad", gate="verify_enclosure_release.py")
def t_release_authority_tamper_bites():
    fixture = _fixture()
    must_pass(run(_args(fixture)), "candidate publication before authority tamper")
    release = _release(fixture)
    authority = release / "authorities" / "pcb-release" / "source" / "array.kicad_pcb"
    authority.write_bytes(authority.read_bytes() + b"\n# tampered\n")
    must_fail(run([KPY, VERIFY, release]), "tampered release-local PCB",
              "bound size/hash differs")


if __name__ == "__main__":
    sys.exit(main())
