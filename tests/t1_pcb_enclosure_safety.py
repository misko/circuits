#!/usr/bin/env python3
"""Adversarial packaging tests for enclosure receipts and output safety."""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

import yaml

import harness as _harness

# Reuse the intentionally small synthetic enclosure without registering the
# original suite's tests a second time in this process.
_original_test = _harness.test
_harness.test = lambda *args, **kwargs: lambda function: function
try:
    import t1_pcb_enclosure as _base
finally:
    _harness.test = _original_test

from harness import check, contains, eq, main, must_fail, must_pass, run, test


ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "pcb-enclosure" / "scripts"
PACKAGE = SCRIPTS / "package_enclosure.py"
BUILD_COLLISION = SCRIPTS / "build_collision.py"
KPY = "/usr/bin/python3"
sys.path.insert(0, str(SCRIPTS))
from enclosure_common import EnclosureError, run_bounded, stable_input_snapshot
sys.path.pop(0)


def _fixture() -> dict[str, Path]:
    """Return the shared derived fixture with its release authority bound."""
    fixture = _base._fresh_fixture()
    config = yaml.safe_load(fixture["config"].read_text())
    if "release_manifest" not in config["subject"]:
        manifest = fixture["root"] / "subject" / "release-manifest.json"
        _base._write_json(manifest, {
            "schema": 1,
            "kind": "synthetic-pcb-release-manifest",
            "release": config["subject"]["release"],
        })
        config["subject"]["release_manifest"] = _base._binding(
            fixture["root"], manifest)
        _base._write_yaml(fixture["config"], config)
        generation_path = fixture["build"] / "generation.json"
        generation = json.loads(generation_path.read_text())
        generation["config"] = {
            "path": str(fixture["config"]),
            "semantic_sha256": _base._semantic_sha(config),
            "raw_sha256": _base._sha(fixture["config"]),
        }
        _base._write_json(generation_path, generation)
    return fixture


def _verify(fixture: dict[str, Path]) -> None:
    must_pass(run(_base._verify_args(fixture)), "verification before package")


def _package_args(fixture: dict[str, Path], output: Path) -> list[Path | str]:
    return [
        KPY, PACKAGE, fixture["config"], "--root", fixture["root"],
        "--build-dir", fixture["build"], "--output", output,
    ]


def _rewrite_report(fixture: dict[str, Path], mutate) -> None:
    report = json.loads(fixture["report"].read_text())
    mutate(report)
    _base._write_json(fixture["report"], report)


@test("enclosure package rejects a forged one-check verification receipt",
      kind="known_bad", gate="package_enclosure.py")
def t_forged_short_census_bites():
    fixture = _fixture()
    _verify(fixture)

    def forge(report):
        report["checks"] = report["checks"][:1]
        report["summary"] = {
            "passed": 1, "failed": 0, "incomplete": 0, "total": 1,
        }

    _rewrite_report(fixture, forge)
    output = fixture["build"] / "forged.zip"
    must_fail(run(_package_args(fixture, output)), "forged package receipt",
              "closed seven-check v1 census")
    check(not output.exists(), "forged receipt published an archive")


@test("enclosure package rejects a missing verification receipt",
      kind="known_bad", gate="package_enclosure.py")
def t_missing_verification_receipt_bites():
    fixture = _fixture()
    _verify(fixture)
    fixture["report"].unlink()
    output = fixture["build"] / "missing-receipt.zip"
    must_fail(run(_package_args(fixture, output)),
              "missing verification receipt", "cannot inspect")
    check(not output.exists(), "missing receipt published an archive")


@test("enclosure package rejects missing and duplicate verification checks",
      kind="known_bad", gate="package_enclosure.py")
def t_missing_and_duplicate_checks_bite():
    for mutation, expected in (
            ("missing", "missing=['physical_evidence']"),
            ("duplicate", "duplicate=['subject_binding']")):
        fixture = _fixture()
        _verify(fixture)
        report = json.loads(fixture["report"].read_text())
        if mutation == "missing":
            report["checks"].pop()
        else:
            report["checks"][-1] = copy.deepcopy(report["checks"][0])
        report["summary"] = {
            "passed": sum(row["status"] == "PASS" for row in report["checks"]),
            "failed": sum(row["status"] == "FAIL" for row in report["checks"]),
            "incomplete": sum(row["status"] == "INCOMPLETE"
                              for row in report["checks"]),
            "total": len(report["checks"]),
        }
        _base._write_json(fixture["report"], report)
        result = must_fail(
            run(_package_args(fixture, fixture["build"] / f"{mutation}.zip")),
            f"{mutation} package check census")
        contains(result.out, expected)


