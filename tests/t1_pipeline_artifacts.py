#!/usr/bin/env python3
"""Focused regression tests for transactional pipeline artifact bundles."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import check, eq, main, test, tmpdir  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skills" / "pcb-design" / "scripts"))
import pipeline_artifacts as artifacts  # noqa: E402


SEMANTIC = "1" * 64
RAW = "2" * 64


def fixture():
    root = tmpdir("artifact_txn_")
    source = root / "input.csv"
    source.write_text("code,qty\nC1,5\n", encoding="utf-8")
    accepted = root / "accepted"
    return root, source, accepted


def transaction(source, accepted, outputs=None, run_id="run-clean"):
    return artifacts.ArtifactBundleTransaction(
        accepted,
        producer="fixture-producer",
        producer_version="fixture-v1",
        subject={"semantic_sha256": SEMANTIC, "raw_sha256": RAW},
        inputs={"fab/bom.csv": source},
        outputs=outputs or {"result.json": None, "result.csv": None},
        run_id=run_id,
    )


def write_consistent(staging, code="C1", quantity=5):
    (staging / "result.json").write_text(
        json.dumps({"code": code, "quantity": quantity}) + "\n",
        encoding="utf-8",
    )
    (staging / "result.csv").write_text(
        f"code,quantity\n{code},{quantity}\n", encoding="utf-8")


def cross_check(_staging, opened):
    row = opened["result.csv"][0]
    doc = opened["result.json"]
    if row["code"] != doc["code"] or int(row["quantity"]) != doc["quantity"]:
        raise ValueError("JSON and CSV component facts disagree")


def accepted_bytes(path):
    return {
        item.relative_to(path).as_posix(): item.read_bytes()
        for item in path.rglob("*") if item.is_file()
    }


@test("artifact transaction promotes validated outputs and writes bundle.json last")
def t_clean_publication():
    _root, source, accepted = fixture()
    observed = {}

    def serialize(staging, producer_value):
        eq(producer_value, {"code": "C1", "quantity": 5}, "producer state")
        check(not (staging / "bundle.json").exists(),
              "manifest existed before final-state serialization")
        write_consistent(staging, producer_value["code"], producer_value["quantity"])

    def reopen(staging, opened):
        check(not (staging / "bundle.json").exists(),
              "manifest existed before reopen validation")
        cross_check(staging, opened)
        observed.update(opened["result.json"])

    result = transaction(source, accepted).publish(
        lambda _staging: {"code": "C1", "quantity": 5},
        final_state_serializer=serialize,
        reopen_validator=reopen,
    )
    eq(result.path, accepted, "published path")
    eq(result.replaced_existing, False, "first publication")
    eq(observed, {"code": "C1", "quantity": 5}, "durable reopened state")
    manifest = json.loads((accepted / "bundle.json").read_text())
    eq(manifest["schema"], 1, "bundle schema")
    eq(manifest["status"], "PASS", "bundle status")
    eq(manifest["run_id"], "run-clean", "bundle run identity")
    eq(manifest["inputs"]["fab/bom.csv"]["size"], source.stat().st_size,
       "declared input size")
    for name in ("result.csv", "result.json"):
        data = (accepted / name).read_bytes()
        eq(manifest["outputs"][name]["sha256"], hashlib.sha256(data).hexdigest(),
           f"{name} manifest hash")
        eq(manifest["outputs"][name]["size"], len(data),
           f"{name} manifest size")


@test("artifact transaction atomically replaces an accepted bundle")
def t_replace_publication():
    _root, source, accepted = fixture()
    first = transaction(source, accepted, run_id="run-one")
    first.publish(lambda staging: write_consistent(staging, quantity=5),
                  reopen_validator=cross_check)
    second = transaction(source, accepted, run_id="run-two")
    result = second.publish(lambda staging: write_consistent(staging, quantity=7),
                            reopen_validator=cross_check)
    eq(result.replaced_existing, True, "replacement classification")
    eq(json.loads((accepted / "result.json").read_text())["quantity"], 7,
       "new accepted evidence")
    eq(json.loads((accepted / "bundle.json").read_text())["run_id"], "run-two",
       "new accepted manifest")


@test("fresh sibling workspace rejects reliance on stale accepted output",
      kind="known_bad")
def t_stale_preexisting_output():
    _root, source, accepted = fixture()
    transaction(source, accepted, run_id="run-old").publish(
        lambda staging: write_consistent(staging), reopen_validator=cross_check)
    before = accepted_bytes(accepted)
    try:
        transaction(source, accepted, run_id="run-stale").publish(
            lambda _staging: 0, reopen_validator=cross_check)
    except artifacts.ArtifactValidationError as exc:
        check("missing output" in str(exc), "stale rejection diagnosis")
    else:
        raise AssertionError("old accepted files satisfied a new transaction")
    eq(accepted_bytes(accepted), before, "accepted bundle after stale rejection")


@test("accepted bundle cannot contain a declared input", kind="known_bad")
def t_bundle_cannot_replace_input_tree():
    root, source, _accepted = fixture()
    before = {path.relative_to(root).as_posix(): path.read_bytes()
              for path in root.rglob("*") if path.is_file()}
    try:
        transaction(source, root, run_id="run-destructive")
    except artifacts.ArtifactDeclarationError as exc:
        check("contain declared input" in str(exc),
              "destructive target diagnosis missing")
    else:
        raise AssertionError("project-root accepted bundle was allowed")
    after = {path.relative_to(root).as_posix(): path.read_bytes()
             for path in root.rglob("*") if path.is_file()}
    eq(after, before, "constructor mutated the input tree")


@test("exit-zero producer with a missing declared output is rejected",
      kind="known_bad")
def t_exit_zero_missing_output():
    _root, source, accepted = fixture()

    def incomplete(staging):
        (staging / "result.json").write_text('{"code":"C1","quantity":5}\n')
        return 0

    try:
        transaction(source, accepted).publish(incomplete)
    except artifacts.ArtifactValidationError as exc:
        check("missing output" in str(exc), "missing output diagnosis")
    else:
        raise AssertionError("exit-zero producer published incomplete bundle")
    check(not accepted.exists(), "incomplete first bundle was published")


@test("zero-byte declared output is rejected and prior bundle survives",
      kind="known_bad")
def t_zero_byte_output():
    _root, source, accepted = fixture()
    transaction(source, accepted, run_id="run-old").publish(
        lambda staging: write_consistent(staging), reopen_validator=cross_check)
    before = accepted_bytes(accepted)

    def empty_csv(staging):
        (staging / "result.json").write_text('{"code":"C1","quantity":5}\n')
        (staging / "result.csv").touch()

    try:
        transaction(source, accepted, run_id="run-empty").publish(empty_csv)
    except artifacts.ArtifactValidationError as exc:
        check("is empty" in str(exc), "empty output diagnosis")
    else:
        raise AssertionError("zero-byte output was published")
    eq(accepted_bytes(accepted), before, "accepted bundle after empty output")


@test("unparsable output is rejected", kind="known_bad")
def t_unparsable_output():
    _root, source, accepted = fixture()

    def malformed(staging):
        (staging / "result.json").write_text('{"code":')
        (staging / "result.csv").write_text("code,quantity\nC1,5\n")

    try:
        transaction(source, accepted).publish(malformed)
    except artifacts.ArtifactValidationError as exc:
        check("unparsable" in str(exc), "parse rejection diagnosis")
    else:
        raise AssertionError("malformed JSON was published")
    check(not accepted.exists(), "unparsable first bundle was published")


@test("cross-format fact disagreement is rejected and prior bundle survives",
      kind="known_bad")
def t_cross_check_disagreement():
    _root, source, accepted = fixture()
    transaction(source, accepted, run_id="run-old").publish(
        lambda staging: write_consistent(staging), reopen_validator=cross_check)
    before = accepted_bytes(accepted)

    def mixed(staging):
        (staging / "result.json").write_text('{"code":"C1","quantity":5}\n')
        (staging / "result.csv").write_text("code,quantity\nC1,6\n")

    try:
        transaction(source, accepted, run_id="run-mixed").publish(
            mixed, reopen_validator=cross_check)
    except artifacts.ArtifactValidationError as exc:
        check("reopen validation failed" in str(exc),
              "cross-format rejection diagnosis")
    else:
        raise AssertionError("cross-format disagreement was published")
    eq(accepted_bytes(accepted), before, "accepted bundle after disagreement")


@test("producer interruption preserves the accepted bundle", kind="known_bad")
def t_interrupted_producer():
    _root, source, accepted = fixture()
    transaction(source, accepted, run_id="run-old").publish(
        lambda staging: write_consistent(staging), reopen_validator=cross_check)
    before = accepted_bytes(accepted)

    def interrupted(staging):
        (staging / "result.json").write_text('{"partial":true}\n')
        raise KeyboardInterrupt("simulated operator interruption")

    try:
        transaction(source, accepted, run_id="run-interrupted").publish(interrupted)
    except KeyboardInterrupt:
        pass
    else:
        raise AssertionError("interrupted producer unexpectedly returned")
    eq(accepted_bytes(accepted), before, "accepted bundle after interruption")


@test("non-zero producer result preserves the accepted bundle", kind="known_bad")
def t_failed_producer():
    _root, source, accepted = fixture()
    transaction(source, accepted, run_id="run-old").publish(
        lambda staging: write_consistent(staging), reopen_validator=cross_check)
    before = accepted_bytes(accepted)

    def failed(staging):
        (staging / "result.json").write_text('{"partial":true}\n')
        return 17

    try:
        transaction(source, accepted, run_id="run-failed").publish(failed)
    except artifacts.ArtifactProducerError as exc:
        check("non-zero status 17" in str(exc), "producer failure diagnosis")
    else:
        raise AssertionError("failed producer unexpectedly published")
    eq(accepted_bytes(accepted), before, "accepted bundle after producer failure")


@test("boolean producer result cannot masquerade as status zero", kind="known_bad")
def t_boolean_producer_result():
    _root, source, accepted = fixture()
    try:
        transaction(source, accepted).publish(lambda _staging: False)
    except artifacts.ArtifactProducerError as exc:
        check("boolean" in str(exc), "boolean producer-result diagnosis")
    else:
        raise AssertionError("False producer result was accepted as success")
    check(not accepted.exists(), "boolean producer result published a bundle")


@test("failed atomic promotion preserves the accepted bundle", kind="known_bad")
def t_failed_promotion():
    _root, source, accepted = fixture()
    transaction(source, accepted, run_id="run-old").publish(
        lambda staging: write_consistent(staging), reopen_validator=cross_check)
    before = accepted_bytes(accepted)
    original = artifacts._rename_exchange

    def fail_exchange(_source, _target):
        raise OSError("simulated filesystem promotion failure")

    artifacts._rename_exchange = fail_exchange
    try:
        try:
            transaction(source, accepted, run_id="run-failed-promote").publish(
                lambda staging: write_consistent(staging, quantity=9),
                reopen_validator=cross_check,
            )
        except artifacts.ArtifactPromotionError as exc:
            check("atomic promotion failed" in str(exc),
                  "promotion failure diagnosis")
        else:
            raise AssertionError("failed promotion unexpectedly succeeded")
    finally:
        artifacts._rename_exchange = original
    eq(accepted_bytes(accepted), before, "accepted bundle after promotion failure")


@test("retained promotion failure strips the unaccepted manifest",
      kind="known_bad")
def t_retained_failed_promotion_has_no_manifest():
    _root, source, accepted = fixture()
    transaction(source, accepted, run_id="run-old").publish(
        lambda staging: write_consistent(staging), reopen_validator=cross_check)
    before = accepted_bytes(accepted)
    tx = artifacts.ArtifactBundleTransaction(
        accepted,
        producer="fixture-producer",
        producer_version="fixture-v1",
        subject={"semantic_sha256": SEMANTIC, "raw_sha256": RAW},
        inputs={"fab/bom.csv": source},
        outputs={"result.json": None, "result.csv": None},
        run_id="run-retained-promote-fail",
        retain_failed=True,
    )
    original = artifacts._rename_exchange

    def fail_exchange(_source, _target):
        raise OSError("simulated promotion failure")

    artifacts._rename_exchange = fail_exchange
    try:
        try:
            tx.publish(lambda staging: write_consistent(staging, quantity=11),
                       reopen_validator=cross_check)
        except artifacts.ArtifactPromotionError:
            pass
        else:
            raise AssertionError("failed promotion unexpectedly succeeded")
    finally:
        artifacts._rename_exchange = original
    check(tx.failed_workspace is not None, "failure workspace identity")
    check(not (tx.failed_workspace / "bundle.json").exists(),
          "unaccepted PASS manifest survived promotion failure")
    check((tx.failed_workspace / "result.json").is_file(),
          "producer diagnostic output was not retained")
    eq(accepted_bytes(accepted), before,
       "accepted bytes after retained promotion failure")


@test("undeclared producer output is rejected", kind="known_bad")
def t_undeclared_output():
    _root, source, accepted = fixture()

    def extra(staging):
        write_consistent(staging)
        (staging / "debug.log").write_text("not declared\n")

    try:
        transaction(source, accepted).publish(extra)
    except artifacts.ArtifactValidationError as exc:
        check("undeclared output" in str(exc), "undeclared output diagnosis")
    else:
        raise AssertionError("undeclared producer output was published")


@test("producer-created nested output symlink is rejected before parsing",
      kind="known_bad")
def t_nested_parent_symlink():
    root, source, accepted = fixture()
    outside = root / "outside"
    outside.mkdir()
    (outside / "result.json").write_text('{"code":"C1","quantity":5}\n')
    tx = transaction(
        source,
        accepted,
        outputs={"nested/result.json": None},
        run_id="run-symlink",
    )

    def symlink_parent(staging):
        (staging / "nested").symlink_to(outside, target_is_directory=True)

    try:
        tx.publish(symlink_parent)
    except artifacts.ArtifactValidationError as exc:
        check("output" in str(exc) and (
            "escapes" in str(exc) or "symlink" in str(exc)),
            "nested symlink diagnosis")
    else:
        raise AssertionError("nested output symlink was followed and published")
    check(not accepted.exists(), "symlinked first bundle was published")


@test("producer-created hardlinked output cannot enter an accepted bundle",
      kind="known_bad")
def t_hardlinked_output():
    _root, source, accepted = fixture()
    before = source.read_bytes()

    def hardlinked(staging):
        (staging / "result.json").hardlink_to(source)
        (staging / "result.csv").write_text(
            "code,quantity\nC1,5\n", encoding="utf-8")

    try:
        transaction(source, accepted, run_id="run-hardlink").publish(hardlinked)
    except artifacts.ArtifactValidationError as exc:
        check("multiply-linked" in str(exc), "hardlink diagnosis missing")
    else:
        raise AssertionError("hardlinked producer output was published")
    eq(source.read_bytes(), before, "declared input changed during rejection")
    check(not accepted.exists(), "hardlinked first bundle was published")


@test("opt-in failed workspace retention preserves exact diagnostics and prior good",
      kind="known_bad")
def t_retain_failed_workspace():
    _root, source, accepted = fixture()
    transaction(source, accepted, run_id="run-old").publish(
        lambda staging: write_consistent(staging), reopen_validator=cross_check)
    before = accepted_bytes(accepted)
    tx = artifacts.ArtifactBundleTransaction(
        accepted,
        producer="fixture-producer",
        producer_version="fixture-v1",
        subject={"semantic_sha256": SEMANTIC, "raw_sha256": RAW},
        inputs={"fab/bom.csv": source},
        outputs={"result.json": None, "result.csv": None},
        run_id="run-known-bad",
        retain_failed=True,
    )

    def failed(staging):
        (staging / "result.json").write_text('{"partial":true}\n')
        (staging / "result.csv").write_text("code,quantity\nC1,\n")
        return 23

    try:
        tx.publish(failed)
    except artifacts.ArtifactProducerError:
        pass
    else:
        raise AssertionError("failed producer unexpectedly published")
    expected = accepted.parent / "accepted.failed-run-known-bad"
    eq(tx.failed_workspace, expected, "retained workspace identity")
    check(expected.is_dir(), "failed workspace was not retained")
    check(not (expected / "bundle.json").exists(),
          "rejected workspace received an acceptance manifest")
    check((expected / "result.json").read_text() == '{"partial":true}\n',
          "failed diagnostic bytes changed")
    eq(accepted_bytes(accepted), before,
       "accepted bundle after retained failed attempt")


if __name__ == "__main__":
    raise SystemExit(main())
