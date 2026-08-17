#!/bin/bash
# TEMPLATE rebuild_all.sh — the canonical generic pipeline (skill-owned).
# Copy into a new board's 03_src/ and set BOARD + TSX + title below. ZERO board-specific
# generation Python: board + route + rules all run on the SHARED skill scripts.
# See 03_src/contracts.md for the authoritative step order.
set -euo pipefail
cd "$(dirname "$0")/.."                       # -> project root (03_src/..)

# --- board-specific knobs (the ONLY things to edit) -------------------------
BOARD=usb_controlled_debug_hub                 # <board> stem for 04_kicad/<board>.*
TSX=usb_controlled_debug_hub                   # 03_tscircuit/src/<TSX>.tsx basename
SCHEMATIC_TITLE=USB_CONTROLLED_DEBUG_HUB       # human PDF title
# ----------------------------------------------------------------------------

PY=/usr/bin/python3
# resolve the shared skill scripts (repo-relative first, ~/.claude fallback)
REPO_ROOT="$(cd "$(git rev-parse --show-toplevel 2>/dev/null || echo ../../..)" && pwd)"
SKROOT="$REPO_ROOT/skills"
S="$SKROOT/kicad-pcb/scripts"
[ -f "$S/generate_board_generic.py" ] || { SKROOT="$HOME/.claude/skills"; S="$SKROOT/kicad-pcb/scripts"; }
FS="$SKROOT/jlcpcb-fab/scripts"                # fab-skill checkers (bom_source_check)
export PATH="$HOME/.nvm/versions/node/v22.12.0/bin:$HOME/.bun/bin:$PATH"

run_stage() {
    local stage="$1"; shift
    "$PY" "$S/pcb_flow.py" run . --stage "$stage" -- "$@"
}

RESUME_AFTER_SCHEMATIC_REVIEW=false
case "${1:-}" in
    "") ;;
    --resume-after-schematic-review) RESUME_AFTER_SCHEMATIC_REVIEW=true ;;
    *) echo "usage: $0 [--resume-after-schematic-review]"; exit 2 ;;
esac
CJ=03_tscircuit/build/circuit.json
SCHPDF=03_tscircuit/build/schematic.pdf

if [ "$RESUME_AFTER_SCHEMATIC_REVIEW" = false ]; then

# [0a] P-MOD before generation spend: every complex subsystem is a module, or
# an evidence-backed bare-IC exception with an ADR and rejected module set.
$PY "$S/module_first_check.py" . \
    || { echo "GATE FAILED [0a] P-MOD (module_first_check.py): prefer a proven module, or document why modules cannot meet a binding requirement"; exit 1; }

# [0c] RF applicability/requirements are decided before schematic/layout spend.
$PY "$S/rf_contract_check.py" . --require-applicability \
    || { echo "GATE FAILED [0c] RF-CONTRACT: fix 03_src/rules/rf.yaml before continuing"; exit 1; }
run_stage rf_context "$PY" "$S/rf_context.py" . \
    || { echo "GATE FAILED [0c] RF-CONTEXT: local RF source-card selection is incomplete"; exit 1; }
run_stage rf_solver "$PY" "$S/rf_solver.py" . \
    || { echo "GATE FAILED [0c] RF-SOLVER: a declared local solver job failed or exceeded its deadline"; exit 1; }
run_stage rf_source "$PY" "$S/rf_check.py" source . \
    || { echo "GATE FAILED [0c] RF-SOURCE: authored RF geometry/authority is inconsistent"; exit 1; }

# [0] S-COUNT pre-gate: alphanumeric pads mapped BEFORE the first tsci build —
# tscircuit DROPS an unmapped part silently (ERC still 0, 2026-07-21 incident)
$PY "$S/tsx_preflight.py" . \
    || { echo "GATE FAILED [0] TSX-PRE (tsx_preflight.py): map alphanumeric pads in 03_tscircuit/parity_padmap.txt BEFORE tsci build"; exit 1; }

# [0d] Source-only schemas before the expensive foreign producer. These gates
# read authored YAML/part dossiers only; generated schematic/netlist bytes are
# deliberately unavailable here.
$PY "$S/net_label_survival.py" . --schema-only \
    || { echo "GATE FAILED [0d] S-SCHEMA: malformed label_survival contract before tsci build"; exit 1; }
