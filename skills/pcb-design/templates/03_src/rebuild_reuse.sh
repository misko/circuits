#!/usr/bin/env bash
# TEMPLATE rebuild_reuse.sh — the DETERMINISTIC route-authority rebuild driver
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
# --schematic-parity --exit-code-violations 04_kicad/<board>.kicad_pcb = 0/0/0.
# The pinned .kicad_sch is copied beside the board
# first — without it --schematic-parity SILENTLY SKIPS (crow-rv2 finding).
set -euo pipefail
cd "$(dirname "$0")/.."                       # -> project root (03_src/..)

if [ -e 01_docs/COMMISSIONING-HOLD.md ] || [ -L 01_docs/COMMISSIONING-HOLD.md ]; then
    echo "GATE INCOMPLETE [PCB-COMMISSION]: 01_docs/COMMISSIONING-HOLD.md still exists; close the brief/fact locks and adopt every schema example before rebuilding" >&2
    exit 2
fi

PY=/usr/bin/python3
# Resolve the shared skill scripts from an explicit circuits checkout or this
# project's repository. An explicit CIRCUITS_ROOT is authority: never replace
# a bad value with an ambient installed skill.
if [ -n "${CIRCUITS_ROOT:-}" ]; then
    REPO_ROOT="$(cd "$CIRCUITS_ROOT" 2>/dev/null && pwd)" \
        || { echo "GATE FAILED [PCB-TOOLCHAIN]: CIRCUITS_ROOT is not a readable directory: $CIRCUITS_ROOT" >&2; exit 2; }
else
    REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" \
        || { echo "GATE FAILED [PCB-TOOLCHAIN]: project is outside the circuits checkout; export CIRCUITS_ROOT=/absolute/path/to/circuits" >&2; exit 2; }
fi
S="$REPO_ROOT/skills/kicad-pcb/scripts"
[ -f "$S/generate_board_generic.py" ] \
    || { echo "GATE FAILED [PCB-TOOLCHAIN]: resolved circuits checkout '$REPO_ROOT' does not contain skills/kicad-pcb; export CIRCUITS_ROOT=/absolute/path/to/circuits" >&2; exit 2; }
FS="$(dirname "$(dirname "$S")")/jlcpcb-fab/scripts"
export PATH="$HOME/.bun/bin:$PATH"

run_stage() {
    local stage="$1"; shift
    "$PY" "$S/pcb_flow.py" run . --stage "$stage" -- "$@"
}

PIPELINE_EVIDENCE=06_build/verification/pipeline
mkdir -p "$PIPELINE_EVIDENCE/bundles"

# P-MOD is source-only and cheap; the deterministic path must not bypass the
# architecture decision merely because it reuses a pinned schematic.
$PY "$S/module_first_check.py" . \
    || { echo "GATE FAILED P-MOD: module-first architecture contract"; exit 1; }
$PY "$S/rf_contract_check.py" . --require-applicability \
    || { echo "GATE FAILED RF-CONTRACT: explicit RF applicability/requirements"; exit 1; }
run_stage rf_context "$PY" "$S/rf_context.py" . \
    || { echo "GATE FAILED RF-CONTEXT: local RF source-card selection is incomplete"; exit 1; }
run_stage rf_solver "$PY" "$S/rf_solver.py" . \
    || { echo "GATE FAILED RF-SOLVER: a declared local solver job failed or exceeded its deadline"; exit 1; }
run_stage rf_source "$PY" "$S/rf_check.py" source . \
    || { echo "GATE FAILED RF-SOURCE: authored RF geometry/authority is inconsistent"; exit 1; }
$PY "$S/early_design_check.py" . \
    || { echo "GATE FAILED D-SPEC/E-PATH/E-SWDRV/E-SURGE: upstream design contract is red; deterministic replay may not bypass architecture"; exit 1; }
$PY "$S/rules_audit.py" . --phase source \
    || { echo "GATE FAILED A-SOURCE: net-class current/width/pour intent is malformed before deterministic replay"; exit 1; }

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

# Preserve an authenticated build/FINAL marker when route.import_source is
# explicitly `build`; deleting it here makes the deterministic driver destroy
# the very route lineage it is configured to import.  An explicit `promoted`
# source does not consult build/FINAL, so no filesystem-precedence cleanup is
# needed there either.  The importer owns source selection fail-closed.