@test("enclosure package freshly regrades a structurally valid receipt",
      kind="known_bad", gate="package_enclosure.py")
def t_forged_evidence_regrade_bites():
    fixture = _fixture()
    _verify(fixture)
    prior = b"prior-package-must-survive\n"
    output = fixture["build"] / "existing.zip"
    output.write_bytes(prior)

    def forge(report):
        thermal = next(row for row in report["checks"]
                       if row["name"] == "thermal_plan")
        thermal["evidence"]["risk"] = "high"

    _rewrite_report(fixture, forge)
    must_fail(run(_package_args(fixture, output)), "fresh package regrade",
              "does not match a fresh seven-check workspace regrade")
    eq(output.read_bytes(), prior, "prior package after failed regrade")


@test("enclosure package refuses duplicate JSON receipt keys",
      kind="known_bad", gate="package_enclosure.py")
def t_duplicate_json_key_bites():
    fixture = _fixture()
    _verify(fixture)
    payload = fixture["report"].read_text()
    fixture["report"].write_text(
        payload.replace("{\n", "{\n  \"schema\": 1,\n", 1))
    result = must_fail(
        run(_package_args(fixture, fixture["build"] / "duplicate-key.zip")),
        "duplicate JSON receipt key", "duplicate JSON key 'schema'")
    contains(result.out, "ENCLOSURE PACKAGE ERROR")


@test("package output cannot replace or hardlink-alias any package input",
      kind="known_bad", gate="package_enclosure.py")
def t_output_input_aliases_bite():
    fixture = _fixture()
    _verify(fixture)
    mesh = fixture["build"] / "base.stl"
    mesh_before = mesh.read_bytes()
    must_fail(run(_package_args(fixture, mesh)), "same-path package output",
              "destination aliases input file")
    eq(mesh.read_bytes(), mesh_before, "same-path input after package refusal")

    alias = fixture["build"] / "hardlink.zip"
    config_before = fixture["config"].read_bytes()
    os.link(fixture["config"], alias)
    must_fail(run(_package_args(fixture, alias)), "hardlink package output",
              "hard-linked files are not accepted")
    eq(fixture["config"].read_bytes(), config_before,
       "hardlinked config after package refusal")


@test("package output rejects symlink ancestors and build-root escapes",
      kind="known_bad", gate="package_enclosure.py")
def t_unsafe_output_layout_bites():
    fixture = _fixture()
    _verify(fixture)
    outside = fixture["work"] / "outside"
    outside.mkdir()
    link = fixture["build"] / "linked-output"
    link.symlink_to(outside, target_is_directory=True)
    must_fail(
        run(_package_args(fixture, link / "escape.zip")),
        "symlink-ancestor package output", "symlink path component")
    check(not (outside / "escape.zip").exists(),
          "package escaped through a symlink ancestor")
    must_fail(
        run(_package_args(fixture, fixture["root"] / "outside-build.zip")),
        "outside-build package output", "must be a file beneath build root")


@test("package archive publication is atomic across a mid-write failure",
      kind="known_bad", gate="package_enclosure.py")
def t_atomic_archive_failure_preserves_prior_bytes():
    fixture = _fixture()
    _verify(fixture)
    output = fixture["build"] / "atomic.zip"
    prior = b"known-prior-archive\n"
    output.write_bytes(prior)

    spec = importlib.util.spec_from_file_location(
        "_enclosure_package_for_atomic_test", PACKAGE)
    check(spec is not None and spec.loader is not None,
          "could not load package module")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(SCRIPTS))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    real_zip = module.zipfile.ZipFile

    class FailingZip(real_zip):
        writes = 0

        def writestr(self, *args, **kwargs):
            result = super().writestr(*args, **kwargs)
            self.writes += 1
            if self.writes == 2:
                raise OSError("synthetic archive write failure")
            return result

    module.zipfile.ZipFile = FailingZip
    try:
        try:
            module.package(fixture["config"], fixture["root"],
                           fixture["build"], output, False)
        except OSError as exc:
            contains(str(exc), "synthetic archive write failure")
        else:
            check(False, "synthetic mid-write failure unexpectedly succeeded")
    finally:
        module.zipfile.ZipFile = real_zip
    eq(output.read_bytes(), prior, "prior archive after mid-write failure")
    check(not list(fixture["build"].glob(".atomic.zip.*.tmp")),
          "atomic package left a partial temporary file")


