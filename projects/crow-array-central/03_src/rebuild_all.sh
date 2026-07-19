#!/bin/bash
# Full regenerate -> import -> stitch -> rules -> gate chain.
# set -euo pipefail: ANY stage failure stops the chain.
# KRT re-route (03_src/route_prep.py + 03_src/route_waves.sh) is only needed
# when the netlist/placement changes; the chain imports the PROMOTED
# 03_src/route/final.kicad_pcb (canon M3).
set -euo pipefail
cd "$(dirname "$0")/.."
PY=/usr/bin/python3
SKILLS="$(cd "$(dirname "$0")/../../.." 2>/dev/null && pwd)/skills/kicad-pcb/scripts"
[ -d "$SKILLS" ] || SKILLS="$HOME/.claude/skills/kicad-pcb/scripts"
mkdir -p 06_build/netlists 06_build/drc 06_build/route
python3 03_src/make_lib.py | tail -1
python3 03_src/generate_schematic.py | tail -1
kicad-cli sch export netlist -o 06_build/netlists/crow_array_central.net 04_kicad/crow_array_central.kicad_sch >/dev/null
# ERC gate: 0 violations at severity-all
kicad-cli sch erc --severity-all --format json -o 06_build/drc/erc.json 04_kicad/crow_array_central.kicad_sch >/dev/null
python3 - <<'PYEOF'
import json, sys
d = json.load(open('06_build/drc/erc.json'))
v = [x for s in d['sheets'] for x in s['violations']]
print(f'ERC: {len(v)} violations')
sys.exit(1 if v else 0)
PYEOF
# Placement verification (the promoted route below carries the SAME
# placement; this regen + audit guards the generator, then is overwritten).
$PY 03_src/generate_board.py 2>/dev/null | tail -1
$PY 03_src/audit_board.py 2>/dev/null | tail -1
# The PROMOTED route artifact (canon M3) is a COMPLETE board (placement +
# tracks). Use it DIRECTLY as 04_kicad — import_krt fragmented fanout-stub /
# power-tap connectivity, so the routed board is copied, not re-imported.
# NOTE: 03_src/route_fixups.py has already been applied ONCE to the promoted
# 03_src/route/final.kicad_pcb (U6/J9 vendored-FPID identity, J9 edge-silk
# clamp, TDO escape dogbone out of pad 37); it is baked in + committed, NOT
# re-run here (it edits the source in place). See ADR-0007/0009.
cp 03_src/route/final.kicad_pcb 06_build/route/final.kicad_pcb
cp 06_build/route/final.kicad_pcb 04_kicad/crow_array_central.kicad_pcb
# rules BEFORE stitch: the stitcher's internal checks + fill honor the floors
python3 03_src/generate_rules.py >/dev/null
$PY 03_src/stitch_and_fill.py 2>/dev/null | tail -3
python3 03_src/generate_rules.py >/dev/null
# GND rescue: bond the boxed GND SMD pads the pour/grid can't reach (PCM1865 /
# USB-C escape), then clearance nudge on sub-0.09 power-vs-signal tracks.
$PY 03_src/gnd_rescue.py 2>/dev/null | tail -2
# close_gnd: DRC-guarded close of the boxed GND pads gnd_rescue can't reach
# (U3.7 via an I2C_SCL In3 reroute; U1.42 tip via; R34.2 stub). Each edit is
# kept only if unconnected strictly drops and no hard error is added.
$PY 03_src/close_gnd.py 2>/dev/null | tail -6
$PY 03_src/clearance_nudge.py 2>/dev/null | tail -20
# neck_approaches (D25): DRC-guarded necking of power segments at the
# fine-pitch / parallel-escape approaches clearance_nudge cannot shift
# (clusters A/B/C: full-width power + 0.09mm physically does not fit).
# Each neck gets a scoped 'pwr_neck' rule area; generate_rules.py's
# width_*_neck DRU rules carry the exemption (ampacity math in the DRU).
$PY 03_src/neck_approaches.py 2>/dev/null | tail -20
# trim_dangling: DRC-guarded removal of KRT loose-copper spurs, SUBPROCESS-
# PER-EDIT (repeated LoadBoard in one process corrupts SWIG state) with a
# clip-to-pad/via fallback for load-bearing through-pin overshoots
# (connectivity guard reverts any edit that would orphan a pad).
$PY 03_src/trim_dangling.py 2>/dev/null | tail -20
# add_silk_fn (D29): functional silkscreen labels for J/F/TP refs (canon
# P5 / policy_audit P-SILK-FN) — collision-aware, DRC-guarded, idempotent.
$PY 03_src/add_silk_fn.py 2>/dev/null | tail -3
# audit again post-route (I8 AIN length needs tracks)
$PY 03_src/audit_board.py 2>/dev/null | tail -2
# rules LAST: pcbnew saves clobber .kicad_pro netclasses
python3 03_src/generate_rules.py
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity --format json \
    -o 06_build/drc/gate.json 04_kicad/crow_array_central.kicad_pcb >/dev/null
python3 - <<'PYEOF'
import json
from collections import Counter
d = json.load(open('06_build/drc/gate.json'))
print('violations:', len(d['violations']), dict(Counter(v['type'] for v in d['violations'])))
# ADR-0010: the 2 `Zone [GND] <-> Zone [GND]` unconnected items are WAIVED
# (headless fill-engine micro-slivers, zero electrical impact; evidence in
# 01_docs/decisions/0010). ONLY that exact shape is waivable, max 2; any
# pad/track/via unconnected item still fails the gate.
unc = d['unconnected_items']
waived = [u for u in unc
          if all(it['description'].startswith('Zone [GND]') for it in u['items'])]
real = [u for u in unc if u not in waived]
print(f'unconnected: {len(unc)} ({len(waived)} ADR-0010-waived zone slivers, {len(real)} real)')
print('parity:', len(d.get('schematic_parity', [])))
import sys
sys.exit(1 if (d['violations'] or real or len(waived) > 2
               or d.get('schematic_parity')) else 0)
PYEOF
