#!/usr/bin/env python3
"""CANARY WORKER — graded ONE board, in its OWN PROCESS.

Not a gate: it takes a FILE, not a PROJECT_DIR, so `default_battery`'s
`PROJECT_ARG_RE` never picks it up. It exists only to be spawned by
`dispatch_gate.py`, which is the shape `03_src/rebuild_all.sh` already uses and
the shape task #31's per-board remedy will use.

It reads the ONE board it was handed and NOTHING else. That is CORRECT
behaviour: its sibling board is another worker's job. The whole point of the
fixture is that this correctness is invisible to a PER-TRACE predicate, because
this process's trace contains exactly one nets.yaml and the other board's
nets.yaml is, from inside this trace alone, "never opened".
"""
import sys
from pathlib import Path

p = Path(sys.argv[1])
n = len([ln for ln in p.read_text().splitlines() if "name:" in ln])
print(f"WORKER: {n}/{n} net(s) graded against {p}")
sys.exit(0)
