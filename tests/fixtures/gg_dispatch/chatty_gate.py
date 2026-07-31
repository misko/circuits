#!/usr/bin/env python3
"""CANARY GATE — DELIBERATELY NOISY, to drive the tracer past its event cap.

    usage: chatty_gate.py PROJECT_DIR

It grades both boards correctly (so any finding against it is false), and it
re-opens each board's `nets.yaml` 200 times while doing so. That is the ONLY
thing unusual about it, and it exists for one reason: `GRADELIB_MAX_EVENTS`
applies to EVERY traced process, so a fixture that truncates the BATTERY must
out-produce the CANARY, and the canary gates record 3-4 events each (MEASURED
2026-07-31). At a cap of 100 this gate truncates and the canary does not, which
is the separation `t_kb_truncated_trace_is_exit_5` needs.

400 opens is not a caricature of a real gate. `policy_audit.py` records 138
distinct paths over 8 processes on smc0985-cooksense and opens many of them
repeatedly; the shipped cap is 200000, and this fixture reaches its own cap by
being run against a lowered one, not by being unrealistic.
"""
import sys
from pathlib import Path

proj = Path(sys.argv[1])
boards = sorted(d for d in (proj / "03_src").iterdir()
                if (d / "rules" / "nets.yaml").is_file())
for b in boards:
    p = b / "rules" / "nets.yaml"
    n = 0
    for _ in range(200):
        n = len([ln for ln in p.read_text().splitlines() if "name:" in ln])
    print(f"WORKER: {n}/{n} net(s) graded against {p}")
print(f"CANARY-CHATTY PASS: {len(boards)}/{len(boards)} board(s) graded "
      f"under {proj}, re-read 200x each")
sys.exit(0)