@test("package snapshots the same bytes it censuses before archive publication",
      kind="known_bad", gate="package_enclosure.py")
def t_mid_census_input_mutation_bites():
    fixture = _fixture()
    _verify(fixture)
    output = fixture["build"] / "snapshot-race.zip"
    prior = b"prior-package-must-survive\n"
    output.write_bytes(prior)

    spec = importlib.util.spec_from_file_location(
        "_enclosure_package_for_snapshot_test", PACKAGE)
    check(spec is not None and spec.loader is not None,
          "could not load package module")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(SCRIPTS))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    real_entry = module._entry
    base = fixture["build"] / "base.stl"
    original = base.read_bytes()
    changed = False

    def mutate_after_census(path, arcname):
        nonlocal changed
        row = real_entry(path, arcname)
        if arcname == "meshes/base.stl" and not changed:
            changed = True
            path.write_bytes(original + b"\nsolid substituted\nendsolid substituted\n")
        return row

    module._entry = mutate_after_census
    try:
        try:
            module.package(fixture["config"], fixture["root"],
                           fixture["build"], output, False)
        except module.EnclosureError as exc:
            contains(str(exc), "changed after census")
        else:
            check(False, "mid-census input mutation unexpectedly published")
    finally:
        module._entry = real_entry
    eq(output.read_bytes(), prior, "prior archive after input mutation")


@test("derived enclosure configs require an exact release-manifest binding",
      kind="known_bad", gate="enclosure_common.py")
def t_derived_release_authority_bites():
    fixture = _fixture()
    config = yaml.safe_load(fixture["config"].read_text())
    config["subject"].pop("release_manifest")
    _base._write_yaml(fixture["config"], config)
    result = must_fail(run(_base._verify_args(fixture)),
                       "derived config without release authority",
                       "mode derived requires an exact PCB release-manifest binding")
    contains(result.out, "ENCLOSURE VERIFICATION FAIL")


@test("enclosure schema rejects duplicate case-fastener coordinates",
      kind="known_bad", gate="enclosure_common.py")
def t_duplicate_case_fastener_axes_bite():
    fixture = _fixture()
    config = yaml.safe_load(fixture["config"].read_text())
    config["fasteners"]["strategy"] = "separate_perimeter"
    config["fasteners"]["case_holes_mm"] = [
        [-28.0, -18.0], [28.0, -18.0], [-28.0, 18.0], [-28.0, 18.0],
    ]
    _base._write_yaml(fixture["config"], config)
    must_fail(run(_base._verify_args(fixture)),
              "duplicate case-fastener coordinate",
              "duplicate case-fastener axis")


@test("multi-pass CAD parsers consume one private input snapshot",
      kind="known_bad", gate="enclosure_common.py")
def t_private_parser_snapshot_prevents_mixed_subjects():
    root = _base.tmpdir("enclosure_stable_snapshot_")
    subject = root / "assembly.step"
    original = b"STEP-A-authoritative\n"
    subject.write_bytes(original)

    # A transient replacement cannot affect the bytes seen by later parser
    # passes because they receive the private path, not the live subject.
    try:
        with stable_input_snapshot(subject, "synthetic STEP") as \
                (snapshot, binding):
            subject.write_bytes(b"STEP-B-transient----\n")
            eq(snapshot.read_bytes(), original, "private parser subject")
            subject.write_bytes(original)
            eq(binding["size"], len(original), "snapshot binding size")
    except EnclosureError as exc:
        contains(str(exc), "original changed during use")
    else:
        check(False, "transiently changed parser subject was accepted")

    # A mutation that remains at publication time is rejected as well.
    try:
        with stable_input_snapshot(subject, "synthetic STEP"):
            subject.write_bytes(b"STEP-C-final-mutation\n")
    except EnclosureError as exc:
        contains(str(exc), "original changed during use")
    else:
        check(False, "changed multi-pass parser subject was accepted")


