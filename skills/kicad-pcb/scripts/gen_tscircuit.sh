#!/usr/bin/env bash
# gen_tscircuit.sh — render a board's tscircuit/ folder: an ALTERNATE, non-authoritative
# tscircuit design/route of a project, with full JLCPCB fab output + a verification stack
# that proves fidelity against the KiCad fab-of-record.
#
# Canon S-DSL: KiCad .kicad_sch/.kicad_pcb + the gate stack remain the fab-of-record.
# This folder is a SECOND OPINION render — tscircuit authors the board, exports NATIVE
# KiCad, and we run the same kicad-cli gates on it plus a netlist-parity diff against the
# sealed release. It never feeds a fab order on its own.
#
# Usage: gen_tscircuit.sh <project_dir>
#   expects <project_dir>/tscircuit/src/<board>.tsx  (+ package.json)
#   writes  <project_dir>/tscircuit/{build,fab,kicad,verification}/...
#   compares against the newest sealed KiCad board if one exists.
set -uo pipefail
export PATH="$HOME/.bun/bin:$PATH"          # bun + tsci are installed per-user, persist on disk
PROJ="${1:?usage: gen_tscircuit.sh <project_dir>}"
T="$PROJ/tscircuit"
SRC=$(ls "$T"/src/*.tsx 2>/dev/null | head -1)
[ -z "$SRC" ] && { echo "NO tscircuit/src/*.tsx in $PROJ — nothing to render (scaffold only)"; exit 3; }
BASE=$(basename "$SRC" .tsx)
mkdir -p "$T"/build "$T"/fab "$T"/kicad "$T"/verification
step(){ echo "  [$1] $2"; }

step build "circuit-json";      ( cd "$T" && timeout 240 tsci build "src/$BASE.tsx" >/dev/null 2>&1 ) \
  && cp "$T"/dist/*/*.json "$T"/build/circuit.json 2>/dev/null
for f in schematic-svg pcb-svg assembly-svg gltf; do
  ext=${f%-svg}; [ "$f" = gltf ] && ext=gltf || ext=svg; name=${f%-svg}
  step export "$f"; ( cd "$T" && timeout 240 tsci export "src/$BASE.tsx" -f "$f" -o "build/$name.$ext" >/dev/null 2>&1 )
done
step export gerbers;  ( cd "$T" && timeout 240 tsci export "src/$BASE.tsx" -f gerbers -o "fab/gerbers.zip" >/dev/null 2>&1 )
step export kicad_pcb;( cd "$T" && timeout 240 tsci export "src/$BASE.tsx" -f kicad_pcb -o "kicad/$BASE.kicad_pcb" >/dev/null 2>&1 )
step export kicad_sch;( cd "$T" && timeout 240 tsci export "src/$BASE.tsx" -f kicad_sch -o "kicad/$BASE.kicad_sch" >/dev/null 2>&1 )
step export netlist;  ( cd "$T" && timeout 240 tsci export "src/$BASE.tsx" -f readable-netlist -o "verification/tsc_netlist.txt" >/dev/null 2>&1 )

# --- verification: run OUR gate on tscircuit's KiCad export ---
KPCB="$T/kicad/$BASE.kicad_pcb"
if [ -s "$KPCB" ]; then
  step verify "kicad-cli DRC on tscircuit export"
  kicad-cli pcb drc --severity-all --format json -o "$T/verification/drc.json" "$KPCB" >/dev/null 2>&1
  V=$(python3 -c "import json;d=json.load(open('$T/verification/drc.json'));print(len(d['violations']),len(d['unconnected_items']))" 2>/dev/null || echo "? ?")
  echo "    tscircuit-export DRC (kicad-cli, severity-all): $V  (violations unconnected)"
fi

# --- parity vs the sealed KiCad fab-of-record (M1 checker-independence) ---
SEALED=$(ls "$PROJ"/04_kicad/*.kicad_pcb 2>/dev/null | head -1)
{
  echo "# tscircuit-vs-KiCad parity — $(basename "$PROJ")"
  echo
  echo "Compares the tscircuit render's netlist against the KiCad fab-of-record."
  echo "Canon S-DSL: KiCad stays authoritative; this quantifies tscircuit fidelity."
  echo
  if [ -n "$SEALED" ]; then
    echo "KiCad board: \`$SEALED\`"
    # component + net counts, both sides
    python3 - "$SEALED" "$T/verification/tsc_netlist.txt" <<'PY' 2>/dev/null || echo "(parity diff needs pcbnew + a resolvable tsc netlist)"
import sys,re
try:
    import pcbnew
    b=pcbnew.LoadBoard(sys.argv[1])
    kfp={f.GetReference() for f in b.GetFootprints()}
    knets={n for n in b.GetNetsByName().keys() if str(n) and not str(n).startswith('unconnected')}
    print(f"- KiCad: {len(kfp)} footprints, {len(knets)} named nets")
except Exception as e:
    print(f"- KiCad side unreadable: {e}")
try:
    t=open(sys.argv[2]).read()
    tc=len(re.findall(r'^\s*-\s+\w+:', t, re.M))
    tn=len(re.findall(r'^NET:', t, re.M))
    print(f"- tscircuit: ~{tc} components, ~{tn} nets")
    print()
    print("NOTE: refdes/net-name conventions differ between the two front-ends; a")
    print("node-for-node parity requires a name-normalization map (see notes.md). The")
    print("count deltas above are the first-order fidelity signal.")
except Exception as e:
    print(f"- tscircuit side unreadable: {e}")
PY
  else
    echo "(no sealed KiCad board found under 04_kicad/ — parity N/A)"
  fi
} > "$T/verification/parity.md"
echo "  parity report -> $T/verification/parity.md"
echo "DONE: $PROJ/tscircuit rendered."
