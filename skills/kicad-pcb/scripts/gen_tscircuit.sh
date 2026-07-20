#!/usr/bin/env bash
# gen_tscircuit.sh — render a board's tscircuit/ folder.
#
# ADR-0002 Phase D (2026-07-20): the DEFAULT is now the BRIDGE ONLY — the
# minimal set the KiCad backend actually consumes + the gates that certify it:
#   build/circuit.json                 tscircuit's canonical intermediate (tsci build)
#   build/schematic.svg + .pdf         the HUMAN schematic document (tscircuit's own render)
#   kicad/<board>.kicad_sch            OUR converter output (AUTHORITATIVE machine bridge)
#   verification/tsc_netlist.txt       tscircuit readable-netlist (first-order parity signal)
#   verification/erc_converter.rpt     kicad-cli sch ERC on the converter sch (0 errors = bar)
#   verification/parity_converter.md   node-for-node netlist parity vs the sealed 04_kicad
#   verification/parity.md             first-order component/net counts vs the sealed board
#
# The tscircuit PCB STUDY exports are GATED behind `--study` (DEFAULT OFF):
#   build/{pcb.svg,assembly.svg,board.gltf}    tscircuit's own PCB/3D render
#   fab/gerbers.zip                            tscircuit's own gerbers
#   kicad/<board>.kicad_pcb                    tscircuit native PCB export (study copper)
#   kicad/<board>.native.kicad_sch             tscircuit native kicad_sch (buggy — reference only)
#   verification/drc.json                      kicad-cli DRC ON the tscircuit PCB export
# tscircuit's own PCB/gerbers are NEVER our fab source (KRT + the KiCad backend
# route the fab board — the two hard lines, ADR-0002), so rendering them by
# default was duplicate compute. `--study` restores the full second-opinion render
# for the rare case someone wants to eyeball tscircuit's own layout; the capability
# is retained, just no longer the default.
#
# Canon S-DSL: KiCad .kicad_sch/.kicad_pcb + the gate stack remain the fab-of-record.
#
# Usage: gen_tscircuit.sh <project_dir> [--study]
#   expects <project_dir>/tscircuit/src/<board>.tsx  (+ package.json)
#   writes  <project_dir>/tscircuit/{build,kicad,verification}[,fab]/...
#   compares against the newest sealed KiCad board if one exists.
set -uo pipefail
export PATH="$HOME/.bun/bin:$PATH"          # bun + tsci are installed per-user, persist on disk
SKILLDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # resolve BEFORE any cd
STUDY=0
ARGS=()
for a in "$@"; do
  case "$a" in
    --study) STUDY=1 ;;
    *) ARGS+=("$a") ;;
  esac