$PY "$S/electrical_invariants.py" . --schema-only \
    || { echo "GATE FAILED [0d] E-INV-SCHEMA: malformed electrical invariants before tsci build"; exit 1; }
$PY "$S/control_protocol_check.py" . \
    || { echo "GATE FAILED [0d] CONTROL-PROTOCOL: observable timing contract is inconsistent before tsci build"; exit 1; }
$PY "$S/control_profile_codegen.py" . --check \
    || { echo "GATE FAILED [0d] CONTROL-PROFILE: generated firmware/decoder timing artifacts are missing or stale"; exit 1; }
$PY "$S/early_design_check.py" . \
    || { echo "GATE FAILED [0d] D-SPEC/E-PATH/E-SWDRV/E-SURGE/E-CAP/E-FAULT: authored electrical schemas are invalid before tsci build"; exit 1; }
$PY "$S/rules_audit.py" . --phase source \
    || { echo "GATE FAILED [0d] A-SOURCE: net-class current/width/pour intent is malformed before tsci build"; exit 1; }

# [0e] Layout sections and the precedent ladder are part-dossier facts. Grade
# them before TSX and before any hash-bound review; placement repeats the same
# implementation later and adds realized adjacency checks.
$PY "$S/policy_audit.py" . --skip-drc --phase source \
    || { echo "GATE FAILED [0e] P-LAYOUT/P-PREC: close source layout guidance and precedent ladders before tsci build or human review"; exit 1; }

# [0f] Repository schema/bound ratchets are also source-only. Run them before
# producer or reviewer spend: a new field read by nothing and a typed numeric
# ADR bound with no executable provenance are knowable from authored bytes.
# pcb_flow supplies streamed output, heartbeat and a hard timeout.
run_stage source_schema_governance "$PY" "$S/schema_reader_audit.py" --root "$REPO_ROOT" \
    || { echo "GATE FAILED [0f] G-ORPHAN: declare a proven reader or an honest ADVISORY/OWED disposition for every new schema field"; exit 1; }
run_stage adr_bound_governance "$PY" "$S/adr_bound_provenance.py" "$REPO_ROOT" \
    --repo-root "$REPO_ROOT" --timeout 30 \
    || { echo "GATE FAILED [0f] M-BOUND: make every new published inequality executable before build or review"; exit 1; }

# [0b] M-FRESH stamp — BEFORE the build, so the run has a witness that is not
# the build. Refuses on the spot if BOARD=/TSX= above are still the TEMPLATE
# knobs or do not resolve in this project: pluto-rx2-8way-v2 carried
# BOARD=power3s from commission through four commits, so the full driver had
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
# The ONE name for the converter input is $CJ, declared above so the exact
# artifact can also be named by the resume path without rebuilding it.
# Keep the foreign producer inside the same bounded runner as routing and DRC.
# It can be quiet while resolving supplier data or under host I/O pressure; a
# heartbeat distinguishes that from a dead pipeline, and the configured hard
# deadline terminates the complete process group instead of leaving a child.
run_stage tscircuit_deps env --chdir=03_tscircuit bun install --frozen-lockfile --ignore-scripts
run_stage tscircuit_build env --chdir=03_tscircuit ./node_modules/.bin/tsci build "src/$TSX.tsx"
mkdir -p 03_tscircuit/build
cp "03_tscircuit/dist/src/$TSX/circuit.json" "$CJ"

# [1d] tsci can exit zero while embedding hard geometry/component errors in
# circuit.json. Freshness and electrical parity correctly grade the artifact
# they receive, but do not own tscircuit's diagnostic vocabulary.
$PY "$S/circuit_json_diagnostics.py" "$CJ" \
    || { echo "GATE FAILED [1d] TSX-DIAG: tsci returned a circuit artifact containing hard error diagnostics"; exit 1; }

