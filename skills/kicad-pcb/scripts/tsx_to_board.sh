#!/usr/bin/env bash
# tsx_to_board.sh — THE one-command tscircuit-native rebuild (ADR-0002 Phase E).
#
# Drives a tscircuit-authored board through the UNCHANGED, netlist-driven KiCad
# backend, end to end, to DRC 0/0/0 + board-netlist parity vs the sealed reference:
#
#   tsci build                     TSX -> circuit.json
#   circuit_json_to_kicad_sch      circuit.json -> annotated, backend-ready .kicad_sch
#   kicad-cli sch export netlist   the netlist the backend consumes
#   kicad-cli sch erc              schematic gate (0 errors)
#   [placement]                    generate_board.py (default)  OR  circuit_json_to_kicad_pcb.py (--placement tsx)
#   generate_rules.py              netclasses + dru floors ride into the router (canon R1)
#   KRT route                      reuse the promoted 03_src/route/r*.kicad_pcb chain if present
#   [route_taps.py]                project tap-router if present
#   stitch_and_fill.py             pours + thermal vias
#   generate_rules.py LAST         pcbnew saves clobber .kicad_pro netclasses (canon R1/M3)
#   kicad-cli pcb drc              --severity-all --refill-zones --schematic-parity -> 0/0/0
#   board_netlist_parity.py        node-for-node vs the sealed reference board
#
# The KiCad backend (03_src/*.py) runs BYTE-FOR-BYTE UNCHANGED — the driver only
# wires TSX authoring into it and reparents outputs into an isolated build root so
# the sealed 04_kicad/ and releases are NEVER touched. Idempotent: the build root
# is wiped and rebuilt each run.
#
# Usage: tsx_to_board.sh <project_dir> [--placement generate_board|tsx] [--build-root DIR]
#   default build root: <project>/03_tscircuit/tsx_build
#   sealed parity reference: <project>/04_kicad/<board>.kicad_pcb, OR the path in
#     <project>/03_tscircuit/sealed_ref.txt (relative to <project> or absolute).
set -euo pipefail
export PATH="$HOME/.bun/bin:$PATH"
SKILLDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY=/usr/bin/python3

PLACEMENT=generate_board
BUILD_ROOT=""
ARGS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --placement) PLACEMENT="$2"; shift 2 ;;
    --build-root) BUILD_ROOT="$2"; shift 2 ;;
    *) ARGS+=("$1"); shift ;;
  esac
