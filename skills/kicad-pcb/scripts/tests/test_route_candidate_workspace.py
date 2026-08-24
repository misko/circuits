#!/usr/bin/env python3
"""Contract tests for immutable route-candidate grading."""
import json
import inspect
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import route_candidate_workspace as candidate_workspace  # noqa: E402
from route_candidate_workspace import (  # noqa: E402
    CommandResult, grade_candidate, publish_accepted_bundle,
    verify_accepted_bundle, verify_receipt,
)


class FakeRunner:
    def __init__(self, *, routebase_pass=True, via_pass=True):
        self.routebase_pass = routebase_pass
        self.via_pass = via_pass

    def __call__(self, command, cwd):
        joined = " ".join(command)
        if "promoted_route_check.py" in joined:
            return CommandResult(0 if self.routebase_pass else 1, "P-ROUTEBASE")
        if "via_in_pad_guard.py" in joined:
            report = Path(command[command.index("--json") + 1])
            report.write_text(json.dumps({"verdict": "PASS" if self.via_pass else "FAIL"}))
            return CommandResult(0 if self.via_pass else 1, "via")
        if " connectivity " in f" {joined} ":
            report = Path(command[command.index("--json") + 1])
            report.write_text(json.dumps({"verdict": "PASS", "failures": []}))
            return CommandResult(0, "connected")
        if command[:3] == ["kicad-cli", "pcb", "drc"]:
            report = Path(command[command.index("-o") + 1])
            # The authoritative prepared rule says this candidate violates USB
            # clearance. A candidate-owned clamped rule would have hidden it.
            authoritative = (cwd / "subject.kicad_dru").read_text()
            subject = Path(command[-1]).name == "subject.kicad_pcb"
            violations = ([{"type": "clearance", "description": "USB floor"}]
                          if subject and "authoritative" in authoritative else [])
            report.write_text(json.dumps({
                "$schema": "https://schemas.kicad.org/drc.v1.json",
                "source": Path(command[-1]).name,
                "date": "2026-08-24T12:00:00Z",
                "kicad_version": "9.0",
                "violations": violations,
                "unconnected_items": [],
                "schematic_parity": [],
            }))
            return CommandResult(0, "drc")
        raise AssertionError(f"unexpected command: {command}")


def fixture(root):
    prepared = root / "r0.kicad_pcb"
    prepared.write_text("prepared geometry")
    prepared.with_suffix(".kicad_pro").write_text("authoritative project")
    prepared.with_suffix(".kicad_dru").write_text("authoritative USB 0.30")
    candidate = root / "candidate.kicad_pcb"
    candidate.write_text("candidate copper")
    candidate.with_suffix(".kicad_pro").write_text("candidate project")
    candidate.with_suffix(".kicad_dru").write_text("clamped USB 0.15")
    return prepared, candidate