# [1] netlist from the PINNED committed schematic (deterministic — never tsci)
mkdir -p 06_build/netlists
kicad-cli sch export netlist --format kicadsexpr \
    -o "06_build/netlists/$BOARD.net" "$SCH"

$PY "$S/pre_route_review_check.py" . --phase schematic \
    --netlist "06_build/netlists/$BOARD.net" \
    || { echo "GATE FAILED [1a] PR-REVIEW: topology witness missing, stale, or defective"; exit 1; }

$PY "$S/electrical_closure.py" . \
    --json "$PIPELINE_EVIDENCE/electrical_closure.json" \
    --stage-bundle "$PIPELINE_EVIDENCE/bundles/electrical_closure" \
    --stage-result "$PIPELINE_EVIDENCE/E-CLOSURE.stage.json" \
    || { echo "GATE FAILED [1a] E-CLOSURE: composed electrical battery is incomplete or stale"; exit 1; }

# Deterministic replay may consume the accepted prelayout receipt but may not
# bypass it. The full driver owns first-time request/template emission.
PCBA_RECEIPT=06_build/sourcing/prelayout_receipt.json
if [ ! -f "$PCBA_RECEIPT" ]; then
    echo "GATE INCOMPLETE [1b] J-PCBA-PRELAYOUT: no accepted receipt; run rebuild_all.sh to emit the exact JLCPCB request"
    exit 2
fi
$PY "$FS/manufacturing_readiness.py" grade . --phase prelayout \
    --pcba-receipt "$PCBA_RECEIPT" \
    --json 06_build/verification/manufacturing_readiness_prelayout.json \
    --stage-bundle "$PIPELINE_EVIDENCE/bundles/part_freeze" \
    --stage-result "$PIPELINE_EVIDENCE/S-PART-FREEZE.stage.json" \
    || { echo "GATE FAILED [1b] J-PCBA-PRELAYOUT: receipt missing, stale, substituted, insufficient, or bound to another source"; exit 1; }

# [2] board (placement + zones) from committed floorplan.yaml  [SHARED]
$PY "$S/generate_board_generic.py" 03_src/floorplan.yaml -o "04_kicad/$BOARD.kicad_pcb"
# KiCad parity discovers the comparison schematic only beside the board.  Put
# the pinned canonical copy in place before the preliminary and final DRC runs.
cp "$SCH" "04_kicad/$BOARD.kicad_sch"

# [2a] Physical/schematic/footprint pin identity, before any placement review
# or promoted-route import.
$PY "$S/pin_map_check.py" . --board "04_kicad/$BOARD.kicad_pcb" \
    --circuit-json 03_tscircuit/build/circuit.json \
    || { echo "GATE FAILED [2a] P-PINMAP: reconcile pin identities before placement/routing work"; exit 1; }

# [3] placement/pad invariants, if the board defines them  [per-board gate]
if [ -f 03_src/audit_board.py ]; then $PY 03_src/audit_board.py; fi
$PY "$S/placement_routability_preflight.py" grade . \
    --board "04_kicad/$BOARD.kicad_pcb" \
    --placement-config 03_src/placement_gates.json \
    --json 06_build/verification/placement_routability_receipt.json \
    --stage-bundle "$PIPELINE_EVIDENCE/bundles/placement_feasibility" \
    --stage-result "$PIPELINE_EVIDENCE/P-FEASIBILITY.stage.json" \
    || { echo "GATE FAILED [3] KICAD-PLACEMENT: physical placement and declared routability do not jointly pass"; exit 1; }
$PY "$S/model_coverage_check.py" "04_kicad/$BOARD.kicad_pcb" \
    -o 06_build/verification/model_coverage.json \
    || { echo "GATE FAILED [3m] P-MODEL: every fitted footprint needs a renderer-resolvable 3D body before placement review"; exit 1; }
$PY "$S/pad_separation.py" "04_kicad/$BOARD.kicad_pcb" --project . \
    || { echo "GATE FAILED [3] P-PADSEP: separate-footprint copper clearance"; exit 1; }

# [3a] Datasheet placement policy, before promoted-route import.  This is the
# same P-ADJ evaluator used by the final release audit, not a parallel metric.
$PY "$S/policy_audit.py" . --board "$BOARD" --skip-drc --phase placement \
    || { echo "GATE FAILED [3a] P-ADJ: datasheet placement budget violated before routing"; exit 1; }

