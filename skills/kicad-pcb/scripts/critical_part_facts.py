#!/usr/bin/env python3
"""P-CRITFACT — grade selected catastrophic part/footprint facts on a board.

Usage: critical_part_facts.py PROJECT [--board PATH] [--facts PATH]

G-INPUT: the verdict names both the board and accepted-facts manifest graded.
G-COVER: it reports ``N/M facts compared``; an empty manifest is a hard fail.
G-RED: tests/t1_pipeline_reliability.py mutates a required pad and proves this
checker rejects the exact wrong-footprint class.

This is deliberately selective.  It does not pretend to machine-read every
datasheet.  The manifest records only high-consequence accepted facts whose
wrong value can remain internally self-consistent across symbol, footprint and
PCB: order-code identity, complete numbered pad set, mounting-hole/drill count,
and a few safety-critical pin-to-net assignments.
"""
from __future__ import annotations

import argparse
import fnmatch
from pathlib import Path

import pcbnew
import yaml


ATTRS = {
    "smd": pcbnew.PAD_ATTRIB_SMD,
    "pth": pcbnew.PAD_ATTRIB_PTH,
    "npth": pcbnew.PAD_ATTRIB_NPTH,
}


def close(actual: float, expected: float, tolerance: float) -> bool:
    return abs(actual - expected) <= tolerance


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("project")
    ap.add_argument("--board")
    ap.add_argument("--facts", default="03_src/rules/critical_parts.yaml")
    args = ap.parse_args(argv)
    project = Path(args.project).resolve()
    facts_path = Path(args.facts)
    facts_path = facts_path if facts_path.is_absolute() else project / facts_path
    try:
        doc = yaml.safe_load(facts_path.read_text(encoding="utf-8-sig")) or {}
        if doc.get("schema") != 1 or not isinstance(doc.get("parts"), list):
            raise ValueError("schema must be 1 and parts must be a list")
        board_path = Path(args.board or doc.get("board", ""))
        board_path = board_path if board_path.is_absolute() else project / board_path
        board = pcbnew.LoadBoard(str(board_path))
        if board is None:
            raise ValueError(f"could not load board {board_path}")
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"P-CRITFACT FAIL: 0/1 facts compared; board={args.board}; "
              f"facts={facts_path}; {exc}")
        return 2

    footprints = {f.GetReference(): f for f in board.GetFootprints()}
    failures: list[str] = []
    compared = total = 0

    def grade(label: str, condition: bool, detail: str) -> None:
        nonlocal compared, total
        total += 1
        compared += 1
        if not condition:
            failures.append(f"{label}: {detail}")

    for entry in doc["parts"]:
        source = str(entry.get("source", "")).strip()
        dossier = project / str(entry.get("dossier", ""))
        grade(str(entry.get("id", "part")) + " source", len(source) >= 8,
              "accepted fact has no substantive source citation")
        grade(str(entry.get("id", "part")) + " dossier", dossier.is_file(),
              f"dossier missing: {dossier}")
        refs = entry.get("refs") or []
        if entry.get("ref"):
            refs = [entry["ref"]]
        if entry.get("ref_glob"):
            refs = sorted(r for r in footprints
                          if fnmatch.fnmatch(r, str(entry["ref_glob"])))
        if not refs:
            total += 1
            failures.append(f"{entry.get('id', 'part')}: no references selected")
            continue
        for ref in refs:
            fp = footprints.get(str(ref))
            total += 1
            if fp is None:
                failures.append(f"{entry.get('id')} {ref}: footprint missing")
                continue
            compared += 1
            label = f"{entry.get('id')} {ref}"
            if "value" in entry:
                grade(label + " value", fp.GetValue() == str(entry["value"]),
                      f"value={fp.GetValue()!r}, expected {entry['value']!r}")
            pads = list(fp.Pads())
            numbered = sorted((p.GetNumber() for p in pads if p.GetNumber()),
                              key=str)
            if "numbered_pads" in entry:
                expected = sorted(map(str, entry["numbered_pads"]), key=str)
                grade(label + " numbered_pads", numbered == expected,
                      f"pads={numbered}, expected={expected}")
            if "unnumbered_smd" in entry:
                actual = sum(not p.GetNumber() and
                             p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD
                             for p in pads)
                grade(label + " unnumbered_smd",
                      actual == int(entry["unnumbered_smd"]),
                      f"count={actual}, expected={entry['unnumbered_smd']}")
            for attr, count in (entry.get("pad_counts") or {}).items():
                if attr not in ATTRS:
                    raise ValueError(f"{label}: unknown pad attribute {attr}")
                actual = sum(p.GetAttribute() == ATTRS[attr] for p in pads)
                grade(label + f" {attr}_count", actual == int(count),
                      f"count={actual}, expected={count}")
            by_number: dict[str, list] = {}
            for pad in pads:
                by_number.setdefault(pad.GetNumber(), []).append(pad)
            for number, expected_net in (entry.get("pad_nets") or {}).items():
                hits = by_number.get(str(number), [])
                actual = sorted({p.GetNetname() for p in hits})
                grade(label + f" pad_{number}_net",
                      bool(hits) and actual == [str(expected_net)],
                      f"nets={actual}, expected={[str(expected_net)]}")
            for spec in entry.get("drills", []) or []:
                attr = str(spec["attribute"])
                selected = [p for p in pads if p.GetAttribute() == ATTRS[attr]]
                if "count" in spec:
                    grade(label + f" {attr}_drill_count",
                          len(selected) == int(spec["count"]),
                          f"count={len(selected)}, expected={spec['count']}")
                diameter = float(spec["diameter_mm"])
                tol = float(spec.get("tolerance_mm", 0.01))
                actual = [(p.GetDrillSize().x / 1e6,
                           p.GetDrillSize().y / 1e6) for p in selected]
                grade(label + f" {attr}_drill_size",
                      bool(selected) and all(close(x, diameter, tol)
                                             for pair in actual for x in pair),
                      f"drills={actual}, expected={diameter}+-{tol} mm")
            for number, size in (entry.get("pad_sizes") or {}).items():
                selected = by_number.get(str(number), [])
                want = [float(size[0]), float(size[1])]
                tol = float(entry.get("size_tolerance_mm", 0.01))
                actual = [[p.GetSize().x / 1e6, p.GetSize().y / 1e6]
                          for p in selected]
                grade(label + f" pad_{number}_size",
                      bool(selected) and all(
                          (close(pair[0], want[0], tol) and close(pair[1], want[1], tol))
                          or (close(pair[0], want[1], tol) and close(pair[1], want[0], tol))
                          for pair in actual),
                      f"sizes={actual}, expected={want}+-{tol} mm")

    if total == 0:
        print(f"P-CRITFACT FAIL: 0/0 facts compared; board={board_path}; "
              f"facts={facts_path}; empty denominator")
        return 1
    if failures:
        for failure in failures:
            print(f"  FAIL {failure}")
        print(f"P-CRITFACT FAIL: {compared}/{total} facts compared; "
              f"board={board_path}; facts={facts_path}; {len(failures)} mismatch(es)")
        return 1
    print(f"P-CRITFACT PASS: {compared}/{total} facts compared; "
          f"board={board_path}; facts={facts_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
