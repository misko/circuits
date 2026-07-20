#!/bin/bash
# Phase-3 proof (ADR-0001): drive the ENTIRE cook-loadcell KiCad backend from
# the TSX-authored (converter) schematic, end to end, to DRC 0/0/0.
#
# This mirrors 03_src/rebuild_all.sh STEP-FOR-STEP. The 03_src backend scripts
# run BYTE-IDENTICAL: backend_proof/03_src is a symlink to ../../03_src, and
# each script keys its project root off Path(__file__).parent.parent, so with
# the symlinked path that root reparents to backend_proof/ — outputs land in
# backend_proof/04_kicad + backend_proof/06_build and NEVER touch the sealed
# 04_kicad/.
#
# The path differs from rebuild_all.sh in exactly ONE place:
#   generate_schematic.py (schwriter2) is replaced by prepare_backend_sch.py — the
#   single integration adapter. It takes the Phase-2 converter kicad_sch (TSX ->
#   circuit.json -> skills/kicad-pcb/scripts/circuit_json_to_kicad_sch.py) and makes
#   it BACKEND-READY: canonical net names (N5V->5V, N3V3->3V3), KiCad footprint
#   FPIDs filled from the authored TSX footprint tokens, tscircuit's MPN symbol
#   field dropped, and concise TP silk values. See prepare_backend_sch.py for why
#   each is needed. After it, the exported netlist carries canonical nets + FPIDs,
#   so every downstream step — netlist export, generate_board, audit_board,
#   import_krt(r2), stitch_and_fill, generate_rules, DRC --schematic-parity — is
#   the project's own 03_src, byte-for-byte UNCHANGED.
set -euo pipefail
cd "$(dirname "$0")"
PROOF="$(pwd)"
PROJ="$(cd ../.. && pwd)"                       # projects/cook-loadcell
SRC="$PROJ/03_src"
CONV_SCH="$PROJ/tscircuit/kicad/cook_loadcell.kicad_sch"   # TSX-authored schematic
SEALED_PCB="$PROJ/04_kicad/cook_loadcell.kicad_pcb"        # for board-netlist parity
PY=/usr/bin/python3
SKILLS="$(cd "$PROJ/../.." && pwd)/skills/kicad-pcb/scripts"
[ -d "$SKILLS" ] || SKILLS="$HOME/.claude/skills/kicad-pcb/scripts"

K="$PROOF/04_kicad"
B="$PROOF/06_build"
rm -rf "$K" "$B"
mkdir -p "$K" "$B/netlists" "$B/drc" "$B/route"

echo "== [1] SCHEMATIC SOURCE = TSX converter kicad_sch -> ONE adapter (prepare_backend_sch) =="
# The only integration adapter: converter kicad_sch -> backend-ready kicad_sch
# (canonical net names + KiCad FPIDs + MPN drop + concise TP silk). After this,
# the 03_src backend is byte-for-byte unchanged.
$PY "$PROOF/prepare_backend_sch.py" "$CONV_SCH" "$PROJ/tscircuit/src/cook_loadcell.tsx" \
    "$K/cook_loadcell.kicad_sch"
cp "$PROJ/04_kicad/fp-lib-table" "$K/fp-lib-table" 2>/dev/null || true
# seed the minimal .kicad_pro generate_schematic would have written (generate_rules
# merges netclasses+floors into it; it must exist and be valid JSON).
cat > "$K/cook_loadcell.kicad_pro" <<'PRO'
{
  "board": { "design_settings": {} },
  "meta": { "filename": "cook_loadcell.kicad_pro", "version": 1 },
  "schematic": { "legacy_lib_dir": "", "legacy_lib_list": [] }
}
PRO

echo "== [2] export netlist from the prepared TSX schematic (UNCHANGED step) =="
kicad-cli sch export netlist -o "$B/netlists/cook_loadcell.net" "$K/cook_loadcell.kicad_sch" >/dev/null

echo "== [3] ERC gate on the TSX schematic =="
kicad-cli sch erc --severity-all --format json -o "$B/drc/erc.json" "$K/cook_loadcell.kicad_sch" >/dev/null
$PY - "$B/drc/erc.json" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1]))
v = [x for s in d['sheets'] for x in s['violations']]
errs = [x for x in v if x.get('severity') == 'error']
print(f'ERC: {len(errs)} errors, {len(v)-len(errs)} warnings (baselined)')
sys.exit(1 if errs else 0)
PYEOF

echo "== [4] generate_board.py (UNCHANGED 03_src, root=backend_proof) =="
$PY "$PROOF/03_src/generate_board.py" | tail -2

echo "== [5] audit_board.py (UNCHANGED) =="
$PY "$PROOF/03_src/audit_board.py" | tail -2

echo "== [6-7] import promoted KRT route r2.kicad_pcb (UNCHANGED) =="
cp "$SRC/route/r2.kicad_pcb" "$B/route/r2.kicad_pcb"
$PY "$SKILLS/import_krt.py" "$B/route/r2.kicad_pcb" \
    "$K/cook_loadcell.kicad_pcb" "$K/cook_loadcell.kicad_pcb" | grep imported || true

echo "== [8] generate_rules.py (UNCHANGED) =="
$PY "$PROOF/03_src/generate_rules.py" >/dev/null

echo "== [9] stitch_and_fill.py (UNCHANGED) =="
$PY "$PROOF/03_src/stitch_and_fill.py" | tail -4

echo "== [10] audit_board.py (UNCHANGED) =="
$PY "$PROOF/03_src/audit_board.py" | tail -2

echo "== [11] generate_rules.py LAST (UNCHANGED) =="
$PY "$PROOF/03_src/generate_rules.py"

echo "== [12] DRC GATE: --severity-all --refill-zones --schematic-parity =="
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity --format json \
    -o "$B/drc/gate.json" "$K/cook_loadcell.kicad_pcb" >/dev/null
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

echo "== [13] board-netlist parity: built board vs SEALED 04_kicad board =="
$PY "$PROOF/board_netlist_parity.py" "$K/cook_loadcell.kicad_pcb" "$SEALED_PCB"

echo ""
echo "PROOF COMPLETE: TSX-authored schematic -> DRC 0/0/0, board parity vs sealed OK"