# [1r] THE HUMAN SCHEMATIC — regenerated, and DELETED FIRST so that a failure
# leaves ABSENCE rather than the previous revision.
#
# The 07_releases contract ships 03_tscircuit/build/schematic.pdf as
# `pdf/schematic.pdf`, and it is the only artifact in the release a human
# actually reads. `tsci build` does not write it any more than it writes
# build/circuit.json, and this template did not write it either — so it was
# whatever the last `gen_tscircuit.sh` run happened to leave. MEASURED on
# pluto-rx2-8way-v2 2026-07-30: schematic.pdf stamped 14:47:14 beside an
# 18:42:05 circuit.json, i.e. a release would have shipped a schematic
# document that does not match its own netlist, with every gate green.
#
# The `rm -f` is the load-bearing line, not the render. A render step that
# fails or is skipped must not be able to
# leave a stale PDF sitting where the seal will copy it: absence is loud and
# staleness is silent, so we make the failure mode absence and let M-FRESH
# below say so by name. The renderer consumes the exact circuit.json already
# graded above; it does not re-evaluate TSX. Hence `|| true` — the GATE reports
# the missing output by name rather than `set -e` stopping without context.
rm -f 03_tscircuit/build/schematic.svg "$SCHPDF"
NET_ALIAS_ARGS=()
[ -f 03_tscircuit/net_aliases.txt ] \
    && NET_ALIAS_ARGS=(--net-aliases 03_tscircuit/net_aliases.txt)
node "$S/render_schematic_pdf.mjs" "$CJ" "$SCHPDF" \
    --title "$SCHEMATIC_TITLE" "${NET_ALIAS_ARGS[@]}" || true

# [1a] M-FRESH verify — the pipeline asserts the artifacts it is about to grade
# and to SHIP are the ones it just built. build_provenance.py finds the producer
# under dist/ ITSELF (it does not take this script's word for it) and requires
# the bytes to match, so a `touch` cannot forge freshness; it also requires the
# producer to post-date [0b], the sources to be unmoved since, and the human
# schematic to exist and post-date the circuit.json it depicts (F-RENDER).
# Canon M1: the checker neither builds nor copies the things it grades.
$PY "$S/build_provenance.py" verify . --board "$BOARD" --tsx "$TSX" \
    --artifact "$CJ" --render "$SCHPDF" \
    || { echo "GATE FAILED [1a] M-FRESH (build_provenance.py verify): the artifact the converter would read is NOT the one this build produced, or the human schematic the release ships is missing/older than it — every gate below would be green against stale content"; exit 1; }

mkdir -p 04_kicad 06_build/netlists
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
$PY "$S/early_design_check.py" . \
    || { echo "GATE FAILED [1b] D-SPEC/E-PATH/E-SWDRV/E-SURGE: commission boundary, complete delivery path, switching drive, or surge coordination is not proven"; exit 1; }
$PY "$S/power_topology.py" . \
    || { echo "GATE FAILED [1b] E-TOPO (power_topology.py): converter topology does not match the derived Vin-vs-Vout"; exit 1; }
$PY "$S/power_topology.py" . --margin \
    || { echo "GATE FAILED [1b] E-MARGIN (power_topology.py --margin): output setpoint headroom below the delivery IR drop"; exit 1; }
$PY "$S/power_topology.py" . --off-control \
    || { echo "GATE FAILED [1b] E-OFF (power_topology.py --off-control): battery source without a declared de-energization path"; exit 1; }
$PY "$S/count_parity.py" . --pre-board \
    || { echo "GATE FAILED [1b] S-COUNT (count_parity.py): refdes sets disagree across intent/artifacts (silent drop)"; exit 1; }
$PY "$FS/bom_source_check.py" --circuit-only "$CJ" --parts 02_parts \
    || { echo "GATE FAILED [1b] M-BOM leg C (bom_source_check.py --circuit-only): a coded R/C's catalog value != its tsx value prop (the R12/R30 class)"; exit 1; }

