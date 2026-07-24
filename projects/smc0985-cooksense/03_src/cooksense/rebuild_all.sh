#!/usr/bin/env bash
# rebuild_all.sh — cooksense MAIN board build driver (ADR-0007 per-board).
# Regenerates 04_kicad/cooksense.kicad_pcb from 03_src/cooksense/ source in the
# canonical order. Canon M3 (everything downstream regenerates from source) +
# canon R1 (netclasses BEFORE routing AND generate_rules LAST after stitch).
#
# PRECONDITION (upstream schematic stage, not driven here): the netlist
# 06_build/netlists/cooksense.net must exist (tscircuit -> converter). Nets are
# frozen for the routing stage; this driver rebuilds placement+route+stitch only.
#
# Usage (from anywhere):  bash 03_src/cooksense/rebuild_all.sh [--reroute]
#   default    : DETERMINISTIC — import the promoted 03_src/cooksense/route chain
#                (canon M3 authoritative route); stitch fixes (ADC GND-via
#                reservations, eFuse pad4 seed-stub, thermal via, via_janitor)
#                are deterministic, so a fresh clone / CI reproduces 0/0/0.
#   --reroute  : full KRT race re-route (stochastic; 0-crossing topology
#                reconverges to 0 routed-net unconnected on every candidate).
#                Promote the new 06_build FINAL to route/final_chain.kicad_pcb to
#                re-freeze it. Use when placement/nets change.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"   # circuits repo root
PROJ="projects/smc0985-cooksense"
S="skills/kicad-pcb/scripts"
FP="$PROJ/03_src/cooksense/floorplan.yaml"
RT="$PROJ/03_src/cooksense/route.yaml"
PY=/usr/bin/python3
cd "$ROOT"

REUSE=1
[ "${1:-}" = "--reroute" ] && REUSE=0
[ "${1:-}" = "--reuse-route" ] && REUSE=1   # accepted alias (default)

test -f "$PROJ/06_build/netlists/cooksense.net" \
  || { echo "MISSING netlist $PROJ/06_build/netlists/cooksense.net (run the schematic stage first)"; exit 2; }

echo "== 1/7 generate_board (placement, track-free) =="
$PY "$S/generate_board_generic.py" "$FP"

echo "== 2/7 generate_rules (netclasses BEFORE route -- canon R1) =="
$PY "$S/generate_rules_generic.py" "$PROJ"

echo "== 3/7 prep (track-free r0 + keepouts incl. ADC GND-via reservations) =="
$PY "$S/route_and_stitch_generic.py" prep "$RT" --root "$PROJ"

if [ "$REUSE" = "1" ]; then
  echo "== 4/7 route SKIPPED (--reuse-route): using promoted chain =="
  cp "$PROJ/03_src/cooksense/route/final_chain.kicad_pcb" "$PROJ/06_build/route/promote_chain.kicad_pcb"
  echo "$ROOT/$PROJ/06_build/route/promote_chain.kicad_pcb" > "$PROJ/06_build/route/FINAL"
else
  echo "== 4/7 route (KRT race 3, stochastic) =="
  $PY "$S/route_and_stitch_generic.py" route "$RT" --root "$PROJ" --race 3
fi

echo "== 5/7 import chain into track-free board =="
$PY "$S/route_and_stitch_generic.py" import "$RT" --root "$PROJ"

echo "== 5a/8 tie U_EFUSE EP unnamed sub-pads -> GND (P1-A EP thermal path) =="
$PY "$PROJ/03_src/cooksense/tie_efuse_ep.py" "$PROJ"

echo "== 5b/8 unfill stale generate_board zone fills (pre-`fill` passes incl."
echo "        seed_stubs must start from UNFILLED zones; `fill` refills at the end) =="
$PY - "$PROJ/04_kicad/cooksense.kicad_pcb" <<'PYUNFILL'
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
n = sum(1 for z in b.Zones() if z.IsFilled())
for z in b.Zones():
    z.UnFill()
b.Save(sys.argv[1])
print(f"unfilled {n} zones")
PYUNFILL

echo "== 6/8 stitch (pours + thermal/plane vias) =="
$PY "$S/route_and_stitch_generic.py" stitch "$RT" --root "$PROJ"

echo "== 6b/8 post-refill dangling-GND-via prune (fill-AWARE, runs on the FINAL"
echo "        fill state -- prune_stitch_dangling runs mid-chain and 3 J_PI-field"
echo "        rescue vias evaded it when the final refill shifted, 2026-07-24) =="
$PY - "$PROJ/04_kicad/cooksense.kicad_pcb" <<'PYPRUNE'
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
MM = pcbnew.ToMM
CU = [l for l in b.GetEnabledLayers().CuStack()]
tracks = [t for t in b.GetTracks() if t.GetClass() != "PCB_VIA"]
pads = [p for f in b.GetFootprints() for p in f.Pads()]
kill = []
for v in [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]:
    if v.GetNetname() != "GND":
        continue
    pos = v.GetPosition(); vr = v.GetWidth()//2
    # keep if any same-net TRACK touches the barrel
    if any(t.GetNetname() == "GND" and
           (t.GetStart() - pos).EuclideanNorm() < vr + t.GetWidth()//2 + 1000 or
           t.GetNetname() == "GND" and
           (t.GetEnd() - pos).EuclideanNorm() < vr + t.GetWidth()//2 + 1000
           for t in tracks):
        continue
    # keep if a TRUE via-in-pad: barrel inside the pad COPPER (circular test —
    # bbox containment kept 3 useless In1-only vias that sat inside big J_PI
    # THT pad bboxes without touching the pad, 2026-07-24)
    def _in_pad(p):
        d = (p.GetPosition() - pos).EuclideanNorm()
        return d + vr <= min(p.GetSizeX(), p.GetSizeY()) // 2 + 1000
    if any(p.GetNetname() == "GND" and _in_pad(p) for p in pads):
        continue
    # count layers whose FILLED same-net zone contains the via centre
    nlay = 0
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != "GND":
            continue
        for l in CU:
            if z.IsOnLayer(l) and z.GetFilledPolysList(l).Contains(pos):
                nlay += 1
    if nlay < 2:
        kill.append(v)
for v in kill:
    b.Remove(v)
print(f"post-refill prune: removed {len(kill)} dangling GND via(s) "
      f"at {[ (round(MM(v.GetPosition().x),2), round(MM(v.GetPosition().y),2)) for v in kill ]}")
b.Save(sys.argv[1])
PYPRUNE

echo "== 7/8 generate_rules LAST (pcbnew save clobbers netclasses -- canon R1) =="
$PY "$S/generate_rules_generic.py" "$PROJ"

echo "== 8/8 apply_drc_policy (min_resolved_spokes + cosmetic-silk severities) =="
$PY "$PROJ/03_src/cooksense/apply_drc_policy.py" "$PROJ"

echo "== DONE: $PROJ/04_kicad/cooksense.kicad_pcb =="
echo "   gate:  kicad-cli pcb drc --severity-all --refill-zones --schematic-parity"
