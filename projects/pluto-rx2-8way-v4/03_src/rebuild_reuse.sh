#!/usr/bin/env bash
# TEMPLATE rebuild_reuse.sh — the DETERMINISTIC promoted-chain rebuild driver
# (skill-owned; copy into a board's 03_src/ beside rebuild_all.sh — it is
# config-driven and needs NO per-board edits: the board name comes from
# 03_src/floorplan.yaml `project.name`, exactly like the generic backend).
#
# WHEN TO USE WHICH DRIVER
#   rebuild_all.sh    — the FULL pipeline from tscircuit source: tsci build ->
#                       converter .kicad_sch -> ERC/parity -> board -> route ->
#                       gates. Run it when the SCHEMATIC changed, or for the
#                       from-scratch reproducibility proof (canon M3).
#   rebuild_reuse.sh  — THIS driver: the per-iteration / verification rebuild.
#                       Skips the tsci stage entirely and regenerates the board
#                       from committed 03_src config + the PINNED, committed
#                       03_tscircuit/kicad/<board>.kicad_sch, importing the
#                       PROMOTED KRT chain. Every step is deterministic, so it
#                       reproduces the board's routing gate exactly.
#
# WHY THE SPLIT (2026-07-23, measured on crow-rv2 + usb-hub): `tsci build` is
# NON-DETERMINISTIC — rerunning it churns the generated .kicad_sch by ~2900
# lines of UUID/ordering noise (connectivity stays stable per count_parity,
# but kicad-cli's --schematic-parity then reports phantom field diffs against
# the sealed board). The COMMITTED .kicad_sch is therefore the PINNED canonical
# schematic: this driver never regenerates it, it consumes it. This pattern was
# independently rewritten by THREE boards (usb-hub-3s-v2/-v3 rebuild_fast.sh,
# crow-rv2 rebuild_reuse.sh) — an M8 two-strike violation this template retires.
#
# VALID ONLY while KRT-routed pins do NOT move. If a signal-carrying pad's
# placement changes, re-route KRT on a track-free board, re-promote the chain
# into 03_src/route/, and commit it (there is deliberately no autorouter here).
#
# Order is BINDING (03_src/contracts.md): rules BEFORE import (canon R1),
# generate_rules LAST again after stitch (pcbnew saves clobber netclasses),
# then the full gate: kicad-cli pcb drc --severity-all --refill-zones
# --schematic-parity = 0/0/0. The pinned .kicad_sch is copied beside the board
# first — without it --schematic-parity SILENTLY SKIPS (crow-rv2 finding).
set -euo pipefail
cd "$(dirname "$0")/.."                       # -> project root (03_src/..)

PY=/usr/bin/python3
# resolve the shared skill scripts (repo-relative first, ~/.claude fallback)
S="$(cd "$(git rev-parse --show-toplevel 2>/dev/null || echo ../../..)" && pwd)/skills/kicad-pcb/scripts"
[ -f "$S/generate_board_generic.py" ] || S="$HOME/.claude/skills/kicad-pcb/scripts"
export PATH="$HOME/.bun/bin:$PATH"

# P-MOD is source-only and cheap; deterministic reuse must not bypass it.
$PY "$S/module_first_check.py" . \
    || { echo "GATE FAILED P-MOD: module-first architecture contract"; exit 1; }
$PY "$S/rf_contract_check.py" . --require-applicability \
    || { echo "GATE FAILED RF-CONTRACT: incomplete RF requirements"; exit 1; }

# derive the board name from the SAME config the generic backend reads
BOARD=$($PY - <<'PYEOF'
import re
txt = open("03_src/floorplan.yaml").read()
m = re.search(r'^\s*name:\s*["\']?([A-Za-z0-9_.-]+)', txt.split("project:", 1)[1], re.M)
print(m.group(1))
PYEOF
)
[ -n "$BOARD" ] || { echo "rebuild_reuse: no project.name in 03_src/floorplan.yaml"; exit 2; }
SCH="03_tscircuit/kicad/$BOARD.kicad_sch"      # the PINNED canonical schematic
[ -f "$SCH" ] || { echo "rebuild_reuse: pinned $SCH missing — run rebuild_all.sh once and COMMIT it"; exit 2; }

