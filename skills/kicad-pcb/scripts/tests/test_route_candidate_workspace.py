#!/usr/bin/env python3
"""Contract tests for immutable route-candidate grading."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from route_candidate_workspace import (  # noqa: E402
    CommandResult, grade_candidate, verify_receipt,
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
        self.assertEqual(receipt["verdict"], "REJECTED")
        self.assertEqual(receipt["checks"]["physical_drc"]["status"], "FAIL")
        self.assertEqual(
            receipt["shadow_checks"]["native_drc_delta"]["authority"],
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
        self.assertEqual(receipt["checks"]["physical_drc"]["status"], "FAIL")
        self.assertEqual(receipt["verdict"], "REJECTED")
        self.assertIn("native_drc_delta", receipt["shadow_checks"])

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

    def test_shadow_drc_failure_cannot_change_legacy_acceptance(self):
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
        self.assertEqual(receipt["verdict"], "ACCEPTED")
        self.assertEqual(
            receipt["shadow_checks"]["native_drc_delta"]["status"],
            "INCOMPLETE")


if __name__ == "__main__":
    unittest.main()
