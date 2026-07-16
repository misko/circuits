#!/usr/bin/env python3
"""Parse a kicad-cli DRC report; print the canonical gate lines and exit
nonzero unless everything is zero. The report format is the [type]-tagged
text report from `kicad-cli pcb drc --severity-all --refill-zones
--schematic-parity`."""
import collections
import re
import sys
from pathlib import Path

rpt = Path(sys.argv[1]).read_text()

by_type = collections.Counter(re.findall(r"^\[(\w+)\]", rpt, re.M))
m_v = re.search(r"Found (\d+) DRC violations", rpt)
m_u = re.search(r"Found (\d+) unconnected (?:pads|items)", rpt)
m_p = re.search(r"Found (\d+) Footprint errors", rpt)
if not (m_v and m_u):
    raise SystemExit("ERROR: DRC report parse yielded nothing — format drift?")
v, u = int(m_v.group(1)), int(m_u.group(1))
p = int(m_p.group(1)) if m_p else 0

detail = dict(by_type) if (v or u or p) else {}
if p:
    print(f"parity: {p}")
print(f"violations: {v} {detail}")
print(f"unconnected: {u}")
sys.exit(0 if (v == 0 and u == 0 and p == 0) else 1)
