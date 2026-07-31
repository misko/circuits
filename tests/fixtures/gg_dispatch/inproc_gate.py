#!/usr/bin/env python3
"""CANARY GATE — the IN-PROCESS TWIN of `dispatch_gate.py`. Must yield NOTHING.

    usage: inproc_gate.py PROJECT_DIR

Semantically identical to `dispatch_gate.py`: same boards, same files, same
order, same verdict. The ONLY difference is that the reads happen in ONE
process instead of one per board.

It is the CONTROL half of the dispatcher measurement. Without it, a GG-SHADOW
finding against `dispatch_gate.py` could be blamed on the gate's read-set; with
it, the read-sets are provably the same and the only remaining variable is the
PROCESS TOPOLOGY.
"""
import sys
from pathlib import Path

proj = Path(sys.argv[1])
boards = sorted(d for d in (proj / "03_src").iterdir()
                if (d / "rules" / "nets.yaml").is_file())
for b in boards:
    p = b / "rules" / "nets.yaml"
    n = len([ln for ln in p.read_text().splitlines() if "name:" in ln])
    print(f"WORKER: {n}/{n} net(s) graded against {p}")
print(f"CANARY-INPROC PASS: {len(boards)}/{len(boards)} board(s) graded "
      f"under {proj}, all in ONE process")
sys.exit(0)
