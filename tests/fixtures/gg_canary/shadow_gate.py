#!/usr/bin/env python3
"""CANARY GATE — the FLAT-PATH defect, in miniature. Must yield GG-SHADOW.

THE RED FIXTURE FOR GG-SHADOW. Inventory defects 1/7/18 reduced to twelve
lines: a gate that hardcodes `03_src/rules/<name>` on a project that keeps a
second board's rules at `03_src/<board>/rules/<name>`. It reads one file, grades
it correctly, prints a denominator that is TRUE ABOUT WHAT IT READ, and reports
on THE PROJECT.

It is deliberately NOT broken in any other way — it resolves (the one path it
selects EXISTS, so GG-RESOLVE must stay quiet), it reads every key, and its
verdict is honest. If the analyser accuses it of anything except GG-SHADOW, the
analyser is over-reaching, and `t1_trace_audit.py` fails on it.
"""
import sys
from pathlib import Path

import yaml

proj = Path(sys.argv[1])
p = proj / "03_src" / "rules" / "power_tree.yaml"
d = yaml.safe_load(p.read_text()) or {}
rails = d.get("rails") or []
st = d.get("source_type")
lr = d.get("linear_rails") or []
for r in rails:
    _ = r.get("name"), r.get("vin_min"), r.get("vout_max")
for r in lr:
    _ = r.get("name"), r.get("iout_max_A")
print(f"CANARY-SHADOW PASS: {len(rails)}/{len(rails)} rail(s) graded "
      f"against {p} (source_type={st})")
sys.exit(0)
