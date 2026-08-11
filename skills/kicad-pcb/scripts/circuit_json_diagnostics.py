#!/usr/bin/env python3
"""Fail when tscircuit emits error diagnostics despite returning success.

``tsci build`` can exit zero and write a complete-looking circuit.json while
also reporting geometry/component errors inside that artifact.  Downstream
freshness, parity, ERC, and BOM gates then grade the artifact successfully
because none of them owns tscircuit's own diagnostic vocabulary.  This small
boundary checker closes that gap without promoting advisory warnings to hard
failures.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


def diagnostic_kind(item: object) -> str:
    if not isinstance(item, dict):
        return ""
    value = item.get("type", "")
    return value if isinstance(value, str) else ""


def grade(path: Path) -> tuple[list[dict], Counter[str], int]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read circuit JSON {path}: {exc}") from exc
    if not isinstance(doc, list):
        raise ValueError(f"circuit JSON root must be a list, got {type(doc).__name__}")

    errors: list[dict] = []
    warnings: Counter[str] = Counter()
    for item in doc:
        kind = diagnostic_kind(item)
        folded = kind.casefold()
        if folded == "error" or folded.endswith("_error"):
            errors.append(item)
        elif folded == "warning" or folded.endswith("_warning"):
            warnings[kind] += 1
    return errors, warnings, len(doc)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Fail on error diagnostics embedded in tscircuit circuit.json")
    ap.add_argument("circuit_json")
    ap.add_argument("--show", type=int, default=12,
                    help="maximum individual error messages to print")
    args = ap.parse_args(argv)
    path = Path(args.circuit_json)

    try:
        errors, warnings, scanned = grade(path)
    except ValueError as exc:
        print(f"TSX-DIAG LOAD ERROR: {exc}")
        return 2

    warning_total = sum(warnings.values())
    diagnostic_total = len(errors) + warning_total
    coverage = (f"coverage: {diagnostic_total} diagnostic record(s) graded / "
                f"{scanned} circuit JSON element(s) scanned")
    if errors:
        print(f"TSX-DIAG FAIL: {len(errors)} embedded error diagnostic(s); "
              f"{warning_total} advisory warning(s)")
        print(f"  {coverage}")
        for item in errors[:max(0, args.show)]:
            kind = diagnostic_kind(item) or "error"
            message = str(item.get("message", "(no message)")).replace("\n", " ")
            print(f"  {kind}: {message}")
        if len(errors) > max(0, args.show):
            print(f"  ... {len(errors) - max(0, args.show)} more error diagnostic(s)")
        return 1

    summary = ", ".join(f"{kind}={count}" for kind, count in sorted(warnings.items()))
    suffix = f" ({summary})" if summary else ""
    print(f"TSX-DIAG PASS: 0 embedded errors; {warning_total} advisory warning(s){suffix}")
    print(f"  {coverage}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
