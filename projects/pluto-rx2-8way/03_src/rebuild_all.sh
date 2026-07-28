#!/bin/bash
# pluto-rx2-8way rebuild_all.sh — the canonical generic pipeline, seeded from
# skills/pcb-design/templates/03_src/rebuild_all.sh. ZERO board-specific
# generation Python: board + route + rules all run on the SHARED skill scripts.
# See 03_src/contracts.md for the authoritative step order.
#
# SEEDED-BUT-UNEDITED UNTIL 2026-07-28: this file still carried the template's
# `BOARD=power3s / TSX=power3s`, so it would have built a board this project
# does not have. Fixed at stage 4 together with route.yaml (which was still
# cook-loadcell's schema example verbatim).
#
# THREE DELIBERATE DEVIATIONS FROM THE TEMPLATE, each with its reason:
#  (a) the converter emits to 03_tscircuit/kicad/<board>.kicad_sch FIRST — the
#      home 03_tscircuit/contracts.md calls "the AUTHORITATIVE machine bridge"
#      and the exact path rebuild_reuse.sh requires ("run rebuild_all.sh once
#      and COMMIT it"). The template writes only 04_kicad/, so rebuild_reuse's
#      stated precondition could never be satisfied by running rebuild_all.
#      The 04_kicad copy is made from it, so the two are identical by
#      construction.
#  (b) `03_src/audit_board.py` is guarded with -f. This board has no per-board
#      audit script and should not need one (the generic backend + the SHARED
#      placement_gates.py own that job); rebuild_reuse.sh already guards the
#      same call and the template does not.
#  (c) STAGE 4 STOPS AT STEP [2]. Steps [3]+ need a promoted KRT route chain,
#      which does not exist yet — `route.yaml` deliberately carries no `final:`
#      key. For the SCHEMATIC gate alone use the bridge:
#        bash <kicad-pcb skill>/scripts/gen_tscircuit.sh projects/pluto-rx2-8way
#      which writes only 03_tscircuit/ and never touches 04_kicad.
set -euo pipefail
cd "$(dirname "$0")/.."                       # -> project root (03_src/..)

# --- board-specific knobs (the ONLY things to edit) -------------------------
BOARD=pluto_rx2_8way                           # <board> stem for 04_kicad/<board>.*
TSX=pluto_rx2_8way                             # 03_tscircuit/src/<TSX>.tsx basename
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
# (a): the converter's output lands in 03_tscircuit/kicad/ (the authoritative
# machine bridge per 03_tscircuit/contracts.md, and the PINNED canonical
# rebuild_reuse.sh consumes); 04_kicad gets a COPY for the board stages.
( cd 03_tscircuit && tsci build "src/$TSX.tsx" )
mkdir -p 03_tscircuit/kicad 06_build/netlists 04_kicad
$PY "$S/circuit_json_to_kicad_sch.py" 03_tscircuit/build/circuit.json \
    -o "03_tscircuit/kicad/$BOARD.kicad_sch" --parts 02_parts
cp "03_tscircuit/kicad/$BOARD.kicad_sch" "04_kicad/$BOARD.kicad_sch"
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
# (b): guarded — this board carries no per-board audit script by design.
if [ -f 03_src/audit_board.py ]; then $PY 03_src/audit_board.py; fi
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
