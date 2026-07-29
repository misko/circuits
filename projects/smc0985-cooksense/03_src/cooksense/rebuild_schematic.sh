#!/usr/bin/env bash
# rebuild_schematic.sh — cooksense SCHEMATIC stage driver (v1.7, canon M3).
#
# `rebuild_all.sh` rebuilds placement+route from a netlist it treats as frozen.
# This is the stage that PRODUCES that netlist, and it exists as a committed
# script because it is NOT just `gen_tscircuit.sh`: this board has to force the
# converter's `--mode grid`, and the reason is a measured cross-net short.
#
# ############################ WHY --mode grid ##############################
# `circuit_json_to_kicad_sch.py` defaults to `--mode layout` (WIRED): it imports
# tscircuit's own schematic wire geometry.  It carries a guard that detects
# cross-net LABEL merges after import and auto-falls-back to `--mode grid`, and
# on 2026-07-28 that guard FIRED on one input (root labels
# ['SHIELD_DRAIN','TH_CAM_A']) and did not fire on another.
#
# MEASURED, 2026-07-28, on this board with the ADR-0020-correction netlist:
#   layout/WIRED  -> "4 segs dropped as cross-net", and the exported netlist has
#                    NO net `AND1` AT ALL.  Its three nodes — R_AND1PD.1,
#                    U_AND1.4 (the AND gate's OUTPUT) and U_AND3.1 — appear
#                    inside `3V3`, which is a 79-node power rail.
#                    THAT IS A HARD SHORT OF A SAFETY-CHAIN INTERMEDIATE TO 3V3:
#                    AND1 = MODE_AUTO_HW . WD_OK . ESTOP_OK, so three of the
#                    seven KEY_RELAY_ALLOWED terms would be permanently TRUE.
#   grid          -> 193 nets, `AND1` = {R_AND1PD.1, U_AND1.4, U_AND3.1},
#                    `3V3` = 76 nodes, every other net node-for-node as authored.
#
# The board has ALWAYS been built from grid mode (the guard fell back to it on
# every prior run), so this is not a change of substance — it is the same output,
# obtained deterministically instead of by luck.  The converter defect is
# REPORTED upstream, not patched here: this agent may not edit `skills/`, and it
# is the same family as commit fd76c6d ("the cross-net guard watched PINS, but
# the merge happens on LABELS").
#
# The HUMAN schematic document is unaffected — it is tscircuit's OWN render
# (build/schematic.pdf, ADR-0002), never the converter's sheet.
# ###########################################################################
#
# Usage:  bash 03_src/cooksense/rebuild_schematic.sh
set -euo pipefail
export PATH="$HOME/.bun/bin:$PATH"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
PROJ="$ROOT/projects/smc0985-cooksense"
S="$ROOT/skills/kicad-pcb/scripts"
T="$PROJ/03_tscircuit"
PY=/usr/bin/python3
cd "$ROOT"

echo "== 1/4 gen_tscircuit (tsx -> circuit.json, human schematic PDF, tsc netlist) =="
bash "$S/gen_tscircuit.sh" "$PROJ" || true      # its own parity leg compares against
                                                # the OLD 04_kicad board and is expected
                                                # to differ until rebuild_all.sh runs

echo "== 2/4 converter FORCED to --mode grid (see the header: layout mode shorts AND1 to 3V3) =="
$PY "$S/circuit_json_to_kicad_sch.py" "$T/build/circuit.json" \
    -o "$T/kicad/cooksense.kicad_sch" --project cooksense --mode grid

echo "== 3/4 ERC + netlist export from the grid sheet =="
kicad-cli sch erc --severity-all -o "$T/verification/erc_converter.rpt" \
    "$T/kicad/cooksense.kicad_sch" >/dev/null 2>&1 || true
ERRS=$(grep -c '; error' "$T/verification/erc_converter.rpt" 2>/dev/null || echo 0)
WARN=$(grep -c '; warning' "$T/verification/erc_converter.rpt" 2>/dev/null || echo 0)
echo "   converter ERC: $ERRS errors, $WARN warnings"
kicad-cli sch export netlist -o "$T/verification/converter_netlist.net" \
    "$T/kicad/cooksense.kicad_sch" >/dev/null 2>&1
mkdir -p "$PROJ/06_build/netlists"
cp "$T/verification/converter_netlist.net" "$PROJ/06_build/netlists/cooksense.net"

echo "== 4/4 SAFETY-CHAIN SANITY: the nets a cross-net merge would eat =="
$PY - "$PROJ/06_build/netlists/cooksense.net" <<'PYCHK'
import re, sys
s = open(sys.argv[1]).read()
nets = re.findall(r'\(net\s+\(code "\d+"\)\s+\(name "([^"]*)"\)(.*?)\n\t\t\)', s, re.S)
d = {n: re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)', b) for n, b in nets}
# every AND-chain intermediate and permission, with the node count it MUST have
EXPECT = {
    "AND1": 3, "AND2": 3, "KEY_RELAY_ALLOWED": 3, "CTR_SAFE": 3,
    "FAULT_SET_N": 3, "FAULT_LATCH_CLEAR": 5, "WD_OK": 10, "WD_OK_EXP": 2,
    "EF_OVLO": 3, "COIL_EN": 2, "COIL_EN_IN": 4,
}
bad = []
for k, n in EXPECT.items():
    got = d.get(k)
    if got is None:
        bad.append(f"{k}: MISSING (merged into another net?)")
    elif len(got) != n:
        bad.append(f"{k}: {len(got)} nodes, expected {n} -> {sorted(got)}")
print(f"   {len(nets)} nets; safety-chain spot-check {len(EXPECT)-len(bad)}/{len(EXPECT)}")
for b in bad:
    print("   FAIL " + b)
sys.exit(1 if bad else 0)
PYCHK
echo "== DONE: $PROJ/06_build/netlists/cooksense.net =="
echo "   next: bash 03_src/cooksense/rebuild_all.sh --reroute"