done
PROJ="${ARGS[0]:?usage: gen_tscircuit.sh <project_dir> [--study]}"
PROJ="$(cd "$PROJ" && pwd)"                  # absolute — the script cds into $T later
T="$PROJ/tscircuit"
SRC=$(ls "$T"/src/*.tsx 2>/dev/null | head -1)
[ -z "$SRC" ] && { echo "NO tscircuit/src/*.tsx in $PROJ — nothing to render (scaffold only)"; exit 3; }
BASE=$(basename "$SRC" .tsx)
mkdir -p "$T"/build "$T"/kicad "$T"/verification
[ "$STUDY" = 1 ] && mkdir -p "$T"/fab
step(){ echo "  [$1] $2"; }

# NOTE: `tsci export -o P` resolves P relative to the INPUT file's directory
# (src/) and strips leading slashes — so outputs are written as ../<dir>/... to
# land at the tscircuit/ root. All tsci commands run from $T.
cd "$T" || exit 2

# --- BRIDGE (DEFAULT): circuit.json + human schematic doc ---
step build "circuit-json";      timeout 240 tsci build "src/$BASE.tsx" >/dev/null 2>&1 \
  && cp "dist/src/$BASE/circuit.json" "build/circuit.json" 2>/dev/null
step export "schematic-svg";    timeout 240 tsci export "src/$BASE.tsx" -f schematic-svg -o "../build/schematic.svg" >/dev/null 2>&1
step export netlist;            timeout 240 tsci export "src/$BASE.tsx" -f readable-netlist -o "../verification/tsc_netlist.txt" >/dev/null 2>&1

# --- HUMAN-FACING schematic document = tscircuit's OWN render (ADR-0002) ---
# The two audiences are split: humans read tscircuit's clean native schematic
# (no collisions); the machine reads kicad/<board>.kicad_sch (correctness only,
# ERC/netlist/parity). We do NOT re-render our KiCad rebuild for the human PDF.
# tscircuit exports schematic-svg; rsvg-convert makes the PDF the release ships.
if [ -s "build/schematic.svg" ] && command -v rsvg-convert >/dev/null; then
  step render "schematic.svg -> schematic.pdf (tscircuit render = the human schematic)"
  rsvg-convert -f pdf -o "build/schematic.pdf" "build/schematic.svg" 2>/dev/null \
    && echo "    build/schematic.pdf (SHIP THIS as the release schematic document)"
fi

# --- STUDY-ONLY (gated behind --study, DEFAULT OFF): tscircuit's own PCB/gerbers/3D ---
# These are a SECOND-OPINION render of tscircuit's OWN layout. They are never a fab
# source (KRT + the KiCad backend own the fab route). Retired from the default path
# (ADR-0002 Phase D) to kill duplicate compute; kept fully reversible under --study.
if [ "$STUDY" = 1 ]; then
  echo "  --study: rendering tscircuit's own PCB/gerbers/3D + DRC-on-export (second opinion)"
  for spec in "pcb-svg:build/pcb.svg" "assembly-svg:build/assembly.svg" "gltf:build/board.gltf"; do
    f=${spec%%:*}; out=${spec#*:}
    step export "$f"; timeout 240 tsci export "src/$BASE.tsx" -f "$f" -o "../$out" >/dev/null 2>&1
  done
  step export gerbers;  timeout 240 tsci export "src/$BASE.tsx" -f gerbers -o "../fab/gerbers.zip" >/dev/null 2>&1
  step export kicad_pcb;timeout 240 tsci export "src/$BASE.tsx" -f kicad_pcb -o "../kicad/$BASE.kicad_pcb" >/dev/null 2>&1
  # tscircuit's OWN native kicad_sch export is kept for reference only (ADR-0001
  # Phase-2: it has two proven bugs — the Device:U_chip_<footprint> symbol-id
  # collision that truncates 2+ many-pin custom-footprint chips to 2 pins, and no
  # symbol annotation so `sch export netlist` builds 0 nets). It is NOT authoritative.
  step export kicad_sch_native; timeout 240 tsci export "src/$BASE.tsx" -f kicad_sch -o "../kicad/$BASE.native.kicad_sch" >/dev/null 2>&1
  # verification: run OUR gate on tscircuit's KiCad export
  KPCB="$T/kicad/$BASE.kicad_pcb"
  if [ -s "$KPCB" ]; then
    step verify "kicad-cli DRC on tscircuit export"
    kicad-cli pcb drc --severity-all --format json -o "$T/verification/drc.json" "$KPCB" >/dev/null 2>&1
    V=$(python3 -c "import json;d=json.load(open('$T/verification/drc.json'));print(len(d['violations']),len(d['unconnected_items']))" 2>/dev/null || echo "? ?")
    echo "    tscircuit-export DRC (kicad-cli, severity-all): $V  (violations unconnected)"
  fi
fi

# --- OUR converter: circuit.json -> an ANNOTATED, unique-symbol kicad_sch ---
# This is the AUTHORITATIVE tscircuit->KiCad schematic bridge (ADR-0001 Phase 2;
# ADR-0002 Phase A). DEFAULT MODE = layout (WIRED): it consumes tscircuit's own
# schematic layout that circuit.json carries — schematic_component positions,
# schematic_trace wire routes and schematic_net_label — and emits KiCad `(wire)`
# where tscircuit drew a trace and a KiCad label where tscircuit used a label
# (GND -> ground power symbols). Every source_component still gets a UNIQUE
# per-refdes lib_symbol (never a shared Device:U_chip) and every pin is keyed to
# the KiCad pad name, so `kicad-cli sch export netlist` reaches node-for-node
# parity vs the sealed 04_kicad board — but the sheet is now READABLE and WIRED,
# retiring the S6 label-blob finding. If a board's trace geometry can't import
# without a cross-net short, the converter auto-falls-back to v1's label grid
# (`--mode grid`) for that board and logs it (parity is never worse than v1).
if [ -s "build/circuit.json" ]; then
  step convert "circuit.json -> WIRED kicad_sch (OUR converter, layout mode)"
  CONVOUT=$(python3 "$SKILLDIR/circuit_json_to_kicad_sch.py" "build/circuit.json" \
    -o "kicad/$BASE.kicad_sch" --project "$BASE" 2>&1)
  if [ -s "kicad/$BASE.kicad_sch" ]; then
    echo "    $(echo "$CONVOUT" | head -1)"
  else
    echo "    CONVERTER FAILED: $CONVOUT"
  fi
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

# --- AUTHORITATIVE gate: ERC + node-for-node parity on OUR converter kicad_sch ---
# (ADR-0001 Phase 2). This is the bridge the pipeline actually depends on.
KSCH="$T/kicad/$BASE.kicad_sch"
if [ -s "$KSCH" ]; then
  step gate "ERC on converter kicad_sch (severity-all)"
  kicad-cli sch erc --severity-all -o "$T/verification/erc_converter.rpt" "$KSCH" >/dev/null 2>&1
  ERRS=$(grep -c '; error' "$T/verification/erc_converter.rpt" 2>/dev/null || echo "?")
  WARN=$(grep -c '; warning' "$T/verification/erc_converter.rpt" 2>/dev/null || echo "?")
  echo "    converter ERC: $ERRS errors, $WARN warnings (warnings baselined: lib_symbol_issues env note + named-NC isolated labels)"
  if [ -n "$SEALED" ]; then
    step gate "node-for-node netlist parity vs sealed 04_kicad"
    kicad-cli sch export netlist --format kicadsexpr \
      -o "$T/verification/converter_netlist.net" "$KSCH" >/dev/null 2>&1
    # per-board documented pad-name normalization (tscircuit footprinter vs KiCad land)
    PADMAP=""
    [ -f "$T/parity_padmap.txt" ] && PADMAP="$(cat "$T/parity_padmap.txt")"
    python3 "$SKILLDIR/kicad_sch_parity.py" "$BASE" \
      "$T/verification/converter_netlist.net" "$SEALED" --padmap "$PADMAP" \
      | tee "$T/verification/parity_converter.md"
  fi
fi
echo "DONE: $PROJ/tscircuit rendered ($([ "$STUDY" = 1 ] && echo 'bridge + --study' || echo 'bridge only; pass --study for the PCB/gerber second-opinion render'))."
