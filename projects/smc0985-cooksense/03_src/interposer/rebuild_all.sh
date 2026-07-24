#!/usr/bin/env bash
# rebuild_all.sh — interposer (Board C) build driver (ADR-0007 per-board).
# Regenerates 04_kicad/interposer.* from 03_src/interposer/ source in the
# canonical order (canon M3 + canon R1: rules BEFORE route and LAST again).
#
# MULTI-BOARD SHADOW ROOT: generate_rules_generic aborts on >1 .kicad_pro in
# 04_kicad/, and the flat-path lookups (fab_tier_util.resolve, tier_preflight,
# route_and_stitch net_class_floors) read <root>/03_src/rules/* — which in this
# project belongs to the OTHER board (cooksense symlinks). So every root-scoped
# step runs against a SINGLE-BOARD SHADOW VIEW (06_build/interposer/shadow_root:
# 03_src/rules -> interposer rules, 04_kicad = working copies, 06_build/02_parts
# -> the real tree) and the results are copied back. The sealed cooksense files
# are never read for config and never written.
#
# PRECONDITION (schematic stage, not driven here): 06_build/netlists/interposer.net
# (tsci build -> converter -> kicad-cli sch export netlist; see journal
# 03_schematic_interposer.md) and 04_kicad/interposer.kicad_sch (converter copy).
#
# Usage:  bash 03_src/interposer/rebuild_all.sh [--reroute]
#   default   : DETERMINISTIC — import the promoted 03_src/interposer/route
#               chain (canon M3). Fresh clone / CI reproduces DRC 0/0/0.
#   --reroute : full KRT race re-route (stochastic; this 10-net board
#               reconverges CLEAN on every candidate). Promote the new FINAL to
#               03_src/interposer/route/final_chain.kicad_pcb and commit it.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"   # circuits repo root
PROJ="projects/smc0985-cooksense"
S="skills/kicad-pcb/scripts"
FP="$PROJ/03_src/interposer/floorplan.yaml"
RT="$PROJ/03_src/interposer/route.yaml"
PY=/usr/bin/python3
cd "$ROOT"

REUSE=1
[ "${1:-}" = "--reroute" ] && REUSE=0

test -f "$PROJ/06_build/netlists/interposer.net" \
  || { echo "MISSING netlist $PROJ/06_build/netlists/interposer.net (run the schematic stage first)"; exit 2; }

SH="$ROOT/$PROJ/06_build/interposer/shadow_root"

echo "== 0/7 shadow root (single-board view for root-scoped generics) =="
rm -rf "$SH"
mkdir -p "$SH/03_src" "$SH/04_kicad"
ln -s ../../../../03_src/interposer/rules      "$SH/03_src/rules"
ln -s ../../../../03_src/interposer/route.yaml "$SH/03_src/route.yaml"
ln -s ../../../../03_src/interposer/floorplan.yaml "$SH/03_src/floorplan.yaml"
ln -s ../../../../03_src/interposer            "$SH/03_src/interposer"
ln -s ../../../../03_src/lib                   "$SH/03_src/lib"
ln -s ../../../02_parts                        "$SH/02_parts"
# 06_build is a REAL dir exposing ONLY this board's artifacts: policy_audit /
# electrical_invariants glob 06_build/netlists/*.net and grade the FIRST match
# — with the whole 06_build symlinked they graded the OTHER board's
# cooksense.net (E-INV 40/50 false-fails, measured 2026-07-24).
mkdir -p "$SH/06_build/netlists" "$SH/06_build/interposer/route"
ln -s ../../../../netlists/interposer.net      "$SH/06_build/netlists/interposer.net"
# interposer/route is a REAL dir (prep/import mkdir into it — pathlib mkdir
# chokes on a symlinked parent); the evidence dirs are symlinks to the real
# tree so the audit view sees fab/twin/pdf/verification/pin_audit.
for d in fab twin pdf verification pin_audit; do
  ln -s ../../../$d "$SH/06_build/interposer/$d" 2>/dev/null || true