rm -f 06_build/route/FINAL 2>/dev/null || true   # force `import` to replay the promoted chain

# [1] netlist from the PINNED committed schematic (deterministic — never tsci)
mkdir -p 06_build/netlists
kicad-cli sch export netlist --format kicadsexpr \
    -o "06_build/netlists/$BOARD.net" "$SCH"

# [2] board (placement + zones) from committed floorplan.yaml  [SHARED]
$PY "$S/generate_board_generic.py" 03_src/floorplan.yaml -o "04_kicad/$BOARD.kicad_pcb"
$PY "$S/pad_separation.py" "04_kicad/$BOARD.kicad_pcb" --project . \
    || { echo "GATE FAILED P-PADSEP: separate footprint pads and route explicitly"; exit 1; }

# [3] placement/pad invariants, if the board defines them  [per-board gate]
if [ -f 03_src/audit_board.py ]; then $PY 03_src/audit_board.py; fi

# [4] netclasses + .kicad_dru BEFORE import (canon R1: rules ride into the route)  [SHARED]
#     (generate_rules_generic itself purges kicad-cli's stray
#     <board>.kicad_pcb.kicad_pro/.prl droppings — do NOT re-add a bespoke rmstray)
$PY "$S/generate_rules_generic.py" .

# [4a] P-LAND before promoted-route import: fail on a package/placement launch
# wall while the board is still track-free, not after replaying/stitching it.
$PY "$S/escape_check.py" --board "04_kicad/$BOARD.kicad_pcb" \
    || { echo "GATE FAILED [4a] P-LAND: a placed pad cannot launch its declared width"; exit 1; }

# [5] import the PROMOTED KRT chain once into the track-free board  [SHARED]
$PY "$S/route_and_stitch_generic.py" import 03_src/route.yaml
# [5b] taps — no-op unless route.yaml configures `taps:`  [SHARED]
$PY "$S/route_and_stitch_generic.py" taps   03_src/route.yaml

# [6] stitch: pours + stitch/thermal vias + island heal + gate  [SHARED]
$PY "$S/route_and_stitch_generic.py" stitch 03_src/route.yaml

# Re-run the project geometry audit on the routed board. The pre-import pass
# proves the physical rule area exists; this pass gives the assertion teeth by
# proving real promoted copper avoids it and the ANT4 control crossing is on
# In2.Cu while In1.Cu remains an uninterrupted GND reference.
if [ -f 03_src/audit_board.py ]; then $PY 03_src/audit_board.py --routed; fi

# [7] generate_rules LAST — pcbnew saves in the chain clobber netclasses  [SHARED]
$PY "$S/generate_rules_generic.py" .

# [8] routing gate: full-severity DRC, zones refilled, schematic parity.
#     The pinned sch must sit beside the board or --schematic-parity silently skips.
mkdir -p 06_build/route
cp "$SCH" "04_kicad/$BOARD.kicad_sch"
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity \
    --format json -o 06_build/route/gate.json "04_kicad/$BOARD.kicad_pcb"
$PY - <<'PYEOF'
import json
g = json.load(open("06_build/route/gate.json"))
v = len(g["violations"]); u = len(g["unconnected_items"])
p = len(g.get("schematic_parity", []) or [])
print(f"ROUTING GATE: {v} violations / {u} unconnected / {p} parity")
raise SystemExit(0 if v == u == p == 0 else 1)
PYEOF

# [8a] Reproduce the masked/via-fenced CPWG solve and make the realized-length
# audit consume the same declared phase tuple.
KRT_PY="$HOME/gits/KiCadRoutingTools/.venv/bin/python"
[ -x "$KRT_PY" ] || { echo "GATE FAILED [8a] RF-SOLVE: missing $KRT_PY"; exit 1; }
mkdir -p 06_build/verify
$PY "$S/fence_pitch.py" "04_kicad/$BOARD.kicad_pcb" 2.5 1.1910 \
    | tee 06_build/verify/fence_pitch.txt
"$KRT_PY" 03_src/cpwg_field_solver.py --output 06_build/verify/cpwg_field.json
$PY "$S/copper_length_audit.py" . --strict \
    || { echo "GATE FAILED [8a] R-LEN: realized phase geometry/constants"; exit 1; }
echo "rebuild_reuse: routing gate GREEN (0/0/0) from committed source"
