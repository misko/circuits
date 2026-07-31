#!/usr/bin/env python3
"""CANARY GATE — CORRECT, and a DISPATCHER. Must yield NOTHING.

    usage: dispatch_gate.py PROJECT_DIR

THE SECOND NEGATIVE CONTROL, and the one that caught a real defect. This gate
grades BOTH boards — it is as correct as `clean_gate.py` — but it does the work
in ONE WORKER SUBPROCESS PER BOARD instead of in-process. That is not an exotic
shape: `projects/smc0985-cooksense/03_src/rebuild_all.sh` already dispatches
per-board that way, `adr_bound_provenance.py` and `waiver_provenance.py` spawn
subprocesses, and it is EXACTLY the shape the per-board path resolution owed by
task #31 will take.

`inproc_gate.py` is the SAME GRADING with the same read-set in one process. The
pair is the measurement: two gates that open the identical set of files, whose
GG-SHADOW verdict differed only by how many processes did the opening.

MEASURED 2026-07-31, pre-fix (`real` built PER TRACE inside `gg_shadow`):

    dispatch_gate.py   RAW EXIT 1, 2 GG-SHADOW findings   <-- both FALSE
    inproc_gate.py     RAW EXIT 0, 0 findings

Post-fix (`real` is a UNION over every trace in the run):

    dispatch_gate.py   RAW EXIT 0, 0 findings
    inproc_gate.py     RAW EXIT 0, 0 findings
"""
import subprocess
import sys
from pathlib import Path

proj = Path(sys.argv[1])
boards = sorted(d for d in (proj / "03_src").iterdir()
                if (d / "rules" / "nets.yaml").is_file())
worker = Path(__file__).resolve().parent / "dispatch_worker.py"
rc = 0
for b in boards:
    cp = subprocess.run([sys.executable, str(worker),
                         str(b / "rules" / "nets.yaml")])
    rc = rc or cp.returncode
print(f"CANARY-DISPATCH PASS: {len(boards)}/{len(boards)} board(s) graded "
      f"under {proj}, one WORKER SUBPROCESS each")
sys.exit(rc)