done
# audit-view extras (policy_audit runs against this shadow as its project):
ln -s ../../../01_docs                         "$SH/01_docs"
ln -s ../../../08_reviews                      "$SH/08_reviews"
ln -s ../../../../03_src/interposer/audit_board.py "$SH/03_src/audit_board.py"
ln -s ../../../../03_src/interposer/rebuild_all.sh "$SH/03_src/rebuild_all.sh"
mkdir -p "$SH/03_tscircuit"
for f in src build kicad verification package.json; do
  ln -s ../../../../03_tscircuit/$f "$SH/03_tscircuit/$f" 2>/dev/null || true
done
cp "$ROOT/$PROJ/03_tscircuit/manifest_interposer.yaml" "$SH/03_tscircuit/manifest.yaml"

echo "== 1/7 generate_board (placement, track-free) =="
# SHARED-FILE GUARD (measured 2026-07-24): generate_board_generic rewrites
# 04_kicad/fp-lib-table (16 -> 4 libs) and 04_kicad/refdes_waiver.json ([] —
# erasing cooksense's 5-refdes waiver) — both SHARED with the sealed cooksense
# board; the clobber flipped the sealed board's policy audit to FAIL
# (R-DRC 152 / P-SILK-REF 5). Snapshot + restore around the step: cooksense's
# fp-lib-table is a superset of the 4 libs the interposer needs, and the
# interposer waives no refdes, so the cooksense versions serve BOTH boards.
TMPG=$(mktemp -d)
cp "$PROJ/04_kicad/fp-lib-table" "$PROJ/04_kicad/refdes_waiver.json" "$TMPG/" 2>/dev/null || true
$PY "$S/generate_board_generic.py" "$FP"
[ -f "$TMPG/fp-lib-table" ] && cp "$TMPG/fp-lib-table" "$PROJ/04_kicad/fp-lib-table"
[ -f "$TMPG/refdes_waiver.json" ] && cp "$TMPG/refdes_waiver.json" "$PROJ/04_kicad/refdes_waiver.json"
rm -rf "$TMPG"

echo "== 2/7 generate_rules BEFORE route (canon R1; shadow) =="
cp "$PROJ/04_kicad/interposer.kicad_pcb" "$PROJ/04_kicad/interposer.kicad_pro" "$SH/04_kicad/"
[ -f "$PROJ/04_kicad/fp-lib-table" ] && cp "$PROJ/04_kicad/fp-lib-table" "$SH/04_kicad/"
[ -f "$PROJ/04_kicad/interposer.kicad_sch" ] && cp "$PROJ/04_kicad/interposer.kicad_sch" "$SH/04_kicad/"
$PY "$S/generate_rules_generic.py" "$SH"

echo "== 2b/7 tier_preflight (R-PREFLIGHT; shadow) =="
$PY "$S/tier_preflight.py" "$SH"

echo "== 3/7 prep (track-free r0 + H* mounting-hole keepouts; ZIF bosses NOT fenced) =="
$PY "$S/route_and_stitch_generic.py" prep "$RT" --root "$SH"

if [ "$REUSE" = "1" ]; then
  echo "== 4/7 route SKIPPED: using promoted chain =="
  cp "$PROJ/03_src/interposer/route/final_chain.kicad_pcb" "$SH/06_build/interposer/route/promote_chain.kicad_pcb"
  echo "$SH/06_build/interposer/route/promote_chain.kicad_pcb" > "$SH/06_build/interposer/route/FINAL"
else
  echo "== 4/7 route (KRT race 3, stochastic) =="
  $PY "$S/route_and_stitch_generic.py" route "$RT" --root "$SH" --race 3
fi

echo "== 5/7 import chain into track-free board (NO taps, NO stitch: zero zones by design) =="
$PY "$S/route_and_stitch_generic.py" import "$RT" --root "$SH"

echo "== 6/7 generate_rules LAST (pcbnew saves clobber netclasses — canon R1; shadow) =="
$PY "$S/generate_rules_generic.py" "$SH"

echo "== 7/7 copy back board + pro + dru to the real 04_kicad =="
cp "$SH/04_kicad/interposer.kicad_pcb" "$SH/04_kicad/interposer.kicad_pro" "$SH/04_kicad/interposer.kicad_dru" "$PROJ/04_kicad/"

echo "== DONE: $PROJ/04_kicad/interposer.kicad_pcb =="
echo "   gate:  kicad-cli pcb drc --severity-all --refill-zones --schematic-parity"