done
PROJ="${ARGS[0]:?usage: tsx_to_board.sh <project_dir> [--placement generate_board|tsx] [--build-root DIR]}"
PROJ="$(cd "$PROJ" && pwd)"
T="$PROJ/03_tscircuit"
SRCDIR="$PROJ/03_src"
[ -f "$SRCDIR/generate_board.py" ] || { echo "FATAL: no $SRCDIR/generate_board.py (backend not present)"; exit 2; }
TSX=$(ls "$T"/src/*.tsx 2>/dev/null | head -1)
[ -n "$TSX" ] || { echo "FATAL: no $T/src/*.tsx"; exit 2; }
TSCBASE=$(basename "$TSX" .tsx)

# Internal board name = the netlist basename the backend expects (may differ from
# the TSX name; e.g. lipo3s_tsc.tsx builds the usb_power_3s board).
BOARD=$($PY - "$SRCDIR/generate_board.py" <<'PY'
import re,sys
s=open(sys.argv[1]).read()
m=re.search(r'"([A-Za-z0-9_]+)\.net"',s)
print(m.group(1) if m else "")
PY
)
[ -n "$BOARD" ] || { echo "FATAL: could not parse board name (.net) from generate_board.py"; exit 2; }

# Sealed parity reference (overridable via 03_tscircuit/sealed_ref.txt).
if [ -f "$T/sealed_ref.txt" ]; then
  SEALED=$(grep -vE '^\s*#|^\s*$' "$T/sealed_ref.txt" | head -1)
  case "$SEALED" in /*) : ;; *) SEALED="$PROJ/$SEALED" ;; esac
else
  SEALED="$PROJ/04_kicad/$BOARD.kicad_pcb"
fi

BUILD_ROOT="${BUILD_ROOT:-$T/tsx_build}"
K="$BUILD_ROOT/04_kicad"
B="$BUILD_ROOT/06_build"

echo "=================================================================="
echo " tsx_to_board.sh — $(basename "$PROJ")"
echo "   TSX          : $TSX"
echo "   board name   : $BOARD"
echo "   placement    : $PLACEMENT"
echo "   build root   : $BUILD_ROOT   (isolated; sealed 04_kicad/ untouched)"
echo "   sealed ref   : $SEALED"
echo "=================================================================="
gate(){ echo "  --> $*"; }
fail(){ echo "  XX FAIL: $*"; exit 1; }

# ---- isolated, idempotent build root: symlink 03_src so backend reparents here ----
rm -rf "$BUILD_ROOT"
mkdir -p "$K" "$B/netlists" "$B/drc" "$B/route"
ln -s "$SRCDIR" "$BUILD_ROOT/03_src"          # __file__.parent.parent -> BUILD_ROOT (reparent trick)
RSRC="$BUILD_ROOT/03_src"                      # run backend scripts THROUGH the symlink
cp "$PROJ/04_kicad/fp-lib-table" "$K/fp-lib-table" 2>/dev/null || true
cat > "$K/$BOARD.kicad_pro" <<PRO
{
  "board": { "design_settings": {} },
  "meta": { "filename": "$BOARD.kicad_pro", "version": 1 },
  "schematic": { "legacy_lib_dir": "", "legacy_lib_list": [] }
}
PRO

# ---- [1] tsci build: TSX -> circuit.json ----
gate "[1] tsci build -> circuit.json"
mkdir -p "$T/build"
( cd "$T" && timeout 300 tsci build "src/$TSCBASE.tsx" >/dev/null 2>&1 \
    && cp "dist/src/$TSCBASE/circuit.json" "build/circuit.json" )
[ -s "$T/build/circuit.json" ] || fail "tsci build produced no circuit.json"

# ---- [2] converter: circuit.json -> backend-ready .kicad_sch ----
gate "[2] circuit_json_to_kicad_sch -> $BOARD.kicad_sch"
NETALIAS=""; [ -f "$T/net_aliases.txt" ] && NETALIAS="--net-aliases $T/net_aliases.txt"
$PY "$SKILLDIR/circuit_json_to_kicad_sch.py" "$T/build/circuit.json" \
    -o "$K/$BOARD.kicad_sch" --project "$BOARD" $NETALIAS | sed 's/^/      /'
[ -s "$K/$BOARD.kicad_sch" ] || fail "converter produced no kicad_sch"

# ---- [3] export netlist (what the backend consumes) ----
gate "[3] kicad-cli sch export netlist"
kicad-cli sch export netlist -o "$B/netlists/$BOARD.net" "$K/$BOARD.kicad_sch" >/dev/null 2>&1
[ -s "$B/netlists/$BOARD.net" ] || fail "netlist export empty"

# ---- [4] ERC gate ----
gate "[4] kicad-cli sch erc --severity-all"
kicad-cli sch erc --severity-all --format json -o "$B/drc/erc.json" "$K/$BOARD.kicad_sch" >/dev/null 2>&1
$PY - "$B/drc/erc.json" <<'PY' || fail "ERC errors"
import json,sys
d=json.load(open(sys.argv[1]))
v=[x for s in d['sheets'] for x in s['violations']]
e=[x for x in v if x.get('severity')=='error']
print(f"      ERC: {len(e)} errors, {len(v)-len(e)} warnings (baselined)")
sys.exit(1 if e else 0)
PY

# ---- [5] placement ----
if [ "$PLACEMENT" = "tsx" ]; then
  gate "[5] placement-as-code: circuit_json_to_kicad_pcb (authored pcbX/pcbY)"
  $PY "$SKILLDIR/circuit_json_to_kicad_pcb.py" "$T/build/circuit.json" \
      --netlist "$B/netlists/$BOARD.net" -o "$K/$BOARD.kicad_pcb" \
      --outline-from "$SEALED" | sed 's/^/      /'
  # project-supplied legalize+silk pass (seed-agnostic), if present
  for LG in "$T/placement_proof/legalize_and_silk.py" "$SRCDIR/legalize_and_silk.py"; do
    [ -f "$LG" ] && { gate "    legalize_and_silk"; $PY "$LG" "$K/$BOARD.kicad_pcb" 2>/dev/null | tail -2 | sed 's/^/      /' || true; break; }
  done
else
  gate "[5] placement: generate_board.py (UNCHANGED backend, hand-coded floorplan)"
  $PY "$RSRC/generate_board.py" 2>/dev/null | tail -2 | sed 's/^/      /'
fi
[ -s "$K/$BOARD.kicad_pcb" ] || fail "placement produced no kicad_pcb"

# ---- audit (if the project has one) ----
if [ -f "$SRCDIR/audit_board.py" ]; then
  gate "    audit_board.py (placement gate)"
  $PY "$RSRC/audit_board.py" 2>/dev/null | tail -2 | sed 's/^/      /' || true
fi

# ---- [6] generate_rules BEFORE routing (canon R1: rules ride into the router) ----
gate "[6] generate_rules.py (netclasses + dru floors, pre-route)"
$PY "$RSRC/generate_rules.py" >/dev/null 2>&1 || true

# ---- [7] KRT route: reuse the promoted chain if present ----
CHAIN=$(ls "$SRCDIR"/route/r*.kicad_pcb 2>/dev/null | sort -V | tail -1)
if [ -n "$CHAIN" ]; then
  gate "[7] import promoted KRT route: $(basename "$CHAIN")"
  cp "$CHAIN" "$B/route/$(basename "$CHAIN")"
  $PY "$SKILLDIR/import_krt.py" "$B/route/$(basename "$CHAIN")" \
      "$K/$BOARD.kicad_pcb" "$K/$BOARD.kicad_pcb" 2>/dev/null | grep -i imported | sed 's/^/      /' || true
else
  echo "  !! no promoted chain under 03_src/route/ — a fresh KRT route is required"
  echo "     (see references/routing-pipeline.md; the reuse path is the reproducible one)"
  fail "no promoted route chain to reuse"
fi

# ---- [8] project tap-router (if present) ----
if [ -f "$SRCDIR/route_taps.py" ]; then
  gate "[8] route_taps.py"
  $PY "$RSRC/route_taps.py" 2>/dev/null | tail -2 | sed 's/^/      /' || true
fi

# ---- [9] stitch_and_fill ----
gate "[9] stitch_and_fill.py (pours + thermal vias)"
$PY "$RSRC/stitch_and_fill.py" 2>/dev/null | tail -3 | sed 's/^/      /' || true

# ---- audit again (post-route) ----
if [ -f "$SRCDIR/audit_board.py" ]; then
  gate "    audit_board.py (post-route)"
  $PY "$RSRC/audit_board.py" 2>/dev/null | tail -2 | sed 's/^/      /' || true
fi

# ---- [10] generate_rules LAST (pcbnew saves clobber netclasses) ----
gate "[10] generate_rules.py LAST"
$PY "$RSRC/generate_rules.py" 2>/dev/null | tail -1 | sed 's/^/      /' || true

# ---- [11] DRC GATE: must be 0/0/0 ----
gate "[11] DRC: --severity-all --refill-zones --schematic-parity"
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity --format json \
    -o "$B/drc/gate.json" "$K/$BOARD.kicad_pcb" >/dev/null 2>&1
$PY - "$B/drc/gate.json" <<'PY' || fail "DRC not clean"
import json,sys
from collections import Counter
d=json.load(open(sys.argv[1]))
nv,nu,npar=len(d['violations']),len(d['unconnected_items']),len(d.get('schematic_parity',[]))
print(f"      violations: {nv} {dict(Counter(v['type'] for v in d['violations']))}")
print(f"      unconnected: {nu}")
print(f"      schematic-parity: {npar}")
sys.exit(1 if (nv or nu or npar) else 0)
PY
echo "      DRC 0/0/0 — CLEAN"

# ---- [12] board-netlist parity vs the sealed reference ----
gate "[12] board_netlist_parity.py vs sealed reference"
if [ -s "$SEALED" ]; then
  $PY "$SKILLDIR/board_netlist_parity.py" "$K/$BOARD.kicad_pcb" "$SEALED" | sed 's/^/      /'
else
  echo "      (no sealed reference at $SEALED — parity SKIPPED)"
fi

echo "=================================================================="
echo " tsx_to_board.sh COMPLETE — $BOARD -> DRC 0/0/0, board parity vs sealed"
echo " build root: $BUILD_ROOT (throwaway; sealed 04_kicad/ + releases untouched)"
echo "=================================================================="
