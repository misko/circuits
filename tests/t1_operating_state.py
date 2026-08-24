#!/usr/bin/env python3
"""T1: generic cross-device operating-state compatibility."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (check, eq, main, must_fail, must_pass, run, test,  # noqa: E402
                     tmpdir)

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills/kicad-pcb/scripts"
CHECK = SCRIPTS / "operating_state_check.py"
sys.path.insert(0, str(SCRIPTS))

from operating_state_check import (grade_document, grade_file,  # noqa: E402
                                   verify_receipt)


def endpoint(ref, low, high, *, quantity="voltage", unit="V",
             evidence_sha=None):
    return {"ref": ref, "quantity": quantity, "unit": unit,
            "min": low, "max": high, "evidence": {
                "source": f"02_parts/{ref}/part.yaml",
                "sha256": evidence_sha or "a" * 64,
                "locator": f"exact {ref} authority"}}


def document(source=(19, 21), sink=(16.07, 30), *, evidence=None):
    evidence = evidence or {}
    return {"schema": 1, "contracts": [{
        "id": "pd_to_input_efuse", "phase": "negotiated",
        "producer": endpoint("U_PD", *source,
                             evidence_sha=evidence.get("U_PD")),
        "consumer": endpoint("U_PD_IN", *sink,
                             evidence_sha=evidence.get("U_PD_IN")),
    }]}


def manifest(*rows):
    if not rows:
        rows = (("pd_to_input_efuse", "negotiated"),)
    return {"schema": 1, "expected": [
        {"id": cid, "phase": phase} for cid, phase in sorted(rows)]}


def evidence_tree(root):
    result = {}
    for ref in ("U_PD", "U_PD_IN"):
        path = root / "02_parts" / ref / "part.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"mpn: {ref}\nvalidated_state: true\n")
        result[ref] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


@test("20 V negotiated source is contained by the downstream input window")
def t_compatible_state():
    result = grade_document(document(), manifest())
    eq(result["verdict"], "ACCEPTED")
    eq(result["authority"], "SHADOW",
       "authored endpoint numbers were promoted as extracted truth")
    eq(result["coverage"], {"passing": 1, "total": 1})


@test("CH224K 15 V straps are rejected by the TPS16630 UVLO window",
      kind="known_bad")
def t_ch224_wrong_state():
    result = grade_document(document(source=(15, 15)), manifest())
    eq(result["verdict"], "REJECTED")
    eq(result["findings"][0]["id"], "E-STATE-RANGE")
    check("15..15 V is not within" in result["findings"][0]["detail"],
          "decoded state mismatch was not explicit")


@test("a producer corner outside only one side still fails full containment",
      kind="known_bad")
def t_full_corner_containment():
    eq(grade_document(document(source=(15.9, 20)), manifest())["verdict"], "REJECTED")
    eq(grade_document(document(source=(20, 30.1)), manifest())["verdict"], "REJECTED")


@test("startup, off and fault use the same exact interval composition")
def t_other_phases():
    rows = []
    for cid, phase, source, sink in (
        ("startup_inrush", "startup", (0, 0.42), (0, 0.5)),
        ("off_leakage", "off", (0, 0.00001), (0, 0.0001)),
        ("fault_limit", "fault", (2.08, 2.65), (2.0, 3.0)),
    ):
        rows.append({"id": cid, "phase": phase,
                     "producer": endpoint("source", *source,
                                          quantity="current", unit="A"),
                     "consumer": endpoint("sink", *sink,
                                          quantity="current", unit="A")})
    rows.sort(key=lambda row: row["id"])
    expected = manifest(*((row["id"], row["phase"]) for row in rows))
    result = grade_document({"schema": 1, "contracts": rows}, expected)
    eq(result["verdict"], "ACCEPTED")
    eq(result["coverage"], {"passing": 3, "total": 3})


@test("empty, malformed or unit-confused state contracts are INCOMPLETE",
      kind="known_bad")
def t_schema_fail_closed():
    eq(grade_document({"schema": 1, "contracts": []}, manifest())["verdict"],
       "INCOMPLETE")
    wrong = document()
    wrong["contracts"][0]["consumer"]["unit"] = "A"
    eq(grade_document(wrong, manifest())["verdict"], "INCOMPLETE")
    unknown = document()
    unknown["contracts"][0]["phase"] = "sometimes"
    eq(grade_document(unknown, manifest())["verdict"], "INCOMPLETE")
    eq(grade_document(document(), {"schema": 1, "expected": [
        {"id": "missing_fault", "phase": "fault"}]})["verdict"],
       "INCOMPLETE", "missing manifest-owned state was accepted")


@test("state receipt is exact-source hash bound and becomes stale on change",
      kind="known_bad")
def t_receipt_staleness():
    root = tmpdir("operating-state-")
    evidence = evidence_tree(root)
    config = root / "operating_states.yaml"
    manifest_path = root / "operating_state_manifest.yaml"
    config.write_text(yaml.safe_dump(document(evidence=evidence), sort_keys=False))
    manifest_path.write_text(yaml.safe_dump(manifest(), sort_keys=False))
    receipt = grade_file(config, manifest_path, evidence_root=root)
    eq(receipt["verdict"], "ACCEPTED")
    eq(receipt["authority"], "SHADOW")
    eq(receipt["evidence"]["authority"], "UNVERIFIED")
    check(verify_receipt(receipt)[0], "fresh receipt did not reopen")
    config.write_text(yaml.safe_dump(
        document(source=(15, 15), evidence=evidence), sort_keys=False))
    valid, failures = verify_receipt(receipt)
    check(not valid, "changed source retained an accepted receipt")
    check(any("subject moved or changed" in row for row in failures),
          "staleness reason missing")


@test("the operating-state CLI names its exact inputs and exits nonzero on a "
      "range mismatch", kind="known_bad")
def t_cli_rejects_incompatible_state():
    root = tmpdir("operating-state-cli-")
    evidence = evidence_tree(root)
    config = root / "operating_states.yaml"
    manifest_path = root / "operating_state_manifest.yaml"
    receipt = root / "receipt.json"
    config.write_text(yaml.safe_dump(
        document(source=(15, 15), evidence=evidence), sort_keys=False))
    manifest_path.write_text(yaml.safe_dump(manifest(), sort_keys=False))
    result = must_fail(run([
        sys.executable, CHECK, root, "--config", config,
        "--manifest", manifest_path, "--json", receipt,
    ]), "operating-state CLI mismatch", "E-STATE REJECTED")
    check(str(receipt.resolve()) in result.out,
          "CLI did not name the exact receipt it wrote")


@test("invented endpoint evidence cannot be promoted by E-STATE",
      kind="known_bad")
def t_endpoint_evidence_is_reopened():
    root = tmpdir("operating-state-evidence-vacuity-")
    config = root / "operating_states.yaml"
    manifest_path = root / "operating_state_manifest.yaml"
    receipt = root / "receipt.json"
    config.write_text(yaml.safe_dump(document(), sort_keys=False))
    manifest_path.write_text(yaml.safe_dump(manifest(), sort_keys=False))
    result = must_fail(run([
        sys.executable, CHECK, root, "--config", config,
        "--manifest", manifest_path, "--json", receipt,
    ]), "E-STATE with syntactically valid but nonexistent endpoint evidence",
       "E-STATE INCOMPLETE")
    check("E-STATE-EVIDENCE" in result.out,
          "missing evidence was not diagnosed at its owning boundary")


@test("existing citation bytes do not prove authored numeric endpoints",
      kind="vacuity", gate="operating_state_check.py")
def t_vacuity_unextracted_numeric_endpoints():
    root = tmpdir("operating-state-unextracted-values-")
    evidence = evidence_tree(root)
    config = root / "operating_states.yaml"
    manifest_path = root / "operating_state_manifest.yaml"
    # The cited files contain only an MPN and a generic validation marker; no
    # 19..21 V or 16.07..30 V value exists in either one.
    config.write_text(yaml.safe_dump(document(evidence=evidence), sort_keys=False))
    manifest_path.write_text(yaml.safe_dump(manifest(), sort_keys=False))
    receipt = grade_file(config, manifest_path, evidence_root=root)
    eq(receipt["verdict"], "ACCEPTED",
       "the declared citation-only blind spot stopped reproducing")
    eq(receipt["authority"], "SHADOW", "vacuous result escaped shadow")
    eq(receipt["evidence"]["authority"], "UNVERIFIED",
       "unextracted endpoint numbers gained evidence authority")


@test("changed cited endpoint bytes invalidate an accepted receipt",
      kind="known_bad")
def t_endpoint_evidence_staleness():
    root = tmpdir("operating-state-evidence-stale-")
    evidence = evidence_tree(root)
    config = root / "operating_states.yaml"
    manifest_path = root / "operating_state_manifest.yaml"
    config.write_text(yaml.safe_dump(document(evidence=evidence), sort_keys=False))
    manifest_path.write_text(yaml.safe_dump(manifest(), sort_keys=False))
    receipt = grade_file(config, manifest_path, evidence_root=root)
    eq(receipt["verdict"], "ACCEPTED")
    (root / "02_parts/U_PD/part.yaml").write_text("mpn: CHANGED\n")
    valid, failures = verify_receipt(receipt)
    check(not valid, "changed endpoint authority retained promotion validity")
    check(any("evidence:02_parts/U_PD/part.yaml" in row for row in failures),
          "changed endpoint evidence was not named")


if __name__ == "__main__":
    sys.exit(main())