# [2] ERC gate — 0 ERRORS. TWO RUNS, AND THE SPLIT IS THE CANON'S, NOT A
# SOFTENING. Canon S4 and the kicad-pcb golden rules both say the gate is
# "0 errors, warnings baselined with reasons" — but this template gated with
# `--severity-all --exit-code-violations`, which returns nonzero on ANY
# reported violation, warnings included. So the TEMPLATE contradicted the canon
# it implements, and a board fails its own driver on cosmetics.
#
# MEASURED 2026-07-30 on pluto-rx2-8way-v2's real .kicad_sch:
#   --severity-all   --exit-code-violations  -> EXIT 5, 220 findings
#                                               (131 endpoint_off_grid,
#                                                 89 lib_symbol_issues)
#   --severity-error --exit-code-violations  -> EXIT 0, 0 findings
# Both classes are artifacts of the tscircuit->KiCad converter's geometry and
# symbol-library synthesis; neither is electrical. A driver that cannot reach
# its own DRC stage on 220 cosmetic warnings gets edited per-board, and the
# per-board edit is how the ERC gate quietly becomes whatever each board could
# make pass.
#
# The full-severity report is still written FIRST and unconditionally, because
# "baselined with reasons" is only reviewable if the baseline is recorded —
# dropping it would trade a false gate for a blind one.
kicad-cli sch erc --severity-all "04_kicad/$BOARD.kicad_sch" -o 06_build/erc.rpt
kicad-cli sch erc --severity-error --exit-code-violations \
    "04_kicad/$BOARD.kicad_sch" -o 06_build/erc_errors.rpt \
    || { echo "GATE FAILED [2] ERC: the schematic carries ERC ERRORS (warnings are baselined in 06_build/erc.rpt; errors are not baselinable)"; exit 1; }

# [2c] Pin the exact bytes at the deliberate human-review pause. A resume must
# continue these bytes, not rerun the nondeterministic schematic producer and
# silently change the PDF/netlist that received approval.
$PY "$S/stage_checkpoint.py" record . schematic \
    --input "$CJ" \
    --input "$SCHPDF" \
    --input "04_kicad/$BOARD.kicad_sch" \
    --input "06_build/netlists/$BOARD.net" \
    --input 03_tscircuit/manifest.yaml \
    --input 06_build/build_provenance.json \
    --input 03_src/rebuild_all.sh \
    || { echo "GATE FAILED [2c] CHECKPOINT: could not pin the exact schematic review subject"; exit 1; }
else
    echo "[resume] verify the exact schematic-stage checkpoint; do not rebuild TSX"
    $PY "$S/build_provenance.py" audit . \
        || { echo "GATE FAILED [resume] M-FRESH: schematic sources or generated human/machine artifacts changed; run the full pipeline"; exit 1; }
    $PY "$S/stage_checkpoint.py" verify . schematic \
        || { echo "GATE FAILED [resume] CHECKPOINT: the reviewed schematic-stage bytes changed; run the full pipeline"; exit 1; }
fi

# [2a] Independent topology/ratings and human-readability reviews of the exact
# netlist/PDF. The first run intentionally stops here until fresh reviewers
# write both hash-bound witnesses configured in route.yaml. Continue with
# `rebuild_all.sh --resume-after-schematic-review`; rerunning the producer would
# replace the exact reviewed PDF and is therefore forbidden at this boundary.
$PY "$S/pre_route_review_check.py" . --phase schematic \
    --netlist "06_build/netlists/$BOARD.net" \
    || { echo "GATE FAILED [2a] PR-REVIEW: topology and delivered-schematic readability must both be SOUND before placement/routing spend"; exit 1; }

# [2b] Promote the exact schematic as soon as its own stage is complete and
# independently reviewed.  rebuild_reuse.sh is the deterministic iteration
# driver for the placement/routing stages; delaying this copy until the final
# PCB DRC made it silently consume the previous topology whenever the full
# driver paused (as designed) on a placement review.  A failed schematic stage
# still cannot promote anything: every producer, semantic, ERC, checkpoint and
# human-review gate above must pass first.
mkdir -p 03_tscircuit/kicad
cp "04_kicad/$BOARD.kicad_sch" "03_tscircuit/kicad/$BOARD.kicad_sch"
cmp -s "04_kicad/$BOARD.kicad_sch" "03_tscircuit/kicad/$BOARD.kicad_sch" \
    || { echo "GATE FAILED [2b] M-PIN: promoted schematic differs from the reviewed schematic-stage subject"; exit 1; }

# [3] board (placement + zones) from floorplan.yaml  [SHARED]
$PY "$S/artifact_provenance.py" begin . --stage pcb_layout \
    --input 03_src/floorplan.yaml --input 03_src/route.yaml \
    --input "04_kicad/$BOARD.kicad_sch" \
    --output "04_kicad/$BOARD.kicad_pcb" \
    --output "04_kicad/$BOARD.kicad_pro" \
    --output "04_kicad/$BOARD.kicad_dru" \
    --output 06_build/drc/gate.json