class CandidateWorkspaceTest(unittest.TestCase):
    def test_candidate_workspace_does_not_own_subprocess_launch(self):
        source = inspect.getsource(candidate_workspace)
        self.assertNotIn("subprocess.Popen", source)
        self.assertNotIn("subprocess.run", source)

    def test_kicad_connected_items_need_not_be_hashable(self):
        class UnhashableItem:
            __hash__ = None

            def __init__(self, identity):
                self.identity = identity

            def __eq__(self, other):
                return isinstance(other, UnhashableItem) \
                    and self.identity == other.identity

        reached = list([UnhashableItem("track"), UnhashableItem("pad-2")])
        self.assertIn(UnhashableItem("pad-2"), reached)

    def test_candidate_sidecars_cannot_grade_their_own_board(self):
        root = Path(tempfile.mkdtemp(prefix="candidate-workspace-"))
        prepared, candidate = fixture(root)
        # The local diagnostic would see the clamped candidate sidecar as clean.
        self.assertIn("clamped", candidate.with_suffix(".kicad_dru").read_text())
        receipt = grade_candidate(prepared, candidate, root / "grade",
                                  required_nets=["SCL"],
                                  shadow_native_drc=True,
                                  runner=FakeRunner())
        shadow = json.loads((root / "grade/shadow_receipt.json").read_text())
        self.assertEqual(receipt["verdict"], "REJECTED")
        self.assertEqual(receipt["checks"]["physical_drc"]["status"], "FAIL")
        self.assertEqual(
            shadow["checks"]["native_drc_delta"]["authority"],
            "SHADOW")
        self.assertIn("authoritative",
                      (root / "grade/subject.kicad_dru").read_text())

    def test_clean_receipt_is_relocatable_and_tamper_evident(self):
        root = Path(tempfile.mkdtemp(prefix="candidate-workspace-"))
        prepared, candidate = fixture(root)
        prepared.with_suffix(".kicad_dru").write_text("clean prepared rules")
        workspace = root / "grade"
        receipt = grade_candidate(prepared, candidate, workspace,
                                  required_nets=["SCL"], runner=FakeRunner())
        self.assertEqual(receipt["verdict"], "ACCEPTED")
        moved = root / "relocated"
        shutil.move(workspace, moved)
        self.assertTrue(verify_receipt(moved / "receipt.json")[0])
        (moved / "subject.kicad_dru").write_text("mutated")
        valid, failures = verify_receipt(moved / "receipt.json")
        self.assertFalse(valid)
        self.assertTrue(any("artifact changed" in row for row in failures))

    def test_tool_incompletion_never_reads_as_acceptance(self):
        root = Path(tempfile.mkdtemp(prefix="candidate-workspace-"))
        prepared, candidate = fixture(root)

        def incomplete(command, cwd):
            if command[:3] == ["kicad-cli", "pcb", "drc"]:
                return CommandResult(2, "tool failed")
            return FakeRunner()(command, cwd)

        receipt = grade_candidate(prepared, candidate, root / "grade",
                                  runner=incomplete)
        self.assertEqual(receipt["verdict"], "INCOMPLETE")

    def test_shadow_classifier_cannot_weaken_legacy_hard_rejection(self):
        root = Path(tempfile.mkdtemp(prefix="candidate-workspace-"))
        prepared, candidate = fixture(root)
        receipt = grade_candidate(prepared, candidate, root / "grade",
                                  shadow_native_drc=True,
                                  runner=FakeRunner())
        shadow = json.loads((root / "grade/shadow_receipt.json").read_text())
        self.assertEqual(receipt["checks"]["physical_drc"]["status"], "FAIL")
        self.assertEqual(receipt["verdict"], "REJECTED")
        self.assertIn("native_drc_delta", shadow["checks"])

    def test_receipt_status_forgery_breaks_content_binding(self):
        root = Path(tempfile.mkdtemp(prefix="candidate-workspace-"))
        prepared, candidate = fixture(root)
        workspace = root / "grade"
        receipt = grade_candidate(prepared, candidate, workspace,
                                  runner=FakeRunner())
        self.assertEqual(receipt["verdict"], "REJECTED")
        forged = json.loads((workspace / "receipt.json").read_text())
        forged["verdict"] = "ACCEPTED"
        for row in forged["checks"].values():
            row["status"] = "PASS"
        (workspace / "receipt.json").write_text(json.dumps(forged))
        valid, failures = verify_receipt(workspace / "receipt.json")
        self.assertFalse(valid)
        self.assertIn("receipt content binding changed", failures)

    def test_shadow_drc_request_runs_no_extra_tool_or_changes_acceptance(self):
        root = Path(tempfile.mkdtemp(prefix="candidate-workspace-"))
        prepared, candidate = fixture(root)
        prepared.with_suffix(".kicad_dru").write_text("clean prepared rules")
        drc_calls = 0

        def runner(command, cwd):
            nonlocal drc_calls
            if command[:3] == ["kicad-cli", "pcb", "drc"]:
                drc_calls += 1
                if drc_calls > 1:
                    raise RuntimeError("shadow tool unavailable")
            return FakeRunner()(command, cwd)

        receipt = grade_candidate(
            prepared, candidate, root / "grade", shadow_native_drc=True,
            runner=runner)
        shadow = json.loads((root / "grade/shadow_receipt.json").read_text())
        self.assertEqual(receipt["verdict"], "ACCEPTED")
        self.assertEqual(drc_calls, 1)
        self.assertEqual(
            shadow["checks"]["native_drc_delta"]["status"],
            "INCOMPLETE")

    def test_shadow_mutation_scope_does_not_enter_authoritative_receipt(self):
        root = Path(tempfile.mkdtemp(prefix="candidate-workspace-"))
        prepared, candidate = fixture(root)
        prepared.with_suffix(".kicad_dru").write_text("clean prepared rules")
        mutation_baseline = root / "previous.kicad_pcb"
        mutation_baseline.write_text("previous wave copper")
        delta_result = {
            "schema": 1, "kind": "semantic-copper-delta-v1",
            "status": "PASS", "changed": True, "changed_nets": ["SDA"],
            "counts": {"changed_nets": 1}, "findings": [],
        }
        source_result = {
            "schema": 1, "kind": "source-owned-copper-equivalence-v1",
            "status": "PASS", "counts": {"source": 1, "retained": 1,
                                           "missing": 0},
        }
        with mock.patch(
                "route_candidate_workspace._semantic_copper_shadow",
                return_value={
                    "schema": 1,
                    "kind": "route-semantic-copper-shadow-v1",
                    "copper_delta": delta_result,
                    "source_copper_equivalence": source_result,
                }) as semantic:
            receipt = grade_candidate(
                prepared, candidate, root / "grade",
                required_nets=["SCL"], touched_nets=["SDA"],
                mutation_baseline=mutation_baseline,
                shadow_semantic_copper=True, runner=FakeRunner())
        shadow = json.loads((root / "grade/shadow_receipt.json").read_text())
        self.assertEqual(receipt["required_nets"], ["SCL"])
        self.assertNotIn("touched_nets", receipt)
        semantic.assert_not_called()
        self.assertTrue(shadow["requested"]["semantic_copper"])
        self.assertEqual(shadow["requested"]["touched_nets"], ["SDA"])
        self.assertEqual(
            shadow["requested"]["mutation_baseline"]["status"],
            "PENDING")
        self.assertNotIn(
            "sha256", shadow["requested"]["mutation_baseline"],
            "authoritative transaction opened a shadow-only baseline")
        self.assertNotIn("mutation_baseline", receipt["origins"])
        self.assertNotIn("mutation_baseline.kicad_pcb", receipt["artifacts"])

    def test_semantic_copper_is_off_by_default_and_failure_is_contained(self):
        root = Path(tempfile.mkdtemp(prefix="candidate-workspace-"))
        prepared, candidate = fixture(root)
        prepared.with_suffix(".kicad_dru").write_text("clean prepared rules")
        with mock.patch(
                "route_candidate_workspace._semantic_copper_shadow",
                side_effect=RuntimeError("child timed out")) as semantic:
            default = grade_candidate(
                prepared, candidate, root / "default", runner=FakeRunner())
            enabled = grade_candidate(
                prepared, candidate, root / "enabled",
                shadow_semantic_copper=True, runner=FakeRunner())
        self.assertEqual(semantic.call_count, 0)
        default_shadow = json.loads(
            (root / "default/shadow_receipt.json").read_text())
        enabled_shadow = json.loads(
            (root / "enabled/shadow_receipt.json").read_text())
        self.assertEqual(
            default_shadow["checks"]["copper_delta"]["status"], "N-A")
        self.assertEqual(enabled["verdict"], "ACCEPTED")
        self.assertEqual(
            enabled_shadow["checks"]["copper_delta"]["status"],
            "INCOMPLETE")
        self.assertEqual(
            enabled_shadow["checks"]["source_copper_equivalence"]["status"],
            "INCOMPLETE")

    def test_shadow_receipt_churn_cannot_change_authoritative_binding(self):
        root = Path(tempfile.mkdtemp(prefix="candidate-shadow-identity-"))
        prepared, candidate = fixture(root)
        prepared.with_suffix(".kicad_dru").write_text("clean prepared rules")
        workspace = root / "grade"
        receipt = grade_candidate(
            prepared, candidate, workspace, shadow_native_drc=True,
            runner=FakeRunner())
        binding = receipt["binding"]["receipt_sha256"]
        shadow_path = workspace / "shadow_receipt.json"
        shadow = json.loads(shadow_path.read_text())
        shadow["checks"]["native_drc_delta"]["status"] = "PASS"
        shadow_path.write_text(json.dumps(shadow))
        reopened = json.loads((workspace / "receipt.json").read_text())
        self.assertEqual(reopened["binding"]["receipt_sha256"], binding)
        self.assertTrue(verify_receipt(workspace / "receipt.json")[0])
        other_baseline = root / "shadow-only-baseline.kicad_pcb"
        other_baseline.write_text("different shadow baseline")
        second = grade_candidate(
            prepared, candidate, root / "grade-2", touched_nets=["SDA"],
            mutation_baseline=other_baseline,
            shadow_semantic_copper=True, runner=FakeRunner())
        self.assertEqual(
            second["binding"]["receipt_sha256"], binding,
            "shadow scope changed authoritative receipt identity")

    def test_shadow_write_failure_cannot_fail_authoritative_grade(self):
        root = Path(tempfile.mkdtemp(prefix="candidate-shadow-write-"))
        prepared, candidate = fixture(root)
        prepared.with_suffix(".kicad_dru").write_text("clean prepared rules")
        workspace = root / "grade"
        real_atomic = candidate_workspace._atomic_json

        def fail_shadow(path, value):
            if Path(path).name == "shadow_receipt.json":
                raise OSError("shadow disk unavailable")
            return real_atomic(path, value)

        with mock.patch(
                "route_candidate_workspace._atomic_json",
                side_effect=fail_shadow):
            receipt = grade_candidate(
                prepared, candidate, workspace, shadow_native_drc=True,
                runner=FakeRunner())
        self.assertEqual(receipt["verdict"], "ACCEPTED")
        self.assertTrue((workspace / "receipt.json").is_file())
        self.assertTrue(verify_receipt(workspace / "receipt.json")[0])
        self.assertFalse((workspace / "shadow_receipt.json").exists())

    def test_retry_cannot_modify_an_existing_attempt_workspace(self):
        root = Path(tempfile.mkdtemp(prefix="candidate-retry-"))
        prepared, candidate = fixture(root)
        prepared.with_suffix(".kicad_dru").write_text("clean prepared rules")
        workspace = root / "grade"
        grade_candidate(prepared, candidate, workspace, runner=FakeRunner())
        before = {
            path.relative_to(workspace).as_posix(): path.read_bytes()
            for path in workspace.rglob("*") if path.is_file()
        }
        with self.assertRaisesRegex(ValueError, "workspace already exists"):
            grade_candidate(prepared, candidate, workspace,
                            shadow_native_drc=True, runner=FakeRunner())
        after = {
            path.relative_to(workspace).as_posix(): path.read_bytes()
            for path in workspace.rglob("*") if path.is_file()
        }
        self.assertEqual(after, before)

    def test_receipt_rejects_invented_checks_symlinks_and_baseline_mismatch(self):
        root = Path(tempfile.mkdtemp(prefix="candidate-workspace-"))
        prepared, candidate = fixture(root)
        prepared.with_suffix(".kicad_dru").write_text("clean prepared rules")

        def rewrite(workspace, mutate):
            receipt_path = workspace / "receipt.json"
            payload = json.loads(receipt_path.read_text())
            mutate(payload)
            payload["binding"]["receipt_sha256"] = \
                candidate_workspace._receipt_digest(payload)
            receipt_path.write_text(json.dumps(payload))
            return verify_receipt(receipt_path)

        for name, mutate in (
                ("invented", lambda row: row["checks"].__setitem__(
                    "invented", {"status": "PASS"})),
                ("missing", lambda row: row["checks"].pop("route_base")),
                ("baseline", lambda row: row["origins"].__setitem__(
                    "mutation_baseline", row["origins"]["prepared"]))):
            with self.subTest(name=name):
                workspace = root / name
                grade_candidate(prepared, candidate, workspace,
                                runner=FakeRunner())
                valid, failures = rewrite(workspace, mutate)
                self.assertFalse(valid)
                self.assertTrue(any(
                    "census" in value or "presence disagrees" in value
                    for value in failures), failures)

        workspace = root / "symlink"
        grade_candidate(prepared, candidate, workspace, runner=FakeRunner())
        outside = root / "outside"
        outside.mkdir()
        escaped = outside / "escaped.bin"
        escaped.write_bytes(b"same bytes")
        (workspace / "nested").symlink_to(outside, target_is_directory=True)

        def add_escape(payload):
            payload["artifacts"]["nested/escaped.bin"] = \
                candidate_workspace._file_record(escaped)

        valid, failures = rewrite(workspace, add_escape)
        self.assertFalse(valid)
        self.assertTrue(any("traverses a symlink" in value
                            for value in failures), failures)

    def test_promotion_is_fail_closed_and_preserves_pointer(self):
        root = Path(tempfile.mkdtemp(prefix="candidate-workspace-"))
        prepared, candidate = fixture(root)
        prepared.with_suffix(".kicad_dru").write_text("clean prepared rules")
        workspace = root / "grade"
        receipt = grade_candidate(
            prepared, candidate, workspace, runner=FakeRunner())
        self.assertEqual(receipt["verdict"], "ACCEPTED")
        accepted_root = root / "accepted"
        accepted_root.mkdir()
        (accepted_root / "accepted.json").write_bytes(b"existing pointer\n")
        pointer_bytes = (accepted_root / "accepted.json").read_bytes()
        with self.assertRaisesRegex(ValueError, "disabled"):
            publish_accepted_bundle(workspace / "receipt.json", accepted_root)
        self.assertEqual(
            (accepted_root / "accepted.json").read_bytes(), pointer_bytes)
        self.assertFalse((accepted_root / "bundles").exists())


if __name__ == "__main__":
    unittest.main()
