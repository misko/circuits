#!/usr/bin/env python3
"""CANARY GATE — the WRONG-PLACE RESOLUTION. Must yield GG-RESOLVE.

THE RED FIXTURE GG-RESOLVE SHIPPED WITHOUT. Round 1 emitted the check-ID, gave
it a canon row, and never once showed it failing — inside the layer whose whole
property is that a gate which cannot be made to fail is worthless. It was worse
than untested: it was STRUCTURALLY unable to fire, because it watched `open`
alone while every real gate guards with `Path.is_file()`. MEASURED 2026-07-31:
160 `.is_file()`, 88 `.is_dir()`, 82 `.exists()` and 12 `os.path.*` calls across
47 of 58 scripts, and NONE of them raises a Python audit event. GG-RESOLVE
measured exactly zero on the incident its own canon row cites.

This gate reproduces that incident in eleven lines. It SELECTS one path for
`policy_waivers.yaml` — the flat `03_src/rules/` address — on a subject that
keeps it at `03_src/boardB/rules/`, asks `is_file()`, opens nothing, and carries
on. Nothing in the process ever calls `open` on that name, so the finding exists
ONLY IF THE STAT FAMILY IS OBSERVED. `t_kb_the_stat_channel_off_blinds_resolve`
switches that channel off and measures this gate going silent.

IT IS DELIBERATELY CLEAN IN EVERY OTHER WAY, and each of those is load-bearing
against a different over-reach:

  * it READS both boards' `power_tree.yaml` — so GG-SHADOW must stay quiet
    (it ENUMERATED, it did not select);
  * it therefore opens something pre-existing under the subject root — so the
    read count is not zero and exit 3 must stay away.

If the analyser reports anything but GG-RESOLVE here, it is over-reaching.
"""
import sys
from pathlib import Path

proj = Path(sys.argv[1])

# THE DEFECT: one hardcoded address, on a project that does not use it.
waivers = proj / "03_src" / "rules" / "policy_waivers.yaml"
n_waivers = 0
if waivers.is_file():                       # a PROBE. No `open` is issued.
    n_waivers = len(waivers.read_text().splitlines())

# Everything else is the exemplar shape: enumerate, never select.
graded = 0
for p in sorted(proj.rglob("03_src/**/rules/power_tree.yaml")):
    p.read_text()
    graded += 1

print(f"CANARY-RESOLVE PASS: {graded}/{graded} rules document(s) graded, "
      f"{n_waivers} waiver line(s) from {waivers}")
sys.exit(0)