$PY "$S/generate_board_generic.py" 03_src/floorplan.yaml -o "04_kicad/$BOARD.kicad_pcb"
$PY "$S/count_parity.py" . \
    || { echo "GATE FAILED [3] S-COUNT (count_parity.py): generated PCB refdes differ from schematic intent"; exit 1; }

# [3a] P-PINMAP — run as soon as both producer artifacts exist. The dossier's
# physical pin set must reach the generated schematic and the real footprint;
# intentional manufacturer-fused lands require explicit evidence.
$PY "$S/pin_map_check.py" . --board "04_kicad/$BOARD.kicad_pcb" \
    --circuit-json 03_tscircuit/build/circuit.json \
    || { echo "GATE FAILED [3a] P-PINMAP: reconcile physical, schematic, and footprint pins before placement/routing work"; exit 1; }
if [ -f 03_src/rules/critical_parts.yaml ]; then
    $PY "$S/critical_part_facts.py" .
else
    echo "[3b] no critical_parts.yaml — no selective catastrophic part facts declared"
fi

# [4] placement/pad invariants  [per-board gate + SHARED placement gates]
# `03_src/audit_board.py` is the ONLY per-board emitter this pipeline still
# sanctions (03_src/contracts.md), and on a ZERO-BESPOKE-PYTHON board it does
# not exist: ADR-0002's whole point is that a new board writes NO generation
# Python, so placement comes from floorplan.yaml and every invariant the script
# would have hand-checked is a SHARED gate that runs below or beside this line
# — generate_board_generic's own `asserts:` (pad_net polarity, body_offset,
# pad_order, pad_beyond_edge), P-COLLIDE, placement_gates.py P-OUT/P-CAP,
# escape_check.py --board P-LAND, copper_length_audit.py R-LEN.
#
# Calling it unconditionally ABORTS every such board at `set -e` (the template
# shipped this way; pluto-rx2-8way-v2 hit it 2026-07-30). SKIPPING IT SILENTLY
# is the worse repair, and is why this is an `if` with an `else` that SPEAKS: a
# board that LOST its audit script would then be indistinguishable from a board
# that never had one, and would read as having passed a gate that never ran —
# the M-COVER class, arriving in a driver instead of a checker.
if [ -f 03_src/audit_board.py ]; then
    $PY 03_src/audit_board.py
else
    echo "[4] no 03_src/audit_board.py (generic-backend board) — shared placement gates below"
fi
# P-OUT pads-inside-outline + P-CAP corridor crossing-demand vs capacity —
# the two checks the cooksense routing D-BACK (2026-07-23, ~13h) proved were
# missing statically. Config 03_src/placement_gates.json is OPTIONAL
# (missing file = defaults); waivers live inside it, evidence required.
$PY "$S/placement_gates.py" "04_kicad/$BOARD.kicad_pcb" --config 03_src/placement_gates.json
$PY "$S/model_coverage_check.py" "04_kicad/$BOARD.kicad_pcb" \
    -o 06_build/verification/model_coverage.json \
    || { echo "GATE FAILED [4m] P-MODEL: every fitted footprint needs a renderer-resolvable 3D body before placement review"; exit 1; }
$PY "$S/critical_route_check.py" . --board "04_kicad/$BOARD.kicad_pcb" \
    || { echo "GATE FAILED [4a] R-PAIRMAP: critical pair polarity/wave/layer contract is incomplete"; exit 1; }
$PY "$S/rf_check.py" source . --require-geometry \
    --out 06_build/rf/placement \
    || { echo "GATE FAILED [4a2] RF-PLACEMENT: source-deferred controlled-impedance coordinates must close before route preparation"; exit 1; }

# P-PADSEP — separate-footprint pads must clear the fab-tier floor even on the
# same net; joining is explicit track/zone copper. Also catches paste over a
# foreign land, which ordinary connectivity DRC does not consider a short.
$PY "$S/pad_separation.py" "04_kicad/$BOARD.kicad_pcb" --project . \
    || { echo "GATE FAILED [4b] P-PADSEP: move footprints apart and route the connection explicitly"; exit 1; }

