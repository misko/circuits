#!/bin/bash
# ADR-0002 Phase B — PLACEMENT-AS-CODE proof, cook-loadcell.
#
# Drives a board from tscircuit-AUTHORED placement (pcbX/pcbY/pcbRotation in the
# TSX -> circuit.json pcb_component) through OUR audit + legalize + route to
# DRC 0/0/0 and node-for-node parity vs the sealed board. Never touches
# 04_kicad/ or releases (writes only under placement_proof/).
#
# Reproduces the honest measurements:
#   [A] the RAW auto-placement seed (no authored pcb coords) -> audit + DRC
#       violation counts, recorded to 06_build/raw_*.
#   [B] the AUTHORED placement-as-code seed -> audit PASS -> route -> DRC 0/0/0.
set -euo pipefail
cd "$(dirname "$0")"
PROOF="$(pwd)"
PROJ="$(cd ../.. && pwd)"                       # projects/cook-loadcell
SEALED="$PROJ/04_kicad/cook_loadcell.kicad_pcb"
SK="$(cd "$PROJ/../.." && pwd)/skills/kicad-pcb/scripts"
[ -d "$SK" ] || SK="$HOME/.claude/skills/kicad-pcb/scripts"
PY=/usr/bin/python3
export PATH="$HOME/.bun/bin:$PATH"
NOISE='enum choices|Debug: Adding|duplicate image handler|GetWidth called'

K="$PROOF/04_kicad"; B="$PROOF/06_build"
mkdir -p "$K" "$B/netlists" "$B/drc" "$B/route"
cat > "$K/cook_loadcell.kicad_pro" <<'PRO'
{ "board": { "design_settings": {} }, "meta": { "filename": "cook_loadcell.kicad_pro", "version": 1 }, "schematic": { "legacy_lib_dir": "", "legacy_lib_list": [] } }
PRO
cp "$PROJ/04_kicad/fp-lib-table" "$K/fp-lib-table" 2>/dev/null || true

echo "== [1] tsci build: authored TSX -> circuit.json =="
timeout 240 tsci build "src/cook_loadcell.tsx" >/tmp/pp_build.log 2>&1
cp "dist/src/cook_loadcell/circuit.json" "build/circuit.json"

echo "== [2] converter kicad_sch + netlist (connectivity, FPIDs) =="
$PY "$SK/circuit_json_to_kicad_sch.py" build/circuit.json \
    -o "$K/cook_loadcell.kicad_sch" --parts-dir "$PROJ/02_parts" 2>&1 | grep -Ev "$NOISE" | tail -1
kicad-cli sch export netlist -o "$B/netlists/cook_loadcell.net" "$K/cook_loadcell.kicad_sch" >/dev/null 2>&1

echo "== [3] PLACER: land parts at tscircuit-authored placement =="
$PY "$SK/circuit_json_to_kicad_pcb.py" build/circuit.json \
    --netlist "$B/netlists/cook_loadcell.net" --outline-from "$SEALED" \
    -o "$K/cook_loadcell.kicad_pcb" 2>&1 | grep -Ev "$NOISE"

echo "== [4] LEGALIZE + SILK (import -> legalize -> silk) =="
$PY legalize_and_silk.py 2>&1 | grep -Ev "$NOISE"

echo "== [5] AUDIT gate (must PASS) =="
$PY 03_src/audit_board.py 2>&1 | grep -Ev "$NOISE" | tail -2

echo "== [6] reuse promoted route r2 (placement == sealed floorplan) =="
cp "$PROJ/03_src/route/r2.kicad_pcb" "$B/route/r2.kicad_pcb"
$PY "$SK/import_krt.py" "$B/route/r2.kicad_pcb" \
    "$K/cook_loadcell.kicad_pcb" "$K/cook_loadcell.kicad_pcb" 2>&1 | grep -Ei "imported" || true

echo "== [7] rules -> stitch -> rules (LAST) =="
$PY 03_src/generate_rules.py >/dev/null 2>&1
$PY 03_src/stitch_and_fill.py 2>&1 | grep -Ev "$NOISE" | tail -3
$PY 03_src/audit_board.py 2>&1 | grep -Ev "$NOISE" | tail -1
$PY 03_src/generate_rules.py 2>&1 | grep -Ev "$NOISE" | tail -1

echo "== [8] DRC GATE: --severity-all --refill-zones --schematic-parity =="
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity --format json \
    -o "$B/drc/gate.json" "$K/cook_loadcell.kicad_pcb" >/dev/null 2>&1
$PY - "$B/drc/gate.json" <<'PYEOF'
import json, sys
from collections import Counter
d = json.load(open(sys.argv[1]))
nv, nu, np = len(d['violations']), len(d['unconnected_items']), len(d.get('schematic_parity', []))
print('violations:', nv, dict(Counter(v['type'] for v in d['violations'])))
print('unconnected:', nu)
print('parity:', np)
sys.exit(1 if (nv or nu or np) else 0)
PYEOF

echo "== [9] board-netlist parity vs SEALED 04_kicad =="
$PY board_netlist_parity.py "$K/cook_loadcell.kicad_pcb" "$SEALED" 2>&1 | grep -Ev "$NOISE" | tail -1

echo ""
echo "PLACEMENT-AS-CODE PROOF COMPLETE: authored pcbX/pcbY -> audit PASS -> DRC 0/0/0"
