#!/usr/bin/env python3
"""P-DRC: grade exact refill DRC before human placement review and routing.

An unrouted board legitimately has ratsnest ``unconnected_items`` and may
carry preliminary ``isolated_copper`` zone islands, but it must not reach human
review with shorts, clearance errors, invalid library links, malformed holes,
or schematic-parity defects. This checker grades KiCad's JSON report after a
fresh ``--refill-zones --schematic-parity`` run and names both denominators.

The placement allowance is deliberately not configurable: exposing an
arbitrary violation-type allowlist would let a caller suppress the very short
or clearance class this boundary exists to catch. Final routed DRC still owns
whether every preliminary island becomes connected copper.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("report")
    args = ap.parse_args(argv)
    path = Path(args.report)
    if not path.is_file():
        print(f"P-DRC INVOCATION: missing JSON report {path}")
        return 2
    try:
        doc = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"P-DRC INVOCATION: unreadable JSON report {path}: {exc}")
        return 2
    required = ("violations", "unconnected_items", "schematic_parity")
    if not isinstance(doc, dict) or any(not isinstance(doc.get(k), list)
                                        for k in required):
        print("P-DRC UNGRADED: report must contain list-valued violations, "
              "unconnected_items and schematic_parity")
        return 3

    allowed_types = {"isolated_copper"}
    types = Counter(str(v.get("type", "<missing>"))
                    for v in doc["violations"] if isinstance(v, dict))
    blocking = [v for v in doc["violations"]
                if not isinstance(v, dict)
                or str(v.get("type", "<missing>")) not in allowed_types]
    parity = doc["schematic_parity"]

    print(f"input: report = {path.resolve()}")
    print(f"P-DRC coverage: {len(doc['violations'])}/"
          f"{len(doc['violations'])} violation(s) classified; "
          f"{len(doc['unconnected_items'])} unrouted connection(s) observed; "
          f"{len(parity)} parity finding(s)")
    print(f"P-DRC types: {dict(types) or 'NONE'}; "
          f"allowed={sorted(allowed_types)}")
    for row in blocking[:20]:
        if isinstance(row, dict):
            print(f"FAIL P-DRC [{row.get('type', '<missing>')}]: "
                  f"{row.get('description', '<no description>')}")
        else:
            print(f"FAIL P-DRC [malformed]: {row!r}")
    if len(blocking) > 20:
        print(f"FAIL P-DRC: ... and {len(blocking) - 20} more blocking rows")
    if parity:
        print(f"FAIL P-DRC: {len(parity)} schematic-parity finding(s)")
    if blocking or parity:
        print("P-DRC FAIL: placement has non-ratsnest defects before review")
        return 1
    print("P-DRC PASS: exact refilled placement has no non-allowed DRC or "
          "schematic-parity finding")
    return 0


if __name__ == "__main__":
    sys.exit(main())
