#!/bin/bash
# Resume the exact generated schematic artifacts after the user accepts the
# public-catalog pre-layout checkpoint. This script intentionally does not run
# tscircuit again: supplier-warning and PDF metadata churn can replace the
# reviewed hashes without changing electrical connectivity.
set -euo pipefail
cd "$(dirname "$0")/.."

PY=/usr/bin/python3
REPO_ROOT="$(git rev-parse --show-toplevel)"
S="$REPO_ROOT/skills/kicad-pcb/scripts"
FS="$REPO_ROOT/skills/jlcpcb-fab/scripts"
BOARD=usb_controlled_debug_hub
CJ=03_tscircuit/build/circuit.json
SCHPDF=03_tscircuit/build/schematic.pdf
REQUEST=06_build/sourcing/prelayout_request.json
EVIDENCE=06_build/sourcing/catalog_stock_check_programmatic_2026-08-19.json
DECISION=01_docs/decisions/0017-public-catalog-prelayout-checkpoint.md

$PY "$S/build_provenance.py" audit .
$PY "$FS/jlc_pcba_availability.py" verify-request "$REQUEST" \
    --bom "$CJ" --assembly 03_src/rules/assembly.yaml \
    --procurement-policy 01_docs/sourcing/procurement-policy.yaml \
    --build-quantity 5 --phase prelayout
$PY "$FS/manufacturing_readiness.py" grade . --phase prelayout \
    --catalog-request "$REQUEST" --catalog-evidence "$EVIDENCE" \
    --catalog-decision "$DECISION" \
    --json 06_build/verification/manufacturing_readiness_prelayout.json

kicad-cli sch erc --severity-all "04_kicad/$BOARD.kicad_sch" -o 06_build/erc.rpt
kicad-cli sch erc --severity-error --exit-code-violations \
    "04_kicad/$BOARD.kicad_sch" -o 06_build/erc_errors.rpt

$PY "$S/stage_checkpoint.py" record . schematic \
    --input "$CJ" --input "$SCHPDF" \
    --input "04_kicad/$BOARD.kicad_sch" \
    --input "06_build/netlists/$BOARD.net" \
    --input 03_tscircuit/manifest.yaml \
    --input 06_build/build_provenance.json \
    --input 03_src/rebuild_all.sh

echo "PUBLIC-SOURCING RESUME PASS: exact schematic-stage bytes pinned"
echo "NEXT: bash 03_src/rebuild_all.sh --resume-after-schematic-review"