# P-LAYOUT/P-PREC/P-ADJ: the SAME policy implementation used at release,
# narrowed to placement rows and run while rerouting is still avoidable.
$PY "$S/policy_audit.py" . --board "$BOARD" --skip-drc --phase placement \
    || { echo "GATE FAILED [4c] P-ADJ: datasheet placement budget violated before routing"; exit 1; }

$PY "$S/generate_rules_generic.py" .
kicad-cli pcb drc --severity-all --refill-zones --schematic-parity \
    --format json -o 06_build/drc/pre_route.json "04_kicad/$BOARD.kicad_pcb"
$PY "$S/placement_drc_check.py" 06_build/drc/pre_route.json \
    || { echo "GATE FAILED [4c2] P-DRC: exact placement has a short, clearance, library, hole, or parity defect before human review"; exit 1; }

# [5] netclasses BEFORE route-prep (canon R1)  [SHARED]
$PY "$S/generate_rules_generic.py" .

# [5a] P-LAND at the moment pad geometry + width floors first coexist.  This
# is deliberately BEFORE route import: a pad that cannot emit its class width
# is a placement/package problem, not a router failure discovered minutes later.
$PY "$S/escape_check.py" --board "04_kicad/$BOARD.kicad_pcb" \
    || { echo "GATE FAILED [5a] P-LAND: a placed pad cannot launch its declared width"; exit 1; }

# [5b] R-PREFLIGHT: tool config == declared fab tier — refuse before prep/import
# (the template replays a promoted chain via `import`, which bypasses the
#  route-command gate; run the preflight explicitly so rebuilds are gated too)
$PY "$S/tier_preflight.py" . \
    || { echo "GATE FAILED [5b] R-PREFLIGHT (tier_preflight.py): a routing/stitch parameter disagrees with the declared fab tier"; exit 1; }

# [5c] Prepare deterministic seed copper before review. P-ROUTEBASE compares
# this exact r0 with the promoted chain, so stale prep cannot consume a human
# review cycle and then disappear at import.
run_stage route_prep   $PY "$S/route_and_stitch_generic.py" prep   03_src/route.yaml

# [5d] Exact pre-route pin/layout/render reviews plus the preliminary
# same-camera A-RENDER report. Final staged reviews still run after routing.
$PY "$FS/model_registration_gate.py" . --board "04_kicad/$BOARD.kicad_pcb" \
    || { echo "GATE FAILED [5d] P-MODEL-REG: native body, footprint, courtyard, or attachment datums disagree"; exit 1; }
# [5e] P-ORIENT: one semantic edge authority, per-instance geometry, bounded
# progress-visible renders, and exact human approval before routing spend.
timeout --signal=TERM --kill-after=10s 180s \
    $PY "$FS/connector_orientation_gate.py" . --board "04_kicad/$BOARD.kicad_pcb" \
    || { echo "GATE FAILED [5e] P-ORIENT: connector mouth/edge geometry, render evidence, or explicit approval is missing, stale, or defective"; exit 1; }
$PY "$S/pre_route_review_check.py" . --phase placement \
    --board "04_kicad/$BOARD.kicad_pcb" \
    || { echo "GATE FAILED [5d] P-ROUTEBASE/PR-REVIEW: prepared-route compatibility or placement evidence is missing, stale, or defective"; exit 1; }

# [6-8] import + stitch from route.yaml  [SHARED]
# Honor route.import_source from route.yaml.  Hard-coding `promoted` here makes
# projects using the reviewed build/FINAL chain fail even when their declared
# provenance policy and exact route marker are valid.
run_stage route_import $PY "$S/route_and_stitch_generic.py" import 03_src/route.yaml
run_stage route_taps   $PY "$S/route_and_stitch_generic.py" taps   03_src/route.yaml
run_stage stitch       $PY "$S/route_and_stitch_generic.py" stitch 03_src/route.yaml
$PY "$S/critical_route_check.py" . --board "04_kicad/$BOARD.kicad_pcb" --require-connected \
    || { echo "GATE FAILED [8a] R-CRITESC: critical pairs are open, on forbidden layers, or use forbidden vias"; exit 1; }
$PY "$S/reference_plane_check.py" "04_kicad/$BOARD.kicad_pcb" \
    --config 03_src/rules/nets.yaml \
    --json 06_build/verification/reference_plane.json \
    || { echo "GATE FAILED [8b] R-REFPLANE: foreign inner copper interrupts a declared high-speed reference corridor"; exit 1; }

