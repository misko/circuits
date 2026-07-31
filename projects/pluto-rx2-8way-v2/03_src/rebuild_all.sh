#!/bin/bash
# TEMPLATE rebuild_all.sh — the canonical generic pipeline (skill-owned).
# Copy into a new board's 03_src/ and set BOARD + TSX below. ZERO board-specific
# generation Python: board + route + rules all run on the SHARED skill scripts.
# See 03_src/contracts.md for the authoritative step order.
set -euo pipefail
cd "$(dirname "$0")/.."                       # -> project root (03_src/..)

# --- board-specific knobs (the ONLY things to edit) -------------------------
BOARD=pluto_rx2_8way_v2                                  # <board> stem for 04_kicad/<board>.*
TSX=pluto_rx2_8way_v2                                    # 03_tscircuit/src/<TSX>.tsx basename
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

# [0b] M-FRESH stamp — BEFORE the build, so the run has a witness that is not
# the build. Refuses on the spot if BOARD=/TSX= above are still the TEMPLATE
# knobs or do not resolve in this project: pluto-rx2-8way-v2 carried
# BOARD=pluto_rx2_8way_v2 from commission through four commits, so the full driver had
# NEVER RUN there while its stage gates reported green one at a time. A driver
# that was never run for this board must not look like one that ran and passed.
$PY "$S/build_provenance.py" stamp . --board "$BOARD" --tsx "$TSX" \
    || { echo "GATE FAILED [0b] M-FRESH (build_provenance.py stamp): the driver's BOARD=/TSX= knobs do not resolve to this project — edit them at the top of this file"; exit 1; }

# [1] tscircuit TSX -> circuit.json -> converter .kicad_sch -> netlist
#
# `tsci build` writes dist/src/<TSX>/circuit.json. It DOES NOT WRITE build/.
# The bridge home is build/circuit.json (03_tscircuit/contracts.md), so the
# copy is what connects them — and its absence is precisely the 2026-07-30
# pluto-rx2-8way-v2 defect: the converter was handed build/circuit.json, a path
# the builder never writes, so it consumed a SUPERSEDED file and TSX-PRE,
# S-NETMERGE, E-INV, E-ADR, E-TOPO, E-MARGIN, S-COUNT, E-NETREF and M-BOM all
# went green against an obsolete pad-numbering scheme. No checker was wrong.
# They graded exactly what they were handed.
CJ=03_tscircuit/build/circuit.json             # the ONE name for the converter input
( cd 03_tscircuit && tsci build "src/$TSX.tsx" )
mkdir -p 03_tscircuit/build
cp "03_tscircuit/dist/src/$TSX/circuit.json" "$CJ"

# [1a] M-FRESH verify — the pipeline asserts the artifact it is about to grade
# is the one it just built. build_provenance.py finds the producer under dist/
# ITSELF (it does not take this script's word for it) and requires the bytes to
# match, so a `touch` cannot forge freshness; it also requires the producer to
# post-date [0b] and the sources to be unmoved since. Canon M1: the checker
# neither builds nor copies the thing it grades.
$PY "$S/build_provenance.py" verify . --board "$BOARD" --tsx "$TSX" --artifact "$CJ" \
    || { echo "GATE FAILED [1a] M-FRESH (build_provenance.py verify): the artifact the converter would read is NOT the one this build produced — every gate below would be green against stale content"; exit 1; }

$PY "$S/circuit_json_to_kicad_sch.py" "$CJ" \
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
$PY "$FS/bom_source_check.py" --circuit-only "$CJ" --parts 02_parts \
    || { echo "GATE FAILED [1b] M-BOM leg C (bom_source_check.py --circuit-only): a coded R/C's catalog value != its tsx value prop (the R12/R30 class)"; exit 1; }

# [2] ERC gate (0 errors)
kicad-cli sch erc --severity-all --exit-code-violations "04_kicad/$BOARD.kicad_sch" \
    -o 06_build/erc.rpt || { echo "ERC FAILED"; exit 1; }

# [3] board (placement + zones) from floorplan.yaml  [SHARED]
$PY "$S/generate_board_generic.py" 03_src/floorplan.yaml -o "04_kicad/$BOARD.kicad_pcb"

# [4] placement/pad invariants  [per-board gate + SHARED placement gates]
# THIS BOARD HAS NO `03_src/audit_board.py`, DELIBERATELY, and the guard says so
# rather than the absence being silent. v2 is a ZERO-BESPOKE-PYTHON board (repo
# ADR-0002): placement comes from floorplan.yaml and every placement invariant
# it would have hand-checked is a SHARED gate that runs below or beside this
# line — `generate_board_generic`'s own `asserts:` (pad_net polarity, 12/12),
# P-COLLIDE, `placement_gates.py` P-OUT/P-CAP, `escape_check.py --board`
# P-LAND, and `copper_length_audit.py` R-LEN/R-LEN-OCT. The template calls the
# per-board script unconditionally; running it when it does not exist would
# abort the driver, and SKIPPING IT SILENTLY would let a board that lost its
# audit script look like one that passed it.
if [ -f 03_src/audit_board.py ]; then $PY 03_src/audit_board.py; \
  else echo "[4] no 03_src/audit_board.py (generic-backend board) - shared placement gates below"; fi
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
