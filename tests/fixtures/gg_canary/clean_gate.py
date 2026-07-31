#!/usr/bin/env python3
"""CANARY GATE — the CLEAN one. Must yield NOTHING.

The most important of the three. A gate-on-gates that flags a correct gate is a
tax, not a ratchet: it gets switched off inside a week, and then the two real
predicates go unwatched. `PREC_OWED_CEILING` is the repo's own record of that —
the ratchet broke on a CORRECT action and the test that pinned it went red for
being right.

It is also the NEGATIVE CONTROL for the whole canary: `shadow_gate.py` and
`resolve_gate.py` prove the analyser CAN fire; this one proves it does not fire
on everything. A canary made only of defective gates would be satisfied by an
analyser that returns a finding unconditionally.

This gate ENUMERATES both boards' rule files instead of selecting one (the
`waiver_provenance.waiver_files()` exemplar: enumerate, never select), reads
every key present in each, and prints a denominator that describes what it
actually read. Any GG-* finding here means the analyser is over-reaching and
the suite fails on it.
"""
import sys
from pathlib import Path

import yaml

proj = Path(sys.argv[1])
seen, graded = set(), 0
for p in sorted(proj.rglob("03_src/**/rules/power_tree.yaml")) + \
        sorted(proj.glob("03_src/rules/power_tree.yaml")):
    rp = p.resolve()
    if rp in seen:
        continue
    seen.add(rp)
    d = yaml.safe_load(p.read_text()) or {}
    for k in list(d):                      # every key present is READ
        v = d[k]
        if isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    for kk in list(item):
                        _ = item[kk]
    graded += 1
print(f"CANARY-CLEAN PASS: {graded}/{len(seen)} rules document(s) graded, "
      f"enumerated (never selected) under {proj}")
sys.exit(0)
