#!/bin/bash
# TEMPLATE rebuild_all.sh — the canonical generic pipeline (skill-owned).
# Copy into a new board's 03_src/ and set BOARD + TSX below. ZERO board-specific
# generation Python: board + route + rules all run on the SHARED skill scripts.
# See 03_src/contracts.md for the authoritative step order.
set -euo pipefail
cd "$(dirname "$0")/.."                       # -> project root (03_src/..)

# --- board-specific knobs (the ONLY things to edit) -------------------------
BOARD=power3s                                  # <board> stem for 04_kicad/<board>.*
TSX=power3s                                    # 03_tscircuit/src/<TSX>.tsx basename
# ----------------------------------------------------------------------------

PY=/usr/bin/python3
# resolve the shared skill scripts (repo-relative first, ~/.claude fallback)
SKROOT="$(cd "$(git rev-parse --show-toplevel 2>/dev/null || echo ../../..)" && pwd)/skills"
S="$SKROOT/kicad-pcb/scripts"
[ -f "$S/generate_board_generic.py" ] || { SKROOT="$HOME/.claude/skills"; S="$SKROOT/kicad-pcb/scripts"; }
FS="$SKROOT/jlcpcb-fab/scripts"                # fab-skill checkers (bom_source_check)
export PATH="$HOME/.nvm/versions/node/v22.12.0/bin:$HOME/.bun/bin:$PATH"

# [0] S-COUNT pre-gate: alphanumeric pads mapped BEFORE the first tsci build —
# tscircuit DROPS an unmapped part silently (ERC still 0, 2026-07-21 incident)
$PY "$S/tsx_preflight.py" . \
    || { echo "GATE FAILED [0] TSX-PRE (tsx_preflight.py): map alphanumeric pads in 03_tscircuit/parity_padmap.txt BEFORE tsci build"; exit 1; }

# [1] tscircuit TSX -> circuit.json -> converter .kicad_sch -> netlist
( cd 03_tscircuit && tsci build "src/$TSX.tsx" )
$PY "$S/circuit_json_to_kicad_sch.py" 03_tscircuit/build/circuit.json \
    -o "04_kicad/$BOARD.kicad_sch" --parts 02_parts
kicad-cli sch export netlist --output "06_build/netlists/$BOARD.net" "04_kicad/$BOARD.kicad_sch"

# [1b] CHEAP SEMANTIC BATTERY at the schematic gate — seconds each, run HERE
# and not first at seal (a defect authored at this stage and caught at seal
# costs a superseded release: R12/R30 shipped in 2 sealed BOMs; the P5VA_4
# net-merge shipped a DO-NOT-ORDER board — both 2026-07-23).
$PY "$S/net_label_survival.py" . \
    || { echo "GATE FAILED [1b] S-NETMERGE (net_label_survival.py): a schematic net label merged/swallowed at netlist export"; exit 1; }
$PY "$S/electrical_invariants.py" . \
    || { echo "GATE FAILED [1b] E-INV (electrical_invariants.py): netlist violates a design-intent assertion"; exit 1; }
$PY "$S/electrical_invariants.py" . --adr-coverage \
    || { echo "GATE FAILED [1b] E-ADR (electrical_invariants.py --adr-coverage): a protection/topology ADR emitted no invariant"; exit 1; }
$PY "$S/power_topology.py" . \
    || { echo "GATE FAILED [1b] E-TOPO (power_topology.py): converter topology does not match the derived Vin-vs-Vout"; exit 1; }
$PY "$S/power_topology.py" . --margin \
    || { echo "GATE FAILED [1b] E-MARGIN (power_topology.py --margin): output setpoint headroom below the delivery IR drop"; exit 1; }
$PY "$S/power_topology.py" . --off-control \
    || { echo "GATE FAILED [1b] E-OFF (power_topology.py --off-control): battery source without a declared de-energization path"; exit 1; }
$PY "$S/count_parity.py" . \
    || { echo "GATE FAILED [1b] S-COUNT (count_parity.py): refdes sets disagree across intent/artifacts (silent drop)"; exit 1; }
$PY "$FS/bom_source_check.py" --circuit-only 03_tscircuit/build/circuit.json --parts 02_parts \
    || { echo "GATE FAILED [1b] M-BOM leg C (bom_source_check.py --circuit-only): a coded R/C's catalog value != its tsx value prop (the R12/R30 class)"; exit 1; }

# [2] ERC gate (0 errors)
kicad-cli sch erc --severity-all --exit-code-violations "04_kicad/$BOARD.kicad_sch" \
    -o 06_build/erc.rpt || { echo "ERC FAILED"; exit 1; }

# [3] board (placement + zones) from floorplan.yaml  [SHARED]
$PY "$S/generate_board_generic.py" 03_src/floorplan.yaml -o "04_kicad/$BOARD.kicad_pcb"

# [4] placement/pad invariants  [per-board gate + SHARED placement gates]
$PY 03_src/audit_board.py
# P-OUT pads-inside-outline + P-CAP corridor crossing-demand vs capacity —
# the two checks the cooksense routing D-BACK (2026-07-23, ~13h) proved were
# missing statically. Config 03_src/placement_gates.json is OPTIONAL
# (missing file = defaults); waivers live inside it, evidence required.
$PY "$S/placement_gates.py" "04_kicad/$BOARD.kicad_pcb" --config 03_src/placement_gates.json

# [5] netclasses BEFORE route-prep (canon R1)  [SHARED]
$PY "$S/generate_rules_generic.py" .

# [5b] R-PREFLIGHT: tool config == declared fab tier — refuse before prep/import
# (the template replays a promoted chain via `import`, which bypasses the
#  route-command gate; run the preflight explicitly so rebuilds are gated too)
$PY "$S/tier_preflight.py" . \
    || { echo "GATE FAILED [5b] R-PREFLIGHT (tier_preflight.py): a routing/stitch parameter disagrees with the declared fab tier"; exit 1; }

# [6-8] route + stitch from route.yaml  [SHARED]
$PY "$S/route_and_stitch_generic.py" prep   03_src/route.yaml
$PY "$S/route_and_stitch_generic.py" import 03_src/route.yaml   # replay promoted route/ chain (M3)
$PY "$S/route_and_stitch_generic.py" stitch 03_src/route.yaml

# [9] generate_rules LAST (pcbnew saves clobber .kicad_pro netclasses)  [SHARED]
$PY "$S/generate_rules_generic.py" .

# [10] DRC gate — must be 0 / 0 / 0 at full severity
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity \
    --format json -o 06_build/drc/gate.json "04_kicad/$BOARD.kicad_pcb"
$PY -c "import json;g=json.load(open('06_build/drc/gate.json'));v,u,p=len(g['violations']),len(g['unconnected_items']),len(g.get('schematic_parity',[]));print(f'DRC {v}/{u}/{p}');exit(0 if v==u==p==0 else 1)"
