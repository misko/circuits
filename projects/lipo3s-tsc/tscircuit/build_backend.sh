#!/bin/bash
# lipo3s-tsc CAPSTONE backend build (ADR-0001): drive the ENTIRE usb-power-3s KiCad
# backend from the TSX-authored (converter) schematic to DRC 0/0/0 + board-netlist
# parity vs the sealed usb-power-3s board. Mirrors ../03_src/rebuild_all.sh step for
# step, with generate_schematic.py REPLACED by the converter's backend-ready kicad_sch.
# The 03_src backend scripts (copied verbatim from usb-power-3s) run UNCHANGED; the
# board's internal name stays "usb_power_3s" so the promoted route r5 + rules + FPIDs
# transfer byte-for-byte. Writes only under lipo3s-tsc/.
set -euo pipefail
cd "$(dirname "$0")/.."                 # projects/lipo3s-tsc
PROJ="$(pwd)"
SRC="$PROJ/03_src"
CONV_SCH="$PROJ/tscircuit/kicad/lipo3s_tsc.kicad_sch"
SEALED="$PROJ/../usb-power-3s/04_kicad/usb_power_3s.kicad_pcb"
PY=/usr/bin/python3
SKILLS="$HOME/.claude/skills/kicad-pcb/scripts"
K="$PROJ/04_kicad"; B="$PROJ/06_build"
mkdir -p "$K" "$B/netlists" "$B/drc" "$B/route"

echo "== [1] schematic source = TSX converter kicad_sch (no adapter) =="
cp "$CONV_SCH" "$K/usb_power_3s.kicad_sch"
[ -f "$K/usb_power_3s.kicad_pro" ] || cat > "$K/usb_power_3s.kicad_pro" <<'PRO'
{
  "board": { "design_settings": {} },
  "meta": { "filename": "usb_power_3s.kicad_pro", "version": 1 },
  "schematic": { "legacy_lib_dir": "", "legacy_lib_list": [] }
}
PRO

echo "== [2] export netlist =="
kicad-cli sch export netlist -o "$B/netlists/usb_power_3s.net" "$K/usb_power_3s.kicad_sch" >/dev/null 2>&1

echo "== [3] ERC gate (0 errors) =="
kicad-cli sch erc --severity-all --format json -o "$B/drc/erc.json" "$K/usb_power_3s.kicad_sch" >/dev/null 2>&1
$PY - "$B/drc/erc.json" <<'PYEOF'
import json,sys
d=json.load(open(sys.argv[1]))
v=[x for s in d['sheets'] for x in s['violations']]
errs=[x for x in v if x.get('severity')=='error']
print(f"ERC: {len(errs)} errors, {len(v)-len(errs)} warnings (baselined)")
sys.exit(1 if errs else 0)
PYEOF

echo "== [4] generate_board.py (UNCHANGED 03_src) =="
$PY "$SRC/generate_board.py" 2>/dev/null | tail -2
echo "== [5] audit_board.py =="
$PY "$SRC/audit_board.py" 2>/dev/null | tail -2 || true
echo "== [6-7] import promoted KRT route r5 =="
cp "$SRC/route/r5.kicad_pcb" "$B/route/r5.kicad_pcb"
$PY "$SKILLS/import_krt.py" "$B/route/r5.kicad_pcb" \
    "$K/usb_power_3s.kicad_pcb" "$K/usb_power_3s.kicad_pcb" 2>/dev/null | grep imported || true
echo "== [8] route_taps.py =="
$PY "$SRC/route_taps.py" 2>/dev/null | tail -2 || true
echo "== [9] stitch_and_fill.py =="
$PY "$SRC/stitch_and_fill.py" 2>/dev/null | tail -3 || true
echo "== [10] audit_board.py =="
$PY "$SRC/audit_board.py" 2>/dev/null | tail -2 || true
echo "== [11] generate_rules.py LAST =="
$PY "$SRC/generate_rules.py" 2>/dev/null | tail -1

echo "== [12] DRC GATE: --severity-all --refill-zones --schematic-parity =="
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity --format json \
    -o "$B/drc/gate.json" "$K/usb_power_3s.kicad_pcb" >/dev/null 2>&1
$PY - "$B/drc/gate.json" <<'PYEOF'
import json,sys
from collections import Counter
d=json.load(open(sys.argv[1]))
nv,nu,np=len(d['violations']),len(d['unconnected_items']),len(d.get('schematic_parity',[]))
print('violations:',nv,dict(Counter(v['type'] for v in d['violations'])))
print('unconnected:',nu)
print('parity:',np)
sys.exit(1 if (nv or nu or np) else 0)
PYEOF

echo "== [13] board-netlist parity: built vs SEALED usb-power-3s =="
$PY "$PROJ/../cook-loadcell/tscircuit/backend_proof/board_netlist_parity.py" \
    "$K/usb_power_3s.kicad_pcb" "$SEALED"
echo ""
echo "CAPSTONE BUILD COMPLETE"