$PY "$S/generate_rules_generic.py" .
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity \
    --format json -o 06_build/drc/pre_route.json "04_kicad/$BOARD.kicad_pcb"
$PY "$S/placement_drc_check.py" 06_build/drc/pre_route.json \
    || { echo "GATE FAILED [3b] P-DRC: exact placement has a short, clearance, library, hole, or parity defect before human review"; exit 1; }

# [4] netclasses + .kicad_dru BEFORE import (canon R1: rules ride into the route)  [SHARED]
#     (generate_rules_generic itself purges kicad-cli's stray
#     <board>.kicad_pcb.kicad_pro/.prl droppings — do NOT re-add a bespoke rmstray)
$PY "$S/generate_rules_generic.py" .

# [4a] P-LAND before promoted-route import: fail on a package/placement launch
# wall while the board is still track-free, not after replaying/stitching it.
$PY "$S/escape_check.py" --board "04_kicad/$BOARD.kicad_pcb" \
    || { echo "GATE FAILED [4a] P-LAND: a placed pad cannot launch its declared width"; exit 1; }

$PY "$S/tier_preflight.py" . \
    || { echo "GATE FAILED [4b] R-PREFLIGHT: route geometry disagrees with the fab tier"; exit 1; }
$PY "$S/route_and_stitch_generic.py" prep 03_src/route.yaml

$PY "$FS/model_registration_gate.py" . --board "04_kicad/$BOARD.kicad_pcb" \
    || { echo "GATE FAILED [4c] P-MODEL-REG: native body, footprint, courtyard, or attachment datums disagree"; exit 1; }
timeout --signal=TERM --kill-after=10s 180s \
    $PY "$FS/connector_orientation_gate.py" . --board "04_kicad/$BOARD.kicad_pcb" \
    || { echo "GATE FAILED [4d] P-ORIENT: connector mouth/edge geometry, render evidence, or explicit approval is missing, stale, or defective"; exit 1; }
$PY "$S/pre_route_review_check.py" . --phase placement \
    --board "04_kicad/$BOARD.kicad_pcb" \
    || { echo "GATE FAILED [4c] P-ROUTEBASE/PR-REVIEW: prepared-route compatibility or placement evidence missing, stale, or defective"; exit 1; }

# [5] import the PROMOTED KRT chain once into the track-free board  [SHARED]
$PY "$S/route_and_stitch_generic.py" import 03_src/route.yaml
# [5b] taps — no-op unless route.yaml configures `taps:`  [SHARED]
$PY "$S/route_and_stitch_generic.py" taps   03_src/route.yaml

# [6] stitch: pours + stitch/thermal vias + island heal + gate  [SHARED]
$PY "$S/route_and_stitch_generic.py" stitch 03_src/route.yaml
$PY "$S/critical_route_check.py" . --board "04_kicad/$BOARD.kicad_pcb" --require-connected \
    || { echo "GATE FAILED [6a] R-CRITESC: critical-pair copper is incomplete"; exit 1; }

# [7] generate_rules LAST — pcbnew saves in the chain clobber netclasses  [SHARED]
$PY "$S/generate_rules_generic.py" .
$PY "$S/rules_audit.py" . --board "04_kicad/$BOARD.kicad_pcb" \
    || { echo "GATE FAILED [7a] A-CLASS/A-AGREE/A-AMP/A-FIRE/A-ORDER: generated rules do not enforce authored copper intent"; exit 1; }
run_stage rf_realized "$PY" "$S/rf_check.py" realized . --board "04_kicad/$BOARD.kicad_pcb" \
    || { echo "GATE FAILED [7c] RF-REALIZED: saved RF copper/fence evidence is incomplete"; exit 1; }

# [8] Atomic route acceptance over the exact reused board.
run_stage route_acceptance "$PY" "$S/route_acceptance_gate.py" grade . \
    --board "04_kicad/$BOARD.kicad_pcb" --mode full \
    --drc-json 06_build/route/gate.json \
    --json 06_build/verification/route_acceptance_receipt.json \
    || { echo "GATE FAILED [8] KICAD-ROUTING: final reused copper was not atomically accepted"; exit 1; }
echo "rebuild_reuse: route acceptance GREEN from committed source"
