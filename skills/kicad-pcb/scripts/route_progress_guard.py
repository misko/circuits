#!/usr/bin/env python3
"""Bound repeated routing attempts by semantic progress, not file churn.

The guard consumes one small JSON observation per attempt.  It deliberately
ignores output hashes and raw X/Y coordinates: stochastic geometry that leaves
the same nets, finding classes, owners, and frontier unresolved is not novel.

    route_progress_guard.py observe OBSERVATION.json STATE.json

Exit 0 means another diagnostic attempt is allowed (or routing is complete).
Exit 1 means the caller must stop and backtrack.  The updated state and a
machine-readable decision are always written atomically.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


COORDINATE_KEYS = {
    "x", "y", "x_mm", "y_mm", "position", "coordinate", "coordinates",
    "start", "end", "bbox", "point",
}
STOP_DECISIONS = {"STAGNATED", "BUDGET_EXHAUSTED"}


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def _strings(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("expected a list")
    return sorted({str(item).strip() for item in value if str(item).strip()})


def _semantic(value: Any) -> Any:
    """Remove stochastic coordinates while retaining semantic ownership."""
    if isinstance(value, dict):
        return {
            str(key): _semantic(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
            if str(key).lower() not in COORDINATE_KEYS
        }
    if isinstance(value, list):
        rows = [_semantic(item) for item in value]
        return sorted(rows, key=lambda item: json.dumps(item, sort_keys=True))
    if isinstance(value, str):
        # Descriptions are allowed, but numeric coordinate drift must not buy
        # another attempt.  Named nets/owners remain untouched.
        return re.sub(r"(?<![A-Za-z_])[-+]?\d+(?:\.\d+)?", "#", value.strip())
    return value


def normalize_observation(observation: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(observation, dict):
        raise ValueError("observation must be a JSON object")
    subject = str(observation.get("subject") or "").strip()
    if not subject:
        raise ValueError("observation.subject is required")
    unresolved = _strings(observation.get("unresolved", []))
    findings = observation.get("hard_findings", [])
    frontier = observation.get("frontier", [])
    if not isinstance(findings, list) or not isinstance(frontier, list):
        raise ValueError("hard_findings and frontier must be lists")
    return {
        "subject": subject,
        "unresolved": unresolved,
        "hard_findings": _semantic(findings),
        "frontier": _semantic(frontier),
    }


def signature(normalized: dict[str, Any]) -> str:
    semantic = {key: normalized[key]
                for key in ("unresolved", "hard_findings", "frontier")}
    payload = json.dumps(semantic, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def observe(observation: dict[str, Any], previous: dict[str, Any] | None = None,
            *, plateau_attempts: int = 2, max_attempts: int = 5,
            max_novel_signatures: int = 3,
            max_operation_amplification: float = 8.0) -> tuple[dict[str, Any], dict[str, Any]]:
    if plateau_attempts < 2:
        raise ValueError("plateau_attempts must be at least 2")
    if max_attempts < plateau_attempts:
        raise ValueError("max_attempts must be >= plateau_attempts")
    if max_novel_signatures < 1 or max_operation_amplification <= 1:
        raise ValueError("novel-signature and amplification limits are invalid")

    current = normalize_observation(observation)
    sig = signature(current)
    old = previous if isinstance(previous, dict) else {}
    if old.get("schema") != 1 or old.get("subject") != current["subject"]:
        old = {}

    attempts = int(old.get("attempts", 0)) + 1
    seen = list(old.get("seen_signatures") or [])
    is_novel = sig not in seen
    if is_novel:
        seen.append(sig)
    same_count = (int(old.get("same_signature_count", 0)) + 1
                  if old.get("last_signature") == sig else 1)
    unresolved_count = len(current["unresolved"])
    prior_best = old.get("best_unresolved_count")
    improved = prior_best is None or unresolved_count < int(prior_best)
    best = unresolved_count if prior_best is None else min(
        unresolved_count, int(prior_best))

    operations = observation.get("operations") or {}
    if not isinstance(operations, dict):
        raise ValueError("operations must be a mapping when present")
    requested = int(operations.get("requested", 0) or 0)
    expanded = max(int(operations.get("queued", 0) or 0),
                   int(operations.get("ripups", 0) or 0))
    amplified = bool(requested and expanded >=
                     requested * max_operation_amplification and not improved)

    complete = not current["unresolved"] and not current["hard_findings"]
    if complete:
        decision, reason = "COMPLETE", "no unresolved work or hard findings"
    elif amplified:
        decision = "STAGNATED"
        reason = (f"operation amplification {expanded}/{requested} reached "
                  f"{max_operation_amplification:g}x without reducing opens")
    elif same_count >= plateau_attempts:
        decision = "STAGNATED"
        reason = (f"same semantic frontier repeated {same_count} times; "
                  "coordinate/hash variation is not progress")
    elif attempts >= max_attempts:
        decision, reason = "BUDGET_EXHAUSTED", f"attempt budget {max_attempts} reached"
    elif len(seen) > max_novel_signatures:
        decision = "BUDGET_EXHAUSTED"
        reason = f"novel diagnostic budget {max_novel_signatures} exceeded"
    elif improved or is_novel:
        decision, reason = "NOVEL_PROGRESS", (
            "unresolved denominator reduced" if improved and attempts > 1
            else "new semantic finding/frontier signature")
    else:
        decision, reason = "CONTINUE_DIAGNOSTIC", "within bounded diagnostic budget"

    state = {
        "schema": 1,
        "subject": current["subject"],
        "attempts": attempts,
        "best_unresolved_count": best,
        "last_signature": sig,
        "same_signature_count": same_count,
        "seen_signatures": seen,
        "last_observation": current,
        "last_decision": decision,
    }
    result = {
        "schema": 1,
        "subject": current["subject"],
        "decision": decision,
        "reason": reason,
        "attempt": attempts,
        "signature": sig,
        "unresolved_count": unresolved_count,
        "novel_signatures": len(seen),
        "stop": decision in STOP_DECISIONS,
    }
    return state, result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    cmd = sub.add_parser("observe")
    cmd.add_argument("observation", type=Path)
    cmd.add_argument("state", type=Path)
    cmd.add_argument("--result", type=Path)
    cmd.add_argument("--plateau-attempts", type=int, default=2)
    cmd.add_argument("--max-attempts", type=int, default=5)
    cmd.add_argument("--max-novel-signatures", type=int, default=3)
    cmd.add_argument("--max-operation-amplification", type=float, default=8.0)
    args = parser.parse_args(argv)

    try:
        observation = json.loads(args.observation.read_text(encoding="utf-8-sig"))
        prior = (json.loads(args.state.read_text(encoding="utf-8-sig"))
                 if args.state.is_file() else None)
        state, result = observe(
            observation, prior, plateau_attempts=args.plateau_attempts,
            max_attempts=args.max_attempts,
            max_novel_signatures=args.max_novel_signatures,
            max_operation_amplification=args.max_operation_amplification)
        _atomic_json(args.state, state)
        if args.result:
            _atomic_json(args.result, result)
    except Exception as exc:  # fail closed at the command boundary
        print(f"ROUTE-PROGRESS INCOMPLETE: {exc}")
        return 2

    print(f"ROUTE-PROGRESS {result['decision']}: {result['reason']} "
          f"(attempt {result['attempt']}, opens {result['unresolved_count']})")
    print("coverage: 3/3 semantic dimensions graded "
          "(unresolved, hard findings, frontier)")
    return 1 if result["stop"] else 0


if __name__ == "__main__":
    sys.exit(main())