# [9] generate_rules LAST (pcbnew saves clobber .kicad_pro netclasses)  [SHARED]
$PY "$S/generate_rules_generic.py" .
$PY "$S/rules_audit.py" . --board "04_kicad/$BOARD.kicad_pcb" \
    || { echo "GATE FAILED [9a] A-CLASS/A-AGREE/A-AMP/A-FIRE/A-ORDER: generated rules do not enforce authored copper intent"; exit 1; }
$PY "$S/via_ampacity_check.py" "04_kicad/$BOARD.kicad_pcb" 03_src/route.yaml \
    --json 06_build/verification/via_ampacity.json \
    || { echo "GATE FAILED [9b] A-VIA: a declared series transfer bank lacks current capacity"; exit 1; }
run_stage rf_realized "$PY" "$S/rf_check.py" realized . --board "04_kicad/$BOARD.kicad_pcb" \
    || { echo "GATE FAILED [9c] RF-REALIZED: saved RF copper/fence evidence is incomplete"; exit 1; }

# [10] DRC gate — must be 0 / 0 / 0 at full severity
run_stage layout_drc kicad-cli pcb drc --severity-all --refill-zones --schematic-parity \
    --format json -o 06_build/drc/gate.json "04_kicad/$BOARD.kicad_pcb"
$PY -c "import json;g=json.load(open('06_build/drc/gate.json'));v,u,p=len(g['violations']),len(g['unconnected_items']),len(g.get('schematic_parity',[]));print(f'DRC {v}/{u}/{p}');exit(0 if v==u==p==0 else 1)"
$PY "$S/artifact_provenance.py" finish . --stage pcb_layout

# [10c] GG-*: OBSERVED grading — canon M-COVER's observation arm.  [SHARED]
# Every gate above printed `N graded / M total`. This one RE-RUNS a derived
# battery of them under `skills/kicad-pcb/gradelib/` and grades what they
# ACTUALLY OPENED: a same-basename file under this root that nothing read
# (GG-SHADOW — on an ADR-0007 two-board project every flat `03_src/rules/<name>`
# gate grades ONE board and reports on the PROJECT), and a path a gate SELECTED
# that is not there while that basename is (GG-RESOLVE).
#
# ADVISORY ON PURPOSE — `|| true`, and that is a decision, not an oversight. A
# day-one fleet mandate lands as red rows on every board and is switched off
# within the week; this repo has already lost a check that way. What this line
# buys a board agent is the NAMES, at the moment they are cheap to act on.
#
# IT DOES NOT WRITE INTO THIS PROJECT. The battery runs against a
# `cp -a --reflink=auto` copy with symlinks preserved: traced gates open
# `*.kicad_prl` (every pcbnew LoadBoard does) and `06_build/policy_audit.md` for
# writing, and a grader that mutates its subject is not observing it.
# `--in-place` opts out. MEASURED 11 s on a two-board project.
#
# READ THE READ COUNT WITH ITS CAVEAT. It is a SUPERSET of subject evidence: a
# battery gate's own output that ALREADY EXISTED when the run started is counted
# in it, because neither the write-set (a METHOD test) nor the pre-run snapshot
# (an EXISTENCE test) is an IDENTITY test. Only the ZERO carries a verdict.
# Exit codes are a VOCABULARY: 3 = GRADED NOTHING (never a pass), 4 = a path did
# not resolve, 5 = UNOBSERVABLE. `--explain` prints the legend.
$PY "$S/trace_audit.py" --subject . || true

# [11] Verify the schematic-stage pin survived the later PCB stages unchanged.
# Promotion happens at [2b], where the independently reviewed schematic stage
# closes, so deterministic iteration is usable during deliberate placement and
# routing pauses.  Nothing after that boundary may silently replace it.
cmp -s "04_kicad/$BOARD.kicad_sch" "03_tscircuit/kicad/$BOARD.kicad_sch" \
    || { echo "GATE FAILED [11] M-PIN: PCB stages changed the reviewed pinned schematic"; exit 1; }
if [ -f 01_docs/findings.yaml ]; then
    $PY "$S/project_state.py" .
else
    echo "[11b] no findings.yaml — maturity remains undeclared"
fi