@test("collision builder routes every multi-pass authority through snapshots")
def t_collision_builder_uses_private_subjects():
    root = _base.tmpdir("enclosure_collision_snapshots_")
    build = root / "build"
    build.mkdir()
    step = root / "assembly.step"
    step.write_bytes(b"STEP subject\n")
    step_report = build / "step-inspection.json"
    component = build / "step-components.stl"
    interface = build / "board-interface.json"
    generation = build / "generation.json"
    case = build / "assembled-case.stl"
    source = build / "enclosure.scad"
    for path, payload in (
            (step_report, b"{}\n"), (interface, b"{}\n"),
            (component, b"solid c\nendsolid c\n"),
            (case, b"solid a\nendsolid a\n"),
            (source, b"cube([1,1,1]);\n")):
        path.write_bytes(payload)
    _base._write_json(generation, {
        "source": {"path": source.name, "sha256": _base._sha(source),
                   "size": source.stat().st_size},
    })

    spec = importlib.util.spec_from_file_location(
        "_enclosure_collision_snapshot_test", BUILD_COLLISION)
    check(spec is not None and spec.loader is not None,
          "could not load collision module")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(SCRIPTS))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    real_build = module._build_snapshots
    observed = {}

    def fake_build(step_copy, report_copy, component_copy, interface_copy,
                   generation_copy, case_copy, source_copy, board_z, output,
                   report_output, originals, bindings):
        copies = {
            "step": step_copy, "step_report": report_copy,
            "component_mesh": component_copy, "interface": interface_copy,
            "generation": generation_copy,
            "case_mesh": case_copy, "source": source_copy,
        }
        for key, copy in copies.items():
            check(copy != originals[key] and copy.is_file(),
                  f"{key} did not use a private snapshot")
            eq(_base._sha(copy), bindings[key]["sha256"],
               f"{key} snapshot digest")
        observed["called"] = True
        return {"status": "COMPLETE"}

    module._build_snapshots = fake_build
    try:
        result = module.build(
            step, step_report, component, interface, generation, case, 7.8,
            build / "intersection.stl", build / "collision.json")
    finally:
        module._build_snapshots = real_build
    eq(result["status"], "COMPLETE", "snapshot-wrapped collision result")
    check(observed.get("called") is True,
          "snapshot-wrapped collision implementation was not called")


@test("collision receipts name the published mesh, not the atomic staging file")
def t_collision_metrics_use_published_name():
    root = _base.tmpdir("enclosure_collision_metric_name_")
    staged = root / ".intersection.stl.synthetic.stl"
    staged.write_text(
        "solid empty_intersection\n"
        "  facet normal 0 0 0\n"
        "    outer loop\n"
        "      vertex 0 0 0\n"
        "      vertex 0 0 0\n"
        "      vertex 0 0 0\n"
        "    endloop\n"
        "  endfacet\n"
        "endsolid empty_intersection\n")

    spec = importlib.util.spec_from_file_location(
        "_enclosure_collision_metric_name_test", BUILD_COLLISION)
    check(spec is not None and spec.loader is not None,
          "could not load collision module")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(SCRIPTS))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)

    metrics = module._metrics_named(staged, "intersection.stl")
    eq(metrics["path"], "intersection.stl", "published collision-mesh name")
    check(staged.name not in json.dumps(metrics),
          "collision metrics leaked the atomic staging filename")


@test("bounded enclosure subprocess capture truncates and times out safely",
      kind="known_bad", gate="enclosure_common.py")
def t_bounded_subprocess_limits_bite():
    result = run_bounded(
        [sys.executable, "-c", "print('x' * 10000)"],
        timeout_s=2, max_output_bytes_per_stream=128, check=True)
    contains(result.stdout, "output truncated; retained final 128")
    check(len(result.stdout) < 256, "bounded capture retained unbounded output")

    started = time.monotonic()
    try:
        run_bounded(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            timeout_s=0.1, max_output_bytes_per_stream=128)
    except EnclosureError as exc:
        contains(str(exc), "timed out after 0.1s")
    else:
        check(False, "bounded subprocess ignored its deadline")
    check(time.monotonic() - started < 2,
          "timed-out subprocess was not cleaned up promptly")

    orphan_code = (
        "import subprocess,sys; "
        "subprocess.Popen([sys.executable,'-c',"
        "'import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); "
        "time.sleep(30)'])"
    )
    started = time.monotonic()
    try:
        run_bounded([sys.executable, "-c", orphan_code], timeout_s=0.1,
                    max_output_bytes_per_stream=128)
    except EnclosureError as exc:
        contains(str(exc), "timed out after 0.1s")
    else:
        check(False, "orphaned process-group member escaped its deadline")
    # The shared pipeline runtime grants a bounded TERM/KILL and output-drain
    # grace after the hard command deadline.  The whole call must still return
    # within that declared finite envelope.
    check(time.monotonic() - started < 6,
          "orphaned process group was not killed promptly")


if __name__ == "__main__":
    sys.exit(main())
